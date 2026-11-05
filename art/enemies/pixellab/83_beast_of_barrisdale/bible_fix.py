"""83 Beast of Barrisdale's battle sheet brought to the bible, its design kept (the user, 2026-10-29: "fix to
bible, keep design"; PixelLab's restyle changed 14 px and its clean added two colours, so the drawn sheet is the
start). It was already eight colours on the game palette; what failed was its outline -- open at its wing tips
and a leg -- and lone pixels. Each of its ten frames through tidy.tidy() (specks folded, the outline closed,
interior black to 14%); its one-pixel white eyes, teeth and drool kept. Its one view faces left on every row,
as the fight draws it (not mirrored to the right as enemy_sheet's tagless rows would be). Writes idle_sheet.png
for pixellab_enemy.py install, and frame 0 as idle_frame0_clean.png.

    python art/enemies/pixellab/83_beast_of_barrisdale/bible_fix.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from tidy import tidy

FW, FH, FRAMES = 100, 65, 10
src = Image.open(ROOT / 'assets/enemies/83_beast_of_barrisdale.png').convert('RGBA')
frames = [tidy(src.crop((f * FW, 0, (f + 1) * FW, FH))) for f in range(FRAMES)]
sheet = Image.new('RGBA', (FRAMES * FW, 8 * FH), (0, 0, 0, 0))
for row in range(8):
    for f, im in enumerate(frames):
        sheet.paste(im, (f * FW, row * FH))
sheet.save(HERE / 'idle_sheet.png')
frames[0].save(HERE / 'idle_frame0_clean.png')
for f, im in enumerate(frames):
    im.save(HERE / f'fixed_{f}.png')
print(len({p[:3] for p in sheet.get_flattened_data() if p[3]} - {(0, 0, 0)}), 'colours + black')
