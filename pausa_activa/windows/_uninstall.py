"""UninstallWindow."""

from __future__ import annotations

import os
from collections.abc import Callable

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.installer import (
    _eliminar_accesos_directos,
    _get_install_dir_from_registry,
    _programar_borrado_carpeta,
    _quitar_registro_desinstalador,
)
from pausa_activa.windows._base import CenteredWindow, _card, _checkbox, set_autoarranque


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
