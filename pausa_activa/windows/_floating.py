"""Floating Timer (mini widget)."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import Canvas
from typing import Any

import customtkinter as ctk

from pausa_activa.constants import C, F


class FloatingTimer(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, get_remaining: Callable[[], int],
                 get_paused: Callable[[], bool], on_click: Callable[[], None]) -> None:
        super().__init__(parent)
        self._get_remaining = get_remaining
        self._get_paused = get_paused
        self._on_click = on_click
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1A1A2E")
        self.resizable(False, False)
        self.geometry("140x50")
        self.attributes("-alpha", 0.85)

        self._canvas = Canvas(self, width=140, height=50, bg="#1A1A2E", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._drag_data = {"x": 0, "y": 0, "dragged": False}
        self._canvas.bind("<ButtonPress-1>", self._start_drag)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_click_release)

        self._update_display()

    def _start_drag(self, event: Any) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["dragged"] = False

    def _on_drag(self, event: Any) -> None:
        self._drag_data["dragged"] = True
        x = self.winfo_x() + event.x - self._drag_data["x"]
        y = self.winfo_y() + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def _on_click_release(self, event: Any) -> None:
        if not self._drag_data.get("dragged", False):
            self._on_click()

    def _update_display(self) -> None:
        try:
            if not self.winfo_exists():
                return
            remaining = self._get_remaining()
            paused = self._get_paused()
            mins, secs = divmod(max(0, remaining), 60)
            time_str = f"{mins:02d}:{secs:02d}"
            color = C.YELLOW if paused else C.GREEN
            self._canvas.delete("all")
            self._canvas.create_text(70, 15, text=time_str, font=F(16, "bold"), fill=color, tags="time")
            status = "⏸ PAUSED" if paused else "▶ RUNNING"
            self._canvas.create_text(70, 37, text=status, font=F(8), fill=C.TEXT_DIM, tags="status")
            self.after(500, self._update_display)
        except Exception:
            pass

    def destroy(self) -> None:
        super().destroy()
