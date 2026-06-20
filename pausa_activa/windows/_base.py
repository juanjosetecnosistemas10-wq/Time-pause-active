"""Shared helpers, base window class, and standalone functions."""

from __future__ import annotations

import sys
import winreg
from tkinter import Canvas
from typing import Any

import customtkinter as ctk

from pausa_activa.audio import AudioManager
from pausa_activa.constants import (
    APP_NAME,
    C,
    F,
    center_window,
)

_audio_manager: AudioManager | None = None


def get_audio_manager() -> AudioManager:
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


def set_autoarranque(enable: bool, app_path: str) -> None:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)
    try:
        if enable:
            if getattr(sys, "frozen", False):
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
            else:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{sys.executable}" "{app_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def get_autoarranque() -> bool:
    key = None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        return True
    except Exception:
        return False
    finally:
        if key:
            winreg.CloseKey(key)


def _card(parent: ctk.CTkBaseClass, **kwargs: Any) -> ctk.CTkFrame:
    kwargs.setdefault("fg_color", C.CARD)
    kwargs.setdefault("corner_radius", 12)
    kwargs.setdefault("border_width", 0)
    kwargs.setdefault("border_color", C.CARD_BORDER)
    return ctk.CTkFrame(parent, **kwargs)


def _entry(parent: ctk.CTkBaseClass, variable: ctk.Variable, width: int = 120) -> ctk.CTkEntry:
    return ctk.CTkEntry(parent, textvariable=variable, font=F(11),
                        fg_color=C.BG3, text_color=C.TEXT, border_color=C.BORDER,
                        width=width, corner_radius=6)


def _checkbox(parent: ctk.CTkBaseClass, text: str, variable: ctk.Variable) -> ctk.CTkCheckBox:
    return ctk.CTkCheckBox(parent, text=text, variable=variable,
                           fg_color=C.ACCENT, text_color=C.TEXT,
                           font=F(9), hover_color=C.ACCENT2,
                           corner_radius=4, border_width=2, checkmark_color=C.BG)


def _radio(parent: ctk.CTkBaseClass, text: str, variable: ctk.Variable, value: str) -> ctk.CTkRadioButton:
    return ctk.CTkRadioButton(parent, text=text, variable=variable, value=value,
                              fg_color=C.ACCENT, text_color=C.TEXT,
                              font=F(9), hover_color=C.ACCENT2,
                              border_width_checked=5, border_width_unchecked=2)


class CenteredWindow(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent, *args, **kwargs)
        self.resizable(False, False)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass
        self.after(10, self._fade_in)

    def _fade_in(self) -> None:
        try:
            for i in range(1, 11):
                self.after(i * 15, lambda v=i / 10: self.attributes("-alpha", v))
        except Exception:
            self.attributes("-alpha", 1.0)

    def center(self) -> None:
        center_window(self)


def draw_bar_chart(
    canvas: Canvas,
    width: int,
    height: int,
    counts: dict[str, int],
    meta: int,
    day_labels: list[str] | None = None,
) -> None:
    import datetime as dt
    canvas.delete("all")
    today = dt.date.today()
    labels = day_labels or ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]
    baseline_y = height - 3
    canvas.create_line(0, baseline_y, width, baseline_y, fill=C.BORDER, width=1)

    filtered: dict[str, int] = {}
    for i in range(7):
        d = today - dt.timedelta(6 - i)
        key = d.isoformat()
        filtered[key] = counts.get(key, 0)

    max_val = max(filtered.values()) if filtered else 1
    max_val = max(max_val, meta, 1)
    bar_w = max(8, min(28, (width - 20) // 14))
    gap = max(2, (width - 7 * bar_w) // 8)
    available_h = max(10, height - 18)
    for i in range(7):
        d = today - dt.timedelta(6 - i)
        key = d.isoformat()
        val = filtered.get(key, 0)
        x = gap + i * (bar_w + gap)
        bar_h = max(2, int((val / max_val) * available_h))
        color = C.GREEN if val >= meta else (C.YELLOW if val >= meta // 2 else C.TEXT_DIM)
        canvas.create_rectangle(
            x, baseline_y - bar_h, x + bar_w, baseline_y,
            fill=color, outline="", width=0,
        )
        if height > 50 and bar_h > 8:
            canvas.create_text(
                x + bar_w // 2, baseline_y - bar_h - 2,
                text=str(val), fill=C.TEXT_DIM, font=F(7),
            )
        canvas.create_text(
            x + bar_w // 2, baseline_y + 4,
            text=labels[i], fill=C.TEXT_DIM, font=F(6),
        )


def _dibujar_grafico(parent: ctk.CTkFrame, history: dict[str, dict[str, Any]], meta: int) -> None:
    import datetime as dt
    from calendar import day_abbr
    canvas = Canvas(parent, width=340, height=140, bg=C.CARD, highlightthickness=0)
    canvas.pack(padx=10, pady=10)
    counts: dict[str, int] = {}
    for day, data in history.items():
        counts[day] = data.get("completadas", 0)
    today = dt.date.today()
    labels = [day_abbr[(today - dt.timedelta(days=6 - i)).weekday()][:3] for i in range(7)]
    draw_bar_chart(canvas, 340, 140, counts, meta, day_labels=labels)
