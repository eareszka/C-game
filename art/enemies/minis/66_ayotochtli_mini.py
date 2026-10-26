"""66 Ayotochtli's map mini: the Aztec "tortoise-rabbit", the armadillo, its segmented shell like a horse's
trappings, curled up so that "neither its head nor neck are clearly visible, with only the ears sticking out" --
rolling at you in its ball, fast, at the player's scale, four views, two frames (tools/minis.py).

Its battle roll (assets/enemies/redraws/66_ayotochtli_roll.png, PixelLab's) is a ball of banded tan shell: it only
ever moves curled up, "in its ball and just rolling around fast" (the user, of its battle). Drawn here after it as
one ball turned whole, as 33's rolling stone is: a round of shell, its bands' seams wrapping it in the shell's dark
tan and rolling on half a band each frame -- coming at you they roll down toward you, going away up and over, side
on they roll round ahead of it -- its two ears poking out of the top, rolled under on the next frame. Shaded by
form: its mid tan most of it, its dark tan massed low and to the right, its light tan a sparse lit patch high on the
left; no black inside it, one black outline round it.
12 px of ball: its battle height at the minis' one scale (28/79) is under the minis' floor of 12; its long
ears stand 4 px over that. Three of its battle colours and black: its shell's light, mid and dark tan, one ramp.

Its chase: the roll (chase_speed(), src/main.cpp) -- straight at you, kicked off fast, rolling out nearly to a stop,
then kicked off again.

    python art/enemies/minis/66_ayotochtli_mini.py
"""
from pathlib import Path
import math, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'L': 'd0c078', 'M': 'b29e5c', 'D': '8d6b4f'}
CHASE = 'roll'
R = 5.0                                          # the ball's radius: 10 rows of shell, 12 with its outline
BANDS = 7                                        # its shell's bands round the ball
BASE = minis.H - 2                               # its lowest row; the outline under it


def shell(axis, turn):
    """The ball, rolling about `axis` ('x': toward or away from you, 'y': side on) turned on by `turn` of a band:
    each pixel of its face as a point on the sphere, its band from the angle round the axis, a seam each band's
    edge, and the seams between its plates crosswise, set like bricks; then shaded by form."""
    g = {}
    for py in range(10):
        for px in range(10):
            lx, ly = px - 4.5, py - 4.5
            if lx * lx + ly * ly > (R + 0.2) ** 2: continue
            lz = math.sqrt(max(0.0, R * R - lx * lx - ly * ly))
            along, across = (ly, lx) if axis == 'x' else (lx, ly)
            u = math.atan2(along, lz) / (2 * math.pi) * BANDS + turn
            k, b = math.floor(u), u % 1
            plate = (across + 2.5 * k + 10.5) % 5 < 0.6          # the seams between a band's plates, set like bricks
            seam = (b < 0.3 or plate) and abs(across) < 4.0 and abs(along) < 4.4
            if lx + ly > 4.6 or seam: c = 'D'                # the dark: low and right, and the seams
            elif lx + ly < -3.6 and lx < -0.5 and ly < -0.5: c = 'L'   # the lit patch, high and left
            else: c = 'M'
            g[20 + px - 5, BASE - 9 + py] = c
    return g


def ears(g, side):
    """Its two long rabbit's ears poking out of its top: from the front and back side by side, leaning apart; side
    on one, the near one, leaning back toward its tail."""
    top = BASE - 9
    if side:
        for p in ((21, top - 1), (21, top - 2), (22, top - 3), (22, top - 4)): g[p] = 'M'
    else:
        for x, lean in ((18, -1), (21, 1)):
            for p in ((x, top - 1), (x, top - 2), (x + lean, top - 3), (x + lean, top - 4)): g[p] = 'M'
    return g


def view(axis, roll, side):
    """Two frames, half a band apart; its ears out on the first, rolled under on the second."""
    return [ff.outline(ears(shell(axis, 0.0), side)), ff.outline(shell(axis, roll))]


FRAMES = {'D': view('x', 1.0, False),            # rolling down toward you
          'U': view('x', -1.0, False),           # rolling up and over, away
          'L': view('y', 1.0, True)}             # rolling round ahead of it, to the left
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(66, 'ayotochtli', FRAMES, PAL, cap=16)
    minis.chase_gif(66, CHASE, FRAMES, PAL)
