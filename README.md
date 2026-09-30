# ExoPlayer Optimizer Pro

A dark, modern desktop GUI that re-encodes videos with **FFmpeg** so they play smoothly on **Telegram, Android phones and Fire TV** — where high-profile H.264 or unusual codecs often cause buffering, freezing or stuttering.

Built with Python + Tkinter. Batch processing, live progress bar, ETA and a real-time FFmpeg log.

![Made with Python](https://img.shields.io/badge/python-3.8%2B-blue)
![FFmpeg](https://img.shields.io/badge/ffmpeg-required-green)

---

## ✨ Features

- 🎬 **Batch conversion** — queue as many videos as you want and convert them in one go.
- 🚫 **Anti-freeze encoding profile** — forces **H.264 Baseline Profile @ Level 3.1**, no B-frames, 4:2:0 pixel format and `+faststart` — the format combination that ExoPlayer/Telegram handle best.
- ⚡ **Fast mode** — `ultrafast` preset + CRF 26 to finish as soon as possible.
- 📐 **Optional 720p** — caps resolution at 1280 px wide for smaller, phone-friendly files.
- 🔊 **Audio copy option** — skips audio re-encoding if the source is already AAC.
- 📊 **Live progress** — per-file and total progress bar with estimated time remaining.
- 📝 **Real-time FFmpeg log** — watch exactly what the encoder is doing.

## 🖥️ Requirements

| Software | Notes |
|---|---|
| **Python 3.8+** | Tkinter is included by default on Windows/macOS. On some Linux distros install it: `sudo apt install python3-tk` |
| **FFmpeg** | Must be installed **and available in the system `PATH`** (both `ffmpeg` and `ffprobe` are used) |

### Installing FFmpeg

- **Windows** — download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, add the `bin` folder to your `PATH`, then restart the terminal.
- **macOS** — `brew install ffmpeg`
- **Linux** — `sudo apt install ffmpeg` (Debian/Ubuntu) or the equivalent for your distro.

Verify it works:

```bash
ffmpeg -version
ffprobe -version
```

## 🚀 How to run

```bash
python exoplayer_optimizer_pro.py
```

No external Python packages are needed — it only uses the standard library.

## 📖 How to use

1. Click **Select Videos** and pick one or more files (`mp4`, `mkv`, `avi`, `mov`, `webm`, `flv`, `wmv`, `m4v`).
2. *(Optional)* Click **Change folder** to choose where converted files are saved. By default they go next to the original video.
3. Pick your options:
   - **Fast mode** — much quicker encoding, slightly larger files.
   - **Force 720p** — smaller files, great for phones.
   - **Copy audio without re-encoding** — faster, only if the audio is already AAC/compatible.
4. Press **START CONVERSION** and watch the progress bar, ETA and live log.
5. Converted files are saved with a `_small` / `_small_version` suffix so the originals are never touched.

## ⚙️ What does it encode to?

| Setting | Value |
|---|---|
| Video codec | H.264 (`libx264`) |
| Profile / Level | Baseline @ 3.1 (maximum device compatibility) |
| B-frames | Disabled (`-bf 0`) |
| Pixel format | `yuv420p` |
| Keyframe interval | 60 frames |
| MP4 flag | `+faststart` (moov atom at the front → instant playback) |
| Audio | AAC 128k (or copied if selected) |
| Resolution | Capped at 1080p, or 720p if that option is enabled |

## 📂 Project structure

```
exoplayer_optimizer_pro.py   # The whole app (single file)
README.md
```

## 📄 License

MIT — free to use, modify and distribute.
