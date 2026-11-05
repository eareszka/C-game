"""83 Beast of Barrisdale's map mini: the redrawn beast (2026-11-02) at the player's scale, four views, two frames
(tools/minis.py).

IN FLIGHT, as it flies in battle, its head low. Through PixelLab (pixellab-out/83-redo-mini, four generations): eight
rotations of its approved flying frame (art/enemies/pixellab/83_beast_of_barrisdale/redo/anim/key_fly.png) sent at 26 px
tall, then its front (south-east: it faces us), back (north-west) and side (south: PixelLab's labels are off here) each
given a wingbeat. Each frame on the mini's palette pixel for pixel, its own black lines kept, one black outline round it:
wings up, then wings down. The right view is the left mirrored. Three colours and black: its grey, the salmon of its
wings, face and feet, the red of its wing shade and mouth. The previous mini is kept in redo/mini/previous.

Its chase: the swoop (chase_speed(), src/main.cpp) -- a glide, then wingbeats -- hovering (mini_hover(), src/main.cpp;
it flies, enemy_flies() in include/enemy.h).

    python art/enemies/minis/83_beast_of_barrisdale_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '848694', 'E': 'ec8476', 'R': 'b6433d'}
CHASE = 'swoop'
HOVER = 11               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 28
SRC = ROOT / 'pixellab-out/83-redo-mini/m/animations'
FLIGHTS = {'D': ('v1/flyd', (0, 3)), 'U': ('v2/flyu', (0, 3)), 'L': ('v3/flyl', (0, 2))}   # wings up, wings down


def tone(h, s, v):
    """Its darks black; its greys charcoal (its pale teeth salmon); then by saturation, not brightness (its
    gaping mouth is a bright red): the full reds red -- its mouth, its wing ribs -- the soft ones salmon."""
    if v < 0.22: return 'K'                  # its near-black lines (to 0.2) black, so its parts stay apart
    if s < 0.3: return 'E' if v > 0.85 else 'G'
    return 'R' if s > 0.6 else 'E'


SCALE = 1                # PixelLab drew it at the mini's size: pixel for pixel


def view(name, picks):
    """Each frame on the mini's palette pixel for pixel, its own black lines kept, its outer black taken off and
    the outline redrawn round it, scaled by SCALE, its bottom on the cell's last but one row, centred."""
    letters = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)): k for k, c in PAL.items()}
    out = []
    for i in picks:
        im = minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL)
        im = im.crop(im.getbbox())
        g = {(x, y): letters[im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
        edge = {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in ff.N4)}
        g = {p: c for p, c in g.items() if p not in edge}
        xs, ys = [x for x, y in g], [y for x, y in g]
        dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
        out.append(ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()}))
    return out


# Its side face, stamped by hand: on three colours PixelLab's folds to a pink blob. A black eye, a red mouth; ' ' leaves a pixel.
FACES = {('L', 0): (8, 20, ('KK', '  ', '  ', '  ', 'RRR')), ('L', 1): (8, 20, ('KK', '  ', '  ', ' RR'))}

FRAMES = {v: view(*FLIGHTS[v]) for v in FLIGHTS}
for (v, f), (x0, y0, patch) in FACES.items():
    g = {p: c for p, c in FRAMES[v][f].items()}
    for y, r in enumerate(patch):
        for x, c in enumerate(r):
            if c != ' ': g[x0 + x, y0 + y] = c
    FRAMES[v][f] = ff.outline(g)          # the outline closed again round the face where it fills a gap
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(83, 'beast_of_barrisdale', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(83, CHASE, FRAMES, PAL, hover=HOVER)
