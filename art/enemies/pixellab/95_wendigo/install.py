"""95 Wendigo's redo into the game (approved by the user 2026-11-03): 102x66 cells (the raised arms need the columns), one view in all 8 directions, 3 poses a direction in one row,
the default 0 1 0 2 loop. assets/enemies/95_wendigo.png, the old sheet, stays where it is.

    python art/enemies/pixellab/95_wendigo/install.py
"""
from pathlib import Path
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 102, 66, 3
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
dest = ROOT / 'assets/enemies/redraws/95_wendigo.png'
sheet = Image.new('RGBA', (W * FRAMES * 8, H))
for d, v in enumerate(ORDER):
    for i in range(FRAMES):
        sheet.paste(Image.open(HERE / 'anim' / f'c_{i}.png').convert('RGBA'), ((d * FRAMES + i) * W, 0))
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, False, palette=palette)
print('installed', dest.name, sheet.size, len(palette) - 1, 'colours + black')
rec = ROOT / 'assets/enemies/redraws/installation.json'
data = json.loads(rec.read_text(encoding='utf-8'))
listed = data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))
entry = {'id': 95, 'sheet': 'idle', 'png': 'assets/enemies/redraws/95_wendigo.png', 'aseprite': 'assets/enemies/redraws/95_wendigo.aseprite',
         'source': 'art/enemies/pixellab/95_wendigo/frame0.png', 'frame_size': [W, H], 'frames': FRAMES, 'rows': False,
         'tags': list(ORDER), 'make': 'animate', 'job': 'art/enemies/pixellab/95_wendigo/install.py'}
at = [n for n, e in enumerate(listed) if e.get('id') == 95]
if at: listed[at[0]:at[-1] + 1] = [entry]
else: listed.append(entry)
rec.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
