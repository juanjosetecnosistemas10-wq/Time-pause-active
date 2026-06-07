"""Standalone uninstaller for FlowBreak."""
import os
import sys
import subprocess
import tkinter as tk
import tkinter.messagebox as mb
import winreg

def main() -> None:
    root = tk.Tk()
    root.withdraw()

    install_dir: str = ""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FlowBreak",
        )
        install_dir, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
    except Exception:
        pass

    if not install_dir or not os.path.isdir(install_dir):
        mb.showerror("Error", "No se encontr\u00f3 FlowBreak instalado.")
        root.destroy()
        return

    exe_path: str = os.path.join(install_dir, "FlowBreak.exe")
    if os.path.exists(exe_path):
        subprocess.run([exe_path, "--uninstall"], creationflags=0x08000000)
    root.destroy()

if __name__ == "__main__":
    main()
