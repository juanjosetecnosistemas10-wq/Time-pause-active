"""Todas las ventanas de la UI."""

from __future__ import annotations

import os
import random
import subprocess
import sys
import threading
import winreg
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from pausa_activa.constants import (
    BG, BG2, BG3, ACCENT, ACCENT2, GREEN, YELLOW, TEXT, TEXT_DIM, BORDER, AGUA,
    APP_NAME, EJERCICIOS, FRASES, set_theme, set_idioma, _, I18N, THEMES,
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
# Widgets reutilizables modernos
# ═══════════════════════════════════════════════════════════════════════════

class ModernButton(tk.Canvas):
    """Botón moderno con hover effect y bordes redondeados."""
    def __init__(
        self, parent: tk.Widget, text: str, command: Callable[[], Any] | None = None,
        bg_color: str = ACCENT, fg_color: str = TEXT, hov_color: str | None = None,
        font: tuple[str, int, str] = ("Segoe UI", 10), padx: int = 20, pady: int = 8,
        **kwargs: Any,
    ) -> None:
        self._bg = bg_color
        self._fg = fg_color
        self._hov = hov_color or self._lighten(bg_color)
        self._cmd = command
        self._font = font
        self._padx = padx
        self._pady = pady
        self._text = text
        super().__init__(parent, bg=BG, highlightthickness=0, relief="flat", **kwargs)
        self._text_id: int | None = None
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _lighten(self, color: str) -> str:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw(self) -> None:
        self.delete("all")
        # Measure text
        tmp = tk.Label(self, text=self._text, font=self._font)
        tmp.update_idletasks()
        tw = tmp.winfo_reqwidth()
        th = tmp.winfo_reqheight()
        tmp.destroy()
        w = tw + self._padx * 2 + 16
        h = th + self._pady * 2 + 8
        r = 8
        self.configure(width=w, height=h)
        self.coords("all")
        self.create_rounded_rect(0, 0, w, h, r, fill=self._bg, outline="", tags="bg")
        self._text_id = self.create_text(
            w // 2, h // 2, text=self._text, font=self._font,
            fill=self._fg, tags="txt", anchor="center"
        )

    def create_rounded_rect(
        self, x1: float, y1: float, x2: float, y2: float, r: float,
        **kwargs: Any,
    ) -> int:
        points = [
            x1 + r, y1, x1 + r, y1, x2 - r, y1,
            x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y1 + r, x2, y2 - r, x2, y2 - r,
            x2, y2, x2 - r, y2, x2 - r, y2,
            x1 + r, y2, x1 + r, y2, x1, y2,
            x1, y2 - r, x1, y2 - r, x1, y1 + r,
            x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, _: Any) -> None:
        if self._text_id:
            self.itemconfig("bg", fill=self._hov)

    def _on_leave(self, _: Any) -> None:
        if self._text_id:
            self.itemconfig("bg", fill=self._bg)

    def _on_click(self, _: Any) -> None:
        if self._cmd:
            self._cmd()


def _card(parent: tk.Widget, **kwargs: Any) -> tk.Frame:
    """Crea una tarjeta con borde sutil."""
    f = tk.Frame(parent, bg=BG2, highlightthickness=1, highlightbackground=BORDER, **kwargs)
    return f


def _label(parent: tk.Widget, text: str, **kwargs: Any) -> tk.Label:
    return tk.Label(parent, text=text, bg=parent["bg"], fg=TEXT,
                    font=("Segoe UI", 10), **kwargs)


def _heading(parent: tk.Widget, text: str, **kwargs: Any) -> tk.Label:
    return tk.Label(parent, text=text, bg=parent["bg"], fg=TEXT,
                    font=("Segoe UI", 13, "bold"), **kwargs)


def _subheading(parent: tk.Widget, text: str, **kwargs: Any) -> tk.Label:
    return tk.Label(parent, text=text, bg=parent["bg"], fg=TEXT_DIM,
                    font=("Segoe UI", 9, "bold"), **kwargs)


def _entry(parent: tk.Widget, variable: tk.StringVar, width: int = 10) -> tk.Entry:
    return tk.Entry(parent, textvariable=variable, font=("Segoe UI", 11),
                    bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0,
                    width=width, highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=ACCENT)


def _checkbox(parent: tk.Widget, text: str, variable: tk.BooleanVar) -> tk.Checkbutton:
    return tk.Checkbutton(parent, text=f"  {text}", variable=variable,
                          font=("Segoe UI", 9), bg=parent["bg"], fg=TEXT,
                          selectcolor=BG3 if BG != BG3 else BG2,
                          activebackground=parent["bg"], activeforeground=TEXT)


def _radio(parent: tk.Widget, text: str, variable: tk.StringVar, value: str) -> tk.Radiobutton:
    return tk.Radiobutton(parent, text=f"  {text}", variable=variable, value=value,
                          font=("Segoe UI", 9), bg=parent["bg"], fg=TEXT,
                          selectcolor=BG3 if BG != BG3 else BG2,
                          activebackground=parent["bg"], activeforeground=TEXT)


# ═══════════════════════════════════════════════════════════════════════════
# Clase base
# ═══════════════════════════════════════════════════════════════════════════

class CenteredWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent, *args, **kwargs)
        self.configure(bg=BG)
        self.resizable(False, False)

    def center(self) -> None:
        self.update_idletasks()
        w: int = self.winfo_width()
        h: int = self.winfo_height()
        sw: int = self.winfo_screenwidth()
        sh: int = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


# ═══════════════════════════════════════════════════════════════════════════
# Gráfico de barras simple para stats
# ═══════════════════════════════════════════════════════════════════════════

def _dibujar_grafico(parent: tk.Frame, history: dict[str, dict[str, Any]], meta: int) -> None:
    """Dibuja un gráfico de barras ASCII/texto para los últimos 7 días."""
    import datetime as dt
    from calendar import day_abbr
    p_bg: str = parent["bg"] if parent else BG
    today = dt.date.today()
    days: list[str] = [(today - dt.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    max_val: int = max(
        (history.get(d, {}).get("completadas", 0) for d in days),
        default=meta,
    )
    max_val = max(max_val, meta, 1)
    bar_chars: str = "█▇▆▅▄▃▂▁"
    for dia_iso in days:
        data = history.get(dia_iso, {"completadas": 0, "saltadas": 0})
        comp = data["completadas"]
        bar_len: int = int((comp / max_val) * 10) if max_val else 0
        bar: str = bar_chars[0] * bar_len if bar_len else "▁"
        weekday_num: int = dt.date.fromisoformat(dia_iso).weekday()
        weekday_name: str = day_abbr[weekday_num]
        row = tk.Frame(parent, bg=p_bg)
        row.pack(fill="x", padx=8, pady=1)
        tk.Label(row, text=f"{weekday_name}", font=("Segoe UI", 7), bg=p_bg,
                 fg=TEXT_DIM, width=4, anchor="e").pack(side="left")
        tk.Label(row, text=bar, font=("Segoe UI", 8), bg=p_bg, fg=ACCENT,
                 anchor="w").pack(side="left", padx=(4, 0))
        tk.Label(row, text=f"{comp}", font=("Segoe UI", 7), bg=p_bg,
                 fg=TEXT_DIM).pack(side="left", padx=(4, 0))


# ═══════════════════════════════════════════════════════════════════════════
# PausaWindow
# ═══════════════════════════════════════════════════════════════════════════

class PausaWindow(CenteredWindow):
    def __init__(
        self,
        parent: tk.Tk,
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
        self.ejercicio: dict[str, Any] = ejercicio
        self._job: str | None = None
        self.title("Pausa Activa")
        self.attributes("-topmost", True)
        self._build()
        self.center()
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._skip)
        if sonido_ambiente != "ninguno":
            audio_manager.start_ambient(sonido_ambiente)

    def _build(self) -> None:
        # Header con gradiente visual
        header = tk.Frame(self, bg=ACCENT, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=_("pausa_activa"), font=("Segoe UI", 10, "bold"),
                 bg=ACCENT, fg=BG).pack(expand=True)

        # Icono grande
        tk.Label(self, text=self.ejercicio["icono"], font=("Segoe UI Emoji", 56),
                 bg=BG).pack(pady=(16, 0))
        tk.Label(self, text=self.ejercicio["nombre"], font=("Segoe UI", 16, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(4, 0))

        # Tarjeta de pasos
        fp = _card(self)
        fp.pack(padx=28, fill="x", pady=(12, 8))
        for i, paso in enumerate(self.ejercicio["pasos"], 1):
            r = tk.Frame(fp, bg=BG2)
            r.pack(fill="x", padx=14, pady=5)
            num = tk.Label(r, text=f"{i}", font=("Segoe UI", 8, "bold"),
                           bg=ACCENT, fg=BG, width=2, height=1)
            num.pack(side="left", padx=(0, 10))
            tk.Label(r, text=paso, font=("Segoe UI", 10), bg=BG2,
                     fg=TEXT, wraplength=280, justify="left").pack(side="left")

        # Timer grande
        self.lbl_t = tk.Label(self, text=self._fmt_time(self.remaining),
                              font=("Segoe UI", 40, "bold"), bg=BG, fg=GREEN)
        self.lbl_t.pack(pady=(10, 2))
        tk.Label(self, text=_("tiempo_restante"), font=("Segoe UI", 8),
                 bg=BG, fg=TEXT_DIM).pack()

        # Barra de progreso
        pb_frame = tk.Frame(self, bg=BG3, height=6, width=340)
        pb_frame.pack(pady=(10, 0))
        pb_frame.pack_propagate(False)
        self._pb_fill = tk.Frame(pb_frame, bg=GREEN, height=6, width=340)
        self._pb_fill.pack(side="left", anchor="w")

        ModernButton(self, text=_("saltar_pausa"), bg_color=BG3, fg_color=TEXT_DIM,
                     font=("Segoe UI", 9), padx=16, pady=4,
                     command=self._skip).pack(pady=(16, 20))

    @staticmethod
    def _fmt_time(s: int) -> str:
        m, s = divmod(max(0, int(s)), 60)
        return f"{m:02d}:{s:02d}"

    def _tick(self) -> None:
        if self.remaining <= 0:
            self._done()
            return
        self.lbl_t.config(text=self._fmt_time(self.remaining))
        pct = max(0, int(340 * self.remaining / (self.remaining + 1)))
        self._pb_fill.configure(width=pct)
        self.remaining -= 1
        self._job = self.after(1000, self._tick)

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
# StatsWindow con gráfico
# ═══════════════════════════════════════════════════════════════════════════

class StatsWindow(CenteredWindow):
    def __init__(
        self,
        parent: tk.Tk,
        stats: dict[str, Any],
        meta: int,
        hist_file: str,
        history: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(_("estadisticas"))
        self.attributes("-topmost", True)
        total: int = stats["completadas"] + stats["saltadas"]
        pct: int = int(stats["completadas"] / total * 100) if total else 0
        meta_ok: bool = stats["completadas"] >= meta

        # Header
        header = tk.Frame(self, bg=ACCENT, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=_("estadisticas"), font=("Segoe UI", 11, "bold"),
                 bg=ACCENT, fg=BG).pack(expand=True)

        # Tarjeta principal de stats
        card = _card(self)
        card.pack(padx=24, fill="x", pady=(16, 8))
        rows: list[tuple[str, str, str]] = [
            ("Pausas completadas", f"{stats['completadas']} / {meta}", GREEN),
            ("Pausas saltadas",    str(stats["saltadas"]),              ACCENT2),
            ("Tasa de exito",      f"{pct}%",                          ACCENT),
            ("Racha actual",       f"{stats.get('racha', 0)} días consecutivos", YELLOW),
            ("Meta diaria",        "✓ CUMPLIDA" if meta_ok else "○ En progreso",
             GREEN if meta_ok else TEXT_DIM),
        ]
        for label, val, color in rows:
            r = tk.Frame(card, bg=BG2)
            r.pack(fill="x", padx=16, pady=7)
            tk.Label(r, text=label, font=("Segoe UI", 10), bg=BG2,
                     fg=TEXT_DIM, anchor="w").pack(side="left")
            tk.Label(r, text=val, font=("Segoe UI", 11, "bold"), bg=BG2,
                     fg=color).pack(side="right")

        # Gráfico semanal
        if history:
            _subheading(self, text="Últimos 7 días").pack(pady=(10, 2), anchor="w", padx=28)
            graph_card = _card(self)
            graph_card.pack(padx=28, fill="x")
            _dibujar_grafico(graph_card, history, meta)

        # Historial
        if stats["historial"]:
            _subheading(self, text="Últimas pausas").pack(pady=(10, 2), anchor="w", padx=28)
            hist_card = _card(self)
            hist_card.pack(padx=28, fill="x", pady=(0, 12))
            for entry in stats["historial"][-5:][::-1]:
                color = GREEN if entry["estado"] == "completada" else ACCENT2
                r = tk.Frame(hist_card, bg=BG2)
                r.pack(fill="x", padx=14, pady=4)
                tk.Label(r, text=f"{entry['hora']}  •  {entry['ejercicio']}",
                         font=("Segoe UI", 9), bg=BG2,
                         fg=color).pack(side="left")
                tk.Label(r, text=f"[{entry['estado']}]",
                         font=("Segoe UI", 8, "bold"), bg=BG2,
                         fg=color).pack(side="right")

        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=14)
        ModernButton(bf, text=_("exportar_csv"), bg_color=BG3, fg_color=TEXT,
                     font=("Segoe UI", 9), padx=14, pady=4,
                     command=lambda: self._open_csv(hist_file)).pack(side="left", padx=4)
        ModernButton(bf, text=_("cerrar"), bg_color=ACCENT, fg_color=BG,
                     font=("Segoe UI", 10, "bold"), padx=20, pady=6,
                     command=self.destroy).pack(side="left", padx=4)
        self.center()

    @staticmethod
    def _open_csv(hist_file: str) -> None:
        if os.path.exists(hist_file):
            subprocess.run(["notepad.exe", hist_file])


# ═══════════════════════════════════════════════════════════════════════════
# ConfigWindow con perfiles, temas, modos, idioma, notificaciones
# ═══════════════════════════════════════════════════════════════════════════

class ConfigWindow(CenteredWindow):
    def __init__(
        self,
        parent: tk.Tk,
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
        self._build()
        self.center()

    def _field(self, parent: tk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        tk.Label(parent, text=label, font=("Segoe UI", 10), bg=BG2,
                 fg=TEXT_DIM, anchor="w").grid(
            row=row, column=0, sticky="w", padx=16, pady=8)
        _entry(parent, var).grid(row=row, column=1, padx=16, pady=8, sticky="e")

    def _tab(self, nb: ttk.Notebook, title: str) -> tk.Frame:
        f = tk.Frame(nb, bg=BG, padx=14, pady=10)
        nb.add(f, text=f"  {title}  ")
        return f

    def _config_style(self, style_name: str, color: str) -> None:
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure(style_name, troughcolor=BG3, background=color,
                    bordercolor=BG3, lightcolor=color, darkcolor=color)

    def _build(self) -> None:
        # Header
        header = tk.Frame(self, bg=ACCENT, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=_("configuracion"), font=("Segoe UI", 11, "bold"),
                 bg=ACCENT, fg=BG).pack(expand=True)

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Dark.TNotebook", background=BG, borderwidth=0)
        style.configure("Dark.TNotebook.Tab", background=BG3, foreground=TEXT_DIM,
                        padding=[12, 5], font=("Segoe UI", 9))
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", TEXT)])
        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # ── TAB 1: Temporizador ──
        t1 = self._tab(nb, _("config_temporizador"))
        self.v_int = tk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = tk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = tk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = tk.StringVar(value=self.cfg["hora_fin"])
        self.v_pos = tk.StringVar(value=str(self.cfg["posponer_min"]))
        self.v_meta = tk.StringVar(value=str(self.cfg["meta_pausas"]))
        self.v_modo = tk.StringVar(value=self.cfg.get("modo", "normal"))

        card_t1 = _card(t1)
        card_t1.pack(fill="x")
        self._field(card_t1, "Intervalo entre pausas (min)", self.v_int, 0)
        self._field(card_t1, "Duración de la pausa (min)",   self.v_dur, 1)
        self._field(card_t1, "Hora inicio (HH:MM)",          self.v_ini, 2)
        self._field(card_t1, "Hora fin (HH:MM)",             self.v_fin, 3)
        self._field(card_t1, "Minutos para posponer",        self.v_pos, 4)
        self._field(card_t1, "Meta de pausas diarias",       self.v_meta, 5)

        modo_card = _card(t1)
        modo_card.pack(fill="x", pady=(8, 0))
        _subheading(modo_card, text="Modo de timer").pack(anchor="w", padx=14, pady=(8, 4))
        for val, lbl in [("normal", _("modo_normal")),
                         ("pomodoro", _("modo_pomodoro"))]:
            _radio(modo_card, lbl, self.v_modo, val).pack(anchor="w", padx=14, pady=2)
        tk.Label(modo_card, text="Pomodoro: 25 min trabajo / 5 min pausa",
                 font=("Segoe UI", 7), bg=BG2, fg=TEXT_DIM).pack(anchor="w", padx=14, pady=(0, 8))

        # ── TAB 2: Opciones ──
        t2 = self._tab(nb, _("config_opciones"))
        _subheading(t2, text="No molestar").pack(anchor="w", pady=(4, 2))
        nm_card = _card(t2)
        nm_card.pack(fill="x")
        self.v_nm = tk.BooleanVar(value=self.cfg.get("no_molestar", True))
        self.v_fs = tk.BooleanVar(value=self.cfg.get("fin_de_semana", False))
        _checkbox(nm_card, _("no_molestar"), self.v_nm).pack(anchor="w", padx=10, pady=5)
        _checkbox(nm_card, _("fin_de_semana_opt"), self.v_fs).pack(anchor="w", padx=10, pady=(0, 5))

        _subheading(t2, text="Recordatorio de agua").pack(anchor="w", pady=(10, 2))
        agua_card = _card(t2)
        agua_card.pack(fill="x")
        self.v_agua = tk.BooleanVar(value=self.cfg.get("agua_activo", True))
        self.v_agua_min = tk.StringVar(value=str(self.cfg.get("agua_min", 30)))
        _checkbox(agua_card, "Activar recordatorio de hidratación", self.v_agua).pack(
            anchor="w", padx=10, pady=5)
        row_agua = tk.Frame(agua_card, bg=BG2)
        row_agua.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(row_agua, text="Cada cuantos minutos:", font=("Segoe UI", 9),
                 bg=BG2, fg=TEXT_DIM).pack(side="left")
        _entry(row_agua, self.v_agua_min, width=5).pack(side="left", padx=8)

        _subheading(t2, text="General").pack(anchor="w", pady=(10, 2))
        self.v_snd = tk.BooleanVar(value=self.cfg["sonido"])
        self.v_auto = tk.BooleanVar(value=get_autoarranque())
        gen_card = _card(t2)
        gen_card.pack(fill="x")
        _checkbox(gen_card, _("sonido_alerta"), self.v_snd).pack(anchor="w", padx=10, pady=4)
        _checkbox(gen_card, _("autoarranque"), self.v_auto).pack(anchor="w", padx=10, pady=4)

        _subheading(t2, text="Perfiles").pack(anchor="w", pady=(10, 2))
        perfil_card = _card(t2)
        perfil_card.pack(fill="x")
        self.v_perfil = tk.StringVar(value=self.cfg.get("perfil", "default"))
        for p in self._profiles:
            _radio(perfil_card, p, self.v_perfil, p).pack(anchor="w", padx=10, pady=2)

        _subheading(t2, text="Idioma").pack(anchor="w", pady=(10, 2))
        lang_card = _card(t2)
        lang_card.pack(fill="x")
        self.v_idioma = tk.StringVar(value=self.cfg.get("idioma", "es"))
        for val, lbl in [("es", "Español"), ("en", "English")]:
            _radio(lang_card, lbl, self.v_idioma, val).pack(anchor="w", padx=10, pady=2)

        # ── TAB 3: Sonido ──
        t3 = self._tab(nb, _("config_sonido"))
        _subheading(t3, text="Sonido ambiente durante la pausa").pack(anchor="w", pady=(4, 6))
        amb_card = _card(t3)
        amb_card.pack(fill="x")
        self.v_amb = tk.StringVar(value=self.cfg.get("sonido_ambiente", "ninguno"))
        for val, lbl in [("ninguno", _("sin_sonido")), ("lluvia", _("lluvia")),
                         ("naturaleza", _("naturaleza"))]:
            _radio(amb_card, f"  {lbl}", self.v_amb, val).pack(anchor="w", padx=12, pady=6)

        _subheading(t3, text="Notificaciones").pack(anchor="w", pady=(10, 2))
        notif_card = _card(t3)
        notif_card.pack(fill="x")
        self.v_notif_sound = tk.StringVar(value=self.cfg.get("notificacion_sonido", "default"))
        self.v_notif_dur = tk.StringVar(value=self.cfg.get("notificacion_duracion", "short"))
        tk.Label(notif_card, text="Sonido:", font=("Segoe UI", 9),
                 bg=BG2, fg=TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 2))
        for val, lbl in [("default", "Default"), ("sms", "SMS"), ("mail", "Mail"),
                         ("reminder", "Recordatorio")]:
            _radio(notif_card, lbl, self.v_notif_sound, val).pack(anchor="w", padx=10, pady=1)
        tk.Label(notif_card, text="Duración:", font=("Segoe UI", 9),
                 bg=BG2, fg=TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 2))
        for val, lbl in [("short", "Corta"), ("long", "Larga")]:
            _radio(notif_card, lbl, self.v_notif_dur, val).pack(anchor="w", padx=10, pady=1)

        # ── TAB 4: Ejercicios ──
        t4 = self._tab(nb, _("config_ejercicios"))
        _subheading(t4, text="Marca los ejercicios que quieres incluir:").pack(anchor="w", pady=(0, 6))
        ej_card = _card(t4)
        ej_card.pack(fill="x")
        self.ej_vars: dict[str, tk.BooleanVar] = {}
        activos: list[str] = self.cfg.get("ejercicios_activos",
                                           [e["id"] for e in EJERCICIOS])
        for ej in EJERCICIOS:
            v = tk.BooleanVar(value=ej["id"] in activos)
            self.ej_vars[ej["id"]] = v
            r = tk.Frame(ej_card, bg=BG2)
            r.pack(fill="x", padx=10, pady=3)
            _checkbox(r, f"{ej['icono']} {ej['nombre']}", v).pack(side="left")

        _subheading(t4, text="Tema").pack(anchor="w", pady=(10, 2))
        tema_card = _card(t4)
        tema_card.pack(fill="x")
        self.v_tema = tk.StringVar(value=self.cfg.get("tema", "oscuro"))
        for val, lbl in [("oscuro", "🌙 Oscuro"), ("claro", "☀️ Claro")]:
            _radio(tema_card, lbl, self.v_tema, val).pack(anchor="w", padx=10, pady=2)

        self.lbl_err = tk.Label(self, text="", font=("Segoe UI", 9), bg=BG, fg=ACCENT2)
        self.lbl_err.pack()
        ModernButton(self, text=_("guardar"), bg_color=ACCENT, fg_color=BG,
                     font=("Segoe UI", 10, "bold"), padx=28, pady=8,
                     command=self._save).pack(pady=(8, 14))

    def _validate_positive_ints(self, *values: int) -> None:
        for v in values:
            if v <= 0:
                raise ValueError("Todos los valores deben ser positivos")

    def _save(self) -> None:
        try:
            iv = int(self.v_int.get())
            dv = int(self.v_dur.get())
            pv = int(self.v_pos.get())
            mv = int(self.v_meta.get())
            amv = int(self.v_agua_min.get())
            self._validate_positive_ints(iv, dv, pv, mv, amv)
            h0, m0 = map(int, self.v_ini.get().split(":"))
            h1, m1 = map(int, self.v_fin.get().split(":"))
            if not (0 <= h0 < 24 and 0 <= m0 < 60 and 0 <= h1 < 24 and 0 <= m1 < 60):
                raise ValueError("Hora inválida")
            if (h1, m1) <= (h0, m0):
                raise ValueError("Hora fin debe ser mayor que hora inicio")
        except ValueError as e:
            self.lbl_err.config(text=f"Error: {e}")
            return
        except Exception:
            self.lbl_err.config(text="Revisa los valores ingresados")
            return
        activos = [eid for eid, v in self.ej_vars.items() if v.get()]
        if not activos:
            self.lbl_err.config(text="Selecciona al menos un ejercicio")
            return
        set_autoarranque(self.v_auto.get(), self._app_path)

        # Aplicar tema si cambió
        nuevo_tema = self.v_tema.get()
        if nuevo_tema != self.cfg.get("tema"):
            set_theme(nuevo_tema)

        # Aplicar idioma si cambió
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
        parent: tk.Tk,
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
        self.title("Bienvenido a Pausas Activas")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self._build()
        self.center()

    def _build(self) -> None:
        self._frame = tk.Frame(self, bg=BG)
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

    def _dots(self, parent: tk.Frame) -> None:
        f = tk.Frame(parent, bg=BG)
        f.pack(pady=(0, 16))
        for i in range(3):
            color = ACCENT if i == self.step else BG3
            tk.Label(f, text="●", font=("Segoe UI", 10), bg=BG,
                     fg=color).pack(side="left", padx=3)

    def _step_bienvenida(self) -> None:
        f = self._frame
        # Header
        hdr = tk.Frame(f, bg=ACCENT, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="👋  Bienvenido", font=("Segoe UI", 14, "bold"),
                 bg=ACCENT, fg=BG).pack(expand=True)

        tk.Label(f, text=_("bienvenido"), font=("Segoe UI", 15, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(16, 2))
        tk.Label(f, text="Tu asistente de bienestar en el trabajo",
                 font=("Segoe UI", 10), bg=BG, fg=TEXT_DIM).pack(pady=(0, 16))
        cards = [
            ("⏱", "Recordatorios automáticos", "Te avisa cada cierto tiempo para que hagas una pausa activa."),
            ("🏃", "Ejercicios guiados",        "Cuello, espalda, ojos, respiración y más."),
            ("💧", "Hidratación",               "Recordatorios para que tomes agua regularmente."),
            ("📊", "Estadísticas",              "Lleva el registro de tus pausas y rachas diarias."),
        ]
        for ico, titulo, desc in cards:
            row = _card(f)
            row.pack(fill="x", padx=24, pady=3)
            tk.Label(row, text=ico, font=("Segoe UI Emoji", 20), bg=BG2).pack(side="left", padx=(12, 6), pady=8)
            col = tk.Frame(row, bg=BG2)
            col.pack(side="left", pady=6)
            tk.Label(col, text=titulo, font=("Segoe UI", 10, "bold"), bg=BG2, fg=TEXT, anchor="w").pack(anchor="w")
            tk.Label(col, text=desc, font=("Segoe UI", 9), bg=BG2, fg=TEXT_DIM, anchor="w", wraplength=280).pack(anchor="w")
        self._dots(f)
        ModernButton(f, text="Siguiente →", bg_color=ACCENT, fg_color=BG,
                     font=("Segoe UI", 10, "bold"), padx=28, pady=8,
                     command=self._next).pack(pady=(0, 24))

    def _step_config(self) -> None:
        f = self._frame
        hdr = tk.Frame(f, bg=ACCENT, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙️  Configura tu rutina", font=("Segoe UI", 11, "bold"),
                 bg=ACCENT, fg=BG).pack(expand=True)

        tk.Label(f, text="Puedes cambiar esto después en Configuración",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM).pack(pady=(8, 12))

        card_cfg = _card(f)
        card_cfg.pack(fill="x", padx=24)

        self.v_int = tk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = tk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = tk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = tk.StringVar(value=self.cfg["hora_fin"])
        self.v_meta = tk.StringVar(value=str(self.cfg["meta_pausas"]))

        def campo(lbl: str, var: tk.StringVar, row: int) -> None:
            tk.Label(card_cfg, text=lbl, font=("Segoe UI", 10), bg=BG2,
                     fg=TEXT_DIM, anchor="w").grid(row=row, column=0, sticky="w", padx=14, pady=7)
            _entry(card_cfg, var).grid(row=row, column=1, padx=14, pady=7, sticky="e")

        campo("Intervalo entre pausas (min)", self.v_int, 0)
        campo("Duración de la pausa (min)",   self.v_dur, 1)
        campo("Hora inicio (HH:MM)",          self.v_ini, 2)
        campo("Hora fin (HH:MM)",             self.v_fin, 3)
        campo("Meta de pausas diarias",       self.v_meta, 4)

        _subheading(f, text="Ejercicios a incluir:").pack(anchor="w", padx=28, pady=(8, 4))
        ej_card = _card(f)
        ej_card.pack(fill="x", padx=24)
        self.ej_vars = {}
        activos = self.cfg.get("ejercicios_activos", [e["id"] for e in EJERCICIOS])
        cols = 2
        for i, ej in enumerate(EJERCICIOS):
            v = tk.BooleanVar(value=ej["id"] in activos)
            self.ej_vars[ej["id"]] = v
            r, c = divmod(i, cols)
            _checkbox(ej_card, f"{ej['icono']} {ej['nombre']}", v).grid(
                row=r, column=c, sticky="w", padx=10, pady=3)

        self.lbl_err = tk.Label(f, text="", font=("Segoe UI", 9), bg=BG, fg=ACCENT2)
        self.lbl_err.pack()
        self._dots(f)
        bf = tk.Frame(f, bg=BG)
        bf.pack(pady=(0, 20))
        ModernButton(bf, text="← Atrás", bg_color=BG3, fg_color=TEXT,
                     font=("Segoe UI", 10), padx=16, pady=6,
                     command=self._prev).pack(side="left", padx=4)
        ModernButton(bf, text="Siguiente →", bg_color=ACCENT, fg_color=BG,
                     font=("Segoe UI", 10, "bold"), padx=24, pady=6,
                     command=self._save_and_next).pack(side="left", padx=4)

    def _step_listo(self) -> None:
        f = self._frame
        hdr = tk.Frame(f, bg=GREEN, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎉  ¡Todo listo!", font=("Segoe UI", 15, "bold"),
                 bg=GREEN, fg=BG if BG == "#111827" else "#FFFFFF").pack(expand=True)

        tk.Label(f, text="La app ya está configurada y lista para cuidarte.",
                 font=("Segoe UI", 10), bg=BG, fg=TEXT_DIM).pack(pady=(16, 16))
        resumen = _card(f)
        resumen.pack(fill="x", padx=28)
        items = [
            ("⏱ Intervalo",  f"Cada {self.cfg['intervalo_min']} min"),
            ("🕐 Duración",  f"{self.cfg['duracion_pausa_min']} min de pausa"),
            ("🕗 Horario",   f"{self.cfg['hora_inicio']} a {self.cfg['hora_fin']}"),
            ("🎯 Meta",      f"{self.cfg['meta_pausas']} pausas por día"),
        ]
        for lbl, val in items:
            row = tk.Frame(resumen, bg=BG2)
            row.pack(fill="x", padx=14, pady=5)
            tk.Label(row, text=lbl, font=("Segoe UI", 10), bg=BG2, fg=TEXT_DIM).pack(side="left")
            tk.Label(row, text=val, font=("Segoe UI", 10, "bold"), bg=BG2, fg=TEXT).pack(side="right")
        tk.Label(f, text="La app se minimizará a la bandeja del sistema.",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM).pack(pady=(10, 4))
        self._dots(f)
        ModernButton(f, text="¡Empezar! 🚀", bg_color=GREEN, fg_color=BG,
                     font=("Segoe UI", 11, "bold"), padx=32, pady=10,
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
            iv = int(self.v_int.get())
            dv = int(self.v_dur.get())
            mv = int(self.v_meta.get())
            if iv <= 0 or dv <= 0 or mv <= 0:
                raise ValueError("Los valores deben ser positivos")
            h0, m0 = map(int, self.v_ini.get().split(":"))
            h1, m1 = map(int, self.v_fin.get().split(":"))
            if not (0 <= h0 < 24 and 0 <= m0 < 60):
                raise ValueError("Hora inicio inválida")
            if not (0 <= h1 < 24 and 0 <= m1 < 60):
                raise ValueError("Hora fin inválida")
            if (h1, m1) <= (h0, m0):
                raise ValueError("Hora fin debe ser mayor que hora inicio")
        except ValueError as e:
            self.lbl_err.config(text=f"Error: {e}")
            return
        except Exception:
            self.lbl_err.config(text="Revisa los valores ingresados")
            return

        activos = [eid for eid, v in self.ej_vars.items() if v.get()]
        if not activos:
            self.lbl_err.config(text="Selecciona al menos un ejercicio")
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
        parent: tk.Tk,
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
        self.title("Desinstalar Pausas Activas")
        self.attributes("-topmost", True)
        self._build()
        self.center()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=ACCENT2, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🗑️  Desinstalar", font=("Segoe UI", 12, "bold"),
                 bg=ACCENT2, fg=BG).pack(expand=True)

        tk.Label(self, text="Esta acción eliminará la configuración de la app y no puede deshacerse.",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM, justify="center", wraplength=320).pack(pady=(14, 12))
        box = _card(self)
        box.pack(padx=24, fill="x")
        self.v_autoarranque = tk.BooleanVar(value=True)
        self.v_datos = tk.BooleanVar(value=True)
        self.v_accesos = tk.BooleanVar(value=True)
        self.v_carpeta = tk.BooleanVar(value=True)
        opciones = [
            (self.v_autoarranque, "Quitar del autoarranque de Windows"),
            (self.v_datos,        "Eliminar configuración, estadísticas e historial"),
            (self.v_accesos,      "Eliminar accesos directos (escritorio / menú Inicio)"),
            (self.v_carpeta,      "Eliminar carpeta de instalación y archivos"),
        ]
        for var, texto in opciones:
            _checkbox(box, texto, var).pack(anchor="w", padx=10, pady=5)
        self.lbl_estado = tk.Label(self, text="", font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM)
        self.lbl_estado.pack(pady=(4, 4))
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(0, 20))
        ModernButton(bf, text="Cancelar", bg_color=BG3, fg_color=TEXT,
                     font=("Segoe UI", 10), padx=18, pady=6,
                     command=self.destroy).pack(side="left", padx=4)
        ModernButton(bf, text="Desinstalar", bg_color=ACCENT2, fg_color=BG,
                     font=("Segoe UI", 10, "bold"), padx=18, pady=6,
                     command=self._confirmar).pack(side="left", padx=4)

    def _confirmar(self) -> None:
        import tkinter.messagebox as mb
        ok: bool = mb.askyesno(
            "Confirmar desinstalación",
            "¿Seguro que deseas desinstalar Pausas Activas?\n\nLa aplicación se cerrará al terminar.",
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
            self.lbl_estado.config(text="Quitando autoarranque...")
            self.update()
            try:
                set_autoarranque(False, "")
            except Exception as e:
                errores.append(f"Autoarranque: {e}")
        if self.v_datos.get():
            self.lbl_estado.config(text="Eliminando datos...")
            self.update()
            for f in [self._config_file, self._stats_file, self._hist_file]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception as e:
                    errores.append(f"Archivo {os.path.basename(f)}: {e}")
        if self.v_accesos.get():
            self.lbl_estado.config(text="Eliminando accesos directos...")
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
                "Desinstalación con advertencias",
                "Se completó con algunos errores:\n\n" + "\n".join(errores),
                parent=self,
            )
        else:
            mb.showinfo(
                "Desinstalación completa",
                "Pausas Activas ha sido desinstalado correctamente.",
                parent=self,
            )
        self.destroy()
        self.on_quit()
