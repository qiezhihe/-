"""Build the multi-size Windows icon from the player portrait."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Assets/Art/pixel_portal_v1/runtime/player_portrait.png'
TARGET = ROOT / 'RogueFPS.ico'
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    image = Image.open(SOURCE).convert('RGBA')
    bounds = image.getbbox()
    if bounds:
        image = image.crop(bounds)
    side = max(image.size)
    square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    square.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    square = square.resize((256, 256), Image.LANCZOS)
    square.save(TARGET, format='ICO', sizes=SIZES)
    print(f'Wrote {TARGET} ({", ".join(f"{w}x{h}" for w, h in SIZES)})')


if __name__ == '__main__':
    main()