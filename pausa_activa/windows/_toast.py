"""Toast notification window and helper function."""

from __future__ import annotations

import customtkinter as ctk

from pausa_activa.constants import C, F


class ToastNotification(ctk.CTkToplevel):
    _counter: int = 0

    def __init__(
        self,
        title: str,
        message: str,
        kind: str = "info",
        duration: int = 3000,
        parent: ctk.CTkBaseClass | None = None,
    ) -> None:
        super().__init__(parent or ctk.CTk())
        ToastNotification._counter += 1
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=C.CARD)
        self.resizable(False, False)

        colors = {"info": C.ACCENT, "exito": C.GREEN, "advertencia": C.YELLOW, "error": "#EF4444"}
        accent = colors.get(kind, C.ACCENT)

        bar = ctk.CTkFrame(self, fg_color=accent, width=4, height=60)
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(8, 14), pady=8)

        icon_map = {"info": "ℹ️", "exito": "✅", "advertencia": "⚠️", "error": "❌"}
        ctk.CTkLabel(
            content, text=f"{icon_map.get(kind, 'ℹ️')}  {title}",
            font=F(10, "bold"), text_color=C.TEXT, anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            content, text=message, font=F(9),
            text_color=C.TEXT_DIM, anchor="w", wraplength=280,
        ).pack(fill="x")

        w, h = 340, 70
        screen_w = self.winfo_screenwidth()
        offset = (ToastNotification._counter % 5) * (h + 8)
        self.geometry(f"{w}x{h}+{screen_w - w - 20}+{20 + offset}")
        self.attributes("-alpha", 0.0)
        for i in range(1, 7):
            self.after(i * 20, lambda v=i / 6: self.attributes("-alpha", min(v, 1.0)))
        self.after(duration, self._close)

    def _close(self) -> None:
        for i in range(6, 0, -1):
            self.after((6 - i) * 20, lambda v=i / 6: self.attributes("-alpha", v))
        self.after(150, self.destroy)


def toast(title: str, message: str, kind: str = "info", duration: int = 3000) -> None:
    ToastNotification(title, message, kind=kind, duration=duration)
