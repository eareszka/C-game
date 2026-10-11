"""04 Lili, medium tier (a little larger than the 13 px sprite it replaces: 18 px), to
art/direction/SPRITE_STYLE.md: four directions, running only.

    python art/enemies/04_lili_design.py        # writes design.json, 04_lili.txt, draft.png

The user, 2026-10-10: "slightly large", "4 directions running around only". So
three drawn views -- front (D), side (R, mirrored for L), back (U) -- each a
3-frame scuttle (legs one way / under it / the other way, played 0 1 2 1); no
standing idle and no 3/4 views. Then: the front and back "as thin" as the
side view, "only 4 legs" in every view, "slightly less detailed and smaller".

A pink lump that is mostly head: ears, a hot-pink snout, bristles down its
back, and four short tapering legs. The legs grow out of the
body (no line across the hip) and are pink, never black: battles are on black.

Drafted as shapes (silhouette, then outline, then tones by form), then drawn
into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io
from PIL import Image, ImageDraw
PAL = {'K': '000000', 'D': '792727', 'M': 'ec8476', 'L': 'f0b890', 'P': 'fc74b4'}
W, H = 28, 22
GROUND = 19
MIR = lambda p: (W - 1 - p[0], p[1])

def mask(draw_fn):
    im = Image.new('1', (W, H), 0); draw_fn(ImageDraw.Draw(im)); px = im.load()
    return {(x, y) for y in range(H) for x in range(W) if px[x, y]}

def both(s): return s | {MIR(p) for p in s}
def shift(s, dy): return {(x, y + dy) for x, y in s}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
def rim(shape):
    """The pixels just outside a shape: its outline, drawn round it so a 1-px leg keeps its colour."""
    return {(x + dx, y + dy) for (x, y) in shape for dx, dy in N4} - shape

def leg(hip, foot):
    """A leg that tapers from 3 px at the hip to 1 at the foot."""
    (hx, hy), (fx, fy) = hip, foot; out = set()
    for y in range(hy, fy + 1):
        t = (y - hy) / max(1, fy - hy); cx = hx + (fx - hx) * t; w = 3 if t < 0.4 else 2 if t < 0.8 else 1
        x0 = round(cx - (w - 1) / 2); out |= {(x0 + i, y) for i in range(w)}
    return out

def paint(g, shape, tone, line=True):
    """A part in front of what is already there: its fill, and its outline round it."""
    for p in shape: g[p] = tone
    if line:
        for p in rim(shape): g[p] = 'K'

def ell(box): return mask(lambda d: d.ellipse(box, fill=1))

def tones(g, body, light, lower):
    """By form: light on the patch that faces us and up, dark where the body turns under (outside `lower`)."""
    for q in body & light: g[q] = 'L'
    for q in body - lower: g[q] = 'D'

def side(p):
    """Running right. p = -1, 0, 1: the legs' swing; under it (0) it rides a pixel higher."""
    dy = -1 if p == 0 else 0; g = {}
    o = lambda s: shift(s, dy)
    step = lambda hx, way: leg((hx, 13 + dy), (hx + 2 * p * way, GROUND - (1 if p * way > 0 else 0)))
    paint(g, o(mask(lambda d: [d.polygon([(x, 8), (x + 1, 4 + k), (x + 3, 7)], fill=1) for x, k in ((5, 1), (9, 0))])), 'D')   # bristles
    rump, head = o(ell((3, 6, 18, 15))), o(ell((11, 5, 23, 15)))
    ear = o(mask(lambda d: d.polygon([(14, 7), (16, 2), (19, 6)], fill=1)))
    body = rump | head | ear
    near = step(6, 1) | step(10, -1) | step(15, 1) | step(19, -1)              # four legs
    paint(g, body | near, 'M')                                                  # one shape: no line across a hip, or the ear's root
    tones(g, body, o(ell((13, 6, 21, 10)) | ell((6, 7, 11, 9))), o(ell((0, 0, 24, 13))))
    for q in near - body: g[q] = 'M'
    paint(g, o(ell((22, 9, 25, 12))), 'P')                                      # the snout
    g[(19, 8 + dy)] = 'K'                                                       # the eye
    return g

def facing(p, back=False):
    """Running at us (or away): as thin as the side view is tall, two legs each side stepping in turn."""
    dy = -1 if p == 0 else 0; g = {}
    o = lambda s: shift(s, dy)
    def fan(way):                                                              # the left side's legs; the right mirrors, out of time
        up = lambda s: 1 if p * way * s > 0 else 0                             # a lifted leg: a pixel up and a pixel further out
        return [leg((hx, hy + dy), (fx - up(s), GROUND - up(s))) for hx, hy, fx, s in ((9, 12, 7, 1), (12, 13, 11, -1))]
    L, R = fan(1), [{MIR(q) for q in l} for l in fan(-1)]
    ears = o(both(mask(lambda d: d.polygon([(8, 8), (8, 2), (12, 5)], fill=1))))
    ball = o(ell((7, 5, 20, 15)))
    body, legs = ball | ears, set().union(*L, *R)
    paint(g, body | legs, 'M')                                                  # one shape
    tones(g, body, o(ell((9, 6, 18, 8))) if not back else o(ell((9, 6, 18, 10))), o(ell((4, 0, 23, 13))))
    for l in L + R:                                                            # a line between one leg and the next
        for q in rim(l) - body: g[q] = 'K'
    for q in legs - body: g[q] = 'M'
    if back:
        for q in o({(x, y) for x in (13, 14) for y in (6, 7, 9, 10, 12)}): g[q] = 'D'   # the bristles, down its back
        return g
    paint(g, o(ell((11, 10, 16, 13))), 'P')                                      # the snout
    for q in o(both({(11, 7)})): g[q] = 'K'                                       # eyes: one black pixel each, the only black dots on the face (the user)
    return g

VIEWS = {'D': [facing(p) for p in (-1, 0, 1)], 'R': [side(p) for p in (-1, 0, 1)], 'U': [facing(p, True) for p in (-1, 0, 1)]}
rows = lambda g: [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]

if __name__ == '__main__':
    order = [f'{k}{i}' for k in 'DRU' for i in range(3)]
    json.dump({'pal': PAL, 'view_w': W, 'views': {f'{k}{i}': rows(g) for k, fr in VIEWS.items() for i, g in enumerate(fr)}, 'order': order}, open('design.json', 'w'))
    t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + ['#BODY', '13', '#POSE', 'frames', '#DIRS', 'cardinal']
    for k, fr in VIEWS.items():
        for i, g in enumerate(fr): t += [f'#{k}' + (f'@{i}' if i else '')] + rows(g)[:-1]
    io.open('04_lili.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 6, H * 3), (0, 0, 0, 255)); im.paste((255, 170, 200, 255), (W * 3, 0, W * 6, H * 3))
    for r, fr in enumerate(VIEWS.values()):
        for i, g in enumerate(fr):
            for (x, y), c in g.items(): [im.putpixel((b * 3 * W + i * W + x, r * H + y), tuple(int(PAL[c][k:k + 2], 16) for k in (0, 2, 4)) + (255,)) for b in (0, 1)]
    im.resize((im.width * 6, im.height * 6), Image.NEAREST).save('draft.png')
    allg = [g for fr in VIEWS.values() for g in fr]
    assert all(0 <= x < W and 0 <= y < H - 1 for g in allg for x, y in g), 'drawn outside the frame'
    ys = [y for g in allg for (x, y), c in g.items() if c != 'K']; print('rows', min(ys), max(ys), 'tall', max(ys) - min(ys) + 1)
