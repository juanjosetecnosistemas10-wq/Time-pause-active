"""Recordatorio de hidratación."""

from __future__ import annotations

import threading
import time
import winsound
from typing import Any, Callable

from pausa_activa.notifications import send_win_notification


class WaterReminder:
    def __init__(self, cfg_getter: Callable[[], dict[str, Any]]) -> None:
        self._cfg_getter: Callable[[], dict[str, Any]] = cfg_getter
        self._stop: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def restart(self) -> None:
        self.stop()
        self._thread = None
        self.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            cfg: dict[str, Any] = self._cfg_getter()
            if not cfg.get("agua_activo", True):
                if self._stop.wait(60):
                    return
                continue
            mins: int = max(1, cfg.get("agua_min", 30))
            remaining_sec: int = mins * 60
            while remaining_sec > 0:
                if self._stop.wait(1):
                    return
                remaining_sec -= 1
            if self._stop.is_set():
                return
            send_win_notification(
                "💧 Hidratación",
                "¡Recuerda tomar agua!",
                sound=cfg.get("notificacion_sonido", "default"),
                duration=cfg.get("notificacion_duracion", "short"),
            )
            try:
                winsound.Beep(440, 200)
                time.sleep(0.1)
                winsound.Beep(550, 200)
            except Exception:
                pass
