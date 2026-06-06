from pausa_activa.installer import _validar_install_dir


def test_validar_install_dir_empty():
    valid, msg = _validar_install_dir("")
    assert not valid
    assert "vacía" in msg


def test_validar_install_dir_path_traversal():
    valid, msg = _validar_install_dir("C:\\Users\\..\\Windows")
    assert not valid
    assert ".." in msg


def test_validar_install_dir_valid():
    valid, msg = _validar_install_dir("C:\\Program Files\\PausasActivas")
    assert valid
    assert msg == ""
