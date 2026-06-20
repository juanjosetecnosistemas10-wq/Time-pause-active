"""Entry point for FlowBreak."""
import os
import sys

from pausa_activa.app import App

APP_PATH = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
APP_DIR = os.path.dirname(APP_PATH)

if __name__ == "__main__":
    # Handle --uninstall flag
    if "--uninstall" in sys.argv:
        import tkinter as tk
        import tkinter.messagebox as mb

        from pausa_activa.installer import (
            _eliminar_accesos_directos,
            _get_install_dir_from_registry,
            _programar_borrado_carpeta,
            _quitar_registro_desinstalador,
        )
        from pausa_activa.windows import set_autoarranque

        root = tk.Tk()
        root.withdraw()

        ok = mb.askyesno(
            "Desinstalar FlowBreak",
            "¿Seguro que deseas desinstalar FlowBreak?\n\n"
            "Se eliminarán los accesos directos, el registro de desinstalación\n"
            "y la carpeta de instalación.",
            icon="warning",
        )
        if ok:
            errores = []
            # Remove autostart
            try:
                set_autoarranque(False, "")
            except Exception as e:
                errores.append(str(e))
            # Remove shortcuts
            _eliminar_accesos_directos(errores)
            # Save install_dir before removing registry
            install_dir = _get_install_dir_from_registry() or APP_DIR
            # Remove registry
            try:
                _quitar_registro_desinstalador()
            except Exception:
                pass
            # Schedule folder deletion
            _programar_borrado_carpeta(install_dir)
            mb.showinfo(
                "Desinstalación completa",
                "FlowBreak ha sido desinstalado.\n\n"
                "La carpeta de instalación se eliminará al cerrar esta ventana.",
            )
        root.destroy()
        sys.exit(0)

    app = App(APP_PATH, APP_DIR)
    app.mainloop()
