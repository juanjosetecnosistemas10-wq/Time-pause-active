import os
import sys

from pausa_activa.app import App

APP_PATH = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
APP_DIR = os.path.dirname(APP_PATH)

if __name__ == "__main__":
    app = App(APP_PATH, APP_DIR)
    app.mainloop()
