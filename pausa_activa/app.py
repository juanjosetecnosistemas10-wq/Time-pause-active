"""Clase principal de la aplicación."""

from __future__ import annotations

import os
import random
import sys
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Any, Callable

from pausa_activa.constants import (
    BG, BG2, BG3, ACCENT, ACCENT2, GREEN, YELLOW, TEXT, TEXT_DIM, BORDER,
    APP_DISPLAY, EJERCICIOS, FRASES, set_theme, set_idioma,
    log,
)
from pausa_activa.config import ConfigManager
from pausa_activa.audio import AudioManager
from pausa_activa.water import WaterReminder
from pausa_activa.notifications import send_win_notification
from pausa_activa.installer import InstallerWindow, _is_installed
from pausa_activa.windows import (
    PausaWindow, StatsWindow, ConfigWindow, WelcomeWindow, UninstallWindow,
    audio_manager,
)

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE: bool = True
except ImportError:
    TRAY_AVAILABLE = False


class Updater:
    """Auto-updater vía GitHub Releases."""

    REPO: str = "tu_usuario/Time-pause-active"

    @staticmethod
    def check() -> str | None:
        try:
            import urllib.request
            import json
            url: str = f"https://api.github.com/repos/{Updater.REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "PausasActivas"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data: dict[str, Any] = json.loads(resp.read().decode())
            return data.get("tag_name")
        except Exception:
            return None


class App(tk.Tk):
    def __init__(
        self,
        app_path: str,
        app_dir: str,
        cfg_mgr: ConfigManager | None = None,
        audio_mgr: AudioManager | None = None,
        water_mgr: WaterReminder | None = None,
    ) -> None:
        super().__init__()

        # Dependencias inyectadas o por defecto
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

        # Aplicar tema e idioma guardados
        set_theme(self.cfg.get("tema", "oscuro"))
        set_idioma(self.cfg.get("idioma", "es"))

        self.title(APP_DISPLAY)
        self.configure(bg=BG)
        self.resizable(False, False)
        try:
            self.iconbitmap(os.path.join(app_dir, "PausasActivas.ico"))
        except Exception:
            pass

        self._water: WaterReminder = water_mgr or WaterReminder(lambda: self.cfg)

        log.info(
            "App iniciada. running=%s, instalada=%s, primera_vez=%s",
            self.running, _is_installed(), self.cfg.get("primera_vez", True),
        )

        # Auto-updater en segundo plano
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
            APP_DISPLAY,
        )
        self._load_ejercicios()

    def _load_ejercicios(self) -> None:
        from pausa_activa.constants import load_ejercicios_from_file
        ejercicios = load_ejercicios_from_file(self._ejercicios_file)
        import pausa_activa.constants as const
        const.EJERCICIOS.clear()
        const.EJERCICIOS.extend(ejercicios)

    def _check_update(self) -> None:
        try:
            version: str | None = Updater.check()
            if version:
                log.info("Ultima version disponible: %s", version)
        except Exception:
            pass

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
        self._build()
        self._center()
        self.deiconify()
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._hide)

        if self.cfg.get("agua_activo", True):
            self._water.start()

        if TRAY_AVAILABLE:
            threading.Thread(target=self._start_tray, daemon=True).start()

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _start_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Abrir",          self._show_cb, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pausa ya",        lambda i, it: self.after(0, self._now)),
            pystray.MenuItem("Posponer",        lambda i, it: self.after(0, self._posponer)),
            pystray.MenuItem("Pausar/Reanudar", lambda i, it: self.after(0, self._toggle)),
            pystray.MenuItem("Estadisticas",    lambda i, it: self.after(0, self._open_stats)),
            pystray.MenuItem("Configuracion",   lambda i, it: self.after(0, self._open_config)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Desinstalar",     lambda i, it: self.after(0, self._open_uninstall)),
            pystray.MenuItem("Salir", self._quit),
        )
        self._tray = pystray.Icon(
            "PausasActivas",
            self._make_tray_icon(TRAY_ACTIVE),
            "Pausas Activas",
            menu,
        )
        self._tray.run()

    def _update_tray(self) -> None:
        if not TRAY_AVAILABLE or not self._tray:
            return
        if not self.running:
            c = TRAY_PAUSED
            tip = "Pausado"
        elif not self._in_active_hours(self.cfg):
            c = TRAY_OFF
            tip = "Fuera de horario"
        else:
            c = TRAY_ACTIVE
            tip = f"Proxima pausa en {self._fmt_time(self.remaining)}"
        self._tray.icon = self._make_tray_icon(c)
        self._tray.title = f"Pausas Activas - {tip}"

    @staticmethod
    def _make_tray_icon(color: tuple[int, int, int] = (108, 99, 255), size: int = 64):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 4, size - 4, size - 4], fill=color + (255,))
        d.text((size // 2 - 6, size // 2 - 10), "P", fill=(255, 255, 255, 255))
        return img

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
        h = tk.Frame(self, bg=BG)
        h.pack(fill="x", padx=24, pady=(22, 0))
        tk.Label(h, text=APP_DISPLAY, font=("Segoe UI", 15, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Button(h, text="Stats", font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM,
                  bd=0, cursor="hand2", activebackground=BG, activeforeground=GREEN,
                  relief="flat", command=self._open_stats).pack(side="right", padx=(4, 0))
        tk.Button(h, text="Config", font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM,
                  bd=0, cursor="hand2", activebackground=BG, activeforeground=ACCENT,
                  relief="flat", command=self._open_config).pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=10)
        self.lbl_badge = tk.Label(self, text="ACTIVO", font=("Segoe UI", 8, "bold"),
                                  bg=BG, fg=GREEN)
        self.lbl_badge.pack()
        tk.Label(self, text="PROXIMA PAUSA EN", font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=TEXT_DIM).pack()
        self.lbl_cd = tk.Label(self, text="00:00",
                               font=("Courier New", 54, "bold"), bg=BG, fg=ACCENT)
        self.lbl_cd.pack(pady=(2, 0))
        self.pb = ttk.Progressbar(self, orient="horizontal", length=280,
                                  mode="determinate", maximum=100, value=100)
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("a.Horizontal.TProgressbar", troughcolor=BG3, background=ACCENT,
                    bordercolor=BG3, lightcolor=ACCENT, darkcolor=ACCENT)
        self.pb.configure(style="a.Horizontal.TProgressbar")
        self.pb.pack(pady=(6, 0))
        self.lbl_st = tk.Label(self, text="", font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM)
        self.lbl_st.pack(pady=(4, 0))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)
        self.lbl_meta = tk.Label(self, text="", font=("Segoe UI", 9, "bold"),
                                 bg=BG, fg=TEXT_DIM)
        self.lbl_meta.pack()
        self.lbl_stats = tk.Label(self, text="", font=("Segoe UI", 9),
                                  bg=BG, fg=TEXT_DIM)
        self.lbl_stats.pack()
        self.lbl_cfg = tk.Label(self, text="", font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM)
        self.lbl_cfg.pack()
        self.lbl_agua = tk.Label(self, text="", font=("Segoe UI", 8), bg=BG, fg="#4FC3F7")
        self.lbl_agua.pack()
        self._update_cfg_label()
        self._update_stats_label()
        self._update_agua_label()
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(14, 8))
        self.btn_p = tk.Button(bf, text="Pausar", font=("Segoe UI", 10), bg=BG3,
                               fg=TEXT, bd=0, cursor="hand2", activebackground=BORDER,
                               activeforeground=TEXT, relief="flat", padx=14, pady=7,
                               command=self._toggle)
        self.btn_p.pack(side="left", padx=4)
        tk.Button(bf, text="Pausa ya", font=("Segoe UI", 10), bg=ACCENT, fg="white",
                  bd=0, cursor="hand2", activebackground="#5A52D5",
                  activeforeground="white", relief="flat", padx=14, pady=7,
                  command=self._now).pack(side="left", padx=4)
        tk.Button(bf, text="Posponer", font=("Segoe UI", 10), bg=BG3, fg=TEXT,
                  bd=0, cursor="hand2", activebackground=BORDER, activeforeground=TEXT,
                  relief="flat", padx=14, pady=7, command=self._posponer).pack(side="left", padx=4)
        tk.Button(self, text="Minimizar a bandeja", font=("Segoe UI", 8), bg=BG,
                  fg=TEXT_DIM, bd=0, cursor="hand2", activebackground=BG,
                  activeforeground=TEXT, relief="flat",
                  command=self._hide).pack(pady=(0, 18))

    def _update_cfg_label(self) -> None:
        c = self.cfg
        modo = c.get("modo", "normal").upper()
        self.lbl_cfg.config(
            text=f"[{modo}] Cada {c['intervalo_min']} min  -  "
                 f"Pausa {c['duracion_pausa_min']} min  -  "
                 f"{c['hora_inicio']} a {c['hora_fin']}"
        )

    def _update_agua_label(self) -> None:
        if self.cfg.get("agua_activo", True):
            self.lbl_agua.config(
                text=f"💧 Recordatorio de agua cada {self.cfg.get('agua_min', 30)} min"
            )
        else:
            self.lbl_agua.config(text="")

    def _update_stats_label(self) -> None:
        s = self.stats
        meta: int = self.cfg["meta_pausas"]
        comp: int = s["completadas"]
        self.lbl_stats.config(
            text=f"Hoy: {comp} completadas  /  {s['saltadas']} saltadas"
        )
        barra: str = "█" * comp + "░" * (max(0, meta - comp))
        color: str = GREEN if comp >= meta else (YELLOW if comp >= meta // 2 else TEXT_DIM)
        self.lbl_meta.config(text=f"Meta: {barra} {comp}/{meta}", fg=color)

    def _center(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{sw - w - 30}+{30}")

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
            return dtime(h0, m0) <= now <= dtime(h1, m1)
        except Exception:
            return True

    def _countdown_color(self) -> str:
        if self._total_sec == 0:
            return ACCENT
        pct: float = self.remaining / self._total_sec
        if pct > 0.5:
            return ACCENT
        if pct > 0.2:
            return YELLOW
        return ACCENT2

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
        if not self.running or self.pausa_open:
            self._job = self.after(1000, self._tick)
            return

        if self.cfg.get("fin_de_semana", False) and self._is_weekend():
            self.lbl_st.config(text="Fin de semana — descansando 😎")
            self.lbl_cd.config(fg=TEXT_DIM, text="--:--")
            self.lbl_badge.config(text="FIN DE SEMANA", fg=YELLOW)
            self._job = self.after(1000, self._tick)
            return

        if not self._in_active_hours(self.cfg):
            self.lbl_st.config(text="Fuera del horario activo")
            self.lbl_cd.config(fg=TEXT_DIM, text="--:--")
            self.lbl_badge.config(text="FUERA DE HORARIO", fg=ACCENT2)
            self._update_tray()
            self._job = self.after(1000, self._tick)
            return

        color: str = self._countdown_color()
        self.lbl_cd.config(fg=color, text=self._fmt_time(self.remaining))
        self.lbl_st.config(text="Trabajando...")
        self.lbl_badge.config(text="ACTIVO", fg=GREEN)
        total: int = self._total_sec if self._total_sec else 1
        self.pb["value"] = (self.remaining / total) * 100
        if self.remaining % 30 == 0:
            self._update_tray()

        if self.remaining <= 0:
            if self.cfg.get("no_molestar", True) and self._is_fullscreen():
                self.lbl_st.config(text="Pausa pospuesta (pantalla completa detectada)")
                self.lbl_badge.config(text="NO MOLESTAR", fg=YELLOW)
                self._total_sec = 5 * 60
                self.remaining = self._total_sec
            else:
                self._trigger_pausa()
        else:
            self.remaining -= 1

        self._job = self.after(1000, self._tick)

    @staticmethod
    def _is_weekend() -> bool:
        return datetime.now().weekday() >= 5

    @staticmethod
    def _is_fullscreen() -> bool:
        import ctypes
        try:
            QUNS_RUNNING_D3D_FULL_SCREEN = 5
            QUNS_PRESENTATION_MODE = 4
            state = ctypes.c_int(0)
            ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(state))
            return state.value in (QUNS_RUNNING_D3D_FULL_SCREEN, QUNS_PRESENTATION_MODE)
        except Exception:
            return False

    def _trigger_pausa(self) -> None:
        if self.pausa_open:
            return
        self.pausa_open = True
        log.info("Pausa activada, ejercicio=%s", self._last_ej or "aleatorio")
        self._show()
        if self.cfg.get("sonido", True):
            threading.Thread(target=audio_manager.play_alert, daemon=True).start()
        self.after(0, lambda: send_win_notification(
            "Pausa Activa",
            "Es hora de moverte un poco!",
            sound=self.cfg.get("notificacion_sonido", "default"),
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

    def _done_pausa(self) -> None:
        self.pausa_open = False
        interval: int = self._get_interval()
        self._total_sec = interval * 60
        self.remaining = self._total_sec
        self.stats["completadas"] += 1
        now = datetime.now()
        self.stats["historial"].append({
            "hora": now.strftime("%H:%M"),
            "ejercicio": self._last_ej,
            "estado": "completada",
        })
        meta: int = self.cfg["meta_pausas"]
        if self.stats["completadas"] == meta:
            self.stats["meta_cumplida"] = True
            self.after(0, lambda: send_win_notification(
                "Meta cumplida!",
                f"Completaste {meta} pausas hoy. Excelente habito!",
            ))
        self._cfg_mgr.save_stats(self.stats)
        self._update_stats_label()
        self._cfg_mgr.append_csv([
            now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            self._last_ej, "completada",
        ])
        self.lbl_st.config(text=random.choice(FRASES))
        self._update_tray()

    def _skip_pausa(self) -> None:
        self.pausa_open = False
        interval: int = self._get_interval()
        self._total_sec = interval * 60
        self.remaining = self._total_sec
        now = datetime.now()
        self.stats["saltadas"] += 1
        self.stats["historial"].append({
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
        self.lbl_st.config(text="Pausa saltada.")
        self._update_tray()

    def _toggle(self) -> None:
        self.running = not self.running
        if self.running:
            self.btn_p.config(text="Pausar", fg=TEXT)
            self.lbl_st.config(text="Trabajando...")
            self.lbl_badge.config(text="ACTIVO", fg=GREEN)
        else:
            self.btn_p.config(text="Reanudar", fg=GREEN)
            self.lbl_st.config(text="Timer pausado")
            self.lbl_badge.config(text="PAUSADO", fg=TEXT_DIM)
        self._update_tray()

    def _now(self) -> None:
        self.remaining = 0

    def _posponer(self) -> None:
        mins: int = self.cfg.get("posponer_min", 10)
        self._total_sec = mins * 60
        self.remaining = self._total_sec
        self.lbl_st.config(text=f"Pausa pospuesta {mins} min")

    def _open_config(self) -> None:
        def on_save(c: dict[str, Any]) -> None:
            self.cfg = c
            self._total_sec = c["intervalo_min"] * 60
            self.remaining = self._total_sec
            self._cfg_mgr.save_config(c)
            self._update_cfg_label()
            self._update_agua_label()
            self._water.restart()
            # Refrescar UI por si cambió el tema
            self.configure(bg=BG)
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
