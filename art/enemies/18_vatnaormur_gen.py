"""Writes 18_vatnaormur.txt: the Vatnaormur, Iceland's lake serpent -- "a great
snake with humps or spikes on its back", grown huge from a slug in a lake.

A dark green serpent rearing a horse-like head out of the water, spiked coils
looping out of the lake behind it. The five views are hand-drawn with the pixel
plugin in 18_views.aseprite (exported to 18_views.png): row 0 the whole view,
rows 1-3 its layers -- what is behind the neck, the neck and head, what is in
front of it. Front and back are exact mirror images. This script adds the lake, the
tail and the idle animation -- five frames, one smooth cycle (it is big, so it
gets more frames than the usual three): the neck sways the head slowly out and
back (bending more toward the head), the tail tip curls up out of the water
behind it, and the serpent heaves up and sinks back a pixel, each a beat behind
the last, while the ripples drift."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, blank, put, tube, rising_frame, sea, write, source_path

VW, VH = 96, 56           # one drawn view
OX = 9                    # where the view sits in the frame: room on the left for the tail
W, H = VW + 2 * OX, 58    # the frame: room for the tail, the sway and the heave
WATER = 47                # the lake surface row in the frame
VIEW_WATER = 46           # ... and in the drawn view
HEAD = 20                 # view rows above this move with the head as one piece
PAL = {'K': '000000', 'G': '3c6448', 'g': '24402c', 'B': 'a8c890', 'S': 'd7c890', 'Y': 'f8d878',
       'W': 'fcfcfc', 'R': 'b6433d', 'A': '3c78d8', 'a': '84a7e9'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
FRAMES = 5               # one idle cycle; each motion below is a sine wave over it, a beat apart
def wave(n, amp, lag=0.0): return round(amp * math.sin(2 * math.pi * n / FRAMES - lag))
def BOB(n):  return 1 - wave(n, 1, 0.8)            # top row of the view in the frame: heaves up, sinks
def SWAY(n): return wave(n, 3)                     # how far the head leans
def CURL(n): return wave(n, 3, 1.6)                # the tail tip, side views
def PEEK(n): return wave(n, 11, 1.6)               # the tail tip from the front / back: out either side of the neck

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '18_views.png'), PAL)
LAYERS = {k: [grab(i * VW, (n + 1) * VH, VW, VH) for n in range(3)] for i, k in enumerate(ORDER)}

def scales(d, below):
    return 'B' if below and d >= 2 else 'G'

def tail(g, view, n):
    """The tail tip rising out of the lake beyond the coils (behind everything):
    curling in the side views, peeking out from behind the neck head-on."""
    if view in ('D', 'U'):
        cx, c = OX + 48, PEEK(n)
        pts, radii = [(cx, WATER + 3), (cx, 34), (cx + c // 2, 25), (cx + c, 19), (cx + c + c // 3, 16)], (4, 3, 2, 1)
    else:
        bx, c = 7, CURL(n)
        pts, radii = [(bx, WATER + 3), (bx - 1, 36), (bx + c // 2, 28), (bx + 4 + c, 24), (bx + 7 + c, 27)], (4, 3, 2, 1)
    t = blank(W, H)
    put(t, tube(pts, radii, scales))
    for y in range(H):
        for x in range(W):
            if g[y][x] == '.' and t[y][x] != '.': g[y][x] = t[y][x]

def lean(y, n):
    """How far the neck row y (in the view) shifts: the whole head by SWAY,
    fading to nothing at the water."""
    f = min(1, max(0, (VIEW_WATER - y) / (VIEW_WATER - HEAD)))
    return round(SWAY(n) * f)

def frame(view, n):
    g = rising_frame(LAYERS[view], (W, H), OX, BOB(n), lambda y: lean(y, n))
    tail(g, view, n)
    sea(g, n, WATER, OX + 48.5, 55, FRAMES)
    return g

def main():
    V = {}
    for n in range(FRAMES):
        V.update({view + (f'@{n}' if n else ''): frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
