"""FlowBuddy - Virtual Pet mascot."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from tkinter import Canvas

import customtkinter as ctk

from pausa_activa.constants import C, F
from pausa_activa.windows._base import CenteredWindow


class FlowBuddyWidget(ctk.CTkFrame):
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

        self._canvas = Canvas(main, width=160, height=160, bg=C.BG, highlightthickness=0)
        self._canvas.pack(pady=(16, 4))
        self._draw_pet(80, 80)

        ctk.CTkLabel(main, text=pet_state.get("nombre", "FlowBuddy"),
                     font=F(18, "bold"), text_color=C.TEXT).pack()
        self._mood_lbl = ctk.CTkLabel(main, text="", font=F(11), text_color=C.TEXT_DIM)
        self._mood_lbl.pack(pady=(2, 8))

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

        level_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                  border_width=1, border_color=C.CARD_BORDER)
        level_card.pack(fill="x", padx=20, pady=(8, 0))
        level = pet_state.get("nivel", 1)
        xp = pet_state.get("xp", 0)
        xp_next = pet_state.get("xp_siguiente", 100)
        ctk.CTkLabel(level_card, text=f"🎮 Nivel {level}  ·  {xp}/{xp_next} XP",
                     font=F(10, "bold"), text_color=C.ACCENT).pack(pady=8)

        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="🍖 Alimentar", fg_color=C.GREEN, text_color="#FFFFFF",
                      font=F(9, "bold"), corner_radius=12, width=100, height=34,
                      command=on_feed).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="🎮 Jugar", fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(9, "bold"), corner_radius=12, width=100, height=34,
                      command=on_play).pack(side="left", padx=4)

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
