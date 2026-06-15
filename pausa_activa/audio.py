"""Gestor de sonidos ambiente y alertas."""

from __future__ import annotations

import os
import random
import struct
import threading
import time
import wave
import winsound
import math

from pausa_activa.constants import log


class AudioManager:
    def __init__(self) -> None:
        self._ambient_dir: str = os.path.join(
            os.environ.get("TEMP", os.path.expanduser("~")),
            ".flowbreak_audio",
        )
        self._lock: threading.Lock = threading.Lock()
        self._active_tipo: str | None = None
        self._sounds_dir: str = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "sounds"
        )

    def _generar_wav_lluvia(self, path: str, duracion_seg: int = 30) -> None:
        sample_rate: int = 22050
        n_samples: int = sample_rate * duracion_seg
        factor: float = math.pi / (sample_rate * duracion_seg)
        
        samples: list[int] = []
        for i in range(n_samples):
            envelope: float = 0.5 + 0.5 * math.sin(i * factor)
            ruido: float = random.uniform(-1, 1)
            sample: int = int(ruido * 12000 * envelope)
            if sample < -32768:
                sample = -32768
            elif sample > 32767:
                sample = 32767
            samples.append(sample)
            
        data = struct.pack(f"<{len(samples)}h", *samples)
        with wave.open(path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(data)

    def _generar_wav_naturaleza(self, path: str, duracion_seg: int = 30) -> None:
        sample_rate: int = 22050
        n_samples: int = sample_rate * duracion_seg
        
        freqs = [400, 550, 700, 850, 1000]
        factor_env = math.pi / (sample_rate * duracion_seg)
        c1 = [2 * math.pi * freq / sample_rate for freq in freqs]
        c2 = [2 * math.pi * freq * 1.5 / sample_rate for freq in freqs]
        
        samples: list[int] = []
        for i in range(n_samples):
            envelope: float = 0.5 + 0.5 * math.sin(i * factor_env)
            viento: float = random.uniform(-0.3, 0.3) * envelope
            pajaro: float = 0.0
            for c1_val, c2_val in zip(c1, c2):
                pajaro += 0.08 * math.sin(c1_val * i) + 0.04 * math.sin(c2_val * i + 1.3)
            sample = int((viento + pajaro * 0.5) * 10000)
            if sample < -32768:
                sample = -32768
            elif sample > 32767:
                sample = 32767
            samples.append(sample)
            
        data = struct.pack(f"<{len(samples)}h", *samples)
        with wave.open(path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(data)

    def _get_ambient_wav(self, tipo: str) -> str:
        external: str = os.path.join(self._sounds_dir, f"{tipo}.wav")
        if os.path.exists(external):
            return external
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
            self._active_tipo = tipo
        if tipo == "ninguno":
            return

        def _async_load_and_play():
            try:
                path: str = self._get_ambient_wav(tipo)
                with self._lock:
                    if self._active_tipo == tipo:
                        winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_LOOP)
            except Exception as e:
                log.debug("Failed playing ambient sound asynchronously: %s", e)

        threading.Thread(target=_async_load_and_play, daemon=True).start()

    def stop_ambient(self) -> None:
        with self._lock:
            self._active_tipo = None
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

    def cleanup(self) -> None:
        """Remove generated WAV files from temp directory."""
        self.stop_ambient()
        try:
            if os.path.isdir(self._ambient_dir):
                import shutil
                shutil.rmtree(self._ambient_dir, ignore_errors=True)
        except Exception:
            pass

