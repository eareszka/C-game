"""91 Kurrea's map mini: the redesigned crystal serpent (2026-11-03) at the player's scale, four views, two frames (tools/minis.py).

Through PixelLab (pixellab-out/91-redo2-mini, four generations): eight rotations of its approved frame
(art/enemies/pixellab/91_kurrea/redo2/frame0.png) sent at 36 px wide to fit the 40-wide cell, then its side (south), three-quarter front
(south-east) and three-quarter back (north-west) each given a slither; straight on it is only a sliver. Each frame on the mini's palette
pixel for pixel, its own black lines kept, one black outline. The left view is the right mirrored. Three colours and black (the bible's
limit, so the plates carry two of the four battle pastels): the stag's mid purple for the body, pink and mint for the plates.

Its chase: the slither (chase_speed(), chase_bend(), src/main.cpp).

    python art/enemies/minis/91_kurrea_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'B': '664b95', 'P': 'ec8476', 'M': 'a8f0bc'}
CHASE = 'slither'
HEIGHT = 28
SRC = ROOT / 'pixellab-out/91-redo2-mini/m/animations'
FLIGHTS = {'D': ('sld', (0, 2)), 'U': ('slu', (0, 2)), 'L': ('slr', (0, 2))}   # the ripple, two steps along


def tone(h, s, v):
    """Dark purple and black lines black or body; warm plates pink; cool plates mint; lilac underside and purples the body."""
    if v < 0.16: return 'K'
    if s > 0.25 and v > 0.7 and (h < 75 or h > 340): return 'P'
    if v > 0.7 and 75 <= h < 225: return 'M'
    return 'B'


def view(name, picks):
    letters = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)): k for k, c in PAL.items()}
    out = []
    for i in picks:
        im = minis.recolour(Image.open(next(SRC.rglob(f'{name}-{i:02d}.png'))).convert('RGBA'), tone, PAL)
        im = im.crop(im.getbbox())
        g = {(x, y): letters[im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
        edge = {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in ff.N4)}
        g = {p: c for p, c in g.items() if p not in edge}
        top = max(y for x, y in g) - 24                     # at most 25 rows inside the outline: the horn's tip gives
        g = {p: c for p, c in g.items() if p[1] >= top}
        left = min(x for x, y in g)                         # at most 33 wide inside its outline, clear of the 40-wide cell's sides: the tail's tip gives
        g = {p: c for p, c in g.items() if p[0] <= left + 32}
        xs, ys = [x for x, y in g], [y for x, y in g]
        dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
        out.append(ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()}))
    return out


FRAMES = {v: view(*FLIGHTS[v]) for v in FLIGHTS}
FRAMES['L'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]   # drawn head to the right: L its mirror
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(91, 'kurrea', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(91, CHASE, FRAMES, PAL)
