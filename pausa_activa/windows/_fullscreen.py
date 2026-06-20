"""Fullscreen Timer (presentations)."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import Canvas

import customtkinter as ctk

from pausa_activa.constants import C, F, _


class FullscreenTimer(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, get_remaining: Callable[[], int],
                 get_paused: Callable[[], bool], on_exit: Callable[[], None]) -> None:
        super().__init__(parent)
        self._get_remaining = get_remaining
        self._get_paused = get_paused
        self._on_exit = on_exit
        self.overrideredirect(True)
        self.configure(fg_color=C.BG)
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self._on_exit())

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        self._canvas = Canvas(self, width=screen_w, height=screen_h, bg=C.BG, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._update_display()

    def _update_display(self) -> None:
        try:
            if not self.winfo_exists():
                return
            remaining = self._get_remaining()
            paused = self._get_paused()
            mins, secs = divmod(max(0, remaining), 60)
            time_str = f"{mins:02d}:{secs:02d}"
            w = self._canvas.winfo_width()
            h = self._canvas.winfo_height()

            self._canvas.delete("all")

            cx, cy = w // 2, h // 2 - 30
            r = min(w, h) // 4

            self._canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                      outline=C.BG3, width=12, tags="ring_bg")

            total = max(1, remaining + 300)
            pct = remaining / total
            self._canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                     start=90, extent=360 * pct,
                                     outline=C.ACCENT, width=12, style="arc", tags="ring_fg")

            color = C.YELLOW if paused else C.ACCENT
            self._canvas.create_text(cx, cy, text=time_str, font=F(48, "bold"), fill=color, tags="time")

            status = "⏸  PAUSED" if paused else "▶  RUNNING"
            self._canvas.create_text(cx, cy + r + 40, text=status, font=F(16), fill=C.TEXT_DIM, tags="status")

            hint = _("fullscreen_salir")
            self._canvas.create_text(cx, h - 40, text=hint, font=F(12), fill=C.TEXT_MUTED, tags="hint")

            self.after(500, self._update_display)
        except Exception:
            pass
