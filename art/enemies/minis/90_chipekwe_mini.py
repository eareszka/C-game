"""90 Chipekwe's map mini: the redrawn horned beast (2026-11-03) at the player's scale, four views, two frames (tools/minis.py).

Through PixelLab (pixellab-out/90-redo-mini, four generations): eight rotations of its approved frame
(art/enemies/pixellab/90_chipekwe/redo/frame0_final.png) sent at 36 px wide to fit the 40-wide cell, then front (labelled south-east),
back (north-west) and side (south) each given a heavy plod. Each frame on the mini's palette pixel for pixel, its own black lines
kept, one black outline round it. The right view is the left mirrored. Three colours and black: Igtuk's periwinkle, its navy, the
ivory of its horn.

Its chase: the plod (chase_speed(), src/main.cpp) -- slow and steady, as its weight asks.

    python art/enemies/minis/90_chipekwe_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'L': '84a7e9', 'N': '37387b', 'I': 'e8e0c0'}
CHASE = 'plod'
HEIGHT = 28
SRC = ROOT / 'pixellab-out/90-redo-mini/m/animations'
FLIGHTS = {'D': ('plodd', (0, 2)), 'U': ('plodu', (0, 2)), 'L': ('plodl', (0, 2))}   # step, other step


def tone(h, s, v):
    """Near-blacks black; warm pale the horn; bright blues periwinkle; the rest navy."""
    if v < 0.22: return 'K'
    if 15 < h < 80 and v > 0.45: return 'I'
    return 'L' if v > 0.56 else 'N'


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
# Its eyes, by hand: PixelLab's blur away at this size. A black mark each, on the frame as placed.
EYES = {('D', 0): ((14, 14), (15, 14), (21, 14), (22, 14)), ('D', 1): ((14, 12), (15, 12), (21, 12), (22, 12)),
        ('L', 0): ((9, 12), (10, 12)), ('L', 1): ((9, 15), (10, 15))}
for (v, f), marks in EYES.items():
    for p in marks: FRAMES[v][f][p] = 'K'
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(90, 'chipekwe', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(90, CHASE, FRAMES, PAL)
