"""28 Opimachus's map mini: the little snake-fighting cat-griffin up on its four legs and trotting, its red crest
up, its striped tail curled, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet only sits. Through PixelLab (art/enemies/pixellab/28_opimachus/mini, pixellab-out/28-mini): its
battle frame at 2x, edited to stand mid-stride, rotated to its eight views, a four-frame trot on the front, the back
and the left side. Shrunk (registered to one box a view, minis.snap, minis.shrink) they came out noisy at this
size, so drawn here after them: the body (crest, brown hawk's head, beak, the line of its ruff, tan cat's body,
the tail curled up beside it) the same on both frames, and only the legs moving -- a trot, diagonal pairs by turns.
13 px tall: its battle height (36 px) at the minis' one scale, 28/79 (the user, 2026-10-23: a mini's size is its
battle size, made small). Three of its battle colours and black: its tan (body, ruff, beak), its brown (head, tail),
its red (crest). Its gold ruff goes into the tan, parted from the head by a black line.

Its chase: bold, never stopping (the lore: small, but it goes straight for the serpent's neck) -- a dash straight
at you, then a trot (the Questing Beast's dash: chase_speed(), src/main.cpp).

    python art/enemies/minis/28_opimachus_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'T': 'b2966a', 'B': '633e1b', 'R': 'b6433d'}
CHASE = 'dash'

FRONT = (14, [                                   # rows 16-23, no outline: ff.outline gives it one
    '....R.R.R.....',
    '...BBBBBBB..B.',
    '...BKBBBKB..B.',
    '...BBBTBBB..T.',
    '...KKKTKKK..B.',
    '..TTTTTTTTT.B.',
    '..TTTTTTTTTTB.',
    '...TTTTTTTT...',
], (3, 5, 8, 10))
BACK = (14, [
    '....R.R.R.....',
    '...BBBBBBB..B.',
    '...BBBBBBB..B.',
    '...BBBBBBB..T.',
    '...KKKKKKK..B.',
    '..TTTTTTTTT.B.',
    '..TTTTTTTTTTB.',
    '...TTTTTTTT...',
], (3, 5, 8, 10))
SIDE = (12, [                                    # its head to the left, the beak out in front
    '....R.R.........',
    '...BBBBB.....B..',
    'TTTBKBBB.....B..',
    '...BBBBB.....T..',
    '...KKKKKTTTTTB..',
    '..TTTTTTTTTTTB..',
    '..TTTTTTTTTTT...',
    '...TTTTTTTTTT...',
], (3, 5, 10, 12))


def frame(view, step):
    """The body on rows 16-23 and its four legs under it; on each frame one diagonal pair plants (down to row 26),
    the other is lifted (to row 25)."""
    x0, rows, legs = view
    g = {(x0 + x, 16 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
    planted = (legs[0], legs[3]) if step == 0 else (legs[1], legs[2])
    for c in legs:
        for y in range(24, 27 if c in planted else 26):
            g[x0 + c, y] = 'T'
    return ff.outline(g)


FRAMES = {v: [frame(view, 0), frame(view, 1)] for v, view in (('D', FRONT), ('U', BACK), ('L', SIDE))}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(28, 'opimachus', FRAMES, PAL, cap=13)
    minis.chase_gif(28, CHASE, FRAMES, PAL)
