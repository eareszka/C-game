"""93 Chipique's choppy frames padded to 100x68 for PixelLab's 1-generation instruction edit, whose sides must be multiples of 4 (1 px added on each side).

    python art/enemies/pixellab/93_chipique/redo3/clean/pad.py
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
OFF = (1, 1)
for i in range(8):
    f = Image.open(HERE.parent / 'long' / f'c_{i}.png').convert('RGBA')
    b = Image.new('RGBA', (100, 68))
    b.paste(f, OFF)
    b.save(HERE / f'in_{i}.png')
