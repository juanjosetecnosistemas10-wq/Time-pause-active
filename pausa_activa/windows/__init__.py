"""Windows package — re-exports all UI classes and helpers."""

from __future__ import annotations

from pausa_activa.windows._achievements import ACHIEVEMENTS, AchievementsWindow, check_achievements
from pausa_activa.windows._ai import AIEngine, AIInsightsWindow
from pausa_activa.windows._base import (
    CenteredWindow,
    _card,
    _checkbox,
    _dibujar_grafico,
    _entry,
    _radio,
    draw_bar_chart,
    get_audio_manager,
    get_autoarranque,
    set_autoarranque,
)
from pausa_activa.windows._break import BreakWindow
from pausa_activa.windows._compact import CompactWindow
from pausa_activa.windows._config import ConfigWindow
from pausa_activa.windows._custom_exercise import CustomExerciseWindow
from pausa_activa.windows._floating import FloatingTimer
from pausa_activa.windows._flowbuddy import FlowBuddyWidget, FlowBuddyWindow
from pausa_activa.windows._fullscreen import FullscreenTimer
from pausa_activa.windows._posture import PostureReminder
from pausa_activa.windows._stats import StatsWindow, StatsWindowEnhanced
from pausa_activa.windows._toast import ToastNotification, toast
from pausa_activa.windows._tutorial import TutorialWindow
from pausa_activa.windows._uninstall import UninstallWindow
from pausa_activa.windows._welcome import WelcomeWindow
from pausa_activa.windows._workout import WorkoutEditorWindow, WorkoutWindow

PausaWindow = BreakWindow

__all__ = [
    "get_audio_manager", "set_autoarranque", "get_autoarranque",
    "_card", "_entry", "_checkbox", "_radio",
    "CenteredWindow",
    "draw_bar_chart", "_dibujar_grafico",
    "BreakWindow", "PausaWindow",
    "StatsWindow", "StatsWindowEnhanced",
    "ConfigWindow",
    "WelcomeWindow",
    "UninstallWindow",
    "ToastNotification", "toast",
    "FloatingTimer",
    "CompactWindow",
    "FullscreenTimer",
    "ACHIEVEMENTS", "check_achievements", "AchievementsWindow",
    "CustomExerciseWindow",
    "WorkoutWindow", "WorkoutEditorWindow",
    "TutorialWindow",
    "PostureReminder",
    "FlowBuddyWidget", "FlowBuddyWindow",
    "AIInsightsWindow", "AIEngine",
]
