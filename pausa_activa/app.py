"""Main application class for FlowBreak."""

from __future__ import annotations

import os
import random
import sys
import threading
import customtkinter as ctk
from datetime import datetime
from tkinter import Canvas
from typing import Any, Callable

from pausa_activa.constants import (
    C, APP_NAME, APP_DISPLAY, __version__, UPDATER_REPO,
    EJERCICIOS, set_theme, set_idioma, get_random_phrase,
    darken_color, F, set_font_size,
    _,
    log, center_window,
)
from pausa_activa.config import ConfigManager
from pausa_activa.audio import AudioManager
from pausa_activa.water import WaterReminder
from pausa_activa.notifications import send_win_notification
from pausa_activa.installer import InstallerWindow, _is_installed
from pausa_activa.windows import (
    PausaWindow, StatsWindow, ConfigWindow, WelcomeWindow, UninstallWindow,
    draw_bar_chart, audio_manager,
)

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE: bool = True
except ImportError:
    TRAY_AVAILABLE = False


# Cache for tray icons — generated once per state
_TRAY_ICON_CACHE: dict[str, Image.Image] = {}


def _make_person_icon(base_size: int, fig_color: tuple[int, int, int, int],
                      bg_color: tuple[int, int, int]) -> Image.Image:
    """Draw a simple person figure (stretching pose) on a circular gradient bg."""
    img = Image.new("RGBA", (base_size, base_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = base_size // 2
    r = base_size // 2 - base_size // 40
    s = base_size / 512.0

    d.ellipse([c - r - base_size // 30, c - r - base_size // 30,
               c + r + base_size // 30, c + r + base_size // 30],
              fill=bg_color + (60,))
    for i in range(20):
        t = i / 20.0
        cr = int(r * (1 - t * 0.15))
        ca = tuple(min(255, int(cv * (1 - t * 0.3))) for cv in bg_color)
        d.ellipse([c - cr, c - cr, c + cr, c + cr], fill=ca + (255,))
    d.ellipse([c - r // 3, c - r // 2, c + r // 3, c], fill=(255, 255, 255, 60))

    cx, cy = c, c + int(30 * s)
    hr = int(36 * s)
    d.ellipse([cx - hr, cy - int(168 * s) - hr, cx + hr, cy - int(168 * s) + hr], fill=fig_color)
    bt, bb = cy - int(132 * s), cy - int(24 * s)
    bw = int(20 * s)
    d.polygon([cx - bw, bt, cx + bw, bt, cx + int(10 * s), bb, cx - int(10 * s), bb], fill=fig_color)
    lw = max(2, int(12 * s))
    d.line([(cx - int(18 * s), bt + int(8 * s)), (cx - int(80 * s), cy - int(140 * s)),
            (cx - int(110 * s), cy - int(180 * s))], fill=fig_color, width=lw)
    d.line([(cx + int(18 * s), bt + int(8 * s)), (cx + int(80 * s), cy - int(140 * s)),
            (cx + int(110 * s), cy - int(180 * s))], fill=fig_color, width=lw)
    d.line([(cx - int(10 * s), bb), (cx - int(50 * s), cy + int(60 * s)),
            (cx - int(70 * s), cy + int(130 * s))], fill=fig_color, width=lw)
    d.line([(cx + int(10 * s), bb), (cx + int(50 * s), cy + int(60 * s)),
            (cx + int(70 * s), cy + int(130 * s))], fill=fig_color, width=lw)
    return img


def _get_tray_icon(color: tuple[int, int, int], size: int = 64) -> Image.Image:
    key = f"{color}_{size}"
    if key not in _TRAY_ICON_CACHE:
        img = _make_person_icon(256, (255, 255, 255, 255), color)
        _TRAY_ICON_CACHE[key] = img.resize((size, size), Image.LANCZOS)
    return _TRAY_ICON_CACHE[key]


class Updater:
    """Auto-updater via GitHub Releases."""
    REPO: str = UPDATER_REPO

    @staticmethod
    def _parse_version(tag: str) -> tuple[int, ...]:
        return tuple(int(x) for x in tag.lstrip("vV").replace("-", ".").split("."))

    @staticmethod
    def current_version() -> str:
        return __version__

    @staticmethod
    def check() -> dict[str, Any] | None:
        """Check GitHub for latest release. Returns {'version': tag, 'url': download_url} or None."""
        try:
            import urllib.request
            import json
            url: str = f"https://api.github.com/repos/{Updater.REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data: dict[str, Any] = json.loads(resp.read().decode())
            latest_tag: str = str(data.get("tag_name", ""))
            if not latest_tag:
                return None
            current = Updater._parse_version(Updater.current_version())
            latest = Updater._parse_version(latest_tag)
            if latest <= current:
                return None
            exe_url: str | None = None
            for asset in data.get("assets", []):
                name: str = asset.get("name", "")
                if name.endswith(".exe") and "FlowBreak" in name:
                    exe_url = asset.get("browser_download_url")
                    break
            return {"version": latest_tag, "url": exe_url or ""}
        except Exception as e:
            log.debug("Update check failed: %s", e)
            return None


class App(ctk.CTk):
    def __init__(
        self,
        app_path: str,
        app_dir: str,
        cfg_mgr: ConfigManager | None = None,
        audio_mgr: AudioManager | None = None,
        water_mgr: WaterReminder | None = None,
    ) -> None:
        super().__init__()

        ctk.set_default_color_theme("blue")

        self._app_path: str = app_path
        self._app_dir: str = app_dir
        self._cfg_mgr: ConfigManager = cfg_mgr or ConfigManager(
            *self._paths_from_dir(app_dir)
        )
        self._audio_mgr: AudioManager = audio_mgr or audio_manager
        self._init_paths(app_dir)

        self.cfg: dict[str, Any] = self._cfg_mgr.load_config()
        self.stats: dict[str, Any] = self._cfg_mgr.load_stats()
        self.remaining: int = self.cfg["intervalo_min"] * 60
        self.running: bool = True
        self.pausa_open: bool = False
        self._job: str | None = None
        self._tray: Any = None
        self._last_ej: str = ""
        self._total_sec: int = self.cfg["intervalo_min"] * 60
        self._nm_skip: bool = False
        self._update_available: bool = False
        self._update_info: dict[str, Any] | None = None
        self._pending_restart: bool = False

        set_theme(self.cfg.get("tema", "oscuro"), self.cfg.get("color_acento", "azul"), self.cfg.get("fondo", "estandar"))
        set_idioma(self.cfg.get("idioma", "es"))
        set_font_size(self.cfg.get("tamano_letra", "normal"))

        self.title(APP_DISPLAY)
        self.configure(fg_color=C.BG)
        self.resizable(False, False)
        try:
            self.iconbitmap(os.path.join(app_dir, "FlowBreak.ico"))
        except Exception:
            pass

        self._water: WaterReminder = water_mgr or WaterReminder(lambda: self.cfg)

        log.info(
            "App iniciada. running=%s, instalada=%s, primera_vez=%s",
            self.running, _is_installed(), self.cfg.get("primera_vez", True),
        )

        threading.Thread(target=self._check_update, daemon=True).start()

        if not _is_installed():
            self.withdraw()
            InstallerWindow(self, self._after_install, app_path, self._programs_dir)
        elif self.cfg.get("primera_vez", True):
            self.withdraw()
            WelcomeWindow(
                self, self.cfg, self._after_welcome, app_path,
                config_saver=self._cfg_mgr.save_config,
            )
        else:
            self._start_main()

    def _paths_from_dir(self, app_dir: str) -> tuple[str, str, str]:
        return (
            os.path.join(app_dir, "config.json"),
            os.path.join(app_dir, "stats.json"),
            os.path.join(app_dir, "historial.csv"),
        )

    def _init_paths(self, app_dir: str) -> None:
        self._config_file, self._stats_file, self._hist_file = self._paths_from_dir(app_dir)
        self._ejercicios_file: str = os.path.join(app_dir, "ejercicios.json")
        self._programs_dir: str = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
            APP_NAME,
        )
        self._load_ejercicios()

    def _load_ejercicios(self) -> None:
        from pausa_activa.constants import load_ejercicios_from_file
        ejercicios = load_ejercicios_from_file(self._ejercicios_file)
        EJERCICIOS.clear()
        EJERCICIOS.extend(ejercicios)

    def _check_update(self) -> None:
        try:
            info: dict[str, Any] | None = Updater.check()
            if info:
                self._update_info = info
                self._update_available = True
                ver: str = info["version"]
                log.info("Actualizacion disponible: %s (actual: %s)", ver, __version__)
                self.after(3000, lambda: self._show_update_notification(ver))
            else:
                log.debug("No hay actualizaciones disponibles")
        except Exception as e:
            log.debug("Error checking updates: %s", e)

    def _show_update_notification(self, version: str) -> None:
        if not self._update_available:
            return
        msg: str = _("update_notif_msg").format(version=version)
        send_win_notification(
            APP_DISPLAY,
            msg,
            sound="reminder",
            duration="long",
        )
        if self.lbl_update:
            self.lbl_update.configure(text=f"{_('update_badge')} {version}", text_color=C.YELLOW)
            self.lbl_update.pack(pady=(0, 2))

    def _update_paths(self, app_dir: str) -> None:
        self._app_dir = app_dir
        self._init_paths(app_dir)
        self._cfg_mgr = ConfigManager(*self._paths_from_dir(app_dir))

    def _after_install(self, install_dir: str) -> None:
        self._update_paths(install_dir)
        self.cfg = self._cfg_mgr.load_config()
        self.stats = self._cfg_mgr.load_stats()
        self.remaining = self.cfg["intervalo_min"] * 60
        self._total_sec = self.remaining
        self.withdraw()
        WelcomeWindow(
            self, self.cfg, self._after_welcome, self._app_path,
            config_saver=self._cfg_mgr.save_config,
        )

    def _after_welcome(self, cfg_updated: dict[str, Any]) -> None:
        self.cfg = cfg_updated
        self.remaining = self.cfg["intervalo_min"] * 60
        self._total_sec = self.remaining
        self._start_main()

    def _start_main(self) -> None:
        set_font_size(self.cfg.get("tamano_letra", "normal"))
        self._build()
        self._fade_in()
        self._center()
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._hide)

        if self.cfg.get("agua_activo", True):
            self._water.start()

        if TRAY_AVAILABLE:
            threading.Thread(target=self._start_tray, daemon=True).start()

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _start_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem(_("abrir"),          self._show_cb, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(_("pausa_ya_tray"),   lambda i, it: self.after(0, self._now)),
            pystray.MenuItem(_("posponer_tray"),   lambda i, it: self.after(0, self._posponer)),
            pystray.MenuItem(_("pausar_tray"),     lambda i, it: self.after(0, self._toggle)),
            pystray.MenuItem(_("estadisticas"),    lambda i, it: self.after(0, self._open_stats)),
            pystray.MenuItem(_("configuracion"),   lambda i, it: self.after(0, self._open_config)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(_("buscar_actualizaciones"), lambda i, it: self.after(0, self._manual_update_check)),
            pystray.MenuItem(_("desinstalar"),     lambda i, it: self.after(0, self._open_uninstall)),
            pystray.MenuItem(_("salir"), self._quit),
        )
        self._tray = pystray.Icon(
            APP_NAME,
            _get_tray_icon(C.TRAY_ACTIVE),
            APP_DISPLAY,
            menu,
        )
        self._tray.run()

    def _update_tray(self) -> None:
        if not TRAY_AVAILABLE or not self._tray:
            return
        if not self.running:
            c = C.TRAY_PAUSED
            tip = _("pausado")
        elif not self._in_active_hours(self.cfg):
            c = C.TRAY_OFF
            tip = _("fuera_horario")
        else:
            c = C.TRAY_ACTIVE
            tip = _("prox_pausa").format(t=self._fmt_time(self.remaining))
        self._tray.icon = _get_tray_icon(c)
        self._tray.title = f"{APP_DISPLAY} - {tip}"

    def _show_cb(self, i=None, it=None) -> None:
        self.after(0, self._show)

    def _show(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _hide(self) -> None:
        self.withdraw()

    def _quit(self, i=None, it=None) -> None:
        self.running = False
        self._water.stop()
        audio_manager.stop_ambient()
        if self._tray:
            self._tray.stop()
        self.after(0, self.destroy)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.minsize(380, 520)
        # Minimal title bar
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=24, pady=(16, 0))

        dot = ctk.CTkLabel(title_frame, text="●", font=F(9), text_color=C.GREEN)
        dot.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            title_frame, text=APP_DISPLAY,
            font=F(13, "bold"), text_color=C.TEXT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame, text="· " + _("pausa_activa"),
            font=F(9), text_color=C.TEXT_DIM,
        ).pack(side="left", padx=(4, 0))

        btn_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="⚙", width=28, height=28,
            fg_color="transparent", text_color=C.TEXT_DIM, hover_color=C.BG3,
            font=F(12), corner_radius=14,
            command=self._open_config,
        ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            btn_frame, text="📊", width=28, height=28,
            fg_color="transparent", text_color=C.TEXT_DIM, hover_color=C.BG3,
            font=F(12), corner_radius=14,
            command=self._open_stats,
        ).pack(side="left")

        # Status text — single line
        self.lbl_st = ctk.CTkLabel(
            self, text=_("trabajando"), font=F(10),
            text_color=C.TEXT_DIM, fg_color="transparent",
        )
        self.lbl_st.pack(pady=(10, 0))

        self.badge_frame = ctk.CTkFrame(self, fg_color=C.GREEN, corner_radius=14)
        self.badge_frame.pack(pady=(4, 0))
        self.lbl_badge = ctk.CTkLabel(
            self.badge_frame, text=_("badge_activo"), font=F(8, "bold"),
            text_color=C.BG,
        )
        self.lbl_badge.pack(padx=18, pady=3)

        # Circular timer
        self._canvas = Canvas(
            self, width=180, height=180,
            bg=C.BG, highlightthickness=0,
        )
        self._canvas.pack(pady=(12, 0))

        self._canvas.create_arc(
            14, 14, 166, 166, start=90, extent=360,
            outline=C.BG3, width=9, style="arc", tags="bg_arc",
        )
        self._canvas.create_arc(
            14, 14, 166, 166, start=90, extent=360,
            outline=C.ACCENT, width=9, style="arc", tags="fg_arc",
        )
        self._canvas.create_text(
            90, 88, text="00:00",
            font=F(30, "bold"),
            fill=C.ACCENT, tags="cd_text",
        )

        # Progress bar
        self._progress = ctk.CTkProgressBar(
            self, width=240, height=4,
            corner_radius=2, fg_color=C.BG3,
            progress_color=C.ACCENT,
        )
        self._progress.pack(pady=(8, 0))
        self._progress.set(1.0)

        # Update notification
        self.lbl_update = ctk.CTkLabel(
            self, text="", font=F(9, "bold"),
            text_color=C.YELLOW, fg_color="transparent",
            cursor="hand2",
        )
        self.lbl_update.bind("<Button-1>", lambda e: self._show_update_dialog())

        # Stats
        self.lbl_stats = ctk.CTkLabel(
            self, text="", font=F(10),
            text_color=C.TEXT_DIM, fg_color="transparent",
        )
        self.lbl_stats.pack(pady=(10, 0))

        self.lbl_meta = ctk.CTkLabel(
            self, text="", font=F(9, "bold"),
            text_color=C.TEXT_DIM, fg_color="transparent",
        )
        self.lbl_meta.pack()

        # Weekly mini chart
        chart_card = ctk.CTkFrame(self, fg_color=C.BG2, corner_radius=12)
        chart_card.pack(fill="x", padx=24, pady=(6, 0))
        self._week_canvas = Canvas(
            chart_card, width=280, height=80,
            bg=C.BG2, highlightthickness=0,
        )
        self._week_canvas.pack(padx=8, pady=(4, 8))

        # Infobar: agua + cfg
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(pady=(4, 0))
        self.lbl_agua = ctk.CTkLabel(
            bar, text="", font=F(8),
            text_color=C.AGUA, fg_color="transparent",
        )
        self.lbl_agua.pack(side="left", padx=4)
        self.lbl_cfg = ctk.CTkLabel(
            bar, text="", font=F(8),
            text_color=C.TEXT_DIM, fg_color="transparent",
        )
        self.lbl_cfg.pack(side="left", padx=4)

        self._update_cfg_label()
        self._update_stats_label()
        self._update_agua_label()

        # Button row — pill buttons
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=(8, 4))

        self.btn_p = ctk.CTkButton(
            bf, text=_("btn_pausar"), font=F(10),
            fg_color=C.BG3, text_color=C.TEXT, hover_color=C.BG4,
            width=90, height=32, corner_radius=16, border_width=0,
            command=self._toggle,
        )
        self.btn_p.pack(side="left", padx=3)

        ctk.CTkButton(
            bf, text="▶ " + _("pausa_ya"), font=F(10),
            fg_color=C.ACCENT, text_color=C.BG, hover_color=darken_color(C.ACCENT),
            width=90, height=32, corner_radius=16, border_width=0,
            command=self._now,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            bf, text="⏰ " + _("posponer"), font=F(10),
            fg_color=C.BG3, text_color=C.TEXT, hover_color=C.BG4,
            width=90, height=32, corner_radius=16, border_width=0,
            command=self._posponer,
        ).pack(side="left", padx=3)

        # Minimize
        ctk.CTkButton(
            self, text=_("minimizar"), font=F(8),
            fg_color="transparent", text_color=C.TEXT_DIM,
            hover_color=C.BG3, corner_radius=8, width=60, height=22,
            cursor="hand2",
            command=self._hide,
        ).pack(pady=(2, 8))

    def _update_cfg_label(self) -> None:
        c = self.cfg
        modo = c.get("modo", "normal").upper()
        self.lbl_cfg.configure(
            text=f"[{modo}] Cada {c['intervalo_min']} min  -  "
                 f"Pausa {c['duracion_pausa_min']} min  -  "
                 f"{c['hora_inicio']} a {c['hora_fin']}",
        )

    def _update_agua_label(self) -> None:
        if self.cfg.get("agua_activo", True):
            self.lbl_agua.configure(
                text=_("agua_recordatorio_every").format(min=self.cfg.get('agua_min', 30)),
            )
        else:
            self.lbl_agua.configure(text="")

    def _update_stats_label(self) -> None:
        s = self.stats
        meta: int = self.cfg["meta_pausas"]
        comp: int = s["completadas"]
        comp_color: str = C.GREEN if comp >= meta else (C.YELLOW if comp >= meta // 2 else C.TEXT_DIM)
        self.lbl_stats.configure(
            text=f"✅ {_('stats_completadas')}: {comp}   ⏭ {_('stats_saltadas')}: {s['saltadas']}",
            text_color=comp_color,
        )
        barra: str = "█" * comp + "░" * (max(0, meta - comp))
        top: str = f"🎯 {_('stats_cumplida')}" if comp >= meta else f"{comp}/{meta}"
        self.lbl_meta.configure(text=f"{_('stats_meta_diaria')}: {barra}  {top}", text_color=comp_color)
        self._draw_week_chart()

    def _draw_week_chart(self) -> None:
        canvas = getattr(self, "_week_canvas", None)
        if not canvas:
            return
        from datetime import datetime, timedelta
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        counts: dict[str, int] = {}
        for entry in self.stats.get("historial", []):
            if entry["estado"] != "completada":
                continue
            day = entry.get("fecha", "")
            if not day:
                day = today.strftime("%Y-%m-%d")
            try:
                dt = datetime.strptime(day, "%Y-%m-%d")
                if today - timedelta(6) <= dt <= today:
                    counts[day] = counts.get(day, 0) + 1
            except ValueError:
                pass
        draw_bar_chart(
            canvas, 280, 80, counts,
            self.cfg.get("meta_pausas", 4),
        )

    def _fade_in(self) -> None:
        try:
            self.attributes("-alpha", 0.0)
            self.deiconify()
            for i in range(1, 11):
                self.after(i * 15, lambda v=i / 10: self.attributes("-alpha", v))
        except Exception:
            self.deiconify()

    def _center(self) -> None:
        center_window(self)

    @staticmethod
    def _fmt_time(s: int) -> str:
        m, s = divmod(max(0, int(s)), 60)
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _in_active_hours(cfg: dict[str, Any]) -> bool:
        from datetime import time as dtime
        try:
            now = datetime.now().time()
            h0, m0 = map(int, cfg["hora_inicio"].split(":"))
            h1, m1 = map(int, cfg["hora_fin"].split(":"))
            start = dtime(h0, m0)
            end = dtime(h1, m1)
            if start <= end:
                return start <= now <= end
            return now >= start or now <= end
        except Exception:
            return True

    def _countdown_color(self) -> str:
        if self._total_sec == 0:
            return C.ACCENT
        pct: float = self.remaining / self._total_sec
        if pct > 0.5:
            return C.ACCENT
        if pct > 0.2:
            return C.YELLOW
        return C.ACCENT2

    def _get_interval(self) -> int:
        modo: str = self.cfg.get("modo", "normal")
        if modo == "pomodoro":
            return 25
        return self.cfg["intervalo_min"]

    def _get_duration(self) -> int:
        modo: str = self.cfg.get("modo", "normal")
        if modo == "pomodoro":
            return 5
        return self.cfg["duracion_pausa_min"]

    # ── Tick principal ────────────────────────────────────────────────────────

    def _tick(self) -> None:
        try:
            if not self.running or self.pausa_open:
                self._job = self.after(1000, self._tick)
                return

            if self.cfg.get("fin_de_semana", False) and self._is_weekend():
                self.lbl_st.configure(text=_("fin_semana"))
                self._canvas.itemconfig("cd_text", text="--:--", fill=C.TEXT_DIM)
                self.badge_frame.configure(fg_color=C.YELLOW)
                self.lbl_badge.configure(text=_("badge_fin_semana"), text_color=C.BG)
                self._job = self.after(1000, self._tick)
                return

            if not self._in_active_hours(self.cfg):
                self.lbl_st.configure(text=_("fuera_horario"))
                self._canvas.itemconfig("cd_text", text="--:--", fill=C.TEXT_DIM)
                self.badge_frame.configure(fg_color=C.ACCENT2)
                self.lbl_badge.configure(text=_("badge_fuera_horario"), text_color=C.BG)
                self._update_tray()
                self._job = self.after(1000, self._tick)
                return

            color: str = self._countdown_color()
            total: int = self._total_sec if self._total_sec else 1
            pct: float = self.remaining / total

            self._canvas.itemconfig("cd_text", text=self._fmt_time(self.remaining), fill=color)
            self._canvas.itemconfig("fg_arc", extent=360 * pct, outline=color)
            self.lbl_st.configure(text=_("trabajando"))
            self.badge_frame.configure(fg_color=C.GREEN)
            self.lbl_badge.configure(text=_("trabajando").upper(), text_color=C.BG)
            self._progress.set(pct)

            if self.remaining % 30 == 0:
                self._update_tray()

            if self.remaining <= 0:
                if self.cfg.get("no_molestar", True) and self._is_fullscreen():
                    self.lbl_st.configure(text=_("pospuesto_fullscreen"))
                    self.badge_frame.configure(fg_color=C.YELLOW)
                    self.lbl_badge.configure(text=_("no_molestar").upper(), text_color=C.BG)
                    self._total_sec = 5 * 60
                    self.remaining = self._total_sec
                else:
                    self._trigger_pausa()
            else:
                self.remaining -= 1

            self._job = self.after(1000, self._tick)
        except Exception as ex:
            import logging
            logging.getLogger(__name__).exception("Error en _tick: %s", ex)
            self._job = self.after(1000, self._tick)

    @staticmethod
    def _is_weekend() -> bool:
        return datetime.now().weekday() >= 5

    @staticmethod
    def _is_fullscreen() -> bool:
        import ctypes
        try:
            state = ctypes.c_int(0)
            ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(state))
            if state.value in (5, 4):
                return True
        except Exception:
            pass
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            fw = rect.right - rect.left
            fh = rect.bottom - rect.top
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            if fw >= sw * 0.95 and fh >= sh * 0.95:
                return True
        except Exception:
            pass
        return False

    def _trigger_pausa(self) -> None:
        try:
            if self.pausa_open:
                return
            self.pausa_open = True
            log.info("Pausa activada, ejercicio=%s", self._last_ej or "aleatorio")
            self._show()
            sonido = self.cfg.get("sonido", True)
            if sonido:
                threading.Thread(target=audio_manager.play_alert, daemon=True).start()
            self.after(0, lambda: send_win_notification(
                APP_DISPLAY,
                _("break_time_body"),
                sound="None" if sonido else self.cfg.get("notificacion_sonido", "default"),
                duration=self.cfg.get("notificacion_duracion", "short"),
            ))
            activos = [
                e for e in EJERCICIOS
                if e["id"] in self.cfg.get("ejercicios_activos", [e["id"] for e in EJERCICIOS])
            ]
            if not activos:
                activos = list(EJERCICIOS)
            ej = random.choice(activos)
            self._last_ej = ej["nombre"]
            dur: int = self._get_duration() * 60
            PausaWindow(
                self, ej, dur, self._done_pausa, self._skip_pausa,
                sonido_ambiente=self.cfg.get("sonido_ambiente", "ninguno"),
            )
        except Exception as ex:
            log.exception("Error en _trigger_pausa: %s", ex)
            self.pausa_open = False

    def _done_pausa(self) -> None:
        self.pausa_open = False
        interval: int = self._get_interval()
        self._total_sec = interval * 60
        self.remaining = self._total_sec
        self.stats["completadas"] += 1
        now = datetime.now()
        self.stats["historial"].append({
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M"),
            "ejercicio": self._last_ej,
            "estado": "completada",
        })
        meta: int = self.cfg["meta_pausas"]
        if self.stats["completadas"] == meta:
            self.stats["meta_cumplida"] = True
            self.after(0, lambda: send_win_notification(
                _("meta_cumplida"),
                _("meta_completada_msg").format(meta=meta),
            ))
        self._cfg_mgr.save_stats(self.stats)
        self._update_stats_label()
        self._cfg_mgr.append_csv([
            now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            self._last_ej, "completada",
        ])
        self.lbl_st.configure(text=get_random_phrase())
        self._update_tray()

    def _skip_pausa(self) -> None:
        self.pausa_open = False
        interval: int = self._get_interval()
        self._total_sec = interval * 60
        self.remaining = self._total_sec
        now = datetime.now()
        self.stats["saltadas"] += 1
        self.stats["historial"].append({
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M"),
            "ejercicio": self._last_ej,
            "estado": "saltada",
        })
        self._cfg_mgr.save_stats(self.stats)
        self._update_stats_label()
        self._cfg_mgr.append_csv([
            now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            self._last_ej, "saltada",
        ])
        self.lbl_st.configure(text=_("pausa_saltada"))
        self._update_tray()

    def _toggle(self) -> None:
        self.running = not self.running
        if self.running:
            self.btn_p.configure(text=_("btn_pausar"), text_color=C.TEXT)
            self.lbl_st.configure(text=_("trabajando"))
            self.badge_frame.configure(fg_color=C.GREEN)
            self.lbl_badge.configure(text=_("badge_activo"), text_color=C.BG)
        else:
            self.btn_p.configure(text=_("btn_reanudar"), text_color=C.GREEN)
            self.lbl_st.configure(text=_("pausado"))
            self.badge_frame.configure(fg_color=C.TEXT_DIM)
            self.lbl_badge.configure(text=_("badge_pausado"), text_color=C.BG)
        self._update_tray()

    def _now(self) -> None:
        self.remaining = 0

    def _posponer(self) -> None:
        mins: int = self.cfg.get("posponer_min", 10)
        self._total_sec = mins * 60
        self.remaining = self._total_sec
        self.lbl_st.configure(text=_("pausa_pospuesta").format(mins=mins))

    def _manual_update_check(self) -> None:
        self.lbl_st.configure(text=_("buscando_updates"))
        info: dict[str, Any] | None = Updater.check()
        if info:
            self._update_info = info
            self._update_available = True
            self._show_update_dialog()
        else:
            self.lbl_st.configure(text=_("version_actual"))

    def _show_update_dialog(self) -> None:
        if not self._update_info:
            return
        ver: str = self._update_info["version"]
        url: str = self._update_info.get("url", "")
        import tkinter.messagebox as mb
        ok: bool = mb.askyesno(
            _("update_disponible"),
            _("update_msg").format(ver=ver, cur=__version__),
            parent=self,
        )
        if ok:
            if url:
                self._download_and_install(url)
            else:
                mb.showwarning(
                    _("no_disponible"),
                    _("update_no_url"),
                    parent=self,
                )

    def _download_and_install(self, url: str) -> None:
        import tempfile
        self.lbl_st.configure(text=_("descargando_update"))
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        threading.Thread(target=self._do_download, args=(url,), daemon=True).start()

    def _do_download(self, url: str) -> None:
        import urllib.request
        import tempfile
        tmp_exe: str = ""
        try:
            tmp_dir: str = tempfile.gettempdir()
            tmp_exe = os.path.join(tmp_dir, "FlowBreak_Update.exe")
            urllib.request.urlretrieve(url, tmp_exe)
            self.after(0, lambda: self._finish_download(tmp_exe))
        except Exception as e:
            self.after(0, lambda e=e: self._download_error(e))

    def _finish_download(self, tmp_exe: str) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._install_update(tmp_exe)
        try:
            os.remove(tmp_exe)
        except Exception:
            pass

    def _download_error(self, exc: Exception) -> None:
        import tkinter.messagebox as mb
        self._progress.stop()
        self._progress.configure(mode="determinate")
        mb.showerror(_("error"), f"{_('err_download')}\n{exc}", parent=self)
        self.lbl_st.configure(text=_("err_update"))

    def _install_update(self, new_exe: str) -> None:
        current_exe: str = self._app_path
        if not getattr(sys, "frozen", False):
            import tkinter.messagebox as mb
            mb.showinfo(
                _("update_lista"),
                _("update_dev_msg"),
                parent=self,
            )
            return
        import tempfile
        bat: str = os.path.join(tempfile.gettempdir(), "flowbreak_update.bat")
        pid: int = os.getpid()
        with open(bat, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("chcp 65001 >nul\n")
            f.write("echo Actualizando FlowBreak...\n")
            f.write(":loop\n")
            f.write(f'tasklist /fi "PID eq {pid}" | find "{pid}" >nul 2>&1\n')
            f.write("if not errorlevel 1 (\n")
            f.write("  timeout /t 1 /nobreak >nul\n")
            f.write("  goto loop\n")
            f.write(")\n")
            f.write(f'copy /y "{new_exe}" "{current_exe}" >nul 2>&1\n')
            f.write(f'start "" "{current_exe}"\n')
            f.write(f'del "%~f0"\n')
        import subprocess
        subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)
        self._water.stop()
        audio_manager.stop_ambient()
        if self._tray:
            self._tray.stop()
        self.destroy()
        sys.exit(0)

    def _reapply_theme(self) -> None:
        """Rebuild UI after theme change so all widgets pick up new colors."""
        for w in list(self.winfo_children()):
            w.destroy()
        self._build()
        self.configure(fg_color=C.BG)
        if self._update_available:
            self.lbl_update.configure(text=f"⬇ {self._update_info['version']}", text_color=C.YELLOW)
            self.lbl_update.pack(pady=(0, 2))
        self._update_stats_label()
        self._update_cfg_label()
        self._update_agua_label()
        self._update_tray()
        self._water.restart()

    def _open_config(self) -> None:
        def on_save(c: dict[str, Any]) -> None:
            old_tema = self.cfg.get("tema")
            old_font = self.cfg.get("tamano_letra")
            self.cfg = c
            self._total_sec = c["intervalo_min"] * 60
            self.remaining = self._total_sec
            self._cfg_mgr.save_config(c)
            if c.get("tema") != old_tema or c.get("tamano_letra") != old_font or c.get("color_acento") != self.cfg.get("color_acento"):
                if c.get("tamano_letra") != old_font:
                    set_font_size(c.get("tamano_letra", "normal"))
                self._reapply_theme()
            else:
                self._update_cfg_label()
                self._update_agua_label()
            self._water.restart()
        profiles: list[str] = self._cfg_mgr.list_profiles()
        ConfigWindow(self, self.cfg, on_save, self._app_path, profiles=profiles)

    def _open_stats(self) -> None:
        history = self._cfg_mgr.get_stats_history()
        StatsWindow(
            self, self.stats, self.cfg["meta_pausas"],
            self._hist_file, history=history,
        )

    def _open_uninstall(self) -> None:
        UninstallWindow(
            self, self._quit,
            self._config_file, self._stats_file, self._hist_file, self._app_dir,
        )
