"""20 Sermilik's frosty breath where PixelLab left it wrong (the user, 2026-10-29: "make sure the blowing ice comes
from the mouth, it doesnt in the right and left frames, and in the back frames its drawn on top when it should
be furthest back drawn"). A puff of breath, white with an ice-blue heart, painted by hand:
  side (R; L mirrors it): blown out of its mouth at the tip of its snout -- big on the breath frame, a smaller
    fading puff after;
  back (U): its mouth faces away, so the puff is behind it -- drawn only where nothing of the bear is, peeking
    out over its head.
One black outline round each puff, on clear pixels only. From the untouched frames in no_breath/.

    python art/enemies/pixellab/20_sermilik/breath.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
PAL = {'W': (0xfc, 0xfc, 0xfc), 'B': (0xdc, 0xf0, 0xff)}
BIG = [
    '..WWW.WW...',
    '.WWBWWWWW..',
    'WWBBBWBWWW.',
    'WWWBBBBWWWW',
    '.WWBWWBBWW.',
    '..WWWWWWW..',
    '....WW.....',
]
SMALL = [
    '.WW.W.',
    'WWBWWW',
    '.WWWW.',
]
# frame: (puff, where its left middle goes, behind the bear?)
PUFFS = {
    'idle_anim_R_4': (BIG, (75, 31), False),       # out of its mouth, touching the snout, the breath frame
    'idle_anim_R_6': (SMALL, (76, 33), False),     # fading, still at its mouth
    'idle_anim_U_7': (BIG, (43, 16), True),        # behind its head: its lower part hidden, the rest peeking over
    'idle_anim_U_8': (SMALL, (45, 15), True),
}


def puff(im, rows, at, behind):
    out = im.copy()
    x0, y0 = at[0], at[1] - len(rows) // 2
    g = {(x0 + x, y0 + y): PAL[c] for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    clear = lambda p: 0 <= p[0] < im.width and 0 <= p[1] < im.height and not im.getpixel(p)[3]
    for p, c in g.items():
        if clear(p) or not behind:
            if 0 <= p[0] < im.width and 0 <= p[1] < im.height:
                out.putpixel(p, c + (255,))
    for (x, y) in g:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in g and clear(q):
                out.putpixel(q, (0, 0, 0, 255))
    return out


def unstreak(im):
    """The back view: PixelLab's breath left a white streak drawn over its back -- back to the plain back pixels
    (the still back view's) wherever the frame has breath colours, or the streak's black edge, down its middle."""
    still = Image.open(HERE / 'idle_view_U.png').convert('RGBA')
    out = im.copy()
    for y in range(22, 43):
        for x in range(40, 57):
            p, q = im.getpixel((x, y)), still.getpixel((x, y))
            streak = set(PAL.values()) | {(0, 0, 0), (0x84, 0xa7, 0xe9)}     # the breath's whites and blues, its edge
            if p[3] and p[:3] in streak and q[3] and q[:3] not in streak:
                out.putpixel((x, y), q)
    return out


for name, (rows, at, behind) in PUFFS.items():
    im = Image.open(HERE / 'no_breath' / f'{name}.png').convert('RGBA')
    if behind:
        im = unstreak(im)
    puff(im, rows, at, behind).save(HERE / f'{name}.png')
    print(name, 'puff', 'behind' if behind else 'in front')
