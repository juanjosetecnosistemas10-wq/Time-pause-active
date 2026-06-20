from pausa_activa.hotkeys import HotkeyManager


def test_hotkeys_register_unregister() -> None:
    mgr = HotkeyManager()

    called = False
    def cb() -> None:
        nonlocal called
        called = True

    mgr.register("test_key", "<ctrl>+<alt>+t", cb)
    assert "test_key" in mgr._hotkeys
    assert mgr._hotkeys["test_key"]["combo"] == "<ctrl>+<alt>+t"
    assert mgr._hotkeys["test_key"]["callback"] == cb

    assert mgr._enabled is True
    mgr.set_enabled(False)
    assert mgr._enabled is False
    mgr.set_enabled(True)
    assert mgr._enabled is True

    mgr.unregister("test_key")
    assert "test_key" not in mgr._hotkeys
