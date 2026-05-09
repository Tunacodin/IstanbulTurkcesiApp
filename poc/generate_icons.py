"""PWA icon'larini olustur (Pillow ile).
Ciktilar:
  static/icons/icon-192.png   (Android home screen)
  static/icons/icon-512.png   (App store / splash)
  static/icons/icon-maskable.png  (Android adaptive)
  static/icons/apple-touch-icon.png  (iOS)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent / "static" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BG = (17, 17, 17)        # koyu (--accent)
FG = (255, 255, 255)
ACCENT = (192, 57, 43)   # kırmızı (mikrofon)


def draw_icon(size: int, maskable: bool = False, save_as: str | None = None) -> None:
    img = Image.new("RGB", (size, size), BG if not maskable else (250, 250, 250))
    d = ImageDraw.Draw(img)

    # Maskable için iç bölge ortada %80 alan içinde olmalı (safe zone)
    margin = int(size * 0.10) if maskable else int(size * 0.04)
    inner = size - 2 * margin

    # Koyu arka plan dairesi (maskable'da BG farklı)
    if maskable:
        d.rectangle([0, 0, size, size], fill=(250, 250, 250))
        d.ellipse([margin, margin, size - margin, size - margin], fill=BG)

    # Mikrofon stilize: dikdörtgen + alt çubuk
    cx = size // 2
    body_w = int(inner * 0.34)
    body_h = int(inner * 0.50)
    body_top = int(margin + inner * 0.18)
    body_left = cx - body_w // 2
    body_right = cx + body_w // 2
    body_bottom = body_top + body_h
    radius = body_w // 2
    d.rounded_rectangle(
        [body_left, body_top, body_right, body_bottom],
        radius=radius, fill=ACCENT,
    )

    # Ayak çubuğu
    stand_y = body_bottom + int(inner * 0.06)
    stand_h = int(inner * 0.04)
    d.rectangle(
        [cx - body_w // 2 - 4, stand_y, cx + body_w // 2 + 4, stand_y + stand_h],
        fill=FG,
    )
    # Sap
    d.rectangle(
        [cx - 4, body_bottom, cx + 4, stand_y + stand_h],
        fill=FG,
    )

    # Üstte küçük "İT" harfleri
    try:
        font_size = int(inner * 0.13)
        try:
            font = ImageFont.truetype("seguisb.ttf", font_size)  # Windows Segoe UI Semibold
        except OSError:
            font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    text = "İT"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(((size - tw) / 2, margin + int(inner * 0.02)), text, fill=FG, font=font)

    out = OUT_DIR / (save_as or f"icon-{size}.png")
    img.save(out, "PNG", optimize=True)
    print(f"  yazıldı: {out}")


for sz in [192, 512]:
    draw_icon(sz)
draw_icon(512, maskable=True, save_as="icon-maskable.png")
draw_icon(180, save_as="apple-touch-icon.png")
print("Tamamlandı.")
