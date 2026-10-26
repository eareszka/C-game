"""75 Makalala's map mini: East Africa's "the noisy one", a giant ground bird that screams and clubs its prey to
death with the great bony knob on its head -- sprinting at you on its long legs, its neck out, at the player's
scale, four views, two frames (tools/minis.py).

Its battle sheet stands facing front. Through PixelLab (art/enemies/pixellab/75_makalala/mini, pixellab-out/
75-mini, four generations): eight rotations of its battle front, then its front, back and side each given a
sprint, an ostrich's run. Shrunk to 22 px they ran its beak and knob into one blob and lost its legs, so its grids
are drawn by hand from them (G): the round bony knob on its head, its eyes, its hooked beak, its long neck, its
body with its wings folded at its sides, its long thin legs apart enough that the ground shows between them; one
black outline round it all, and between its wings and its body. Two frames: one foot lifted, then the other; from
the side its legs striding wide, then passing. The right view is the left mirrored.
23 px tall: a pixel over its battle height (63 px) at the minis' one scale, 28/79, for its long legs. Three of its
battle colours and black: its grey, its light grey (its knob, whose pale bone goes to it, and its legs, as in its battle), its beak yellow. Its
dark grey goes: its wings are set off from its body by a black line instead.

Its chase: the dash (chase_speed(), src/main.cpp) -- a sprint straight at you, then a breath, its legs striding.

    python art/enemies/minis/75_makalala_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '595965', 'L': '848694', 'Y': 'c9a433'}
CHASE = 'dash'
HEIGHT = 23

# By hand, from its PixelLab sprints (pixellab-out/75-mini/animations: v1 front, v2 back, v3 side): M its grey, L its
# light grey, Y its beak, K its eyes; '.' inside a row is the black line between its wings and its body. 0 and 1:
# one foot lifted, then the other.
G = {}
FRONT = [".....LLL.....",
         "....LLLLL....",
         ".....LLL.....",
         ".....MMM.....",
         "....MKMKM....",
         "....MYYYM....",
         ".....YYY.....",
         "......Y......",
         ".....MMM.....",
         ".....MMM.....",
         "....MMMMM....",
         "..M.MMMMM.M..",
         "..MM.MMM.MM..",
         "..MM.MMM.MM..",
         "...M.MMM.M...",
         "....MMMMM...."]
BACK = [".....LLL.....",
        "....LLLLL....",
        ".....LLL.....",
        ".....MMM.....",
        "....MMMMM....",
        "....MMMMM....",
        ".....MMM.....",
        ".....MMM.....",
        ".....MMM.....",
        ".....MMM.....",
        "....MMMMM....",
        "..M.MMMMM.M..",
        "..MM.MMM.MM..",
        "..MM.MMM.MM..",
        "...M.MMM.M...",
        "....MMMMM...."]
LEGS_A = ["....L...L....",
          "....L...L....",
          "....L...L....",
          "...L....L....",
          "...L....LL..."]
LEGS_B = ["....L...L....",
          "....L...L....",
          "....L...L....",
          "....L....L...",
          "...LL....L..."]
G['D0'] = FRONT + LEGS_A; G['D1'] = FRONT + LEGS_B
G['U0'] = BACK + LEGS_A;  G['U1'] = BACK + LEGS_B
SIDE = ["....LLL.......",
        "...LLLLL......",
        "....LLL.......",
        "...MMMM.......",
        "YYYMKMM.......",
        "YYYYMMM.......",
        ".Y...MM.......",
        ".....MM.......",
        ".....MM.......",
        ".....MMM......",
        "....MMMMMM....",
        "....MM.MMMM...",
        "....MMM.MMMM..",
        ".....MMM.MMMM.",
        "......MMMMM...",
        ".......MM....."]
G['L0'] = SIDE + [".......L.L....",
                  "......L...L...",
                  "......L...L...",
                  ".....L.....L..",
                  "...LL......L.."]
G['L1'] = SIDE + [".......LL.....",
                  ".......L.L....",
                  ".......L..LL..",
                  ".......L......",
                  "......LL......"]
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
    minis.make(75, 'makalala', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(75, CHASE, FRAMES, PAL)
