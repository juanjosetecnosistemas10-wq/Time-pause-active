"""Achievements manager and window."""

from __future__ import annotations

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.windows._base import CenteredWindow

ACHIEVEMENTS = [
    {"id": "primera_pausa", "key": "logro_primera_pausa", "icon": "🎯", "cond": lambda s, *_: s["completadas"] >= 1},
    {"id": "5_pausas", "key": "logro_5_pausas", "icon": "⭐", "cond": lambda s, *_: s["completadas"] >= 5},
    {"id": "10_pausas", "key": "logro_10_pausas", "icon": "🏆", "cond": lambda s, *_: s["completadas"] >= 10},
    {"id": "racha_3", "key": "logro_racha_3", "icon": "🔥", "cond": lambda s, *_: s.get("racha", 0) >= 3},
    {"id": "racha_7", "key": "logro_racha_7", "icon": "💎", "cond": lambda s, *_: s.get("racha", 0) >= 7},
    {"id": "racha_30", "key": "logro_racha_30", "icon": "👑", "cond": lambda s, *_: s.get("racha", 0) >= 30},
    {"id": "early_bird", "key": "logro_early_bird", "icon": "🌅",
     "cond": lambda s, h, *_: any(e.get("hora", "")[:2] < "09" for e in h.get("historial", [])) if h else False},
    {"id": "night_owl", "key": "logro_night_owl", "icon": "🦉",
     "cond": lambda s, h, *_: any(e.get("hora", "")[:2] >= "20" for e in h.get("historial", [])) if h else False},
]


def check_achievements(stats: dict, history: dict, shown: list) -> list[dict]:
    new_achievements = []
    for ach in ACHIEVEMENTS:
        if ach["id"] not in shown:
            try:
                if ach["cond"](stats, history):
                    new_achievements.append(ach)
                    shown.append(ach["id"])
            except Exception:
                pass
    return new_achievements


class AchievementsWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, stats: dict, shown: list) -> None:
        super().__init__(parent)
        self.title(_("logros"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("360x500")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="🏆", font=("Segoe UI Emoji", 40), text_color=C.TEXT).pack(pady=(16, 0))
        ctk.CTkLabel(main, text=_("logros"), font=F(16, "bold"), text_color=C.TEXT).pack(pady=(4, 12))

        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12)

        for ach in ACHIEVEMENTS:
            unlocked = ach["id"] in shown
            card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=12,
                                border_width=1, border_color=C.CARD_BORDER if unlocked else C.BG3)
            card.pack(fill="x", pady=4)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)
            icon = ach["icon"] if unlocked else "🔒"
            ctk.CTkLabel(row, text=icon, font=F(18), text_color=C.TEXT).pack(side="left", padx=(0, 10))
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(text_frame, text=_(ach["key"]), font=F(10, "bold" if unlocked else ""),
                         text_color=C.TEXT if unlocked else C.TEXT_MUTED, anchor="w").pack(fill="x")
            status = "✅ Desbloqueado" if unlocked else "⏳ Pendiente"
            ctk.CTkLabel(text_frame, text=status, font=F(8),
                         text_color=C.GREEN if unlocked else C.TEXT_MUTED, anchor="w").pack(fill="x")

        ctk.CTkButton(main, text=_("cerrar"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=120, height=34,
                      command=self.destroy).pack(pady=12)
        self.center()
