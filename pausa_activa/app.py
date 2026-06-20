"""Main application class for FlowBreak."""

from __future__ import annotations

import math
import os
import random
import sys
import threading
from datetime import date, datetime
from tkinter import Canvas
from typing import Any

import customtkinter as ctk

from pausa_activa.audio import AudioManager
from pausa_activa.config import ConfigManager
from pausa_activa.constants import (
    APP_DISPLAY,
    APP_NAME,
    EJERCICIOS,
    UPDATER_REPO,
    WELLNESS_NOTES,
    C,
    F,
    _,
    __version__,
    darken_color,
    get_random_phrase,
    log,
    set_font_size,
    set_idioma,
    set_theme,
)
from pausa_activa.hotkeys import create_default_manager
from pausa_activa.installer import InstallerWindow, _get_install_dir_from_registry, _is_installed
from pausa_activa.notifications import send_win_notification
from pausa_activa.water import WaterReminder
from pausa_activa.windows import (
    AchievementsWindow,
    AIEngine,
    AIInsightsWindow,
    BreakWindow,
    CompactWindow,
    ConfigWindow,
    CustomExerciseWindow,
    FloatingTimer,
    FlowBuddyWindow,
    PostureReminder,
    StatsWindowEnhanced,
    TutorialWindow,
    UninstallWindow,
    WelcomeWindow,
    WorkoutWindow,
    check_achievements,
    draw_bar_chart,
    get_audio_manager,
    toast,
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
        try:
            return tuple(int(x) for x in tag.lstrip("vV").replace("-", ".").split("."))
        except (ValueError, TypeError):
            return (0,)

    @staticmethod
    def current_version() -> str:
        return __version__

    @staticmethod
    def check() -> dict[str, Any] | None:
        """Check GitHub for latest release. Returns {'version': tag, 'url': download_url} or None."""
        try:
            import json
            import urllib.request
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
            if not exe_url:
                return None
            return {"version": latest_tag, "url": exe_url}
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
        # audio_mgr param accepted for API compat; module-level audio_manager used directly
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

        def _on_water_notify() -> None:
            today = datetime.now().strftime("%Y-%m-%d")
            if self.stats.get("agua_respondidas_fecha") != today:
                self.stats["agua_respondidas_hoy"] = 0
                self.stats["agua_respondidas_fecha"] = today
            self.stats["agua_respondidas_hoy"] = self.stats.get("agua_respondidas_hoy", 0) + 1
        self._water: WaterReminder = water_mgr or WaterReminder(lambda: self.cfg, on_notify=_on_water_notify)

        log.info(
            "App iniciada. running=%s, instalada=%s, primera_vez=%s",
            self.running, _is_installed(), self.cfg.get("primera_vez", True),
        )

        threading.Thread(target=self._check_update, daemon=True).start()

        # If installed but running from wrong folder → relocate
        if _is_installed():
            reg_dir = _get_install_dir_from_registry()
            if reg_dir and os.path.normpath(app_dir) != os.path.normpath(reg_dir):
                dest = os.path.join(reg_dir, os.path.basename(app_path))
                if getattr(sys, "frozen", False) and dest != app_path:
                    import shutil
                    import subprocess
                    try:
                        shutil.copy2(app_path, dest)
                        subprocess.Popen([dest])
                        sys.exit(0)
                    except PermissionError:
                        log.warning("No se pudo copiar a %s (archivo en uso), continuando desde %s", dest, app_path)

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
        self._programs_dir: str = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
            APP_NAME,
        )

    def _check_update(self) -> None:
        try:
            info: dict[str, Any] | None = Updater.check()
            if info:
                self._update_info = info
                self._update_available = True
                ver: str = info["version"]
                log.info("Actualizacion disponible: %s (actual: %s)", ver, __version__)
                try:
                    self.after(3000, lambda: self._show_update_notification(ver))
                except Exception:
                    pass
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
        lbl = getattr(self, "lbl_update", None)
        if lbl:
            lbl.configure(text=f"{_('update_badge')} {version}", text_color=C.YELLOW)
            lbl.pack(pady=(0, 2))

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

        # Inicializar FlowBuddy ANTES de _build
        self._pet_state = self.cfg.get("pet_state", {
            "nombre": "FlowBuddy",
            "energia": 100,
            "felicidad": 100,
            "salud": 100,
            "nivel": 1,
            "xp": 0,
            "xp_siguiente": 100,
            "ultimo_alimento": 0,
        })

        # Inicializar AI Engine
        self._ai_engine = AIEngine(self.stats, self.cfg)

        self._build()
        self._fade_in()
        self._center()
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._hide)

        if self.cfg.get("agua_activo", True):
            self._water.start()

        # Posture reminder
        self._posture = PostureReminder(self)
        if self.cfg.get("postura_recordatorio", False):
            self._posture.start(self.cfg.get("postura_intervalo_min", 20))

        # Floating timer
        self._floating: FloatingTimer | None = None
        if self.cfg.get("floating_enabled", False):
            self._create_floating_timer()

        # Compact mode
        self._compact: CompactWindow | None = None
        if self.cfg.get("compacto_enabled", False):
            self._create_compact_window()

        # Tutorial
        if self.cfg.get("primera_vez", True) and not self.cfg.get("tutorial_completado", False):
            self.after(1000, self._open_tutorial)

        # Check achievements on startup
        self.after(2000, self._check_achievements)

        # Eye reminder (20-20-20)
        self._schedule_eye_reminder()

        # Weekly snapshot
        self._save_weekly_snapshot()

        # FlowBuddy decay
        self._pet_decay_job: str | None = None
        self._start_pet_decay()

        if TRAY_AVAILABLE:
            threading.Thread(target=self._start_tray, daemon=True).start()

        self._hotkeys = create_default_manager(
            on_break_now=self._hotkey_break_now,
            on_snooze=self._hotkey_snooze,
            on_pause_resume=self._hotkey_pause_resume,
            on_show_hide=self._hotkey_show_hide,
            on_quit=self._hotkey_quit,
        )
        self._hotkeys.start()

    def _create_floating_timer(self) -> None:
        try:
            if self._floating and self._floating.winfo_exists():
                self._floating.destroy()
            self._floating = FloatingTimer(
                self, lambda: self.remaining,
                lambda: not self.running,
                self._show,
            )
        except Exception as e:
            log.warning("Could not create floating timer: %s", e)

    def _create_compact_window(self) -> None:
        try:
            if self._compact and self._compact.winfo_exists():
                self._compact.destroy()
            self._compact = CompactWindow(
                self, lambda: self.remaining,
                lambda: not self.running,
                self._toggle,
                self._next_step,
                self._skip,
            )
        except Exception as e:
            log.warning("Could not create compact window: %s", e)

    def _open_tutorial(self) -> None:
        TutorialWindow(self, lambda: self.cfg.update({"tutorial_completado": True})).center()

    def _check_achievements(self) -> None:
        shown = self.cfg.get("logros_mostrados", [])
        new_achs = check_achievements(self.stats, self.stats, shown)
        if new_achs:
            self.cfg["logros_mostrados"] = shown
            self._cfg_mgr.save_config(self.cfg)
            for ach in new_achs:
                toast(_("logro_desbloqueado"), f"{ach['icon']} {_(ach['key'])}", kind="exito", duration=4000)

    def _next_step(self) -> None:
        pass

    def _skip(self) -> None:
        pass

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
        self._posture.stop()
        get_audio_manager().cleanup()
        # Save pet state
        self.cfg["pet_state"] = self._pet_state
        self._cfg_mgr.save_config(self.cfg)
        if self._floating and self._floating.winfo_exists():
            self._floating.destroy()
        if self._compact and self._compact.winfo_exists():
            self._compact.destroy()
        if self._tray:
            self._tray.stop()
        if hasattr(self, "_hotkeys"):
            self._hotkeys.stop()
        if self._pet_decay_job:
            try:
                self.after_cancel(self._pet_decay_job)
            except Exception:
                pass
        self.after(0, self.destroy)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.minsize(400, 720)
        self.configure(fg_color=C.BG)

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(20, 0))

        left_h = ctk.CTkFrame(header, fg_color="transparent")
        left_h.pack(side="left")

        dot = ctk.CTkLabel(left_h, text="●", font=F(10), text_color=C.GREEN)
        dot.pack(side="left", padx=(0, 8))

        name_frame = ctk.CTkFrame(left_h, fg_color="transparent")
        name_frame.pack(side="left")
        ctk.CTkLabel(
            name_frame, text=APP_DISPLAY,
            font=F(16, "bold"), text_color=C.TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_frame, text=_("pausa_activa"),
            font=F(9), text_color=C.TEXT_MUTED,
        ).pack(anchor="w")

        right_h = ctk.CTkFrame(header, fg_color="transparent")
        right_h.pack(side="right")

        ctk.CTkButton(
            right_h, text="⚙", width=32, height=32,
            fg_color=C.BG3, text_color=C.TEXT_DIM, hover_color=C.BG4,
            font=F(14), corner_radius=10,
            command=self._open_config,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            right_h, text="📊", width=32, height=32,
            fg_color=C.BG3, text_color=C.TEXT_DIM, hover_color=C.BG4,
            font=F(14), corner_radius=10,
            command=self._open_stats,
        ).pack(side="left")

        # ── Wellness Card ──────────────────────────────────────────────
        wellness_card = ctk.CTkFrame(self, fg_color=C.CARD, corner_radius=16,
                                      border_width=1, border_color=C.CARD_BORDER)
        wellness_card.pack(fill="x", padx=24, pady=(12, 0))

        wellness_title = ctk.CTkLabel(
            wellness_card, text="💭 Notas de bienestar",
            font=F(11, "bold"), text_color=C.TEXT, anchor="w",
        )
        wellness_title.pack(pady=(12, 4), padx=16)

        self._wellness_label = ctk.CTkLabel(
            wellness_card, text="", font=F(9), text_color=C.TEXT_DIM, anchor="w",
            wraplength=280, justify="left",
        )
        self._wellness_label.pack(pady=(0, 12), padx=16)

        self._update_wellness_note()

        # ── Status Badge ───────────────────────────────────────────────
        self.badge_frame = ctk.CTkFrame(self, fg_color=C.GREEN, corner_radius=20)
        self.badge_frame.pack(pady=(16, 0))
        self.lbl_badge = ctk.CTkLabel(
            self.badge_frame, text=_("badge_activo"), font=F(9, "bold"),
            text_color="#FFFFFF",
        )
        self.lbl_badge.pack(padx=20, pady=4)

        # ── Status text ────────────────────────────────────────────────
        self.lbl_st = ctk.CTkLabel(
            self, text=_("trabajando"), font=F(11),
            text_color=C.TEXT_DIM, fg_color="transparent",
        )
        self.lbl_st.pack(pady=(8, 0))

        # ── Circular Timer (grande, moderno) ───────────────────────────
        timer_container = ctk.CTkFrame(self, fg_color="transparent")
        timer_container.pack(pady=(8, 0))

        self._canvas = Canvas(
            timer_container, width=220, height=220,
            bg=C.BG, highlightthickness=0,
        )
        self._canvas.pack()

        cx, cy, r = 110, 110, 95
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=C.BG3, width=8, tags="bg_oval",
        )
        self._canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=90, extent=360,
            outline=C.ACCENT, width=8, style="arc", tags="fg_arc",
        )
        self._canvas.create_text(
            cx, cy - 8, text="00:00",
            font=F(38, "bold"), fill=C.TEXT, tags="cd_text",
        )
        self._canvas.create_text(
            cx, cy + 28, text=_("tiempo_restante"),
            font=F(9), fill=C.TEXT_MUTED, tags="cd_sub",
        )

        # Partículas y efectos
        self._particles: list[dict] = []
        self._confetti: list[dict] = []
        self._anim_frame = 0
        self._start_particle_animation()

        # ── Progress Bar ───────────────────────────────────────────────
        self._progress = ctk.CTkProgressBar(
            self, width=260, height=6,
            corner_radius=3, fg_color=C.BG3,
            progress_color=C.ACCENT,
        )
        self._progress.pack(pady=(10, 0))
        self._progress.set(1.0)

        # ── Update notification ────────────────────────────────────────
        self.lbl_update = ctk.CTkLabel(
            self, text="", font=F(9, "bold"),
            text_color=C.YELLOW, fg_color="transparent",
            cursor="hand2",
        )
        self.lbl_update.bind("<Button-1>", lambda e: self._show_update_dialog())

        # ── Stats Card ─────────────────────────────────────────────────
        stats_card = ctk.CTkFrame(self, fg_color=C.CARD, corner_radius=16,
                                   border_width=1, border_color=C.CARD_BORDER)
        stats_card.pack(fill="x", padx=24, pady=(12, 0))

        self.lbl_stats = ctk.CTkLabel(
            stats_card, text="", font=F(11),
            text_color=C.TEXT, fg_color="transparent",
        )
        self.lbl_stats.pack(pady=(10, 2))

        self.lbl_meta = ctk.CTkLabel(
            stats_card, text="", font=F(10, "bold"),
            text_color=C.TEXT_DIM, fg_color="transparent",
        )
        self.lbl_meta.pack(pady=(0, 10))

        # ── Weekly Chart Card ──────────────────────────────────────────
        chart_card = ctk.CTkFrame(self, fg_color=C.CARD, corner_radius=16,
                                   border_width=1, border_color=C.CARD_BORDER)
        chart_card.pack(fill="x", padx=24, pady=(8, 0))

        ctk.CTkLabel(
            chart_card, text=_("ultimos_7_dias"), font=F(9, "bold"),
            text_color=C.TEXT_DIM, fg_color="transparent",
        ).pack(anchor="w", padx=14, pady=(10, 2))

        self._week_canvas = Canvas(
            chart_card, width=300, height=70,
            bg=C.CARD, highlightthickness=0,
        )
        self._week_canvas.pack(padx=10, pady=(0, 10))

        # ── Info Bar ───────────────────────────────────────────────────
        info_bar = ctk.CTkFrame(self, fg_color="transparent")
        info_bar.pack(fill="x", padx=28, pady=(10, 0))

        self.lbl_agua = ctk.CTkLabel(
            info_bar, text="", font=F(9),
            text_color=C.AGUA, fg_color="transparent",
        )
        self.lbl_agua.pack(side="left")

        self.lbl_cfg = ctk.CTkLabel(
            info_bar, text="", font=F(9),
            text_color=C.TEXT_MUTED, fg_color="transparent",
        )
        self.lbl_cfg.pack(side="right")

        self._update_cfg_label()
        self._update_stats_label()
        self._update_agua_label()

        # ── Action Buttons (modern pills) ──────────────────────────────
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=(14, 4))

        self.btn_p = ctk.CTkButton(
            bf, text=_("btn_pausar"), font=F(11, "bold"),
            fg_color=C.BG3, text_color=C.TEXT, hover_color=C.BG4,
            width=100, height=38, corner_radius=19, border_width=0,
            command=self._toggle,
        )
        self.btn_p.pack(side="left", padx=4)

        ctk.CTkButton(
            bf, text="▶  " + _("pausa_ya"), font=F(11, "bold"),
            fg_color=C.ACCENT, text_color="#FFFFFF",
            hover_color=darken_color(C.ACCENT),
            width=110, height=38, corner_radius=19, border_width=0,
            command=self._now,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            bf, text="⏰  " + _("posponer"), font=F(11, "bold"),
            fg_color=C.BG3, text_color=C.TEXT, hover_color=C.BG4,
            width=110, height=38, corner_radius=19, border_width=0,
            command=self._posponer,
        ).pack(side="left", padx=4)

        # ── Minimize link ──────────────────────────────────────────────
        ctk.CTkButton(
            self, text=_("minimizar"), font=F(9),
            fg_color="transparent", text_color=C.TEXT_MUTED,
            hover_color=C.BG3, corner_radius=8, width=80, height=24,
            cursor="hand2",
            command=self._hide,
        ).pack(pady=(4, 4))

        # ── Extra Buttons Row ─────────────────────────────────────────
        extra_row = ctk.CTkFrame(self, fg_color="transparent")
        extra_row.pack(pady=(0, 8))

        ctk.CTkButton(
            extra_row, text="🏆 " + _("logros"), font=F(9),
            fg_color=C.BG3, text_color=C.TEXT_DIM, hover_color=C.BG4,
            width=90, height=28, corner_radius=14,
            command=lambda: AchievementsWindow(self, self.stats, self.cfg.get("logros_mostrados", [])).center(),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            extra_row, text="🏋️ " + _("workouts"), font=F(9),
            fg_color=C.BG3, text_color=C.TEXT_DIM, hover_color=C.BG4,
            width=90, height=28, corner_radius=14,
            command=self._open_workouts,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            extra_row, text="🤖 IA", font=F(9),
            fg_color=C.BG3, text_color=C.TEXT_DIM, hover_color=C.BG4,
            width=70, height=28, corner_radius=14,
            command=self._open_ai_insights,
        ).pack(side="left", padx=3)

    def _update_cfg_label(self) -> None:
        c = self.cfg
        modo = c.get("modo", "normal").upper()
        self.lbl_cfg.configure(
            text=f"{modo}  ·  {c['intervalo_min']}m / {c['duracion_pausa_min']}m  ·  "
                 f"{c['hora_inicio']}–{c['hora_fin']}",
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

        # Nivel y XP
        level, xp, xp_needed = self._get_level()
        level_text = f"  🎮 Nv.{level}"

        self.lbl_stats.configure(
            text=f"✅ {comp} completadas  ⏭ {s['saltadas']} saltadas  🔥 {s.get('racha', 0)}d racha{level_text}",
            text_color=comp_color,
        )
        pct = min(100, int(comp / meta * 100)) if meta > 0 else 0

        # Desafío diario
        challenge = self._get_daily_challenge()
        completed = self.cfg.get("daily_challenge_completed", "")
        challenge_icon = "✅" if completed == challenge["id"] else "🎯"
        challenge_text = f"{challenge_icon} {challenge['title']}"

        top: str = "🎯 ¡Meta alcanzada!" if comp >= meta else f"{pct}% — {comp}/{meta}"
        self.lbl_meta.configure(text=f"{top}  ·  {challenge_text}", text_color=comp_color)
        self._draw_week_chart()

    def _update_wellness_note(self) -> None:
        note = random.choice(WELLNESS_NOTES)
        self._wellness_label.configure(text=f"{note['icon']} {note['title']}\n{note['msg']}")

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
                self.after(i * 15, lambda v=i / 10: self._safe_set_alpha(v))
        except Exception:
            try:
                self.deiconify()
            except Exception:
                pass

    def _safe_set_alpha(self, alpha: float) -> None:
        try:
            if self.winfo_exists():
                self.attributes("-alpha", alpha)
        except Exception:
            pass

    def _center(self) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 3  # Un poco más arriba del centro para verse mejor
        self.geometry(f"+{x}+{y}")

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

            # Auto night mode check (cada 5 min)
            if self.remaining % 3600 == 0:
                self._check_auto_night_mode()
                self._save_weekly_snapshot()

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

    def _trigger_pausa(self) -> None:
        try:
            if self.pausa_open:
                return
            self.pausa_open = True
            log.info("Pausa activada, ejercicio=%s", self._last_ej or "aleatorio")
            self._show()
            sonido = self.cfg.get("sonido", True)
            if sonido:
                threading.Thread(target=get_audio_manager().play_alert, daemon=True).start()
            self.after(0, lambda: send_win_notification(
                APP_DISPLAY,
                _("break_time_body"),
                sound=self.cfg.get("notificacion_sonido", "default") if sonido else "None",
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
            BreakWindow(
                self, ej, dur, self._done_pausa, self._skip_pausa,
                sonido_ambiente=self.cfg.get("sonido_ambiente", "ninguno"),
                guia_voz=self.cfg.get("guia_voz", True),
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
        self.stats["this_week_completadas"] = self.stats.get("this_week_completadas", 0) + 1
        now = datetime.now()
        self.stats["historial"].append({
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M"),
            "ejercicio": self._last_ej,
            "estado": "completada",
        })

        # Mini-interacciones: confetti + XP
        self._spawn_confetti(35)
        self._spawn_sparkles(6)
        self._add_xp(25)
        self._check_daily_challenge()
        self._on_break_done_pet()

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
        self._cfg_mgr.trim_csv()
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
        self._cfg_mgr.trim_csv()
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
        if not self.running:
            self._toggle()

    def _posponer(self) -> None:
        mins: int = self.cfg.get("posponer_min", 10)
        self._total_sec = mins * 60
        self.remaining = self._total_sec
        self.lbl_st.configure(text=_("pausa_pospuesta").format(mins=mins))

    def _hotkey_break_now(self) -> None:
        self.after(0, self._now)

    def _hotkey_snooze(self) -> None:
        self.after(0, self._posponer)

    def _hotkey_pause_resume(self) -> None:
        self.after(0, self._toggle)

    def _hotkey_show_hide(self) -> None:
        self.after(0, self._toggle_visibility)

    def _toggle_visibility(self) -> None:
        if self.winfo_viewable():
            self._hide()
        else:
            self._show()

    def _hotkey_quit(self) -> None:
        self.after(0, self._quit)

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
        self.lbl_st.configure(text=_("descargando_update"))
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        threading.Thread(target=self._do_download, args=(url,), daemon=True).start()

    def _do_download(self, url: str) -> None:
        import tempfile
        import urllib.request
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
        # Use install dir from registry if available
        install_dir = _get_install_dir_from_registry() or self._app_dir
        current_exe: str = os.path.join(install_dir, os.path.basename(self._app_path))
        if not os.path.exists(current_exe):
            current_exe = self._app_path
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
            f.write('del "%~f0"\n')
        import subprocess
        subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)
        self._water.stop()
        get_audio_manager().cleanup()
        if self._tray:
            self._tray.stop()
        self.destroy()
        sys.exit(0)

    # ════════════════════════════════════════════════════════════════════════
    # MINI-INTERACCIONES: Partículas, Sparkles, Confetti
    # ════════════════════════════════════════════════════════════════════════

    def _start_particle_animation(self) -> None:
        self._animate_particles()

    def _animate_particles(self) -> None:
        try:
            if not self.winfo_exists():
                return
            canvas = self._canvas
            cx, cy, r = 110, 110, 95

            # Limpiar partículas anteriores
            canvas.delete("particle")
            canvas.delete("sparkle")
            canvas.delete("confetti")

            self._anim_frame = (self._anim_frame + 1) % 10000

            # Partículas flotantes alrededor del reloj
            if self.running and not self.pausa_open and self.remaining > 0:
                num_particles = 6
                for i in range(num_particles):
                    angle = (self._anim_frame * 0.02 + i * (2 * math.pi / num_particles))
                    dist = r + 15 + math.sin(angle * 2) * 8
                    px = cx + math.cos(angle) * dist
                    py = cy + math.sin(angle) * dist
                    size = 2 + math.sin(angle * 3 + self._anim_frame * 0.1) * 1.5
                    color = C.ACCENT if i % 2 == 0 else C.GREEN
                    canvas.create_oval(
                        px - size, py - size, px + size, py + size,
                        fill=color, outline="", tags="particle",
                    )

            # Sparkles cuando la meta se acerca
            if self.running and self.remaining > 0:
                total = self._total_sec if self._total_sec else 1
                pct = self.remaining / total
                if pct < 0.15:  # Últimos 15%
                    import random
                    for _ in range(2):
                        angle = random.uniform(0, 2 * math.pi)
                        dist = r + random.uniform(-5, 5)
                        sx = cx + math.cos(angle) * dist
                        sy = cy + math.sin(angle) * dist
                        size = random.uniform(1, 3)
                        canvas.create_oval(
                            sx - size, sy - size, sx + size, sy + size,
                            fill=C.YELLOW, outline="", tags="sparkle",
                        )

            # Confetti cuando se completa
            for c in self._confetti[:]:
                c["y"] += c["vy"]
                c["x"] += c["vx"]
                c["vy"] += 0.1  # gravedad
                c["rotation"] += c["vr"]
                if c["y"] > 250:
                    self._confetti.remove(c)
                    continue
                canvas.create_rectangle(
                    c["x"] - 3, c["y"] - 2, c["x"] + 3, c["y"] + 2,
                    fill=c["color"], outline="", tags="confetti",
                )

            self.after(50, self._animate_particles)
        except Exception:
            self.after(100, self._animate_particles)

    def _spawn_confetti(self, count: int = 40) -> None:
        import random
        colors = [C.ACCENT, C.GREEN, C.YELLOW, "#EF4444", "#8B5CF6", "#EC4899"]
        cap = max(count, 80)
        for __ in range(count):
            if len(self._confetti) >= cap:
                break
            self._confetti.append({
                "x": random.uniform(30, 190),
                "y": random.uniform(-20, 30),
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(1, 3),
                "color": random.choice(colors),
                "rotation": random.uniform(0, 360),
                "vr": random.uniform(-5, 5),
            })

    def _spawn_sparkles(self, count: int = 8) -> None:
        canvas = self._canvas
        cx, cy, r = 110, 110, 95
        for __ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            dist = r + random.uniform(-10, 10)
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist
            size = random.uniform(2, 5)
            canvas.create_text(
                sx, sy, text="✨", font=("Segoe UI Emoji", int(size * 3)),
                tags="sparkle",
            )

    # ════════════════════════════════════════════════════════════════════════
    # SISTEMA DE NIVELES
    # ════════════════════════════════════════════════════════════════════════

    def _get_level(self) -> tuple[int, int, int]:
        xp = self.stats.get("xp", 0)
        level = 1
        xp_needed = 100
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.5)
        return level, xp, xp_needed

    def _add_xp(self, amount: int) -> None:
        old_level, old_xp, old_needed = self._get_level()
        self.stats["xp"] = self.stats.get("xp", 0) + amount
        new_level, new_xp, new_needed = self._get_level()
        if new_level > old_level:
            self._spawn_confetti(30)
            toast("🎉 ¡Nivel aumentado!", f"¡Ahora eres nivel {new_level}!", kind="exito")

    # ════════════════════════════════════════════════════════════════════════
    # DESAFÍOS DIARIOS
    # ════════════════════════════════════════════════════════════════════════

    DAILY_CHALLENGES = [
        {"id": "early_bird", "title": "🌅 Madrugador", "desc": "Completa una pausa antes de las 9am", "xp": 50},
        {"id": "double", "title": "💪 Doble", "desc": "Completa 2 pausas en 1 hora", "xp": 30},
        {"id": "streak3", "title": "🔥 Racha x3", "desc": "Consigue una racha de 3 días", "xp": 75},
        {"id": "all_exercises", "title": "🏃 Variedad", "desc": "Usa 3 ejercicios diferentes hoy", "xp": 40},
        {"id": "posture", "title": "🧘 Postura perfecta", "desc": "Activa el recordatorio de postura", "xp": 25},
        {"id": "hydration", "title": "💧 Hidratado", "desc": "Responde 3 recordatorios de agua", "xp": 35},
        {"id": "complete_all", "title": "🏆 Día completo", "desc": "Alcanza tu meta diaria de pausas", "xp": 100},
        {"id": "night_owl", "title": "🦉 Búho nocturno", "desc": "Completa una pausa después de las 8pm", "xp": 50},
    ]

    def _get_daily_challenge(self) -> dict:
        today = date.today().toordinal()
        idx = today % len(self.DAILY_CHALLENGES)
        return self.DAILY_CHALLENGES[idx]

    def _check_daily_challenge(self) -> None:
        challenge = self._get_daily_challenge()
        completed = self.cfg.get("daily_challenge_completed", "")
        if completed == challenge["id"]:
            return
        cid = challenge["id"]
        success = False
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        if cid == "early_bird":
            success = now.hour < 9 and self.stats.get("completadas", 0) > 0
        elif cid == "double":
            today_breaks = [
                e for e in self.stats.get("historial", [])
                if e.get("fecha") == today_str and e.get("estado") == "completada"
            ]
            for i, b1 in enumerate(today_breaks):
                for b2 in today_breaks[i + 1:]:
                    t1 = datetime.strptime(f"{b1['fecha']} {b1['hora']}", "%Y-%m-%d %H:%M")
                    t2 = datetime.strptime(f"{b2['fecha']} {b2['hora']}", "%Y-%m-%d %H:%M")
                    if abs((t1 - t2).total_seconds()) <= 3600:
                        success = True
                        break
                if success:
                    break
        elif cid == "streak3":
            success = self.stats.get("racha", 0) >= 3
        elif cid == "all_exercises":
            exercises_today = set()
            for e in self.stats.get("historial", []):
                if e.get("fecha") == today_str and e.get("estado") == "completada":
                    exercises_today.add(e.get("ejercicio", ""))
            success = len(exercises_today) >= 3
        elif cid == "posture":
            success = self.cfg.get("postura_recordatorio", False)
        elif cid == "hydration":
            success = self.stats.get("agua_respondidas_hoy", 0) >= 3
        elif cid == "complete_all":
            success = self.stats.get("completadas", 0) >= self.cfg.get("meta_pausas", 6)
        elif cid == "night_owl":
            success = now.hour >= 20

        if success:
            self.cfg["daily_challenge_completed"] = challenge["id"]
            self._add_xp(challenge["xp"])
            self._spawn_confetti(25)
            toast("🎯 ¡Desafío completado!", f"{challenge['title']}: +{challenge['xp']} XP", kind="exito")

    # ════════════════════════════════════════════════════════════════════════
    # FRASES MOTIVACIONALES ANIMADAS (typewriter)
    # ════════════════════════════════════════════════════════════════════════

    def _animate_phrase(self, phrase: str, label: ctk.CTkLabel, idx: int = 0) -> None:
        try:
            if not self.winfo_exists():
                return
            if idx <= len(phrase):
                label.configure(text=phrase[:idx])
                self.after(40, lambda: self._animate_phrase(phrase, label, idx + 1))
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════════════════
    # MODO NOCTURNO AUTOMÁTICO
    # ════════════════════════════════════════════════════════════════════════

    def _check_auto_night_mode(self) -> None:
        hour = datetime.now().hour
        if 20 <= hour or hour < 7:
            if self.cfg.get("tema") != "oscuro":
                self.cfg["tema"] = "oscuro"
                set_theme("oscuro", self.cfg.get("color_acento", "azul"), self.cfg.get("fondo", "estandar"))

    # ════════════════════════════════════════════════════════════════════════
    # COMPARATIVA SEMANAL
    # ════════════════════════════════════════════════════════════════════════

    def _get_weekly_comparison(self) -> tuple[int, int]:
        this_week = self.stats.get("this_week_completadas", 0)
        last_week = self.stats.get("last_week_completadas", 0)
        return this_week, last_week

    def _save_weekly_snapshot(self) -> None:
        today = date.today()
        last_snap = self.stats.get("last_snapshot_date", "")
        today_str = today.isoformat()
        if today.weekday() == 0 and last_snap != today_str:
            self.stats["last_week_completadas"] = self.stats.get("this_week_completadas", 0)
            self.stats["this_week_completadas"] = 0
            self.stats["last_snapshot_date"] = today_str

    # ════════════════════════════════════════════════════════════════════════
    # MODO MEDITACIÓN (respiración guiada)
    # ════════════════════════════════════════════════════════════════════════

    def _start_meditation(self) -> None:
        self._meditation_active = True
        self._meditation_phase = 0  # 0=inhalar, 1=retener, 2=exhalar
        self._meditation_timer = 0
        self._meditation_cycle = 0
        self._animate_meditation()

    def _animate_meditation(self) -> None:
        if not getattr(self, "_meditation_active", False):
            return
        phases = [("Inhala... 4s", 4), ("Retén... 4s", 4), ("Exhala... 6s", 6)]
        phase_name, phase_dur = phases[self._meditation_phase % 3]
        self.lbl_st.configure(text=phase_name)

        canvas = self._canvas
        cx, cy = 110, 110
        canvas.delete("meditation")
        size = 20 + self._meditation_timer * 8
        canvas.create_oval(
            cx - size, cy - size, cx + size, cy + size,
            outline=C.ACCENT, width=2, tags="meditation",
        )

        self._meditation_timer += 1
        if self._meditation_timer >= phase_dur:
            self._meditation_timer = 0
            self._meditation_phase += 1
            if self._meditation_phase >= 3:
                self._meditation_phase = 0
                self._meditation_cycle += 1
                if self._meditation_cycle >= 5:
                    self._meditation_active = False
                    canvas.delete("meditation")
                    self.lbl_st.configure(text="Meditación completada 🧘")
                    return

        self.after(1000, self._animate_meditation)

    # ════════════════════════════════════════════════════════════════════════
    # RECORDATORIO 20-20-20 (ojos)
    # ════════════════════════════════════════════════════════════════════════

    def _schedule_eye_reminder(self) -> None:
        if self.cfg.get("eye_reminder", False):
            ms = 20 * 60 * 1000  # 20 minutos
            self.after(ms, self._eye_reminder_notify)

    def _eye_reminder_notify(self) -> None:
        if not self.running:
            return
        toast("👁️ Regla 20-20-20",
              "Mira algo a 6+ metros por 20 segundos", kind="info", duration=8000)
        self._schedule_eye_reminder()

    # ════════════════════════════════════════════════════════════════════════
    # SPOTIFY (placeholder - detecta si está reproduciendo)
    # ════════════════════════════════════════════════════════════════════════

    def _check_spotify(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq spotify.exe"],
                capture_output=True, text=True, timeout=3
            )
            return "spotify.exe" in result.stdout.lower()
        except Exception:
            return False

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

        # Update posture reminder
        if self.cfg.get("postura_recordatorio", False):
            self._posture.start(self.cfg.get("postura_intervalo_min", 20))
        else:
            self._posture.stop()

        # Update floating timer
        if self.cfg.get("floating_enabled", False) and (not self._floating or not self._floating.winfo_exists()):
            self._create_floating_timer()
        elif not self.cfg.get("floating_enabled", False) and self._floating and self._floating.winfo_exists():
            self._floating.destroy()
            self._floating = None

        # Update compact mode
        if self.cfg.get("compacto_enabled", False) and (not self._compact or not self._compact.winfo_exists()):
            self._create_compact_window()
        elif not self.cfg.get("compacto_enabled", False) and self._compact and self._compact.winfo_exists():
            self._compact.destroy()
            self._compact = None

    def _open_workouts(self) -> None:
        workouts = self.cfg.get("workouts", [])
        WorkoutWindow(
            self, workouts, EJERCICIOS,
            lambda wo: self.cfg.update({"workouts": wo}) or self._cfg_mgr.save_config(self.cfg),
            self._run_workout,
        ).center()

    def _run_workout(self, wo: dict) -> None:
        toast(_("workout"), f"Rutina: {wo['nombre']}", kind="info")

    def _open_custom_exercise(self) -> None:
        def on_save(ej: dict) -> None:
            EJERCICIOS.append(ej)
            activos = self.cfg.get("ejercicios_activos", [])
            activos.append(ej["id"])
            self.cfg["ejercicios_activos"] = activos
            self._cfg_mgr.save_config(self.cfg)
            toast(_("toast_exito"), f"Ejercicio '{ej['nombre']}' creado", kind="exito")
        CustomExerciseWindow(self, on_save).center()

    # ── FlowBuddy - Mascota Virtual ──────────────────────────────────

    def _start_pet_decay(self) -> None:
        """Reduce stats de la mascota cada 30 min si no haces pausas."""
        def _decay():
            try:
                now = datetime.now().timestamp()
                last_break = self._pet_state.get("ultimo_alimento", now)
                hours_since = (now - last_break) / 3600

                if hours_since > 1:
                    self._pet_state["energia"] = max(0, self._pet_state.get("energia", 100) - int(hours_since * 5))
                    self._pet_state["felicidad"] = max(0, self._pet_state.get("felicidad", 100) - int(hours_since * 3))

                if hasattr(self, "_buddy_widget") and self._buddy_widget.winfo_exists():
                    self._buddy_widget.update_state(self._pet_state)
                self.cfg["pet_state"] = self._pet_state
            except Exception:
                pass
            self._pet_decay_job = self.after(30 * 60 * 1000, _decay)
        self._pet_decay_job = self.after(30 * 60 * 1000, _decay)

    def _feed_pet(self) -> None:
        self._pet_state["energia"] = min(100, self._pet_state.get("energia", 100) + 20)
        self._pet_state["felicidad"] = min(100, self._pet_state.get("felicidad", 100) + 10)
        self._pet_state["ultimo_alimento"] = datetime.now().timestamp()
        self.cfg["pet_state"] = self._pet_state
        toast("🐾 FlowBuddy", "¡FlowBuddy está feliz! +20 energía", kind="exito")
        if hasattr(self, "_buddy_widget") and self._buddy_widget.winfo_exists():
            self._buddy_widget.update_state(self._pet_state)

    def _play_with_pet(self) -> None:
        self._pet_state["felicidad"] = min(100, self._pet_state.get("felicidad", 100) + 25)
        self._pet_state["energia"] = max(0, self._pet_state.get("energia", 100) - 10)
        self.cfg["pet_state"] = self._pet_state
        toast("🐾 FlowBuddy", "¡FlowBuddy jugó contigo! +25 felicidad", kind="info")
        if hasattr(self, "_buddy_widget") and self._buddy_widget.winfo_exists():
            self._buddy_widget.update_state(self._pet_state)

    def _on_break_done_pet(self) -> None:
        """Llamar cuando se completa una pausa para mejorar al pet."""
        self._pet_state["energia"] = min(100, self._pet_state.get("energia", 100) + 15)
        self._pet_state["felicidad"] = min(100, self._pet_state.get("felicidad", 100) + 20)
        self._pet_state["salud"] = min(100, self._pet_state.get("salud", 100) + 5)
        self._pet_state["ultimo_alimento"] = datetime.now().timestamp()
        self.cfg["pet_state"] = self._pet_state

    def _open_flowbuddy(self) -> None:
        FlowBuddyWindow(
            self, self._pet_state,
            on_feed=self._feed_pet,
            on_play=self._play_with_pet,
        ).center()

    # ── AI Insights ──────────────────────────────────────────────────

    def _open_ai_insights(self) -> None:
        insights = self._ai_engine.analyze()
        AIInsightsWindow(self, insights).center()

    def _open_config(self) -> None:
        def on_save(c: dict[str, Any]) -> None:
            old_tema = self.cfg.get("tema")
            old_font = self.cfg.get("tamano_letra")
            old_accent = self.cfg.get("color_acento")
            old_fondo = self.cfg.get("fondo")
            self.cfg = c
            self._total_sec = c["intervalo_min"] * 60
            self.remaining = self._total_sec
            self._cfg_mgr.save_config(c)
            if c.get("tema") != old_tema or c.get("tamano_letra") != old_font or c.get("color_acento") != old_accent or c.get("fondo") != old_fondo:
                if c.get("tamano_letra") != old_font:
                    set_font_size(c.get("tamano_letra", "normal"))
                self._reapply_theme()
            else:
                self._update_cfg_label()
                self._update_agua_label()

            # Floating timer
            if c.get("floating_enabled", False) and (not self._floating or not self._floating.winfo_exists()):
                self._create_floating_timer()
            elif not c.get("floating_enabled", False) and self._floating and self._floating.winfo_exists():
                self._floating.destroy()
                self._floating = None

            # Compact window
            if c.get("compacto_enabled", False) and (not self._compact or not self._compact.winfo_exists()):
                self._create_compact_window()
            elif not c.get("compacto_enabled", False) and self._compact and self._compact.winfo_exists():
                self._compact.destroy()
                self._compact = None

            self._water.restart()
        profiles: list[str] = self._cfg_mgr.list_profiles()
        ConfigWindow(self, self.cfg, on_save, self._app_path, profiles=profiles)

    def _open_stats(self) -> None:
        history = self._cfg_mgr.get_stats_history()
        StatsWindowEnhanced(
            self, self.stats, self.cfg["meta_pausas"],
            self._hist_file, history=history,
            on_export=self._export_stats,
            on_import=self._import_stats,
        )

    def _export_stats(self) -> None:
        try:
            from tkinter import filedialog
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                title=_("exportar_stats"),
            )
            if path:
                import json
                csv_history = ""
                try:
                    with open(self._hist_file, encoding="utf-8") as f:
                        csv_history = f.read()
                except Exception:
                    pass
                data = {
                    "version": 2,
                    "stats": self.stats,
                    "config": {k: v for k, v in self.cfg.items() if not k.startswith("_")},
                    "historial_csv": csv_history,
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                toast(_("toast_exito"), _("exportar_ok").format(path=path), kind="exito")
        except Exception as e:
            toast(_("error"), str(e), kind="error")

    def _import_stats(self) -> None:
        try:
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                filetypes=[("JSON", "*.json")],
                title=_("importar_stats"),
            )
            if path:
                import json
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if "stats" in data:
                    self.stats.update(data["stats"])
                    self._cfg_mgr.save_stats(self.stats)
                if "config" in data:
                    for k, v in data["config"].items():
                        if k in self.cfg:
                            self.cfg[k] = v
                    self._cfg_mgr.save_config(self.cfg)
                if data.get("version") == 2 and data.get("historial_csv"):
                    try:
                        with open(self._hist_file, "w", encoding="utf-8", newline="") as f:
                            f.write(data["historial_csv"])
                    except Exception:
                        pass
                elif "history" in data:
                    self._cfg_mgr.save_stats(data["history"])
                toast(_("toast_exito"), _("importar_ok"), kind="exito")
        except Exception as e:
            toast(_("error"), _("importar_error").format(error=str(e)), kind="error")

    def _open_uninstall(self) -> None:
        UninstallWindow(
            self, self._quit,
            self._config_file, self._stats_file, self._hist_file, self._app_dir,
        )
