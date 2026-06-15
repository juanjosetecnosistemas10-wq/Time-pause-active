"""Constantes del proyecto."""

from __future__ import annotations

import json
import logging
import os
import random
import ctypes
import ctypes.wintypes
from typing import Any


def center_window(win: Any) -> None:
    """Center window on the monitor containing the mouse pointer."""
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    if w < 100:
        w = 400
    if h < 100:
        h = 500
    try:
        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        pt = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        monitor = user32.MonitorFromPoint(pt, 0x00000002)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(monitor, ctypes.byref(info))
        mw = info.rcMonitor.right - info.rcMonitor.left
        mh = info.rcMonitor.bottom - info.rcMonitor.top
        x = info.rcMonitor.left + (mw - w) // 2
        y = info.rcMonitor.top + (mh - h) // 2
    except Exception:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
    win.geometry(f"+{x}+{y}")


APP_NAME: str = "FlowBreak"
APP_DISPLAY: str = "FlowBreak"
__version__: str = "2.0.3"
UPDATER_REPO: str = "juanjosetecnosistemas10-wq/Time-pause-active"


def darken_color(hex_color: str, amount: int = 30) -> str:
    """Darken a hex color by the given amount."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{max(0, r - amount):02x}{max(0, g - amount):02x}{max(0, b - amount):02x}"

INSTALL_DIR_REG: str = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FlowBreak"

# ── Temas ──────────────────────────────────────────────────────────────────

THEMES: dict[str, dict[str, Any]] = {
    "oscuro": {
        "BG": "#0A0E1A",
        "BG2": "#111827",
        "BG3": "#1F2937",
        "BG4": "#374151",
        "ACCENT": "#3B82F6",
        "ACCENT2": "#F43F5E",
        "ACCENT3": "#8B5CF6",
        "GREEN": "#10B981",
        "YELLOW": "#F59E0B",
        "TEXT": "#F9FAFB",
        "TEXT_DIM": "#9CA3AF",
        "TEXT_MUTED": "#6B7280",
        "BORDER": "#1E293B",
        "AGUA": "#06B6D4",
        "CARD": "#111827",
        "CARD_BORDER": "#1E293B",
        "SUCCESS_BG": "#064E3B",
        "WARNING_BG": "#422006",
        "ERROR_BG": "#450A0A",
        "TRAY_ACTIVE": (59, 130, 246),
        "TRAY_PAUSED": (156, 163, 175),
        "TRAY_OFF": (244, 63, 94),
        "GLOW": "#3B82F6",
        "SURFACE": "#0F172A",
    },
    "claro": {
        "BG": "#F8FAFC",
        "BG2": "#FFFFFF",
        "BG3": "#F1F5F9",
        "BG4": "#E2E8F0",
        "ACCENT": "#2563EB",
        "ACCENT2": "#E11D48",
        "ACCENT3": "#7C3AED",
        "GREEN": "#059669",
        "YELLOW": "#D97706",
        "TEXT": "#0F172A",
        "TEXT_DIM": "#64748B",
        "TEXT_MUTED": "#94A3B8",
        "BORDER": "#E2E8F0",
        "AGUA": "#0891B2",
        "CARD": "#FFFFFF",
        "CARD_BORDER": "#E2E8F0",
        "SUCCESS_BG": "#DCFCE7",
        "WARNING_BG": "#FEF3C7",
        "ERROR_BG": "#FEE2E2",
        "TRAY_ACTIVE": (37, 99, 235),
        "TRAY_PAUSED": (100, 116, 139),
        "TRAY_OFF": (225, 29, 72),
        "GLOW": "#2563EB",
        "SURFACE": "#FFFFFF",
    },
}

# ── Paletas de acento ──────────────────────────────────────────────────────

ACCENT_PALETTES: dict[str, dict[str, Any]] = {
    "azul":    {"ACCENT": "#3B82F6", "TRAY_ACTIVE": (59, 130, 246), "GLOW": "#3B82F6"},
    "verde":   {"ACCENT": "#10B981", "TRAY_ACTIVE": (16, 185, 129), "GLOW": "#10B981"},
    "morado":  {"ACCENT": "#8B5CF6", "TRAY_ACTIVE": (139, 92, 246), "GLOW": "#8B5CF6"},
    "rosa":    {"ACCENT": "#EC4899", "TRAY_ACTIVE": (236, 72, 153), "GLOW": "#EC4899"},
    "naranja": {"ACCENT": "#F97316", "TRAY_ACTIVE": (249, 115, 22), "GLOW": "#F97316"},
    "teal":    {"ACCENT": "#14B8A6", "TRAY_ACTIVE": (20, 184, 166), "GLOW": "#14B8A6"},
    "rojo":    {"ACCENT": "#EF4444", "TRAY_ACTIVE": (239, 68, 68), "GLOW": "#EF4444"},
}

# ── Paletas de fondo ───────────────────────────────────────────────────────

FONDO_PALETTES: dict[str, dict[str, str]] = {
    "estandar":   {},
    "profundo":   {"BG": "#030712", "BG2": "#0A0E1A", "BG3": "#1F2937", "CARD": "#111827",
                   "TEXT": "#F9FAFB", "TEXT_DIM": "#9CA3AF", "TEXT_MUTED": "#6B7280",
                   "SURFACE": "#0A0E1A"},
    "gris":       {"BG": "#111318", "BG2": "#1C1F26", "BG3": "#2D3139", "CARD": "#1C1F26",
                   "TEXT": "#F9FAFB", "TEXT_DIM": "#9CA3AF", "TEXT_MUTED": "#6B7280",
                   "SURFACE": "#111318"},
    "azulado":    {"BG": "#0B1120", "BG2": "#111827", "BG3": "#1E293B", "CARD": "#111827",
                   "TEXT": "#F9FAFB", "TEXT_DIM": "#9CA3AF", "TEXT_MUTED": "#6B7280",
                   "SURFACE": "#0B1120"},
    "blanco":     {"BG": "#FFFFFF", "BG2": "#F8FAFC", "BG3": "#F1F5F9", "CARD": "#FFFFFF",
                   "TEXT": "#0F172A", "TEXT_DIM": "#64748B", "TEXT_MUTED": "#94A3B8",
                   "SURFACE": "#FFFFFF"},
    "gris_suave": {"BG": "#F1F5F9", "BG2": "#FFFFFF", "BG3": "#E2E8F0", "CARD": "#FFFFFF",
                   "TEXT": "#0F172A", "TEXT_DIM": "#64748B", "TEXT_MUTED": "#94A3B8",
                   "SURFACE": "#F1F5F9"},
    "calido":     {"BG": "#FFFBEB", "BG2": "#FFFFFF", "BG3": "#FEF3C7", "CARD": "#FFFFFF",
                   "TEXT": "#0F172A", "TEXT_DIM": "#64748B", "TEXT_MUTED": "#94A3B8",
                   "SURFACE": "#FFFBEB"},
}

_tema_actual: str = "oscuro"


class _Colors:
    """Mutable color container — references stay valid when theme changes."""

    def load(self, nombre: str) -> None:
        t = THEMES.get(nombre, THEMES["oscuro"])
        for k, v in t.items():
            setattr(self, k, v)


C = _Colors()
C.load("oscuro")


def set_theme(nombre: str, acento: str = "azul", fondo: str = "estandar") -> None:
    global _tema_actual
    if nombre not in THEMES:
        return
    _tema_actual = nombre
    C.load(nombre)
    paleta = ACCENT_PALETTES.get(acento, ACCENT_PALETTES["azul"])
    for k, v in paleta.items():
        setattr(C, k, v)
    fondos = FONDO_PALETTES.get(fondo, {})
    for k, v in fondos.items():
        setattr(C, k, v)
    try:
        import customtkinter as ctk
        if nombre == "oscuro":
            ctk.set_appearance_mode("dark")
        elif nombre == "claro":
            ctk.set_appearance_mode("light")
        else:
            try:
                import darkdetect
                ctk.set_appearance_mode("dark" if darkdetect.theme() == "Dark" else "light")
            except (ImportError, Exception):
                ctk.set_appearance_mode("dark")
    except ImportError:
        pass


def get_theme() -> str:
    return _tema_actual


# ── Logging ────────────────────────────────────────────────────────────────

LOG_DIR: str = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
    APP_NAME,
    "logs",
)
os.makedirs(LOG_DIR, exist_ok=True)

_log_initialized: bool = False


def _ensure_logging() -> None:
    global _log_initialized
    if _log_initialized:
        return
    _log_initialized = True

    _file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, "flowbreak.log"),
        encoding="utf-8",
    )
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            _file_handler,
        ],
    )


log = logging.getLogger("FlowBreak")
_ensure_logging()

# ── Config por defecto ─────────────────────────────────────────────────────

# ── Font scaling ──────────────────────────────────────────────────────────

FONT_MULTIPLIERS: dict[str, float] = {
    "pequeno": 0.85,
    "normal": 1.0,
    "grande": 1.15,
    "muy_grande": 1.3,
}

_font_mult: float = 1.0


def set_font_size(key: str) -> None:
    global _font_mult
    _font_mult = FONT_MULTIPLIERS.get(key, 1.0)


def F(size: int, weight: str = "") -> tuple:
    """Return a Segoe UI font tuple scaled by the current multiplier."""
    scaled = max(1, int(size * _font_mult))
    if weight:
        return ("Segoe UI", scaled, weight)
    return ("Segoe UI", scaled)


DEFAULT_CONFIG: dict[str, Any] = {
    "intervalo_min": 45,
    "duracion_pausa_min": 5,
    "hora_inicio": "08:00",
    "hora_fin": "18:00",
    "ejercicios_activos": [],
    "sonido": True,
    "posponer_min": 10,
    "autoarranque": False,
    "meta_pausas": 6,
    "no_molestar": True,
    "agua_activo": True,
    "agua_min": 30,
    "fin_de_semana": False,
    "sonido_ambiente": "ninguno",
    "primera_vez": True,
    "tema": "oscuro",
    "modo": "normal",
    "perfil": "default",
    "idioma": "es",
    "notificacion_sonido": "default",
    "notificacion_duracion": "short",
    "tamano_letra": "normal",
    "color_acento": "azul",
    "fondo": "estandar",
    "hotkeys_enabled": True,
    "pantalla_completa": False,
    "guia_voz": True,
    "tts_activo": False,
    "sonidos_personalizados": False,
    # ── Nuevas features ──
    "postura_recordatorio": False,
    "postura_intervalo_min": 20,
    "pomodoro_trabajo_min": 25,
    "pomodoro_descanso_corto_min": 5,
    "pomodoro_descanso_largo_min": 15,
    "pomodoro_rondas_largas": 4,
    "compacto_enabled": False,
    "floating_enabled": False,
    "floating_opacity": 85,
    "workouts": [],
    "workout_ultimo": None,
    "logros_mostrados": [],
    "hotkey_siguiente": "ctrl+right",
    "hotkey_anterior": "ctrl+left",
    "hotkey_pausar": "ctrl+space",
    "hotkey_saltar": "ctrl+escape",
    "color_personalizado_primary": "",
    "color_personalizado_accent": "",
    "sound_packs": ["default"],
    "sound_pack_activo": "default",
    "tutorial_paso": 0,
    "tutorial_completado": False,
    "fullscreen_tema": "oscuro",
}

# ── Ejercicios ─────────────────────────────────────────────────────────────

EJERCICIOS_BUILTIN: list[dict[str, Any]] = [
    {"id": "cuello",  "nombre": "Estiramiento de cuello",  "icono": "🧘", "instrucciones": "Libera la tensión del cuello y hombros acumulada por la pantalla.", "pasos": ["Inclina la cabeza a la derecha llevando la oreja al hombro 15 seg", "Inclina la cabeza a la izquierda llevando la oreja al hombro 15 seg", "Gira el cuello suavemente a la derecha y a la izquierda 5 veces cada lado"]},
    {"id": "hombros", "nombre": "Estiramiento de hombros", "icono": "💪", "instrucciones": "Afloja los hombros rígidos por la mala postura frente al ordenador.", "pasos": ["Sube los hombros hasta las orejas aguantando 3 seg y suelta 10 veces", "Rota los hombros hacia atrás en círculos amplios 10 veces", "Rota los hombros hacia adelante en círculos amplios 10 veces"]},
    {"id": "espalda", "nombre": "Estiramiento de espalda", "icono": "🏃", "instrucciones": "Estira la espalda para contrarrestar horas de estar sentado.", "pasos": ["Entrelaza las manos y estíralas hacia arriba con palmas al techo 15 seg", "Inclínate hacia adelante desde la cadera tocando los pies 15 seg", "Gira el tronco a la derecha y a la izquierda con manos en la cadera 5 veces"]},
    {"id": "visual",  "nombre": "Descanso visual",         "icono": "👁️", "instrucciones": "Descansa tus ojos del brillo de la pantalla. Sigue la regla 20-20-20.", "pasos": ["Mira un objeto lejano a 6+ metros por 20 segundos", "Cierra los ojos y cúbrelos con las palmas sin presionar 15 seg", "Parpadea rápidamente 10 veces y haz círculos con los ojos 5 por lado"]},
    {"id": "manos",   "nombre": "Ejercicio de manos y muñecas", "icono": "✋", "instrucciones": "Previene lesiones por escritura y uso del ratón.", "pasos": ["Extiende el brazo con palma arriba y empuja los dedos hacia abajo 12 seg cada mano", "Abre y cierra los puños extendiendo bien los dedos 10 veces", "Gira las muñecas en círculos 5 veces por lado"]},
    {"id": "sentad",  "nombre": "Sentadillas y piernas",     "icono": "🏋️", "instrucciones": "Activa piernas y glúteos para mejorar la circulación.", "pasos": ["Levántate de la silla y baja en sentadilla hasta 90° con espalda recta 8 veces", "Eleva talones quedándote de puntillas 15 veces", "Eleva rodillas alternando como marchando en el sitio 20 veces"]},
    {"id": "respira", "nombre": "Respiración profunda",      "icono": "🌬️", "instrucciones": "Oxigena tu cuerpo y relaja la mente con respiración consciente.", "pasos": ["Inhala profundamente por la nariz contando 4 seg", "Retén el aire contando 4 seg", "Exhala lentamente por la boca contando 6 seg. Repite 5 veces"]},
    {"id": "caminar", "nombre": "Caminata activa en el sitio", "icono": "🚶", "instrucciones": "Activa la circulación caminando sin moverte del sitio.", "pasos": ["Marcha levantando las rodillas a la altura de la cadera 30 seg", "Balancea los brazos coordinados al caminar 30 seg", "Haz talones a los glúteos alternando piernas 30 seg"]},
    {"id": "postura", "nombre": "Corrección de postura",     "icono": "🧍", "instrucciones": "Corrige la postura encorvada y fortalece la espalda alta.", "pasos": ["Párate derecho llevando hombros atrás y abajo, pecho abierto 15 seg", "Lleva los brazos en forma de W apretando omóplatos 12 veces", "Mantén la postura correcta respirando profundo 20 seg"]},
    {"id": "cadera",  "nombre": "Movilidad de cadera",       "icono": "🔄", "instrucciones": "Afloja las caderas y la zona lumbar tras estar sentado.", "pasos": ["De pie, apoya manos en caderas y haz círculos amplios a la derecha 20 seg", "Repite círculos hacia la izquierda 20 seg", "Empuja la cadera adelante y atrás balanceando 10 veces"]},
    {"id": "tobillos","nombre": "Movilidad de tobillos",     "icono": "🦶", "instrucciones": "Mejora la circulación de piernas y previene pies hinchados.", "pasos": ["Eleva un pie y rota el tobillo en círculos derecha 15 seg", "Rota el mismo tobillo a la izquierda 15 seg", "Cambia de pie y repite rotaciones 30 seg total"]},
    {"id": "yoga",    "nombre": "Estiramiento de yoga silla", "icono": "🧎", "instrucciones": "Estira la espalda y relaja la mente con esta postura.", "pasos": ["Siéntate erguido al borde de la silla, estira brazos arriba 15 seg", "Inclínate hacia adelante dejando caer brazos y cabeza 15 seg", "Gira el tronco hacia la derecha y agarra el respaldo 10 seg cada lado"]},
]

EJERCICIOS: list[dict[str, Any]] = list(EJERCICIOS_BUILTIN)


def load_ejercicios_from_file(filepath: str) -> list[dict[str, Any]]:
    if os.path.exists(filepath):
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Error loading ejercicios from %s: %s", filepath, e)
    return list(EJERCICIOS_BUILTIN)


# ── Notas de bienestar ──────────────────────────────────────────────────────

WELLNESS_NOTES: list[dict[str, str]] = [
    {"icon": "🧘", "title": "Respira profundo", "msg": "Inhala 4 seg, sostén 4 seg, exhala 6 seg. Repite 3 veces."},
    {"icon": "💧", "title": "Hidrátate", "msg": "Tómate un vaso de agua. Tu cuerpo te lo agradecerá."},
    {"icon": "👀", "title": "Descansa la vista", "msg": "Mira algo lejano a 6 metros por 20 segundos."},
    {"icon": "🧍", "title": "Corrige tu postura", "msg": "Espalda recta, hombros relajados, pies en el suelo."},
    {"icon": "🌞", "title": "Busca luz natural", Si buscas una ventana. La luz natural mejora tu ánimo."},
    {"icon": "🧠", "title": "Limpia tu mente", "msg": "Cierra los ojos 30 segundos y piensa en algo que te haga feliz."},
    {"icon": "💪", "title": "Estira tu cuerpo", "msg": "Estira los brazos arriba y mantén 10 segundos."},
    {"icon": "😊", "title": "Sonríe", "msg": "Una sonrisa libera endorfinas. ¡Hazlo ahora!"},
    {"icon": "🪑", "title": "Levántate", "msg": "Si llevas más de 30 min sentado, párate y camina un momento."},
    {"icon": "🎶", "title": "Escucha música", "msg": "Pon una canción que te guste y disfruta el momento."},
    {"icon": "🌿", "title": "Conecta con la naturaleza", "msg": "Mira por la ventana o sal un momento al exterior."},
    {"icon": "🫁", "title": "Oxigena tu cerebro", "msg": "5 respiraciones profundas aumentan tu concentración."},
    {"icon": " massag", "title": "Relaja el cuello", "msg": "Inclina la cabeza suavemente a cada lado, 10 seg por lado."},
    {"icon": "☕", "title": "Pausa consciente", "msg": "Si tomas café, disfrútalo sin mirar la pantalla."},
    {"icon": "🙏", "title": "Agradece", "msg": "Piensa en 3 cosas buenas que te pasaron hoy."},
    {"icon": "💪", "title": "Activa piernas", "msg": "Haz 10 sentadillas suaves para activar la circulación."},
    {"icon": "🎵", "title": "Canta", "msg": "Canta tu canción favorita. Libera tensión y mejora el ánimo."},
    {"icon": "🤗", "title": "Abrázate", "msg": "Un abrazo a ti mismo reduce el estrés. Hazlo ahora."},
    {"icon": "🌺", "title": "Aromaterapia", "msg": "Si tienes aceite esencial, aplícalo en las muñecas."},
    {"icon": "😴", "title": "Poder del sueño", "msg": "Dormir 7-8 horas mejora tu productividad un 30%."},
]


# ── i18n ───────────────────────────────────────────────────────────────────

I18N: dict[str, dict[str, Any]] = {
    "es": {
        # Identidad
        "app_name": "FlowBreak",
        "flowbreak": "FlowBreak",
        "pausa_activa": "PAUSA ACTIVA",
        # Temporizador
        "break_now": "Pausa ya",
        "pausa_ya": "Pausa ya",
        "reanudar": "Reanudar",
        "snooze": "Posponer",
        "posponer": "Posponer",
        "minimize_tray": "Minimizar a bandeja",
        "minimizar": "Minimizar a bandeja",
        "saltar_pausa": "Saltar pausa",
        "tiempo_restante": "tiempo restante",
        "preparate": "Prepárate",
        "trabajando": "Trabajando...",
        "pausado": "Timer pausado",
        "pausa_saltada": "Pausa saltada.",
        "btn_pausar": "⏸ Pausar",
        "btn_reanudar": "▶ Reanudar",
        "pausa_pospuesta": "Pausa pospuesta {mins} min",
        "prox_pausa": "Próxima pausa en {t}",
        # Tray menu
        "abrir": "Abrir",
        "pausa_ya_tray": "Pausa ya",
        "posponer_tray": "Posponer",
        "pausar_tray": "Pausar/Reanudar",
        "buscar_actualizaciones": "Buscar actualizaciones",
        "salir": "Salir",
        # Hotkeys
        "hotkey_break_now": "Pausa ya (Ctrl+Alt+B)",
        "hotkey_snooze": "Posponer (Ctrl+Alt+S)",
        "hotkey_pause_resume": "Pausar/Reanudar (Ctrl+Alt+P)",
        "hotkey_show_hide": "Mostrar/Ocultar (Ctrl+Alt+H)",
        "hotkey_quit": "Salir (Ctrl+Alt+Q)",
        "section_hotkeys": "Atajos globales",
        "hotkeys_enabled": "Activar atajos globales",
        # Badges
        "badge_activo": "ACTIVO",
        "badge_pausado": "PAUSADO",
        "badge_fin_semana": "FIN DE SEMANA",
        "badge_fuera_horario": "FUERA DE HORARIO",
        "badge_no_molestar": "NO MOLESTAR",
        "pospuesto_fullscreen": "Pausa pospuesta (pantalla completa detectada)",
        # Configuración
        "settings": "Configuración",
        "configuracion": "Configuración",
        "save": "Guardar",
        "guardar": "Guardar",
        "cancel": "Cancelar",
        "cancelar": "Cancelar",
        # Installer
        "install_title": "Instalar FlowBreak",
        "install_desc": "Configura la instalación y haz clic en Instalar.",
        "install_folder_label": "Carpeta de instalación:",
        "install_options_label": "Opciones:",
        "install_opt_desktop": "  Crear acceso directo en el Escritorio",
        "install_opt_start": "  Agregar al Menú Inicio",
        "install_opt_autostart": "  Iniciar automáticamente con Windows",
        "install_err_empty": "La carpeta de instalación no puede estar vacía.",
        "install_err_traversal": "La carpeta de instalación no puede contener '..'.",
        "install_err_chars": "La carpeta de instalación contiene caracteres no válidos.",
        "install_err_no_dir": "Indica una carpeta de instalación.",
        "install_cancel_title": "Cancelar instalación",
        "install_cancel_msg": "¿Seguro que deseas cancelar?\nLa app se cerrará.",
        "install_progress_dir": "Creando carpeta de instalación...",
        "install_progress_files": "Copiando archivos...",
        "install_progress_desktop": "Creando acceso directo en el escritorio...",
        "install_progress_start": "Agregando al Menú Inicio...",
        "install_progress_autostart": "Configurando autoarranque...",
        "install_progress_register": "Registrando en el sistema...",
        "install_progress_done": "¡Instalación completa!",
        "install_ok_title": "¡Listo!",
        "install_ok_msg": "FlowBreak se instaló en:\n{dir}",
        "install_perm_error_title": "Error de permisos",
        "install_perm_error_msg": "No se pudo escribir en:\n{dir}\n\nIntenta ejecutar como Administrador.",
        "instalar": "Instalar",
        "uninstall": "Desinstalar",
        "desinstalar": "Desinstalar",
        # Estadísticas
        "statistics": "Estadísticas",
        "estadisticas": "Estadísticas de hoy",
        "weekly_chart": "Últimos 7 días",
        "export_csv": "Exportar CSV",
        "exportar_csv": "Exportar CSV",
        "close": "Cerrar",
        "cerrar": "Cerrar",
        # Metas / notificaciones
        "goal_achieved": "¡Meta cumplida!",
        "meta_cumplida": "¡Meta cumplida!",
        "water_reminder": "¡Recuerda tomar agua!",
        "agua_recordatorio": "¡Recuerda tomar agua!",
        "agua_recordatorio_every": "💧 Recordatorio de agua cada {min} min",
        "drink_water_body": "¡Recuerda tomar agua!",
        "outside_hours": "Fuera del horario activo",
        "fuera_horario": "Fuera del horario activo",
        "weekend": "Fin de semana — descansando",
        "fin_semana": "Fin de semana — descansando",
        "no_disturb": "No interrumpir si hay pantalla completa",
        "no_molestar": "No interrumpir si hay pantalla completa",
        "weekend_pause": "Pausar en fin de semana",
        "fin_de_semana_opt": "Pausar en fin de semana (sab y dom)",
        "sound_alert": "Activar sonido de alerta",
        "sonido_alerta": "Activar sonido de alerta al iniciar pausa",
        "autostart": "Iniciar con Windows",
        "autoarranque": "Iniciar con Windows (autoarranque)",
        "no_sound": "Sin sonido",
        "sin_sonido": "Sin sonido",
        "rain": "Lluvia",
        "lluvia": "Lluvia",
        "nature": "Naturaleza",
        "naturaleza": "Naturaleza",
        # Tabs
        "tab_timer": "⏱ Temporizador",
        "config_temporizador": "⏱ Temporizador",
        "tab_options": "⚙ Opciones",
        "config_opciones": "⚙ Opciones",
        "tab_sound": "🔊 Sonido",
        "config_sonido": "🔊 Sonido",
        "tab_exercises": "🏃 Ejercicios",
        "config_ejercicios": "🏃 Ejercicios",
        # Modos
        "mode_normal": "Normal",
        "modo_normal": "Normal",
        "mode_pomodoro": "Pomodoro",
        "modo_pomodoro": "Pomodoro",
        "modo_personalizado": "Personalizado",
        # Idioma / tema
        "language": "Idioma",
        "theme": "Tema",
        "dark": "Oscuro",
        "light": "Claro",
        # Varios
        "profile": "Perfil",
        "about": "Acerca de",
        "bienvenido": "¡Bienvenido a FlowBreak!",
        # ConfigWindow fields
        "field_intervalo": "Intervalo entre pausas (min)",
        "field_duracion_pausa": "Duración de la pausa (min)",
        "field_hora_inicio": "Hora inicio (HH:MM)",
        "field_hora_fin": "Hora fin (HH:MM)",
        "field_posponer": "Minutos para posponer",
        "field_meta_pausas": "Meta de pausas diarias",
        "modo_timer": "Modo de timer",
        "pomodoro_desc": "Pomodoro: 25 min trabajo / 5 min pausa",
        "section_no_molestar": "No molestar",
        "section_agua": "Recordatorio de agua",
        "chk_activar_agua": "Activar recordatorio de hidratación",
        "field_agua_intervalo": "Cada cuantos minutos:",
        "section_general": "General",
        "section_perfiles": "Perfiles",
        "section_idioma": "Idioma",
        "idioma_es": "Español",
        "idioma_en": "English",
        "section_sonido_ambiente": "Sonido ambiente durante la pausa",
        "sonido_critica": "Crítica",
        "section_notificaciones": "Notificaciones",
        "field_sonido_tipo": "Sonido:",
        "field_duracion": "Duración:",
        "dur_corta": "Corta",
        "dur_larga": "Larga",
        "section_ejercicios": "Marca los ejercicios que quieres incluir:",
        "theme_oscuro": "Oscuro",
        "theme_claro": "Claro",
        "section_accent_color": "Color de acento",
        "accent_azul": "Azul",
        "accent_verde": "Verde",
        "accent_morado": "Púrpura",
        "accent_rosa": "Rosa",
        "accent_naranja": "Naranja",
        "accent_teal": "Teal",
        "accent_rojo": "Rojo",
        "section_fondo": "Fondo",
        "fondo_estandar": "Estándar",
        "fondo_profundo": "Profundo",
        "fondo_gris": "Gris",
        "fondo_azulado": "Azulado",
        "fondo_blanco": "Blanco",
        "fondo_gris_suave": "Gris suave",
        "fondo_calido": "Cálido",
        # StatsWindow
        "stats_completadas": "Pausas completadas",
        "stats_saltadas": "Pausas saltadas",
        "stats_tasa_exito": "Tasa de éxito",
        "stats_racha": "Racha actual",
        "stats_meta_diaria": "Meta diaria",
        "stats_cumplida": "CUMPLIDA",
        "stats_en_progreso": "En progreso",
        "ultimos_7_dias": "Últimos 7 días",
        "ultimas_pausas": "Últimas pausas",
        # Welcome window
        "welcome_title": "Bienvenido a FlowBreak",
        "welcome_heading": "👋  Bienvenido",
        "welcome_card1_title": "Recordatorios automáticos",
        "welcome_card1_desc": "Te avisa cada cierto tiempo para que hagas una pausa activa.",
        "welcome_card2_title": "Ejercicios guiados",
        "welcome_card2_desc": "Cuello, espalda, ojos, respiración y más.",
        "welcome_card3_title": "Hidratación",
        "welcome_card3_desc": "Recordatorios para que tomes agua regularmente.",
        "welcome_card4_title": "Estadísticas",
        "welcome_card4_desc": "Lleva el registro de tus pausas y rachas diarias.",
        "welcome_step1_heading": "⚙️  Configura tu rutina",
        "welcome_step1_info": "Puedes cambiar esto después en Configuración",
        "welcome_field_intervalo": "Intervalo entre pausas (min)",
        "welcome_field_duracion": "Duración de la pausa (min)",
        "welcome_field_hora_ini": "Hora inicio (HH:MM)",
        "welcome_field_hora_fin": "Hora fin (HH:MM)",
        "welcome_field_meta": "Meta de pausas diarias",
        "welcome_ej_subheading": "Ejercicios a incluir:",
        "next_step": "Siguiente →",
        "back_step": "← Atrás",
        "welcome_step2_heading": "🎉  ¡Todo listo!",
        "welcome_step2_info": "La app ya está configurada y lista para cuidarte.",
        "welcome_summary_intervalo": "Intervalo",
        "welcome_summary_intervalo_val": "Cada {min} min",
        "welcome_summary_duracion": "Duración",
        "welcome_summary_duracion_val": "{min} min de pausa",
        "welcome_summary_horario": "Horario",
        "welcome_summary_meta": "Meta",
        "welcome_summary_meta_val": "{meta} pausas por día",
        "welcome_step2_tray_info": "La app se minimizará a la bandeja del sistema.",
        "to": "a",
        "welcome_start": "¡Empezar! 🚀",
        "err_hora_inicio": "Hora inicio inválida",
        # Error messages
        "err_valores_positivos": "Todos los valores deben ser positivos",
        "err_hora_invalida": "Hora inválida",
        "err_hora_fin": "Hora fin debe ser mayor que hora inicio",
        "err_hora_fin_mayor": "Hora fin debe ser mayor que hora inicio",
        "err_revisa_valores": "Revisa los valores ingresados",
        "err_selecciona_ej": "Selecciona al menos un ejercicio",
        "err_campo_intervalo": "Intervalo: debe ser un número entero",
        "err_campo_duracion": "Duración: debe ser un número entero",
        "err_campo_posponer": "Posponer: debe ser un número entero",
        "err_campo_meta": "Meta: debe ser un número entero",
        "err_campo_agua": "Agua (min): debe ser un número entero",
        "err_valor_positivo": "debe ser un valor positivo",
        "field_hora_inicio": "Hora inicio",
        "field_hora_fin": "Hora fin",
        "break_time_body": "Es hora de moverte un poco!",
        "descargando_update": "Descargando actualización...",
        "err_download": "No se pudo descargar la actualización",
        "err_update": "Error al actualizar.",
        "error": "Error",
        "buscando_updates": "Buscando actualizaciones...",
        "version_actual": "Ya tienes la última versión disponible.",
        "update_disponible": "Actualización disponible",
        "update_msg": "Versión {ver} disponible!\n\nVersión actual: {cur}\n\n¿Deseas descargar e instalar la actualización?",
        "no_disponible": "No disponible",
        "update_no_url": "No se encontró el instalador. Visita la página del proyecto.",
        "update_lista": "Actualización lista",
        "update_dev_msg": "La actualización se aplicará al ejecutar la versión empaquetada.",
        "update_notif_msg": "Versión {version} disponible! Haz clic para descargar.",
        "update_badge": "⬇",
        "meta_completada_msg": "Completaste {meta} pausas hoy. Excelente hábito!",
        "exportar": "Exportar",
        "exportar_stats": "Exportar estadísticas",
        "exportado_ok": "Datos exportados a:\n{path}",
        "exportado_error": "No se pudo exportar:\n{e}",
        "todos": "Todos",
        # Uninstall
        "uninstall_title": "Desinstalar FlowBreak",
        "uninstall_heading": "Desinstalar",
        "uninstall_warning": "Esta acción eliminará la configuración de la app y no puede deshacerse.",
        "uninstall_opt_auto": "Quitar del autoarranque de Windows",
        "uninstall_opt_datos": "Eliminar configuración, estadísticas e historial",
        "uninstall_opt_accesos": "Eliminar accesos directos (escritorio / menú Inicio)",
        "uninstall_opt_carpeta": "Eliminar carpeta de instalación y archivos",
        "uninstall_btn": "Desinstalar",
        "uninstall_confirm_title": "Confirmar desinstalación",
        "uninstall_confirm_msg": "¿Seguro que deseas desinstalar FlowBreak?\n\nLa aplicación se cerrará al terminar.",
        "uninstall_status_auto": "Quitando autoarranque...",
        "uninstall_status_datos": "Eliminando datos...",
        "uninstall_status_accesos": "Eliminando accesos directos...",
        "uninstall_warn_title": "Desinstalación con advertencias",
        "uninstall_warn_msg": "Se completó con algunos errores:\n\n",
        "uninstall_ok_title": "Desinstalación completa",
        "uninstall_ok_msg": "FlowBreak ha sido desinstalado correctamente.",
        # Tamaño de letra
        "section_font_size": "Tamaño de letra",
        "font_pequeno": "Pequeño",
        "font_normal": "Normal",
        "font_grande": "Grande",
        "font_muy_grande": "Muy grande",
        # BreakWindow immersive / summary
        "break_fullscreen": "Pantalla completa",
        "break_voice": "Guía por voz",
        "break_summary_title": "Pausa completada",
        "break_summary_ejercicio": "Ejercicio: {nombre}",
        "break_summary_tiempo": "Duración: {min} min",
        "break_summary_pasos": "Pasos realizados: {completos}/{total}",
        "break_summary_congrats": "¡Sigue así!",
        "comenzar": "Comenzar",
        "break_congrats_title": "¡Muy bien!",
        "break_congrats_desc": "Completaste tu pausa activa. Tu cuerpo te lo agradece.",
        # Frases motivacionales
        "frases": [
            "¡Excelente! Tu cuerpo te lo agradece.",
            "Cada pausa es una inversión en tu salud.",
            "¡Bien hecho! Sigue así.",
            "Tu productividad mejora con cada descanso.",
            "Eres constante. Eso marca la diferencia.",
            "Pequeños hábitos, grandes cambios.",
            "Tu espalda y tus ojos te lo agradecen.",
            "Pausa completada. Vuelves más fuerte.",
            "¡Meta del día cumplida! Gran trabajo.",
            "Descansar es parte del éxito.",
        ],
        # ── Nuevas features ──
        # Postura
        "postura_recordatorio": "Recordatorio de postura",
        "postura_intervalo": "Cada cuántos minutos (postura):",
        # Pomodoro
        "pomodoro_trabajo": "Trabajo (min)",
        "pomodoro_descanso_corto": "Descanso corto (min)",
        "pomodoro_descanso_largo": "Descanso largo (min)",
        "pomodoro_rondas": "Rondas antes de descanso largo",
        "pomodoro_sesion_trabajo": "Sesión de trabajo",
        "pomodoro_sesion_descanso": "Descanso",
        "pomodoro_sesion_largo": "Descanso largo",
        # Compacto
        "modo_compacto": "Modo compacto",
        "compacto_desc": "Mini ventana con timer y controles básicos",
        # Floating
        "floating_timer": "Timer flotante",
        "floating_desc": "Mini timer siempre visible en escritorio",
        "floating_opacidad": "Opacidad del timer flotante",
        # Workout
        "workout": "Rutina de ejercicio",
        "workouts": "Mis rutinas",
        "workout_crear": "Crear rutina",
        "workout_nombre": "Nombre de la rutina",
        "workout_agregar_ej": "Agregar ejercicio",
        "workout_orden": "Orden",
        "workout_guardar": "Guardar rutina",
        "workout_ejecutar": "Iniciar rutina",
        "workout_vacia": "No hay rutinas creadas",
        # Logros
        "logros": "Logros",
        "logro_primera_pausa": "Primera pausa completada",
        "logro_5_pausas": "5 pausas en un día",
        "logro_10_pausas": "10 pausas en un día",
        "logro_racha_3": "Racha de 3 días",
        "logro_racha_7": "Racha de 1 semana",
        "logro_racha_30": "Racha de 1 mes",
        "logro_todos_ejercicios": "Todos los ejercicios completados",
        "logro_early_bird": "Pausa antes de las 9am",
        "logro_night_owl": "Pausa después de las 8pm",
        "logro_water_10": "10 recordatorios de agua",
        "logro_desbloqueado": "¡Logro desbloqueado!",
        # Exportar/Importar
        "exportar_stats": "Exportar estadísticas",
        "importar_stats": "Importar estadísticas",
        "exportar_ok": "Estadísticas exportadas a:\n{path}",
        "importar_ok": "Estadísticas importadas correctamente",
        "importar_error": "Error al importar: {error}",
        # Hotkeys personalizables
        "section_hotkeys_custom": "Atajos de teclado",
        "hotkey_siguiente": "Siguiente paso/ejercicio",
        "hotkey_anterior": "Paso/ejercicio anterior",
        "hotkey_pausar": "Pausar/reanudar timer",
        "hotkey_saltar": "Saltar pausa",
        # Sonido
        "sound_packs": "Paquetes de sonido",
        "sound_pack_default": "Por defecto",
        "sound_pack_nature": "Naturaleza",
        "sound_pack_minimal": "Minimalista",
        "sound_pack_activo": "Paquete activo",
        # Tutorial
        "tutorial_paso1_titulo": "Paso 1: Configura tus pausas",
        "tutorial_paso1_desc": "Establece cada cuánto tiempo quieres hacer una pausa activa.",
        "tutorial_paso2_titulo": "Paso 2: Elige ejercicios",
        "tutorial_paso2_desc": "Selecciona los ejercicios que más te gusten.",
        "tutorial_paso3_titulo": "Paso 3: Personaliza",
        "tutorial_paso3_desc": "Cambia colores, sonidos y otros ajustes.",
        "tutorial_saltar": "Saltar tutorial",
        "tutorial_completar": "¡Entendido!",
        # Fullscreen
        "fullscreen_timer": "Modo pantalla completa",
        "fullscreen_desc": "Timer grande a pantalla completa para presentaciones",
        "fullscreen_salir": "Salir de pantalla completa (Esc)",
        # Toast
        "toast_info": "Información",
        "toast_exito": "Éxito",
        "toast_advertencia": "Advertencia",
    },
    "en": {
        # Identity
        "app_name": "FlowBreak",
        "flowbreak": "FlowBreak",
        "pausa_activa": "ACTIVE BREAK",
        # Timer
        "break_now": "Break now",
        "pausa_ya": "Break now",
        "reanudar": "Resume",
        "snooze": "Snooze",
        "posponer": "Snooze",
        "minimize_tray": "Minimize to tray",
        "minimizar": "Minimize to tray",
        "saltar_pausa": "Skip break",
        "tiempo_restante": "time remaining",
        "preparate": "Get ready",
        "trabajando": "Working...",
        "pausado": "Timer paused",
        "pausa_saltada": "Break skipped.",
        "btn_pausar": "⏸ Pause",
        "btn_reanudar": "▶ Resume",
        "pausa_pospuesta": "Break snoozed {mins} min",
        "prox_pausa": "Next break in {t}",
        # Tray menu
        "abrir": "Open",
        "pausa_ya_tray": "Break now",
        "posponer_tray": "Snooze",
        "pausar_tray": "Pause/Resume",
        "buscar_actualizaciones": "Check for updates",
        "salir": "Exit",
        # Hotkeys
        "hotkey_break_now": "Break now (Ctrl+Alt+B)",
        "hotkey_snooze": "Snooze (Ctrl+Alt+S)",
        "hotkey_pause_resume": "Pause/Resume (Ctrl+Alt+P)",
        "hotkey_show_hide": "Show/Hide (Ctrl+Alt+H)",
        "hotkey_quit": "Exit (Ctrl+Alt+Q)",
        "section_hotkeys": "Global Hotkeys",
        "hotkeys_enabled": "Enable global hotkeys",
        # Badges
        "badge_activo": "ACTIVE",
        "badge_pausado": "PAUSED",
        "badge_fin_semana": "WEEKEND",
        "badge_fuera_horario": "OUTSIDE HOURS",
        "badge_no_molestar": "DO NOT DISTURB",
        "pospuesto_fullscreen": "Break postponed (fullscreen detected)",
        # Settings
        "settings": "Settings",
        "configuracion": "Settings",
        "save": "Save",
        "guardar": "Save",
        "cancel": "Cancel",
        "cancelar": "Cancel",
        "install": "Install",
        "instalar": "Install",
        "uninstall": "Uninstall",
        "desinstalar": "Uninstall",
        # Installer
        "install": "Install",
        "install_title": "Install FlowBreak",
        "install_desc": "Configure the installation and click Install.",
        "install_folder_label": "Installation folder:",
        "install_options_label": "Options:",
        "install_opt_desktop": "  Create Desktop shortcut",
        "install_opt_start": "  Add to Start Menu",
        "install_opt_autostart": "  Start automatically with Windows",
        "install_err_empty": "Installation folder cannot be empty.",
        "install_err_traversal": "Installation folder cannot contain '..'.",
        "install_err_chars": "Installation folder contains invalid characters.",
        "install_err_no_dir": "Specify an installation folder.",
        "install_cancel_title": "Cancel installation",
        "install_cancel_msg": "Are you sure you want to cancel?\nThe app will close.",
        "install_progress_dir": "Creating installation folder...",
        "install_progress_files": "Copying files...",
        "install_progress_desktop": "Creating desktop shortcut...",
        "install_progress_start": "Adding to Start Menu...",
        "install_progress_autostart": "Configuring autostart...",
        "install_progress_register": "Registering in the system...",
        "install_progress_done": "Installation complete!",
        "install_ok_title": "Done!",
        "install_ok_msg": "FlowBreak installed in:\n{dir}",
        "install_perm_error_title": "Permission error",
        "install_perm_error_msg": "Could not write to:\n{dir}\n\nTry running as Administrator.",
        # Statistics
        "statistics": "Statistics",
        "estadisticas": "Today's statistics",
        "weekly_chart": "Last 7 days",
        "export_csv": "Export CSV",
        "exportar_csv": "Export CSV",
        "close": "Close",
        "cerrar": "Close",
        # Goals / notifications
        "goal_achieved": "Goal achieved!",
        "meta_cumplida": "Goal achieved!",
        "water_reminder": "Remember to drink water!",
        "agua_recordatorio": "Remember to drink water!",
        "agua_recordatorio_every": "💧 Water reminder every {min} min",
        "drink_water_body": "Time to hydrate! Drink some water.",
        "outside_hours": "Outside active hours",
        "fuera_horario": "Outside active hours",
        "weekend": "Weekend — resting",
        "fin_semana": "Weekend — resting",
        "no_disturb": "Don't interrupt if fullscreen",
        "no_molestar": "Don't interrupt if fullscreen",
        "weekend_pause": "Pause on weekends",
        "fin_de_semana_opt": "Pause on weekends (sat & sun)",
        "sound_alert": "Enable alert sound",
        "sonido_alerta": "Enable alert sound on break start",
        "autostart": "Start with Windows",
        "autoarranque": "Start with Windows",
        "no_sound": "No sound",
        "sin_sonido": "No sound",
        "rain": "Rain",
        "lluvia": "Rain",
        "nature": "Nature",
        "naturaleza": "Nature",
        # Tabs
        "tab_timer": "⏱ Timer",
        "config_temporizador": "⏱ Timer",
        "tab_options": "⚙ Options",
        "config_opciones": "⚙ Options",
        "tab_sound": "🔊 Sound",
        "config_sonido": "🔊 Sound",
        "tab_exercises": "🏃 Exercises",
        "config_ejercicios": "🏃 Exercises",
        # Modes
        "mode_normal": "Normal",
        "modo_normal": "Normal",
        "mode_pomodoro": "Pomodoro",
        "modo_pomodoro": "Pomodoro",
        "modo_personalizado": "Custom",
        # Language / theme
        "language": "Language",
        "theme": "Theme",
        "dark": "Dark",
        "light": "Light",
        # Misc
        "profile": "Profile",
        "about": "About",
        "bienvenido": "Welcome to FlowBreak!",
        # ConfigWindow fields
        "field_intervalo": "Interval between breaks (min)",
        "field_duracion_pausa": "Break duration (min)",
        "field_hora_inicio": "Start time (HH:MM)",
        "field_hora_fin": "End time (HH:MM)",
        "field_posponer": "Snooze minutes",
        "field_meta_pausas": "Daily break goal",
        "modo_timer": "Timer mode",
        "pomodoro_desc": "Pomodoro: 25 min work / 5 min break",
        "section_no_molestar": "Do not disturb",
        "section_agua": "Water reminder",
        "chk_activar_agua": "Activate hydration reminder",
        "field_agua_intervalo": "Every how many minutes:",
        "section_general": "General",
        "section_perfiles": "Profiles",
        "section_idioma": "Language",
        "idioma_es": "Spanish",
        "idioma_en": "English",
        "section_sonido_ambiente": "Ambient sound during break",
        "sonido_critica": "Critical",
        "section_notificaciones": "Notifications",
        "field_sonido_tipo": "Sound:",
        "field_duracion": "Duration:",
        "dur_corta": "Short",
        "dur_larga": "Long",
        "section_ejercicios": "Select exercises to include:",
        "theme_oscuro": "Dark",
        "theme_claro": "Light",
        "section_accent_color": "Accent color",
        "accent_azul": "Blue",
        "accent_verde": "Green",
        "accent_morado": "Purple",
        "accent_rosa": "Pink",
        "accent_naranja": "Orange",
        "accent_teal": "Teal",
        "accent_rojo": "Red",
        "section_fondo": "Background",
        "fondo_estandar": "Standard",
        "fondo_profundo": "Deep",
        "fondo_gris": "Gray",
        "fondo_azulado": "Blueish",
        "fondo_blanco": "White",
        "fondo_gris_suave": "Soft gray",
        "fondo_calido": "Warm",
        # StatsWindow
        "stats_completadas": "Completed breaks",
        "stats_saltadas": "Skipped breaks",
        "stats_tasa_exito": "Success rate",
        "stats_racha": "Current streak",
        "stats_meta_diaria": "Daily goal",
        "stats_cumplida": "ACHIEVED",
        "stats_en_progreso": "In progress",
        "ultimos_7_dias": "Last 7 days",
        "ultimas_pausas": "Recent breaks",
        # Welcome window
        "welcome_title": "Welcome to FlowBreak",
        "welcome_heading": "👋  Welcome",
        "welcome_card1_title": "Automatic reminders",
        "welcome_card1_desc": "Reminds you periodically to take an active break.",
        "welcome_card2_title": "Guided exercises",
        "welcome_card2_desc": "Neck, back, eyes, breathing and more.",
        "welcome_card3_title": "Hydration",
        "welcome_card3_desc": "Reminders to drink water regularly.",
        "welcome_card4_title": "Statistics",
        "welcome_card4_desc": "Track your breaks and daily streaks.",
        "welcome_step1_heading": "⚙️  Configure your routine",
        "welcome_step1_info": "You can change this later in Settings",
        "welcome_field_intervalo": "Interval between breaks (min)",
        "welcome_field_duracion": "Break duration (min)",
        "welcome_field_hora_ini": "Start time (HH:MM)",
        "welcome_field_hora_fin": "End time (HH:MM)",
        "welcome_field_meta": "Daily break goal",
        "welcome_ej_subheading": "Exercises to include:",
        "next_step": "Next →",
        "back_step": "← Back",
        "welcome_step2_heading": "🎉  All set!",
        "welcome_step2_info": "The app is configured and ready to take care of you.",
        "welcome_summary_intervalo": "Interval",
        "welcome_summary_intervalo_val": "Every {min} min",
        "welcome_summary_duracion": "Duration",
        "welcome_summary_duracion_val": "{min} min break",
        "welcome_summary_horario": "Schedule",
        "welcome_summary_meta": "Goal",
        "welcome_summary_meta_val": "{meta} breaks per day",
        "welcome_step2_tray_info": "The app will minimize to the system tray.",
        "to": "to",
        "welcome_start": "Let's start! 🚀",
        "err_hora_inicio": "Invalid start time",
        # Error messages
        "err_valores_positivos": "All values must be positive",
        "err_hora_invalida": "Invalid time",
        "err_hora_fin": "End time must be after start time",
        "err_hora_fin_mayor": "End time must be after start time",
        "err_revisa_valores": "Check the entered values",
        "err_selecciona_ej": "Select at least one exercise",
        "err_campo_intervalo": "Interval: must be a whole number",
        "err_campo_duracion": "Duration: must be a whole number",
        "err_campo_posponer": "Snooze: must be a whole number",
        "err_campo_meta": "Goal: must be a whole number",
        "err_campo_agua": "Water (min): must be a whole number",
        "err_valor_positivo": "must be a positive value",
        "field_hora_inicio": "Start time",
        "field_hora_fin": "End time",
        "break_time_body": "Time to move! Take a break.",
        "descargando_update": "Downloading update...",
        "err_download": "Could not download the update",
        "err_update": "Update error.",
        "error": "Error",
        "buscando_updates": "Checking for updates...",
        "version_actual": "You already have the latest version.",
        "update_disponible": "Update available",
        "update_msg": "Version {ver} available!\n\nCurrent version: {cur}\n\nDo you want to download and install the update?",
        "no_disponible": "Not available",
        "update_no_url": "Installer not found. Visit the project page.",
        "update_lista": "Update ready",
        "update_dev_msg": "The update will be applied when running the packaged version.",
        "update_notif_msg": "Version {version} available! Click to download.",
        "update_badge": "⬇",
        "meta_completada_msg": "You completed {meta} breaks today. Great habit!",
        "exportar": "Export",
        "exportar_stats": "Export statistics",
        "exportado_ok": "Data exported to:\n{path}",
        "exportado_error": "Could not export:\n{e}",
        "todos": "All files",
        # Uninstall
        "uninstall_title": "Uninstall FlowBreak",
        "uninstall_heading": "Uninstall",
        "uninstall_warning": "This will delete the app configuration and cannot be undone.",
        "uninstall_opt_auto": "Remove from Windows startup",
        "uninstall_opt_datos": "Delete configuration, statistics and history",
        "uninstall_opt_accesos": "Delete shortcuts (desktop / Start menu)",
        "uninstall_opt_carpeta": "Delete installation folder and files",
        "uninstall_btn": "Uninstall",
        "uninstall_confirm_title": "Confirm uninstall",
        "uninstall_confirm_msg": "Are you sure you want to uninstall FlowBreak?\n\nThe application will close upon finishing.",
        "uninstall_status_auto": "Removing autostart...",
        "uninstall_status_datos": "Deleting data...",
        "uninstall_status_accesos": "Deleting shortcuts...",
        "uninstall_warn_title": "Uninstall with warnings",
        "uninstall_warn_msg": "Completed with some errors:\n\n",
        "uninstall_ok_title": "Uninstall complete",
        "uninstall_ok_msg": "FlowBreak has been uninstalled successfully.",
        # Font size
        "section_font_size": "Font size",
        "font_pequeno": "Small",
        "font_normal": "Normal",
        "font_grande": "Large",
        "font_muy_grande": "Extra large",
        # BreakWindow immersive / summary
        "break_fullscreen": "Fullscreen break",
        "break_voice": "Voice guide",
        "break_summary_title": "Break completed",
        "break_summary_ejercicio": "Exercise: {nombre}",
        "break_summary_tiempo": "Duration: {min} min",
        "break_summary_pasos": "Steps done: {completos}/{total}",
        "break_summary_congrats": "Keep it up!",
        "comenzar": "Start",
        "break_congrats_title": "Great job!",
        "break_congrats_desc": "You completed your active break. Your body thanks you.",
        # ── New features ──
        # Posture
        "postura_recordatorio": "Posture reminder",
        "postura_intervalo": "Posture reminder interval (min):",
        # Pomodoro
        "pomodoro_trabajo": "Work (min)",
        "pomodoro_descanso_corto": "Short break (min)",
        "pomodoro_descanso_largo": "Long break (min)",
        "pomodoro_rondas": "Rounds before long break",
        "pomodoro_sesion_trabajo": "Work session",
        "pomodoro_sesion_descanso": "Break",
        "pomodoro_sesion_largo": "Long break",
        # Compact
        "modo_compacto": "Compact mode",
        "compacto_desc": "Mini window with timer and basic controls",
        # Floating
        "floating_timer": "Floating timer",
        "floating_desc": "Mini timer always visible on desktop",
        "floating_opacidad": "Floating timer opacity",
        # Workout
        "workout": "Workout",
        "workouts": "My workouts",
        "workout_crear": "Create workout",
        "workout_nombre": "Workout name",
        "workout_agregar_ej": "Add exercise",
        "workout_orden": "Order",
        "workout_guardar": "Save workout",
        "workout_ejecutar": "Start workout",
        "workout_vacia": "No workouts created",
        # Achievements
        "logros": "Achievements",
        "logro_primera_pausa": "First break completed",
        "logro_5_pausas": "5 breaks in one day",
        "logro_10_pausas": "10 breaks in one day",
        "logro_racha_3": "3-day streak",
        "logro_racha_7": "1-week streak",
        "logro_racha_30": "1-month streak",
        "logro_todos_ejercicios": "All exercises completed",
        "logro_early_bird": "Break before 9am",
        "logro_night_owl": "Break after 8pm",
        "logro_water_10": "10 water reminders",
        "logro_desbloqueado": "Achievement unlocked!",
        # Export/Import
        "exportar_stats": "Export statistics",
        "importar_stats": "Import statistics",
        "exportar_ok": "Statistics exported to:\n{path}",
        "importar_ok": "Statistics imported successfully",
        "importar_error": "Import error: {error}",
        # Custom hotkeys
        "section_hotkeys_custom": "Keyboard shortcuts",
        "hotkey_siguiente": "Next step/exercise",
        "hotkey_anterior": "Previous step/exercise",
        "hotkey_pausar": "Pause/resume timer",
        "hotkey_saltar": "Skip break",
        # Sound
        "sound_packs": "Sound packs",
        "sound_pack_default": "Default",
        "sound_pack_nature": "Nature",
        "sound_pack_minimal": "Minimal",
        "sound_pack_activo": "Active pack",
        # Tutorial
        "tutorial_paso1_titulo": "Step 1: Configure your breaks",
        "tutorial_paso1_desc": "Set how often you want to take an active break.",
        "tutorial_paso2_titulo": "Step 2: Choose exercises",
        "tutorial_paso2_desc": "Select the exercises you like most.",
        "tutorial_paso3_titulo": "Step 3: Customize",
        "tutorial_paso3_desc": "Change colors, sounds and other settings.",
        "tutorial_saltar": "Skip tutorial",
        "tutorial_completar": "Got it!",
        # Fullscreen
        "fullscreen_timer": "Fullscreen mode",
        "fullscreen_desc": "Large timer fullscreen for presentations",
        "fullscreen_salir": "Exit fullscreen (Esc)",
        # Toast
        "toast_info": "Information",
        "toast_exito": "Success",
        "toast_advertencia": "Warning",
        # Motivational phrases
        "frases": [
            "Excellent! Your body thanks you.",
            "Every break is an investment in your health.",
            "Well done! Keep it up.",
            "Your productivity improves with every rest.",
            "You are consistent. That makes the difference.",
            "Small habits, big changes.",
            "Your back and eyes thank you.",
            "Break completed. You come back stronger.",
            "Daily goal achieved! Great job.",
            "Rest is part of success.",
        ],
    },
}

_idioma_actual: str = "es"


def set_idioma(lang: str) -> None:
    global _idioma_actual
    if lang in I18N:
        _idioma_actual = lang


def _(key: str) -> str:
    return I18N[_idioma_actual].get(key, key)


def get_random_phrase() -> str:
    return random.choice(I18N[_idioma_actual].get("frases", ["Buen trabajo!"]))
