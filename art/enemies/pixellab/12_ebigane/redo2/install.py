"""12 Ebigane's redo into the game (approved by the user 2026-11-03): 104x68 cells, one left view with its right-hand directions (DR R UR) mirrored, as anim/anim.py's poses: idle 3 poses a direction, fly 4.
assets/enemies/12_ebigane.png and _fly.png, the old sheets, stay where they are.

    python art/enemies/pixellab/12_ebigane/redo2/install.py
"""
from pathlib import Path
import json
import sys
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H = 104, 68
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
RIGHT = {'DR', 'R', 'UR'}
rec = ROOT / 'assets/enemies/redraws/installation.json'
data = json.loads(rec.read_text(encoding='utf-8'))
listed = data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))
listed[:] = [e for e in listed if e.get('id') != 12]
for name, stem, frames, png in (('idle', 'c', 3, '12_ebigane.png'), ('fly', 'f', 4, '12_ebigane_fly.png')):
    sheet = Image.new('RGBA', (W * frames * 8, H))
    for d, v in enumerate(ORDER):
        for i in range(frames):
            f = Image.open(HERE / 'anim' / f'{stem}_{i}.png').convert('RGBA')
            sheet.paste(ImageOps.mirror(f) if v in RIGHT else f, ((d * frames + i) * W, 0))
    palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
    enemy_sheet.install(sheet, str(ROOT / 'assets/enemies/redraws' / png), frames, False, palette=palette)
    print('installed', png, sheet.size, len(palette) - 1, 'colours + black')
    listed.append({'id': 12, 'sheet': name, 'png': 'assets/enemies/redraws/' + png, 'aseprite': 'assets/enemies/redraws/' + png.replace('.png', '.aseprite'),
                   'source': 'art/enemies/pixellab/12_ebigane/redo2/frame0.png', 'frame_size': [W, H], 'frames': frames, 'rows': False,
                   'tags': list(ORDER), 'make': 'animate', 'job': 'art/enemies/pixellab/12_ebigane/redo2/install.py'})
rec.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
