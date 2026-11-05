"""38 Igtuk's views, from its redesign after A Book of Creatures' illustration (sketch.py; PixelLab's
instruction-only edit, try 2, cleaned the sketch -- the style-matched route was refused, out of credits) and, once
approved, the rotate of it.
Each placed on the 98x65 cell, feet on the bottom row, centred; folded onto seven game-palette colours (nearest,
Lab), flat as the user wants the cast (memory: enemy-art-flat-few-shades): its pale blue-grey hide and one shade,
its far legs' and beard's dark grey and one shade, its mouth's pink and the dark inside it, its eye's white; its
near-blacks black. Then 37's smooth() idea for its hide (each hide pixel the colour most of its eight neighbours
have) and 36's flat() (patches of six pixels or fewer merged, sparing its eye and mouth); tidy.tidy(); the eye
stamped (FACE). Writes idle_frame0_clean.png and idle_view_*.png.

    python art/enemies/pixellab/38_igtuk/views.py
"""
from pathlib import Path
import colorsys
import importlib.util
import sys
from collections import Counter
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(HERE))
import fcremap
import tidy as tidy_mod
from tidy import tidy
_spec = importlib.util.spec_from_file_location('cu_views', ROOT / 'art/enemies/pixellab/36_cu_sith/views.py')
cu = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cu)

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
HIDE, HIDE_D, DARK, DARK_D = h('a4aaba'), h('848694'), h('595965'), h('34343e')
MOUTH, MOUTH_D, WHITE = h('ec8476'), h('5e486a'), h('fcfcfc')
KEEP = [HIDE, HIDE_D, DARK, DARK_D, MOUTH, MOUTH_D, WHITE]
# Blue (the user: "make it blue but within the game's art style"): folded in its greys, as PixelLab drew it, then
# its greys onto the palette's blues, step for step -- its hide the light blue and the mid blue under it, its far
# legs and beard the deep blue and the darkest grey -- as 35 Lomie's coat went blue.
BLUE = {HIDE: h('84a7e9'), HIDE_D: h('375a94'), DARK: h('37387b'), DARK_D: h('34343e')}


def blue(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] and px[x, y][:3] in BLUE: px[x, y] = BLUE[px[x, y][:3]] + (255,)
    return im
ROT = ROOT / 'pixellab-out/38-igtuk/idle-rotate/idle-rotate/rotations/v1'
PICK = {'DR': 'south-west-07', 'R': None, 'UR': 'south-east-01'}
# No head-on or from-behind view (the user, 2026-10-30: "the front and back angles don't really work for this
# sprite, treat it like the Snawfus"): walking toward us it shows its 3/4 front (D a copy of DR), away from us its
# 3/4 back (U falls back to UR, tools/enemy_sheet.SOURCE). Its head-on work (cavity(), the brow fur ball) is kept
# for the record, unused.
# By eye (the rotate took the approved right side view as its "south"): D west (head on, jaw open), DR south-west,
# R the approved pose (the user: "that's the right facing pose"), UR south-east (from behind, head up right), U east.
FLIP = set()
W, H = 98, 65
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def unblue(im):
    """A rotated view (PixelLab turned the blue still): its pixels onto the blue colours, then back to the greys the
    rest of the steps work in."""
    back = {v: k for k, v in BLUE.items()}
    keep = list(BLUE.values()) + [MOUTH, MOUTH_D, WHITE]
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            if colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))[2] < 0.08: px[x, y] = (0, 0, 0, 255); continue
            c = min(keep, key=lambda k: fcremap.lab_dist(p[:3], k))
            px[x, y] = back.get(c, c) + (255,)
    return im


def fold(im):
    """Its near-blacks black; its pinks the mouth's two (by brightness: the palette has no dusky pink); the rest
    onto KEEP."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            hu, sa, va = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
            if va < 0.08: px[x, y] = (0, 0, 0, 255); continue
            if sa > 0.25 and (hu * 360 >= 290 or hu * 360 <= 20):
                px[x, y] = (MOUTH if va > 0.55 else MOUTH_D) + (255,); continue
            px[x, y] = min(KEEP, key=lambda k: fcremap.lab_dist(p[:3], k)) + (255,)
    return im


def smooth(im, passes=2):
    """Flatter: each grey pixel takes the grey most of its eight grey neighbours have, so shade sits in patches."""
    px, w, hh = im.load(), im.width, im.height
    greys = (HIDE, HIDE_D, DARK, DARK_D)
    for _ in range(passes):
        new = {}
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if not c[3] or c[:3] not in greys: continue
                n = Counter(px[x + dx, y + dy][:3] for dx, dy in N8
                            if 0 <= x + dx < w and 0 <= y + dy < hh and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in greys)
                top = n.most_common(1)
                if top and top[0][1] >= 5 and top[0][0] != c[:3]: new[x, y] = top[0][0]
        for p, c in new.items(): px[p] = c + (255,)
    return im


def flat(im):
    return cu.flat(smooth(im), most=8, spare={WHITE, MOUTH, MOUTH_D})


LET = {'K': (0, 0, 0), 'h': HIDE, 'd': HIDE_D, 'W': WHITE}
# Its eye to the bible (the user: "match it to the bible"): the shrink made its white eye ball a black blob; it
# becomes the cast's eye (Cu Sith's, 36): black above and behind a pale dot toward its snout -- small, where the
# Book of Creatures' great eye is, level with its jaw. Its snout's hair tuft, left floating a row above the snout
# by the shrink, joined to it by a pixel of its stalk. (left, top, rows), '.' left as drawn.
FACE = {'R': (63, 33, ('hKKhh', 'hKWhh', 'hhhhh')), 'tuft': (74, 27, ('K',)),
        'D': (42, 31, ('KK............', 'KW..........KK', '............WK')),    # the rotate's two eye dots,
        'DR': (56, 32, ('KK', 'KW'))}                                              # each given the cast's black


# Its black fur ball (the hair tuft at its snout's tip) seen in every view as the side view has it (the user: it
# "needs to be seen from front", and "looks off" in the 3/4 front views, where PixelLab drew it as a post): a small
# round dark ball in a black ring on a one-pixel stalk. The front: the forehead scribble PixelLab left (a "3")
# cleared, the ball there, on its brow above the eyes, its stalk end-on. The 3/4 front: the post cleared ('t', empty) and the ball set on
# the stalk rising from its snout. (left, top, rows), '.' left as drawn.
FUR = {'D': [(47, 24, ('hhhhh', 'hhhhh', 'hhhhh', 'hhhhh')),      # head on, its snout points at us: the ball on its
             (48, 22, ('.KKK.', 'KGGGK', 'KGGGK', '.KKK.'))],    # brow over the eyes (the user circled the spot)
       'DR': [(59, 23, ('tttttttt', 'tttttttt', 'tttttttt', 'tttttttt', '.KK.....')),
              (65, 21, ('..K..', 'KKGK.', 'KGGGK', '.KKK.', '..K..')),
              (55, 28, ('hhhhhhhhhKK',))]}  # the post's root on its crown smoothed to hide, the outline stepping to its snout


def fur(im, v):
    let = dict(LET, G=DARK_D, t=None)
    for x0, y0, rows in FUR.get(v, ()):
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == '.': continue
                im.putpixel((x0 + x, y0 + y), (0, 0, 0, 0) if c == 't' else let[c] + (255,))
    return im


def face(im, v):
    fur(im, v)
    if v == 'R' and 'tuft' in FACE:
        x0, y0, rows = FACE['tuft']
        im.putpixel((x0, y0), (0, 0, 0, 255))
    if v in FACE:
        x0, y0, rows = FACE[v]
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.': im.putpixel((x0 + x, y0 + y), LET[c] + (255,))
    return im


WIDE = 74                                # its drawn width: its peers' side views are 64-74 wide, 48-58 tall
                                         # (the user: "bring it to correct size"); it was 88x54


def shrink(im, wide=WIDE):
    """Scaled down by blocks: each new pixel the most common colour of the drawn pixels its block covers, black
    when black is two in five of them (so its lines stay), empty when the block is mostly empty."""
    im = im.crop(im.getbbox())
    s = wide / im.width
    w, hh = wide, round(im.height * s)
    px = im.load()
    out = Image.new('RGBA', (w, hh))
    for y in range(hh):
        for x in range(w):
            cells = [px[i, j] for j in range(int(y / s), max(int(y / s) + 1, int((y + 1) / s)))
                     for i in range(int(x / s), max(int(x / s) + 1, int((x + 1) / s))) if i < im.width and j < im.height]
            drawn = [c[:3] for c in cells if c[3]]
            if len(drawn) * 2 < len(cells): continue
            k = drawn.count((0, 0, 0))
            col = Counter(c for c in drawn if c != (0, 0, 0)).most_common(1)
            out.putpixel((x, y), ((0, 0, 0) if not col or k * 5 >= 2 * len(drawn) else col[0][0]) + (255,))
    return out


def seams(im):
    """Interior black to the bible's 9-14% (the fold left 1.7%): where its pale hide meets a darker part (its far
    legs, its beard, its mouth), the darker part's pixel on the edge goes black -- the line that separates the
    near legs from the far, the beard from the jaw."""
    px, w, hh = im.load(), im.width, im.height
    light = {HIDE, HIDE_D}
    dark = {DARK, DARK_D, MOUTH_D, MOUTH}                # its mouth's pink too: the line of its lips
    edge = [(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] in dark
            and any(0 <= x + dx < w and 0 <= y + dy < hh and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in light
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in edge: px[p] = (0, 0, 0, 255)
    # and where its two far legs (dark grey) cross its beard and each other (their shade), the shade's edge pixel
    # black, two in three of them: the far legs drawn apart, not a dark smear
    for i, (x, y) in enumerate([(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] == DARK_D
                                and any(0 <= x + dx < w and 0 <= y + dy < hh and px[x + dx, y + dy][:3] == DARK and px[x + dx, y + dy][3]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]):
        if i % 3: px[x, y] = (0, 0, 0, 255)
    return im


def cavity(im, raw):
    """Its open mouth's black hole as drawn (the user: the front "is not very readable"): tidy() caps interior
    black at the bible's 14% and filled the gaping mouth -- the front's whole face -- with blue. Every pixel black
    in `raw` (the view before tidy) and joined through black to its mouth's pink goes back to black."""
    rp, px, w, hh = raw.load(), im.load(), im.width, im.height
    black = lambda q: rp[q][3] and rp[q][:3] == (0, 0, 0)
    pink = {MOUTH, MOUTH_D}
    todo = [(x, y) for y in range(hh) for x in range(w) if black((x, y))
            and any(0 <= x + dx < w and 0 <= y + dy < hh and rp[x + dx, y + dy][3] and rp[x + dx, y + dy][:3] in pink
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    seen = set(todo)
    while todo:
        x, y = todo.pop()
        px[x, y] = (0, 0, 0, 255)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < w and 0 <= q[1] < hh and q not in seen and black(q):
                seen.add(q); todo.append(q)
    return im


def place(im):
    im = im.crop(im.getbbox())
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(im, ((W - im.width) // 2, H - 1 - im.height))   # a row left under its feet for tidy's outline
    return out


if __name__ == '__main__':
    for v, name in PICK.items():
        if name is None:                 # the approved pose: from PixelLab's draft, brought to size
            im = place(shrink(flat(fold(Image.open(HERE / 'idle_frame0_draft.png').convert('RGBA')))))
        elif v == 'D':                   # head on: its mouth is its face -- no seams, the cavity kept black
            im = place(flat(unblue(Image.open(next(ROT.glob(f'*views-{name}.png'))).convert('RGBA'))))
            blue(face(cavity(tidy(im.copy()), im), v)).save(HERE / 'idle_frame0_clean.png')
            print(v, name); continue
        else:                            # a rotated view: at size already
            im = place(flat(unblue(Image.open(next(ROT.glob(f'*views-{name}.png'))).convert('RGBA'))))
        if v in FLIP: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im = face(tidy(seams(im)), v)
        if v in FUR:                     # the cleared post's edges closed again, the ball's dark spared
            tidy_mod.KEEP = {DARK_D, WHITE}
            im = tidy(im)
            tidy_mod.KEEP = set()
        blue(im).save(HERE / f'idle_view_{v}.png')
        if v == 'DR': blue(im).save(HERE / 'idle_frame0_clean.png')     # D: the 3/4 front
        print(v, name)
