"""Compact Window (mini mode)."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from pausa_activa.constants import C, F
from pausa_activa.windows._base import CenteredWindow


class CompactWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, get_remaining: Callable[[], int],
                 get_paused: Callable[[], bool], on_toggle: Callable[[], None],
                 on_next: Callable[[], None], on_skip: Callable[[], None]) -> None:
        super().__init__(parent)
        self._get_remaining = get_remaining
        self._get_paused = get_paused
        self._on_toggle = on_toggle
        self._on_next = on_next
        self._on_skip = on_skip
        self.title("FlowBreak Compact")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("260x100")
        self.resizable(False, False)

        main = ctk.CTkFrame(self, fg_color=C.CARD, corner_radius=12)
        main.pack(fill="both", expand=True, padx=6, pady=6)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(6, 0))
        self._time_label = ctk.CTkLabel(top, text="00:00", font=F(20, "bold"), text_color=C.TEXT)
        self._time_label.pack(side="left")
        self._status_label = ctk.CTkLabel(top, text="▶", font=F(14), text_color=C.GREEN)
        self._status_label.pack(side="right")

        btns = ctk.CTkFrame(main, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=(4, 6))
        ctk.CTkButton(btns, text="⏸/▶", width=40, height=28, font=F(9),
                      fg_color=C.BG3, text_color=C.TEXT, corner_radius=8,
                      command=self._on_toggle).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="⏭", width=40, height=28, font=F(9),
                      fg_color=C.BG3, text_color=C.TEXT, corner_radius=8,
                      command=self._on_next).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="✕", width=40, height=28, font=F(9),
                      fg_color="#EF4444", text_color="#FFFFFF", corner_radius=8,
                      command=self._on_skip).pack(side="right", padx=2)
        ctk.CTkButton(btns, text="🔍", width=40, height=28, font=F(9),
                      fg_color=C.BG3, text_color=C.TEXT, corner_radius=8,
                      command=self._expand).pack(side="right", padx=2)

        self._update_display()

    def _expand(self) -> None:
        self._on_next()

    def _update_display(self) -> None:
        try:
            if not self.winfo_exists():
                return
            remaining = self._get_remaining()
            paused = self._get_paused()
            mins, secs = divmod(max(0, remaining), 60)
            self._time_label.configure(text=f"{mins:02d}:{secs:02d}")
            self._status_label.configure(text="⏸" if paused else "▶",
                                         text_color=C.YELLOW if paused else C.GREEN)
            self.after(500, self._update_display)
        except Exception:
            pass
