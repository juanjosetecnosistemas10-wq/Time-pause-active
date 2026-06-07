"""Dev launcher — runs FlowBreak from source with auto-reload on file changes."""
import os
import sys
import time
import subprocess
import threading
from pathlib import Path

WATCH_DIR = Path(__file__).parent / "pausa_activa"
EXTENSIONS = (".py",)


def _hash_files() -> int:
    return sum(os.path.getsize(f) for f in WATCH_DIR.rglob("*") if f.suffix in EXTENSIONS and f.is_file())


def _watcher(stop_event: threading.Event) -> None:
    prev = _hash_files()
    while not stop_event.is_set():
        time.sleep(1)
        curr = _hash_files()
        if curr != prev:
            prev = curr
            stop_event.set()


def main() -> None:
    proc: subprocess.Popen | None = None
    try:
        while True:
            stop_event = threading.Event()
            watcher = threading.Thread(target=_watcher, args=(stop_event,), daemon=True)
            watcher.start()

            print("=" * 50)
            print("  FlowBreak — Modo desarrollo")
            print("  Cambia archivos en pausa_activa/ y la app se reinicia sola")
            print("  Cierra la ventana de la app o presiona Ctrl+C para salir")
            print("=" * 50)

            proc = subprocess.Popen(
                [sys.executable, str(Path(__file__).parent / "pausa_activa.py")],
                cwd=Path(__file__).parent,
            )

            stop_event.wait()
            print("\n[dev] Cambios detectados, reiniciando...")
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
    except KeyboardInterrupt:
        print("\n[dev] Saliendo...")
    finally:
        if proc and proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    main()
