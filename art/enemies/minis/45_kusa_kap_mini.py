"""45 Kusa Kap's map mini: the redrawn sea eagle (2026-11-03) at the player's scale, four views, two frames (tools/minis.py).

IN FLIGHT with the dugong in its talons. Through PixelLab (pixellab-out/45-redo-mini, four generations): eight rotations of
its approved frame (art/enemies/pixellab/45_kusa_kap/redo/frame0.png) sent at 36 px wide so it fits the 40-wide cell, then
front (south), back (north) and side (west) each given a wingbeat. Each frame on the mini's palette pixel for pixel, its own
black lines kept, one black outline round it: wings up, then wings down. The right view is the left mirrored. Three colours
and black: its rust, the dugong's grey, the yellow of its beak, breast and talons; its dark feather ends go black. Its
eyes are stamped by hand.

Its chase: the swoop (chase_speed(), src/main.cpp), hovering (mini_hover(), src/main.cpp; enemy_flies() in include/enemy.h).

    python art/enemies/minis/45_kusa_kap_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'R': '792727', 'G': '848694', 'Y': 'f0bc3c'}
CHASE = 'swoop'
HOVER = 11               # mini_hover() in src/main.cpp: its shadow's half width
HEIGHT = 26
SRC = ROOT / 'pixellab-out/45-redo-mini/m/animations'
FLIGHTS = {'D': ('flyd', (0, 3)), 'U': ('flyu', (0, 1)), 'L': ('flyl', (0, 3))}   # wings up, wings down


def tone(h, s, v):
    """Blue-greys (even dark) the dugong; golds and creams yellow; true blacks black; everything else its rust."""
    if 180 < h < 290 and v > 0.12: return 'G'
    if 18 < h < 72 and v > 0.4: return 'Y'
    if s < 0.2 and v > 0.3: return 'G'
    if v < 0.2: return 'K'
    return 'R'


def view(name, picks):
    letters = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)): k for k, c in PAL.items()}
    out = []
    for i in picks:
        im = minis.recolour(Image.open(next(SRC.rglob(f'{name}-{i:02d}.png'))).convert('RGBA'), tone, PAL)
        im = im.crop(im.getbbox())
        g = {(x, y): letters[im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
        edge = {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in ff.N4)}
        g = {p: c for p, c in g.items() if p not in edge}
        xs, ys = [x for x, y in g], [y for x, y in g]
        dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
        out.append(ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()}))
    return out


FRAMES = {v: view(*FLIGHTS[v]) for v in FLIGHTS}
# Its eyes, by hand: PixelLab's fold away at this size. A black mark each, on the frame as placed.
EYES = {('D', 0): ((19, 11), (22, 11)), ('D', 1): ((19, 12), (22, 12)), ('L', 0): ((16, 11),), ('L', 1): ((16, 11),)}
for (v, f), marks in EYES.items():
    for p in marks: FRAMES[v][f][p] = 'K'
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(45, 'kusa_kap', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(45, CHASE, FRAMES, PAL, hover=HOVER)
