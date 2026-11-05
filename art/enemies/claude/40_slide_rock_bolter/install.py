"""40 Slide-Rock Bolter's battle sheet from its approved frame 0 (big.py's big_frame0.png; the user, 2026-10-30:
"no animation, we are just going to do frame 0s"): one view, front only, so every direction's cells hold the
same frame -- three identical frames a direction, the game's default {0,1,0,2} loop, which stands still.
Installed through enemy_sheet.install (its .aseprite packed, the build recorded) as
assets/enemies/redraws/40_slide_rock_bolter.png; battle.cpp's entry switched to it by hand; redraw_status marked.

    python art/enemies/claude/40_slide_rock_bolter/install.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 98, 65, 3
f0 = Image.open(HERE / 'big_frame0.png').convert('RGBA')
sheet = Image.new('RGBA', (W * 8 * FRAMES, H))
for i in range(8 * FRAMES):
    sheet.paste(f0, (i * W, 0))
dest = str(ROOT / 'assets/enemies/redraws/40_slide_rock_bolter.png')
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, dest, FRAMES, False, ms=250, palette=palette)
print('installed', dest, sheet.size, len(palette) - 1, 'colours + black')
