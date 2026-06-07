# ⏱ FlowBreak

Desktop timer for active breaks with exercise guidance, analytics, water reminders, and ambient sounds.

## Features

- **Smart timer**: Configurable work/break intervals with normal and Pomodoro modes
- **9 guided exercises**: Neck, shoulders, back, eyes, hands, squats, breathing, walking, power posture
- **Circular countdown**: Modern animated timer with progress arc (green → yellow → red)
- **System tray**: Minimizes to tray with live countdown tooltip and context menu
- **Rich statistics**: Daily completion/skip tracking, streak counter, 7-day bar chart
- **Water reminder**: Periodic hydration notifications with configurable interval
- **Ambient sounds**: Rain or nature sounds during breaks (procedurally generated)
- **Do Not Disturb**: Auto-snoozes breaks during fullscreen or presentation mode
- **Dark/Light themes**: Two complete themes
- **Spanish/English**: Full i18n with both languages
- **Profiles**: Multiple named configuration profiles
- **Motivational phrases**: Encouraging messages after each completed break

## Requirements

- Python 3.10+ (with tkinter, included by default on Windows)

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python pausa_activa.py
```

## Build standalone .exe

```bash
pip install pyinstaller
pyinstaller FlowBreak.spec
```

Or use the included Inno Setup script (`setup_flowbreak.iss`) for a professional installer.

## Configuration

Available from the app's Settings panel (gear icon):

| Setting | Default | Description |
|---|---|---|
| Interval | 45 min | Minutes between breaks |
| Break duration | 5 min | How long each break lasts |
| Start time | 08:00 | Don't disturb before this time |
| End time | 18:00 | Don't disturb after this time |
| Daily goal | 6 breaks | Target breaks per day |
| Snooze | 10 min | Postpone duration |
| Mode | Normal | Normal or Pomodoro (25/5) |

## Tech stack

- Python + CustomTkinter (modern UI)
- pystray (system tray)
- PIL/Pillow (icon generation)
- winotify (Windows notifications)
- PyInstaller (build distribution)

## License

MIT
