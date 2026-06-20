"""Custom Exercise Editor."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.windows._base import CenteredWindow
from pausa_activa.windows._toast import toast


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
