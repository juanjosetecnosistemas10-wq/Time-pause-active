"""ConfigWindow with CTkTabview."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from pausa_activa.constants import (
    EJERCICIOS,
    C,
    F,
    _,
    set_idioma,
    set_theme,
)
from pausa_activa.windows._achievements import ACHIEVEMENTS
from pausa_activa.windows._base import (
    CenteredWindow,
    _card,
    _checkbox,
    _entry,
    _radio,
    get_autoarranque,
    set_autoarranque,
)


class ConfigWindow(CenteredWindow):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        cfg: dict[str, Any],
        on_save: Callable[[dict[str, Any]], None],
        app_path: str,
        profiles: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.cfg: dict[str, Any] = dict(cfg)
        self.on_save: Callable[[dict[str, Any]], None] = on_save
        self._app_path: str = app_path
        self._profiles: list[str] = profiles or ["default"]
        self.title(_("configuracion"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("480x720")
        self._build()
        self.center()

    def _field(self, parent: ctk.CTkFrame, label: str, var: ctk.Variable, row: int) -> None:
        ctk.CTkLabel(parent, text=label, font=F(10),
                     text_color=C.TEXT_MUTED, anchor="w").pack(
            side="left", padx=16, pady=8)
        _entry(parent, var).pack(
            side="right", padx=16, pady=8)

    def _build(self) -> None:
        self.configure(fg_color=C.BG)

        ctk.CTkLabel(self, text="⚙️  " + _("configuracion"), font=F(16, "bold"),
                     text_color=C.TEXT).pack(pady=(12, 4))

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(container, fg_color="transparent",
                                       segmented_button_fg_color=C.BG3,
                                       segmented_button_selected_color=C.ACCENT,
                                       segmented_button_selected_hover_color=C.ACCENT,
                                       segmented_button_unselected_color=C.BG4,
                                       text_color=C.TEXT)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        bottom_frame = ctk.CTkFrame(container, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.lbl_err = ctk.CTkLabel(bottom_frame, text="", font=F(9), text_color=C.ACCENT2)
        self.lbl_err.pack(pady=(0, 4))
        ctk.CTkButton(bottom_frame, text="💾  Guardar cambios", fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(11, "bold"), corner_radius=14, height=42, width=220,
                      command=self._save).pack()

        def _scroll(p):
            sf = ctk.CTkScrollableFrame(p, fg_color="transparent")
            sf.pack(fill="both", expand=True)
            return sf

        t1 = _scroll(self.tabview.add("⏱ Temporizador"))
        t2 = _scroll(self.tabview.add("⚙ Opciones"))
        t3 = _scroll(self.tabview.add("🎨 Apariencia"))
        t4 = _scroll(self.tabview.add("🏃 Ejercicios"))
        t5 = _scroll(self.tabview.add("🔧 Avanzado"))

        self.v_int = ctk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = ctk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = ctk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = ctk.StringVar(value=self.cfg["hora_fin"])
        self.v_pos = ctk.StringVar(value=str(self.cfg["posponer_min"]))
        self.v_meta = ctk.StringVar(value=str(self.cfg["meta_pausas"]))
        self.v_modo = ctk.StringVar(value=self.cfg.get("modo", "normal"))

        card_t1 = _card(t1)
        card_t1.pack(fill="x", pady=(4, 0))
        self._field(card_t1, "Intervalo entre pausas (min)", self.v_int, 0)
        self._field(card_t1, "Duración de la pausa (min)", self.v_dur, 1)
        self._field(card_t1, "Hora inicio (HH:MM)", self.v_ini, 2)
        self._field(card_t1, "Hora fin (HH:MM)", self.v_fin, 3)
        self._field(card_t1, "Minutos para posponer", self.v_pos, 4)
        self._field(card_t1, "Meta de pausas diarias", self.v_meta, 5)

        modo_card = _card(t1)
        modo_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(modo_card, text="Modo de timer", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(8, 4))
        for val, lbl in [("normal", "Normal"), ("pomodoro", "Pomodoro (25/5)")]:
            _radio(modo_card, lbl, self.v_modo, val).pack(anchor="w", padx=14, pady=1)
        ctk.CTkLabel(modo_card, text="Pomodoro: bloques de 25 min trabajo + 5 min pausa",
                     font=F(7), text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 6))

        opts = _card(t2)
        opts.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(opts, text="General", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_nm = ctk.BooleanVar(value=self.cfg.get("no_molestar", True))
        self.v_fs = ctk.BooleanVar(value=self.cfg.get("fin_de_semana", False))
        self.v_voz = ctk.BooleanVar(value=self.cfg.get("guia_voz", True))
        _checkbox(opts, "No interrumpir si hay pantalla completa", self.v_nm).pack(anchor="w", padx=10, pady=3)
        _checkbox(opts, "Pausar en fin de semana (sáb y dom)", self.v_fs).pack(anchor="w", padx=10, pady=3)
        _checkbox(opts, "Guía por voz durante la pausa", self.v_voz).pack(anchor="w", padx=10, pady=(0, 6))

        agua = _card(t2)
        agua.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(agua, text="💧 Recordatorio de agua", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_agua = ctk.BooleanVar(value=self.cfg.get("agua_activo", True))
        self.v_agua_min = ctk.StringVar(value=str(self.cfg.get("agua_min", 30)))
        _checkbox(agua, "Activar recordatorio de hidratación", self.v_agua).pack(anchor="w", padx=10, pady=3)
        row_agua = ctk.CTkFrame(agua, fg_color="transparent")
        row_agua.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(row_agua, text="Cada cuántos minutos:", font=F(9),
                     text_color=C.TEXT_MUTED).pack(side="left")
        _entry(row_agua, self.v_agua_min, width=60).pack(side="left", padx=8)

        post = _card(t2)
        post.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(post, text="🧘 Recordatorio de postura", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_postura = ctk.BooleanVar(value=self.cfg.get("postura_recordatorio", False))
        self.v_postura_min = ctk.StringVar(value=str(self.cfg.get("postura_intervalo_min", 20)))
        _checkbox(post, "Activar recordatorio de postura", self.v_postura).pack(anchor="w", padx=10, pady=3)
        row_post = ctk.CTkFrame(post, fg_color="transparent")
        row_post.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(row_post, text="Cada cuántos minutos:", font=F(9),
                     text_color=C.TEXT_MUTED).pack(side="left")
        _entry(row_post, self.v_postura_min, width=60).pack(side="left", padx=8)

        gen = _card(t2)
        gen.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(gen, text="Sistema", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_snd = ctk.BooleanVar(value=self.cfg["sonido"])
        self.v_auto = ctk.BooleanVar(value=get_autoarranque())
        _checkbox(gen, "Sonido de alerta al iniciar pausa", self.v_snd).pack(anchor="w", padx=10, pady=3)
        _checkbox(gen, "Iniciar con Windows (autoarranque)", self.v_auto).pack(anchor="w", padx=10, pady=(0, 4))

        idioma_card = _card(t2)
        idioma_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(idioma_card, text="🌍 Idioma", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_idioma = ctk.StringVar(value=self.cfg.get("idioma", "es"))
        for val, lbl in [("es", "Español"), ("en", "English")]:
            _radio(idioma_card, lbl, self.v_idioma, val).pack(anchor="w", padx=10, pady=1)

        tema_card = _card(t3)
        tema_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(tema_card, text="🌙 Tema", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_tema = ctk.StringVar(value=self.cfg.get("tema", "oscuro"))
        for val, lbl in [("oscuro", "Oscuro"), ("claro", "Claro")]:
            _radio(tema_card, lbl, self.v_tema, val).pack(anchor="w", padx=14, pady=2)

        accent_card = _card(t3)
        accent_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(accent_card, text="🎨 Color de acento", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_accent = ctk.StringVar(value=self.cfg.get("color_acento", "azul"))
        for val in ("azul", "verde", "morado", "rosa", "naranja", "teal", "rojo"):
            _radio(accent_card, val.capitalize(), self.v_accent, val).pack(anchor="w", padx=14, pady=1)

        fondo_card = _card(t3)
        fondo_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(fondo_card, text="🖼️ Fondo", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_fondo = ctk.StringVar(value=self.cfg.get("fondo", "estandar"))
        for val in ("estandar", "profundo", "gris", "azulado", "blanco"):
            _radio(fondo_card, val.capitalize(), self.v_fondo, val).pack(anchor="w", padx=14, pady=1)

        font_card = _card(t3)
        font_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(font_card, text="🔤 Tamaño de letra", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_font = ctk.StringVar(value=self.cfg.get("tamano_letra", "normal"))
        for val in ("pequeno", "normal", "grande", "muy_grande"):
            _radio(font_card, val.replace("_", " ").capitalize(), self.v_font, val).pack(anchor="w", padx=14, pady=1)

        ej_card = _card(t4)
        ej_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(ej_card, text="Marca los ejercicios que quieres incluir:",
                     font=F(9, "bold"), text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.ej_vars: dict[str, ctk.BooleanVar] = {}
        activos: list[str] = self.cfg.get("ejercicios_activos",
                                            [e["id"] for e in EJERCICIOS])
        for ej in EJERCICIOS:
            v = ctk.BooleanVar(value=ej["id"] in activos)
            self.ej_vars[ej["id"]] = v
            r = ctk.CTkFrame(ej_card, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)
            _checkbox(r, f"{ej['icono']} {ej['nombre']}", v).pack(side="left")

        modes_card = _card(t5)
        modes_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(modes_card, text="🖥️ Modos de ventana", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_compact = ctk.BooleanVar(value=self.cfg.get("compacto_enabled", False))
        self.v_floating = ctk.BooleanVar(value=self.cfg.get("floating_enabled", False))
        self.v_fs_timer = ctk.BooleanVar(value=self.cfg.get("pantalla_completa", False))
        _checkbox(modes_card, "Modo compacto (mini ventana)", self.v_compact).pack(anchor="w", padx=10, pady=3)
        _checkbox(modes_card, "Timer flotante en escritorio", self.v_floating).pack(anchor="w", padx=10, pady=3)
        _checkbox(modes_card, "Modo pantalla completa", self.v_fs_timer).pack(anchor="w", padx=10, pady=(0, 6))

        sound_card = _card(t5)
        sound_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(sound_card, text="🔊 Sonido ambiente", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_amb = ctk.StringVar(value=self.cfg.get("sonido_ambiente", "ninguno"))
        for val, lbl in [("ninguno", "Sin sonido"), ("lluvia", "Lluvia"), ("naturaleza", "Naturaleza")]:
            _radio(sound_card, lbl, self.v_amb, val).pack(anchor="w", padx=14, pady=2)

        self.v_sound_pack = ctk.StringVar(value=self.cfg.get("sound_pack_activo", "default"))
        ctk.CTkLabel(sound_card, text="Paquete de sonido:", font=F(9),
                     text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(6, 2))
        for val, lbl in [("default", "Por defecto"), ("nature", "Naturaleza"), ("minimal", "Minimalista")]:
            _radio(sound_card, lbl, self.v_sound_pack, val).pack(anchor="w", padx=14, pady=1)

        hotkey_card = _card(t5)
        hotkey_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(hotkey_card, text="⌨️ Atajos de teclado", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_hk_next = ctk.StringVar(value=self.cfg.get("hotkey_siguiente", "ctrl+right"))
        self.v_hk_prev = ctk.StringVar(value=self.cfg.get("hotkey_anterior", "ctrl+left"))
        self.v_hk_pause = ctk.StringVar(value=self.cfg.get("hotkey_pausar", "ctrl+space"))
        self.v_hk_skip = ctk.StringVar(value=self.cfg.get("hotkey_saltar", "ctrl+escape"))
        self._field(hotkey_card, "Siguiente paso", self.v_hk_next, 0)
        self._field(hotkey_card, "Paso anterior", self.v_hk_prev, 1)
        self._field(hotkey_card, "Pausar/reanudar", self.v_hk_pause, 2)
        self._field(hotkey_card, "Saltar pausa", self.v_hk_skip, 3)
        ctk.CTkLabel(hotkey_card, text="Ejemplo: ctrl+right, alt+space",
                     font=F(7), text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 6))

        logro_card = _card(t5)
        logro_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(logro_card, text="🏆 Logros desbloqueados", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        shown = self.cfg.get("logros_mostrados", [])
        for ach in ACHIEVEMENTS:
            unlocked = ach["id"] in shown
            row = ctk.CTkFrame(logro_card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=1)
            icon = ach["icon"] if unlocked else "🔒"
            status = "✅" if unlocked else "⏳"
            ctk.CTkLabel(row, text=f"{icon} {_(ach['key'])} {status}", font=F(9),
                         text_color=C.TEXT if unlocked else C.TEXT_MUTED, anchor="w").pack(side="left")

    def _parse_time(self, raw: str, label: str) -> tuple[int, int]:
        try:
            h, m = map(int, raw.split(":"))
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
            return h, m
        except Exception:
            raise ValueError(f"{label}: {_('err_hora_invalida')}")

    def _save(self) -> None:
        try:
            raw = self.v_int.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_intervalo"))
            iv = int(raw)
            raw = self.v_dur.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_duracion"))
            dv = int(raw)
            raw = self.v_pos.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_posponer"))
            pv = int(raw)
            raw = self.v_meta.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_meta"))
            mv = int(raw)
            raw = self.v_agua_min.get().strip()
            if not raw.isdigit():
                raise ValueError(_("err_campo_agua"))
            amv = int(raw)
            for name, val in [("Intervalo", iv), ("Duración", dv),
                              ("Posponer", pv), ("Meta", mv), ("Agua (min)", amv)]:
                if val <= 0:
                    raise ValueError(f"{name}: {_('err_valor_positivo')}")
            h0, m0 = self._parse_time(self.v_ini.get(), _("field_hora_inicio"))
            h1, m1 = self._parse_time(self.v_fin.get(), _("field_hora_fin"))
        except ValueError as e:
            self.lbl_err.configure(text=f"⚠ {e}")
            return
        activos = [eid for eid, v in self.ej_vars.items() if v.get()]
        if not activos:
            self.lbl_err.configure(text=_("err_selecciona_ej"))
            return
        set_autoarranque(self.v_auto.get(), self._app_path)

        nuevo_tema = self.v_tema.get()
        nuevo_accent = self.v_accent.get()
        nuevo_fondo = self.v_fondo.get()
        if nuevo_tema != self.cfg.get("tema") or nuevo_accent != self.cfg.get("color_acento", "azul") or nuevo_fondo != self.cfg.get("fondo", "estandar"):
            set_theme(nuevo_tema, nuevo_accent, nuevo_fondo)

        nuevo_idioma = self.v_idioma.get()
        if nuevo_idioma != self.cfg.get("idioma"):
            set_idioma(nuevo_idioma)

        self.cfg.update({
            "intervalo_min":      iv,
            "duracion_pausa_min": dv,
            "hora_inicio":        self.v_ini.get(),
            "hora_fin":           self.v_fin.get(),
            "posponer_min":       pv,
            "sonido":             self.v_snd.get(),
            "ejercicios_activos": activos,
            "meta_pausas":        mv,
            "no_molestar":        self.v_nm.get(),
            "fin_de_semana":      self.v_fs.get(),
            "guia_voz":           self.v_voz.get(),
            "agua_activo":        self.v_agua.get(),
            "agua_min":           amv,
            "sonido_ambiente":    self.v_amb.get(),
            "tema":               nuevo_tema,
            "modo":               self.v_modo.get(),
            "idioma":             nuevo_idioma,
            "tamano_letra":       self.v_font.get(),
            "color_acento":       nuevo_accent,
            "fondo":              nuevo_fondo,
            "postura_recordatorio": self.v_postura.get(),
            "postura_intervalo_min": int(self.v_postura_min.get() or 20),
            "compacto_enabled":   self.v_compact.get(),
            "floating_enabled":   self.v_floating.get(),
            "pantalla_completa":  self.v_fs_timer.get(),
            "hotkey_siguiente":   self.v_hk_next.get(),
            "hotkey_anterior":    self.v_hk_prev.get(),
            "hotkey_pausar":      self.v_hk_pause.get(),
            "hotkey_saltar":      self.v_hk_skip.get(),
            "sound_pack_activo":  self.v_sound_pack.get(),
        })
        self.on_save(self.cfg)
        self.destroy()
