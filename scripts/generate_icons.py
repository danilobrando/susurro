"""Generate template PNG icons for the menu bar.

Run once after install — output is checked into the repo so end users don't need PIL:

    python scripts/generate_icons.py

Template images are monochrome black + alpha; macOS tints them to match the
menu bar appearance (white in dark mode, black in light mode).
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent.parent / "susurro" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 44  # @2x of a 22pt menu bar icon
BLACK = (0, 0, 0, 255)


def _new() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _draw_mic(draw: ImageDraw.ImageDraw, *, filled: bool) -> None:
    # Body — rounded rectangle.
    bw, bh = 14, 22
    bx = (SIZE - bw) // 2
    by = 6
    if filled:
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=7, fill=BLACK)
    else:
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=7, outline=BLACK, width=2)
    # Stand arc under the body.
    ax, ay, asize = SIZE // 2 - 12, by + bh - 6, 24
    draw.arc([ax, ay, ax + asize, ay + asize], start=20, end=160, fill=BLACK, width=2)
    # Stem to the base.
    sx, sy = SIZE // 2, ay + 14
    draw.line([sx, sy, sx, sy + 5], fill=BLACK, width=2)
    # Base.
    draw.line([sx - 5, sy + 5, sx + 5, sy + 5], fill=BLACK, width=2)


def make_idle() -> None:
    img, draw = _new()
    _draw_mic(draw, filled=False)
    img.save(OUT_DIR / "idle.png")


def make_recording() -> None:
    img, draw = _new()
    _draw_mic(draw, filled=True)
    img.save(OUT_DIR / "recording.png")


def make_processing() -> None:
    img, draw = _new()
    # Three filled dots — universal "thinking" signal.
    r = 3
    y = SIZE // 2
    for cx in (12, 22, 32):
        draw.ellipse([cx - r, y - r, cx + r, y + r], fill=BLACK)
    img.save(OUT_DIR / "processing.png")


def main() -> None:
    make_idle()
    make_recording()
    make_processing()
    for p in sorted(OUT_DIR.glob("*.png")):
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
