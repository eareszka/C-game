"""34 Anaye's redo into the game (approved by the user 2026-11-04): 130x118 cells, one view in all 8 directions, one row a direction, 9 poses from anim2/stepped.py: 0 1 idle; 1 2 3 4 lift; 5 6 7 8 slam. Anaye::anim_frame picks each pose against its next shot, 260 ms a pose.
assets/enemies/34_anaye.png, the old sheet, stays where it is.

    python art/enemies/pixellab/34_anaye/redo2/install.py
"""
from pathlib import Path
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H = 130, 118
POSES = (0, 1, 3, 4, 6, 7, 9, 11, 13)
FRAMES = len(POSES)
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
dest = ROOT / 'assets/enemies/redraws/34_anaye.png'
sheet = Image.new('RGBA', (W * FRAMES, H * 8))
for d in range(8):
    for i, n in enumerate(POSES):
        sheet.paste(Image.open(HERE / 'anim2' / f'c_{n}.png').convert('RGBA'), (i * W, d * H))
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, True, palette=palette)
print('installed', dest.name, sheet.size, len(palette) - 1, 'colours + black')
rec = ROOT / 'assets/enemies/redraws/installation.json'
data = json.loads(rec.read_text(encoding='utf-8'))
listed = data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))
entry = {'id': 34, 'sheet': 'idle', 'png': 'assets/enemies/redraws/34_anaye.png', 'aseprite': 'assets/enemies/redraws/34_anaye.aseprite',
         'source': 'art/enemies/pixellab/34_anaye/redo2/frame0.png', 'frame_size': [W, H], 'frames': FRAMES, 'rows': True,
         'tags': list(ORDER), 'make': 'animate', 'job': 'art/enemies/pixellab/34_anaye/redo2/install.py'}
at = [n for n, e in enumerate(listed) if e.get('id') == 34]
if at: listed[at[0]:at[-1] + 1] = [entry]
else: listed.append(entry)
rec.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
