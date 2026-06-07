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

from pausa_activa.constants import (
    C, APP_DISPLAY, APP_NAME, INSTALL_DIR_REG, _, log, center_window,
)


def _crear_acceso_directo(target: str, lnk_path: str, icon: str = "") -> None:
    ps: list[str] = [
        "powershell", "-NoProfile", "-Command",
        "param($target,$lnk,$icon)\n"
        "$ws=New-Object -ComObject WScript.Shell\n"
        "$s=$ws.CreateShortcut($lnk)\n"
        "$s.TargetPath=$target\n"
        "$s.WorkingDirectory=[System.IO.Path]::GetDirectoryName($target)\n"
        "if($icon){$s.IconLocation=$icon}\n"
        "$s.Save()",
        "-target", target,
        "-lnk", lnk_path,
        "-icon", (icon if icon else ""),
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
    winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY)
    winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{exe_path}" --uninstall')
    winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path or exe_path)
    winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_DISPLAY)
    winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
    winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
    winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
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
    with open(bat, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write(":loop\n")
        f.write(f'tasklist /fi "PID eq {pid}" | find "{pid}" >nul 2>&1\n')
        f.write("if not errorlevel 1 ( timeout /t 1 /nobreak >nul && goto loop )\n")
        f.write(f'rd /s /q "{folder}" >nul 2>&1\n')
        f.write('del "%~f0"\n')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)


def _quitar_registro_desinstalador() -> None:
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, INSTALL_DIR_REG)
    except FileNotFoundError:
        pass


class InstallerWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, on_finish: Callable[[str], None], app_path: str, programs_dir: str) -> None:
        super().__init__(parent)
        self.on_finish: Callable[[str], None] = on_finish
        self._app_path: str = app_path
        self._programs_dir: str = programs_dir
        self._install_dir: tk.StringVar = tk.StringVar(value=programs_dir)
        self.title(_("install_title"))
        self.configure(bg=C.BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self._build()
        self._center()
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

    def _build(self) -> None:
        tk.Label(self, text="⚡", font=("Segoe UI Emoji", 40), bg=C.BG).pack(pady=(28, 4))
        tk.Label(self, text=_("install_title"),
                 font=("Segoe UI", 15, "bold"), bg=C.BG, fg=C.ACCENT).pack()
        tk.Label(self, text=_("install_desc"),
                 font=("Segoe UI", 9), bg=C.BG, fg=C.TEXT_DIM).pack(pady=(4, 18))
        dir_frame = tk.Frame(self, bg=C.BG2, highlightthickness=1, highlightbackground=C.BORDER)
        dir_frame.pack(padx=28, fill="x")
        tk.Label(dir_frame, text=_("install_folder_label"), font=("Segoe UI", 9, "bold"),
                 bg=C.BG2, fg=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Entry(dir_frame, textvariable=self._install_dir, font=("Segoe UI", 9),
                 bg=C.BG3, fg=C.TEXT, insertbackground=C.TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=C.BORDER, width=46).pack(
                     padx=12, pady=(0, 10), fill="x")
        opt_frame = tk.Frame(self, bg=C.BG2, highlightthickness=1, highlightbackground=C.BORDER)
        opt_frame.pack(padx=28, fill="x", pady=14)
        tk.Label(opt_frame, text=_("install_options_label"), font=("Segoe UI", 9, "bold"),
                 bg=C.BG2, fg=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(10, 2))
        self.v_escritorio = tk.BooleanVar(value=True)
        self.v_inicio = tk.BooleanVar(value=True)
        self.v_autostart = tk.BooleanVar(value=True)
        for var, txt in [
            (self.v_escritorio, _("install_opt_desktop")),
            (self.v_inicio,     _("install_opt_start")),
            (self.v_autostart,  _("install_opt_autostart")),
        ]:
            tk.Checkbutton(opt_frame, text=txt, variable=var, font=("Segoe UI", 9),
                           bg=C.BG2, fg=C.TEXT, selectcolor=C.BG3,
                           activebackground=C.BG2, activeforeground=C.TEXT).pack(anchor="w", padx=10, pady=4)
        tk.Frame(opt_frame, bg=C.BG2).pack(pady=4)
        self.pb = ttk.Progressbar(self, orient="horizontal", length=380,
                                  mode="determinate", maximum=100, value=0)
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("inst.Horizontal.TProgressbar", troughcolor=C.BG3, background=C.ACCENT,
                    bordercolor=C.BG3, lightcolor=C.ACCENT, darkcolor=C.ACCENT)
        self.pb.configure(style="inst.Horizontal.TProgressbar")
        self.pb.pack(padx=28, pady=(0, 4))
        self.pb.pack_forget()
        self.lbl_estado = tk.Label(self, text="", font=("Segoe UI", 9), bg=C.BG, fg=C.TEXT_DIM)
        self.lbl_estado.pack()
        bf = tk.Frame(self, bg=C.BG)
        bf.pack(pady=(12, 24))
        tk.Button(bf, text=_("cancelar"), font=("Segoe UI", 10), bg=C.BG3, fg=C.TEXT,
                  bd=0, cursor="hand2", activebackground=C.BORDER, activeforeground=C.TEXT,
                  relief="flat", padx=18, pady=8, command=self._cancelar).pack(side="left", padx=6)
        self.btn = tk.Button(bf, text=_("install"), font=("Segoe UI", 10, "bold"),
                             bg=C.ACCENT, fg="white", bd=0, cursor="hand2",
                             activebackground="#5A52D5", activeforeground="white",
                             relief="flat", padx=24, pady=8, command=self._instalar)
        self.btn.pack(side="left", padx=6)

    def _progress(self, pct: int, msg: str) -> None:
        self.pb["value"] = pct
        self.lbl_estado.config(text=msg)
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
        self.btn.config(state="disabled")
        self.pb.pack(padx=28, pady=(0, 4))
        try:
            self._progress(10, _("install_progress_dir"))
            os.makedirs(install_dir, exist_ok=True)
            self._progress(25, _("install_progress_files"))
            dest_exe = os.path.join(install_dir, os.path.basename(self._app_path))
            if os.path.abspath(self._app_path) != os.path.abspath(dest_exe):
                shutil.copy2(self._app_path, dest_exe)
            src_ico = os.path.join(os.path.dirname(self._app_path), "FlowBreak.ico")
            dest_ico = os.path.join(install_dir, "FlowBreak.ico")
            if os.path.exists(src_ico) and os.path.abspath(src_ico) != os.path.abspath(dest_ico):
                shutil.copy2(src_ico, dest_ico)
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
        except PermissionError:
            mb.showerror(_("install_perm_error_title"),
                         _("install_perm_error_msg").format(dir=install_dir), parent=self)
            self.btn.config(state="normal")
            self.pb.pack_forget()
            self.lbl_estado.config(text="")
        except Exception as e:
            mb.showerror(_("error"), str(e), parent=self)
            self.btn.config(state="normal")
            self.pb.pack_forget()
            self.lbl_estado.config(text="")

    def _center(self) -> None:
        center_window(self)
