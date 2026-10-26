"""41 Sasnalkahi's map mini: the great bear, humped at the shoulder, lumbering at you on all fours, its head low, at
the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has a front, a side and a back. Through PixelLab (art/enemies/pixellab/41_sasnalkahi/mini,
pixellab-out/41-mini, one generation): its side frame given a heavy walk -- head low, the hump steady, the near
legs and the far legs swinging opposite. Its shape is that walk's and the battle front's and back's, shrunk
(minis.snap, minis.shrink) and drawn over by hand: ONE bear, one silhouette with one black outline round it (the
user: built of ellipses with a black edge each, it was "too many shapes instead of one coherent bear"). Inside, it
reads by colour, not by black lines: the far legs and the underside in shadow, the muzzle and claws pale; black only
for its eyes and nose. The body is the same on both frames; only the legs step.
21 px tall: its battle height (60 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
brown (fur), its dark brown (shadow: the far legs, its underside, under its chin), its pale cream (muzzle, claws).

Its chase: it lumbers at you without stopping, steady and heavy (the plod: chase_speed(), src/main.cpp).

    python art/enemies/minis/41_sasnalkahi_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': '815423', 'B': '583518', 'C': 'cebe82'}
CHASE = 'plod'

# The bodies, fill only (the outline is drawn round the whole bear at the end), rows 8-20; the legs go under them.
SIDE = (7, [                                     # its head to the left, low; its hump over the shoulders
    '.........AAAAA.............',
    '...AA...AAAAAAAA...........',
    '...AAAAAAAAAAAAAAAAA.......',
    '..AAAAAAAAAAAAAAAAAAAAA....',
    '..AAAAAAAAAAAAAAAAAAAAAA...',
    '.AAKAAAAAAAAAAAAAAAAAAAAA..',
    '.AAAAAAAAAAAAAAAAAAAAAAAA..',
    'CCAAAAAAAAAAAAAAAAAAAAAAAA.',
    'KCCAAAAAAAAAAAAAAAAAAAAAAA.',
    'CCCAABBBAAAAAAAAAAAAAAAABB.',
    '.AABBBBBBAAAAABBBBAAAAAABB.',
    '.....BBBBAAAAABBBBBAAAAABB.',
    '......BBBAAAABBBBBBAAAABB..',
])
FRONT = (12, [                                   # its broad head low before its shoulders
    '......AAAAA......',
    '....AAAAAAAAA....',
    '...AAAAAAAAAAA...',
    '..AAAAAAAAAAAAA..',
    '.AAAABAAAAABAAAA.',
    'BAAAAAAAAAAAAAAAB',
    'BAAAAAKAAAKAAAAAB',
    'BAAAAAACKCAAAAAAB',
    'BAAAAAACCCAAAAAAB',
    'BAAAAAABBBAAAAAAB',
    'BAAABBBBBBBBBAAAB',
    'BAAABBBBBBBBBAAAB',
    'BBAABBBBBBBBBAABB',
])
BACK = (13, [                                    # its rump, parted down the middle; its ears over its hump
    '.....A...A.....',
    '....AAAAAAA....',
    '...AAAAAAAAA...',
    '..AAAAAAAAAAA..',
    '.AAAAAAAAAAAAA.',
    '.AAAAAAAAAAAAA.',
    'BAAAAAAAAAAAAAB',
    'BAAAAAAAAAAAAAB',
    'BAAAAAAAAAAAAAB',
    'BAAAAAABAAAAAAB',
    'BAAAAAABAAAAAAB',
    'BBAAAABBBAAAABB',
    'BBBBBBBBBBBBBBB',
])


def leg(g, x, top, swing, c, lift=0, toes=0):
    """A leg 3 px wide from (x, top) down to its paw, slanting swing pixels, lifted lift off the ground, its claws
    pale on its toe side (-1 left, +1 right, 0 all along). Fills only clear pixels."""
    bottom = 26 - lift
    for y in range(top, bottom + 1):
        cx = x + round(swing * (y - top) / max(1, bottom - top))
        for dx in (-1, 0, 1):
            g.setdefault((cx + dx, y), 'C' if y == bottom and (toes == 0 or dx == toes) else c)


def frame(view, legs):
    """The body, then its legs under it -- the near ones (A) over the far ones and the shadow (B) -- and one
    outline round the whole."""
    x0, rows = view
    g = {(x0 + x, 8 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    near = {}
    for x, top, swing, c, *rest in legs:
        leg(near if c == 'A' else g, x, top, swing, c, *rest)
    g.update({p: c for p, c in near.items() if p not in g or g[p] == 'B'})
    return ff.outline(g)


def side(step):
    """step 0: the near foreleg and the far hind leg reach forward, the others swing back; 1 the reverse."""
    s = 1 if step == 0 else -1
    return frame(SIDE, [(10, 20, -2 * s, 'A', 0, -1), (27, 20, 2 * s, 'A', 0, -1),
                        (13, 20, 2 * s, 'B', 0, -1), (24, 20, -2 * s, 'B', 0, -1)])


def front(step):
    """Its forelegs lifting by turns, the hind legs in shadow between them."""
    a, b = (0, 2) if step == 0 else (2, 0)
    return frame(FRONT, [(14, 20, -1, 'A', a), (26, 20, 1, 'A', b), (18, 21, 0, 'B', b), (22, 21, 0, 'B', a)])


def back(step):
    """Its hind legs lifting by turns, the forelegs in shadow between them."""
    a, b = (0, 2) if step == 0 else (2, 0)
    return frame(BACK, [(15, 20, -1, 'A', a), (25, 20, 1, 'A', b), (18, 21, 0, 'B', b), (22, 21, 0, 'B', a)])


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(41, 'sasnalkahi', FRAMES, PAL, cap=21)
    minis.chase_gif(41, CHASE, FRAMES, PAL)
