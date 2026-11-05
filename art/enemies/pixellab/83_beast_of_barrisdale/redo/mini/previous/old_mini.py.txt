"""83 Beast of Barrisdale's map mini: the roaring winged beast of Knoydart at the player's scale, four views, two
frames (tools/minis.py).

IN FLIGHT (the user: "this is a flier") and compact, squished together as its flying sheet has it (the user:
"use pixellab make it more squished together, that's too far lanky"). Through PixelLab (art/enemies/pixellab/
83_beast_of_barrisdale/mini, pixellab-out/83-mini-small, four generations): eight rotations of its battle flying
frame (assets/enemies/83_beast_of_barrisdale_fly.png) sent at 26 px tall, so PixelLab draws it at about the mini's
size and the shrink keeps its face (a first try at full size, pixellab-out/83-mini, shrank to a blob); then its
front (south-east: it faces us), back (north-west) and side (west) each given a hover, its fan of wings beating, its tucked legs and hooked claws flexing. Each mini frame is
one of those on the mini's palette (minis.recolour) pixel for pixel -- no shrink, which blurred the face away --
its own black lines kept, scaled by one SCALE for every view, one black outline round it: wings up, then wings down -- its wingbeat as it hovers
over its shadow. The right view is the left mirrored. 28 px tall with its outline at the front, a little over Alber's mini (the user: "needs be larger like
alber mini"), over its battle height (57 px) at the minis' one scale (20). Three of its battle colours and black:
its charcoal, the salmon of its wings, face and claws, the red of its wing ribs and mouth.

Its chase: the swoop (chase_speed(), src/main.cpp) -- a glide, then wingbeats -- hovering (mini_hover(),
src/main.cpp; it flies, enemy_flies() in include/enemy.h).

    python art/enemies/minis/83_beast_of_barrisdale_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '595965', 'E': 'ec8476', 'R': 'b6433d'}
CHASE = 'swoop'
HOVER = 11               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 28
SRC = ROOT / 'pixellab-out/83-mini-small/animations'
FLIGHTS = {'D': ('v1/flyd', (0, 2)), 'U': ('v2/flyu', (0, 2)), 'L': ('v3/flyl', (0, 2))}   # wings up, wings down


def tone(h, s, v):
    """Its darks black; its greys charcoal (its pale teeth salmon); then by saturation, not brightness (its
    gaping mouth is a bright red): the full reds red -- its mouth, its wing ribs -- the soft ones salmon."""
    if v < 0.22: return 'K'                  # its near-black lines (to 0.2) black, so its parts stay apart
    if s < 0.3: return 'E' if v > 0.85 else 'G'
    return 'R' if s > 0.6 else 'E'


SCALE = 24 / 28          # PixelLab drew it at about the mini's size: its tallest (the front, 28 px inside its
                         # outline) brought within the cell, every view by the same, nearest pixel -- no shrink


def view(name, picks):
    """Each frame on the mini's palette pixel for pixel, its own black lines kept, its outer black taken off and
    the outline redrawn round it, scaled by SCALE, its bottom on the cell's last but one row, centred."""
    letters = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)): k for k, c in PAL.items()}
    out = []
    for i in picks:
        im = minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL)
        im = im.crop(im.getbbox())
        im = im.resize((round(im.width * SCALE), round(im.height * SCALE)), Image.NEAREST)
        g = {(x, y): letters[im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
        edge = {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in ff.N4)}
        g = {p: c for p, c in g.items() if p not in edge}
        xs, ys = [x for x, y in g], [y for x, y in g]
        dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
        out.append(ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()}))
    return out


# Its face, repainted by hand (the user: "keep 3, hand-fix the face"): on three colours the PixelLab face folds to
# a few pink and red pixels. Head on, a pink face with two black eye dots over its gaping red mouth, black inside;
# from the side, its eye and its jaws open. (view, frame): (left, top, rows), on the frame as placed.
FACE_FRONT = ('EEEEE', 'EKEKE', 'ERRRE', 'RKKKR', 'ERRRE')
FACE_SIDE = ('EKEE', 'RRRE', 'KKKE', 'RRRE')
FACES = {('D', 0): (20, 20, FACE_FRONT), ('D', 1): (21, 21, FACE_FRONT), ('L', 0): (7, 16, FACE_SIDE),
         ('L', 1): (9, 13, FACE_SIDE)}

FRAMES = {v: view(*FLIGHTS[v]) for v in FLIGHTS}
for (v, f), (x0, y0, patch) in FACES.items():
    g = {p: c for p, c in FRAMES[v][f].items()}
    for y, r in enumerate(patch):
        for x, c in enumerate(r):
            g[x0 + x, y0 + y] = c
    FRAMES[v][f] = ff.outline(g)          # the outline closed again round the face where it fills a gap
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(83, 'beast_of_barrisdale', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(83, CHASE, FRAMES, PAL, hover=HOVER)
