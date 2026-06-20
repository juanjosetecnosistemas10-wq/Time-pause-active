"""BreakWindow — step-by-step exercise with animations."""

from __future__ import annotations

import math
import re
import threading
from collections.abc import Callable
from tkinter import Canvas
from typing import Any

import customtkinter as ctk

from pausa_activa.constants import (
    C,
    F,
    _,
    darken_color,
    get_random_phrase,
    log,
)
from pausa_activa.windows._base import CenteredWindow, get_audio_manager


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

        prep_sec = 10
        min_ex = 10
        min_total = prep_sec + min_ex
        num = self._num_steps

        ex_times = []
        for paso in pasos:
            ex_times.append(self._parse_step_time(paso))

        if any(t is not None for t in ex_times):
            step_durs = []
            for t in ex_times:
                if t is not None:
                    step_durs.append(prep_sec + t)
                else:
                    step_durs.append(min_total)
            total_from_desc = sum(step_durs)
            if total_from_desc < duracion_sec:
                extra = duracion_sec - total_from_desc
                idxs = [i for i, t in enumerate(ex_times) if t is None]
                if idxs:
                    per = extra // len(idxs)
                    for i in idxs:
                        step_durs[i] += per
        else:
            total_min = num * min_total
            actual = max(total_min, duracion_sec)
            avg = actual // num
            step_durs = [avg] * num
            if num > 1 and avg >= min_total + 5:
                step_durs[0] -= 5
                step_durs[-1] += 5
        self._step_durations: list[int] = step_durs
        self._prep_duration: int = prep_sec
        self.remaining: int = sum(step_durs)
        self._duracion_original: int = self.remaining
        self._current_step: int = 0
        self._step_remaining: int = step_durs[0]
        self._in_prep: bool = True

        self._ambient_sonido: str = sonido_ambiente
        self._showing_presentation: bool = True
        self._showing_summary: bool = False
        self._guia_voz: bool = guia_voz
        self._step_completed_count: int = 0
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

        self._anim_canvas = Canvas(
            main, width=220, height=180,
            bg=C.BG, highlightthickness=0,
        )
        self._anim_canvas.pack(pady=(4, 0))

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
        return math.sin(t * freq * 2 * math.pi)

    def _dibujar_mano(self, canvas: Canvas, w: int, h: int, step: int, hp: float) -> None:
        canvas.delete("all")
        self._dibujar_figura(canvas, w, h, torso_lean=10 * hp)

    def _dibujar_ojo(self, canvas: Canvas, w: int, h: int, sp: float) -> None:
        canvas.delete("all")
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
                o = self._osc(sp, 3)
                if self._current_step == 0:
                    sq = 0.2 * self._osc(sp, 3)
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
                    a = 160 * self._osc(sp, 3)
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
                    hp = self._osc(sp, 3)
                elif self._current_step == 1:
                    hp = self._osc(sp, 3)
                else:
                    hp = sp
                self._dibujar_mano(canvas, w, h, self._current_step, hp)
            elif eid == "sentad":
                o = self._osc(sp, 3)
                if self._current_step == 0:
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-10, arm_r_angle=10, torso_lean=sway)
                elif self._current_step == 1:
                    sq = 0.8 * o
                    lean_fwd = 15 * o
                    self._dibujar_figura(canvas, w, h, squat=sq, torso_lean=lean_fwd,
                                          arm_l_angle=-80*o, arm_r_angle=80*o,
                                          leg_l_angle=50*o, leg_r_angle=-50*o)
                else:
                    phase2 = sp * 6.283 * 4
                    lift = max(0, math.sin(phase2)) * 0.6
                    self._dibujar_figura(canvas, w, h, squat=lift, torso_lean=sway+5*math.sin(phase2),
                                          arm_l_angle=-30*math.sin(phase2), arm_r_angle=30*math.sin(phase2),
                                          leg_l_angle=40*math.sin(phase2), leg_r_angle=-40*math.sin(phase2))
            elif eid == "caminar":
                phase = sp * 6.283 * 6
                bounce = 0.1 * abs(math.sin(phase))
                leg_l = 30*math.sin(phase)-5
                leg_r = -30*math.sin(phase)+5
                self._dibujar_figura(canvas, w, h,
                                      leg_l_angle=leg_l, leg_r_angle=leg_r,
                                      arm_l_angle=-35*math.sin(phase), arm_r_angle=35*math.sin(phase),
                                      squat=bounce, torso_lean=sway)
            elif eid == "postura":
                o = self._osc(sp, 2)
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
                    leg_swing = 20 * math.sin(sp * 12.566)
                    self._dibujar_figura(canvas, w, h, leg_l_angle=5, leg_r_angle=leg_swing,
                                          arm_l_angle=-25, arm_r_angle=25, torso_lean=sway)
                else:
                    leg_swing = 20 * math.cos(sp * 12.566)
                    self._dibujar_figura(canvas, w, h, leg_l_angle=leg_swing, leg_r_angle=5,
                                          arm_l_angle=-25, arm_r_angle=25, torso_lean=sway)
            elif eid == "yoga":
                if self._current_step == 0:
                    a = 30 + 40 * self._osc(sp, 2)
                    self._dibujar_figura(canvas, w, h, arm_l_angle=-a, arm_r_angle=a,
                                          squat=0.15, torso_lean=sway)
                elif self._current_step == 1:
                    o = self._osc(sp, 2)
                    bend = 70 * o
                    arm_bend = 90 * o
                    self._dibujar_figura(canvas, w, h, torso_lean=bend + sway,
                                          arm_l_angle=-arm_bend, arm_r_angle=arm_bend,
                                          squat=0.3*o)
                else:
                    twist = 40 * math.sin(sp * 6.283)
                    self._dibujar_figura(canvas, w, h, torso_lean=twist + sway,
                                          arm_l_angle=-60, arm_r_angle=60,
                                          squat=0.2)
            elif eid == "visual":
                self._dibujar_ojo(canvas, w, h, sp)
            elif eid == "respira":
                self._dibujar_respiracion(canvas, w, h)
            else:
                self._dibujar_figura(canvas, w, h, torso_lean=sway)

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
        if self._current_step + 1 < self._num_steps:
            self._last_step = self._current_step
            self._current_step += 1
            self._step_remaining = self._current_step_duration
            self._step_completed_count = self._current_step
            self._in_prep = True
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

        frase = get_random_phrase()
        ctk.CTkLabel(
            main, text=f"💬  {frase}", font=F(10),
            text_color=C.TEXT_MUTED, wraplength=340, justify="center",
        ).pack(pady=(16, 12))

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

    def destroy(self) -> None:
        get_audio_manager().stop_ambient()
        super().destroy()
