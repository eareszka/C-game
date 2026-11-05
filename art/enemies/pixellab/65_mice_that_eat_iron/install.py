"""65 Mice That Eat Iron's battle sheet from its approved gnaw (gnaw/gnaw_N.png; the user approved it 2026-11-02): four
frames at 150 ms, 38x22, one front view in every direction. Installed through enemy_sheet.install (its .aseprite
packed, the build recorded) as assets/enemies/redraws/65_mice_that_eat_iron.png; battle.cpp's entry set by hand.

    python art/enemies/pixellab/65_mice_that_eat_iron/install.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 38, 22, 4
fs = [Image.open(HERE / 'gnaw' / f'gnaw_{i}.png').convert('RGBA') for i in range(FRAMES)]
sheet = Image.new('RGBA', (W * 8 * FRAMES, H))
for d in range(8):
    for i, f in enumerate(fs):
        sheet.paste(f, ((d * FRAMES + i) * W, 0))
dest = ROOT / 'assets/enemies/redraws/65_mice_that_eat_iron.png'
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, False, ms=150, palette=palette)
print('installed', dest, sheet.size, len(palette) - 1, 'colours + black')
