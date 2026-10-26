"""73 Lidérc's map mini: Hungary's will-o'-the-wisp, the shape-shifter -- a marsh flame, a shooting star, a
featherless hen hatched from an egg kept under a man's armpit -- that "spits fire and throws sparks when angry":
a burning black hen in the air, drifting like a marsh light and then streaking at you like a shooting star, at the
player's scale, four views, two frames (tools/minis.py).

Its battle sheet is already PixelLab's (art/enemies/pixellab/73_liderc): its redraw has all its views, front, back
and both sides, its flames flickering through five frames. Shrunk to 19 px they ran its legs into a block, lost
its face and thinned its pale flames to a column, so its grids are drawn by hand from them (G): its round black
body and head, its yellow beak, its wings two fans of fire with tongues licking up, its two thin legs dangling,
toes spread, apart enough that the ground shows between them. One black outline round it all. Two frames: its
flames flaring orange with yellow hearts, then burning pale yellow and higher (its battle frames 0 and 2). The
right view is the left mirrored.
19 px tall: its battle height (53 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
body's near-black, its flame orange (its red goes to it), its flame yellow (its pale cream goes to it; its beak).

A flier: it hovers over its shadow (mini_hover(), src/main.cpp), its flames always flickering.
Its chase: the streak (chase_speed(), src/main.cpp) -- drifting slow like a marsh light, then streaking straight
at you like its shooting star.

    python art/enemies/minis/73_liderc_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'B': '292931', 'O': 'fc9838', 'Y': 'f0bc3c'}
CHASE = 'streak'
HEIGHT = 19
HOVER = 6                                        # its shadow's half width (mini_hover() in src/main.cpp)

# By hand, from its battle views (assets/enemies/redraws/73_liderc.png): B its black, O its flame orange, Y its flame
# yellow and beak; the outline is drawn round them. 0 its flames flaring, 1 burning pale and high.
G = {}
BODY = ["....BBBBBBBB....",
        "....BBBBBBBB....",
        ".....BBBBBB.....",
        "......BBBB......",
        ".....B....B.....",
        ".....B....B.....",
        ".....B....B.....",
        "....BBB..BBB...."]
FLAME0 = ["..O.O......O.O..",
          ".OOOOO....OOOOO.",
          ".OOYOOO..OOOYOO.",
          "OOYYYO.BB.OYYYOO",
          "OOYYYOBBBBOYYYOO",
          ".OOYYBBYYBBYYOO.",
          "..OOYBBBBBBYOO..",
          "...OOBBBBBBOO..."]
FLAME1 = ["..Y.Y......Y.Y..",
          "..YYY.Y..Y.YYY..",
          ".OYYYYO..OYYYYO.",
          ".OYYYO.BB.OYYYO.",
          ".OYYYOBBBBOYYYO.",
          "..OYYBBYYBBYYO..",
          "...OYBBBBBBYO...",
          "....OBBBBBBO...."]
def back(rows):
    return [r[:6] + r[6:10].replace('Y', 'B') + r[10:] if i == 5 else r for i, r in enumerate(rows)]
G['D0'] = FLAME0 + BODY
G['D1'] = FLAME1 + BODY
G['U0'] = back(FLAME0) + BODY
G['U1'] = back(FLAME1) + BODY
LEGS = ["...BBBBBB.......",
        "....B...B.......",
        "....B...B.......",
        "....B...B.......",
        "...BB..BB......."]
G['L0'] = ["...........O.O..",
           "..........OOOO..",
           ".........OOYOO..",
           "........OOYYOOO.",
           ".BB.....OYYYYOO.",
           "BBBB...OOYYYYOO.",
           "YBBBB.OOYYYYOO..",
           ".BBBBBBOYYYOO...",
           "..BBBBBBOYOO....",
           "..BBBBBBBOO.....",
           "..BBBBBBBB......"] + LEGS
G['L1'] = ["..........Y.Y...",
           "..........YYY...",
           ".........OYYYO..",
           "........OYYYYO..",
           ".BB.....OYYYYO..",
           "BBBB...OYYYYYO..",
           "YBBBB.OYYYYYO...",
           ".BBBBBBOYYYO....",
           "..BBBBBBOYO.....",
           "..BBBBBBBO......",
           "..BBBBBBBB......"] + LEGS
G = {k: '\n'.join(v) for k, v in G.items()}


def grid(s):
    """A drawn grid, centred, its bottom row on the ground, one black outline round it."""
    rows = s.strip(chr(10)).split(chr(10))
    h, w = len(rows), max(map(len, rows))
    return ff.outline({(x + (minis.W - w) // 2, y + minis.H - 1 - h): c
                       for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {v: [grid(G[v + '0']), grid(G[v + '1'])] for v in 'DUL'}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(73, 'liderc', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(73, CHASE, FRAMES, PAL, hover=HOVER)
