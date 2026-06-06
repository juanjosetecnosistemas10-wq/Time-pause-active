"""Gestor de sonidos ambiente y alertas."""

from __future__ import annotations

import os
import random
import struct
import threading
import time
import wave
import winsound

from pausa_activa.constants import log


class AudioManager:
    def __init__(self) -> None:
        self._ambient_dir: str = os.path.join(
            os.environ.get("TEMP", os.path.expanduser("~")),
            ".pausas_activas_audio",
        )
        self._lock: threading.Lock = threading.Lock()

    def _generar_wav_lluvia(self, path: str, duracion_seg: int = 30) -> None:
        import math
        sample_rate: int = 22050
        n_samples: int = sample_rate * duracion_seg
        with wave.open(path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for i in range(n_samples):
                t: float = i / sample_rate
                envelope: float = 0.5 + 0.5 * math.sin(math.pi * t / duracion_seg)
                ruido: float = random.uniform(-1, 1)
                sample: int = int(ruido * 12000 * envelope)
                sample = max(-32768, min(32767, sample))
                wf.writeframes(struct.pack("<h", sample))

    def _generar_wav_naturaleza(self, path: str, duracion_seg: int = 30) -> None:
        import math
        sample_rate: int = 22050
        n_samples: int = sample_rate * duracion_seg
        with wave.open(path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                envelope = 0.5 + 0.5 * math.sin(math.pi * t / duracion_seg)
                viento = random.uniform(-0.3, 0.3) * envelope
                pajaro: float = 0.0
                for freq in [400, 550, 700, 850, 1000]:
                    pajaro += 0.08 * math.sin(2 * math.pi * freq * t)
                    pajaro += 0.04 * math.sin(2 * math.pi * freq * 1.5 * t + 1.3)
                sample = int((viento + pajaro * 0.5) * 10000)
                sample = max(-32768, min(32767, sample))
                wf.writeframes(struct.pack("<h", sample))

    def _get_ambient_wav(self, tipo: str) -> str:
        os.makedirs(self._ambient_dir, exist_ok=True)
        path: str = os.path.join(self._ambient_dir, f"{tipo}.wav")
        if not os.path.exists(path):
            if tipo == "lluvia":
                self._generar_wav_lluvia(path)
            elif tipo == "naturaleza":
                self._generar_wav_naturaleza(path)
        return path

    def start_ambient(self, tipo: str) -> None:
        with self._lock:
            self.stop_ambient()
        if tipo == "ninguno":
            return
        try:
            path: str = self._get_ambient_wav(tipo)
            winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_LOOP)
        except Exception:
            pass

    def stop_ambient(self) -> None:
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    @staticmethod
    def play_alert() -> None:
        try:
            for freq in [660, 880, 1100]:
                winsound.Beep(freq, 100)
                time.sleep(0.05)
        except Exception:
            pass
