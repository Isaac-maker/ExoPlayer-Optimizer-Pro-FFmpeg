import os
import re
import time
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from datetime import timedelta


# ==============================
#  Color palette / theme
# ==============================
BG_MAIN      = "#0f1117"
BG_PANEL     = "#171a21"
BG_CARD      = "#1c2029"
BG_LOG       = "#0a0c10"
ACCENT       = "#7c5cff"
ACCENT_HOVER = "#8f74ff"
GREEN        = "#2ecc71"
GREEN_HOVER  = "#3fe08a"
BLUE         = "#4f9cf9"
DANGER       = "#e5534b"
DANGER_HOVER = "#ff6b63"
TEXT_MAIN    = "#f2f4f8"
TEXT_MUTED   = "#8b93a3"
BORDER       = "#2a2f3a"
SUCCESS      = "#3ddc84"
WARNING      = "#ffb454"


class FFmpegApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ExoPlayer Optimizer Pro — FFmpeg")
        self.root.geometry("860x720")
        self.root.configure(bg=BG_MAIN)
        self.root.minsize(780, 620)

        self.files = []
        self.output_folder = ""
        self.total_duration = 0
        self.current_file_index = 0
        self.is_running = False
        self.start_time = None

        # ---------- Styles ----------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar",
                        thickness=8,
                        troughcolor=BG_CARD,
                        background=ACCENT,
                        bordercolor=BG_CARD)
        style.configure("Vertical.TScrollbar",
                        background=BG_PANEL,
                        troughcolor=BG_CARD,
                        arrowcolor=TEXT_MUTED,
                        bordercolor=BG_PANEL)

        # ========== CONVERT BUTTON (pinned at bottom) ==========
        # IMPORTANT: packed with side="bottom" BEFORE the expanding content above,
        # so it always keeps its space at the bottom of the window.
        self.btn_convert = tk.Button(root, text="🚀  START CONVERSION",
                                     command=self.start_conversion,
                                     bg=GREEN, fg="#0a0a0a", font=("Segoe UI", 13, "bold"),
                                     activebackground=GREEN_HOVER, activeforeground="#0a0a0a",
                                     bd=0, pady=13, cursor="hand2", state="disabled",
                                     disabledforeground="#666666")
        self.btn_convert.pack(side="bottom", fill="x", padx=24, pady=(4, 18))

        # ========== HEADER ==========
        header = tk.Frame(root, bg=BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 8))

        title_wrap = tk.Frame(header, bg=BG_MAIN)
        title_wrap.pack(anchor="w")

        tk.Label(title_wrap, text="🎬", font=("Segoe UI", 20), bg=BG_MAIN, fg=TEXT_MAIN).pack(side="left")
        tk.Label(title_wrap, text="ExoPlayer Optimizer Pro", font=("Segoe UI", 18, "bold"),
                 fg=TEXT_MAIN, bg=BG_MAIN).pack(side="left", padx=(8, 0))

        tk.Label(header, text="Re-encode videos so they play smoothly on Telegram / Android / Fire TV",
                 font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_MAIN).pack(anchor="w", pady=(2, 0))

        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", pady=(14, 0))

        # ========== TOP PANEL: Files + Output folder ==========
        top_panel = tk.Frame(root, bg=BG_MAIN)
        top_panel.pack(fill="x", padx=24, pady=10)

        btn_frame = tk.Frame(top_panel, bg=BG_MAIN)
        btn_frame.pack(fill="x")

        self.btn_select = self._make_button(
            btn_frame, "📁  Select Videos", self.select_files, BLUE
        )
        self.btn_select.pack(side="left", padx=(0, 10))

        self.btn_clear = self._make_button(
            btn_frame, "🗑  Clear List", self.clear_files, DANGER
        )
        self.btn_clear.pack(side="left", padx=(0, 10))

        # Output folder row
        dest_frame = tk.Frame(top_panel, bg=BG_MAIN)
        dest_frame.pack(fill="x", pady=(12, 0))

        tk.Label(dest_frame, text="📂 Output folder:", fg=TEXT_MUTED, bg=BG_MAIN,
                 font=("Segoe UI", 10)).pack(side="left")

        self.lbl_output = tk.Label(dest_frame, text="(same folder as each video)", fg=GREEN,
                                   bg=BG_MAIN, font=("Segoe UI", 10, "bold"))
        self.lbl_output.pack(side="left", padx=(5, 10))

        self._make_button(dest_frame, "Change folder", self.select_output_folder,
                          "#3a4152", hover="#4a5265").pack(side="left")

        # ========== OPTIONS ==========
        opts = tk.LabelFrame(root, text="  Conversion Options  ", bg=BG_PANEL, fg=TEXT_MUTED,
                             font=("Segoe UI", 10), bd=1, relief="solid", highlightbackground=BORDER)
        opts.pack(fill="x", padx=24, pady=6)

        self.fast_mode = tk.BooleanVar(value=True)
        self.res_720 = tk.BooleanVar(value=False)
        self.audio_only_copy = tk.BooleanVar(value=False)

        for text, var in [
            ("Fast mode (ultrafast preset — finishes much sooner)", self.fast_mode),
            ("Force 720p (smaller files, ideal for phones)", self.res_720),
            ("Copy audio without re-encoding (faster if already AAC)", self.audio_only_copy),
        ]:
            cb = tk.Checkbutton(opts, text=text, variable=var, bg=BG_PANEL, fg=TEXT_MAIN,
                                selectcolor=BG_CARD, activebackground=BG_PANEL,
                                activeforeground=TEXT_MAIN, font=("Segoe UI", 9),
                                cursor="hand2")
            cb.pack(anchor="w", padx=14, pady=3)

        # ========== FILE QUEUE ==========
        list_frame = tk.LabelFrame(root, text="  File Queue  ", bg=BG_PANEL, fg=TEXT_MUTED,
                                   font=("Segoe UI", 10), bd=1, relief="solid")
        list_frame.pack(fill="both", expand=True, padx=24, pady=6)

        self.listbox = tk.Listbox(list_frame, bg=BG_CARD, fg=TEXT_MAIN,
                                  selectbackground=ACCENT, selectforeground="#ffffff",
                                  font=("Consolas", 10), bd=0, highlightthickness=0,
                                  activestyle="none", selectmode="extended")
        self.listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # ========== PROGRESS ==========
        prog_frame = tk.Frame(root, bg=BG_MAIN)
        prog_frame.pack(fill="x", padx=24, pady=(6, 0))

        self.lbl_current = tk.Label(prog_frame, text="Waiting for files…", fg=TEXT_MAIN,
                                    bg=BG_MAIN, font=("Segoe UI", 11, "bold"))
        self.lbl_current.pack(anchor="w")

        self.progress = ttk.Progressbar(prog_frame, mode="determinate", maximum=100, style="TProgressbar")
        self.progress.pack(fill="x", pady=(6, 4))

        stats = tk.Frame(prog_frame, bg=BG_MAIN)
        stats.pack(fill="x")
        self.lbl_percent = tk.Label(stats, text="0%", fg=ACCENT, bg=BG_MAIN,
                                    font=("Segoe UI", 10, "bold"))
        self.lbl_percent.pack(side="left")
        self.lbl_eta = tk.Label(stats, text="ETA: --:--", fg=TEXT_MUTED, bg=BG_MAIN,
                                font=("Segoe UI", 10))
        self.lbl_eta.pack(side="right")

        # ========== LIVE LOG ==========
        log_frame = tk.LabelFrame(root, text="  FFmpeg Log (real time)  ", bg=BG_PANEL, fg=TEXT_MUTED,
                                  font=("Segoe UI", 10), bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True, padx=24, pady=6)

        self.log_text = scrolledtext.ScrolledText(log_frame, bg=BG_LOG, fg=SUCCESS,
                                                  font=("Consolas", 9), wrap="word", bd=0,
                                                  highlightthickness=0, state="disabled",
                                                  insertbackground=TEXT_MAIN)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    # ---------- Button helper with hover effect ----------
    def _make_button(self, parent, text, command, color, hover=None):
        hover = hover or color
        btn = tk.Button(parent, text=text, command=command, bg=color, fg="#ffffff",
                        font=("Segoe UI", 10, "bold"), bd=0, padx=16, pady=8,
                        cursor="hand2", activebackground=hover, activeforeground="#ffffff")
        btn.bind("<Enter>", lambda e: e.widget.config(bg=hover))
        btn.bind("<Leave>", lambda e: e.widget.config(bg=color))
        return btn

    def log(self, msg, color=SUCCESS):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ---------- File handling ----------
    def select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select videos to convert",
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.m4v"),
                       ("All files", "*.*")]
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", os.path.basename(p))
        self.update_button_state()

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, "end")
        self.update_button_state()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Choose the output folder")
        if folder:
            self.output_folder = folder
            self.lbl_output.config(text=folder, fg=GREEN)
            self.log(f"Output folder: {folder}", "#64B5F6")
        self.update_button_state()

    def update_button_state(self):
        if self.files and not self.is_running:
            self.btn_convert.config(state="normal",
                                    text=f"🚀  START CONVERSION  ({len(self.files)} file{'s' if len(self.files) != 1 else ''})")
        elif self.is_running:
            self.btn_convert.config(state="disabled", text="⏳  CONVERTING…")
        else:
            self.btn_convert.config(state="disabled", text="🚀  START CONVERSION")

    # ---------- Helpers ----------
    def get_video_duration(self, path):
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=30)
            return float(result.stdout.strip())
        except Exception:
            return None

    def parse_time(self, line):
        match = re.search(r"time=\s*([\d:.]+)", line)
        if match:
            t = match.group(1)
            parts = t.split(":")
            if len(parts) == 3:
                try:
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except ValueError:
                    return None
        return None

    def format_time(self, seconds):
        if seconds is None or seconds < 0:
            return "--:--"
        return str(timedelta(seconds=int(seconds)))

    def build_cmd(self, input_path, output_path):
        max_w = 1280 if self.res_720.get() else 1920
        preset = "ultrafast" if self.fast_mode.get() else "fast"
        crf = "26" if self.fast_mode.get() else "23"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale='min({max_w},iw)':-2",
            "-c:v", "libx264",
            "-profile:v", "baseline",
            "-level", "3.1",
            "-preset", preset,
            "-crf", crf,
            "-bf", "0",
            "-g", "60",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
        ]

        if self.audio_only_copy.get():
            cmd += ["-c:a", "copy"]
        else:
            cmd += ["-c:a", "aac", "-b:a", "128k"]

        cmd.append(output_path)
        return cmd

    # ---------- Conversion flow ----------
    def start_conversion(self):
        if not self.files:
            return
        self.is_running = True
        self.current_file_index = 0
        self.update_button_state()
        self.log("=" * 55, TEXT_MUTED)
        self.log("STARTING CONVERSION…", WARNING)
        threading.Thread(target=self.process_all, daemon=True).start()

    def process_all(self):
        total_files = len(self.files)
        for idx, file_path in enumerate(self.files, 1):
            self.current_file_index = idx
            self.root.after(0, lambda i=idx, t=total_files: self.lbl_current.config(
                text=f"Processing {i}/{t}: {os.path.basename(self.files[i - 1])}"
            ))

            duration = self.get_video_duration(file_path)
            if duration is None:
                self.root.after(0, lambda f=file_path: self.log(
                    f"⚠️  Could not read duration: {os.path.basename(f)}", WARNING))
                duration = 0

            name, _ = os.path.splitext(os.path.basename(file_path))

            if self.output_folder:
                output_path = os.path.join(self.output_folder, f"{name}_small.mp4")
            else:
                dir_name = os.path.dirname(file_path)
                output_path = os.path.join(dir_name, f"{name}_small_version.mp4")

            self.root.after(0, lambda f=os.path.basename(file_path),
                                       o=os.path.basename(output_path), i=idx, t=total_files:
                            self.log(f"\n📄 [{i}/{t}] {f}  →  {o}", "#64B5F6"))

            cmd = self.build_cmd(file_path, output_path)
            self.log(" ".join(cmd), "#555555")

            self.run_ffmpeg(cmd, duration, idx, total_files)

        self.root.after(0, self.conversion_finished)

    def run_ffmpeg(self, cmd, duration, file_idx, total_files):
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True, startupinfo=startupinfo,
            encoding="utf-8", errors="ignore"
        )

        self.start_time = None
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            self.root.after(0, lambda l=line: self.log(l, SUCCESS))

            current_time = self.parse_time(line)
            if current_time is not None and duration > 0:
                if self.start_time is None:
                    self.start_time = time.time()

                pct = min(100.0, (current_time / duration) * 100)
                global_pct = ((file_idx - 1) / total_files * 100) + (pct / total_files)

                elapsed = time.time() - self.start_time
                if current_time > 0:
                    total_estimated = elapsed / (current_time / duration)
                    remaining = total_estimated - elapsed
                else:
                    remaining = None

                self.root.after(0, lambda gp=global_pct, r=remaining: self.update_progress(gp, r))

        process.wait()

    def update_progress(self, pct, remaining):
        self.progress["value"] = pct
        self.lbl_percent.config(text=f"{pct:.1f}%")
        self.lbl_eta.config(text=f"ETA: {self.format_time(remaining)}")

    def conversion_finished(self):
        self.is_running = False
        self.progress["value"] = 100
        self.lbl_percent.config(text="100%")
        self.lbl_eta.config(text="ETA: 00:00")
        self.lbl_current.config(text="✅ Conversion completed")
        self.log("\n🎉  ALL FILES CONVERTED!", GREEN)
        self.update_button_state()
        messagebox.showinfo("Done",
                            f"{len(self.files)} file(s) converted.\nCheck the output folder.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FFmpegApp(root)
    root.mainloop()
