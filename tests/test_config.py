import os
import json
import tempfile
import pytest

from pausa_activa.config import ConfigManager
from pausa_activa.constants import DEFAULT_CONFIG, EJERCICIOS


@pytest.fixture
def tmp_files():
    with tempfile.TemporaryDirectory() as d:
        cfg = os.path.join(d, "config.json")
        stats = os.path.join(d, "stats.json")
        hist = os.path.join(d, "historial.csv")
        yield cfg, stats, hist


def test_load_config_creates_default(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    c = mgr.load_config()
    assert c["intervalo_min"] == 45
    assert c["duracion_pausa_min"] == 5
    assert c["ejercicios_activos"] == [e["id"] for e in EJERCICIOS]
    assert c["primera_vez"] is True


def test_load_config_reads_existing(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump({"intervalo_min": 30, "duracion_pausa_min": 10}, f)
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    c = mgr.load_config()
    assert c["intervalo_min"] == 30
    assert c["duracion_pausa_min"] == 10
    assert c["hora_inicio"] == "08:00"


def test_load_config_corrupt_json(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    with open(cfg_file, "w", encoding="utf-8") as f:
        f.write("not valid json")
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    c = mgr.load_config()
    assert c["intervalo_min"] == 45


def test_save_and_load_config(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    c = mgr.load_config()
    c["intervalo_min"] = 99
    mgr.save_config(c)
    c2 = mgr.load_config()
    assert c2["intervalo_min"] == 99


def test_load_stats_creates_default(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    s = mgr.load_stats()
    assert s["completadas"] == 0
    assert s["saltadas"] == 0
    assert s["racha"] == 0


def test_save_and_load_stats(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    s = mgr.load_stats()
    s["completadas"] = 5
    s["saltadas"] = 2
    mgr.save_stats(s)
    s2 = mgr.load_stats()
    assert s2["completadas"] == 5
    assert s2["saltadas"] == 2


def test_append_csv(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    mgr.append_csv(["2024-01-01", "10:00", "Test", "completada"])
    mgr.append_csv(["2024-01-01", "11:00", "Test2", "saltada"])
    with open(hist_file, encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 3
    assert "fecha" in lines[0]


def test_load_stats_corrupt_json(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    with open(stats_file, "w", encoding="utf-8") as f:
        f.write("corrupt")
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    s = mgr.load_stats()
    assert s["completadas"] == 0


def test_list_profiles(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    profiles = mgr.list_profiles()
    assert "default" in profiles


def test_save_and_load_with_profile(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    c = mgr.load_config()
    c["intervalo_min"] = 60
    mgr.save_config(c, profile="trabajo")
    c2 = mgr.load_config(profile="trabajo")
    assert c2["intervalo_min"] == 60
    # default no debe cambiar
    c_default = mgr.load_config()
    assert c_default["intervalo_min"] == 45


def test_get_stats_history(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    mgr.append_csv(["2024-01-01", "10:00", "Test", "completada"])
    mgr.append_csv(["2024-01-01", "11:00", "Test2", "saltada"])
    mgr.append_csv(["2024-01-02", "09:00", "Test3", "completada"])
    history = mgr.get_stats_history()
    assert "2024-01-01" in history
    assert history["2024-01-01"]["completadas"] == 1
    assert history["2024-01-01"]["saltadas"] == 1
    assert history["2024-01-02"]["completadas"] == 1


def test_config_has_new_keys(tmp_files):
    cfg_file, stats_file, hist_file = tmp_files
    mgr = ConfigManager(cfg_file, stats_file, hist_file)
    c = mgr.load_config()
    assert "tema" in c
    assert "modo" in c
    assert "perfil" in c
    assert "idioma" in c
    assert "notificacion_sonido" in c
    assert "notificacion_duracion" in c
