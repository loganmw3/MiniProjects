import tkinter as tk
from tkinter import messagebox
import random
import pygame


class GuitarPracticeApp:


    SESSION_SECONDS = 5 * 60  # 5‑minute session

    MAJOR_CHORDS = ["C", "D", "E", "F", "G", "A", "B"]
    MINOR_CHORDS = ["Am", "Bm", "Cm", "Dm", "Em", "Fm", "Gm"]
    ALL_CHORDS = MAJOR_CHORDS + MINOR_CHORDS

    FIXED_PATTERN = ["D", "", "D", "", "", "U", "D", "U"]  # len 8

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Guitar Practice App")
        self.root.geometry("460x740")

        # Sound init 
        pygame.mixer.init()
        try:
            self.tick = pygame.mixer.Sound("tick.wav")
        except pygame.error:
            self.tick = None
            print("tick.wav missing – metronome disabled.")

        # Runtime state 
        self.timer_running = False
        self.paused = False
        self.remaining = self.SESSION_SECONDS

        self.strum_pattern: list[str] = []  # length 8
        self.strum_idx = 0
        self.half_interval_ms = 250
        self.metronome_on = False

        # progression
        self.chords: list[str] = []
        self.chord_idx = 0

        self._build_ui()

    # UI BUILD
    def _build_ui(self):
        # Countdown
        self.timer_lbl = tk.Label(self.root, text="05:00", font=("Helvetica", 26))
        self.timer_lbl.pack(pady=8)

        # Current chord & pattern
        self.chord_lbl = tk.Label(self.root, text="", font=("Helvetica", 30))
        self.chord_lbl.pack()
        self.pattern_lbl = tk.Label(self.root, text="", font=("Helvetica", 26))
        self.pattern_lbl.pack(pady=6)

        # Status & full progression display
        self.status_lbl = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.status_lbl.pack()
        self.progress_lbl = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.progress_lbl.pack(pady=6)

        # Tempo
        tk.Label(self.root, text="Tempo (BPM):").pack()
        self.tempo_entry = tk.Entry(self.root, width=6, justify="center")
        self.tempo_entry.insert(0, "60")
        self.tempo_entry.pack(pady=4)

        # Strumming pattern controls 
        tk.Label(self.root, text="Pattern (8 chars – even=D/blank, odd=U/blank)").pack()
        self.custom_entry = tk.Entry(self.root)
        self.custom_entry.pack(pady=4)
        tk.Button(self.root, text="Set Custom", command=self.set_custom_pattern).pack(pady=1)
        tk.Button(self.root, text="Fixed D U …", command=self.set_fixed_pattern).pack(pady=1)
        tk.Button(self.root, text="Random Pattern", command=self.set_random_pattern).pack(pady=1)

        # Pre‑defined progression buttons 
        prog_frame = tk.Frame(self.root)
        prog_frame.pack(pady=6)
        tk.Label(prog_frame, text="Quick Progressions:").pack(side="left", padx=4)
        tk.Button(prog_frame, text="Major", command=lambda: self.set_progression('major')).pack(side="left", padx=4)
        tk.Button(prog_frame, text="Minor", command=lambda: self.set_progression('minor')).pack(side="left", padx=4)
        tk.Button(prog_frame, text="Random", command=lambda: self.set_progression('random')).pack(side="left", padx=4)

        # Custom dropdown progression
        tk.Label(self.root, text="Custom 4‑chord progression:").pack(pady=4)
        dropdown_frame = tk.Frame(self.root)
        dropdown_frame.pack()
        self.dropdown_vars = [tk.StringVar(value="") for _ in range(4)]
        for i, var in enumerate(self.dropdown_vars):
            om = tk.OptionMenu(dropdown_frame, var, *([""] + self.ALL_CHORDS))
            om.config(width=4)
            om.grid(row=0, column=i, padx=4)
        tk.Button(self.root, text="Use Custom Progression", command=self.use_custom_progression).pack(pady=4)

        # Metronome toggle
        self.met_var = tk.IntVar(value=0)
        tk.Checkbutton(self.root, text="Enable Metronome", variable=self.met_var).pack(pady=4)

        # Transport buttons
        tk.Button(self.root, text="Start", command=self.start).pack(pady=4)
        tk.Button(self.root, text="Pause", command=self.pause).pack(pady=1)
        tk.Button(self.root, text="Resume", command=self.resume).pack(pady=1)
        tk.Button(self.root, text="Stop", command=self.stop).pack(pady=1)

    # PATTERN VALIDATION
    def _validate_and_set_pattern(self, pattern: list[str]):
        if len(pattern) != 8:
            messagebox.showerror("Pattern", "Pattern must be exactly 8 characters.")
            return False
        for i, ch in enumerate(pattern):
            if i % 2 == 0 and ch not in ("D", ""):
                messagebox.showerror("Pattern", "Even slots must be 'D' or blank.")
                return False
            if i % 2 == 1 and ch not in ("U", ""):
                messagebox.showerror("Pattern", "Odd slots must be 'U' or blank.")
                return False
        self.strum_pattern = pattern
        self._render_pattern()
        return True

    def set_fixed_pattern(self):
        self._validate_and_set_pattern(self.FIXED_PATTERN.copy())
        self.status_lbl.config(text="Fixed pattern set")

    def set_random_pattern(self):
        patt = [(random.choice(["D", ""])) if i % 2 == 0 else random.choice(["U", ""]) for i in range(8)]
        self._validate_and_set_pattern(patt)
        self.status_lbl.config(text="Random pattern generated")

    def set_custom_pattern(self):
        raw = self.custom_entry.get().upper().replace(" ", "")
        patt = [c if c in ["D", "U"] else "" for c in raw]
        if self._validate_and_set_pattern(patt):
            self.status_lbl.config(text="Custom pattern set")

    def _render_pattern(self):
        if not self.strum_pattern:
            self.pattern_lbl.config(text="")
            return
        display = []
        for i, ch in enumerate(self.strum_pattern):
            symbol = ch if ch else "-"
            display.append(f"[{symbol}]" if i == self.strum_idx else symbol)
        self.pattern_lbl.config(text=' '.join(display))


    # PROGRESSION HELPERS
    def set_progression(self, mode: str):
        bank = self.MAJOR_CHORDS if mode == 'major' else self.MINOR_CHORDS if mode == 'minor' else self.ALL_CHORDS
        self.chords = random.sample(bank, 4)
        self.chord_idx = 0
        self.progress_lbl.config(text=' '.join(self.chords))
        self.chord_lbl.config(text="")

    def use_custom_progression(self):
        selection = [var.get() for var in self.dropdown_vars if var.get()]
        if not selection:
            messagebox.showwarning("Progression", "Select at least one chord from the dropdowns.")
            return
        self.chords = selection
        # Ensure exactly 4 slots (pad empty selections at end)
        while len(self.chords) < 4:
            self.chords.append(self.chords[-1])  # repeat last choice
        self.chord_idx = 0
        self.progress_lbl.config(text=' '.join(self.chords))
        self.chord_lbl.config(text="")
        self.status_lbl.config(text="Custom progression loaded")


    # TRANSPORT CONTROLS
    def _validated_bpm(self):
        try:
            bpm = int(self.tempo_entry.get())
            if bpm <= 0:
                raise ValueError
            return bpm
        except ValueError:
            messagebox.showerror("Tempo", "Enter a positive integer BPM.")
            return None

    def start(self):
        if self.timer_running:
            return
        if not self.strum_pattern:
            messagebox.showwarning("Pattern", "Set a strumming pattern first.")
            return
        bpm = self._validated_bpm()
        if bpm is None:
            return
        self.half_interval_ms = int(60 / (bpm * 2) * 1000)

        # reset state
        self.timer_running = True
        self.paused = False
        self.remaining = self.SESSION_SECONDS
        self.strum_idx = 0
        self.metronome_on = bool(self.met_var.get()) and self.tick is not None

        self._tick_timer()
        self._tick_loop()

    def pause(self):
        if self.timer_running and not self.paused:
            self.paused = True
            self.metronome_on = False

    def resume(self):
        if self.timer_running and self.paused:
            self.paused = False
            self.metronome_on = bool(self.met_var.get()) and self.tick is not None
            self._tick_timer()
            self._tick_loop()

    def stop(self):
        self.timer_running = False
        self.paused = False
        self.metronome_on = False
        self.remaining = self.SESSION_SECONDS
        self.timer_lbl.config(text="05:00")
        self.chord_lbl.config(text="")
        self.pattern_lbl.config(text="")
        self.status_lbl.config(text="")
        self.progress_lbl.config(text="")


    # TIMERS
    def _tick_timer(self):
        if not self.timer_running or self.paused:
            return
        mins, secs = divmod(self.remaining, 60)
        self.timer_lbl.config(text=f"{mins:02}:{secs:02}")
        if self.remaining > 0:
            self.remaining -= 1
            self.root.after(1000, self._tick_timer)
        else:
            self.timer_running = False
            self.chord_lbl.config(text="Session complete!")
            self.pattern_lbl.config(text="")

    def _tick_loop(self):
        if not self.timer_running or self.paused:
            return

        # Render pattern and maybe play tick
        self._render_pattern()
        if self.metronome_on and self.strum_idx % 2 == 0:
            self._play_tick()

        # Advance strum index
        self.strum_idx = (self.strum_idx + 1) % 8
        if self.strum_idx == 0:
            self._advance_chord()

        self.root.after(self.half_interval_ms, self._tick_loop)

    def _play_tick(self):
        if self.tick:
            self.tick.play()

    def _advance_chord(self):
        if not self.chords:
            return
        self.chord_lbl.config(text=self.chords[self.chord_idx])
        self.chord_idx = (self.chord_idx + 1) % len(self.chords)


if __name__ == "__main__":
    root = tk.Tk()
    app = GuitarPracticeApp(root)
    root.mainloop()
