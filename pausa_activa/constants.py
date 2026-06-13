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
UPDATER_REPO: str = "tu_usuario/Time-pause-active"


def darken_color(hex_color: str, amount: int = 30) -> str:
    """Darken a hex color by the given amount."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{max(0, r - amount):02x}{max(0, g - amount):02x}{max(0, b - amount):02x}"

INSTALL_DIR_REG: str = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FlowBreak"

# ── Temas ──────────────────────────────────────────────────────────────────

THEMES: dict[str, dict[str, Any]] = {
    "oscuro": {
        "BG": "#0B1120",
        "BG2": "#162032",
        "BG3": "#1E2D45",
        "BG4": "#2A3D5C",
        "ACCENT": "#38BDF8",
        "ACCENT2": "#FB7185",
        "ACCENT3": "#A78BFA",
        "GREEN": "#4ADE80",
        "YELLOW": "#FBBF24",
        "TEXT": "#F1F5F9",
        "TEXT_DIM": "#94A3B8",
        "TEXT_MUTED": "#64748B",
        "BORDER": "#1E3A5F",
        "AGUA": "#22D3EE",
        "CARD": "#111D33",
        "CARD_BORDER": "#1A2D4A",
        "SUCCESS_BG": "#064E3B",
        "WARNING_BG": "#422006",
        "ERROR_BG": "#450A0A",
        "TRAY_ACTIVE": (56, 189, 248),
        "TRAY_PAUSED": (148, 163, 184),
        "TRAY_OFF": (251, 113, 133),
    },
    "claro": {
        "BG": "#F0F4F8",
        "BG2": "#FFFFFF",
        "BG3": "#E2E8F0",
        "BG4": "#CBD5E1",
        "ACCENT": "#0284C7",
        "ACCENT2": "#E11D48",
        "ACCENT3": "#7C3AED",
        "GREEN": "#16A34A",
        "YELLOW": "#D97706",
        "TEXT": "#0B1120",
        "TEXT_DIM": "#475569",
        "TEXT_MUTED": "#94A3B8",
        "BORDER": "#CBD5E1",
        "AGUA": "#0891B2",
        "CARD": "#FFFFFF",
        "CARD_BORDER": "#E2E8F0",
        "SUCCESS_BG": "#DCFCE7",
        "WARNING_BG": "#FEF3C7",
        "ERROR_BG": "#FEE2E2",
        "TRAY_ACTIVE": (2, 132, 199),
        "TRAY_PAUSED": (100, 116, 139),
        "TRAY_OFF": (225, 29, 72),
    },
}

# ── Paletas de acento ──────────────────────────────────────────────────────

ACCENT_PALETTES: dict[str, dict[str, Any]] = {
    "azul":    {"ACCENT": "#38BDF8", "TRAY_ACTIVE": (56, 189, 248)},
    "verde":   {"ACCENT": "#34D399", "TRAY_ACTIVE": (52, 211, 153)},
    "morado":  {"ACCENT": "#A78BFA", "TRAY_ACTIVE": (167, 139, 250)},
    "rosa":    {"ACCENT": "#F472B6", "TRAY_ACTIVE": (244, 114, 182)},
    "naranja": {"ACCENT": "#FB923C", "TRAY_ACTIVE": (251, 146, 60)},
    "teal":    {"ACCENT": "#2DD4BF", "TRAY_ACTIVE": (45, 212, 191)},
    "rojo":    {"ACCENT": "#F87171", "TRAY_ACTIVE": (248, 113, 113)},
}

# ── Paletas de fondo ───────────────────────────────────────────────────────

FONDO_PALETTES: dict[str, dict[str, str]] = {
    "estandar":   {},
    "profundo":   {"BG": "#08080A", "BG2": "#121316", "BG3": "#202126", "CARD": "#121316"},
    "gris":       {"BG": "#161618", "BG2": "#202124", "BG3": "#2E2F34", "CARD": "#202124"},
    "azulado":    {"BG": "#0D1117", "BG2": "#161B22", "BG3": "#21262D", "CARD": "#161B22"},
    "blanco":     {"BG": "#FFFFFF", "BG2": "#F8F8FA", "BG3": "#EEEEF2", "CARD": "#F8F8FA"},
    "gris_suave": {"BG": "#E8E8EC", "BG2": "#DDDDE1", "BG3": "#D0D0D5", "CARD": "#FFFFFF"},
    "calido":     {"BG": "#FAF5F0", "BG2": "#F0EBE6", "BG3": "#E5E0DB", "CARD": "#FFFFFF"},
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
            except ImportError:
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
}

# ── Ejercicios ─────────────────────────────────────────────────────────────

EJERCICIOS_BUILTIN: list[dict[str, Any]] = [
    {"id": "cuello",  "nombre": "Estiramiento de cuello",  "icono": "🧘", "pasos": ["Inclina la cabeza a la derecha (10 seg)", "Inclina la cabeza a la izquierda (10 seg)", "Gira suavemente en circulos (3 veces)"]},
    {"id": "hombros", "nombre": "Estiramiento de hombros", "icono": "💪", "pasos": ["Lleva el brazo derecho al pecho y sujetalo (10 seg)", "Repite con el brazo izquierdo", "Sube los hombros hasta las orejas y suelta (5 veces)"]},
    {"id": "espalda", "nombre": "Estiramiento de espalda", "icono": "🏃", "pasos": ["Parate y estira los brazos hacia arriba (10 seg)", "Inclinate hacia adelante y toca tus pies (10 seg)", "Gira el tronco a cada lado (5 veces)"]},
    {"id": "visual",  "nombre": "Descanso visual",         "icono": "👁️", "pasos": ["Mira un objeto lejano 6+ metros por 20 seg", "Cierra los ojos y apoyalos con las palmas (10 seg)", "Parpadea rapidamente 10 veces"]},
    {"id": "manos",   "nombre": "Ejercicio de manos",      "icono": "✋", "pasos": ["Abre y cierra los punos (10 veces)", "Gira las munecas en circulos (5 por lado)", "Estira los dedos hacia atras suavemente (10 seg)"]},
    {"id": "sentad",  "nombre": "Sentadillas rapidas",     "icono": "🏋️", "pasos": ["Parate con pies al ancho de los hombros", "Baja lentamente hasta 90 grados (5 veces)", "Manten la espalda recta en todo momento"]},
    {"id": "respira", "nombre": "Respiracion profunda",    "icono": "🌬️", "pasos": ["Inhala profundo por 4 segundos", "Reten el aire 4 segundos", "Exhala lentamente por 6 segundos (repite 5 veces)"]},
    {"id": "caminar", "nombre": "Caminar",                 "icono": "🚶", "pasos": ["Levantate y camina al menos 50 pasos", "Sube y baja escaleras si es posible", "Regresa y estira las piernas brevemente"]},
    {"id": "postura", "nombre": "Postura de poder",        "icono": "🧍", "pasos": ["Parate derecho, pies al ancho de los hombros", "Hombros hacia atras y abajo, pecho al frente", "Menton paralelo al piso, manten 30 segundos respirando profundo"]},
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
