"""Todas las ventanas de la UI (FlowBreak)."""

from __future__ import annotations

import os
import random
import math
import re
import subprocess
import sys
import threading
import winreg
import customtkinter as ctk
from tkinter import Canvas, filedialog, messagebox
from typing import Any, Callable

from pausa_activa.constants import (
    C, APP_NAME, APP_DISPLAY, EJERCICIOS, get_random_phrase, set_theme, set_idioma,
    _, I18N, THEMES, F, center_window, darken_color,
    log,
)
from pausa_activa.audio import AudioManager
from pausa_activa.notifications import send_win_notification
from pausa_activa.installer import (
    _get_install_dir_from_registry,
    _eliminar_accesos_directos, _programar_borrado_carpeta,
    _quitar_registro_desinstalador,
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


# ═══════════════════════════════════════════════════════════════════════════
# Gráfico de barras con Canvas
# ═══════════════════════════════════════════════════════════════════════════

def draw_bar_chart(
    canvas: Canvas,
    width: int,
    height: int,
    counts: dict[str, int],
    meta: int,
    day_labels: list[str] | None = None,
) -> None:
    """Draw a 7-day bar chart on the given canvas.
    
    counts: dict mapping ISO date -> count of completed breaks.
    """
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


# ═══════════════════════════════════════════════════════════════════════════
# BreakWindow (antes PausaWindow) — paso a paso con animaciones
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
        guia_voz: bool = True,
    ) -> None:
        super().__init__(parent)
        self.on_done: Callable[[], None] = on_done
        self.on_skip: Callable[[], None] = on_skip
        self.ejercicio: dict[str, Any] = ejercicio
        self._job: str | None = None
        self._anim_job: str | None = None
        pasos = self.ejercicio.get("pasos", [])
        self._num_steps: int = max(len(pasos), 1)

        PREP_SEC = 10
        MIN_EX = 10
        MIN_TOTAL = PREP_SEC + MIN_EX
        num = self._num_steps

        ex_times = []
        for paso in pasos:
            ex_times.append(self._parse_step_time(paso))

        if any(t is not None for t in ex_times):
            step_durs = []
            for t in ex_times:
                if t is not None:
                    step_durs.append(PREP_SEC + t)
                else:
                    step_durs.append(MIN_TOTAL)
            total_from_desc = sum(step_durs)
            if total_from_desc < duracion_sec:
                extra = duracion_sec - total_from_desc
                idxs = [i for i, t in enumerate(ex_times) if t is None]
                if idxs:
                    per = extra // len(idxs)
                    for i in idxs:
                        step_durs[i] += per
        else:
            total_min = num * MIN_TOTAL
            actual = max(total_min, duracion_sec)
            avg = actual // num
            step_durs = [avg] * num
            if num > 1 and avg >= MIN_TOTAL + 5:
                step_durs[0] -= 5
                step_durs[-1] += 5
        self._step_durations: list[int] = step_durs
        self._prep_duration: int = PREP_SEC
        self.remaining: int = sum(step_durs)
        self._duracion_original: int = self.remaining
        self._current_step: int = 0
        self._step_remaining: int = step_durs[0]
        self._in_prep: bool = True

        self._showing_presentation: bool = True
        self._showing_summary: bool = False
        self._guia_voz: bool = guia_voz
        self._step_completed_count: int = 0
        self._step_banner_frames: int = 0
        self._last_step: int = -1

        self._breath_frame: int = 0
        self._anim_progress: float = 0.0

        self.title(_("pausa_activa"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self._build()
        self.center()
        self.protocol("WM_DELETE_WINDOW", self._skip)
        if sonido_ambiente != "ninguno":
            get_audio_manager().start_ambient(sonido_ambiente)
        self._start_animation()
        self._tick()

    def _build(self) -> None:
        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)
        self._main = main

        # ── Exercise Header ────────────────────────────────────────────
        icon_frame = ctk.CTkFrame(main, fg_color="transparent")
        icon_frame.pack(pady=(24, 0))

        ctk.CTkLabel(
            icon_frame, text=self.ejercicio["icono"],
            font=("Segoe UI Emoji", 56), text_color=C.TEXT,
        ).pack()

        ctk.CTkLabel(
            main, text=self.ejercicio["nombre"],
            font=F(20, "bold"), text_color=C.TEXT,
        ).pack(pady=(4, 0))

        ctk.CTkLabel(
            main, text=self.ejercicio.get("instrucciones", ""),
            font=F(10), text_color=C.TEXT_DIM, wraplength=340, justify="center",
        ).pack(pady=(4, 8))

        # ── Step Progress Bar (modern) ─────────────────────────────────
        if self._num_steps > 1:
            progress_frame = ctk.CTkFrame(main, fg_color="transparent")
            progress_frame.pack(fill="x", padx=30, pady=(4, 8))

            self._step_bar = ctk.CTkProgressBar(
                progress_frame, width=300, height=4,
                corner_radius=2, fg_color=C.BG3,
                progress_color=C.ACCENT,
            )
            self._step_bar.pack()
            self._step_bar.set(0)

            self._step_counter = ctk.CTkLabel(
                progress_frame, text=f"Paso 1/{self._num_steps}",
                font=F(9, "bold"), text_color=C.ACCENT,
            )
            self._step_counter.pack(pady=(4, 0))

        # ── Step Instruction Card ──────────────────────────────────────
        step_card = ctk.CTkFrame(
            main, fg_color=C.CARD, corner_radius=16,
            border_width=1, border_color=C.CARD_BORDER,
        )
        step_card.pack(fill="x", padx=24, pady=(4, 8))
        self._step_label = ctk.CTkLabel(
            step_card, text="", font=F(12),
            text_color=C.TEXT, wraplength=300, justify="center",
        )
        self._step_label.pack(padx=20, pady=14)

        # ── Animation Canvas ───────────────────────────────────────────
        self._anim_canvas = Canvas(
            main, width=220, height=180,
            bg=C.BG, highlightthickness=0,
        )
        self._anim_canvas.pack(pady=(4, 0))

        # ── Timer Ring ─────────────────────────────────────────────────
        self._canvas = Canvas(
            main, width=140, height=140,
            bg=C.BG, highlightthickness=0,
        )
        self._canvas.pack(pady=(4, 0))
        cx, cy, r = 70, 70, 60
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=C.BG3, width=6, tags="bg_oval",
        )
        self._canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=90, extent=360,
            outline=C.GREEN, width=6, style="arc", tags="fg_arc",
        )
        self._canvas.create_text(
            cx, cy, text=self._fmt_time(self.remaining),
            font=F(26, "bold"), fill=C.TEXT, tags="cd_text",
        )

        # ── Step Timer ─────────────────────────────────────────────────
        step_timer_frame = ctk.CTkFrame(main, fg_color="transparent")
        step_timer_frame.pack(pady=(2, 0))
        self._step_timer_label = ctk.CTkLabel(
            step_timer_frame, text="",
            font=F(32, "bold"), text_color=C.ACCENT,
        )
        self._step_timer_label.pack()
        self._step_progress = ctk.CTkProgressBar(
            step_timer_frame, width=220, height=5,
            corner_radius=3, fg_color=C.BG3,
            progress_color=C.ACCENT,
        )
        self._step_progress.pack(pady=(4, 0))
        self._step_progress.set(1.0)

        # ── Buttons Row ────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(pady=(8, 16))

        ctk.CTkButton(
            btn_row, text="✅  Listo",
            fg_color=C.GREEN, text_color="#FFFFFF",
            hover_color=darken_color(C.GREEN),
            font=F(11, "bold"), corner_radius=12,
            width=110, height=34,
            command=self._next_step_ready,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text=_("saltar_pausa"),
            fg_color="transparent", text_color=C.TEXT_MUTED,
            font=F(10), hover_color=C.BG3, corner_radius=10,
            width=120, height=30,
            command=self._skip,
        ).pack(side="left", padx=6)

        self._highlight_step()

    def _start_animation(self) -> None:
        self._anim_job = self.after(80, self._animar_ejercicio)

    def _clear_main(self) -> None:
        for w in self._main.winfo_children():
            w.destroy()

    def _osc(self, t: float, freq: float) -> float:
        import math
        return math.sin(t * freq * 2 * math.pi)

    def _dibujar_mano(self, canvas: Canvas, w: int, h: int, step: int, hp: float) -> None:
        canvas.delete("all")
        cw = min(w, h) / 260.0
        cx, cy = w // 2, h // 2
        self._dibujar_figura(canvas, w, h, torso_lean=10 * hp)

    def _dibujar_ojo(self, canvas: Canvas, w: int, h: int, sp: float) -> None:
        canvas.delete("all")
        import math
        cw = min(w, h) / 260.0
        cx, cy = w // 2, h // 2
        eye_r = int(40 * cw)
        pupil_r = int(15 * cw * (0.5 + 0.5 * math.sin(sp * 6.283)))
        canvas.create_oval(cx - eye_r, cy - eye_r, cx + eye_r, cy + eye_r,
                           fill="white", outline=C.ACCENT, width=3)
        canvas.create_oval(cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r,
                           fill=C.TEXT)

    def _dibujar_respiracion(self, canvas: Canvas, w: int, h: int) -> None:
        canvas.delete("all")
        import math
        cw = min(w, h) / 260.0
        cx, cy = w // 2, h // 2
        self._breath_frame += 1
        breath = 0.5 + 0.5 * math.sin(self._breath_frame * 0.1)
        r = int(60 * cw * breath)
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           outline=C.ACCENT, width=4)
        txt = _("preparate") if breath > 0.7 else "Exhala"
        canvas.create_text(cx, cy + r + 30, text=txt, font=F(14), fill=C.TEXT)

    def _animar_ejercicio(self) -> None:
        if self._showing_summary:
            return
        try:
            canvas = getattr(self, "_anim_canvas", None)
            if not canvas:
                self._anim_job = self.after(80, self._animar_ejercicio)
                return
            w = canvas.winfo_width() or 200
            h = canvas.winfo_height() or 200

            eid = self.ejercicio["id"]
            import math

            self._breath_frame += 1
            self._anim_progress += 0.04
            anim_sp = self._anim_progress % 1.0
            sway = 0.6 * math.sin(self._breath_frame * 0.08)

            sp = anim_sp

            if eid == "cuello":
                if self._current_step == 0:
                    ht = 30 * math.sin(sp * 12.566)
                    self._dibujar_figura(canvas, w, h, head_tilt=ht, torso_lean=sway)
                elif self._current_step == 1:
                    ht = 25 * math.cos(sp * 8.368)
                    hn = 20 * math.sin(sp * 8.368)
                    self._dibujar_figura(canvas, w, h, head_tilt=ht, head_nod=hn, torso_lean=sway)
                else:
                    hn = 30 * math.sin(sp * 12.566)
                    self._dibujar_figura(canvas, w, h, head_nod=hn, torso_lean=sway)
            elif eid == "hombros":
                o = self._osc(sp, 10)
                if self._current_step == 0:
                    sq = 0.2 * self._osc(sp, 10)
                    self._dibujar_figura(canvas, w, h, squat=-sq, torso_lean=sway)
                elif self._current_step == 1:
                    a = 70 * o
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-a, arm_r_angle=a,
                                          squat=-0.15*o, torso_lean=sway)
                else:
                    a = 70 * o
                    self._dibujar_figura(canvas, w, h, arm_l_angle=a, arm_r_angle=-a,
                                          squat=-0.15*o, torso_lean=sway)
            elif eid == "espalda":
                if self._current_step == 0:
                    a = 160 * self._osc(sp, 5)
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-a, arm_r_angle=a, torso_lean=sway)
                elif self._current_step == 1:
                    lean = 45 * math.sin(sp * 6.283)
                    self._dibujar_figura(canvas, w, h, torso_lean=lean+sway,
                                          arm_l_angle=-90, arm_r_angle=90)
                else:
                    twist = 70 * math.sin(sp * 12.566)
                    self._dibujar_figura(canvas, w, h, torso_lean=sway,
                                          arm_l_angle=twist, arm_r_angle=-twist)
            elif eid == "manos":
                if self._current_step == 0:
                    hp = self._osc(sp, 6)
                elif self._current_step == 1:
                    hp = self._osc(sp, 10)
                else:
                    hp = sp
                self._dibujar_mano(canvas, w, h, self._current_step, hp)
            elif eid == "sentad":
                o = self._osc(sp, 8)
                if self._current_step == 0:
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-10, arm_r_angle=10, torso_lean=sway)
                elif self._current_step == 1:
                    sq = 0.8 * o
                    lean_fwd = 15 * o
                    self._dibujar_figura(canvas, w, h, squat=sq, torso_lean=lean_fwd,
                                          arm_l_angle=-80*o, arm_r_angle=80*o,
                                          leg_l_angle=50*o, leg_r_angle=-50*o)
                else:
                    phase2 = sp * 6.283 * 12
                    lift = max(0, math.sin(phase2)) * 0.6
                    self._dibujar_figura(canvas, w, h, squat=lift, torso_lean=sway+5*math.sin(phase2),
                                          arm_l_angle=-30*math.sin(phase2), arm_r_angle=30*math.sin(phase2),
                                          leg_l_angle=40*math.sin(phase2), leg_r_angle=-40*math.sin(phase2))
            elif eid == "caminar":
                phase = sp * 6.283 * 15
                bounce = 0.1 * abs(math.sin(phase))
                leg_l = 30*math.sin(phase)-5
                leg_r = -30*math.sin(phase)+5
                self._dibujar_figura(canvas, w, h,
                                      leg_l_angle=leg_l, leg_r_angle=leg_r,
                                      arm_l_angle=-35*math.sin(phase), arm_r_angle=35*math.sin(phase),
                                      squat=bounce, torso_lean=sway)
            elif eid == "postura":
                o = self._osc(sp, 4)
                a = 30 * o
                self._dibujar_figura(canvas, w, h, arm_l_angle=-45-a, arm_r_angle=45+a,
                                      head_tilt=-5+sway*0.5, head_nod=2, torso_lean=sway)
            elif eid == "cadera":
                if self._current_step == 0:
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-45, arm_r_angle=45, torso_lean=sway)
                elif self._current_step == 1:
                    lean_h = 30 * math.cos(sp * 12.566)
                    lean_v = 20 * math.sin(sp * 12.566)
                    self._dibujar_figura(canvas, w, h, torso_lean=lean_h + sway,
                                          squat=lean_v*0.03,
                                          arm_l_angle=-45, arm_r_angle=45)
                else:
                    fwd = 25 * math.sin(sp * 8.368)
                    self._dibujar_figura(canvas, w, h, torso_lean=sway,
                                          squat=fwd*0.04,
                                          arm_l_angle=-45, arm_r_angle=45)
            elif eid == "tobillos":
                if self._current_step == 0:
                    self._dibujar_figura(canvas, w, h, leg_l_angle=5,
                                          arm_l_angle=-25, arm_r_angle=25, torso_lean=sway)
                elif self._current_step == 1:
                    leg_swing = 20 * math.sin(sp * 18.850)
                    self._dibujar_figura(canvas, w, h, leg_l_angle=5, leg_r_angle=leg_swing,
                                          arm_l_angle=-25, arm_r_angle=25, torso_lean=sway)
                else:
                    leg_swing = 20 * math.cos(sp * 18.850)
                    self._dibujar_figura(canvas, w, h, leg_l_angle=leg_swing, leg_r_angle=5,
                                          arm_l_angle=-25, arm_r_angle=25, torso_lean=sway)
            elif eid == "yoga":
                if self._current_step == 0:
                    a = 30 + 40 * self._osc(sp, 4)
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-a, arm_r_angle=a,
                                          squat=0.15, torso_lean=sway)
                elif self._current_step == 1:
                    o = self._osc(sp, 5)
                    bend = 70 * o
                    arm_bend = 90 * o
                    self._dibujar_figura(canvas, w, h, torso_lean=bend + sway,
                                          arm_l_angle=-arm_bend, arm_r_angle=arm_bend,
                                          squat=0.3*o)
                else:
                    twist = 40 * math.sin(sp * 8.368)
                    self._dibujar_figura(canvas, w, h, torso_lean=twist + sway,
                                          arm_l_angle=-60, arm_r_angle=60,
                                          squat=0.2)
            elif eid == "visual":
                self._dibujar_ojo(canvas, w, h, sp)
            elif eid == "respira":
                self._dibujar_respiracion(canvas, w, h)
            else:
                self._dibujar_figura(canvas, w, h, torso_lean=sway)

            if self._step_banner_frames > 0:
                self._step_banner_frames -= 1
                canvas.create_rectangle(0, 0, w, h, fill=C.BG2, stipple="gray25")
                canvas.create_text(w//2, h//2 - 20,
                                    text="▶ Paso " + str(self._current_step + 1),
                                    font=F(22, "bold"), fill=C.ACCENT)
                pasos = self.ejercicio.get("pasos", [])
                if self._current_step < len(pasos):
                    canvas.create_text(w//2, h//2 + 15,
                                        text=pasos[self._current_step][:40],
                                        font=F(11), fill=C.TEXT,
                                        wraplength=w-40)

            self._anim_job = self.after(80, self._animar_ejercicio)
        except Exception:
            log.exception("Error en _animar_ejercicio")
            self._anim_job = self.after(80, self._animar_ejercicio)

    def _speak(self, text: str) -> None:
        if not self._guia_voz:
            return
        def _do_speak() -> None:
            try:
                import win32com.client
                sp = win32com.client.Dispatch("SAPI.SpVoice")
                sp.Speak(text, 1)
            except Exception:
                pass
        threading.Thread(target=_do_speak, daemon=True).start()

    @staticmethod
    def _parse_step_time(paso: str) -> int | None:
        m = re.search(r'(\d+)\s*seg', paso)
        if m:
            base = int(m.group(1))
            m_rep = re.search(r'(\d+)\s*veces', paso)
            if m_rep:
                reps = int(m_rep.group(1))
                return base * reps
            return base
        return None

    @property
    def _current_step_duration(self) -> int:
        return self._step_durations[self._current_step]

    # ── Drawing helpers ─────────────────────────────────────────────────────

    def _dibujar_figura(self, canvas: Canvas, w: int, h: int,
                          head_tilt: float = 0, head_nod: float = 0,
                          arm_l_angle: float = 0, arm_r_angle: float = 0,
                          leg_l_angle: float = 0, leg_r_angle: float = 0,
                          torso_lean: float = 0, squat: float = 0,
                          cw: float = 0) -> None:
        canvas.delete("all")
        if cw == 0:
            cw = min(w, h) / 260.0
        cx, cy = w // 2, int(h * 0.72)

        body_color = C.ACCENT
        head_color = "#3B82F6" if C.BG == "#0B1120" else "#60A5FA"
        joint_color = C.CARD
        ground_color = C.BG3

        head_r = int(22 * cw)
        body_len = int(65 * cw)
        arm_len = int(42 * cw)
        leg_len = int(38 * cw)
        line_w = max(3, int(5 * cw))

        sq = int(squat * 30 * cw)

        hip_x = cx
        hip_y = cy + sq

        lean_len = body_len // 2
        lean_rad = torso_lean * math.pi / 180
        neck_x = hip_x + int(lean_len * math.sin(lean_rad))
        neck_y = hip_y - int(lean_len * math.cos(lean_rad))

        canvas.create_line(neck_x, neck_y, hip_x, hip_y,
                            fill=body_color, width=line_w, capstyle="round")

        head_off = head_r + int(5*cw)
        tilt_rad = head_tilt * math.pi / 180
        nod_rad = head_nod * math.pi / 180
        head_cx = neck_x + int(head_off * math.sin(tilt_rad))
        head_cy = neck_y - int(head_off * math.cos(tilt_rad))
        head_cy = head_cy + int(head_off * 0.6 * math.sin(nod_rad))
        canvas.create_oval(head_cx - head_r, head_cy - head_r,
                            head_cx + head_r, head_cy + head_r,
                            fill=head_color, outline="", width=0)
        canvas.create_oval(head_cx - head_r, head_cy - head_r,
                            head_cx + head_r, head_cy + head_r,
                            fill="", outline=body_color, width=2)
        eye_off = int(7*cw)
        eye_r = max(2, int(3*cw))
        canvas.create_oval(head_cx - eye_off - eye_r, head_cy - eye_r,
                            head_cx - eye_off + eye_r, head_cy + eye_r, fill=C.TEXT)
        canvas.create_oval(head_cx + eye_off - eye_r, head_cy - eye_r,
                            head_cx + eye_off + eye_r, head_cy + eye_r, fill=C.TEXT)
        smile_r = int(6*cw)
        canvas.create_arc(head_cx - smile_r, head_cy + int(2*cw),
                           head_cx + smile_r, head_cy + int(7*cw),
                           start=0, extent=180, fill="", outline=C.TEXT_DIM, width=max(1, int(cw)))

        sh_x = neck_x
        sh_y = neck_y + int(7*cw)

        def _arm_end(jx, jy, angle_deg, length):
            rad = angle_deg * math.pi / 180
            return jx + int(length * math.sin(rad)), jy + int(length * math.cos(rad))

        lx, ly = _arm_end(sh_x, sh_y, arm_l_angle, arm_len)
        canvas.create_line(sh_x, sh_y, lx, ly,
                            fill=body_color, width=line_w, capstyle="round")
        rx, ry = _arm_end(sh_x, sh_y, arm_r_angle, arm_len)
        canvas.create_line(sh_x, sh_y, rx, ry,
                            fill=body_color, width=line_w, capstyle="round")

        hand_r = int(5 * cw)
        canvas.create_oval(lx - hand_r, ly - hand_r, lx + hand_r, ly + hand_r,
                            fill=joint_color, outline=body_color, width=1)
        canvas.create_oval(rx - hand_r, ry - hand_r, rx + hand_r, ry + hand_r,
                            fill=joint_color, outline=body_color, width=1)

        lx2, ly2 = _arm_end(hip_x, hip_y, leg_l_angle, leg_len)
        canvas.create_line(hip_x, hip_y, lx2, ly2,
                            fill=body_color, width=line_w, capstyle="round")
        rx2, ry2 = _arm_end(hip_x, hip_y, leg_r_angle, leg_len)
        canvas.create_line(hip_x, hip_y, rx2, ry2,
                            fill=body_color, width=line_w, capstyle="round")

        foot_w = int(8 * cw)
        foot_h = int(4 * cw)
        canvas.create_oval(lx2 - foot_w, ly2 - foot_h, lx2 + foot_w, ly2 + foot_h,
                            fill=joint_color, outline=body_color, width=1)
        canvas.create_oval(rx2 - foot_w, ry2 - foot_h, rx2 + foot_w, ry2 + foot_h,
                            fill=joint_color, outline=body_color, width=1)

        ground_y = max(ly2, ry2) + int(8*cw)
        canvas.create_oval(cx - int(60*cw), ground_y,
                           cx + int(60*cw), ground_y + int(4*cw),
                           fill=ground_color, outline="", width=0)

    def _animar_respiracion(self) -> None:
        if self._showing_summary:
            return
        try:
            canvas = getattr(self, "_anim_canvas", None)
            if not canvas:
                self._anim_job = self.after(50, self._animar_respiracion)
                return
            w = canvas.winfo_width() or 240
            h = canvas.winfo_height() or 240
            self._breath_frame += 1
            self._dibujar_respiracion(canvas, w, h)
            self._anim_job = self.after(50, self._animar_respiracion)
        except Exception:
            log.exception("Error en _animar_respiracion")
            self._anim_job = self.after(50, self._animar_respiracion)

    # ── Timer ────────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt_time(s: int) -> str:
        m, s = divmod(max(0, int(s)), 60)
        return f"{m:02d}:{s:02d}"

    def _fmt_time_step(self) -> str:
        return str(max(0, int(self._step_remaining)))

    def _tick(self) -> None:
        try:
            if self.remaining <= 0:
                self._show_summary()
                return

            self._step_remaining -= 1
            self.remaining -= 1

            pct = max(0.0, self.remaining / self._duracion_original)
            if pct > 0.5:
                color = C.GREEN
            elif pct > 0.2:
                color = C.YELLOW
            else:
                color = C.ACCENT2
            self._canvas.itemconfig("fg_arc", extent=360 * pct, outline=color)
            self._canvas.itemconfig("cd_text", text=self._fmt_time(self.remaining))

            elapsed = self._current_step_duration - self._step_remaining
            if elapsed < self._prep_duration:
                self._in_prep = True
                prep_left = self._prep_duration - elapsed
                if prep_left <= 3:
                    self._step_timer_label.configure(text=str(prep_left),
                                                      font=F(52, "bold"),
                                                      text_color=C.ACCENT2)
                else:
                    self._step_timer_label.configure(text=str(prep_left),
                                                      font=F(36, "bold"),
                                                      text_color=C.ACCENT)
                self._step_progress.set(max(0.0, prep_left / self._prep_duration))
                self._step_label.configure(text=f"⏳  {_('preparate')}  {prep_left}s")
            else:
                was_prep = self._in_prep
                self._in_prep = False
                ex_elapsed = elapsed - self._prep_duration
                ex_total = self._current_step_duration - self._prep_duration
                ex_left = ex_total - ex_elapsed
                self._step_timer_label.configure(text=str(ex_left),
                                                  font=F(36, "bold"),
                                                  text_color=C.ACCENT)
                self._step_progress.set(max(0.0, ex_left / ex_total))
                if was_prep:
                    self._highlight_step()
                    if self._guia_voz:
                        pasos = self.ejercicio.get("pasos", [])
                        if self._current_step < len(pasos):
                            self._speak(pasos[self._current_step])

            if self._step_remaining <= 0:
                if self._current_step + 1 < self._num_steps:
                    self._last_step = self._current_step
                    self._current_step += 1
                    self._step_remaining = self._current_step_duration
                    self._step_completed_count = self._current_step
                    self._in_prep = True
                    self._step_banner_frames = 12
                    self._anim_progress = 0.0
                    self._breath_frame = 0
                    self._highlight_step()
                else:
                    self._show_summary()
                    return

            self._job = self.after(1000, self._tick)
        except Exception as ex:
            log.exception("Error en BreakWindow._tick: %s", ex)
            self._done()

    def _next_step_ready(self) -> None:
        """El usuario terminó el paso actual, avanza al siguiente o termina."""
        if self._current_step + 1 < self._num_steps:
            self._last_step = self._current_step
            self._current_step += 1
            self._step_remaining = self._current_step_duration
            self._step_completed_count = self._current_step
            self._in_prep = True
            self._step_banner_frames = 12
            self._anim_progress = 0.0
            self._breath_frame = 0
            self._highlight_step()
        else:
            self._show_summary()

    def _highlight_step(self) -> None:
        pasos = self.ejercicio.get("pasos", [])
        if self._current_step < len(pasos):
            txt = pasos[self._current_step]
            self._step_label.configure(text=f"{txt}")
        if hasattr(self, "_step_bar"):
            self._step_bar.set(self._current_step / max(self._num_steps, 1))
        if hasattr(self, "_step_counter"):
            self._step_counter.configure(
                text=f"Paso {self._current_step + 1}/{self._num_steps}"
            )

    # ── Summary screen ──────────────────────────────────────────────────────

    def _show_summary(self) -> None:
        self._showing_summary = True
        try:
            if self._anim_job:
                self.after_cancel(self._anim_job)
                self._anim_job = None
        except Exception:
            pass
        try:
            if self._job:
                self.after_cancel(self._job)
                self._job = None
        except Exception:
            pass
        get_audio_manager().stop_ambient()
        self._clear_main()
        main = self._main

        # ── Success Icon ───────────────────────────────────────────────
        ctk.CTkLabel(
            main, text="🎉", font=("Segoe UI Emoji", 64),
            text_color=C.TEXT,
        ).pack(pady=(30, 0))

        ctk.CTkLabel(
            main, text=_("break_congrats_title"), font=F(24, "bold"),
            text_color=C.GREEN,
        ).pack(pady=(8, 4))

        ctk.CTkLabel(
            main, text=_("break_congrats_desc"),
            font=F(11), text_color=C.TEXT_DIM, wraplength=340, justify="center",
        ).pack(pady=(0, 16))

        # ── Progress Ring ──────────────────────────────────────────────
        ring_size = 120
        ring_canvas = Canvas(
            main, width=ring_size, height=ring_size,
            bg=C.BG, highlightthickness=0,
        )
        ring_canvas.pack(pady=(0, 8))
        rcx, rcy = ring_size // 2, ring_size // 2
        rr = 50
        ring_canvas.create_oval(
            rcx - rr, rcy - rr, rcx + rr, rcy + rr,
            outline=C.BG3, width=8, tags="ring_bg",
        )
        pct_done = self._step_completed_count / max(self._num_steps, 1)
        ring_canvas.create_arc(
            rcx - rr, rcy - rr, rcx + rr, rcy + rr,
            start=90, extent=360 * pct_done,
            outline=C.GREEN, width=8, style="arc", tags="ring_fg",
        )
        stars = int(pct_done * 5)
        star_txt = "⭐" * stars + "☆" * (5 - stars)
        ring_canvas.create_text(rcx, rcy, text=star_txt, font=F(12), fill=C.TEXT)

        # ── Summary Card ───────────────────────────────────────────────
        summary_card = ctk.CTkFrame(
            main, fg_color=C.CARD, corner_radius=16,
            border_width=1, border_color=C.CARD_BORDER,
        )
        summary_card.pack(fill="x", padx=24, pady=(8, 0))

        items = [
            ("🏋️", "Ejercicio", self.ejercicio["nombre"]),
            ("⏱️", "Duración", f"{self._duracion_original // 60} min"),
            ("📋", "Pasos", f"{self._num_steps}/{self._num_steps} completados"),
        ]
        for icon, label, val in items:
            row = ctk.CTkFrame(summary_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(
                row, text=icon, font=F(14), text_color=C.TEXT_DIM,
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(
                row, text=label, font=F(10), text_color=C.TEXT_MUTED, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=val, font=F(10, "bold"), text_color=C.TEXT,
            ).pack(side="right")

        # ── Motivational Phrase ────────────────────────────────────────
        frase = get_random_phrase()
        ctk.CTkLabel(
            main, text=f"💬  {frase}", font=F(10),
            text_color=C.TEXT_MUTED, wraplength=340, justify="center",
        ).pack(pady=(16, 12))

        # ── Close Button ───────────────────────────────────────────────
        ctk.CTkButton(
            main, text="✓  " + _("cerrar"),
            fg_color=C.GREEN, text_color="#FFFFFF",
            font=F(13, "bold"), corner_radius=22,
            height=44, width=180,
            command=self._done,
        ).pack(pady=(4, 20))

    def _done(self) -> None:
        self._showing_summary = True
        try:
            if self._anim_job:
                self.after_cancel(self._anim_job)
        except Exception:
            pass
        try:
            if self._job:
                self.after_cancel(self._job)
        except Exception:
            pass
        get_audio_manager().stop_ambient()
        self.destroy()
        self.on_done()

    def _skip(self) -> None:
        self._showing_summary = True
        try:
            if self._anim_job:
                self.after_cancel(self._anim_job)
        except Exception:
            pass
        try:
            if self._job:
                self.after_cancel(self._job)
        except Exception:
            pass
        get_audio_manager().stop_ambient()
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
        self.geometry("420x680")
        total: int = stats["completadas"] + stats["saltadas"]
        pct: int = int(stats["completadas"] / total * 100) if total > 0 else 0
        meta_ok: bool = stats["completadas"] >= meta

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        # ── Header ─────────────────────────────────────────────────────
        ctk.CTkLabel(
            main, text="📊", font=("Segoe UI Emoji", 36),
            text_color=C.TEXT,
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            main, text=_("estadisticas"), font=F(18, "bold"),
            text_color=C.TEXT,
        ).pack(pady=(0, 16))

        # ── Stat Cards Row ─────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(main, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20)

        stat_items: list[tuple[str, str, str, str]] = [
            ("✅", f"{stats['completadas']}", C.GREEN, "Completadas"),
            ("⏭️", str(stats["saltadas"]), C.ACCENT2, "Saltadas"),
            ("📈", f"{pct}%", C.ACCENT, "Éxito"),
            ("🔥", f"{stats.get('racha', 0)}d", C.YELLOW, "Racha"),
        ]
        for i, (icon, val, color, label) in enumerate(stat_items):
            card = ctk.CTkFrame(
                cards_frame, fg_color=C.CARD, corner_radius=14,
                border_width=1, border_color=C.CARD_BORDER,
            )
            card.grid(row=0, column=i, padx=3, pady=4, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(
                card, text=icon, font=F(16),
                text_color=C.TEXT_DIM,
            ).pack(pady=(10, 2))
            ctk.CTkLabel(
                card, text=val, font=F(18, "bold"),
                text_color=color,
            ).pack()
            ctk.CTkLabel(
                card, text=label, font=F(8),
                text_color=C.TEXT_MUTED,
            ).pack(pady=(0, 8))

        # ── Detail Card ────────────────────────────────────────────────
        detail_card = ctk.CTkFrame(
            main, fg_color=C.CARD, corner_radius=14,
            border_width=1, border_color=C.CARD_BORDER,
        )
        detail_card.pack(fill="x", padx=20, pady=(12, 0))

        status_icon: str = "🎯" if meta_ok else "🔄"
        status_text: str = "Meta alcanzada" if meta_ok else "En progreso"
        status_color: str = C.GREEN if meta_ok else C.TEXT_MUTED

        rows: list[tuple[str, str, str]] = [
            ("Completadas", f"{stats['completadas']} / {meta}", C.GREEN),
            ("Saltadas", str(stats["saltadas"]), C.ACCENT2),
            ("Tasa de éxito", f"{pct}%", C.ACCENT),
            ("Racha", f"{stats.get('racha', 0)} días", C.YELLOW),
            (f"{status_icon} Meta", status_text, status_color),
        ]
        for i, (label, val, color) in enumerate(rows):
            r = ctk.CTkFrame(detail_card, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=5)
            ctk.CTkLabel(
                r, text=label, font=F(10),
                text_color=C.TEXT_DIM, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                r, text=val, font=F(11, "bold"),
                text_color=color,
            ).pack(side="right")
            if i < len(rows) - 1:
                sep = ctk.CTkFrame(detail_card, fg_color=C.CARD_BORDER, height=1)
                sep.pack(fill="x", padx=16)

        # ── Weekly Chart ───────────────────────────────────────────────
        if history:
            chart_card = ctk.CTkFrame(
                main, fg_color=C.CARD, corner_radius=14,
                border_width=1, border_color=C.CARD_BORDER,
            )
            chart_card.pack(fill="x", padx=20, pady=(12, 0))
            ctk.CTkLabel(
                chart_card, text="📅  " + _("ultimos_7_dias"), font=F(10, "bold"),
                text_color=C.TEXT_DIM,
            ).pack(anchor="w", padx=14, pady=(10, 4))
            _dibujar_grafico(chart_card, history, meta)

        # ── Recent Breaks ──────────────────────────────────────────────
        if stats["historial"]:
            hist_card = ctk.CTkFrame(
                main, fg_color=C.CARD, corner_radius=14,
                border_width=1, border_color=C.CARD_BORDER,
            )
            hist_card.pack(fill="x", padx=20, pady=(12, 0))
            ctk.CTkLabel(
                hist_card, text="🕐  " + _("ultimas_pausas"), font=F(10, "bold"),
                text_color=C.TEXT_DIM,
            ).pack(anchor="w", padx=14, pady=(10, 6))
            for entry in stats["historial"][-5:][::-1]:
                dot: str = "🟢" if entry["estado"] == "completada" else "🔴"
                estado_color = C.GREEN if entry["estado"] == "completada" else C.ACCENT2
                r = ctk.CTkFrame(hist_card, fg_color="transparent")
                r.pack(fill="x", padx=14, pady=3)
                ctk.CTkLabel(
                    r, text=f"{dot}  {entry['hora']}  ·  {entry['ejercicio']}",
                    font=F(9), text_color=C.TEXT,
                ).pack(side="left")
                ctk.CTkLabel(
                    r, text=entry["estado"].capitalize(),
                    font=F(8, "bold"), text_color=estado_color,
                ).pack(side="right")
            ctk.CTkFrame(hist_card, fg_color="transparent").pack(pady=(0, 6))

        # ── Buttons ────────────────────────────────────────────────────
        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(14, 16))
        ctk.CTkButton(
            bf, text="📥  " + _("exportar_csv"),
            fg_color=C.BG3, text_color=C.TEXT,
            font=F(10), corner_radius=12, width=130, height=34,
            command=lambda: self._export(hist_file, stats, meta),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            bf, text=_("cerrar"),
            fg_color=C.ACCENT, text_color="#FFFFFF",
            font=F(10, "bold"), corner_radius=12, width=100, height=34,
            command=self.destroy,
        ).pack(side="left", padx=4)
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
        self.geometry("480x720")
        self._build()
        self.center()

    def _field(self, parent: ctk.CTkFrame, label: str, var: ctk.Variable, row: int) -> None:
        ctk.CTkLabel(parent, text=label, font=F(10),
                     text_color=C.TEXT_MUTED, anchor="w").pack(
            side="left", padx=16, pady=8)
        _entry(parent, var).pack(
            side="right", padx=16, pady=8)

    def _build(self) -> None:
        self.configure(fg_color=C.BG)

        # Header
        ctk.CTkLabel(self, text="⚙️  " + _("configuracion"), font=F(16, "bold"),
                     text_color=C.TEXT).pack(pady=(12, 4))

        # Container que contiene tabview + botón
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Tabview en fila 0 (expande)
        self.tabview = ctk.CTkTabview(container, fg_color="transparent",
                                       segmented_button_fg_color=C.BG3,
                                       segmented_button_selected_color=C.ACCENT,
                                       segmented_button_selected_hover_color=C.ACCENT,
                                       segmented_button_unselected_color=C.BG4,
                                       text_color=C.TEXT)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Botón en fila 1 (NO expande, siempre visible)
        bottom_frame = ctk.CTkFrame(container, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.lbl_err = ctk.CTkLabel(bottom_frame, text="", font=F(9), text_color=C.ACCENT2)
        self.lbl_err.pack(pady=(0, 4))
        ctk.CTkButton(bottom_frame, text="💾  Guardar cambios", fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(11, "bold"), corner_radius=14, height=42, width=220,
                      command=self._save).pack()

        def _scroll(p):
            sf = ctk.CTkScrollableFrame(p, fg_color="transparent")
            sf.pack(fill="both", expand=True)
            return sf

        # 5 pestañas
        t1 = _scroll(self.tabview.add("⏱ Temporizador"))
        t2 = _scroll(self.tabview.add("⚙ Opciones"))
        t3 = _scroll(self.tabview.add("🎨 Apariencia"))
        t4 = _scroll(self.tabview.add("🏃 Ejercicios"))
        t5 = _scroll(self.tabview.add("🔧 Avanzado"))

        # ════════════════════════════════════════════════════════════════
        # TAB 1: TEMPORIZADOR
        # ════════════════════════════════════════════════════════════════
        self.v_int = ctk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = ctk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = ctk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = ctk.StringVar(value=self.cfg["hora_fin"])
        self.v_pos = ctk.StringVar(value=str(self.cfg["posponer_min"]))
        self.v_meta = ctk.StringVar(value=str(self.cfg["meta_pausas"]))
        self.v_modo = ctk.StringVar(value=self.cfg.get("modo", "normal"))

        card_t1 = _card(t1)
        card_t1.pack(fill="x", pady=(4, 0))
        self._field(card_t1, "Intervalo entre pausas (min)", self.v_int, 0)
        self._field(card_t1, "Duración de la pausa (min)", self.v_dur, 1)
        self._field(card_t1, "Hora inicio (HH:MM)", self.v_ini, 2)
        self._field(card_t1, "Hora fin (HH:MM)", self.v_fin, 3)
        self._field(card_t1, "Minutos para posponer", self.v_pos, 4)
        self._field(card_t1, "Meta de pausas diarias", self.v_meta, 5)

        modo_card = _card(t1)
        modo_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(modo_card, text="Modo de timer", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(8, 4))
        for val, lbl in [("normal", "Normal"), ("pomodoro", "Pomodoro (25/5)")]:
            _radio(modo_card, lbl, self.v_modo, val).pack(anchor="w", padx=14, pady=1)
        ctk.CTkLabel(modo_card, text="Pomodoro: bloques de 25 min trabajo + 5 min pausa",
                     font=F(7), text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 6))

        # ════════════════════════════════════════════════════════════════
        # TAB 2: OPCIONES
        # ════════════════════════════════════════════════════════════════
        opts = _card(t2)
        opts.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(opts, text="General", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_nm = ctk.BooleanVar(value=self.cfg.get("no_molestar", True))
        self.v_fs = ctk.BooleanVar(value=self.cfg.get("fin_de_semana", False))
        self.v_voz = ctk.BooleanVar(value=self.cfg.get("guia_voz", True))
        _checkbox(opts, "No interrumpir si hay pantalla completa", self.v_nm).pack(anchor="w", padx=10, pady=3)
        _checkbox(opts, "Pausar en fin de semana (sáb y dom)", self.v_fs).pack(anchor="w", padx=10, pady=3)
        _checkbox(opts, "Guía por voz durante la pausa", self.v_voz).pack(anchor="w", padx=10, pady=(0, 6))

        agua = _card(t2)
        agua.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(agua, text="💧 Recordatorio de agua", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_agua = ctk.BooleanVar(value=self.cfg.get("agua_activo", True))
        self.v_agua_min = ctk.StringVar(value=str(self.cfg.get("agua_min", 30)))
        _checkbox(agua, "Activar recordatorio de hidratación", self.v_agua).pack(anchor="w", padx=10, pady=3)
        row_agua = ctk.CTkFrame(agua, fg_color="transparent")
        row_agua.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(row_agua, text="Cada cuántos minutos:", font=F(9),
                     text_color=C.TEXT_MUTED).pack(side="left")
        _entry(row_agua, self.v_agua_min, width=60).pack(side="left", padx=8)

        post = _card(t2)
        post.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(post, text="🧘 Recordatorio de postura", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_postura = ctk.BooleanVar(value=self.cfg.get("postura_recordatorio", False))
        self.v_postura_min = ctk.StringVar(value=str(self.cfg.get("postura_intervalo_min", 20)))
        _checkbox(post, "Activar recordatorio de postura", self.v_postura).pack(anchor="w", padx=10, pady=3)
        row_post = ctk.CTkFrame(post, fg_color="transparent")
        row_post.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(row_post, text="Cada cuántos minutos:", font=F(9),
                     text_color=C.TEXT_MUTED).pack(side="left")
        _entry(row_post, self.v_postura_min, width=60).pack(side="left", padx=8)

        gen = _card(t2)
        gen.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(gen, text="Sistema", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_snd = ctk.BooleanVar(value=self.cfg["sonido"])
        self.v_auto = ctk.BooleanVar(value=get_autoarranque())
        _checkbox(gen, "Sonido de alerta al iniciar pausa", self.v_snd).pack(anchor="w", padx=10, pady=3)
        _checkbox(gen, "Iniciar con Windows (autoarranque)", self.v_auto).pack(anchor="w", padx=10, pady=(0, 4))

        idioma_card = _card(t2)
        idioma_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(idioma_card, text="🌍 Idioma", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_idioma = ctk.StringVar(value=self.cfg.get("idioma", "es"))
        for val, lbl in [("es", "Español"), ("en", "English")]:
            _radio(idioma_card, lbl, self.v_idioma, val).pack(anchor="w", padx=10, pady=1)

        # ════════════════════════════════════════════════════════════════
        # TAB 3: APARIENCIA
        # ════════════════════════════════════════════════════════════════
        tema_card = _card(t3)
        tema_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(tema_card, text="🌙 Tema", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_tema = ctk.StringVar(value=self.cfg.get("tema", "oscuro"))
        for val, lbl in [("oscuro", "Oscuro"), ("claro", "Claro")]:
            _radio(tema_card, lbl, self.v_tema, val).pack(anchor="w", padx=14, pady=2)

        accent_card = _card(t3)
        accent_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(accent_card, text="🎨 Color de acento", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_accent = ctk.StringVar(value=self.cfg.get("color_acento", "azul"))
        for val in ("azul", "verde", "morado", "rosa", "naranja", "teal", "rojo"):
            _radio(accent_card, val.capitalize(), self.v_accent, val).pack(anchor="w", padx=14, pady=1)

        fondo_card = _card(t3)
        fondo_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(fondo_card, text="🖼️ Fondo", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_fondo = ctk.StringVar(value=self.cfg.get("fondo", "estandar"))
        for val in ("estandar", "profundo", "gris", "azulado", "blanco"):
            _radio(fondo_card, val.capitalize(), self.v_fondo, val).pack(anchor="w", padx=14, pady=1)

        font_card = _card(t3)
        font_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(font_card, text="🔤 Tamaño de letra", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=10, pady=(8, 4))
        self.v_font = ctk.StringVar(value=self.cfg.get("tamano_letra", "normal"))
        for val in ("pequeno", "normal", "grande", "muy_grande"):
            _radio(font_card, val.replace("_", " ").capitalize(), self.v_font, val).pack(anchor="w", padx=14, pady=1)

        # ════════════════════════════════════════════════════════════════
        # TAB 4: EJERCICIOS
        # ════════════════════════════════════════════════════════════════
        ej_card = _card(t4)
        ej_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(ej_card, text="Marca los ejercicios que quieres incluir:",
                     font=F(9, "bold"), text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.ej_vars: dict[str, ctk.BooleanVar] = {}
        activos: list[str] = self.cfg.get("ejercicios_activos",
                                            [e["id"] for e in EJERCICIOS])
        for ej in EJERCICIOS:
            v = ctk.BooleanVar(value=ej["id"] in activos)
            self.ej_vars[ej["id"]] = v
            r = ctk.CTkFrame(ej_card, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)
            _checkbox(r, f"{ej['icono']} {ej['nombre']}", v).pack(side="left")

        # ════════════════════════════════════════════════════════════════
        # TAB 5: AVANZADO (Modos, Floating, Sonido, Atajos, Logros)
        # ════════════════════════════════════════════════════════════════
        # Modos
        modes_card = _card(t5)
        modes_card.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(modes_card, text="🖥️ Modos de ventana", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_compact = ctk.BooleanVar(value=self.cfg.get("compacto_enabled", False))
        self.v_floating = ctk.BooleanVar(value=self.cfg.get("floating_enabled", False))
        self.v_fs_timer = ctk.BooleanVar(value=self.cfg.get("pantalla_completa", False))
        _checkbox(modes_card, "Modo compacto (mini ventana)", self.v_compact).pack(anchor="w", padx=10, pady=3)
        _checkbox(modes_card, "Timer flotante en escritorio", self.v_floating).pack(anchor="w", padx=10, pady=3)
        _checkbox(modes_card, "Modo pantalla completa", self.v_fs_timer).pack(anchor="w", padx=10, pady=(0, 6))

        # Sonido
        sound_card = _card(t5)
        sound_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(sound_card, text="🔊 Sonido ambiente", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_amb = ctk.StringVar(value=self.cfg.get("sonido_ambiente", "ninguno"))
        for val, lbl in [("ninguno", "Sin sonido"), ("lluvia", "Lluvia"), ("naturaleza", "Naturaleza")]:
            _radio(sound_card, lbl, self.v_amb, val).pack(anchor="w", padx=14, pady=2)

        self.v_sound_pack = ctk.StringVar(value=self.cfg.get("sound_pack_activo", "default"))
        ctk.CTkLabel(sound_card, text="Paquete de sonido:", font=F(9),
                     text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(6, 2))
        for val, lbl in [("default", "Por defecto"), ("nature", "Naturaleza"), ("minimal", "Minimalista")]:
            _radio(sound_card, lbl, self.v_sound_pack, val).pack(anchor="w", padx=14, pady=1)

        # Atajos
        hotkey_card = _card(t5)
        hotkey_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(hotkey_card, text="⌨️ Atajos de teclado", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_hk_next = ctk.StringVar(value=self.cfg.get("hotkey_siguiente", "ctrl+right"))
        self.v_hk_prev = ctk.StringVar(value=self.cfg.get("hotkey_anterior", "ctrl+left"))
        self.v_hk_pause = ctk.StringVar(value=self.cfg.get("hotkey_pausar", "ctrl+space"))
        self.v_hk_skip = ctk.StringVar(value=self.cfg.get("hotkey_saltar", "ctrl+escape"))
        self._field(hotkey_card, "Siguiente paso", self.v_hk_next, 0)
        self._field(hotkey_card, "Paso anterior", self.v_hk_prev, 1)
        self._field(hotkey_card, "Pausar/reanudar", self.v_hk_pause, 2)
        self._field(hotkey_card, "Saltar pausa", self.v_hk_skip, 3)
        ctk.CTkLabel(hotkey_card, text="Ejemplo: ctrl+right, alt+space",
                     font=F(7), text_color=C.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 6))

        # Logros
        logro_card = _card(t5)
        logro_card.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(logro_card, text="🏆 Logros desbloqueados", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        shown = self.cfg.get("logros_mostrados", [])
        for ach in ACHIEVEMENTS:
            unlocked = ach["id"] in shown
            row = ctk.CTkFrame(logro_card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=1)
            icon = ach["icon"] if unlocked else "🔒"
            status = "✅" if unlocked else "⏳"
            ctk.CTkLabel(row, text=f"{icon} {_(ach['key'])} {status}", font=F(9),
                         text_color=C.TEXT if unlocked else C.TEXT_MUTED, anchor="w").pack(side="left")

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
        nuevo_accent = self.v_accent.get()
        nuevo_fondo = self.v_fondo.get()
        if nuevo_tema != self.cfg.get("tema") or nuevo_accent != self.cfg.get("color_acento", "azul") or nuevo_fondo != self.cfg.get("fondo", "estandar"):
            set_theme(nuevo_tema, nuevo_accent, nuevo_fondo)

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
            "guia_voz":           self.v_voz.get(),
            "agua_activo":        self.v_agua.get(),
            "agua_min":           amv,
            "sonido_ambiente":    self.v_amb.get(),
            "tema":               nuevo_tema,
            "modo":               self.v_modo.get(),
            "idioma":             nuevo_idioma,
            "tamano_letra":       self.v_font.get(),
            "color_acento":       nuevo_accent,
            "fondo":              nuevo_fondo,
            # Postura
            "postura_recordatorio": self.v_postura.get(),
            "postura_intervalo_min": int(self.v_postura_min.get() or 20),
            # Modos
            "compacto_enabled":   self.v_compact.get(),
            "floating_enabled":   self.v_floating.get(),
            "pantalla_completa":  self.v_fs_timer.get(),
            # Atajos
            "hotkey_siguiente":   self.v_hk_next.get(),
            "hotkey_anterior":    self.v_hk_prev.get(),
            "hotkey_pausar":      self.v_hk_pause.get(),
            "hotkey_saltar":      self.v_hk_skip.get(),
            # Sonido
            "sound_pack_activo":  self.v_sound_pack.get(),
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
            ctk.CTkLabel(f, text="\u25cf", font=F(12),
                         text_color=color).pack(side="left", padx=4)

    def _step_bienvenida(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_heading"), font=F(16, "bold"),
                     text_color=C.TEXT).pack(pady=(20, 2))
        ctk.CTkLabel(f, text=_("bienvenido"), font=F(10),
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
            ctk.CTkLabel(col, text=titulo, font=F(10, "bold"),
                         text_color=C.TEXT, anchor="w").pack(anchor="w")
            ctk.CTkLabel(col, text=desc, font=F(8),
                         text_color=C.TEXT_MUTED, anchor="w", wraplength=280).pack(anchor="w")
        self._dots(f)
        ctk.CTkButton(f, text=_("next_step"), fg_color=C.ACCENT, text_color=C.BG,
                      font=F(10, "bold"), corner_radius=12,
                      command=self._next).pack(pady=(0, 24))

    def _step_config(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_step1_heading"), font=F(14, "bold"),
                     text_color=C.TEXT).pack(pady=(14, 2))
        ctk.CTkLabel(f, text=_("welcome_step1_info"),
                     font=F(9), text_color=C.TEXT_MUTED).pack(pady=(6, 10))

        card_cfg = _card(f)
        card_cfg.pack(fill="x", padx=24)

        self.v_int = ctk.StringVar(value=str(self.cfg["intervalo_min"]))
        self.v_dur = ctk.StringVar(value=str(self.cfg["duracion_pausa_min"]))
        self.v_ini = ctk.StringVar(value=self.cfg["hora_inicio"])
        self.v_fin = ctk.StringVar(value=self.cfg["hora_fin"])
        self.v_meta = ctk.StringVar(value=str(self.cfg["meta_pausas"]))

        def campo(lbl: str, var: ctk.Variable, row: int) -> None:
            ctk.CTkLabel(card_cfg, text=lbl, font=F(10),
                         text_color=C.TEXT_MUTED, anchor="w").grid(row=row, column=0, sticky="w", padx=14, pady=7)
            _entry(card_cfg, var).grid(row=row, column=1, padx=14, pady=7, sticky="e")

        campo(_("welcome_field_intervalo"), self.v_int, 0)
        campo(_("welcome_field_duracion"),   self.v_dur, 1)
        campo(_("welcome_field_hora_ini"),   self.v_ini, 2)
        campo(_("welcome_field_hora_fin"),   self.v_fin, 3)
        campo(_("welcome_field_meta"),       self.v_meta, 4)

        ctk.CTkLabel(f, text=_("welcome_ej_subheading"), font=F(9, "bold"),
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

        self.lbl_err = ctk.CTkLabel(f, text="", font=F(9), text_color=C.ACCENT2)
        self.lbl_err.pack()
        self._dots(f)
        bf = ctk.CTkFrame(f, fg_color="transparent")
        bf.pack(pady=(0, 20))
        ctk.CTkButton(bf, text=_("back_step"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(10), corner_radius=12,
                      command=self._prev).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=_("next_step"), fg_color=C.ACCENT, text_color=C.BG,
                      font=F(10, "bold"), corner_radius=12,
                      command=self._save_and_next).pack(side="left", padx=4)

    def _step_listo(self) -> None:
        f = self._frame
        ctk.CTkLabel(f, text=_("welcome_step2_heading"), font=F(15, "bold"),
                     text_color=C.TEXT).pack(pady=(20, 2))
        ctk.CTkLabel(f, text=_("welcome_step2_info"),
                     font=F(10), text_color=C.TEXT_MUTED).pack(pady=(12, 14))
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
            ctk.CTkLabel(row, text=lbl, font=F(10),
                         text_color=C.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=val, font=F(10, "bold"),
                         text_color=C.TEXT).pack(side="right")
        ctk.CTkLabel(f, text=_("welcome_step2_tray_info"),
                     font=F(9), text_color=C.TEXT_MUTED).pack(pady=(10, 4))
        self._dots(f)
        ctk.CTkButton(f, text=_("welcome_start"), fg_color=C.GREEN, text_color=C.BG,
                      font=F(11, "bold"), corner_radius=12,
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

        ctk.CTkLabel(main, text=_("uninstall_heading"), font=F(14, "bold"),
                     text_color=C.TEXT).pack(pady=(14, 0))

        ctk.CTkLabel(main, text=_("uninstall_warning"),
                     font=F(9), text_color=C.TEXT_MUTED, justify="center",
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
        self.lbl_estado = ctk.CTkLabel(main, text="", font=F(9), text_color=C.TEXT_MUTED)
        self.lbl_estado.pack(pady=(4, 4))
        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(0, 20))
        ctk.CTkButton(bf, text=_("cancelar"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(10), corner_radius=12,
                      command=self.destroy).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=_("uninstall_btn"), fg_color=C.ACCENT2, text_color=C.BG,
                      font=F(10, "bold"), corner_radius=12,
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
        # Save install_dir before removing registry
        install_dir: str = _get_install_dir_from_registry() or self._app_dir
        try:
            _quitar_registro_desinstalador()
        except Exception:
            pass
        if self.v_carpeta.get():
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


# ═══════════════════════════════════════════════════════════════════════════
# Toast Notification (modern banner)
# ═══════════════════════════════════════════════════════════════════════════

class ToastNotification(ctk.CTkToplevel):
    _counter: int = 0

    def __init__(
        self,
        title: str,
        message: str,
        kind: str = "info",
        duration: int = 3000,
        parent: ctk.CTkBaseClass | None = None,
    ) -> None:
        super().__init__(parent or ctk.CTk())
        ToastNotification._counter += 1
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=C.CARD)
        self.resizable(False, False)

        colors = {"info": C.ACCENT, "exito": C.GREEN, "advertencia": C.YELLOW, "error": "#EF4444"}
        accent = colors.get(kind, C.ACCENT)

        bar = ctk.CTkFrame(self, fg_color=accent, width=4, height=60)
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(8, 14), pady=8)

        icon_map = {"info": "ℹ️", "exito": "✅", "advertencia": "⚠️", "error": "❌"}
        ctk.CTkLabel(
            content, text=f"{icon_map.get(kind, 'ℹ️')}  {title}",
            font=F(10, "bold"), text_color=C.TEXT, anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            content, text=message, font=F(9),
            text_color=C.TEXT_DIM, anchor="w", wraplength=280,
        ).pack(fill="x")

        w, h = 340, 70
        screen_w = self.winfo_screenwidth()
        offset = (ToastNotification._counter % 5) * (h + 8)
        self.geometry(f"{w}x{h}+{screen_w - w - 20}+{20 + offset}")
        self.attributes("-alpha", 0.0)
        for i in range(1, 7):
            self.after(i * 20, lambda v=i / 6: self.attributes("-alpha", min(v, 1.0)))
        self.after(duration, self._close)

    def _close(self) -> None:
        for i in range(6, 0, -1):
            self.after((6 - i) * 20, lambda v=i / 6: self.attributes("-alpha", v))
        self.after(150, self.destroy)


def toast(title: str, message: str, kind: str = "info", duration: int = 3000) -> None:
    ToastNotification(title, message, kind=kind, duration=duration)


# ═══════════════════════════════════════════════════════════════════════════
# Floating Timer (mini widget)
# ═══════════════════════════════════════════════════════════════════════════

class FloatingTimer(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, get_remaining: Callable[[], int],
                 get_paused: Callable[[], bool], on_click: Callable[[], None]) -> None:
        super().__init__(parent)
        self._get_remaining = get_remaining
        self._get_paused = get_paused
        self._on_click = on_click
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1A1A2E")
        self.resizable(False, False)
        self.geometry("140x50")
        self.attributes("-alpha", 0.85)

        self._canvas = Canvas(self, width=140, height=50, bg="#1A1A2E", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Button-1>", lambda e: self._on_click())

        self._drag_data = {"x": 0, "y": 0}
        self._canvas.bind("<ButtonPress-1>", self._start_drag)
        self._canvas.bind("<B1-Motion>", self._on_drag)

        self._update_display()

    def _start_drag(self, event: Any) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event: Any) -> None:
        x = self.winfo_x() + event.x - self._drag_data["x"]
        y = self.winfo_y() + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def _update_display(self) -> None:
        try:
            if not self.winfo_exists():
                return
            remaining = self._get_remaining()
            paused = self._get_paused()
            mins, secs = divmod(max(0, remaining), 60)
            time_str = f"{mins:02d}:{secs:02d}"
            color = C.YELLOW if paused else C.GREEN
            self._canvas.delete("all")
            self._canvas.create_text(70, 15, text=time_str, font=F(16, "bold"), fill=color, tags="time")
            status = "⏸ PAUSED" if paused else "▶ RUNNING"
            self._canvas.create_text(70, 37, text=status, font=F(8), fill=C.TEXT_DIM, tags="status")
            self.after(500, self._update_display)
        except Exception:
            pass

    def destroy(self) -> None:
        super().destroy()


# ═══════════════════════════════════════════════════════════════════════════
# Compact Window (mini mode)
# ═══════════════════════════════════════════════════════════════════════════

class CompactWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, get_remaining: Callable[[], int],
                 get_paused: Callable[[], bool], on_toggle: Callable[[], None],
                 on_next: Callable[[], None], on_skip: Callable[[], None]) -> None:
        super().__init__(parent)
        self._get_remaining = get_remaining
        self._get_paused = get_paused
        self._on_toggle = on_toggle
        self._on_next = on_next
        self._on_skip = on_skip
        self.title("FlowBreak Compact")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("260x100")
        self.resizable(False, False)

        main = ctk.CTkFrame(self, fg_color=C.CARD, corner_radius=12)
        main.pack(fill="both", expand=True, padx=6, pady=6)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(6, 0))
        self._time_label = ctk.CTkLabel(top, text="00:00", font=F(20, "bold"), text_color=C.TEXT)
        self._time_label.pack(side="left")
        self._status_label = ctk.CTkLabel(top, text="▶", font=F(14), text_color=C.GREEN)
        self._status_label.pack(side="right")

        btns = ctk.CTkFrame(main, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=(4, 6))
        ctk.CTkButton(btns, text="⏸/▶", width=40, height=28, font=F(9),
                      fg_color=C.BG3, text_color=C.TEXT, corner_radius=8,
                      command=self._on_toggle).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="⏭", width=40, height=28, font=F(9),
                      fg_color=C.BG3, text_color=C.TEXT, corner_radius=8,
                      command=self._on_next).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="✕", width=40, height=28, font=F(9),
                      fg_color="#EF4444", text_color="#FFFFFF", corner_radius=8,
                      command=self._on_skip).pack(side="right", padx=2)
        ctk.CTkButton(btns, text="🔍", width=40, height=28, font=F(9),
                      fg_color=C.BG3, text_color=C.TEXT, corner_radius=8,
                      command=self._expand).pack(side="right", padx=2)

        self._update_display()

    def _expand(self) -> None:
        self._on_click_main()

    def _on_click_main(self) -> None:
        pass

    def _update_display(self) -> None:
        try:
            if not self.winfo_exists():
                return
            remaining = self._get_remaining()
            paused = self._get_paused()
            mins, secs = divmod(max(0, remaining), 60)
            self._time_label.configure(text=f"{mins:02d}:{secs:02d}")
            self._status_label.configure(text="⏸" if paused else "▶",
                                         text_color=C.YELLOW if paused else C.GREEN)
            self.after(500, self._update_display)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# Fullscreen Timer (presentations)
# ═══════════════════════════════════════════════════════════════════════════

class FullscreenTimer(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, get_remaining: Callable[[], int],
                 get_paused: Callable[[], bool], on_exit: Callable[[], None]) -> None:
        super().__init__(parent)
        self._get_remaining = get_remaining
        self._get_paused = get_paused
        self._on_exit = on_exit
        self.overrideredirect(True)
        self.configure(fg_color="#0B1120")
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self._on_exit())

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        self._canvas = Canvas(self, width=screen_w, height=screen_h, bg="#0B1120", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._update_display()

    def _update_display(self) -> None:
        try:
            if not self.winfo_exists():
                return
            remaining = self._get_remaining()
            paused = self._get_paused()
            mins, secs = divmod(max(0, remaining), 60)
            time_str = f"{mins:02d}:{secs:02d}"
            w = self._canvas.winfo_width()
            h = self._canvas.winfo_height()

            self._canvas.delete("all")

            cx, cy = w // 2, h // 2 - 30
            r = min(w, h) // 4

            self._canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                     outline=C.BG3, width=12, tags="ring_bg")

            total = max(1, remaining + 300)
            pct = remaining / total
            self._canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                    start=90, extent=360 * pct,
                                    outline=C.ACCENT, width=12, style="arc", tags="ring_fg")

            color = C.YELLOW if paused else C.ACCENT
            self._canvas.create_text(cx, cy, text=time_str, font=F(48, "bold"), fill=color, tags="time")

            status = "⏸  PAUSED" if paused else "▶  RUNNING"
            self._canvas.create_text(cx, cy + r + 40, text=status, font=F(16), fill=C.TEXT_DIM, tags="status")

            hint = _("fullscreen_salir")
            self._canvas.create_text(cx, h - 40, text=hint, font=F(12), fill=C.TEXT_MUTED, tags="hint")

            self.after(500, self._update_display)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# Achievements Manager (gamification)
# ═══════════════════════════════════════════════════════════════════════════

ACHIEVEMENTS = [
    {"id": "primera_pausa", "key": "logro_primera_pausa", "icon": "🎯", "cond": lambda s, *_: s["completadas"] >= 1},
    {"id": "5_pausas", "key": "logro_5_pausas", "icon": "⭐", "cond": lambda s, *_: s["completadas"] >= 5},
    {"id": "10_pausas", "key": "logro_10_pausas", "icon": "🏆", "cond": lambda s, *_: s["completadas"] >= 10},
    {"id": "racha_3", "key": "logro_racha_3", "icon": "🔥", "cond": lambda s, *_: s.get("racha", 0) >= 3},
    {"id": "racha_7", "key": "logro_racha_7", "icon": "💎", "cond": lambda s, *_: s.get("racha", 0) >= 7},
    {"id": "racha_30", "key": "logro_racha_30", "icon": "👑", "cond": lambda s, *_: s.get("racha", 0) >= 30},
    {"id": "early_bird", "key": "logro_early_bird", "icon": "🌅",
     "cond": lambda s, h, *_: any(e.get("hora", "")[:2] < "09" for e in h.get("historial", [])) if h else False},
    {"id": "night_owl", "key": "logro_night_owl", "icon": "🦉",
     "cond": lambda s, h, *_: any(e.get("hora", "")[:2] >= "20" for e in h.get("historial", [])) if h else False},
]


def check_achievements(stats: dict, history: dict, shown: list) -> list[dict]:
    new_achievements = []
    for ach in ACHIEVEMENTS:
        if ach["id"] not in shown:
            try:
                if ach["cond"](stats, history):
                    new_achievements.append(ach)
                    shown.append(ach["id"])
            except Exception:
                pass
    return new_achievements


class AchievementsWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, stats: dict, shown: list) -> None:
        super().__init__(parent)
        self.title(_("logros"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("360x500")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="🏆", font=("Segoe UI Emoji", 40), text_color=C.TEXT).pack(pady=(16, 0))
        ctk.CTkLabel(main, text=_("logros"), font=F(16, "bold"), text_color=C.TEXT).pack(pady=(4, 12))

        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12)

        for ach in ACHIEVEMENTS:
            unlocked = ach["id"] in shown
            card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=12,
                                border_width=1, border_color=C.CARD_BORDER if unlocked else C.BG3)
            card.pack(fill="x", pady=4)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)
            icon = ach["icon"] if unlocked else "🔒"
            ctk.CTkLabel(row, text=icon, font=F(18), text_color=C.TEXT).pack(side="left", padx=(0, 10))
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(text_frame, text=_(ach["key"]), font=F(10, "bold" if unlocked else ""),
                         text_color=C.TEXT if unlocked else C.TEXT_MUTED, anchor="w").pack(fill="x")
            status = "✅ Desbloqueado" if unlocked else "⏳ Pendiente"
            ctk.CTkLabel(text_frame, text=status, font=F(8),
                         text_color=C.GREEN if unlocked else C.TEXT_MUTED, anchor="w").pack(fill="x")

        ctk.CTkButton(main, text=_("cerrar"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=120, height=34,
                      command=self.destroy).pack(pady=12)
        self.center()


# ═══════════════════════════════════════════════════════════════════════════
# Custom Exercise Editor
# ═══════════════════════════════════════════════════════════════════════════

class CustomExerciseWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, on_save: Callable[[dict], None],
                 exercise: dict | None = None) -> None:
        super().__init__(parent)
        self._on_save = on_save
        self._exercise = exercise
        self.title(_("workout_crear") if not exercise else "Editar ejercicio")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("400x520")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="✏️" if exercise else "🆕", font=("Segoe UI Emoji", 32),
                     text_color=C.TEXT).pack(pady=(16, 0))
        title = "Editar ejercicio" if exercise else _("workout_crear")
        ctk.CTkLabel(main, text=title, font=F(14, "bold"), text_color=C.TEXT).pack(pady=(4, 12))

        card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14, border_width=1, border_color=C.CARD_BORDER)
        card.pack(fill="x", padx=20)

        self.v_nombre = ctk.StringVar(value=exercise["nombre"] if exercise else "")
        self.v_icono = ctk.StringVar(value=exercise.get("icono", "🧘") if exercise else "🧘")
        self.v_instr = ctk.StringVar(value=exercise.get("instrucciones", "") if exercise else "")
        self.v_pasos = ctk.StringVar(value="\n".join(exercise.get("pasos", [])) if exercise else "")

        for label, var, height in [
            ("Nombre", self.v_nombre, 1),
            ("Icono (emoji)", self.v_icono, 1),
            ("Instrucciones", self.v_instr, 2),
        ]:
            ctk.CTkLabel(card, text=label, font=F(9, "bold"), text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(8, 2))
            ctk.CTkEntry(card, textvariable=var, font=F(10), fg_color=C.BG3, text_color=C.TEXT,
                         border_color=C.BORDER, corner_radius=8, height=28 if height == 1 else 50,
                         width=340).pack(padx=14, pady=(0, 4))

        ctk.CTkLabel(card, text="Pasos (uno por línea, ej: 'Estirar 30 seg')", font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(8, 2))
        ctk.CTkTextbox(card, font=F(10), fg_color=C.BG3, text_color=C.TEXT, height=100,
                       width=340, corner_radius=8).pack(padx=14, pady=(0, 10))
        self._textbox = card.winfo_children()[-1]
        self._textbox.insert("1.0", self.v_pasos.get())

        btns = ctk.CTkFrame(main, fg_color="transparent")
        btns.pack(pady=12)
        ctk.CTkButton(btns, text=_("workout_guardar"), fg_color=C.GREEN, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=130, height=34,
                      command=self._save).pack(side="left", padx=4)
        ctk.CTkButton(btns, text=_("cancelar"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(10), corner_radius=12, width=100, height=34,
                      command=self.destroy).pack(side="left", padx=4)
        self.center()

    def _save(self) -> None:
        nombre = self.v_nombre.get().strip()
        if not nombre:
            toast(_("error"), "Nombre requerido", kind="error")
            return
        pasos_text = self._textbox.get("1.0", "end").strip()
        pasos = [p.strip() for p in pasos_text.split("\n") if p.strip()]
        if not pasos:
            toast(_("error"), "Agrega al menos un paso", kind="error")
            return
        eid = (self._exercise or {}).get("id", f"custom_{nombre.lower().replace(' ', '_')}")
        ejercicio = {
            "id": eid,
            "nombre": nombre,
            "icono": self.v_icono.get().strip() or "🧘",
            "instrucciones": self.v_instr.get().strip(),
            "pasos": pasos,
            "custom": True,
        }
        self._on_save(ejercicio)
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════
# Workout Window (combine exercises into routines)
# ═══════════════════════════════════════════════════════════════════════════

class WorkoutWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, workouts: list[dict],
                 exercises: list[dict], on_save: Callable[[list], None],
                 on_run: Callable[[dict], None]) -> None:
        super().__init__(parent)
        self._workouts = workouts
        self._exercises = exercises
        self._on_save = on_save
        self._on_run = on_run
        self.title(_("workouts"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("420x560")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 8))
        ctk.CTkLabel(header, text="🏋️ " + _("workouts"), font=F(14, "bold"),
                     text_color=C.TEXT).pack(side="left")
        ctk.CTkButton(header, text="+ " + _("workout_crear"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(9, "bold"), corner_radius=10, width=120, height=30,
                      command=self._create).pack(side="right")

        self._scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=12)
        self._refresh_list()

        ctk.CTkButton(main, text=_("cerrar"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(10), corner_radius=12, width=100, height=34,
                      command=self.destroy).pack(pady=10)
        self.center()

    def _refresh_list(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        if not self._workouts:
            ctk.CTkLabel(self._scroll, text=_("workout_vacia"), font=F(11),
                         text_color=C.TEXT_MUTED).pack(pady=20)
            return
        for wo in self._workouts:
            card = ctk.CTkFrame(self._scroll, fg_color=C.CARD, corner_radius=12,
                                border_width=1, border_color=C.CARD_BORDER)
            card.pack(fill="x", pady=4)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)
            ej_names = " → ".join(wo.get("ejercicio_nombres", []))
            ctk.CTkLabel(row, text=f"🏋️  {wo['nombre']}", font=F(10, "bold"),
                         text_color=C.TEXT, anchor="w").pack(fill="x")
            ctk.CTkLabel(row, text=ej_names[:80], font=F(8), text_color=C.TEXT_DIM,
                         anchor="w").pack(fill="x")
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkButton(btn_row, text=_("workout_ejecutar"), fg_color=C.GREEN, text_color="#FFFFFF",
                          font=F(9, "bold"), corner_radius=8, width=100, height=28,
                          command=lambda w=wo: self._run(w)).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="🗑", fg_color="#EF4444", text_color="#FFFFFF",
                          font=F(9), corner_radius=8, width=30, height=28,
                          command=lambda w=wo: self._delete(w)).pack(side="right", padx=2)

    def _create(self) -> None:
        WorkoutEditorWindow(self, self._exercises, self._workouts, self._on_save, self._refresh_list)

    def _run(self, wo: dict) -> None:
        self._on_run(wo)
        self.destroy()

    def _delete(self, wo: dict) -> None:
        self._workouts.remove(wo)
        self._on_save(self._workouts)
        self._refresh_list()


class WorkoutEditorWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, exercises: list[dict],
                 workouts: list[dict], on_save: Callable[[list]],
                 refresh: Callable[[], None]) -> None:
        super().__init__(parent)
        self._exercises = exercises
        self._workouts = workouts
        self._on_save = on_save
        self._refresh = refresh
        self.selected_ids: list[str] = []
        self.title(_("workout_crear"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("400x480")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="📝 " + _("workout_crear"), font=F(14, "bold"),
                     text_color=C.TEXT).pack(pady=(12, 8))

        name_frame = ctk.CTkFrame(main, fg_color="transparent")
        name_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(name_frame, text=_("workout_nombre"), font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w")
        self.v_name = ctk.StringVar()
        ctk.CTkEntry(name_frame, textvariable=self.v_name, font=F(10), fg_color=C.BG3,
                     text_color=C.TEXT, border_color=C.BORDER, corner_radius=8, width=340).pack(fill="x")

        ctk.CTkLabel(main, text=_("workout_agregar_ej"), font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=20, pady=(10, 4))

        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12)
        self._checkboxes: list[tuple[str, ctk.CTkCheckBox]] = []
        for ej in exercises:
            var = ctk.BooleanVar(value=False)
            cb = _checkbox(scroll, f"{ej['icono']}  {ej['nombre']}", var)
            cb.pack(anchor="w", padx=8, pady=2)
            self._checkboxes.append((ej["id"], var))

        def _save_workout():
            name = self.v_name.get().strip()
            if not name:
                toast(_("error"), "Nombre requerido", kind="error")
                return
            ids = [eid for eid, var in self._checkboxes if var.get()]
            if not ids:
                toast(_("error"), "Selecciona al menos un ejercicio", kind="error")
                return
            nombres = []
            for ej in self._exercises:
                if ej["id"] in ids:
                    nombres.append(ej["nombre"])
            wo = {"nombre": name, "ejercicio_ids": ids, "ejercicio_nombres": nombres}
            self._workouts.append(wo)
            self._on_save(self._workouts)
            self._refresh()
            self.destroy()

        btns = ctk.CTkFrame(main, fg_color="transparent")
        btns.pack(pady=10)
        ctk.CTkButton(btns, text=_("workout_guardar"), fg_color=C.GREEN, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=130, height=34,
                      command=_save_workout).pack(side="left", padx=4)
        ctk.CTkButton(btns, text=_("cancelar"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(10), corner_radius=12, width=100, height=34,
                      command=self.destroy).pack(side="left", padx=4)
        self.center()


# ═══════════════════════════════════════════════════════════════════════════
# Tutorial Window (improved onboarding)
# ═══════════════════════════════════════════════════════════════════════════

class TutorialWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, on_complete: Callable[[], None]) -> None:
        super().__init__(parent)
        self._on_complete = on_complete
        self._step = 0
        self.title("Tutorial")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("440x520")

        self._main = ctk.CTkFrame(self, fg_color=C.BG)
        self._main.pack(fill="both", expand=True)
        self._show_step()
        self.center()

    def _show_step(self) -> None:
        for w in self._main.winfo_children():
            w.destroy()

        steps = [
            ("⚙️", _("tutorial_paso1_titulo"), _("tutorial_paso1_desc"),
             [("⏱", "Intervalo de pausas", "Cada cuánto tiempo quieres hacer una pausa"),
              ("🏃", "Ejercicios", "Selecciona los ejercicios que más te gusten")]),
            ("🎨", _("tutorial_paso2_titulo"), _("tutorial_paso2_desc"),
             [("🎨", "Temas", "Cambia entre modo oscuro y claro"),
              ("🔊", "Sonidos", "Elige sonidos de ambiente para relajarte")]),
            ("🚀", _("tutorial_paso3_titulo"), _("tutorial_paso3_desc"),
             [("🏆", "Logros", "Desbloquea logros por ser constante"),
              ("📊", "Estadísticas", "Revisa tu progreso diario")]),
        ]

        icon, title, desc, features = steps[self._step]

        ctk.CTkLabel(self._main, text=icon, font=("Segoe UI Emoji", 48),
                     text_color=C.TEXT).pack(pady=(24, 0))
        ctk.CTkLabel(self._main, text=title, font=F(18, "bold"),
                     text_color=C.TEXT).pack(pady=(8, 4))
        ctk.CTkLabel(self._main, text=desc, font=F(11),
                     text_color=C.TEXT_DIM, wraplength=360, justify="center").pack(pady=(0, 16))

        for feat_icon, feat_title, feat_desc in features:
            feat_card = ctk.CTkFrame(self._main, fg_color=C.CARD, corner_radius=12,
                                     border_width=1, border_color=C.CARD_BORDER)
            feat_card.pack(fill="x", padx=24, pady=3)
            row = ctk.CTkFrame(feat_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)
            ctk.CTkLabel(row, text=feat_icon, font=F(16), text_color=C.TEXT).pack(side="left", padx=(0, 10))
            tf = ctk.CTkFrame(row, fg_color="transparent")
            tf.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(tf, text=feat_title, font=F(10, "bold"), text_color=C.TEXT, anchor="w").pack(fill="x")
            ctk.CTkLabel(tf, text=feat_desc, font=F(8), text_color=C.TEXT_DIM, anchor="w").pack(fill="x")

        btns = ctk.CTkFrame(self._main, fg_color="transparent")
        btns.pack(pady=20)
        if self._step > 0:
            ctk.CTkButton(btns, text=_("back_step"), fg_color=C.BG3, text_color=C.TEXT,
                          font=F(10), corner_radius=12, width=100, height=34,
                          command=self._prev).pack(side="left", padx=4)
        if self._step < len(steps) - 1:
            ctk.CTkButton(btns, text=_("next_step"), fg_color=C.ACCENT, text_color="#FFFFFF",
                          font=F(10, "bold"), corner_radius=12, width=120, height=34,
                          command=self._next).pack(side="left", padx=4)
        else:
            ctk.CTkButton(btns, text=_("tutorial_completar"), fg_color=C.GREEN, text_color="#FFFFFF",
                          font=F(10, "bold"), corner_radius=12, width=120, height=34,
                          command=self._complete).pack(side="left", padx=4)
        ctk.CTkButton(btns, text=_("tutorial_saltar"), fg_color="transparent", text_color=C.TEXT_MUTED,
                      font=F(9), corner_radius=12, width=100, height=34,
                      command=self._complete).pack(side="left", padx=4)

    def _next(self) -> None:
        self._step += 1
        self._show_step()

    def _prev(self) -> None:
        self._step -= 1
        self._show_step()

    def _complete(self) -> None:
        self._on_complete()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════
# Posture Reminder
# ═══════════════════════════════════════════════════════════════════════════

class PostureReminder:
    def __init__(self, app: Any) -> None:
        self._app = app
        self._job: str | None = None
        self._active = False

    def start(self, interval_min: int) -> None:
        self.stop()
        self._active = True
        self._schedule(interval_min)

    def stop(self) -> None:
        self._active = False
        if self._job:
            try:
                self._app.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _schedule(self, interval_min: int) -> None:
        if not self._active:
            return
        ms = interval_min * 60 * 1000
        self._job = self._app.after(ms, self._notify)

    def _notify(self) -> None:
        if not self._active:
            return
        toast(_("postura_recordatorio"), "Corrige tu postura 🧍", kind="info", duration=5000)
        try:
            get_audio_manager().play_alert()
        except Exception:
            pass
        self._schedule(self._app.cfg.get("postura_intervalo_min", 20))


# ═══════════════════════════════════════════════════════════════════════════
# Enhanced Stats Window (weekly/monthly)
# ═══════════════════════════════════════════════════════════════════════════

class StatsWindowEnhanced(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, stats: dict, meta: int,
                 hist_file: str, history: dict | None = None,
                 on_export: Callable | None = None,
                 on_import: Callable | None = None) -> None:
        super().__init__(parent)
        self.title(_("estadisticas"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("440x700")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="📊", font=("Segoe UI Emoji", 36), text_color=C.TEXT).pack(pady=(16, 4))
        ctk.CTkLabel(main, text=_("estadisticas"), font=F(18, "bold"), text_color=C.TEXT).pack(pady=(0, 8))

        # Period selector
        period_frame = ctk.CTkFrame(main, fg_color="transparent")
        period_frame.pack(fill="x", padx=20, pady=(0, 8))
        self._period = ctk.StringVar(value="semana")
        for val, lbl in [("semana", "7 días"), ("mes", "30 días"), ("todo", "Todo")]:
            ctk.CTkButton(period_frame, text=lbl, font=F(9), corner_radius=10,
                          fg_color=C.ACCENT if val == "semana" else C.BG3,
                          text_color="#FFFFFF" if val == "semana" else C.TEXT,
                          width=90, height=28,
                          command=lambda v=val: self._set_period(v)).pack(side="left", padx=3)

        # Stats cards
        total = stats["completadas"] + stats["saltadas"]
        pct = int(stats["completadas"] / total * 100) if total > 0 else 0

        cards_frame = ctk.CTkFrame(main, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20)
        stat_items = [
            ("✅", f"{stats['completadas']}", C.GREEN),
            ("⏭️", str(stats["saltadas"]), C.ACCENT2),
            ("📈", f"{pct}%", C.ACCENT),
            ("🔥", f"{stats.get('racha', 0)}d", C.YELLOW),
        ]
        for i, (icon, val, color) in enumerate(stat_items):
            card = ctk.CTkFrame(cards_frame, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
            card.grid(row=0, column=i, padx=3, pady=4, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=icon, font=F(14), text_color=C.TEXT_DIM).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=val, font=F(16, "bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=["Comp", "Salt", "Éxito", "Racha"][i],
                         font=F(7), text_color=C.TEXT_MUTED).pack(pady=(0, 6))

        # Detail card
        detail_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                   border_width=1, border_color=C.CARD_BORDER)
        detail_card.pack(fill="x", padx=20, pady=(8, 0))
        rows_data = [
            ("Completadas", f"{stats['completadas']} / {meta}", C.GREEN),
            ("Saltadas", str(stats["saltadas"]), C.ACCENT2),
            ("Tasa de éxito", f"{pct}%", C.ACCENT),
            ("Racha", f"{stats.get('racha', 0)} días", C.YELLOW),
        ]
        for i, (label, val, color) in enumerate(rows_data):
            r = ctk.CTkFrame(detail_card, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(r, text=label, font=F(9), text_color=C.TEXT_DIM, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=val, font=F(10, "bold"), text_color=color).pack(side="right")
            if i < len(rows_data) - 1:
                ctk.CTkFrame(detail_card, fg_color=C.CARD_BORDER, height=1).pack(fill="x", padx=14)

        # Weekly chart
        if history:
            chart_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                      border_width=1, border_color=C.CARD_BORDER)
            chart_card.pack(fill="x", padx=20, pady=(8, 0))
            ctk.CTkLabel(chart_card, text="📅  " + _("ultimos_7_dias"), font=F(10, "bold"),
                         text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(10, 4))
            _dibujar_grafico(chart_card, history, meta)

        # Buttons
        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(10, 12))
        if on_export:
            ctk.CTkButton(bf, text="📥  " + _("exportar_stats"), fg_color=C.BG3, text_color=C.TEXT,
                          font=F(9), corner_radius=12, width=130, height=30,
                          command=on_export).pack(side="left", padx=3)
        if on_import:
            ctk.CTkButton(bf, text="📤  " + _("importar_stats"), fg_color=C.BG3, text_color=C.TEXT,
                          font=F(9), corner_radius=12, width=130, height=30,
                          command=on_import).pack(side="left", padx=3)
        ctk.CTkButton(bf, text=_("cerrar"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=100, height=30,
                      command=self.destroy).pack(side="left", padx=3)
        self.center()

    def _set_period(self, period: str) -> None:
        self._period.set(period)
        toast(_("toast_info"), f"Período: {period}", kind="info")


# ═══════════════════════════════════════════════════════════════════════════
# FLOWBUDDY - Mascota Virtual
# ═══════════════════════════════════════════════════════════════════════════

class FlowBuddyWidget(ctk.CTkFrame):
    """Widget animado de la mascota que se muestra en la ventana principal."""

    def __init__(self, parent: ctk.CTkBaseClass, pet_state: dict) -> None:
        super().__init__(parent, fg_color=C.CARD, corner_radius=16,
                         border_width=2, border_color=C.ACCENT, height=100)
        self._state = pet_state
        self._parent = parent
        self._x = 30.0
        self._dx = 1.5
        self._frame = 0
        self.pack_propagate(False)
        self._build()
        self._animate()

    def _build(self) -> None:
        self._greeting = ctk.CTkLabel(
            self, text="🐾 ¡Hola! Soy FlowBuddy, tu compañero de descansos",
            font=F(12, "bold"), text_color=C.ACCENT, anchor="w",
        )
        self._greeting.pack(fill="x", padx=16, pady=(10, 2))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 8))

        left = ctk.CTkFrame(bottom, fg_color="transparent")
        left.pack(side="left", fill="y")

        self._mood_label = ctk.CTkLabel(left, text="", font=F(10), text_color=C.TEXT_DIM, anchor="w")
        self._mood_label.pack(anchor="w")

        bars = ctk.CTkFrame(left, fg_color="transparent")
        bars.pack(anchor="w", pady=(4, 0))
        for key, icon, color in [("energia", "⚡", C.GREEN), ("felicidad", "😊", C.YELLOW)]:
            row = ctk.CTkFrame(bars, fg_color="transparent")
            row.pack(anchor="w", pady=1)
            ctk.CTkLabel(row, text=icon, font=F(9), width=16).pack(side="left")
            bar = ctk.CTkProgressBar(row, width=100, height=6, corner_radius=3,
                                     fg_color=C.BG3, progress_color=color)
            bar.pack(side="left", padx=4)
            bar.set(self._state.get(key, 100) / 100)
            setattr(self, f"_bar_{key}", bar)

        self._canvas = Canvas(bottom, width=180, height=70, bg=C.CARD, highlightthickness=0)
        self._canvas.pack(side="right", padx=(0, 4))

        self._update_mood()

    def _draw_pet(self, x: float, y: float) -> None:
        self._canvas.delete("pet")
        e = self._state.get("energia", 100)
        h = self._state.get("felicidad", 100)

        import math
        bob = math.sin(self._frame * 0.12) * 3

        self._canvas.create_oval(x - 20, y + 20, x + 20, y + 28,
                                  fill="#22222240", outline="", tags="pet")

        if e > 70:
            body = C.GREEN
        elif e > 40:
            body = C.YELLOW
        else:
            body = "#EF4444"

        self._canvas.create_oval(x - 16, y - 8 + bob, x + 16, y + 16 + bob,
                                  fill=body, outline="", width=0, tags="pet")
        self._canvas.create_oval(x - 14, y - 22 + bob, x - 4, y - 6 + bob,
                                  fill=body, outline="", tags="pet")
        self._canvas.create_oval(x - 4, y - 26 + bob, x + 4, y - 8 + bob,
                                  fill=body, outline="", tags="pet")
        self._canvas.create_oval(x + 4, y - 22 + bob, x + 14, y - 6 + bob,
                                  fill=body, outline="", tags="pet")

        eye_y = y - 2 + bob
        if e > 70 and h > 70:
            self._canvas.create_oval(x - 10, eye_y - 5, x - 2, eye_y + 3, fill="white", outline="", tags="pet")
            self._canvas.create_oval(x + 2, eye_y - 5, x + 10, eye_y + 3, fill="white", outline="", tags="pet")
            self._canvas.create_oval(x - 8, eye_y - 3, x - 3, eye_y + 1, fill="#1a1a2e", tags="pet")
            self._canvas.create_oval(x + 3, eye_y - 3, x + 8, eye_y + 1, fill="#1a1a2e", tags="pet")
            self._canvas.create_oval(x - 6, eye_y - 4, x - 4, eye_y - 2, fill="white", tags="pet")
            self._canvas.create_oval(x + 5, eye_y - 4, x + 7, eye_y - 2, fill="white", tags="pet")
            self._canvas.create_arc(x - 8, eye_y + 4, x + 8, eye_y + 14,
                                     start=200, extent=140, style="arc", outline="#1a1a2e", width=2, tags="pet")
        elif e > 40:
            self._canvas.create_oval(x - 7, eye_y - 3, x - 3, eye_y + 1, fill="#1a1a2e", tags="pet")
            self._canvas.create_oval(x + 3, eye_y - 3, x + 7, eye_y + 1, fill="#1a1a2e", tags="pet")
        else:
            self._canvas.create_line(x - 8, eye_y, x - 3, eye_y, fill="#1a1a2e", width=2, tags="pet")
            self._canvas.create_line(x + 3, eye_y, x + 8, eye_y, fill="#1a1a2e", width=2, tags="pet")

        leg_off = 4 if self._frame % 16 < 8 else -4
        self._canvas.create_oval(x - 9 + leg_off, y + 12 + bob, x - 3 + leg_off, y + 22 + bob,
                                  fill=body, outline="", tags="pet")
        self._canvas.create_oval(x + 3 - leg_off, y + 12 + bob, x + 9 - leg_off, y + 22 + bob,
                                  fill=body, outline="", tags="pet")

        if e > 70:
            note_x = x + 22 + math.sin(self._frame * 0.1) * 4
            note_y = y - 24 + math.cos(self._frame * 0.15) * 4
            self._canvas.create_text(note_x, note_y, text="♪", font=F(12), fill=C.GREEN, tags="pet")
            note_x2 = x - 22 + math.sin(self._frame * 0.12 + 1) * 3
            note_y2 = y - 20 + math.cos(self._frame * 0.13 + 2) * 3
            self._canvas.create_text(note_x2, note_y2, text="♫", font=F(10), fill=C.ACCENT, tags="pet")
        elif e < 30:
            self._canvas.create_text(x + 20, y - 20, text="z", font=F(11), fill=C.ACCENT2, tags="pet")
            self._canvas.create_text(x + 28, y - 28, text="z", font=F(9), fill=C.ACCENT2, tags="pet")

    def _animate(self) -> None:
        try:
            if not self.winfo_exists():
                return
            self._frame += 1
            self._x += self._dx
            if self._x > 156:
                self._dx = -abs(self._dx)
            elif self._x < 24:
                self._dx = abs(self._dx)
            self._draw_pet(self._x, 42)
            self.after(60, self._animate)
        except Exception:
            pass

    def _update_mood(self) -> None:
        e = self._state.get("energia", 100)
        h = self._state.get("felicidad", 100)
        if e > 70 and h > 70:
            text, color = "😊 ¡Feliz y listo para ayudarte!", C.GREEN
        elif e > 50:
            text, color = "😐 Un poco cansado...", C.YELLOW
        elif e > 25:
            text, color = "😟 Necesita descansar pronto", C.ACCENT2
        else:
            text, color = "😴 ¡Agotado! Haz una pausa ya", "#EF4444"
        self._mood_label.configure(text=text, text_color=color)

    def update_state(self, state: dict) -> None:
        self._state = state
        for key in ("energia", "felicidad"):
            bar = getattr(self, f"_bar_{key}", None)
            if bar:
                bar.set(state.get(key, 100) / 100)
        self._update_mood()




class FlowBuddyWindow(CenteredWindow):
    """Ventana ampliada de la mascota con interacciones."""

    def __init__(self, parent: ctk.CTkBaseClass, pet_state: dict,
                 on_feed: Callable[[], None] | None = None,
                 on_play: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self._state = pet_state
        self.title("🐾 FlowBuddy")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("380x520")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        # Avatar grande
        self._canvas = Canvas(main, width=160, height=160, bg=C.BG, highlightthickness=0)
        self._canvas.pack(pady=(16, 4))
        self._draw_pet(80, 80)

        # Nombre y estado
        ctk.CTkLabel(main, text=pet_state.get("nombre", "FlowBuddy"),
                     font=F(18, "bold"), text_color=C.TEXT).pack()
        self._mood_lbl = ctk.CTkLabel(main, text="", font=F(11), text_color=C.TEXT_DIM)
        self._mood_lbl.pack(pady=(2, 8))

        # Barras de estado
        bars_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                 border_width=1, border_color=C.CARD_BORDER)
        bars_card.pack(fill="x", padx=20)

        self._bars: dict[str, ctk.CTkProgressBar] = {}
        for key, label, color in [("energia", "⚡ Energía", C.GREEN),
                                   ("felicidad", "😊 Felicidad", C.YELLOW),
                                   ("salud", "❤️ Salud", "#EF4444")]:
            row = ctk.CTkFrame(bars_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(row, text=label, font=F(9), text_color=C.TEXT_DIM, width=90, anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row, width=160, height=8, corner_radius=4,
                                     fg_color=C.BG3, progress_color=color)
            bar.pack(side="left", padx=8)
            bar.set(pet_state.get(key, 100) / 100)
            self._bars[key] = bar
            ctk.CTkLabel(row, text=f"{pet_state.get(key, 100)}%", font=F(9, "bold"),
                         text_color=color, width=35).pack(side="right")

        # Nivel y XP
        level_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                  border_width=1, border_color=C.CARD_BORDER)
        level_card.pack(fill="x", padx=20, pady=(8, 0))
        level = pet_state.get("nivel", 1)
        xp = pet_state.get("xp", 0)
        xp_next = pet_state.get("xp_siguiente", 100)
        ctk.CTkLabel(level_card, text=f"🎮 Nivel {level}  ·  {xp}/{xp_next} XP",
                     font=F(10, "bold"), text_color=C.ACCENT).pack(pady=8)

        # Botones de interacción
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="🍖 Alimentar", fg_color=C.GREEN, text_color="#FFFFFF",
                      font=F(9, "bold"), corner_radius=12, width=100, height=34,
                      command=on_feed).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="🎮 Jugar", fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(9, "bold"), corner_radius=12, width=100, height=34,
                      command=on_play).pack(side="left", padx=4)

        # Frases del pet
        phrases = self._get_phrases()
        ctk.CTkLabel(main, text=f"💬 \"{random.choice(phrases)}\"",
                     font=F(9), text_color=C.TEXT_MUTED, wraplength=320).pack(pady=(4, 12))

        ctk.CTkButton(main, text=_("cerrar"), fg_color=C.BG3, text_color=C.TEXT,
                      font=F(9), corner_radius=12, width=100, height=30,
                      command=self.destroy).pack(pady=(0, 12))
        self.center()

    def _draw_pet(self, cx: int, cy: int) -> None:
        e = self._state.get("energia", 100)
        if e > 70:
            eyes, mouth = "◕ ◕", "ω"
        elif e > 40:
            eyes, mouth = "• •", "─"
        else:
            eyes, mouth = "− −", "ᴖ"

        self._canvas.create_text(cx, cy - 30, text="🐾", font=("Segoe UI Emoji", 48))
        self._canvas.create_text(cx, cy + 20, text=eyes, font=F(14), fill=C.TEXT)
        self._canvas.create_text(cx, cy + 42, text=mouth, font=F(12), fill=C.TEXT)

    def _get_phrases(self) -> list[str]:
        e = self._state.get("energia", 100)
        if e > 70:
            return ["¡Estoy listo para todo!", "Me siento genial", "¡Vamos a trabajar!"]
        elif e > 40:
            return ["Un cafecito no estaría mal...", "¿Ya descansaste?", "Necesito un respiro"]
        else:
            return ["¡Ayuda! Estoy agotado", "Por favor, haz una pausa", "No doy más..."]

    def update_state(self, state: dict) -> None:
        self._state = state
        for key, bar in self._bars.items():
            bar.set(state.get(key, 100) / 100)


# ═══════════════════════════════════════════════════════════════════════════
# AI INSIGHTS - Ventana de análisis inteligente
# ═══════════════════════════════════════════════════════════════════════════

class AIInsightsWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, insights: dict) -> None:
        super().__init__(parent)
        self.title("🤖 Insights IA")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("420x560")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="🤖", font=("Segoe UI Emoji", 40), text_color=C.TEXT).pack(pady=(16, 0))
        ctk.CTkLabel(main, text="Análisis Inteligente", font=F(16, "bold"), text_color=C.TEXT).pack(pady=(4, 12))

        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12)

        # Patrón de productividad
        prod = insights.get("productividad", {})
        prod_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                 border_width=1, border_color=C.CARD_BORDER)
        prod_card.pack(fill="x", pady=4)
        ctk.CTkLabel(prod_card, text="📊 Patrón de productividad", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        peak = prod.get("hora_pico", "N/A")
        ctk.CTkLabel(prod_card, text=f"Hora pico: {peak}", font=F(9),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12)
        avg = prod.get("promedio_pausas", 0)
        ctk.CTkLabel(prod_card, text=f"Promedio pausas/día: {avg:.1f}", font=F(9),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(0, 8))

        # Intervalo óptimo
        opt_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
        opt_card.pack(fill="x", pady=4)
        ctk.CTkLabel(opt_card, text="🎯 Intervalo óptimo sugerido", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        opt = insights.get("intervalo_optimo", 45)
        ctk.CTkLabel(opt_card, text=f"IA recomienda: cada {opt} minutos", font=F(9),
                     text_color=C.ACCENT).pack(anchor="w", padx=12, pady=(0, 8))

        # Predicción de racha
        pred_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                 border_width=1, border_color=C.CARD_BORDER)
        pred_card.pack(fill="x", pady=4)
        ctk.CTkLabel(pred_card, text="🔥 Predicción de racha", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        streak = insights.get("prediccion_racha", "Media")
        streak_color = C.GREEN if "Alta" in streak else (C.YELLOW if "Media" in streak else C.ACCENT2)
        ctk.CTkLabel(pred_card, text=f"Probabilidad de mantener racha: {streak}", font=F(9),
                     text_color=streak_color).pack(anchor="w", padx=12, pady=(0, 8))

        # Fatiga
        fat_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
        fat_card.pack(fill="x", pady=4)
        ctk.CTkLabel(fat_card, text="😴 Análisis de fatiga", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        fatigue = insights.get("nivel_fatiga", "Normal")
        fat_color = C.GREEN if fatigue == "Bajo" else (C.YELLOW if fatigue == "Normal" else "#EF4444")
        ctk.CTkLabel(fat_card, text=f"Nivel de fatiga: {fatigue}", font=F(9),
                     text_color=fat_color).pack(anchor="w", padx=12, pady=(0, 8))

        # Recomendaciones
        rec_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
        rec_card.pack(fill="x", pady=4)
        ctk.CTkLabel(rec_card, text="💡 Recomendaciones", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        for rec in insights.get("recomendaciones", []):
            ctk.CTkLabel(rec_card, text=f"• {rec}", font=F(9),
                         text_color=C.TEXT_DIM, wraplength=360, anchor="w").pack(anchor="w", padx=12, pady=1)
        ctk.CTkFrame(rec_card, fg_color="transparent").pack(pady=(0, 8))

        ctk.CTkButton(main, text=_("cerrar"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=100, height=34,
                      command=self.destroy).pack(pady=12)
        self.center()


# ═══════════════════════════════════════════════════════════════════════════
# AI ENGINE - Motor de análisis adaptativo
# ═══════════════════════════════════════════════════════════════════════════

class AIEngine:
    """Motor de IA que analiza patrones y sugiere configuración óptima."""

    def __init__(self, stats: dict, config: dict) -> None:
        self._stats = stats
        self._config = config

    def analyze(self) -> dict:
        insights: dict[str, Any] = {}

        # Productividad por hora
        hourly: dict[int, int] = {}
        for entry in self._stats.get("historial", []):
            if entry.get("estado") == "completada":
                try:
                    h = int(entry["hora"].split(":")[0])
                    hourly[h] = hourly.get(h, 0) + 1
                except (ValueError, IndexError):
                    pass

        if hourly:
            peak_hour = max(hourly, key=hourly.get)
            insights["productividad"] = {
                "hora_pico": f"{peak_hour}:00 - {peak_hour + 1}:00",
                "horas_activas": sorted(hourly.keys()),
                "promedio_pausas": sum(self._stats.get("historial", []).__len__()) / max(1, 7),
            }
        else:
            insights["productividad"] = {
                "hora_pico": "Sin datos aún",
                "horas_activas": [],
                "promedio_pausas": 0,
            }

        # Intervalo óptimo
        completadas = self._stats.get("completadas", 0)
        racha = self._stats.get("racha", 0)
        if completadas > 10 and racha > 3:
            optimal = max(25, min(60, 45 - (racha * 2)))
        else:
            optimal = self._config.get("intervalo_min", 45)
        insights["intervalo_optimo"] = optimal

        # Predicción de racha
        if racha >= 7:
            streak_pred = "Alta (90%+)"
        elif racha >= 3:
            streak_pred = "Media (60-80%)"
        else:
            streak_pred = "Baja (<50%)"
        insights["prediccion_racha"] = streak_pred

        # Nivel de fatiga
        recent = self._stats.get("historial", [])[-5:]
        skipped = sum(1 for e in recent if e.get("estado") == "saltada")
        if skipped >= 3:
            fatigue = "Alto - Necesitas más descansos"
        elif skipped >= 1:
            fatigue = "Normal"
        else:
            fatigue = "Bajo - Buen equilibrio"
        insights["nivel_fatiga"] = fatigue

        # Recomendaciones
        recs = []
        if completadas < 3:
            recs.append("Intenta completar al menos 3 pausas diarias")
        if racha < 2:
            recs.append("La constancia es clave: intenta no romper tu racha")
        if skipped > completadas:
            recs.append("Estás saltando muchas pausas, considera reducir el intervalo")
        if hourly:
            peak = max(hourly, key=hourly.get)
            if peak < 10:
                recs.append("Eres más productivo en la mañana, aprovecha eso")
        if not recs:
            recs.append("¡Excelente! Sigue manteniendo tus hábitos saludables")
        insights["recomendaciones"] = recs

        return insights

    def suggest_interval(self) -> int:
        """Sugiere intervalo óptimo basado en análisis de IA."""
        insights = self.analyze()
        return insights.get("intervalo_optimo", self._config.get("intervalo_min", 45))
