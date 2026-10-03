"""Writes 20_sermilik.txt: the Sermilik ("ice-clad") of Aasiaat, Greenland --
"an enormous and highly dangerous polar bear" whose "very long fur" is
"completely covered with ice", its four paws like lumps of ice.

A big enemy (5 frames, like the Vatnaormur): a huge white bear on all fours,
an ice crust over its back with a jagged blue edge, the long fur frozen into
icicles underneath, round ears, head carried low, paws like faceted lumps of
ice with dark claws. The five views are hand-drawn with the pixel plugin in
20_views.aseprite (exported to 20_views.png): row 0 the whole view, row 1 the
body, row 2 the head. Front and back are exact mirror images. This script adds
the idle animation -- five frames, one cycle: it breathes (the back rises),
the head dips and lifts, frosty breath puffs from its nose and a glint moves
over the ice."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, blank, stamp, ellipse, lift, write, source_path

VW, VH = 96, 56           # one drawn view
OX = 1                    # where the view sits in the frame
W, H = VW + 12, VH + 2    # the frame: a spare row/column, room on the right for the breath
PAL = {'K': '000000', 'W': 'fcfcfc', 'L': 'c6ccda', 'M': '595965', 'B': 'dcf0ff', 'I': '84a7e9', 'J': '3c78d8'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
HEAD_OVER = {'D', 'DR', 'R'}   # the head is drawn over the body; from behind, under it
BREATH_ROW = 28           # mid-body in every view, clear of outline runs: rows above it rise
FRAMES = 5                # one idle cycle; each motion is a sine wave over it, a beat apart
def wave(n, amp, lag=0.0): return round(amp * math.sin(2 * math.pi * n / FRAMES - lag))
def NOD(n): return wave(n, 1, 1.2)                 # the head dips and lifts
# The frosty breath: where it leaves the nose (view coordinates) and which way it drifts. None from behind.
NOSE = {'D': ((47.5, 40), (0, 1)), 'DR': ((85.5, 39), (1, 0.5)), 'R': ((93.5, 33), (1, 0))}
BREATH = (0, 0, 2.0, 3.0, 3.6)                     # the puff's radius each frame: none, then out from the nose

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '20_views.png'), PAL)
LAYERS = {k: (grab(i * VW, VH, VW, VH), grab(i * VW, 2 * VH, VW, VH)) for i, k in enumerate(ORDER)}

def breath(g, view, n, top):
    """A pale cloud of frosty breath, touching the nose and growing as it
    drifts out; drawn over the bear from the front (the breath comes toward you)."""
    if view not in NOSE or not BREATH[n]: return
    (nx, ny), (dx, dy) = NOSE[view]
    r = BREATH[n]
    cx, cy = OX + nx + dx * (r - 0.5), top + ny + dy * (r - 0.5)
    for (x, y), t in ellipse(cx, cy, r + 0.5, r * 0.8 + 0.5, lambda x, y, t: t).items():
        assert 0 <= x < W and 0 <= y < len(g), f'{view} frame {n}: breath off the canvas'
        g[y][x] = 'L' if t > 0.7 else 'B'

def frame(view, n):
    body, head = LAYERS[view]
    g = blank(W, VH + 1)                              # a blank top row, for breathing in
    layers = ((body, 1), (head, 1 + NOD(n))) if view in HEAD_OVER else ((head, 1 + NOD(n)), (body, 1))
    for rows, top in layers: stamp(g, OX, top, rows)
    breath(g, view, n, 1 + NOD(n))
    rows = [''.join(r) for r in g]
    if wave(n, 1) > 0:                                # breathing in: the back rises
        rows = lift(rows, BREATH_ROW + 1)
    out = blank(W, H)
    for y, r in enumerate(rows):                      # a glint travels over the ice crust
        stamp(out, 0, y, [''.join('W' if c == 'B' and (x + y - n * 8) % 40 < 2 else c for x, c in enumerate(r))])
    return out

def main():
    V = {}
    for n in range(FRAMES):
        V.update({view + (f'@{n}' if n else ''): frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
