"""Global hotkey manager for FlowBreak."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from pausa_activa.constants import log

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE: bool = True
except ImportError:
    PYNPUT_AVAILABLE = False


class HotkeyManager:
    def __init__(self) -> None:
        self._listener: Any = None
        self._hotkeys: dict[str, dict[str, Any]] = {}
        self._enabled: bool = True
        self._lock = threading.Lock()

    def register(self, name: str, combo: str, callback: Callable[[], None]) -> None:
        """Register a hotkey. Combo format: '<ctrl>+<alt>+b'"""
        with self._lock:
            self._hotkeys[name] = {"combo": combo, "callback": callback}

    def unregister(self, name: str) -> None:
        with self._lock:
            self._hotkeys.pop(name, None)

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled

    def start(self) -> None:
        if not PYNPUT_AVAILABLE:
            log.warning("pynput no disponible, hotkeys globales desactivadas")
            return
        with self._lock:
            if self._listener:
                return
            self._listener = self._build_listener()
        log.info("Global hotkeys started using pynput.keyboard.GlobalHotKeys")

    def stop(self) -> None:
        listener = None
        with self._lock:
            listener = self._listener
            self._listener = None
        if listener:
            try:
                listener.stop()
            except Exception:
                log.debug("Error stopping hotkey listener")
        log.info("Global hotkeys stopped")

    def reload(self) -> None:
        """Rebuild the listener with the current hotkey mapping."""
        with self._lock:
            old = self._listener
            self._listener = None
        if old:
            try:
                old.stop()
            except Exception:
                pass
        with self._lock:
            self._listener = self._build_listener()
        log.debug("Hotkey listener reloaded")

    def _build_listener(self) -> Any:
        def wrap_callback(cb: Callable[[], None]) -> Callable[[], None]:
            def wrapper() -> None:
                with self._lock:
                    enabled = self._enabled
                if enabled:
                    try:
                        cb()
                    except Exception as e:
                        log.exception("Error executing hotkey: %s", e)
            return wrapper

        mapping = {}
        for entry in self._hotkeys.values():
            mapping[entry["combo"]] = wrap_callback(entry["callback"])

        listener = keyboard.GlobalHotKeys(mapping)
        listener.daemon = True
        listener.start()
        return listener


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
