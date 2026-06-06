from pausa_activa.constants import (
    DEFAULT_CONFIG, EJERCICIOS, FRASES,
    BG, ACCENT, GREEN,
    THEMES, set_theme, get_theme, I18N, set_idioma, _,
    load_ejercicios_from_file,
)
import tempfile
import json
import os


def test_default_config_has_all_keys():
    required = [
        "intervalo_min", "duracion_pausa_min", "hora_inicio", "hora_fin",
        "ejercicios_activos", "sonido", "posponer_min", "meta_pausas",
        "no_molestar", "agua_activo", "agua_min", "fin_de_semana",
        "sonido_ambiente", "primera_vez", "tema", "modo", "perfil",
        "idioma", "notificacion_sonido", "notificacion_duracion",
    ]
    for key in required:
        assert key in DEFAULT_CONFIG, f"Missing key: {key}"


def test_ejercicios_have_required_fields():
    for ej in EJERCICIOS:
        assert "id" in ej
        assert "nombre" in ej
        assert "icono" in ej
        assert "pasos" in ej
        assert len(ej["pasos"]) > 0


def test_frases_not_empty():
    assert len(FRASES) > 0


def test_color_constants_defined():
    assert BG.startswith("#")
    assert ACCENT.startswith("#")
    assert GREEN.startswith("#")


def test_themes():
    assert "oscuro" in THEMES
    assert "claro" in THEMES
    old_theme = get_theme()
    set_theme("claro")
    assert get_theme() == "claro"
    set_theme(old_theme)
    assert get_theme() == old_theme


def test_i18n():
    old_lang = I18N.keys()
    assert "es" in I18N
    assert "en" in I18N
    set_idioma("en")
    assert _("bienvenido") == "Welcome to Active Breaks!"
    set_idioma("es")
    assert _("bienvenido") == "¡Bienvenido a Pausas Activas!"


def test_i18n_fallback():
    """Claves que no existen deben devolver la misma clave."""
    set_idioma("es")
    assert _("clave_inexistente") == "clave_inexistente"


def test_load_ejercicios_from_file():
    ejercicios_test = [{"id": "test", "nombre": "Test", "icono": "💪", "pasos": ["paso1"]}]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ejercicios_test, f)
        loaded = load_ejercicios_from_file(path)
        assert loaded == ejercicios_test


def test_load_ejercicios_from_file_not_exists():
    loaded = load_ejercicios_from_file("no_existe.json")
    assert len(loaded) > 0
