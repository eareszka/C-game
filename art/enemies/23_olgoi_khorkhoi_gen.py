"""Writes 23_olgoi_khorkhoi.txt: the Olgoi-Khorkhoi, the Mongolian Death Worm --
a thick blood-red worm of the Gobi with no head or eyes, spiked projections at
its end, said to spit a deadly acid.

A giant enemy (8 frames): the ringed worm rears out of the desert sand, a coil
humping out of the dunes beside it, its eyeless end a round maw ringed with
pale spikes and an inner ring of teeth; seen from the side or behind, the end is
cut off at that spiked rim (no rounded pink tip). Four views -- front, 3/4 front,
side, 3/4 back; no back view, so facing up reuses the 3/4 back -- hand-drawn with
the pixel plugin in 23_views.aseprite (exported to 23_views.png): row 0 the whole
view, rows 1-3 its layers -- behind (coils), the worm, in front (the near coil).
The front is an exact mirror image. This script adds the sand and the idle
animation -- eight frames, one cycle: the worm sways (bending more toward its
end) and heaves up and sinks back in the sand, acid drips from its maw, and the
sand ripples drift with dust kicked up where it breaks the surface."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, rising_frame, sea, write, source_path

VW, VH = 128, 80          # one drawn view
OX = 6                    # where the view sits in the frame: room for the sway
W, H = VW + 2 * OX, VH + 2
SAND = 69                 # the sand surface row in the frame
VIEW_SAND = 68            # ... and in the drawn view
END = 24                  # view rows above this sway with the worm's end as one piece
PAL = {'K': '000000', 'R': 'b6433d', 'r': '7c2a26', 'P': 'ec8476', 'm': '3c1414', 'S': 'd7c890',
       'T': 'd8b878', 't': 'b89858', 'U': 'f0e0b0', 'A': 'a8e050'}
ORDER = ('D', 'DR', 'R', 'UR')     # no back view (the user's call): facing up reuses the 3/4 back
FRAMES = 8                # giant tier: one idle cycle of eight; each motion a sine wave over it, a beat apart
def wave(n, amp, lag=0.0): return round(amp * math.sin(2 * math.pi * n / FRAMES - lag))
def BOB(n):  return 1 - wave(n, 1, 0.8)            # top row of the view in the frame: heaves up, sinks
def SWAY(n): return wave(n, 4)                     # how far the worm's end leans
# The acid: the maw's centre (view coordinates) -- it runs from its lower lip -- and how long the strand is each frame.
LIP = {'D': (63, 22), 'DR': (84, 26), 'R': (100, 20)}
DRIP = (0, 0, 1, 2, 3, 4, 2, 0)

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '23_views.png'), PAL)
LAYERS = {k: [grab(i * VW, (n + 1) * VH, VW, VH) for n in range(3)] for i, k in enumerate(ORDER)}

def lean(y, n):
    f = min(1, max(0, (VIEW_SAND - y) / (VIEW_SAND - END)))
    return round(SWAY(n) * f)

def acid(g, view, n):
    """A strand of acid hanging from the lower lip, lengthening then let go
    of -- always touching the lip, so nothing floats loose."""
    if view not in LIP or not DRIP[n]: return
    lx, ly = LIP[view]
    x0, y0 = OX + lx + lean(ly, n), BOB(n) + ly
    while g[y0][x0] in 'mS': y0 += 1                 # from the maw's centre down to its lower lip
    for k in range(DRIP[n] + 2):                     # the strand runs over the lip and hangs below
        for dx in (0, 1): g[y0 + k][x0 + dx] = 'A'

def frame(view, n):
    g = rising_frame(LAYERS[view], (W, H), OX, BOB(n), lambda y: lean(y, n))
    acid(g, view, n)
    sea(g, n, SAND, OX + 63.5, 66, FRAMES, 'TtU')
    return g

def main():
    V = {}
    for n in range(FRAMES):
        V.update({view + (f'@{n}' if n else ''): frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
