"""Writes 16_kamaitachi.txt: the Kamaitachi -- "something like a weasel with
razor-sharp sickle claws" that travels hidden in whirlwinds.

A lean white ermine (snow country) with a black-tipped tail, its forelimbs two
steel sickles, riding a tornado. The five views are hand-drawn with the pixel
plugin in 16_views.aseprite (exported to 16_views.png); front and back are
exact mirror images. This script adds the idle animation: the whirlwind spins
under it (drawn here, behind the body, a step further round each frame) and it
rides up on the gust."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, float_frame, thick_line, write, source_path

VW, VH = 28, 28           # one drawn view
W, H = 30, 30             # the frame: a spare column/row all round, room for the bob
PAL = {'K': '000000', 'W': 'fcfcfc', 'L': 'c6ccda', 'S': '848694', 'M': '595965',
       'B': '84a7e9', 'b': 'dcf0ff', 'P': 'ec8476'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
BOB = (1, 0, 1)           # rides up on the gust
FUNNEL_X = {'D': 13.5, 'DR': 12, 'R': 13, 'UR': 12, 'U': 13.5}   # the tornado's centre under each view

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '16_views.png'), PAL)
VIEWS = {k: grab(i * VW, 0, VW, VH) for i, k in enumerate(ORDER)}

def whirlwind(g, cx, top, bottom, phase):
    """A tornado funnel: wind bands narrowing downward, each one connected 1-px
    line with a gap (the gust) -- so nothing floats loose. `phase` turns the
    gaps round. Drawn only into empty pixels, so it stays behind the body."""
    n = 5
    for i in range(n):
        y = top + i * (bottom - top) / (n - 1)
        rx = 9 - i * 1.7
        start = (phase * 3 + i * 4) % 18
        pts = [(round(cx + rx * math.cos(k / 18 * 2 * math.pi)), round(y + 1.3 * math.sin(k / 18 * 2 * math.pi)))
               for k in range(start, start + 14)]
        for a, b in zip(pts, pts[1:]):
            for (x, yy) in thick_line(*a, *b, 0, 'B'):
                if 0 <= x < W and 0 <= yy < H and g[yy][x] == '.': g[yy][x] = 'b' if i % 2 else 'B'

def frame(view, n):
    g = float_frame(VIEWS[view], n, None, (W, H), BOB)
    whirlwind(g, FUNNEL_X[view] + 1, 16, 27, n)      # +1: the view sits 1 px in from the frame's left
    return g

def main():
    V = {}
    for suffix, n in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({view + suffix: frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
