"""Stats windows."""

from __future__ import annotations

import os
from collections.abc import Callable
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from pausa_activa.constants import C, F, _
from pausa_activa.windows._base import CenteredWindow, _dibujar_grafico


class StatsWindow(CenteredWindow):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        stats: dict[str, Any],
        meta: int,
        hist_file: str,
        history: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(_("estadisticas"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("420x680")
        total: int = stats["completadas"] + stats["saltadas"]
        pct: int = int(stats["completadas"] / total * 100) if total > 0 else 0
        meta_ok: bool = stats["completadas"] >= meta

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(
            main, text="📊", font=("Segoe UI Emoji", 36),
            text_color=C.TEXT,
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            main, text=_("estadisticas"), font=F(18, "bold"),
            text_color=C.TEXT,
        ).pack(pady=(0, 16))

        cards_frame = ctk.CTkFrame(main, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20)

        stat_items: list[tuple[str, str, str, str]] = [
            ("✅", f"{stats['completadas']}", C.GREEN, "Completadas"),
            ("⏭️", str(stats["saltadas"]), C.ACCENT2, "Saltadas"),
            ("📈", f"{pct}%", C.ACCENT, "Éxito"),
            ("🔥", f"{stats.get('racha', 0)}d", C.YELLOW, "Racha"),
        ]
        for i, (icon, val, color, label) in enumerate(stat_items):
            card = ctk.CTkFrame(
                cards_frame, fg_color=C.CARD, corner_radius=14,
                border_width=1, border_color=C.CARD_BORDER,
            )
            card.grid(row=0, column=i, padx=3, pady=4, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(
                card, text=icon, font=F(16),
                text_color=C.TEXT_DIM,
            ).pack(pady=(10, 2))
            ctk.CTkLabel(
                card, text=val, font=F(18, "bold"),
                text_color=color,
            ).pack()
            ctk.CTkLabel(
                card, text=label, font=F(8),
                text_color=C.TEXT_MUTED,
            ).pack(pady=(0, 8))

        detail_card = ctk.CTkFrame(
            main, fg_color=C.CARD, corner_radius=14,
            border_width=1, border_color=C.CARD_BORDER,
        )
        detail_card.pack(fill="x", padx=20, pady=(12, 0))

        status_icon: str = "🎯" if meta_ok else "🔄"
        status_text: str = "Meta alcanzada" if meta_ok else "En progreso"
        status_color: str = C.GREEN if meta_ok else C.TEXT_MUTED

        rows: list[tuple[str, str, str]] = [
            ("Completadas", f"{stats['completadas']} / {meta}", C.GREEN),
            ("Saltadas", str(stats["saltadas"]), C.ACCENT2),
            ("Tasa de éxito", f"{pct}%", C.ACCENT),
            ("Racha", f"{stats.get('racha', 0)} días", C.YELLOW),
            (f"{status_icon} Meta", status_text, status_color),
        ]
        for i, (label, val, color) in enumerate(rows):
            r = ctk.CTkFrame(detail_card, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=5)
            ctk.CTkLabel(
                r, text=label, font=F(10),
                text_color=C.TEXT_DIM, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                r, text=val, font=F(11, "bold"),
                text_color=color,
            ).pack(side="right")
            if i < len(rows) - 1:
                sep = ctk.CTkFrame(detail_card, fg_color=C.CARD_BORDER, height=1)
                sep.pack(fill="x", padx=16)

        if history:
            chart_card = ctk.CTkFrame(
                main, fg_color=C.CARD, corner_radius=14,
                border_width=1, border_color=C.CARD_BORDER,
            )
            chart_card.pack(fill="x", padx=20, pady=(12, 0))
            ctk.CTkLabel(
                chart_card, text="📅  " + _("ultimos_7_dias"), font=F(10, "bold"),
                text_color=C.TEXT_DIM,
            ).pack(anchor="w", padx=14, pady=(10, 4))
            _dibujar_grafico(chart_card, history, meta)

        if stats["historial"]:
            hist_card = ctk.CTkFrame(
                main, fg_color=C.CARD, corner_radius=14,
                border_width=1, border_color=C.CARD_BORDER,
            )
            hist_card.pack(fill="x", padx=20, pady=(12, 0))
            ctk.CTkLabel(
                hist_card, text="🕐  " + _("ultimas_pausas"), font=F(10, "bold"),
                text_color=C.TEXT_DIM,
            ).pack(anchor="w", padx=14, pady=(10, 6))
            for entry in stats["historial"][-5:][::-1]:
                dot: str = "🟢" if entry["estado"] == "completada" else "🔴"
                estado_color = C.GREEN if entry["estado"] == "completada" else C.ACCENT2
                r = ctk.CTkFrame(hist_card, fg_color="transparent")
                r.pack(fill="x", padx=14, pady=3)
                ctk.CTkLabel(
                    r, text=f"{dot}  {entry['hora']}  ·  {entry['ejercicio']}",
                    font=F(9), text_color=C.TEXT,
                ).pack(side="left")
                ctk.CTkLabel(
                    r, text=entry["estado"].capitalize(),
                    font=F(8, "bold"), text_color=estado_color,
                ).pack(side="right")
            ctk.CTkFrame(hist_card, fg_color="transparent").pack(pady=(0, 6))

        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(14, 16))
        ctk.CTkButton(
            bf, text="📥  " + _("exportar_csv"),
            fg_color=C.BG3, text_color=C.TEXT,
            font=F(10), corner_radius=12, width=130, height=34,
            command=lambda: self._export(hist_file, stats, meta),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            bf, text=_("cerrar"),
            fg_color=C.ACCENT, text_color="#FFFFFF",
            font=F(10, "bold"), corner_radius=12, width=100, height=34,
            command=self.destroy,
        ).pack(side="left", padx=4)
        self.center()

    @staticmethod
    def _export(hist_file: str, stats: dict[str, Any], meta: int) -> None:
        from datetime import datetime as _dt
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json"), (_("todos"), "*.*")],
            title=_("exportar_stats"),
        )
        if not path:
            return
        try:
            if path.endswith(".json"):
                import json
                stats["meta_pausas"] = meta
                stats["exportado"] = _dt.now().isoformat()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
            else:
                import shutil
                if os.path.exists(hist_file):
                    shutil.copy2(hist_file, path)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("fecha,hora,ejercicio,estado\n")
            messagebox.showinfo(_("exportar"), _("exportado_ok").format(path=path))
        except Exception as e:
            messagebox.showerror(_("error"), _("exportado_error").format(e=e))


class StatsWindowEnhanced(CenteredWindow):
    def __init__(self, parent: ctk.CTkBaseClass, stats: dict, meta: int,
                 hist_file: str, history: dict | None = None,
                 on_export: Callable | None = None,
                 on_import: Callable | None = None) -> None:
        super().__init__(parent)
        self.title(_("estadisticas"))
        self.attributes("-topmost", True)
        self.configure(fg_color=C.BG)
        self.geometry("440x700")

        main = ctk.CTkFrame(self, fg_color=C.BG)
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text="📊", font=("Segoe UI Emoji", 36), text_color=C.TEXT).pack(pady=(16, 4))
        ctk.CTkLabel(main, text=_("estadisticas"), font=F(18, "bold"), text_color=C.TEXT).pack(pady=(0, 8))

        period_frame = ctk.CTkFrame(main, fg_color="transparent")
        period_frame.pack(fill="x", padx=20, pady=(0, 8))
        self._period = ctk.StringVar(value="semana")
        for val, lbl in [("semana", "7 días"), ("mes", "30 días"), ("todo", "Todo")]:
            ctk.CTkButton(period_frame, text=lbl, font=F(9), corner_radius=10,
                          fg_color=C.ACCENT if val == "semana" else C.BG3,
                          text_color="#FFFFFF" if val == "semana" else C.TEXT,
                          width=90, height=28,
                          command=lambda v=val: self._set_period(v)).pack(side="left", padx=3)

        total = stats["completadas"] + stats["saltadas"]
        pct = int(stats["completadas"] / total * 100) if total > 0 else 0

        cards_frame = ctk.CTkFrame(main, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20)
        stat_items = [
            ("✅", f"{stats['completadas']}", C.GREEN),
            ("⏭️", str(stats["saltadas"]), C.ACCENT2),
            ("📈", f"{pct}%", C.ACCENT),
            ("🔥", f"{stats.get('racha', 0)}d", C.YELLOW),
        ]
        for i, (icon, val, color) in enumerate(stat_items):
            card = ctk.CTkFrame(cards_frame, fg_color=C.CARD, corner_radius=14,
                                border_width=1, border_color=C.CARD_BORDER)
            card.grid(row=0, column=i, padx=3, pady=4, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=icon, font=F(14), text_color=C.TEXT_DIM).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=val, font=F(16, "bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=["Comp", "Salt", "Éxito", "Racha"][i],
                         font=F(7), text_color=C.TEXT_MUTED).pack(pady=(0, 6))

        detail_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                    border_width=1, border_color=C.CARD_BORDER)
        detail_card.pack(fill="x", padx=20, pady=(8, 0))
        rows_data = [
            ("Completadas", f"{stats['completadas']} / {meta}", C.GREEN),
            ("Saltadas", str(stats["saltadas"]), C.ACCENT2),
            ("Tasa de éxito", f"{pct}%", C.ACCENT),
            ("Racha", f"{stats.get('racha', 0)} días", C.YELLOW),
        ]
        for i, (label, val, color) in enumerate(rows_data):
            r = ctk.CTkFrame(detail_card, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(r, text=label, font=F(9), text_color=C.TEXT_DIM, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=val, font=F(10, "bold"), text_color=color).pack(side="right")
            if i < len(rows_data) - 1:
                ctk.CTkFrame(detail_card, fg_color=C.CARD_BORDER, height=1).pack(fill="x", padx=14)

        if history:
            chart_card = ctk.CTkFrame(main, fg_color=C.CARD, corner_radius=14,
                                      border_width=1, border_color=C.CARD_BORDER)
            chart_card.pack(fill="x", padx=20, pady=(8, 0))
            ctk.CTkLabel(chart_card, text="📅  " + _("ultimos_7_dias"), font=F(10, "bold"),
                         text_color=C.TEXT_DIM).pack(anchor="w", padx=14, pady=(10, 4))
            _dibujar_grafico(chart_card, history, meta)

        bf = ctk.CTkFrame(main, fg_color="transparent")
        bf.pack(pady=(10, 12))
        if on_export:
            ctk.CTkButton(bf, text="📥  " + _("exportar_stats"), fg_color=C.BG3, text_color=C.TEXT,
                          font=F(9), corner_radius=12, width=130, height=30,
                          command=on_export).pack(side="left", padx=3)
        if on_import:
            ctk.CTkButton(bf, text="📤  " + _("importar_stats"), fg_color=C.BG3, text_color=C.TEXT,
                          font=F(9), corner_radius=12, width=130, height=30,
                          command=on_import).pack(side="left", padx=3)
        ctk.CTkButton(bf, text=_("cerrar"), fg_color=C.ACCENT, text_color="#FFFFFF",
                      font=F(10, "bold"), corner_radius=12, width=100, height=30,
                      command=self.destroy).pack(side="left", padx=3)
        self.center()

    def _set_period(self, period: str) -> None:
        self._period.set(period)
        from pausa_activa.windows._toast import toast
        toast(_("toast_info"), f"Período: {period}", kind="info")
