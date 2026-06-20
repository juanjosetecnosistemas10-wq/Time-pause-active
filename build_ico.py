"""Build a multi-resolution ICO with a person doing active stretches."""
import io
import os
import struct

from PIL import Image, ImageDraw

SIZES = [16, 20, 24, 32, 48, 64, 96, 128, 192, 256]

# Palette
BG_MAIN = (56, 189, 248, 255)
BG_GLOW = (56, 189, 248, 60)
HIGHLIGHT = (186, 230, 253, 100)
FIGURE = (255, 255, 255, 255)
FIGURE_SHADOW = (30, 64, 175, 80)


def _draw_figure(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float) -> None:
    """Draw a person in a standing stretch pose (arms up)."""
    s = scale
    # --- Head ---
    head_r = int(42 * s)
    draw.ellipse([cx - head_r, cy - int(190 * s) - head_r,
                  cx + head_r, cy - int(190 * s) + head_r],
                 fill=FIGURE)

    # --- Body (torso) ---
    body_top = cy - int(148 * s)
    body_bot = cy - int(30 * s)
    body_w = int(28 * s)
    draw.polygon([
        cx - body_w, body_top,
        cx + body_w, body_top,
        cx + int(12 * s), body_bot,
        cx - int(12 * s), body_bot,
    ], fill=FIGURE)

    # --- Left arm (raised up and left) ---
    shoulder_l = (cx - int(24 * s), body_top + int(10 * s))
    elbow_l = (cx - int(100 * s), cy - int(160 * s))
    hand_l = (cx - int(140 * s), cy - int(210 * s))
    draw.line([shoulder_l, elbow_l, hand_l], fill=FIGURE, width=max(2, int(16 * s)))
    # Hand circle
    draw.ellipse([hand_l[0] - int(14 * s), hand_l[1] - int(14 * s),
                  hand_l[0] + int(14 * s), hand_l[1] + int(14 * s)], fill=FIGURE)

    # --- Right arm (raised up and right) ---
    shoulder_r = (cx + int(24 * s), body_top + int(10 * s))
    elbow_r = (cx + int(100 * s), cy - int(160 * s))
    hand_r = (cx + int(140 * s), cy - int(210 * s))
    draw.line([shoulder_r, elbow_r, hand_r], fill=FIGURE, width=max(2, int(16 * s)))
    draw.ellipse([hand_r[0] - int(14 * s), hand_r[1] - int(14 * s),
                  hand_r[0] + int(14 * s), hand_r[1] + int(14 * s)], fill=FIGURE)

    # --- Left leg ---
    hip_l = (cx - int(14 * s), body_bot)
    knee_l = (cx - int(60 * s), cy + int(80 * s))
    foot_l = (cx - int(90 * s), cy + int(170 * s))
    draw.line([hip_l, knee_l, foot_l], fill=FIGURE, width=max(2, int(16 * s)))
    # Foot
    draw.ellipse([foot_l[0] - int(16 * s), foot_l[1] - int(10 * s),
                  foot_l[0] + int(16 * s), foot_l[1] + int(10 * s)], fill=FIGURE)

    # --- Right leg ---
    hip_r = (cx + int(14 * s), body_bot)
    knee_r = (cx + int(60 * s), cy + int(80 * s))
    foot_r = (cx + int(90 * s), cy + int(170 * s))
    draw.line([hip_r, knee_r, foot_r], fill=FIGURE, width=max(2, int(16 * s)))
    draw.ellipse([foot_r[0] - int(16 * s), foot_r[1] - int(10 * s),
                  foot_r[0] + int(16 * s), foot_r[1] + int(10 * s)], fill=FIGURE)


def make_base_icon(base_size: int = 512) -> Image.Image:
    """Create a modern gradient icon with a person doing active stretches."""
    img = Image.new("RGBA", (base_size, base_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    c = base_size // 2
    r = base_size // 2 - base_size // 40
    scale = base_size / 512.0

    # Outer glow ring
    draw.ellipse([c - r - base_size//30, c - r - base_size//30,
                  c + r + base_size//30, c + r + base_size//30],
                 fill=BG_GLOW)

    # Main circle with radial gradient effect
    for i in range(24):
        t = i / 24.0
        cr = int(r * (1 - t * 0.18))
        alpha = int(255 * (1 - t * 0.35))
        draw.ellipse([c - cr, c - cr, c + cr, c + cr],
                     fill=(14, 165, 233, alpha))

    # Inner bright spot (top-left highlight)
    draw.ellipse([c - r//3, c - r//2, c + r//3, c],
                 fill=HIGHLIGHT)

    # Draw the stretching figure
    _draw_figure(draw, c, c + int(40 * scale), scale)

    return img


def save_ico(path: str, images: list[Image.Image]) -> None:
    """Save multiple RGBA images as a multi-resolution ICO."""
    pngs = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        pngs.append(buf.getvalue())
    header_size = 6 + len(images) * 16
    with open(path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(images)))
        offset = header_size
        for img, png in zip(images, pngs):
            w = img.width if img.width < 256 else 0
            h = img.height if img.height < 256 else 0
            f.write(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(png), offset))
            offset += len(png)
        for png in pngs:
            f.write(png)


def main() -> None:
    repo = os.path.dirname(os.path.abspath(__file__))
    base = make_base_icon(512)
    icons = [base.resize((s, s), Image.LANCZOS) for s in SIZES]
    ico_path = os.path.join(repo, "FlowBreak.ico")
    save_ico(ico_path, icons)
    print(f"Saved ICO with {len(SIZES)} sizes: {ico_path}")
    png_path = os.path.join(repo, "FlowBreak_256.png")
    base.resize((256, 256), Image.LANCZOS).save(png_path)
    print(f"Saved PNG: {png_path}")


if __name__ == "__main__":
    main()
