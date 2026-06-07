"""Todas las ventanas de la UI (FlowBreak)."""

from __future__ import annotations

import os
import random
import subprocess
import sys
import threading
import winreg
import customtkinter as ctk
from tkinter import Canvas, filedialog, messagebox
from typing import Any, Callable

from pausa_activa.constants import (
    C, APP_NAME, APP_DISPLAY, EJERCICIOS, get_random_phrase, set_theme, set_idioma,
    _, I18N, THEMES, center_window,
    log,
)
from pausa_activa.audio import AudioManager
from pausa_activa.notifications import send_win_notification
from pausa_activa.installer import (
    _get_install_dir_from_registry,
    _eliminar_accesos_directos, _programar_borrado_carpeta,
    _quitar_registro_desinstalador,
)

audio_manager: AudioManager = AudioManager()


def set_autoarranque(enable: bool, app_path: str) -> None:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)
    try:
        if enable:
            if getattr(sys, "frozen", False):
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
            else:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'python "{app_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def get_autoarranque() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False



# ═══════════════════════════════════════════════════════════════════════════
# Clase base
# ═══════════════════════════════════════════════════════════════════════════


def _card(parent: ctk.CTkBaseClass, **kwargs: Any) -> ctk.CTkFrame:
    kwargs.setdefault("fg_color", C.CARD)
    kwargs.setdefault("corner_radius", 12)
    kwargs.setdefault("border_width", 0)
    kwargs.setdefault("border_color", C.CARD_BORDER)
    return ctk.CTkFrame(parent, **kwargs)


def _entry(parent: ctk.CTkBaseClass, variable: ctk.Variable, width: int = 120) -> ctk.CTkEntry:
    return ctk.CTkEntry(parent, textvariable=variable, font=("Segoe UI", 11),
                        fg_color=C.BG3, text_color=C.TEXT, border_color=C.BORDER,
                        width=width, corner_radius=6)


def _checkbox(parent: ctk.CTkBaseClass, text: str, variable: ctk.Variable) -> ctk.CTkCheckBox:
    return ctk.CTkCheckBox(parent, text=text, variable=variable,
                           fg_color=C.ACCENT, text_color=C.TEXT,
                           font=("Segoe UI", 9), hover_color=C.ACCENT2,
                           corner_radius=4, border_width=2, checkmark_color=C.BG)


def _radio(parent: ctk.CTkBaseClass, text: str, variable: ctk.Variable, value: str) -> ctk.CTkRadioButton:
    return ctk.CTkRadioButton(parent, text=text, variable=variable, value=value,
                              fg_color=C.ACCENT, text_color=C.TEXT,
                              font=("Segoe UI", 9), hover_color=C.ACCENT2,
                              border_width_checked=5, border_width_unchecked=2)


class CenteredWindow(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent, *args, **kwargs)
        self.resizable(False, False)

    def center(self) -> None:
        center_window(self)


# ═══════════════════════════════════════════════════════════════════════════
# Gráfico de barras con Canvas
# ═══════════════════════════════════════════════════════════════════════════

def _dibujar_grafico(parent: ctk.CTkFrame, history: dict[str, dict[str, Any]], meta: int) -> Canvas:
    import datetime as dt
    from calendar import day_abbr
    canvas = Canvas(parent, width=340, height=140, bg=C.CARD, highlightthickness=0)
    canvas.pack(padx=10, pady=10)
    today = dt.date.today()
    days: list[str] = [(today - dt.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    max_val: int = max(
        (history.get(d, {}).get("completadas", 0) for d in days),
        default=meta,
    )
    max_val = max(max_val, meta, 1)
    bar_w: int = 30
    gap: int = 12
    start_x: int = 25
    bottom_y: int = 115
    max_h: int = 85
    for i, dia_iso in enumerate(days):
        data = history.get(dia_iso, {"completadas": 0, "saltadas": 0})
        comp = data["completadas"]
        bar_h: int = int((comp / max_val) * max_h) if max_val else 0
        x0: int = start_x + i * (bar_w + gap)
        x1: int = x0 + bar_w
        y0: int = bottom_y - bar_h
        y1: int = bottom_y
        canvas.create_rectangle(x0, y0, x1, y1, fill=C.ACCENT, outline="", width=0)
        canvas.create_text((x0 + x1) // 2, y0 - 5, text=str(comp),
                           fill=C.TEXT_DIM, font=("Segoe UI", 8))
        weekday_num: int = dt.date.fromisoformat(dia_iso).weekday()
        canvas.create_text((x0 + x1) // 2, bottom_y + 10,
                           text=day_abbr[weekday_num][:3],
                           fill=C.TEXT_DIM, font=("Segoe UI", 7))
    return canvas


# ═══════════════════════════════════════════════════════════════════════════
# BreakWindow (antes PausaWindow)
# ═══════════════════════════════════════════════════════════════════════════

class BreakWindow(CenteredWindow):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        ejercicio: dict[str, Any],
        duracion_sec: int,
        on_done: Callable[[], None],
        on_skip: Callable[[], None],
        sonido_ambiente: str = "ninguno",
    ) -> None:
        super().__init__(parent)
        self.on_done: Callable[[], None] = on_done
        self.on_skip: Callable[[], None] = on_skip
        self.remaining: int = duracion_sec
        self._duracion_original: int = duracion_sec
        self.ejercicio: dict[str, Any] = ejercicio
        self._job: str | None = None
        pasos = self.ejercicio.get("pasos", [])
        self._num_steps: int = len(pasos)
        self._current_step: int = 0
        self._step_interval: float = duracion_sec / max(self._num_steps, 1)
        self._step_frames: list[dict[str, Any]] = []
        self.title(_("pausa_activa"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self._build()
        self.center()
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._skip)
        if sonido_ambiente != "ninguno":
            audio_manager.start_ambient(sonido_ambiente)

    def _build(self) -> None:
        main = _card(self, fg_color=C.BG2)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        # Exercise icon
        ctk.CTkLabel(main, text=self.ejercicio["icono"], font=("Segoe UI Emoji", 40),
                     text_color=C.TEXT).pack(pady=(20, 0))

        ctk.CTkLabel(main, text=self.ejercicio["nombre"], font=("Segoe UI", 17, "bold"),
                     text_color=C.TEXT).pack(pady=(4, 0))

        # Step progress dots
        if self._num_steps > 1:
            dot_frame = ctk.CTkFrame(main, fg_color="transparent")
            dot_frame.pack(pady=(8, 4))
            self._step_dots: list[ctk.CTkLabel] = []
            for i in range(self._num_steps):
                dot = ctk.CTkLabel(dot_frame, text="●", font=("Segoe UI", 10),
                                   text_color=C.BG3)
                dot.pack(side="left", padx=4)
                self._step_dots.append(dot)

        # Current step text
        step_card = _card(main, fg_color=C.CARD)
        step_card.pack(fill="x", padx=20, pady=(4, 8))
        self._step_label = ctk.CTkLabel(step_card, text="", font=("Segoe UI", 11),
                                        text_color=C.TEXT, wraplength=280)
        self._step_label.pack(padx=16, pady=10)

        # Circular timer
        self._canvas = Canvas(main, width=200, height=200, bg=C.BG2, highlightthickness=0)
        self._canvas.pack(pady=(4, 0))

        # Skip
        ctk.CTkButton(main, text=_("saltar_pausa"),
                      fg_color="transparent", text_color=C.TEXT_MUTED,
                      font=("Segoe UI", 9),
                      hover_color=C.BG3, corner_radius=8,
                      command=self._skip).pack(pady=(8, 14))

    @staticmethod
    def _fmt_time(s: int) -> str:
        m, s = divmod(max(0, int(s)), 60)
        return f"{m:02d}:{s:02d}"

    def _tick(self) -> None:
        try:
            if self.remaining <= 0:
                self._done()
                return

            # Advance step animation based on elapsed time
            elapsed: int = self._duracion_original - self.remaining
            next_step: int = min(int(elapsed / self._step_interval) if self._step_interval > 0 else 0,
                                 self._num_steps - 1)
            if next_step != self._current_step:
                self._current_step = next_step
                self._highlight_step()

            self._canvas.delete("all")
            pct: float = max(0.0, self.remaining / self._duracion_original)
            if pct > 0.5:
                color: str = C.GREEN
            elif pct > 0.2:
                color = C.YELLOW
            else:
                color = C.ACCENT2
            cx: int = 100
            cy: int = 100
            r: int = 78
            self._canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C.BG3, width=7)
            extent: float = 360.0 * pct
            self._canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=90,
                                    extent=extent, outline=color, width=7, style="arc")
            self._canvas.create_text(cx, cy, text=self._fmt_time(self.remaining),
                                      font=("Segoe UI", 30, "bold"), fill=C.TEXT)
            self.remaining -= 1
            self._job = self.after(1000, self._tick)
        except Exception as ex:
            log.exception("Error en BreakWindow._tick: %s", ex)
            self._done()

    def _highlight_step(self) -> None:
        pasos: list[str] = self.ejercicio.get("pasos", [])
        if self._current_step < len(pasos):
            self._step_label.configure(text=f"→ {pasos[self._current_step]}")
        if hasattr(self, "_step_dots"):
            for i, dot in enumerate(self._step_dots):
                if i < self._current_step:
                    dot.configure(text_color=C.GREEN)
                elif i == self._current_step:
                    dot.configure(text_color=C.ACCENT)
                else:
                    dot.configure(text_color=C.BG3)

    def _done(self) -> None:
        audio_manager.stop_ambient()
        if self._job:
            self.after_cancel(self._job)
        self.destroy()
        self.on_done()

    def _skip(self) -> None:
        audio_manager.stop_ambient()
        if self._job:
            self.after_cancel(self._job)
        self.destroy()
        self.on_skip()


# ═══════════════════════════════════════════════════════════════════════════
# StatsWindow con gráfico Canvas
# ═══════════════════════════════════════════════════════════════════════════

class StatsWindow(CenteredWindow):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        stats: dict[str, Any],
        meta: int,
        hist_file: str,
        history: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(_("estadisticas"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        total: int = stats["completadas"] + stats["saltadas"]
        pct: int = int(stats["completadas"] / total * 100) if total else 0
        meta_ok: bool = stats["completadas"] >= meta

        main = _card(self, fg_color=C.BG2)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(main, text=_("estadisticas"), font=("Segoe UI", 14, "bold"),
                     text_color=C.TEXT).pack(pady=(14, 8))

        # Stats pills
        pill_frame = ctk.CTkFrame(main, fg_color="transparent")
        pill_frame.pack()
        pills: list[tuple[str, str, str]] = [
            ("✅", f"{stats['completadas']}", C.GREEN),
            ("⏭", str(stats["saltadas"]), C.ACCENT2),
            ("📈", f"{pct}%", C.ACCENT),
            ("🔥", f"{stats.get('racha', 0)}d", C.YELLOW),
        ]
        for icon, val, color in pills:
            p = _card(pill_frame, fg_color=C.CARD, corner_radius=10)
            p.pack(side="left", padx=4)
            ctk.CTkLabel(p, text=icon, font=("Segoe UI", 12),
                         text_color=C.TEXT_DIM).pack(side="left", padx=(10, 2), pady=6)
            ctk.CTkLabel(p, text=val, font=("Segoe UI", 14, "bold"),
                         text_color=color).pack(side="left", padx=(0, 10), pady=6)

        # Detail rows
        card = _card(main, fg_color=C.CARD)
        card.pack(fill="x", pady=(10, 0))
        status_icon: str = "🎯" if meta_ok else "🔄"
        status_color: str = C.GREEN if meta_ok else C.TEXT_MUTED
        rows: list[tuple[str, str, str]] = [
            (_("stats_completadas"), f"{stats['completadas']} / {meta}", C.GREEN),
            (_("stats_saltadas"),    str(stats["saltadas"]),              C.ACCENT2),
            (_("stats_tasa_exito"),  f"{pct}%",                          C.ACCENT),
            (_("stats_racha"),       f"{stats.get('racha', 0)} d", C.YELLOW),
            (_("stats_meta_diaria"), f"{status_icon} {_('stats_cumplida') if meta_ok else _('stats_en_progreso')}", status_color),
        ]
        for label, val, color in rows:
            r = ctk.CTkFrame(card, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(r, text=label, font=("Segoe UI", 9),
                         text_color=C.TEXT_MUTED, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=val, font=("Segoe UI", 10, "bold"),
                         text_color=color).pack(side="right")

        if history:
            ctk.CTkLabel(main, text=_("ultimos_7_dias"), font=("Segoe UI", 9, "bold"),
                         text_color=C.TEXT_DIM).pack(pady=(8, 2), anchor="w", padx=4)
            graph_card = _card(main, fg_color=C.CARD)
            graph_card.pack(fill="x")
            _dibujar_grafico(graph_card, history, meta)

        if stats["historial"]:
            ctk.CTkLabel(main, text=_("ultimas_pausas"), font=("Segoe UI", 9, "bold"),
                         text_color=C.TEXT_DIM).pack(pady=(8, 2), anchor="w", padx=4)
            hist_card = _card(main, fg_color=C.CARD)
            hist_card.pack(fill="x")
            for entry in stats["historial"][-5:][::-1]:
                dot: str = "🟢" if entry["estado"] == "completada" else "🔴"
                r = ctk.CTkFrame(hist_card, fg_color="transparent")
                r.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(r, text=f"{dot}  {entry['hora']}  \u2022  {entry['ejercicio']}",
                             font=("Segoe UI", 9), text_color=C.TEXT).pack(side="left")
                ctk.CTkLabel(r, text=f"[{entry['estado']}]",
                             font=("Segoe UI", 8, "bold"),
                              text_color=C.GREEN if entry["estado"] == "completada" else C.ACCENT2).pack(side="right")

        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(10, 14))
        ctk.CTkButton(bf, text=_("exportar_csv"), fg_color=C.BG3, text_color=C.TEXT,
                      font=("Segoe UI", 9), corner_radius=12,
                      command=lambda: self._export(hist_file, stats, meta)).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=_("cerrar"), fg_color=C.ACCENT, text_color=C.BG,
                      font=("Segoe UI", 9, "bold"), corner_radius=12,
                      command=self.destroy).pack(side="left", padx=4)
        self.center()

    @staticmethod
    def _export(hist_file: str, stats: dict[str, Any], meta: int) -> None:
        from datetime import datetime as _dt
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json"), (_("todos"), "*.*")],
            title=_("exportar_stats"),
        )
        if not path:
            return
        try:
            if path.endswith(".json"):
                import json
                stats["meta_pausas"] = meta
                stats["exportado"] = _dt.now().isoformat()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
            else:
                import shutil
                if os.path.exists(hist_file):
                    shutil.copy2(hist_file, path)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("fecha,hora,ejercicio,estado\n")
            messagebox.showinfo(_("exportar"), _("exportado_ok").format(path=path))
        except Exception as e:
            messagebox.showerror(_("error"), _("exportado_error").format(e=e))


# ═══════════════════════════════════════════════════════════════════════════
# ConfigWindow con CTkTabview
# ═══════════════════════════════════════════════════════════════════════════

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
        self._build()
        self.center()

    def _field(self, parent: ctk.CTkFrame, label: str, var: ctk.Variable, row: int) -> None:
        ctk.CTkLabel(parent, text=label, font=("Segoe UI", 10),
                     text_color=C.TEXT_MUTED, anchor="w").grid(
            row=row, column=0, sticky="w", padx=16, pady=8)
        _entry(parent, var).grid(row=row, column=1, padx=16, pady=8, sticky="e")

    def _build(self) -> None:
        main = _card(self, fg_color=C.BG2)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(main, text=_("configuracion"), font=("Segoe UI", 14, "bold"),
                     text_color=C.TEXT).pack(pady=(12, 4))

        self.tabview = ctk.CTkTabview(main, fg_color="transparent",
                                       segmented_button_fg_color=C.BG3,
                                       segmented_button_selected_color=C.ACCENT,
                                       segmented_button_selected_hover_color=C.ACCENT,
                                       segmented_button_unselected_color=C.BG4,
                                       text_color=C.TEXT)
        self.tabview.pack(fill="both", expand=True, padx=4, pady=(2, 4))

        t1 = self.tabview.add(_("config_temporizador"))
        t2 = self.tabview.add(_("config_opciones"))
        t3 = self.tabview.add(_("config_sonido"))
        t4 = self.tabview.add(_("config_ejercicios"))

        # ── TAB 1: Temporizador ──
        self.v_int = ctk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = ctk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = ctk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = ctk.StringVar(value=self.cfg["hora_fin"])
        self.v_pos = ctk.StringVar(value=str(self.cfg["posponer_min"]))
        self.v_meta = ctk.StringVar(value=str(self.cfg["meta_pausas"]))
        self.v_modo = ctk.StringVar(value=self.cfg.get("modo", "normal"))

        card_t1 = _card(t1)
        card_t1.pack(fill="x", pady=(4, 0))
        self._field(card_t1, _("field_intervalo"), self.v_int, 0)
        self._field(card_t1, _("field_duracion_pausa"),   self.v_dur, 1)
        self._field(card_t1, _("field_hora_inicio"),          self.v_ini, 2)
        self._field(card_t1, _("field_hora_fin"),             self.v_fin, 3)
        self._field(card_t1, _("field_posponer"),        self.v_pos, 4)
        self._field(card_t1, _("field_meta_pausas"),       self.v_meta, 5)

        modo_card = _card(t1)
        modo_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(modo_card, text=_("modo_timer"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(8, 4))
        for val, lbl in [("normal", _("modo_normal")),
                         ("pomodoro", _("modo_pomodoro"))]:
            _radio(modo_card, lbl, self.v_modo, val).pack(anchor="w", padx=14, pady=1)
        ctk.CTkLabel(modo_card, text=_("pomodoro_desc"),
                     font=("Segoe UI", 7), text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 6))

        # ── TAB 2: Opciones ──
        opts = _card(t2)
        opts.pack(fill="x", pady=(4, 0))
        self.v_nm = ctk.BooleanVar(value=self.cfg.get("no_molestar", True))
        self.v_fs = ctk.BooleanVar(value=self.cfg.get("fin_de_semana", False))
        _checkbox(opts, _("no_molestar"), self.v_nm).pack(anchor="w", padx=10, pady=4)
        _checkbox(opts, _("fin_de_semana_opt"), self.v_fs).pack(anchor="w", padx=10, pady=(0, 4))

        agua = _card(t2)
        agua.pack(fill="x", pady=(6, 0))
        self.v_agua = ctk.BooleanVar(value=self.cfg.get("agua_activo", True))
        self.v_agua_min = ctk.StringVar(value=str(self.cfg.get("agua_min", 30)))
        _checkbox(agua, _("chk_activar_agua"), self.v_agua).pack(anchor="w", padx=10, pady=4)
        row_agua = ctk.CTkFrame(agua, fg_color="transparent")
        row_agua.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(row_agua, text=_("field_agua_intervalo"), font=("Segoe UI", 9),
                     text_color=C.TEXT_MUTED).pack(side="left")
        _entry(row_agua, self.v_agua_min, width=60).pack(side="left", padx=8)

        gen = _card(t2)
        gen.pack(fill="x", pady=(6, 0))
        self.v_snd = ctk.BooleanVar(value=self.cfg["sonido"])
        self.v_auto = ctk.BooleanVar(value=get_autoarranque())
        _checkbox(gen, _("sonido_alerta"), self.v_snd).pack(anchor="w", padx=10, pady=4)
        _checkbox(gen, _("autoarranque"), self.v_auto).pack(anchor="w", padx=10, pady=4)

        perfil = _card(t2)
        perfil.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(perfil, text=_("section_perfiles"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_perfil = ctk.StringVar(value=self.cfg.get("perfil", "default"))
        for p in self._profiles:
            _radio(perfil, p, self.v_perfil, p).pack(anchor="w", padx=10, pady=1)

        lang = _card(t2)
        lang.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(lang, text=_("section_idioma"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_idioma = ctk.StringVar(value=self.cfg.get("idioma", "es"))
        for val, lbl in [("es", _("idioma_es")), ("en", _("idioma_en"))]:
            _radio(lang, lbl, self.v_idioma, val).pack(anchor="w", padx=10, pady=1)

        # ── TAB 3: Sonido ──
        amb = _card(t3)
        amb.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(amb, text=_("section_sonido_ambiente"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_amb = ctk.StringVar(value=self.cfg.get("sonido_ambiente", "ninguno"))
        for val, lbl in [("ninguno", _("sin_sonido")), ("lluvia", _("lluvia")),
                         ("naturaleza", _("naturaleza"))]:
            _radio(amb, lbl, self.v_amb, val).pack(anchor="w", padx=14, pady=3)

        notif = _card(t3)
        notif.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(notif, text=_("section_notificaciones"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_notif_sound = ctk.StringVar(value=self.cfg.get("notificacion_sonido", "default"))
        self.v_notif_dur = ctk.StringVar(value=self.cfg.get("notificacion_duracion", "short"))
        ctk.CTkLabel(notif, text=_("field_sonido_tipo"), font=("Segoe UI", 9),
                     text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(4, 2))
        for val, lbl in [("default", "Default"), ("sms", "SMS"), ("mail", "Mail"),
                         ("reminder", _("agua_recordatorio")), ("critical", _("sonido_critica"))]:
            _radio(notif, lbl, self.v_notif_sound, val).pack(anchor="w", padx=18, pady=1)
        ctk.CTkLabel(notif, text=_("field_duracion"), font=("Segoe UI", 9),
                     text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(4, 2))
        for val, lbl in [("short", _("dur_corta")), ("long", _("dur_larga"))]:
            _radio(notif, lbl, self.v_notif_dur, val).pack(anchor="w", padx=18, pady=1)

        # ── TAB 4: Ejercicios ──
        ej_card = _card(t4)
        ej_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(ej_card, text=_("section_ejercicios"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.ej_vars: dict[str, ctk.BooleanVar] = {}
        activos: list[str] = self.cfg.get("ejercicios_activos",
                                            [e["id"] for e in EJERCICIOS])
        for ej in EJERCICIOS:
            v = ctk.BooleanVar(value=ej["id"] in activos)
            self.ej_vars[ej["id"]] = v
            r = ctk.CTkFrame(ej_card, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)
            _checkbox(r, f"{ej['icono']} {ej['nombre']}", v).pack(side="left")

        tema_card = _card(t4)
        tema_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(tema_card, text=_("theme"), font=("Segoe UI", 9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_tema = ctk.StringVar(value=self.cfg.get("tema", "oscuro"))
        for val, lbl in [("oscuro", _("theme_oscuro")), ("claro", _("theme_claro"))]:
            _radio(tema_card, lbl, self.v_tema, val).pack(anchor="w", padx=14, pady=2)

        self.lbl_err = ctk.CTkLabel(main, text="", font=("Segoe UI", 9), text_color=C.ACCENT2)
        self.lbl_err.pack()
        ctk.CTkButton(main, text=_("guardar"), fg_color=C.ACCENT, text_color=C.BG,
                      font=("Segoe UI", 9, "bold"), corner_radius=12,
                      command=self._save).pack(pady=(6, 12))

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
        if nuevo_tema != self.cfg.get("tema"):
            set_theme(nuevo_tema)

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
            "agua_activo":        self.v_agua.get(),
            "agua_min":           amv,
            "sonido_ambiente":    self.v_amb.get(),
            "tema":               nuevo_tema,
            "modo":               self.v_modo.get(),
            "perfil":             self.v_perfil.get(),
            "idioma":             nuevo_idioma,
            "notificacion_sonido": self.v_notif_sound.get(),
            "notificacion_duracion": self.v_notif_dur.get(),
        })
        self.on_save(self.cfg)
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════
# WelcomeWindow
# ═══════════════════════════════════════════════════════════════════════════

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
            ctk.CTkLabel(f, text="\u25cf", font=("Segoe UI", 12),
                         text_color=color).pack(side="left", padx=4)

    def _step_bienvenida(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_heading"), font=("Segoe UI", 16, "bold"),
                     text_color=C.TEXT).pack(pady=(20, 2))
        ctk.CTkLabel(f, text=_("bienvenido"), font=("Segoe UI", 10),
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
            ctk.CTkLabel(col, text=titulo, font=("Segoe UI", 10, "bold"),
                         text_color=C.TEXT, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=desc, font=("Segoe UI", 8),
                         text_color=C.TEXT_MUTED, anchor="w", wraplength=280).pack(anchor="w")
        self._dots(f)
        ctk.CTkButton(f, text=_("next_step"), fg_color=C.ACCENT, text_color=C.BG,
                      font=("Segoe UI", 10, "bold"), corner_radius=12,
                      command=self._next).pack(pady=(0, 24))

    def _step_config(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_step1_heading"), font=("Segoe UI", 14, "bold"),
                     text_color=C.TEXT).pack(pady=(14, 2))
        ctk.CTkLabel(f, text=_("welcome_step1_info"),
                     font=("Segoe UI", 9), text_color=C.TEXT_MUTED).pack(pady=(6, 10))

        card_cfg = _card(f)
        card_cfg.pack(fill="x", padx=24)

        self.v_int = ctk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = ctk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = ctk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = ctk.StringVar(value=self.cfg["hora_fin"])
        self.v_meta = ctk.StringVar(value=str(self.cfg["meta_pausas"]))

        def campo(lbl: str, var: ctk.Variable, row: int) -> None:
            ctk.CTkLabel(card_cfg, text=lbl, font=("Segoe UI", 10),
                         text_color=C.TEXT_MUTED, anchor="w").grid(row=row, column=0, sticky="w", padx=14, pady=7)
            _entry(card_cfg, var).grid(row=row, column=1, padx=14, pady=7, sticky="e")

        campo(_("welcome_field_intervalo"), self.v_int, 0)
        campo(_("welcome_field_duracion"),   self.v_dur, 1)
        campo(_("welcome_field_hora_ini"),   self.v_ini, 2)
        campo(_("welcome_field_hora_fin"),   self.v_fin, 3)
        campo(_("welcome_field_meta"),       self.v_meta, 4)

        ctk.CTkLabel(f, text=_("welcome_ej_subheading"), font=("Segoe UI", 9, "bold"),
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

        self.lbl_err = ctk.CTkLabel(f, text="", font=("Segoe UI", 9), text_color=C.ACCENT2)
        self.lbl_err.pack()
        self._dots(f)
        bf = ctk.CTkFrame(f, fg_color="transparent")
        bf.pack(pady=(0, 20))
        ctk.CTkButton(bf, text=_("back_step"), fg_color=C.BG3, text_color=C.TEXT,
                      font=("Segoe UI", 10), corner_radius=12,
                      command=self._prev).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=_("next_step"), fg_color=C.ACCENT, text_color=C.BG,
                      font=("Segoe UI", 10, "bold"), corner_radius=12,
                      command=self._save_and_next).pack(side="left", padx=4)

    def _step_listo(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_step2_heading"), font=("Segoe UI", 15, "bold"),
                     text_color=C.TEXT).pack(pady=(20, 2))
        ctk.CTkLabel(f, text=_("welcome_step2_info"),
                     font=("Segoe UI", 10), text_color=C.TEXT_MUTED).pack(pady=(12, 14))
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
            ctk.CTkLabel(row, text=lbl, font=("Segoe UI", 10),
                         text_color=C.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=val, font=("Segoe UI", 10, "bold"),
                         text_color=C.TEXT).pack(side="right")
        ctk.CTkLabel(f, text=_("welcome_step2_tray_info"),
                     font=("Segoe UI", 9), text_color=C.TEXT_MUTED).pack(pady=(10, 4))
        self._dots(f)
        ctk.CTkButton(f, text=_("welcome_start"), fg_color=C.GREEN, text_color=C.BG,
                      font=("Segoe UI", 11, "bold"), corner_radius=12,
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


# ═══════════════════════════════════════════════════════════════════════════
# UninstallWindow
# ═══════════════════════════════════════════════════════════════════════════

class UninstallWindow(CenteredWindow):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_quit: Callable[[], None],
        config_file: str,
        stats_file: str,
        hist_file: str,
        app_dir: str,
    ) -> None:
        super().__init__(parent)
        self.on_quit: Callable[[], None] = on_quit
        self._config_file: str = config_file
        self._stats_file: str = stats_file
        self._hist_file: str = hist_file
        self._app_dir: str = app_dir
        self.title(_("uninstall_title"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self._build()
        self.center()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self) -> None:
        main = _card(self, fg_color=C.BG2)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(main, text=_("uninstall_heading"), font=("Segoe UI", 14, "bold"),
                     text_color=C.TEXT).pack(pady=(14, 0))

        ctk.CTkLabel(main, text=_("uninstall_warning"),
                     font=("Segoe UI", 9), text_color=C.TEXT_MUTED, justify="center",
                     wraplength=340).pack(pady=(12, 10))
        box = _card(main)
        box.pack(fill="x")
        self.v_autoarranque = ctk.BooleanVar(value=True)
        self.v_datos = ctk.BooleanVar(value=True)
        self.v_accesos = ctk.BooleanVar(value=True)
        self.v_carpeta = ctk.BooleanVar(value=True)
        opciones: list[tuple[ctk.BooleanVar, str]] = [
            (self.v_autoarranque, _("uninstall_opt_auto")),
            (self.v_datos,        _("uninstall_opt_datos")),
            (self.v_accesos,      _("uninstall_opt_accesos")),
            (self.v_carpeta,      _("uninstall_opt_carpeta")),
        ]
        for var, texto in opciones:
            _checkbox(box, texto, var).pack(anchor="w", padx=10, pady=5)
        self.lbl_estado = ctk.CTkLabel(main, text="", font=("Segoe UI", 9), text_color=C.TEXT_MUTED)
        self.lbl_estado.pack(pady=(4, 4))
        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(0, 20))
        ctk.CTkButton(bf, text=_("cancelar"), fg_color=C.BG3, text_color=C.TEXT,
                      font=("Segoe UI", 10), corner_radius=12,
                      command=self.destroy).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=_("uninstall_btn"), fg_color=C.ACCENT2, text_color=C.BG,
                      font=("Segoe UI", 10, "bold"), corner_radius=12,
                      command=self._confirmar).pack(side="left", padx=4)

    def _confirmar(self) -> None:
        import tkinter.messagebox as mb
        ok: bool = mb.askyesno(
            _("uninstall_confirm_title"),
            _("uninstall_confirm_msg"),
            icon="warning",
            parent=self,
        )
        if not ok:
            return
        self._ejecutar()

    def _ejecutar(self) -> None:
        import tkinter.messagebox as mb
        errores: list[str] = []
        if self.v_autoarranque.get():
            self.lbl_estado.configure(text=_("uninstall_status_auto"))
            self.update()
            try:
                set_autoarranque(False, "")
            except Exception as e:
                errores.append(f"Autoarranque: {e}")
        if self.v_datos.get():
            self.lbl_estado.configure(text=_("uninstall_status_datos"))
            self.update()
            for f in [self._config_file, self._stats_file, self._hist_file]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception as e:
                    errores.append(f"Archivo {os.path.basename(f)}: {e}")
        if self.v_accesos.get():
            self.lbl_estado.configure(text=_("uninstall_status_accesos"))
            self.update()
            _eliminar_accesos_directos(errores)
        try:
            _quitar_registro_desinstalador()
        except Exception:
            pass
        if self.v_carpeta.get():
            install_dir: str = _get_install_dir_from_registry() or self._app_dir
            if install_dir and os.path.isdir(install_dir):
                _programar_borrado_carpeta(install_dir)
        if errores:
            mb.showwarning(
                _("uninstall_warn_title"),
                _("uninstall_warn_msg") + "\n" + "\n".join(errores),
                parent=self,
            )
        else:
            mb.showinfo(
                _("uninstall_ok_title"),
                _("uninstall_ok_msg"),
                parent=self,
            )
        self.destroy()
        self.on_quit()


# ═══════════════════════════════════════════════════════════════════════════
# Alias backward-compatible
# ═══════════════════════════════════════════════════════════════════════════

PausaWindow = BreakWindow
