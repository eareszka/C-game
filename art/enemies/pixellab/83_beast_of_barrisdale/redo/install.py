"""83 Beast of Barrisdale's redo into the game (approved by the user 2026-11-02): grounded, flying and block sheets, one
left-facing view in 8 identical rows, 100x65 cells, from redo/anim. The old sheets are kept beside this file as
previous_installed*.png; assets/enemies/83_beast_of_barrisdale_fly.png, the old flying sheet, stays where it is.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/install.py
"""
from pathlib import Path
import json
import shutil
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H = 100, 65
OUT = ROOT / 'assets/enemies/redraws'
OLD = {'previous_installed.png': OUT / '83_beast_of_barrisdale.png',
       'previous_installed_fly.png': ROOT / 'assets/enemies/83_beast_of_barrisdale_fly.png'}
for name, src in OLD.items():
    if not (HERE / name).exists():
        shutil.copy(src, HERE / name)

SHEETS = [('idle', '83_beast_of_barrisdale.png', 10, 130),
          ('fly', '83_beast_of_barrisdale_fly.png', 10, 130),
          ('block', '83_beast_of_barrisdale_block.png', 7, 286)]
entries = []
for key, name, frames, ms in SHEETS:
    fr = [Image.open(HERE / 'anim' / f'{key}_{i}.png').convert('RGBA') for i in range(frames)]
    sheet = Image.new('RGBA', (W * frames, H * 8))
    for r in range(8):
        for i, f in enumerate(fr):
            sheet.paste(f, (i * W, r * H))
    palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
    enemy_sheet.install(sheet, str(OUT / name), frames, True, ms=ms, palette=palette)
    print('installed', name, sheet.size, len(palette) - 1, 'colours + black')
    entries.append({'id': 83, 'sheet': key, 'png': f'assets/enemies/redraws/{name}',
                    'aseprite': f'assets/enemies/redraws/{name[:-4]}.aseprite',
                    'source': f'art/enemies/pixellab/83_beast_of_barrisdale/redo/anim/{key}_0.png',
                    'frame_size': [W, H], 'frames': frames, 'rows': True, 'tags': ['D', 'UL', 'L', 'DL'],
                    'make': 'animate', 'frame_ms': ms,
                    'job': 'art/enemies/pixellab/83_beast_of_barrisdale/redo/install.py'})

rec = OUT / 'installation.json'
data = json.loads(rec.read_text(encoding='utf-8'))
listed = data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))
at = [n for n, e in enumerate(listed) if e.get('id') == 83]
listed[at[0]:at[-1] + 1] = entries
rec.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
print('installation.json updated')
