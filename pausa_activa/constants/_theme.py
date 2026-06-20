from __future__ import annotations

from typing import Any

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

ACCENT_PALETTES: dict[str, dict[str, Any]] = {
    "azul":    {"ACCENT": "#3B82F6", "TRAY_ACTIVE": (59, 130, 246), "GLOW": "#3B82F6"},
    "verde":   {"ACCENT": "#10B981", "TRAY_ACTIVE": (16, 185, 129), "GLOW": "#10B981"},
    "morado":  {"ACCENT": "#8B5CF6", "TRAY_ACTIVE": (139, 92, 246), "GLOW": "#8B5CF6"},
    "rosa":    {"ACCENT": "#EC4899", "TRAY_ACTIVE": (236, 72, 153), "GLOW": "#EC4899"},
    "naranja": {"ACCENT": "#F97316", "TRAY_ACTIVE": (249, 115, 22), "GLOW": "#F97316"},
    "teal":    {"ACCENT": "#14B8A6", "TRAY_ACTIVE": (20, 184, 166), "GLOW": "#14B8A6"},
    "rojo":    {"ACCENT": "#EF4444", "TRAY_ACTIVE": (239, 68, 68), "GLOW": "#EF4444"},
}

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
