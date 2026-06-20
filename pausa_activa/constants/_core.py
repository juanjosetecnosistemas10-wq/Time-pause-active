from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import os
from typing import Any


def center_window(win: Any) -> None:
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    if w < 100:
        w = 400
    if h < 100:
        h = 500
    try:
        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        pt = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        monitor = user32.MonitorFromPoint(pt, 0x00000002)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(monitor, ctypes.byref(info))
        mw = info.rcMonitor.right - info.rcMonitor.left
        mh = info.rcMonitor.bottom - info.rcMonitor.top
        x = info.rcMonitor.left + (mw - w) // 2
        y = info.rcMonitor.top + (mh - h) // 2
    except Exception:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
    win.geometry(f"+{x}+{y}")


APP_NAME: str = "FlowBreak"
APP_DISPLAY: str = "FlowBreak"
__version__: str = "2.0.3"
UPDATER_REPO: str = "juanjosetecnosistemas10-wq/Time-pause-active"


def darken_color(hex_color: str, amount: int = 30) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{max(0, r - amount):02x}{max(0, g - amount):02x}{max(0, b - amount):02x}"


INSTALL_DIR_REG: str = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FlowBreak"


LOG_DIR: str = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
    APP_NAME,
    "logs",
)
os.makedirs(LOG_DIR, exist_ok=True)

_log_initialized: bool = False


def _ensure_logging() -> None:
    global _log_initialized
    if _log_initialized:
        return
    _log_initialized = True
    _file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, "flowbreak.log"),
        encoding="utf-8",
    )
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            _file_handler,
        ],
    )


log = logging.getLogger("FlowBreak")
_ensure_logging()
