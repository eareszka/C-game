"""34 Anaye: p_0..8 into the game's sheet (idle_sheet.png, one view in all 8 rows) and a stacked review. Nothing installed.

    python art/enemies/pixellab/34_anaye/redo_bc/anim/pack.py
"""
import sys
from collections import Counter
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet
frames = [Image.open(HERE / f'p_{i}.png').convert('RGBA') for i in range(9)]
sheet = enemy_sheet.sheet_of({d: frames for d in enemy_sheet.ORDER}, True)   # every row the same view: the helper mirrors left rows otherwise, and the coded blade point assumes one
sheet.save(HERE.parent / 'idle_sheet.png')
c = Counter(p[:3] for p in sheet.get_flattened_data() if p[3])
print(sheet.size, len(c), 'colours', sorted('%02x%02x%02x' % k for k in c))
W, H = 130, 118
print('rows identical', all(sheet.crop((0, d * H, 9 * W, (d + 1) * H)).tobytes() == sheet.crop((0, 0, 9 * W, H)).tobytes() for d in range(8)))
print('feet row', {f.getbbox()[3] for f in frames})
print('distinct', len({f.tobytes() for f in frames}))
