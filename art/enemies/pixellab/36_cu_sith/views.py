"""36 Cu Sith's views, from its approved redesign (the user, 2026-10-29: concept 3, "mossy dog" -- the green
fairy hound of the Highlands, big as a calf, a shaggy mossy mane, pale underparts, its tail coiled over its back,
great paws; sized up from its old 32x29 cell, "very small for being this difficulty", to the big 98x65 frame most enemies have, "the same size as most other sprites") and, once
approved, the rotate of it (idle-rotate-result.json), its labels a step off, assigned by eye:
  D  south-west (head on), DR its approved draft, R north-west mirrored (side on, it faced left),
  UR north mirrored (rump to us, head up right), U north-east (straight from behind).
Each placed on the 98x65 cell, feet on the bottom row, centred; folded straight onto five chosen game-palette
colours (nearest, Lab; snapping to the whole palette first sent its pale green belly yellow) -- FLAT (the user:
"too many versions of green, it should look more flat"; a chibi restyle, try 2, was "too good" for the rest
of the cast): one coat green and its dark shade, its underparts' pale mint, its dark legs' grey and muzzle
charcoal; its near-blacks black. Then flat(): any patch of one colour of six pixels or fewer takes the colour
round it, so its mane's fur clumps go. Eyes a solid black mark (the bible). Then tidy.tidy(). Writes idle_frame0_clean.png and
idle_view_*.png. fold(), holes() and eyes() are anim.py's too.

    python art/enemies/pixellab/36_cu_sith/views.py
"""
from pathlib import Path
import colorsys
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(HERE))
import fcremap
from tidy import tidy

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
KEEP = [h(c) for c in ('2c6c44', '163623', 'a8f0bc', '474751', '282828')]
ROT = ROOT / 'pixellab-out/36-cu-sith/idle-rotate/idle-rotate/rotations/v1'
FRONT = HERE / 'eyes/md/sprites/v1/eyesd.png'   # the rotate's front, its face redrawn by PixelLab to the 3/4's eye
PICK = {'D': FRONT, 'DR': None, 'R': 'north-west-05', 'UR': 'north-04', 'U': 'north-east-03'}
FLIP = {'R', 'UR'}                       # drawn facing left: mirrored to face right (UR, the user: its head up right)
W, H = 98, 65


def fold(im):
    """Its near-blacks black, the rest onto KEEP."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            if colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))[2] < 0.08: px[x, y] = (0, 0, 0, 255); continue
            px[x, y] = min(KEEP, key=lambda k: fcremap.lab_dist(p[:3], k)) + (255,)
    return im


def flat(im, most=6, spare=()):
    """A patch of one colour (not black, nor one in `spare`: eyes, teeth) of `most` pixels or fewer takes the colour
    most common round it, three passes."""
    from collections import Counter
    px, w, hh = im.load(), im.width, im.height
    n4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    inside = lambda q: 0 <= q[0] < w and 0 <= q[1] < hh
    for _ in range(3):
        seen = set()
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if (x, y) in seen or not c[3] or c[:3] == (0, 0, 0) or c[:3] in spare: continue
                comp, todo = [(x, y)], [(x, y)]; seen.add((x, y))
                while todo:
                    a, b = todo.pop()
                    for dx, dy in n4:
                        q = (a + dx, b + dy)
                        if inside(q) and q not in seen and px[q] == c: seen.add(q); comp.append(q); todo.append(q)
                if len(comp) > most: continue
                nb = Counter(px[q][:3] for a, b in comp for q in ((a + dx, b + dy) for dx, dy in n4)
                             if inside(q) and px[q][3] and px[q] != c and px[q][:3] != (0, 0, 0) and px[q][:3] not in spare)
                if nb:
                    for p in comp: px[p] = nb.most_common(1)[0][0] + (255,)
    return im


# Its eyes alike in every view (the user, 2026-10-30: the 3/4 front's eye is right, "use pixellab, make sure the
# eyes are consistent in all angles"). PixelLab redrew the front's face matched to the 3/4 front (eyes/, a
# style-matched edit): each eye a pale dot with black above it and on its outer side. Its side (PixelLab's side
# edit lost the eye in the muzzle; the user: "take PixelLab's front, copy it to the side") gets the same eye under
# its brow, its muzzle plain dark green (PixelLab striped it black), a charcoal nose at the tip. Stamped after
# tidy(), which would fold the one-pixel dots. (left, top, rows) on the placed view; letters as LET, '.' left as
# drawn. The 3/4 front's eye, the reference, keeps its black dash and takes the same pale dot under it, and is
# put back on its head in frames where PixelLab ran it into the brow's line.
LET = {'K': (0, 0, 0), 'g': h('2c6c44'), 'd': h('163623'), 'c': h('282828'), 'm': h('a8f0bc')}
FACE = {'D': (46, 12, ('..g...g..', '', '', '', 'KK...KK..', 'Km...mK..', '', '', '........g')),   # PixelLab's front eyes,
             # their pale dots put back after tidy; three lone dark-green pixels on its brow and cheek greened
        'R': (61, 15, ('..KK.....', '.gKm.....', 'KdddddK..', 'KddddddK.', 'Kddddddc.', '.dddddddc')),
        'DR': (62, 14, ('gKKg', '.Km.'))}   # the 3/4 front's own eye, its pale dot as the front's: on its head in every frame


def face(im, v):
    if v in FACE:
        x0, y0, rows = FACE[v]
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.': im.putpixel((x0 + x, y0 + y), LET[c] + (255,))
    return im


def holes(im, v):
    return im                            # its mouth shut


def eyes(im):
    return im                            # PixelLab drew them a black mark


if __name__ == '__main__':
    for v, name in PICK.items():
        src = HERE / 'idle_frame0_draft.png' if name is None else name if isinstance(name, Path) else next(ROT.glob(f'*views-{name}.png'))
        im = Image.open(src).convert('RGBA')
        im = flat(fold(im))
        if v in FLIP: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im = im.crop(im.getbbox())
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.paste(im, ((W - im.width) // 2, H - im.height))
        face(tidy(eyes(holes(out, v))), v).save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
        print(v, name)
