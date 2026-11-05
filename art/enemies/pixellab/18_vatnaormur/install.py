"""18 Vatnaormur's battle sheet from its approved animation (anim/f_N.png; the user approved it 2026-11-02): five frames,
98x65, one front view in every direction (it always faces front). Installed through enemy_sheet.install as
assets/enemies/redraws/18_vatnaormur.png. The old sheet and its pool stay in assets/enemies/, not loaded. battle.cpp's entry and
Vatnaormur's shot points and anim_frame() in enemies.cpp were set by hand to match.

    python art/enemies/pixellab/18_vatnaormur/install.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 98, 65, 5
fs = [Image.open(HERE / 'anim' / f'f_{i}.png').convert('RGBA') for i in range(FRAMES)]
sheet = Image.new('RGBA', (W * 8 * FRAMES, H))
for d in range(8):
    for i, f in enumerate(fs):
        sheet.paste(f, ((d * FRAMES + i) * W, 0))
dest = ROOT / 'assets/enemies/redraws/18_vatnaormur.png'
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, False, ms=260, palette=palette)
print('installed', dest, sheet.size, len(palette) - 1, 'colours + black')
