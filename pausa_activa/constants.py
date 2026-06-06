"""Constantes del proyecto."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

APP_NAME: str = "PausasActivas"
APP_DISPLAY: str = "Pausas Activas"

INSTALL_DIR_REG: str = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PausasActivas"

# ── Temas ──────────────────────────────────────────────────────────────────
# Se mantienen como variables de módulo para compatibilidad con imports.

THEMES: dict[str, dict[str, Any]] = {
    "oscuro": {
        "BG": "#111827",
        "BG2": "#1F2937",
        "BG3": "#374151",
        "ACCENT": "#38BDF8",
        "ACCENT2": "#FB7185",
        "GREEN": "#4ADE80",
        "YELLOW": "#FBBF24",
        "TEXT": "#F1F5F9",
        "TEXT_DIM": "#94A3B8",
        "BORDER": "#334155",
        "AGUA": "#22D3EE",
        "TRAY_ACTIVE": (56, 189, 248),
        "TRAY_PAUSED": (148, 163, 184),
        "TRAY_OFF": (251, 113, 133),
    },
    "claro": {
        "BG": "#F1F5F9",
        "BG2": "#FFFFFF",
        "BG3": "#E2E8F0",
        "ACCENT": "#0284C7",
        "ACCENT2": "#E11D48",
        "GREEN": "#16A34A",
        "YELLOW": "#D97706",
        "TEXT": "#0F172A",
        "TEXT_DIM": "#64748B",
        "BORDER": "#CBD5E1",
        "AGUA": "#0891B2",
        "TRAY_ACTIVE": (2, 132, 199),
        "TRAY_PAUSED": (100, 116, 139),
        "TRAY_OFF": (225, 29, 72),
    },
}

_tema_actual: str = "oscuro"

# Variables de módulo para compatibilidad (se actualizan con el tema)
BG: str = ""
BG2: str = ""
BG3: str = ""
ACCENT: str = ""
ACCENT2: str = ""
GREEN: str = ""
YELLOW: str = ""
TEXT: str = ""
TEXT_DIM: str = ""
BORDER: str = ""
AGUA: str = ""
TRAY_ACTIVE: tuple[int, int, int] = (0, 0, 0)
TRAY_PAUSED: tuple[int, int, int] = (0, 0, 0)
TRAY_OFF: tuple[int, int, int] = (0, 0, 0)


def _apply_theme(nombre: str) -> None:
    """Actualiza las variables de módulo según el tema seleccionado."""
    global BG, BG2, BG3, ACCENT, ACCENT2, GREEN, YELLOW, TEXT, TEXT_DIM, BORDER, AGUA
    global TRAY_ACTIVE, TRAY_PAUSED, TRAY_OFF
    t = THEMES.get(nombre, THEMES["oscuro"])
    BG = t["BG"]
    BG2 = t["BG2"]
    BG3 = t["BG3"]
    ACCENT = t["ACCENT"]
    ACCENT2 = t["ACCENT2"]
    GREEN = t["GREEN"]
    YELLOW = t["YELLOW"]
    TEXT = t["TEXT"]
    TEXT_DIM = t["TEXT_DIM"]
    BORDER = t["BORDER"]
    AGUA = t["AGUA"]
    TRAY_ACTIVE = t["TRAY_ACTIVE"]
    TRAY_PAUSED = t["TRAY_PAUSED"]
    TRAY_OFF = t["TRAY_OFF"]


_apply_theme(_tema_actual)


def set_theme(nombre: str) -> None:
    global _tema_actual
    if nombre in THEMES:
        _tema_actual = nombre
        _apply_theme(nombre)


def get_theme() -> str:
    return _tema_actual


# ── Logging ────────────────────────────────────────────────────────────────

LOG_DIR: str = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
    APP_DISPLAY,
    "logs",
)
os.makedirs(LOG_DIR, exist_ok=True)

_file_handler = logging.FileHandler(
    os.path.join(LOG_DIR, "pausas_activas.log"),
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
log = logging.getLogger(APP_NAME)

# ── Config por defecto ─────────────────────────────────────────────────────

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


# ── Frases ─────────────────────────────────────────────────────────────────

FRASES: list[str] = [
    "Excelente! Tu cuerpo te lo agradece.",
    "Cada pausa es una inversion en tu salud.",
    "Bien hecho! Sigue asi.",
    "Tu productividad mejora con cada descanso.",
    "Eres constante. Eso marca la diferencia.",
    "Pequenos habitos, grandes cambios.",
    "Tu espalda y tus ojos te lo agradecen.",
    "Pausa completada. Vuelves mas fuerte.",
]

# ── i18n ───────────────────────────────────────────────────────────────────

I18N: dict[str, dict[str, str]] = {
    "es": {
        "app_name": "Pausas Activas",
        "pausa_activa": "PAUSA ACTIVA",
        "saltar_pausa": "Saltar pausa",
        "tiempo_restante": "tiempo restante",
        "estadisticas": "Estadísticas de hoy",
        "configuracion": "Configuración",
        "bienvenido": "¡Bienvenido a Pausas Activas!",
        "trabajando": "Trabajando...",
        "pausado": "Timer pausado",
        "pausa_ya": "Pausa ya",
        "posponer": "Posponer",
        "minimizar": "Minimizar a bandeja",
        "guardar": "Guardar",
        "cancelar": "Cancelar",
        "instalar": "Instalar",
        "desinstalar": "Desinstalar",
        "meta_cumplida": "¡Meta cumplida!",
        "agua_recordatorio": "¡Recuerda tomar agua!",
        "fuera_horario": "Fuera del horario activo",
        "fin_semana": "Fin de semana — descansando",
        "no_molestar": "No interrumpir si hay pantalla completa",
        "fin_de_semana_opt": "Pausar en fin de semana (sab y dom)",
        "sonido_alerta": "Activar sonido de alerta al iniciar pausa",
        "autoarranque": "Iniciar con Windows (autoarranque)",
        "sin_sonido": "Sin sonido",
        "lluvia": "Lluvia",
        "naturaleza": "Naturaleza",
        "exportar_csv": "Exportar CSV",
        "cerrar": "Cerrar",
        "config_temporizador": "⏱ Temporizador",
        "config_opciones": "⚙ Opciones",
        "config_sonido": "🔊 Sonido",
        "config_ejercicios": "🏃 Ejercicios",
        "modo_normal": "Normal",
        "modo_pomodoro": "Pomodoro",
        "modo_personalizado": "Personalizado",
    },
    "en": {
        "app_name": "Active Breaks",
        "pausa_activa": "ACTIVE BREAK",
        "saltar_pausa": "Skip break",
        "tiempo_restante": "time remaining",
        "estadisticas": "Today's statistics",
        "configuracion": "Settings",
        "bienvenido": "Welcome to Active Breaks!",
        "trabajando": "Working...",
        "pausado": "Timer paused",
        "pausa_ya": "Break now",
        "posponer": "Snooze",
        "minimizar": "Minimize to tray",
        "guardar": "Save",
        "cancelar": "Cancel",
        "instalar": "Install",
        "desinstalar": "Uninstall",
        "meta_cumplida": "Goal achieved!",
        "agua_recordatorio": "Remember to drink water!",
        "fuera_horario": "Outside active hours",
        "fin_semana": "Weekend — resting",
        "no_molestar": "Don't interrupt if fullscreen",
        "fin_de_semana_opt": "Pause on weekends (sat & sun)",
        "sonido_alerta": "Enable alert sound on break start",
        "autoarranque": "Start with Windows",
        "sin_sonido": "No sound",
        "lluvia": "Rain",
        "naturaleza": "Nature",
        "exportar_csv": "Export CSV",
        "cerrar": "Close",
        "config_temporizador": "⏱ Timer",
        "config_opciones": "⚙ Options",
        "config_sonido": "🔊 Sound",
        "config_ejercicios": "🏃 Exercises",
        "modo_normal": "Normal",
        "modo_pomodoro": "Pomodoro",
        "modo_personalizado": "Custom",
    },
}

_idioma_actual: str = "es"


def set_idioma(lang: str) -> None:
    global _idioma_actual
    if lang in I18N:
        _idioma_actual = lang


def _(key: str) -> str:
    return I18N[_idioma_actual].get(key, key)
