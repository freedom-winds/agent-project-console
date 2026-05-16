"""Generate launcher/icon.ico used by the .exe.

Run:
    python launcher/make_icon.py
"""
import os

from PIL import Image, ImageDraw


def build(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (11, 16, 32, 255))  # #0B1020 dark navy
    d = ImageDraw.Draw(img)
    s = size / 64.0
    # Trunk
    d.rectangle([28 * s, 36 * s, 36 * s, 56 * s], fill=(96, 165, 250, 255))
    # 3-layer tree (largest at bottom)
    d.polygon([(12 * s, 38 * s), (52 * s, 38 * s), (32 * s, 22 * s)], fill=(34, 197, 94, 255))
    d.polygon([(16 * s, 28 * s), (48 * s, 28 * s), (32 * s, 14 * s)], fill=(96, 165, 250, 255))
    d.polygon([(20 * s, 18 * s), (44 * s, 18 * s), (32 * s, 6 * s)], fill=(167, 139, 250, 255))
    return img


def main() -> None:
    here = os.path.abspath(os.path.dirname(__file__))
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [build(s) for s in sizes]
    out_ico = os.path.join(here, "icon.ico")
    images[0].save(out_ico, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[1:])
    out_png = os.path.join(here, "icon.png")
    build(128).save(out_png, format="PNG")
    print("wrote", out_ico)
    print("wrote", out_png)


if __name__ == "__main__":
    main()
