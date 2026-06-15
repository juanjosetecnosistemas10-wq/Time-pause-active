"""Notificaciones del sistema."""

from __future__ import annotations

from pausa_activa.constants import APP_NAME, log

try:
    from winotify import Notification, audio
    WINOTIFY_AVAILABLE: bool = True
except ImportError:
    WINOTIFY_AVAILABLE = False


def send_win_notification(
    title: str,
    msg: str,
    sound: str = "default",
    duration: str = "short",
) -> None:
    if WINOTIFY_AVAILABLE:
        try:
            toast = Notification(
                app_id=APP_NAME,
                title=title,
                msg=msg,
                duration=duration,
            )
            if sound and sound.lower() != "none":
                try:
                    from winotify import audio as winaudio
                    sound_map = {
                        "default": winaudio.Default,
                        "sms": winaudio.SMS,
                        "mail": winaudio.Mail,
                        "reminder": winaudio.Reminder,
                        "loop": winaudio.LoopingCall,
                    }
                    toast.set_audio(sound_map.get(sound, winaudio.Default), loop=False)
                except Exception:
                    pass
            toast.show()
            return
        except Exception:
            pass
    log.debug("Notificación omitida: %s - %s", title, msg)
