"""83 Beast of Barrisdale's flying sheet (its phase-two alt, assets/enemies/83_beast_of_barrisdale_fly.png)
brought to the bible as its idle was (bible_fix.py; the user approved that, 2026-10-29): its design kept, its
outline open at claw tips and wing edges on every frame, so each of its ten frames through tidy.tidy(), every
row its one left-facing view. Reinstalled in place through enemy_sheet.install (its .aseprite repacked, the
build recorded).

    python art/enemies/pixellab/83_beast_of_barrisdale/fly_fix.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))
from tidy import tidy
import enemy_sheet

FW, FH, FRAMES = 100, 65, 10
PNG = ROOT / 'assets/enemies/83_beast_of_barrisdale_fly.png'
src = Image.open(PNG).convert('RGBA')
frames = [tidy(src.crop((f * FW, 0, (f + 1) * FW, FH))) for f in range(FRAMES)]
for f, im in enumerate(frames):
    im.save(HERE / f'fly_fixed_{f}.png')
sheet = Image.new('RGBA', (FRAMES * FW, 8 * FH), (0, 0, 0, 0))
for row in range(8):
    for f, im in enumerate(frames):
        sheet.paste(im, (f * FW, row * FH))
if '--install' in sys.argv:
    enemy_sheet.built(str(PNG))     # the sheet as it stands is the drawn one, not a hand edit to keep
    enemy_sheet.install(sheet, str(PNG), FRAMES, True, ms=130,
                        palette=sorted('%02x%02x%02x' % c for c in {q[:3] for q in sheet.get_flattened_data() if q[3]}))
    print('installed', PNG)
print(len({p[:3] for p in sheet.get_flattened_data() if p[3]} - {(0, 0, 0)}), 'colours + black')
