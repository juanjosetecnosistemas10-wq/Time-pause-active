"""Gestor de configuración, estadísticas y perfiles."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any

from pausa_activa.constants import DEFAULT_CONFIG, EJERCICIOS, log


class ConfigManager:
    def __init__(self, config_file: str, stats_file: str, hist_file: str) -> None:
        self._config_file: str = config_file
        self._stats_file: str = stats_file
        self._hist_file: str = hist_file
        self._config_dir: str = os.path.dirname(config_file)

    @property
    def hist_file(self) -> str:
        return self._hist_file

    @property
    def config_dir(self) -> str:
        return self._config_dir

    def _profile_path(self, profile_name: str) -> str:
        return os.path.join(self._config_dir, f"config_{profile_name}.json")

    def list_profiles(self) -> list[str]:
        profiles: list[str] = ["default"]
        if os.path.isdir(self._config_dir):
            for f in os.listdir(self._config_dir):
                if f.startswith("config_") and f.endswith(".json"):
                    name = f[7:-5]
                    if name != "default":
                        profiles.append(name)
        return profiles

    def load_config(self, profile: str | None = None) -> dict[str, Any]:
        path = self._profile_path(profile) if profile else self._config_file
        try:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    c: dict[str, Any] = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    c.setdefault(k, v)
                if not c["ejercicios_activos"]:
                    c["ejercicios_activos"] = [e["id"] for e in EJERCICIOS]
                return c
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Error loading config from %s, using defaults: %s", path, e)
        c = dict(DEFAULT_CONFIG)
        c["ejercicios_activos"] = [e["id"] for e in EJERCICIOS]
        return c

    def save_config(self, cfg: dict[str, Any], profile: str | None = None) -> None:
        path = self._profile_path(profile) if profile else self._config_file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    def load_stats(self) -> dict[str, Any]:
        today: str = datetime.now().strftime("%Y-%m-%d")
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, encoding="utf-8") as f:
                    s: dict[str, Any] = json.load(f)
                if s.get("fecha") != today:
                    racha: int = s.get("racha", 0)
                    ayer_ok: bool = s.get("meta_cumplida", False)
                    s = {
                        "fecha": today, "completadas": 0, "saltadas": 0,
                        "historial": [], "racha": racha + 1 if ayer_ok else 0,
                        "meta_cumplida": False,
                    }
                return s
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Error loading stats, resetting: %s", e)
        return {
            "fecha": today, "completadas": 0, "saltadas": 0,
            "historial": [], "racha": 0, "meta_cumplida": False,
        }

    def save_stats(self, s: dict[str, Any]) -> None:
        with open(self._stats_file, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)

    def append_csv(self, row: list[str]) -> None:
        exists: bool = os.path.exists(self._hist_file)
        with open(self._hist_file, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(["fecha", "hora", "ejercicio", "estado"])
            w.writerow(row)

    def get_stats_history(self) -> dict[str, dict[str, Any]]:
        """Retorna stats históricos día por día."""
        history: dict[str, dict[str, Any]] = {}
        if os.path.exists(self._hist_file):
            try:
                with open(self._hist_file, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        dia = row.get("fecha", "")
                        if dia not in history:
                            history[dia] = {"completadas": 0, "saltadas": 0}
                        estado = row.get("estado", "")
                        if estado == "completada":
                            history[dia]["completadas"] += 1
                        elif estado == "saltada":
                            history[dia]["saltadas"] += 1
            except Exception:
                pass
        return history
