from __future__ import annotations

FONT_MULTIPLIERS: dict[str, float] = {
    "pequeno": 0.85,
    "normal": 1.0,
    "grande": 1.15,
    "muy_grande": 1.3,
}

_font_mult: float = 1.0


def set_font_size(key: str) -> None:
    global _font_mult
    _font_mult = FONT_MULTIPLIERS.get(key, 1.0)


def F(size: int, weight: str = "") -> tuple:
    scaled = max(8, round(size * _font_mult))
    return ("Segoe UI", scaled, weight) if weight else ("Segoe UI", scaled)
