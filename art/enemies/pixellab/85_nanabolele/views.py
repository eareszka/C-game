"""85 Nanabolele's views, assigned by eye from the rotate of its approved design (concept 3, the user's pick,
2026-10-29; idle-rotate-result.json). PixelLab took our side-on pose as its "south", so its labels are off:
  D  south-west  -- straight at us, head on, jaws and both eyes
  DR west, mirrored -- the user's art note: its body turned to the right, its head toward the player
  R  south       -- side on, head to the right
  UR east        -- from behind, tail toward us
  U  north-east  -- straight from behind
Each placed on the 98x65 cell, feet on the bottom row, centred; snapped to the game palette, then all five
folded onto eight chosen colours (the rest to their nearest of those, Lab): its green ramp, the glow green and
pale mint of its lights and belly, horn brown, eye orange, tooth white. The near-blacks go to black, then
interior black is thinned to lines as 19's views.py does (blobs take the darkest green).
Writes idle_frame0_clean.png (D) and idle_view_*.png.

    python art/enemies/pixellab/85_nanabolele/views.py
"""
from pathlib import Path
import glob, sys
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap

ROT = ROOT / 'pixellab-out/85-nanabolele/idle-rotate/idle-rotate/rotations/v1'
PICK = {'D': ('south-west-07', False), 'DR': ('west-06', True), 'R': ('south-00', False),
        'UR': ('east-02', False), 'U': ('north-east-03', False)}
W, H = 98, 65

def load(name, mirror):
    im = Image.open(next(ROT.glob(f'*views-{name}.png'))).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            px[x, y] = (0, 0, 0, 0) if p[3] < 128 else tuple(fcremap.nearest(p[:3])[:3]) + (255,)
    im = im.crop(im.getbbox())
    if mirror: im = ImageOps.mirror(im)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(im, ((W - im.width) // 2, H - im.height))
    return out

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
SHADE = (0x14, 0x2e, 0x1f)


def share(im):
    """Black with drawn pixels on all four sides, as a share of the drawn."""
    px = im.load()
    drawn = [(x, y) for y in range(H) for x in range(W) if px[x, y][3]]
    inside = lambda x, y: all(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] for dx, dy in N4)
    return sum(1 for x, y in drawn if px[x, y][:3] == (0, 0, 0) and inside(x, y)) / len(drawn)


def thin(im):
    """Black inside the body with three or four black neighbours is a blob, not a seam: it takes the darkest
    green (then two, if still over the band)."""
    px = im.load()
    inside = lambda x, y: all(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] for dx, dy in N4)
    for need in (4, 3, 2):
        if share(im) <= 0.16:
            break
        for p in [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == (0, 0, 0)
                  and inside(x, y) and sum(px[x + dx, y + dy][:3] == (0, 0, 0) for dx, dy in N4) >= need]:
            px[p] = SHADE + (255,)
    return im


views = {v: load(*PICK[v]) for v in PICK}
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
keep = [h(c) for c in ('142e1f', '235436', '29633e', '4edc4a', 'a8f0bc', '967448', 'fc9838', 'e8e0c0')]
BLACK = {h(c) for c in ('0c0a12', '282828', '200c0e')}
for v, im in views.items():
    px = im.load()
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if p[3] and p[:3] in BLACK:
                px[x, y] = (0, 0, 0, 255)
            elif p[3] and p[:3] != (0, 0, 0) and p[:3] not in keep:
                px[x, y] = min(keep, key=lambda k: fcremap.lab_dist(p[:3], k)) + (255,)
    thin(im)
    print(v, 'interior black', round(100 * share(im)), '%')
    im.save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
print('kept', ['%02x%02x%02x' % c for c in keep])
