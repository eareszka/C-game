"""46 Lusca's redo into the game (approved by the user 2026-11-03): 98x65 cells, 8 directions of 3 poses in one row,
the default 0 1 0 2 loop. assets/enemies/46_lusca.png, the old sheet, stays where it is.

    python art/enemies/pixellab/46_lusca/redo/install.py
"""
from pathlib import Path
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 98, 65, 3
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
dest = ROOT / 'assets/enemies/redraws/46_lusca.png'
sheet = Image.new('RGBA', (W * FRAMES * 8, H))
for d, v in enumerate(ORDER):
    for i in range(FRAMES):
        sheet.paste(Image.open(HERE / 'anim' / f'{v}_{i}.png').convert('RGBA'), ((d * FRAMES + i) * W, 0))
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, False, palette=palette)
print('installed', dest.name, sheet.size, len(palette) - 1, 'colours + black')
rec = ROOT / 'assets/enemies/redraws/installation.json'
data = json.loads(rec.read_text(encoding='utf-8'))
listed = data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))
entry = {'id': 46, 'sheet': 'idle', 'png': 'assets/enemies/redraws/46_lusca.png', 'aseprite': 'assets/enemies/redraws/46_lusca.aseprite',
         'source': 'art/enemies/pixellab/46_lusca/redo/frame0_skinny.png', 'frame_size': [W, H], 'frames': FRAMES, 'rows': False,
         'tags': list(ORDER), 'make': 'animate', 'job': 'art/enemies/pixellab/46_lusca/redo/install.py'}
at = [n for n, e in enumerate(listed) if e.get('id') == 46]
if at: listed[at[0]:at[-1] + 1] = [entry]
else: listed.append(entry)
rec.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
