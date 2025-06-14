import os
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import ffmpeg
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

# Default album art (optional, if you want to provide a default image)
DEFAULT_ALBUM_ART = "default_album_art.jpeg"

# Your new save directory
DEFAULT_SAVE_PATH = "/Users/loganwonnacott/Desktop/Projects/Save"

# Ensure the default save path exists, and create it if it doesn't
os.makedirs(DEFAULT_SAVE_PATH, exist_ok=True)

# Function to download YouTube video and extract MP3, then re-encode it using FFmpeg
def download_youtube_audio(url, title):
    try:
        # Temp file path (accounting for the double .mp3 extension added by yt-dlp)
        temp_file = f"{DEFAULT_SAVE_PATH}/temp_file.mp3.mp3"

        # Download the audio to a temporary file
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{DEFAULT_SAVE_PATH}/temp_file.mp3',  # Save temporarily
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Re-encode the MP3 with the LAME encoder for better iTunes compatibility and rename it to the title
        re_encoded_file = f"{DEFAULT_SAVE_PATH}/{title}.mp3"
        ffmpeg.input(temp_file).output(re_encoded_file, codec='libmp3lame', qscale=2).run()

        # Remove the temporary original file
        if os.path.exists(temp_file):
            os.remove(temp_file)

        return re_encoded_file

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video: {e}")
        return None

# Function to add metadata to MP3 file
def add_metadata(mp3_file, title, artist, album, album_art_path):
    try:
        audio = EasyID3(mp3_file)
        audio['title'] = title
        audio['artist'] = artist
        audio['album'] = album

        # Check if album art was selected
        if album_art_path and os.path.exists(album_art_path):
            with open(album_art_path, 'rb') as albumart:
                audio.tags.add(
                    APIC(
                        encoding=3,  # UTF-8
                        mime='image/jpeg',  # Image type
                        type=3,  # Front cover
                        desc='Cover',
                        data=albumart.read()  # Read image data
                    )
                )
            messagebox.showinfo("Success", "Album art added successfully!")
        else:
            # If no album art was selected or file is missing
            if not album_art_path:
                messagebox.showinfo("Info", "No album art provided.")
            elif not os.path.exists(album_art_path):
                messagebox.showerror("Error", "Album art file does not exist.")

        # Save metadata in ID3v2.3 format for iTunes compatibility
        audio.save(v2_version=3)
        messagebox.showinfo("Success", f"MP3 saved to: {DEFAULT_SAVE_PATH}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add metadata: {e}")

# Function to open file dialog and set the album art file path
def browse_album_art():
    filename = filedialog.askopenfilename(
        title="Select Album Art",
        filetypes=[("JPEG files", "*.jpeg"), ("All files", "*.*")]
    )
    
    if filename:
        album_art_var.set(filename)  # Store the selected file path
        messagebox.showinfo("Selected Album Art", f"Selected file: {filename}")
    else:
        album_art_var.set('')  # Clear the variable if no file selected
        messagebox.showwarning("No file selected", "Please select an image file for album art.")

# GUI setup
def start_app():
    root = tk.Tk()
    root.title("YouTube to MP3 Converter")

    # Variables for user input
    url_var = tk.StringVar()
    title_var = tk.StringVar()
    artist_var = tk.StringVar()
    album_var = tk.StringVar()
    album_art_var = tk.StringVar()  # To hold the path to the selected album art image

    # Functions
    def download_and_convert():
        url = url_var.get()
        title = title_var.get()
        artist = artist_var.get()
        album = album_var.get()
        album_art_path = album_art_var.get()

        if not url or not title or not artist or not album:
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        # Download and convert
        mp3_file = download_youtube_audio(url, title)  # Pass title for file naming
        if mp3_file:
            add_metadata(mp3_file, title, artist, album, album_art_path)

    # Create input fields
    tk.Label(root, text="YouTube URL").pack(pady=5)
    tk.Entry(root, textvariable=url_var, width=50).pack(pady=5)

    tk.Label(root, text="Title").pack(pady=5)
    tk.Entry(root, textvariable=title_var, width=50).pack(pady=5)

    tk.Label(root, text="Artist").pack(pady=5)
    tk.Entry(root, textvariable=artist_var, width=50).pack(pady=5)

    tk.Label(root, text="Album").pack(pady=5)
    tk.Entry(root, textvariable=album_var, width=50).pack(pady=5)

    # Browse button for album art selection
    tk.Button(root, text="Browse Album Art", command=browse_album_art).pack(pady=5)
    tk.Entry(root, textvariable=album_art_var, width=50).pack(pady=5)

    # Download & Convert button
    tk.Button(root, text="Download & Convert", command=download_and_convert).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    start_app()
