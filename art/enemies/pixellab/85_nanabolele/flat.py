"""85 Nanabolele flattened (the user, 2026-10-29, on 36 Cu Sith: "too many versions of green, it should look more
flat" -- "this also goes for the aquatic green glowing dragon"): its body's mid green folded into its main green,
so its hide is one green and one dark shade (the glow green of its spines and the pale mint of its belly kept),
then 36's views.flat() on every frame: a patch of one colour of six pixels or fewer takes the colour round it,
sparing its eyes, teeth, horns and glow, which are never given out either. Reinstalled through enemy_sheet.install
(.aseprite repacked, build recorded); the installed sheet before this is kept as 85_nanabolele_before_flat.png here.

    python art/enemies/pixellab/85_nanabolele/flat.py [--install]
"""
from pathlib import Path
import shutil
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/enemies/pixellab/36_cu_sith'))
import enemy_sheet
import views

h = views.h
FOLD = {h('235436'): h('29633e')}
SPARE = {h(c) for c in ('fc9838', 'e8e0c0', '4edc4a', '967448')}
PNG = ROOT / 'assets/enemies/redraws/85_nanabolele.png'
BEFORE = HERE / '85_nanabolele_before_flat.png'
W, H = 98, 65

if not BEFORE.exists(): shutil.copy(PNG, BEFORE)
im = Image.open(BEFORE).convert('RGBA')
out = Image.new('RGBA', im.size)
for i in range(im.width // W):
    c = im.crop((i * W, 0, i * W + W, H))
    px = c.load()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] and px[x, y][:3] in FOLD: px[x, y] = FOLD[px[x, y][:3]] + (255,)
    out.paste(views.flat(c, spare=SPARE), (i * W, 0))
out.save(HERE / 'flat_sheet.png')
print(len({p[:3] for p in out.get_flattened_data() if p[3]} - {(0, 0, 0)}), 'colours + black')
if '--install' in sys.argv:
    frames, rows = {p: (f, r) for p, f, r in enemy_sheet.battle_sheets()}['assets/enemies/redraws/85_nanabolele.png']
    enemy_sheet.built(str(PNG))
    enemy_sheet.install(out, str(PNG), frames, rows, ms=250,
                        palette=sorted('%02x%02x%02x' % c for c in {q[:3] for q in out.get_flattened_data() if q[3]}))
    print('installed', PNG.relative_to(ROOT))
