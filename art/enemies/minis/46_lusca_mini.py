"""46 Lusca's map mini: the redrawn shark-octopus (2026-11-03) at the player's scale, four views, two frames (tools/minis.py).

Through PixelLab (pixellab-out/46-redo-mini, four generations): eight rotations of its approved frame
(art/enemies/pixellab/46_lusca/redo/frame0_skinny.png) sent at 26 px tall, then front (south), back (north) and side (west)
each given a swim, arms pulsing and jaws working. The back's later frames grew a mouth on its back and are left out. Each
frame on the mini's palette pixel for pixel, its own black lines kept, one black outline round it. The right view is the left
mirrored. Three colours and black: its grey hide, its cream jaw, the red of its arms and mouth.

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide: an octopus's jet.

    python art/enemies/minis/46_lusca_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'R': 'b6433d', 'G': '848694', 'C': 'e8e0c0'}
CHASE = 'surf'
HEIGHT = 28
SRC = ROOT / 'pixellab-out/46-redo-mini/m/animations'
FLIGHTS = {'D': ('swimd', (0, 2)), 'U': ('swimu', (0, 1)), 'L': ('swiml', (0, 2))}   # arms out, arms in


def tone(h, s, v):
    """Near-blacks black; pale warm cream; low-saturation grey; everything else red."""
    if v < 0.2: return 'K'
    if 18 < h < 72 and v > 0.55: return 'C'
    if s < 0.28: return 'G'
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
        top = max(y for x, y in g) - 24                     # at most 25 rows inside the outline: the fin's tip gives
        g = {p: c for p, c in g.items() if p[1] >= top}
        xs, ys = [x for x, y in g], [y for x, y in g]
        dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
        out.append(ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()}))
    return out


FRAMES = {v: view(*FLIGHTS[v]) for v in FLIGHTS}
# Its back: PixelLab's marks there read as a little face, so black wholly inside the hide goes.
for g in FRAMES['U']:
    for (x, y), c in list(g.items()):
        if c == 'K' and all(g.get((x + a, y + b)) in ('G', 'K') for a, b in ff.N4) and y < 20 and sum(g.get((x + a, y + b)) == 'G' for a, b in ff.N4) >= 2:
            g[x, y] = 'G'

# Its eyes, by hand: only one survives the fold head on. One black mark each, on the frame as placed.
EYES = {('D', 0): ((15, 12), (26, 12)), ('D', 1): ((15, 14), (26, 14))}
for (v, f), marks in EYES.items():
    for p in marks: FRAMES[v][f][p] = 'K'
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(46, 'lusca', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(46, CHASE, FRAMES, PAL)
