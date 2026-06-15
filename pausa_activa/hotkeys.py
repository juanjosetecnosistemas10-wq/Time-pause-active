"""Global hotkey manager for FlowBreak."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional

from pausa_activa.constants import log

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE: bool = True
except ImportError:
    PYNPUT_AVAILABLE = False


class HotkeyManager:
    def __init__(self) -> None:
        self._listener: Optional[Any] = None
        self._hotkeys: Dict[str, dict[str, Any]] = {}
        self._enabled: bool = True
        self._lock = threading.Lock()

    def register(self, name: str, combo: str, callback: Callable[[], None]) -> None:
        """Register a hotkey. Combo format: '<ctrl>+<alt>+b'"""
        with self._lock:
            self._hotkeys[name] = {"combo": combo, "callback": callback}
        log.debug("Registered hotkey: %s -> %s", name, combo)

    def unregister(self, name: str) -> None:
        with self._lock:
            self._hotkeys.pop(name, None)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def start(self) -> None:
        if not PYNPUT_AVAILABLE:
            log.warning("pynput no disponible, hotkeys globales desactivadas")
            return
        if self._listener and self._listener.is_alive():
            return

        def wrap_callback(cb: Callable[[], None]) -> Callable[[], None]:
            def wrapper() -> None:
                if self._enabled:
                    try:
                        cb()
                    except Exception as e:
                        log.exception("Error executing hotkey: %s", e)
            return wrapper

        mapping = {}
        with self._lock:
            for entry in self._hotkeys.values():
                mapping[entry["combo"]] = wrap_callback(entry["callback"])

        self._listener = keyboard.GlobalHotKeys(mapping)
        self._listener.daemon = True
        self._listener.start()
        log.info("Global hotkeys started using pynput.keyboard.GlobalHotKeys")

    def stop(self) -> None:
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                log.debug("Error stopping hotkey listener")
            self._listener = None
            log.info("Global hotkeys stopped")


DEFAULT_HOTKEYS = {
    "break_now": "<ctrl>+<alt>+b",
    "snooze": "<ctrl>+<alt>+s",
    "pause_resume": "<ctrl>+<alt>+p",
    "show_hide": "<ctrl>+<alt>+h",
    "quit": "<ctrl>+<alt>+q",
}


def create_default_manager(
    on_break_now: Callable[[], None],
    on_snooze: Callable[[], None],
    on_pause_resume: Callable[[], None],
    on_show_hide: Callable[[], None],
    on_quit: Callable[[], None],
) -> HotkeyManager:
    mgr = HotkeyManager()
    mgr.register("break_now", DEFAULT_HOTKEYS["break_now"], on_break_now)
    mgr.register("snooze", DEFAULT_HOTKEYS["snooze"], on_snooze)
    mgr.register("pause_resume", DEFAULT_HOTKEYS["pause_resume"], on_pause_resume)
    mgr.register("show_hide", DEFAULT_HOTKEYS["show_hide"], on_show_hide)
    mgr.register("quit", DEFAULT_HOTKEYS["quit"], on_quit)
    return mgr