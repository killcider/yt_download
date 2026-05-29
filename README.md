# YT Download

Dark desktop app for downloading one or more YouTube links.

The app shows Korean UI on Korean systems and English UI everywhere else.

## Windows Installation

If you already have the installer:

1. Download `YT-Download-Setup.exe`.
2. Double-click `YT-Download-Setup.exe`.
3. Follow the installer.
4. Open `YT Download` from the Start menu or desktop shortcut.

The installed app includes the required Python runtime and libraries. You do not need
to install Python, uv, PySide6, yt-dlp, or other dependencies separately.

## How to Add Links

Paste one YouTube link per line.

```text
https://www.youtube.com/watch?v=...
https://youtu.be/...
```

Press Enter to move to the next line and add another video link.

## Quality Options

The app supports these quality choices:

- `720p`
- `1080p`
- `4K (2160p)`
- `Best available`

YouTube often provides 1080p and 4K as separate video/audio streams. The app bundles
ffmpeg through `imageio-ffmpeg`, so users do not need to install ffmpeg separately.

The selected quality is a maximum target. For example, `4K (2160p)` downloads up to
4K when the video actually has a 4K source; otherwise yt-dlp falls back to the best
available lower quality.

## Ubuntu / Linux Usage

Install dependencies and run the app:

```bash
uv sync --all-groups
uv run yt-download
```

After the first setup, you can usually run:

```bash
uv run yt-download
```

Build and test a Linux executable:

```bash
uv run pyinstaller packaging/yt-download.spec --noconfirm
./dist/'YT Download'/'YT Download'
```

The output is created under `dist/`.

## Creating the Windows Installer

### Option 1: GitHub Actions

You can create `YT-Download-Setup.exe` without installing uv or Inno Setup on your PC.

1. Open the GitHub repository.
2. Go to `Actions`.
3. Select `Build Windows Installer`.
4. Click `Run workflow`.
5. Open the completed workflow run.
6. Download the `YT-Download-Setup` artifact.

The artifact contains:

```text
YT-Download-Setup.exe
```

### Option 2: Local Windows Build

Windows installers should be built on Windows. From a Windows PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-windows-installer.ps1
```

The final installer is created here:

```text
dist/installer/YT-Download-Setup.exe
```

Only the PC creating the installer needs:

- uv
- Inno Setup

People installing `YT-Download-Setup.exe` do not need these tools.

## Download Folder Behavior

The app defaults to:

1. The system Downloads folder when it exists.
2. `~/Downloads` or `~/다운로드` when present.
3. The home directory as a fallback.

## Stack

- Python
- uv
- PySide6
- yt-dlp
- PyInstaller
- Inno Setup for Windows installer builds

## License

This project is licensed under the PolyForm Noncommercial License 1.0.0.

You may use, copy, modify, and distribute this software for noncommercial purposes only.

Commercial use is prohibited without explicit written permission from the copyright holder.
For commercial licensing, contact: k970702@gmail.com
