"""77 Hoga's map mini: the lake monster of Lake Metztitlan in Mexico, half ox and half fish, that churns the lake
into waves and floods as it goes -- a bull's head with long pale horns on a blue fish's body, swimming at you
through the air, horns first, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet floats side on, its bull's head over a fish's body. Drawn here by hand after it (G): from the front
its bull's face -- brown, its eyes, its pale muzzle and nostrils, its horns curving out and up -- its blue fins
spread either side behind; from the back its horns over its round blue body, its fins, its tail; from the side its
head with a horn up, its muzzle forward, a black gill line where the bull ends, then a fish (the user: "look more
like a fish"): a torpedo of a body, its pale belly stripe along under it, a row of sharp spiked fins along its back,
a fin under its chest, narrowing to a thin stem before a great forked tail. One black outline round it all. Two frames: its fins beating down then up, its tail swept one
way then the other. The right view is the left mirrored.
16 px tall: larger than its battle height (36 px) at the minis' one scale, 28/79, would make it (13). Three of its
battle colours and black: its brown (its head), its tan (its muzzle and its horns, whose pale bone goes to it), its
blue (its fish's body and fins; its other blues go to it); its pale belly stripe in the tan.

Its chase: the dash (chase_speed(), src/main.cpp) -- a bull's charge straight at you, then a breath.

    python art/enemies/minis/77_hoga_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '8d6b4f', 'L': 'd7a175', 'B': '375a94'}
CHASE = 'dash'
HEIGHT = 16

# By hand, after its battle side (assets/enemies/redraws/77_hoga.png): M its brown, L its tan and horns, B its blue,
# K its eyes, nostrils and gill line; the outline is drawn round them. 0 and 1: its fins and tail one way, then the other.
G = {}
HORNS = ["L...................L",
         "LL.................LL",
         ".LL...............LL.",
         "..LLL.MMMMMMMMM.LLL..",
         "....LMMMMMMMMMMML...."]
FACE0 = ["B...MMKMMMMMMKMMM...B",
         "BB..MMMMMMMMMMMMM..BB",
         "BBB.MMMLLLLLLLMMM.BBB",
         ".BBBMMLLLLLLLLLMMBBB.",
         "..BBMLLKLLLLLKLLMBB..",
         "...BBLLLLLLLLLLLBB...",
         "....BBLLLLLLLLLBB....",
         ".....BBBBBBBBBBB.....",
         ".......B.....B......."]
FACE1 = ["....MMKMMMMMMKMMM....",
         "B...MMMMMMMMMMMMM...B",
         "BB..MMMLLLLLLLMMM..BB",
         "BBBBMMLLLLLLLLLMMBBBB",
         ".BBBMLLKLLLLLKLLMBBB.",
         "..BBBLLLLLLLLLLLBBB..",
         "....BBLLLLLLLLLBB....",
         ".....BBBBBBBBBBB.....",
         "......B.......B......"]
BACK0 = ["B...MMMMMMMMMMMMM...B",
         "BB..BBBBBBBBBBBBB..BB",
         "BBB.BBBBBBBBBBBBB.BBB",
         ".BBBBBBBBBBBBBBBBBBB.",
         "..BBBBBBBBBBBBBBBBB..",
         "...BBBBBBBBBBBBBBB...",
         "....BBBBBBBBBBBBB....",
         "......BBBBBBBBB......",
         ".......BBB.BBB......."]
BACK1 = ["....MMMMMMMMMMMMM....",
         "B...BBBBBBBBBBBBB...B",
         "BB..BBBBBBBBBBBBB..BB",
         "BBBBBBBBBBBBBBBBBBBBB",
         ".BBBBBBBBBBBBBBBBBBB.",
         "...BBBBBBBBBBBBBBB...",
         "....BBBBBBBBBBBBB....",
         "......BBBBBBBBB......",
         "......BBB...BBB......"]
G['D0'] = HORNS + FACE0; G['D1'] = HORNS + FACE1
G['U0'] = HORNS + BACK0; G['U1'] = HORNS + BACK1
G['L0'] = ["L.......L.....................",
           "LL......LL....................",
           ".LL....LL.......B..B..........",
           "..LMMMML.......BB.BB.B......BB",
           "..MMMMMMM....BBBBBBBBBB....BBB",
           ".MMKMMMMMKBBBBBBBBBBBBBB..BBB.",
           ".MMMMMMMMKBBBBBBBBBBBBBBBBBB..",
           "LLLMMMMMMKBBBBBBBBBBBBBBBBB...",
           "LLLLMMMMMKBBBBBBBBBBBBBBBBBB..",
           "LKLLLMMMMKBBBBBBBBBBBBBB..BBB.",
           "LLLLLMMMKLLLLLLLLLLLLBB....BBB",
           ".LLLLMM..BBLLLLLLLLBB......BBB",
           ".........BBB..................",
           "..........B..................."]
G['L1'] = ["L.......L.....................",
           "LL......LL....................",
           ".LL....LL.......B..B..........",
           "..LMMMML.......BB.BB.B........",
           "..MMMMMMM....BBBBBBBBBB......B",
           ".MMKMMMMMKBBBBBBBBBBBBBB....BB",
           ".MMMMMMMMKBBBBBBBBBBBBBBBB.BBB",
           "LLLMMMMMMKBBBBBBBBBBBBBBBBBB..",
           "LLLLMMMMMKBBBBBBBBBBBBBBBBBBB.",
           "LKLLLMMMMKBBBBBBBBBBBBBB...BBB",
           "LLLLLMMMKLLLLLLLLLLLLBB.....BB",
           ".LLLLMM..BLLLLLLLLLBB........B",
           "..........BBB.................",
           "............B................."]
G = {k: '\n'.join(v) for k, v in G.items()}


def grid(s):
    """A drawn grid, centred, its bottom row on the ground, one black outline round it, its eyes black inside."""
    rows = s.strip(chr(10)).split(chr(10))
    h, w = len(rows), max(map(len, rows))
    g = {(x + (minis.W - w) // 2, y + minis.H - 1 - h): c
         for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    out = ff.outline({p: ('M' if c == 'K' else c) for p, c in g.items()})
    out.update({p: 'K' for p, c in g.items() if c == 'K'})
    return out


FRAMES = {v: [grid(G[v + '0']), grid(G[v + '1'])] for v in 'DUL'}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(77, 'hoga', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(77, CHASE, FRAMES, PAL)
