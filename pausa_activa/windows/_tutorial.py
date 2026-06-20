"""Tutorial Window (improved onboarding)."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.windows._base import CenteredWindow


class TutorialWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, on_complete: Callable[[], None]) -> None:
        super().__init__(parent)
        self._on_complete = on_complete
        self._step = 0
        self.title("Tutorial")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("440x520")

        self._main = ctk.CTkFrame(self, fg_color=C.BG)
        self._main.pack(fill="both", expand=True)
        self._show_step()
        self.center()

    def _show_step(self) -> None:
        for w in self._main.winfo_children():
            w.destroy()

        steps = [
            ("⚙️", _("tutorial_paso1_titulo"), _("tutorial_paso1_desc"),
             [("⏱", _("tutorial_feat_intervalo"), _("tutorial_feat_intervalo_desc")),
              ("🏃", _("tutorial_feat_ejercicios"), _("tutorial_feat_ejercicios_desc"))]),
            ("🎨", _("tutorial_paso2_titulo"), _("tutorial_paso2_desc"),
             [("🎨", _("tutorial_feat_temas"), _("tutorial_feat_temas_desc")),
              ("🔊", _("tutorial_feat_sonidos"), _("tutorial_feat_sonidos_desc"))]),
            ("🚀", _("tutorial_paso3_titulo"), _("tutorial_paso3_desc"),
             [("🏆", _("tutorial_feat_logros"), _("tutorial_feat_logros_desc")),
              ("📊", _("tutorial_feat_stats"), _("tutorial_feat_stats_desc"))]),
        ]

        icon, title, desc, features = steps[self._step]

        ctk.CTkLabel(self._main, text=icon, font=("Segoe UI Emoji", 48),
                     text_color=C.TEXT).pack(pady=(24, 0))
        ctk.CTkLabel(self._main, text=title, font=F(18, "bold"),
                     text_color=C.TEXT).pack(pady=(8, 4))
        ctk.CTkLabel(self._main, text=desc, font=F(11),
                     text_color=C.TEXT_DIM, wraplength=360, justify="center").pack(pady=(0, 16))

        for feat_icon, feat_title, feat_desc in features:
            feat_card = ctk.CTkFrame(self._main, fg_color=C.CARD, corner_radius=12,
                                     border_width=1, border_color=C.CARD_BORDER)
            feat_card.pack(fill="x", padx=24, pady=3)
            row = ctk.CTkFrame(feat_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)
            ctk.CTkLabel(row, text=feat_icon, font=F(16), text_color=C.TEXT).pack(side="left", padx=(0, 10))
            tf = ctk.CTkFrame(row, fg_color="transparent")
            tf.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(tf, text=feat_title, font=F(10, "bold"), text_color=C.TEXT, anchor="w").pack(fill="x")
            ctk.CTkLabel(tf, text=feat_desc, font=F(8), text_color=C.TEXT_DIM, anchor="w").pack(fill="x")

        btns = ctk.CTkFrame(self._main, fg_color="transparent")
        btns.pack(pady=20)
        if self._step > 0:
            ctk.CTkButton(btns, text=_("back_step"), fg_color=C.BG3, text_color=C.TEXT,
                          font=F(10), corner_radius=12, width=100, height=34,
                          command=self._prev).pack(side="left", padx=4)
        if self._step < len(steps) - 1:
            ctk.CTkButton(btns, text=_("next_step"), fg_color=C.ACCENT, text_color="#FFFFFF",
                          font=F(10, "bold"), corner_radius=12, width=120, height=34,
                          command=self._next).pack(side="left", padx=4)
        else:
            ctk.CTkButton(btns, text=_("tutorial_completar"), fg_color=C.GREEN, text_color="#FFFFFF",
                          font=F(10, "bold"), corner_radius=12, width=120, height=34,
                          command=self._complete).pack(side="left", padx=4)
        ctk.CTkButton(btns, text=_("tutorial_saltar"), fg_color="transparent", text_color=C.TEXT_MUTED,
                      font=F(9), corner_radius=12, width=100, height=34,
                      command=self._complete).pack(side="left", padx=4)

    def _next(self) -> None:
        self._step += 1
        self._show_step()

    def _prev(self) -> None:
        self._step -= 1
        self._show_step()

    def _complete(self) -> None:
        self._on_complete()
        self.destroy()
