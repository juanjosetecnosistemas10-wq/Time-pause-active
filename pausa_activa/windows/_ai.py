"""AI Insights window and engine."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.windows._base import CenteredWindow


class AIInsightsWindow(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, insights: dict) -> None:
        super().__init__(parent)
        self.title("🤖 Insights IA")
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("420x560")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="🤖", font=("Segoe UI Emoji", 40), text_color=C.TEXT).pack(pady=(16, 0))
        ctk.CTkLabel(main, text="Análisis Inteligente", font=F(16, "bold"), text_color=C.TEXT).pack(pady=(4, 12))

        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12)

        prod = insights.get("productividad", {})
        prod_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                 border_width=1, border_color=C.CARD_BORDER)
        prod_card.pack(fill="x", pady=4)
        ctk.CTkLabel(prod_card, text="📊 Patrón de productividad", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        peak = prod.get("hora_pico", "N/A")
        ctk.CTkLabel(prod_card, text=f"Hora pico: {peak}", font=F(9),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12)
        avg = prod.get("promedio_pausas", 0)
        ctk.CTkLabel(prod_card, text=f"Promedio pausas/día: {avg:.1f}", font=F(9),
                     text_color=C.TEXT_DIM).pack(anchor="w", padx=12, pady=(0, 8))

        opt_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
        opt_card.pack(fill="x", pady=4)
        ctk.CTkLabel(opt_card, text="🎯 Intervalo óptimo sugerido", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        opt = insights.get("intervalo_optimo", 45)
        ctk.CTkLabel(opt_card, text=f"IA recomienda: cada {opt} minutos", font=F(9),
                     text_color=C.ACCENT).pack(anchor="w", padx=12, pady=(0, 8))

        pred_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                 border_width=1, border_color=C.CARD_BORDER)
        pred_card.pack(fill="x", pady=4)
        ctk.CTkLabel(pred_card, text="🔥 Predicción de racha", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        streak = insights.get("prediccion_racha", "Media")
        streak_color = C.GREEN if "Alta" in streak else (C.YELLOW if "Media" in streak else C.ACCENT2)
        ctk.CTkLabel(pred_card, text=f"Probabilidad de mantener racha: {streak}", font=F(9),
                     text_color=streak_color).pack(anchor="w", padx=12, pady=(0, 8))

        fat_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
        fat_card.pack(fill="x", pady=4)
        ctk.CTkLabel(fat_card, text="😴 Análisis de fatiga", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        fatigue = insights.get("nivel_fatiga", "Normal")
        fat_color = C.GREEN if fatigue == "Bajo" else (C.YELLOW if fatigue == "Normal" else "#EF4444")
        ctk.CTkLabel(fat_card, text=f"Nivel de fatiga: {fatigue}", font=F(9),
                     text_color=fat_color).pack(anchor="w", padx=12, pady=(0, 8))

        rec_card = ctk.CTkFrame(scroll, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
        rec_card.pack(fill="x", pady=4)
        ctk.CTkLabel(rec_card, text="💡 Recomendaciones", font=F(10, "bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=12, pady=(8, 4))
        for rec in insights.get("recomendaciones", []):
            ctk.CTkLabel(rec_card, text=f"• {rec}", font=F(9),
                         text_color=C.TEXT_DIM, wraplength=360, anchor="w").pack(anchor="w", padx=12, pady=1)
        ctk.CTkFrame(rec_card, fg_color="transparent").pack(pady=(0, 8))

        ctk.CTkButton(main, text=_("cerrar"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=100, height=34,
                      command=self.destroy).pack(pady=12)
        self.center()


class AIEngine:
    def __init__(self, stats: dict, config: dict) -> None:
        self._stats = stats
        self._config = config

    def analyze(self) -> dict:
        insights: dict[str, Any] = {}

        hourly: dict[int, int] = {}
        for entry in self._stats.get("historial", []):
            if entry.get("estado") == "completada":
                try:
                    h = int(entry["hora"].split(":")[0])
                    hourly[h] = hourly.get(h, 0) + 1
                except (ValueError, IndexError):
                    pass

        if hourly:
            peak_hour = max(hourly, key=hourly.get)
            insights["productividad"] = {
                "hora_pico": f"{peak_hour}:00 - {peak_hour + 1}:00",
                "horas_activas": sorted(hourly.keys()),
                "promedio_pausas": len(self._stats.get("historial", [])) / max(1, 7),
            }
        else:
            insights["productividad"] = {
                "hora_pico": "Sin datos aún",
                "horas_activas": [],
                "promedio_pausas": 0,
            }

        completadas = self._stats.get("completadas", 0)
        racha = self._stats.get("racha", 0)
        if completadas > 10 and racha > 3:
            optimal = max(25, min(60, 45 - (racha * 2)))
        else:
            optimal = self._config.get("intervalo_min", 45)
        insights["intervalo_optimo"] = optimal

        if racha >= 7:
            streak_pred = "Alta (90%+)"
        elif racha >= 3:
            streak_pred = "Media (60-80%)"
        else:
            streak_pred = "Baja (<50%)"
        insights["prediccion_racha"] = streak_pred

        recent = self._stats.get("historial", [])[-5:]
        skipped = sum(1 for e in recent if e.get("estado") == "saltada")
        if skipped >= 3:
            fatigue = "Alto - Necesitas más descansos"
        elif skipped >= 1:
            fatigue = "Normal"
        else:
            fatigue = "Bajo - Buen equilibrio"
        insights["nivel_fatiga"] = fatigue

        recs = []
        if completadas < 3:
            recs.append("Intenta completar al menos 3 pausas diarias")
        if racha < 2:
            recs.append("La constancia es clave: intenta no romper tu racha")
        if skipped > completadas:
            recs.append("Estás saltando muchas pausas, considera reducir el intervalo")
        if hourly:
            peak = max(hourly, key=hourly.get)
            if peak < 10:
                recs.append("Eres más productivo en la mañana, aprovecha eso")
        if not recs:
            recs.append("¡Excelente! Sigue manteniendo tus hábitos saludables")
        insights["recomendaciones"] = recs

        return insights

    def suggest_interval(self) -> int:
        insights = self.analyze()
        return insights.get("intervalo_optimo", self._config.get("intervalo_min", 45))
