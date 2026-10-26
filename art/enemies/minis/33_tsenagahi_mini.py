"""33 Tse'nagahi's map mini: the Traveling Rock, a faceted mass of banded sandstone carved with petroglyphs, rolling
after you to crush you, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet sits facing front and leans forward and back as it rolls. Through PixelLab
(art/enemies/pixellab/33_tsenagahi/mini, pixellab-out/33-mini): its battle frame rotated to its eight views -- its
back plain banded stone, its side a narrow faceted wedge with one spiral eye. Drawn here after them as one rock
turned whole: a pentagon of stone, tan above its band, red below, its carvings in ivory. It has no legs: it ROLLS.
Coming at you, its face turns down and over toward you (its carvings and bands roll down a step); going away, its
sun carving rolls up and over; side on, the whole stone tips over a facet, upright, then on its point.
12 px tall: its battle height (34 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
tan, its red (its dark red goes into it), its ivory (spiral eyes, zigzag mouth, the sun on its back).

Its chase: it never stops (the user's pick over its battle's roll-and-settle) -- a fast roll, then a slow grind,
then a fast roll (the Opimachus's dash: chase_speed(), src/main.cpp).

    python art/enemies/minis/33_tsenagahi_mini.py
"""
from pathlib import Path
import math, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': 'd7a175', 'C': 'b6433d', 'D': 'e8e0c0'}
CHASE = 'dash'
R = 6.0                                          # the pentagon's radius: 10 rows of stone, 12 with its outline


def inside(lx, ly):
    """In the stone: a pentagon, point up, about (0, 0), its points worn round (no lone pixel at a tip)."""
    if lx * lx + ly * ly > (0.9 * R) ** 2: return False
    for k in range(5):
        a = math.radians(90 + 36 + 72 * k)       # the outward normal of each face
        if lx * math.cos(a) - ly * math.sin(a) > R * math.cos(math.radians(36)): return False
    return True


def band(ly):
    """Tan above its band, red below; a thin red seam across the top."""
    return 'C' if ly > 0.6 or -3.1 < ly < -2.1 else 'A'


def rock(turn, paint):
    """The stone tipped by turn degrees (counter-clockwise), its lowest row on row 26, centred on column 20;
    paint(lx, ly) colours each pixel from where it lies on the stone."""
    t = math.radians(turn)
    g = {}
    for y in range(-8, 9):
        for x in range(-8, 9):
            lx = x * math.cos(t) - y * math.sin(t)
            ly = x * math.sin(t) + y * math.cos(t)
            if inside(lx, ly): g[x, y] = paint(lx, ly)
    dy = 26 - max(y for _, y in g)
    return ff.outline({(20 + x, y + dy): c for (x, y), c in g.items()})


def face(shift):
    """Its front: two spiral eyes and a zigzag mouth, the bands and carvings rolled down by shift pixels."""
    def paint(lx, ly):
        v = ly - shift
        if round(v) == -1 and round(abs(lx)) == 2: return 'D'                       # the eyes
        if round(v) in (2, 3) and abs(lx) < 3 and (round(lx) + round(v)) % 2 == 0: return 'D'   # the zigzag mouth
        return band(v if v > -5 else v + 10)
    return paint


def sun(shift):
    """Its back: the carved sun, a ring of rays round a dot, rolled up by shift pixels."""
    def paint(lx, ly):
        v = ly + shift
        x, y = round(lx), round(v - 1)
        if (x, y) in {(0, 0), (0, -2), (0, 2), (-2, 0), (2, 0), (-1, -1), (1, 1), (-1, 1), (1, -1)}: return 'D'
        return band(v if v < 5 else v - 10)
    return paint


def side(lx, ly):
    """Side on: one spiral eye and the mouth's end on its leading (left) face."""
    if (round(lx), round(ly)) in {(-3, -1), (-3, 2), (-2, 3)}: return 'D'
    return band(ly)


FRAMES = {'D': [rock(0, face(0)), rock(0, face(2))],
          'U': [rock(0, sun(0)), rock(0, sun(2))],
          'L': [rock(0, side), rock(36, side)]}
FRAMES['R'] = [{(39 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(33, 'tsenagahi', FRAMES, PAL, cap=12)
    minis.chase_gif(33, CHASE, FRAMES, PAL)
