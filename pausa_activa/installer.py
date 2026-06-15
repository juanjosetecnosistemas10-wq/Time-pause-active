"""Instalador, desinstalador y helpers del sistema."""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import tempfile
import tkinter as tk
import tkinter.messagebox as mb
import winreg
from tkinter import ttk
from typing import Callable

import customtkinter as ctk

from pausa_activa.constants import (
    C, APP_DISPLAY, APP_NAME, INSTALL_DIR_REG, _, log, center_window, darken_color, F,
)


def _crear_acceso_directo(target: str, lnk_path: str, icon: str = "") -> None:
    target_safe = target.replace('"', '`"')
    lnk_safe = lnk_path.replace('"', '`"')
    icon_safe = (icon if icon else "").replace('"', '`"')
    ps: list[str] = [
        "powershell", "-NoProfile", "-Command",
        "param($target,$lnk,$icon)\n"
        "$ws=New-Object -ComObject WScript.Shell\n"
        "$s=$ws.CreateShortcut($lnk)\n"
        "$s.TargetPath=$target\n"
        "$s.WorkingDirectory=[System.IO.Path]::GetDirectoryName($target)\n"
        "if($icon){$s.IconLocation=$icon}\n"
        "$s.Save()",
        "-target", target_safe,
        "-lnk", lnk_safe,
        "-icon", icon_safe,
    ]
    subprocess.run(ps, capture_output=True, creationflags=0x08000000)


def _validar_install_dir(install_dir: str) -> tuple[bool, str]:
    if not install_dir:
        return False, _("install_err_empty")
    if ".." in install_dir.split(os.sep):
        return False, _("install_err_traversal")
    try:
        os.path.abspath(install_dir)
    except Exception:
        return False, _("install_err_chars")
    return True, ""


def _registrar_instalacion(install_dir: str, exe_path: str, icon_path: str = "") -> None:
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, INSTALL_DIR_REG)
    try:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{exe_path}" --uninstall')
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path or exe_path)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_DISPLAY)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    finally:
        winreg.CloseKey(key)


def _get_install_dir_from_registry() -> str:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, INSTALL_DIR_REG, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
        return val
    except Exception:
        return ""


def _is_installed() -> bool:
    return bool(_get_install_dir_from_registry())


def _eliminar_accesos_directos(errores: list[str]) -> None:
    lugares: list[str] = []
    try:
        buf = ctypes.create_unicode_buffer(260)
        for csidl in (0x10, 0x02):
            if ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf) == 0:
                lugares.append(buf.value)
    except Exception:
        pass
    for var in ("USERPROFILE", "PUBLIC"):
        base = os.environ.get(var, "")
        if base:
            lugares.append(os.path.join(base, "Desktop"))
            lugares.append(os.path.join(base, "AppData", "Roaming",
                                        "Microsoft", "Windows", "Start Menu", "Programs"))
    for carpeta in lugares:
        for nombre in ("FlowBreak.lnk",):
            ruta = os.path.join(carpeta, nombre)
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
            except Exception as e:
                errores.append(f"Acceso directo {nombre}: {e}")


def _programar_borrado_carpeta(folder: str) -> None:
    pid: int = os.getpid()
    bat: str = os.path.join(tempfile.gettempdir(), "pa_cleanup.bat")
    folder_safe = folder.replace('"', '`"')
    with open(bat, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write(":loop\n")
        f.write(f'tasklist /fi "PID eq {pid}" 2>nul | find "{pid}" >nul 2>&1\n')
        f.write("if %errorlevel%==0 (\n")
        f.write("  timeout /t 2 /nobreak >nul\n")
        f.write("  goto loop\n")
        f.write(")\n")
        f.write(f'if exist "{folder_safe}" rd /s /q "{folder_safe}" >nul 2>&1\n')
        f.write('del "%~f0"\n')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)


def _quitar_registro_desinstalador() -> None:
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, INSTALL_DIR_REG)
    except FileNotFoundError:
        pass


class InstallerWindow(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkBaseClass, on_finish: Callable[[str], None], app_path: str, programs_dir: str) -> None:
        super().__init__(parent)
        self.on_finish: Callable[[str], None] = on_finish
        self._app_path: str = app_path
        self._programs_dir: str = programs_dir
        self._install_dir: tk.StringVar = tk.StringVar(value=programs_dir)
        self.title(_("install_title"))
        self.configure(fg_color=C.BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self._build()
        self._center()
        try:
            self.attributes("-alpha", 0.0)
            self.after(10, self._fade_in)
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

    def _fade_in(self) -> None:
        try:
            for i in range(1, 11):
                self.after(i * 15, lambda v=i / 10: self.attributes("-alpha", v))
        except Exception:
            self.attributes("-alpha", 1.0)

    def _build(self) -> None:
        ctk.CTkLabel(self, text="⚡", font=("Segoe UI Emoji", 40),
                     text_color=C.TEXT).pack(pady=(28, 4))
        ctk.CTkLabel(self, text=_("install_title"), font=F(15, "bold"),
                     text_color=C.ACCENT).pack()
        ctk.CTkLabel(self, text=_("install_desc"), font=F(9),
                     text_color=C.TEXT_DIM).pack(pady=(4, 18))
        dir_frame = ctk.CTkFrame(self, fg_color=C.BG2, border_width=1, border_color=C.BORDER)
        dir_frame.pack(padx=28, fill="x")
        ctk.CTkLabel(dir_frame, text=_("install_folder_label"), font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkEntry(dir_frame, textvariable=self._install_dir, font=F(9),
                     fg_color=C.BG3, text_color=C.TEXT, border_color=C.BORDER, width=46).pack(
                         padx=12, pady=(0, 10), fill="x")
        opt_frame = ctk.CTkFrame(self, fg_color=C.BG2, border_width=1, border_color=C.BORDER)
        opt_frame.pack(padx=28, fill="x", pady=14)
        ctk.CTkLabel(opt_frame, text=_("install_options_label"), font=F(9, "bold"),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(10, 2))
        self.v_escritorio = tk.BooleanVar(value=True)
        self.v_inicio = tk.BooleanVar(value=True)
        self.v_autostart = tk.BooleanVar(value=True)
        for var, txt in [
            (self.v_escritorio, _("install_opt_desktop")),
            (self.v_inicio,     _("install_opt_start")),
            (self.v_autostart,  _("install_opt_autostart")),
        ]:
            ctk.CTkCheckBox(opt_frame, text=txt, variable=var, font=F(9),
                           fg_color=C.ACCENT, text_color=C.TEXT, hover_color=C.ACCENT2,
                           corner_radius=4, border_width=2, checkmark_color=C.BG).pack(
                               anchor="w", padx=10, pady=4)
        self.pb = ctk.CTkProgressBar(self, width=380, height=8, corner_radius=4,
                                     fg_color=C.BG3, progress_color=C.ACCENT)
        self.pb.pack(padx=28, pady=(0, 4))
        self.pb.pack_forget()
        self.lbl_estado = ctk.CTkLabel(self, text="", font=F(9), text_color=C.TEXT_DIM)
        self.lbl_estado.pack()
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=(12, 24))
        ctk.CTkButton(bf, text=_("cancelar"), font=F(10),
                     fg_color=C.BG3, text_color=C.TEXT, hover_color=C.BG4,
                     corner_radius=8, width=90, cursor="hand2",
                     command=self._cancelar).pack(side="left", padx=6)
        self.btn = ctk.CTkButton(bf, text=_("install"), font=F(10, "bold"),
                                fg_color=C.ACCENT, text_color=C.BG,
                                hover_color=darken_color(C.ACCENT),
                                corner_radius=8, width=90, cursor="hand2",
                                command=self._instalar)
        self.btn.pack(side="left", padx=6)

    def _progress(self, pct: int, msg: str) -> None:
        self.pb.set(pct / 100.0)
        self.lbl_estado.configure(text=msg)
        self.update()

    def _cancelar(self) -> None:
        if mb.askyesno(_("install_cancel_title"),
                       _("install_cancel_msg"),
                       parent=self):
            self.master.destroy()

    def _instalar(self) -> None:
        install_dir: str = self._install_dir.get().strip()
        valido, err_msg = _validar_install_dir(install_dir)
        if not valido:
            mb.showerror(_("error"), err_msg, parent=self)
            return
        if not install_dir:
            mb.showerror(_("error"), _("install_err_no_dir"), parent=self)
            return
        self.btn.configure(state="disabled")
        self.pb.pack(padx=28, pady=(0, 4))
        try:
            self._progress(10, _("install_progress_dir"))
            os.makedirs(install_dir, exist_ok=True)
            self._progress(25, _("install_progress_files"))
            dest_exe = os.path.join(install_dir, os.path.basename(self._app_path))
            src_exe = os.path.abspath(self._app_path)
            dst_exe = os.path.abspath(dest_exe)
            copied_ok = False
            if src_exe == dst_exe:
                copied_ok = True
            else:
                try:
                    shutil.copy2(src_exe, dst_exe)
                    copied_ok = True
                except PermissionError:
                    bat = os.path.join(tempfile.gettempdir(), "flowbreak_install_copy.bat")
                    with open(bat, "w", encoding="utf-8") as f:
                        f.write("@echo off\n")
                        f.write(f'copy /y "{src_exe}" "{dst_exe}" >nul 2>&1\n')
                        f.write('del "%~f0"\n')
                    subprocess.run(["cmd", "/c", bat],
                                   creationflags=0x08000000, timeout=10)
                    if os.path.exists(dst_exe):
                        copied_ok = True
                    else:
                        raise PermissionError(
                            f"No se pudo copiar el ejecutable a:\n{install_dir}\n\n"
                            "Cierra FlowBreak si está ejecutando e intenta de nuevo."
                        )
            if not copied_ok:
                raise PermissionError("No se pudo copiar el ejecutable.")
            src_ico = os.path.join(os.path.dirname(self._app_path), "FlowBreak.ico")
            dest_ico = os.path.join(install_dir, "FlowBreak.ico")
            if os.path.exists(src_ico) and os.path.abspath(src_ico) != os.path.abspath(dest_ico):
                try:
                    shutil.copy2(src_ico, dest_ico)
                except PermissionError:
                    pass
            if self.v_escritorio.get():
                self._progress(45, _("install_progress_desktop"))
                buf = ctypes.create_unicode_buffer(260)
                ctypes.windll.shell32.SHGetFolderPathW(0, 0x10, 0, 0, buf)
                lnk = os.path.join(buf.value, "FlowBreak.lnk")
                _crear_acceso_directo(dest_exe, lnk, dest_ico if os.path.exists(dest_ico) else "")
            if self.v_inicio.get():
                self._progress(60, _("install_progress_start"))
                buf = ctypes.create_unicode_buffer(260)
                ctypes.windll.shell32.SHGetFolderPathW(0, 0x02, 0, 0, buf)
                carpeta_inicio = os.path.join(buf.value, APP_DISPLAY)
                os.makedirs(carpeta_inicio, exist_ok=True)
                lnk = os.path.join(carpeta_inicio, "FlowBreak.lnk")
                _crear_acceso_directo(dest_exe, lnk, dest_ico if os.path.exists(dest_ico) else "")
            if self.v_autostart.get():
                self._progress(75, _("install_progress_autostart"))
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Run",
                                     0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{dest_exe}"')
                winreg.CloseKey(key)
            self._progress(90, _("install_progress_register"))
            _registrar_instalacion(install_dir, dest_exe, dest_ico if os.path.exists(dest_ico) else "")
            self._progress(100, _("install_progress_done"))
            mb.showinfo(_("install_ok_title"), _("install_ok_msg").format(dir=install_dir), parent=self)
            self.destroy()
            self.on_finish(install_dir)
        except PermissionError as pe:
            mb.showerror(_("install_perm_error_title"),
                         f"{_('install_perm_error_msg').format(dir=install_dir)}\n\n{pe}", parent=self)
            self.btn.configure(state="normal")
            self.pb.pack_forget()
            self.lbl_estado.configure(text="")
        except Exception as e:
            mb.showerror(_("error"), str(e), parent=self)
            self.btn.configure(state="normal")
            self.pb.pack_forget()
            self.lbl_estado.configure(text="")

    def _center(self) -> None:
        center_window(self)
