"""Writes 13_beast_of_the_charred_forests.txt: the dragon "born from a fire
that burned for seven years" that "lived in fire" and "stalked over northern
Scotland ... breathing fire and incinerating trees".

A wingless, low-slung, crocodile-like drake: charred black scales cracked with
glowing lava, one spine ridge of ember-tipped spikes, no eyes -- the face is
one huge maw of interlocking fangs with the lava throat glowing between them
-- crowned with spikes, and a long ash-grey tail seen from every side. The
five rest views and the open-jaw heads are hand-drawn with the pixel plugin
in 13_views.aseprite (exported to 13_views.png); front and back are exact
mirror images. This script only adds
the idle animation: it breathes -- the body rising as the cracks flare, then
sinking as the jaws gape and it breathes fire (none from behind) -- with the
feet and the tail on the ground staying put."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import blank, put, stamp, ellipse, polygon, views_reader, write, source_path
from build_enemy import poses

W, H = 80, 34
PAL = {'K': '000000', 'D': '282828', 'M': '595965', 'O': 'fc9838', 'Y': 'fae488',
       'W': 'fcfcfc', 'r': 'b70000'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')                 # rest views, 80 px apart on row 0
BREATH_ROW = 23   # in the belly, above the legs: rows above it rise / sink with each breath
OPEN = {'front': (0, 35, 18, 17), 'side': (20, 35, 18, 16)}   # open-jaw heads (with their spike crowns) on row 1
# Where each view's shut head is, which open head replaces it, and the fire: (x, y, dir) of
# the mouth for a cone, or 'burst' head-on.
JAWS = {'D': ('front', 31, 6, (39.5, 17, 'burst')),
        'DR': ('front', 39, 3, (55, 14, 1)),
        'R': ('side', 50, 5, (66, 15, 1))}

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '13_views.png'), PAL)
VIEWS = {k: grab(i * W, 0, W, H) for i, k in enumerate(ORDER)}
HEADS = {k: grab(*box) for k, box in OPEN.items()}

def fire(g, mx, my, d):
    """Fire out of the open jaws: yellow core, orange, red rim. It overlaps the
    mouth, so it never floats loose. Head-on it is a burst toward the viewer."""
    if d == 'burst':
        put(g, ellipse(mx, my, 7, 4, lambda x, y, t: 'Y' if abs(x - mx) < 3 and 0.25 < t < 0.75 else 'O'))
        return
    pts = [(mx, my - 1), (mx + 6 * d, my - 4), (mx + 11 * d, my - 2), (mx + 12 * d, my),
           (mx + 11 * d, my + 2), (mx + 6 * d, my + 4), (mx, my + 1)]
    put(g, polygon(pts, lambda x, y: 'Y' if abs(y - my) <= 1 and abs(x - mx) < 9 else
                               'O' if abs(y - my) <= 2 else 'r'))

def frame(view, n):
    g = blank(W, H)
    for y, row in enumerate(VIEWS[view]): g[y][:] = row
    if n == 1:                                       # the lava cracks (and ember tips) flare
        for row in g:
            for x, c in enumerate(row):
                if c == 'O': row[x] = 'Y'
    if n == 2 and view in JAWS:                      # jaws gape and it breathes fire
        kind, hx, hy, (mx, my, d) = JAWS[view]
        stamp(g, hx, hy, HEADS[kind])
        fire(g, mx, my, d)
    # the breath, with build_enemy's transform: rest / inhale (rise 1) / exhale (sink 1).
    # poses() adds a blank top row; drop it to keep the frame H tall (row 0 is always empty).
    return poses([''.join(r) for r in g], BREATH_ROW)[n][1:]

def main():
    V = {}
    for suffix, n in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({view + suffix: frame(view, n) for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
