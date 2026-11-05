"""93 Chipique's redo into the game (approved by the user 2026-11-03): redo3/whole's 8 poses, one view in every direction (the user: no turning),
98x65 cells, one row a direction, the default 260 ms. assets/enemies/93_chipique.png, the old sheet, stays where it is.

    python art/enemies/pixellab/93_chipique/redo3/install.py
"""
from pathlib import Path
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 98, 65, 8
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
dest = ROOT / 'assets/enemies/redraws/93_chipique.png'
sheet = Image.new('RGBA', (W * FRAMES, H * 8))
for d in range(8):
    for i in range(FRAMES):
        sheet.paste(Image.open(HERE / 'whole' / f'c_{i}.png').convert('RGBA'), (i * W, d * H))
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, True, palette=palette)
print('installed', dest.name, sheet.size, len(palette) - 1, 'colours + black')
rec = ROOT / 'assets/enemies/redraws/installation.json'
data = json.loads(rec.read_text(encoding='utf-8'))
listed = data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))
entry = {'id': 93, 'sheet': 'idle', 'png': 'assets/enemies/redraws/93_chipique.png', 'aseprite': 'assets/enemies/redraws/93_chipique.aseprite',
         'source': 'art/enemies/pixellab/93_chipique/redo3/clean/c4_clean.png', 'frame_size': [W, H], 'frames': FRAMES, 'rows': True,
         'tags': list(ORDER), 'make': 'animate', 'job': 'art/enemies/pixellab/93_chipique/redo3/install.py'}
at = [n for n, e in enumerate(listed) if e.get('id') == 93]
if at: listed[at[0]:at[-1] + 1] = [entry]
else: listed.append(entry)
rec.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
