"""WelcomeWindow — first-run onboarding."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from pausa_activa.constants import EJERCICIOS, C, F, _
from pausa_activa.windows._base import CenteredWindow, _card, _checkbox, _entry


class WelcomeWindow(CenteredWindow):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        cfg: dict[str, Any],
        on_finish: Callable[[dict[str, Any]], None],
        app_path: str,
        config_saver: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.cfg: dict[str, Any] = dict(cfg)
        self.on_finish: Callable[[dict[str, Any]], None] = on_finish
        self._app_path: str = app_path
        self._config_saver: Callable[[dict[str, Any]], None] | None = config_saver
        self.step: int = 0
        self.title(_("welcome_title"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self._build()
        self.center()

    def _build(self) -> None:
        self._frame = ctk.CTkFrame(self, fg_color="transparent")
        self._frame.pack(fill="both", expand=True)
        self._show_step()

    def _clear(self) -> None:
        for w in self._frame.winfo_children():
            w.destroy()

    def _show_step(self) -> None:
        self._clear()
        if self.step == 0:
            self._step_bienvenida()
        elif self.step == 1:
            self._step_config()
        elif self.step == 2:
            self._step_listo()

    def _dots(self, parent: ctk.CTkFrame) -> None:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=(0, 16))
        for i in range(3):
            color = C.ACCENT if i == self.step else C.TEXT_MUTED
            ctk.CTkLabel(f, text="\u25cf", font=F(12),
                         text_color=color).pack(side="left", padx=4)

    def _step_bienvenida(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_heading"), font=F(16, "bold"),
                     text_color=C.TEXT).pack(pady=(20, 2))
        ctk.CTkLabel(f, text=_("bienvenido"), font=F(10),
                     text_color=C.TEXT_DIM).pack(pady=(0, 14))
        cards: list[tuple[str, str, str]] = [
            ("\u23f1", _("welcome_card1_title"), _("welcome_card1_desc")),
            ("\U0001f3c3", _("welcome_card2_title"), _("welcome_card2_desc")),
            ("\U0001f4a7", _("welcome_card3_title"), _("welcome_card3_desc")),
            ("\U0001f4ca", _("welcome_card4_title"), _("welcome_card4_desc")),
        ]
        for ico, titulo, desc in cards:
            row = _card(f)
            row.pack(fill="x", padx=24, pady=3)
            ctk.CTkLabel(row, text=ico, font=("Segoe UI Emoji", 20),
                         text_color=C.TEXT).pack(side="left", padx=(12, 4), pady=8)
            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", pady=4)
            ctk.CTkLabel(col, text=titulo, font=F(10, "bold"),
                         text_color=C.TEXT, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=desc, font=F(8),
                         text_color=C.TEXT_MUTED, anchor="w", wraplength=280).pack(anchor="w")
        self._dots(f)
        ctk.CTkButton(f, text=_("next_step"), fg_color=C.ACCENT, text_color=C.BG,
                      font=F(10, "bold"), corner_radius=12,
                      command=self._next).pack(pady=(0, 24))

    def _step_config(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_step1_heading"), font=F(14, "bold"),
                     text_color=C.TEXT).pack(pady=(14, 2))
        ctk.CTkLabel(f, text=_("welcome_step1_info"),
                     font=F(9), text_color=C.TEXT_MUTED).pack(pady=(6, 10))

        card_cfg = _card(f)
        card_cfg.pack(fill="x", padx=24)

        self.v_int = ctk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = ctk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = ctk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = ctk.StringVar(value=self.cfg["hora_fin"])
        self.v_meta = ctk.StringVar(value=str(self.cfg["meta_pausas"]))

        def campo(lbl: str, var: ctk.Variable, row: int) -> None:
            ctk.CTkLabel(card_cfg, text=lbl, font=F(10),
                         text_color=C.TEXT_MUTED, anchor="w").grid(row=row, column=0, sticky="w", padx=14, pady=7)
            _entry(card_cfg, var).grid(row=row, column=1, padx=14, pady=7, sticky="e")

        campo(_("welcome_field_intervalo"), self.v_int, 0)
        campo(_("welcome_field_duracion"),   self.v_dur, 1)
        campo(_("welcome_field_hora_ini"),   self.v_ini, 2)
        campo(_("welcome_field_hora_fin"),   self.v_fin, 3)
        campo(_("welcome_field_meta"),       self.v_meta, 4)

        ctk.CTkLabel(f, text=_("welcome_ej_subheading"), font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=28, pady=(6, 4))
        ej_card = _card(f)
        ej_card.pack(fill="x", padx=24)
        self.ej_vars: dict[str, ctk.BooleanVar] = {}
        activos: list[str] = self.cfg.get("ejercicios_activos", [e["id"] for e in EJERCICIOS])
        cols: int = 2
        for i, ej in enumerate(EJERCICIOS):
            v = ctk.BooleanVar(value=ej["id"] in activos)
            self.ej_vars[ej["id"]] = v
            r, c = divmod(i, cols)
            _checkbox(ej_card, f"{ej['icono']} {ej['nombre']}", v).grid(
                row=r, column=c, sticky="w", padx=10, pady=3)

        self.lbl_err = ctk.CTkLabel(f, text="", font=F(9), text_color=C.ACCENT2)
        self.lbl_err.pack()
        self._dots(f)
        bf = ctk.CTkFrame(f, fg_color="transparent")
        bf.pack(pady=(0, 20))
        ctk.CTkButton(bf, text=_("back_step"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(10), corner_radius=12,
                      command=self._prev).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=_("next_step"), fg_color=C.ACCENT, text_color=C.BG,
                      font=F(10, "bold"), corner_radius=12,
                      command=self._save_and_next).pack(side="left", padx=4)

    def _step_listo(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_step2_heading"), font=F(15, "bold"),
                     text_color=C.TEXT).pack(pady=(20, 2))
        ctk.CTkLabel(f, text=_("welcome_step2_info"),
                     font=F(10), text_color=C.TEXT_MUTED).pack(pady=(12, 14))
        resumen = _card(f)
        resumen.pack(fill="x", padx=28)
        items: list[tuple[str, str]] = [
            ("\u23f1 " + _("welcome_summary_intervalo"),  _("welcome_summary_intervalo_val").format(min=self.cfg['intervalo_min'])),
            ("\U0001f550 " + _("welcome_summary_duracion"),  _("welcome_summary_duracion_val").format(min=self.cfg['duracion_pausa_min'])),
            ("\U0001f557 " + _("welcome_summary_horario"),   f"{self.cfg['hora_inicio']} {_('to')} {self.cfg['hora_fin']}"),
            ("\U0001f3af " + _("welcome_summary_meta"),      _("welcome_summary_meta_val").format(meta=self.cfg['meta_pausas'])),
        ]
        for lbl, val in items:
            row = ctk.CTkFrame(resumen, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(row, text=lbl, font=F(10),
                         text_color=C.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=val, font=F(10, "bold"),
                         text_color=C.TEXT).pack(side="right")
        ctk.CTkLabel(f, text=_("welcome_step2_tray_info"),
                     font=F(9), text_color=C.TEXT_MUTED).pack(pady=(10, 4))
        self._dots(f)
        ctk.CTkButton(f, text=_("welcome_start"), fg_color=C.GREEN, text_color=C.BG,
                      font=F(11, "bold"), corner_radius=12,
                      command=self._finish).pack(pady=(0, 28))

    def _next(self) -> None:
        self.step += 1
        self._show_step()
        self.center()

    def _prev(self) -> None:
        self.step -= 1
        self._show_step()
        self.center()

    def _save_and_next(self) -> None:
        try:
            raw = self.v_int.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_intervalo"))
            iv = int(raw)
            raw = self.v_dur.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_duracion"))
            dv = int(raw)
            raw = self.v_meta.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_meta"))
            mv = int(raw)
            for name, val in [("Intervalo", iv), ("Duración", dv), ("Meta", mv)]:
                if val <= 0:
                    raise ValueError(f"{name}: {_('err_valor_positivo')}")
            h0, m0 = map(int, self.v_ini.get().split(":"))
            h1, m1 = map(int, self.v_fin.get().split(":"))
            if not (0 <= h0 < 24 and 0 <= m0 < 60):
                raise ValueError(_("err_hora_inicio"))
            if not (0 <= h1 < 24 and 0 <= m1 < 60):
                raise ValueError(_("err_hora_fin"))
        except ValueError as e:
            self.lbl_err.configure(text=f"⚠ {e}")
            return

        activos = [eid for eid, v in self.ej_vars.items() if v.get()]
        if not activos:
            self.lbl_err.configure(text=_("err_selecciona_ej"))
            return

        self.cfg.update({
            "intervalo_min":      iv,
            "duracion_pausa_min": dv,
            "hora_inicio":        self.v_ini.get(),
            "hora_fin":           self.v_fin.get(),
            "meta_pausas":        mv,
            "ejercicios_activos": activos,
            "primera_vez":        False,
            "no_molestar":        self.cfg.get("no_molestar", True),
            "fin_de_semana":      self.cfg.get("fin_de_semana", False),
            "agua_activo":        self.cfg.get("agua_activo", True),
            "agua_min":           self.cfg.get("agua_min", 30),
            "sonido_ambiente":    self.cfg.get("sonido_ambiente", "ninguno"),
            "posponer_min":       self.cfg.get("posponer_min", 10),
            "sonido":             self.cfg.get("sonido", True),
        })
        if self._config_saver:
            self._config_saver(self.cfg)
        self._next()

    def _finish(self) -> None:
        self.cfg["primera_vez"] = False
        self.destroy()
        self.on_finish(self.cfg)
