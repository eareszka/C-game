"""92 Siehnam's map mini: the redrawn skull-faced deer (2026-11-03) at the player's scale, four views, two frames (tools/minis.py).

Through PixelLab (pixellab-out/92-redo-mini, four generations): eight rotations of its approved frame
(art/enemies/pixellab/92_siehnam/redo/frame0.png) sent at 26 px tall, then front (south), back (north) and side (east) each given a stalking
step. Each frame on the mini's palette pixel for pixel, its own black lines kept, one black outline. The left view is the right mirrored.
Three colours and black: bone for the antlers and skull, its tan coat, the dark maroon of its ruff and the blood.

Its chase: the pounce (chase_speed(), chase_frame(), src/main.cpp) -- standing in the wait, stepped out in the lunge, as it comes into the
villages after midnight.

    python art/enemies/minis/92_siehnam_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'W': 'bcbeca', 'C': '8d6b4f', 'R': '421618'}
CHASE = 'pounce'
HEIGHT = 28
SRC = ROOT / 'pixellab-out/92-redo-mini/m/animations'
FLIGHTS = {'D': ('std', (0, 2)), 'U': ('stu', (0, 2)), 'L': ('str', (0, 2))}   # waiting, stepped out


def tone(h, s, v):
    """Blacks black; pale greys and white bone; saturated dark reds the ruff and blood; the rest its coat."""
    if v < 0.14: return 'K'
    if s < 0.18 and v > 0.45: return 'W'
    if (h < 15 or h > 330) and v < 0.62 and s > 0.35: return 'R'
    return 'C'


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
    minis.make(92, 'siehnam', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(92, CHASE, FRAMES, PAL)
