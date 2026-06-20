"""Workout Window and editor."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.windows._base import CenteredWindow, _checkbox
from pausa_activa.windows._toast import toast


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
