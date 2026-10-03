"""Writes 19_skeljaskrimsli.txt: the Skeljaskrimsli, Iceland's shell monster --
a quadruped "the size of a winter's old bull calf or a huge horse", humped,
"the neck is broad, the jaws and teeth impressive", a glow from the mouth
tiny evil red eyes under slanted brows, "short, strong legs" on "circular feet armed with large
claws", a long tail "armed with a lump at the end", and a coat of reflective
shells that rattle as it moves.

The five views are hand-drawn with the pixel plugin in 19_views.aseprite
(exported to 19_views.png): row 0 the whole view, row 1 its tail, row 2 the
body. Front and back are exact mirror images. This script adds the idle
animation -- five frames, one cycle (it is big, so it gets more than the usual
three): it breathes (the hump rises), the tail club sways, the mouth glow
pulses and a glint sweeps across the shells as they shift."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, blank, stamp, lift, write, source_path

VW, VH = 84, 40           # one drawn view (side views 8 px in, room for the tail)
W, H = VW + 2, VH + 2     # the frame: a spare column/row all round
PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda', 'E': '4a3a32', 'e': '7a6050',
       'S': 'd7c890', 'W': 'fcfcfc', 'R': 'd82800', 'O': 'a8f0d0', 'o': '58b890'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
BREATH_ROW = 21           # mid-body in every view, clear of outline runs: rows above it rise
TAIL_FRONT = {'U', 'UR'}  # the tail is drawn over the body from behind
# Where each view's tail leaves the body, and which way it runs: 'x' (sideways,
# sways up and down) or 'y' (hangs toward you, sways side to side).
TAIL_ROOT = {'DR': (31, 'x'), 'R': (34, 'x'), 'UR': (35, 'x'), 'U': (22, 'y')}
FRAMES = 5

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '19_views.png'), PAL)
LAYERS = {k: (grab(i * VW, VH, VW, VH), grab(i * VW, 2 * VH, VW, VH)) for i, k in enumerate(ORDER)}

def wave(n, amp, lag=0.0): return amp * math.sin(2 * math.pi * n / FRAMES - lag)

def sway(tail, view, n):
    """The tail bends further the further it is from the body."""
    if view not in TAIL_ROOT: return tail
    root, axis = TAIL_ROOT[view]
    out = [['.'] * VW for _ in range(VH)]
    for y, r in enumerate(tail):
        for x, c in enumerate(r):
            if c == '.': continue
            far = (root - x) if axis == 'x' else (y - root)
            s = round(wave(n, 2.5, 1.2) * max(0, far) / 20)
            xx, yy = (x, y + s) if axis == 'x' else (x + s, y)
            assert 0 <= xx < VW and 0 <= yy < VH, f'{view} frame {n}: the tail swings off the canvas'
            out[yy][xx] = c
    return [''.join(r) for r in out]

def frame(view, n):
    tail, body = LAYERS[view]
    tail = sway(tail, view, n)
    g = blank(VW, VH)
    for layer in ((body, tail) if view in TAIL_FRONT else (tail, body)): stamp(g, 0, 0, layer)
    rows = [''.join(r) for r in g]
    if wave(n, 1) > 0.3:                                 # breathing in: rows above the pivot rise 1
        rows = lift(rows, BREATH_ROW)
    glow = 'O' if wave(n, 1, 0.6) >= 0 else 'o'
    shifted = []
    for y, r in enumerate(rows):
        row = []
        for x, c in enumerate(r):
            if c == 'O': c = glow
            elif c == 'L' and (x + y - n * 6) % 30 >= 12: c = 'M'    # the glint band travels across the shells
            row.append(c)
        shifted.append(''.join(row))
    out = blank(W, H)
    stamp(out, 1, 1, shifted)
    return out

def main():
    V = {}
    for n in range(FRAMES):
        V.update({view + (f'@{n}' if n else ''): frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
