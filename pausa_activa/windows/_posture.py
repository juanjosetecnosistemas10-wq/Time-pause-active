"""Posture Reminder."""

from __future__ import annotations

from typing import Any

from pausa_activa.windows._base import get_audio_manager
from pausa_activa.windows._toast import toast


class PostureReminder:
    def __init__(self, app: Any) -> None:
        self._app = app
        self._job: str | None = None
        self._active = False

    def start(self, interval_min: int) -> None:
        self.stop()
        self._active = True
        self._schedule(interval_min)

    def stop(self) -> None:
        self._active = False
        if self._job:
            try:
                self._app.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _schedule(self, interval_min: int) -> None:
        if not self._active:
            return
        ms = interval_min * 60 * 1000
        self._job = self._app.after(ms, self._notify)

    def _notify(self) -> None:
        if not self._active:
            return
        toast("🧘 Postura", "Corrige tu postura 🧍", kind="info", duration=5000)
        try:
            get_audio_manager().play_alert()
        except Exception:
            pass
        self._schedule(self._app.cfg.get("postura_intervalo_min", 20))
