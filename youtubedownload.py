import os
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from yt_dlp import YoutubeDL


class YouTubeDownloaderApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("540x360")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # URL Input
        ttk.Label(
            main_frame, text="YouTube URL:", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 2))
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.pack(fill=tk.X, pady=(0, 15))

        # Output Folder Selection
        ttk.Label(
            main_frame,
            text="Save Destination:",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 2))
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 15))

        self.path_entry = ttk.Entry(folder_frame)
        self.path_entry.insert(0, os.path.expanduser("~/Downloads"))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(
            folder_frame, text="Browse", command=self.browse_folder
        )
        browse_btn.pack(side=tk.RIGHT)

        # Format Selection
        ttk.Label(
            main_frame, text="Download Format:", font=("Helvetica", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 2))
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=tk.X, pady=(0, 15))

        self.format_var = tk.StringVar(value="video")
        video_radio = ttk.Radiobutton(
            format_frame,
            text="Video (MP4)",
            value="video",
            variable=self.format_var,
        )
        audio_radio = ttk.Radiobutton(
            format_frame,
            text="Audio Only (MP3)",
            value="audio",
            variable=self.format_var,
        )
        video_radio.pack(side=tk.LEFT, padx=(0, 20))
        audio_radio.pack(side=tk.LEFT)

        # Determinate Progress Bar (0 to 100%)
        self.progress_bar = ttk.Progressbar(
            main_frame, mode="determinate", maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 5))

        # Detailed Status Bar Frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Helvetica", 9),
            foreground="#555555",
        )
        self.status_label.pack(side=tk.LEFT)

        self.percent_label = ttk.Label(
            status_frame,
            text="0%",
            font=("Helvetica", 9, "bold"),
            foreground="#007ACC",
        )
        self.percent_label.pack(side=tk.RIGHT)

        # Download Button
        self.download_btn = ttk.Button(
            main_frame,
            text="Start Download",
            command=self.start_download_thread,
        )
        self.download_btn.pack(fill=tk.X, ipady=5)

    def browse_folder(self):
        selected_dir = filedialog.askdirectory(initialdir=self.path_entry.get())
        if selected_dir:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, selected_dir)

    def progress_hook(self, d):
        if d["status"] == "downloading":
            # Extract numerical percent value
            percent_str = d.get("_percent_str", "0%").strip()
            clean_percent = re.sub(r"\x1b\[[0-9;]*m", "", percent_str)

            try:
                percent_val = float(clean_percent.replace("%", ""))
            except ValueError:
                percent_val = 0.0

            downloaded = d.get("_downloaded_bytes_str", "0B").strip()
            total = d.get("_total_bytes_str", d.get("_total_bytes_estimate_str", "N/A")).strip()
            speed = d.get("_speed_str", "N/A").strip()
            eta = d.get("_eta_str", "N/A").strip()

            status_text = f"Downloading: {downloaded} / {total} @ {speed} (ETA: {eta})"

            # Update GUI safely on main thread
            self.after(0, self.update_progress, percent_val, status_text)

        elif d["status"] == "finished":
            self.after(
                0, self.update_progress, 100.0, "Converting / Finalizing file..."
            )

    def update_progress(self, percent_val, status_text):
        self.progress_bar["value"] = percent_val
        self.percent_label.config(text=f"{percent_val:.1f}%")
        self.status_label.config(text=status_text)

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        save_path = self.path_entry.get().strip()

        if not url:
            messagebox.showwarning("Input Error", "Please enter a valid YouTube URL.")
            return

        if not os.path.exists(save_path):
            messagebox.showwarning(
                "Directory Error", "The selected save directory does not exist."
            )
            return

        self.download_btn.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.percent_label.config(text="0%")
        self.status_label.config(text="Fetching video metadata...")

        threading.Thread(
            target=self.run_download,
            args=(url, save_path, self.format_var.get() == "audio"),
            daemon=True,
        ).start()

    def run_download(self, url, output_path, is_audio):
        extractor_args = {
            "youtube": {
                "player_client": ["tvhtml5", "android", "ios"],
                "player_skip": ["configs"],
            }
        }

        if is_audio:
            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "outtmpl": f"{output_path}/%(title)s.%(ext)s",
                "progress_hooks": [self.progress_hook],
                "extractor_args": extractor_args,
            }
        else:
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": f"{output_path}/%(title)s.%(ext)s",
                "progress_hooks": [self.progress_hook],
                "extractor_args": extractor_args,
            }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.after(
                0, self.download_complete, True, "Download completed successfully!"
            )
        except Exception as e:
            self.after(0, self.download_complete, False, str(e))

    def download_complete(self, success, message):
        self.download_btn.config(state=tk.NORMAL)

        if success:
            self.progress_bar["value"] = 100
            self.percent_label.config(text="100%")
            self.status_label.config(text="Finished!")
            messagebox.showinfo("Success", message)
        else:
            self.status_label.config(text="Error encountered.")
            messagebox.showerror("Download Error", f"Failed to download:\n{message}")


if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()