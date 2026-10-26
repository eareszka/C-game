"""70 Trollgadda's map mini: Sweden's troll pike, so long in Lake Bolmen it "can barely move", a willow shrub
growing from its head and neck, its scales as big as roof tiles -- swimming slowly at you through the air, its
tail sweeping, its willow swaying, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has one view, its side. Through PixelLab (art/enemies/pixellab/70_trollgadda/mini, pixellab-out/
70-mini, one generation): eight rotations of its battle side -- its front head-on under its tree, its back its tail.
Drawn by hand from them (G): the pike long and deep, its snout tapering to open jaws, its eye, its brown fins and
forked tail (its battle fins are the trunk's brown); its willow's trunk rising straight up out of the gape between
its jaws (the user: the trunk "visually come from the mouth") to the round crown over its head; one black outline
round it all. Two frames: its tail swept one way, then the other, its crown swaying a pixel with it.
The right view is the left mirrored.
22 px tall and 45 long, bigger than its battle height (49 px) at the minis' one scale, 28/79, would make it (the
user: "needs to be bigger"): a strip of its own, assets/enemies/minis_70.png, in 48 x 32 cells. Three of its battle colours and black: its
green (the pike), its dark green (the willow's crown, the pike's belly; a little of the green lights the crown
high on its left), its brown (the trunk, its fins and tail). Its bright leaf greens and pale belly go.

Its chase: the drift (chase_speed() and chase_bend(), src/main.cpp) -- slow, 0.7 of the chase pace, weaving a
little as it swims.

    python art/enemies/minis/70_trollgadda_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '4fa667', 'D': '2c6c44', 'B': '815423'}
CHASE = 'drift'
HEIGHT = 22
CW, CH = 48, 32                                  # its own strip's cells

# By hand, from its PixelLab rotations (pixellab-out/70-mini/rotations/v1: west its front, east its back, south its
# side): its crown, shifted a pixel as it sways, over its pike. M its green, D its dark green, B its brown, K its
# eyes and gape; the outline is drawn round them. 0 and 1: its tail one way, then the other.
CROWN = ["....DDDD..DDDD......",
         "..DDMMDDDDDDDDDDD...",
         ".DMMMDDDDDDDDDDDDD..",
         "DMMDDDDDDDDDDDDDDDD.",
         "DMDDDDDDDDDDDDDDDDDD",
         "DDDDDDDDDDDDDDDDDDDD",
         ".DDDDDDDDDDDDDDDDDDD",
         "..DDDDDDDDDDDDDDDDD.",
         "....DDDDD..DDDDDD..."]
def crown(dx, w):
    return [('.' * dx + r).ljust(w, '.')[:w] for r in CROWN]
def pad(rows, dx, w):
    return [('.' * dx + r).ljust(w, '.')[:w] for r in rows]
G = {}
FRONT = [".........BB.........",
         ".........BB.........",
         ".........BB.........",
         "....MMMMMBBMMMMMD...",
         "...MMKMMMBBMMMKMD...",
         "..MMMMMMKBBKMMMMMD..",
         "..MMMMMMKKKKMMMMMD..",
         "{0}MMMMMMMMMMMMMMMD{1}",
         "{2}DMMMMMMMMMMMMMD{3}",
         "...DDDDDDDDDDDDD...."]
def front(f):
    return [r.format(*f) for r in FRONT]
G['D0'] = crown(0, 20) + front(('.B', 'B.', 'BB', '..'))
G['D1'] = crown(1, 21) + front(('.B', 'B.', '..', 'BB'))
BACK = [".........BB.........",
        ".........BB.........",
        ".......MMBBMD.......",
        "......MMMMMMDD......",
        "......MMMMMMDD......",
        ".......MMMMDD.......",
        "........MMDD........"]
G['U0'] = crown(0, 20) + BACK + ["......BBB.BBB.......", ".....BBB...BBB......"]
G['U1'] = crown(1, 21) + BACK + [".....BBB.BBB........", "....BBB...BBB......."]
SIDE0 = ["..BB......................BBB..........",
         "..BB.....................BBBB.......B...",
         ".BBB........MMMMMMMMMMMMMMMMMMM....BBB..",
         ".BB.....MMMMMMMMMMMMMMMMMMMMMMMMM.BBBB..",
         ".BB..MMMMMMMMMMMMMMMMMMMMMMMMMMMMMBBB...",
         ".BBMMMMMKMMMMMMMMMMMMMMMMMMMMMMMMMMBB...",
         "BBBKKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMBB...",
         "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMBBB..",
         ".MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDBBBB",
         "..DDDMMMMMMMMMMMMMMMMMMMMMMMMMMMMDD.BBBB",
         "....DDDDDDBBDDDDDDDDDBBBDDDDDDDD.....BB."]
SIDE1 = ["..BB.......................BB..........",
         "..BB......................BBB...........",
         ".BBB........MMMMMMMMMMMMMMMMMMM.........",
         ".BB.....MMMMMMMMMMMMMMMMMMMMMMMMM....B..",
         ".BB..MMMMMMMMMMMMMMMMMMMMMMMMMMMMMBBBB..",
         ".BBMMMMMKMMMMMMMMMMMMMMMMMMMMMMMMMMBBB..",
         "BBBKKMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMBB...",
         "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMBBB..",
         ".MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDBBB.",
         "..DDDMMMMMMMMMMMMMMMMMMMMMMMMMMMMDD..BB.",
         "....DDDDDDDBDDDDDDDDDDBBDDDDDDDD......B."]
W = 43
G['L0'] = crown(0, W) + pad(SIDE0, 3, W)
G['L1'] = crown(1, W) + pad(SIDE1, 3, W)
G = {k: '\n'.join(v) for k, v in G.items()}


def grid(s):
    """A drawn grid, centred in its cell, its bottom row on the ground, one black outline round it, its eyes and
    gape black inside."""
    rows = s.strip('\n').split('\n')
    h, w = len(rows), max(map(len, rows))
    g = {(x + (CW - w) // 2, y + CH - 1 - h): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    out = ff.outline({p: ('M' if c == 'K' else c) for p, c in g.items()})
    out.update({p: 'K' for p, c in g.items() if c == 'K'})
    return out


FRAMES = {v: [grid(G[v + '0']), grid(G[v + '1'])] for v in 'DUL'}
FRAMES['R'] = [{(CW - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(70, 'trollgadda', FRAMES, PAL, cap=HEIGHT, cell=(CW, CH))
    minis.chase_gif(70, CHASE, FRAMES, PAL, cell=(CW, CH))
