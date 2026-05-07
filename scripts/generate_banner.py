#!/usr/bin/env python3
"""Генерация banners/banner для Telegram (1200×630). Запуск из корня: python scripts/generate_banner.py"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Установите Pillow: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    assets.mkdir(parents=True, exist_ok=True)
    path = assets / "banner.png"

    w, h = 1200, 630
    img = Image.new("RGB", (w, h), "#050008")
    px = img.load()

    # Градиент + виньетка (чёрно‑фиолетовый)
    for y in range(h):
        for x in range(w):
            t = math.hypot(x - w * 0.45, y - h * 0.22) / (w * 0.9)
            v = int(42 + min(108, int(168 * math.exp(-t * 4))))
            bx = max(0, min(255, int(35 + x * 0.012)))
            px[x, y] = (bx // 8, bx // 10, max(35, min(165, int(v))))

    draw = ImageDraw.Draw(img)

    font_big = ImageFont.load_default()
    font_sub = ImageFont.load_default()

    try:
        font_big = ImageFont.truetype("arial.ttf", 68)
        font_sub = ImageFont.truetype("arial.ttf", 40)
        font_mini = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_mini = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except OSError:
            font_mini = font_sub

    title = "Wixyeez UC Shop"
    subtitle = "Безопасно · Оперативно · 24/7"
    badges = ["PayCore"]

    glow = [(88, 28, 198), (180, 50, 220)]
    xy = (80, h // 4)
    pad = [
        (+3, +3),
        (-3, -3),
        (+3, -3),
        (-3, +3),
    ]
    for dx, dy in pad:
        draw.text((xy[0] + dx, xy[1] + dy), title, fill=glow[0], font=font_big)
    draw.text(xy, title, fill=(237, 233, 255), font=font_big)

    sy = xy[1] + 88
    draw.text((80, sy), subtitle, fill=(196, 181, 232), font=font_sub)

    bx, by = 80, h - 120
    bw, bh = 480, 64
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, outline=(148, 120, 255), width=2)
    draw.text((bx + 24, by + bh // 6), "★★★★★  " + "  ·  ".join(badges), fill=(200, 180, 250), font=font_mini)

    img.save(path, format="PNG", optimize=True)
    print(f"OK: {path}")


if __name__ == "__main__":
    main()
