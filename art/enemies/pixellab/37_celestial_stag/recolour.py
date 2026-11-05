"""37 Celestial Stag's source for its frame-0 restyle: its old frame 0 (assets/enemies/37_celestial_stag.png) on
the colours of the reality-shard cave and its torches (the user, 2026-10-30: its current design, "the colors are
supposed to be like the reality shard cave atmosphere and torches"; its antlers the rainbow torch flame).
  coat 4048a0 -> the cave's base 664b95, its shade 2c3070 -> 2b1f40, its light 7078d0 -> the cave's lit b69cee
  its gold antlers -> the torch's rainbow: slanted stripes two pixels wide of its pale tones (src/dungeon.cpp
      RAINBOW), as torch_light() draws them
  its white stars -> lilac, each two pixels (a lone pixel is a speck), its white tail tip -> fcfcfc
Writes source_recolour_old.png on the 98x65 cell, feet on the bottom row (the first source; the user then had the
silhouette redrawn, concepts/), and base/37_celestial_stag.png: the old sheet padded into 98x65 cells, FRAMES a
direction (its three repeated to five: the antlers strobe as the torches do, five frames at 150 ms), the job's
"png", sized as the sheet it will become.

    python art/enemies/pixellab/37_celestial_stag/recolour.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
OLD = ROOT / 'assets/enemies/37_celestial_stag.png'
CW, CH, W, H = 58, 64, 98, 65
OLD_FRAMES, FRAMES = 3, 5
MAP = {'4048a0': '664b95', '2c3070': '2b1f40', '7078d0': 'b69cee', 'e8e8f8': 'fcfcfc'}
GOLD = {'f0c840', 'b08820', 'fff0a0'}
STARS = {'f8f8d0'}
RAINBOW = ['ec8476', 'fae488', 'a8f0bc', '84a7e9', 'b69cee']   # the torch's pale stripes (its peach left out: 8 colours)


def stripe(x, y, f=0):
    return h(RAINBOW[((x + y + 64) // 2 + f) % len(RAINBOW)])


old = Image.open(OLD).convert('RGBA')
base = Image.new('RGBA', (W * 8 * FRAMES, H))
for d in range(8):
    for f in range(FRAMES):
        i = d * OLD_FRAMES + min(f, OLD_FRAMES - 1)
        base.alpha_composite(old.crop((i * CW, 0, i * CW + CW, CH)), ((d * FRAMES + f) * W + (W - CW) // 2, H - CH))
base.save(HERE / 'base/37_celestial_stag.png')

f0 = old.crop((0, 0, CW, CH))
px = f0.load()
stars = []
for y in range(CH):
    for x in range(CW):
        p = px[x, y]
        if not p[3]: continue
        k = '%02x%02x%02x' % p[:3]
        if k in MAP: px[x, y] = h(MAP[k]) + (255,)
        elif k in GOLD and k != 'fff0a0' or (k == 'fff0a0' and y < 24): px[x, y] = stripe(x, y) + (255,)
        elif k in STARS: stars.append((x, y))
for x, y in stars:
    px[x, y] = h('b69cee') + (255,)
    if px[x + 1, y][3] and px[x + 1, y][:3] == h('664b95'): px[x + 1, y] = h('b69cee') + (255,)
box = f0.getbbox()
f0 = f0.crop(box)
out = Image.new('RGBA', (W, H))
out.paste(f0, ((W - f0.width) // 2, H - f0.height))
out.save(HERE / 'source_recolour_old.png')
print(out.getbbox())
