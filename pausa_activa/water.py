"""Recordatorio de hidratación."""

from __future__ import annotations

import threading
import time
import winsound
from collections.abc import Callable
from typing import Any

from pausa_activa.constants import _, log
from pausa_activa.notifications import send_win_notification


class WaterReminder:
    def __init__(self, cfg_getter: Callable[[], dict[str, Any]], on_notify: Callable[[], None] | None = None) -> None:
        self._cfg_getter: Callable[[], dict[str, Any]] = cfg_getter
        self._on_notify: Callable[[], None] | None = on_notify
        self._stop: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock: threading.Lock = threading.Lock()

    def start(self) -> None:
        self._stop.clear()
        t = threading.Thread(target=self._loop, daemon=True)
        with self._lock:
            self._thread = t
        t.start()

    def stop(self) -> None:
        self._stop.set()

    def restart(self) -> None:
        with self._lock:
            self._stop.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2)
            self._thread = None
            self._stop.clear()
            t = threading.Thread(target=self._loop, daemon=True)
            self._thread = t
            t.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                cfg: dict[str, Any] = self._cfg_getter()
                if not cfg.get("agua_activo", True):
                    if self._stop.wait(60):
                        return
                    continue
                mins: int = max(1, cfg.get("agua_min", 30))
                deadline = time.monotonic() + mins * 60
                while time.monotonic() < deadline:
                    if self._stop.wait(1):
                        return
                if self._stop.is_set():
                    return
                send_win_notification(
                    _("water_reminder"),
                    _("drink_water_body"),
                    sound=cfg.get("notificacion_sonido", "default"),
                    duration=cfg.get("notificacion_duracion", "short"),
                )
                if self._on_notify:
                    try:
                        self._on_notify()
                    except Exception:
                        pass
                try:
                    threading.Thread(target=lambda: (winsound.Beep(440, 200), time.sleep(0.1), winsound.Beep(550, 200)), daemon=True).start()
                except Exception:
                    pass
            except Exception as exc:
                log.exception("Error en WaterReminder: %s", exc)
                if self._stop.wait(60):
                    return
