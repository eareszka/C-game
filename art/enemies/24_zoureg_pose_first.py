"""Enemy 24 Zoureg, first-frame drafts: its old design redrawn to the bible, both forms.

A red-hot knife of a snake: a flat coil, a neck, a spade blade for a head. Phase 2 shows it with
three heads. Typed as its colour pixels, the black edge put round after; drawn through the Aseprite
pixel plugin. Writes only drafts and a review; the game's assets are not touched.

Phase 1 shows it from four sides (the user): front, side and back are drawn, the left is the side mirrored.

    python art/enemies/24_zoureg_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/24_zoureg_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

PAL = {'K': '000000', 'W': 'fcfcfc', 'Y': 'fae488', 'O': 'fc9838', 'R': 'b70000', 'r': '7c0a1b'}   # white-hot down to dark red
ONE = (44, 29)      # the old sheets' frames
THREE = (60, 35)
# What the fight reads off the art (class Zoureg): the coil's underside row in the one-headed frame,
# and the top of each head in the three-headed one, where its lasers leave.
BELLY_ROW = 26
TIPS = {'left': (17, 7), 'middle': (30, 3), 'right': (43, 7)}

# The head, its point at (0, 0): (row, first column, letters). A kite of a blade, white-hot down its ridge;
# the two black pixels are its eyes, the black row under it parts the blade from the neck.
HEAD = [(0, 0, 'WW'),
        (1, 0, 'WW'),
        (2, -1, 'YWWY'),
        (3, -1, 'YWWY'),
        (4, -2, 'YYWWYY'),
        (5, -3, 'OYYWWYYO'),
        (6, -4, 'OOOYWWYOOO'),
        (7, -4, 'ROKOYYOKOR'),
        (8, -3, 'RROOOORR'),
        (9, -2, 'rROORr'),
        (10, -1, 'KKKK')]
# One-headed: the neck under the head (its point is at column 21, row 2), thickening a pixel at a time to the coil.
NECK = [(13, 20, 'OORr'), (14, 20, 'OORr'), (15, 20, 'OORr'),
        (16, 19, 'ROORr'), (17, 19, 'ROORr'), (18, 19, 'ROORr'),
        (19, 19, 'ROORRr'), (20, 19, 'ROORRr')]
# The coil: the far turn, the black seam where the near turn lies over it, the near turn, the tail's end.
COIL = [(21, 14, 'rrrRRROORRRrrrrr'),
        (22, 13, 'rrrrRRROORRrrrrrrr'),
        (23, 12, 'OKKKKKKKKKKKKKKKKKKR'),
        (24, 12, 'OYYWWWYYYOOOOOOORRRR'),
        (25, 12, 'ROOYYYOOOOOOOORRRRrr'),
        (26, 13, 'rRRRRRRRRRRrrrrrrr')]
TAIL = [(23, 32, 'R'), (22, 33, 'R'), (21, 34, 'O')]          # a thin end, colour only
TAIL_L = [(y, 43 - x, c) for y, x, c in TAIL]                 # ...at the coil's other end (seen from behind, and behind it from the side)
# From the side, facing right (the left view is its mirror): the same coil further left, the neck leaning back
# then arching forward, the blade edge-on -- a wedge running out to a white needle. One eye.
SIDE_AT = (-7, 0)
NECK_SIDE = [(10, 18, 'YOOOOO'),
             (11, 16, 'OOOOORRR'),
             (12, 15, 'OOORRrrrr'),
             (13, 14, 'OORr'), (14, 14, 'OORr'),
             (15, 13, 'OORr'), (16, 13, 'OORr'),
             (17, 12, 'ROORr'), (18, 12, 'ROORr'),
             (19, 12, 'ROORRr'), (20, 12, 'ROORRr')]
HEAD_SIDE = [(9, 24, 'OYYY'),                    # the head runs on from the neck: a black line between them reads as a gap on the black floor
             (10, 24, 'OOKYYYY'),
             (11, 24, 'OOYYWWWWWWWWWW'),
             (12, 24, 'RROOO')]
POINT_SIDE = {(36, 11), (37, 11)}
# Three-headed: the coil moved to its place in the bigger frame, one stem, two necks fanning out of it.
COIL_AT = (9, 6)
STEM = [(y, 29, 'OORr') for y in range(14, 19)] + [(y, 28, 'ROORr') for y in range(19, 23)] + [(y, 28, 'ROORRr') for y in range(23, 27)]
LEFT_NECK = [(18, 16, 'OORr'), (19, 16, 'OORr'), (20, 17, 'OORr'), (21, 19, 'OORr'), (22, 21, 'OORRr'),
             (23, 23, 'OORRr'), (24, 25, 'ORr'), (25, 26, 'Rr')]   # straight under the head, then leaning in, thicker toward the stem
RIGHT_NECK = [(y, 61 - x - len(t), t) for y, x, t in LEFT_NECK]   # the same fan the other way; lit from the same side


def head(col, row):
    g = ff.grid(HEAD, PAL, col, row)
    return g, {(col, row), (col + 1, row)}                      # ...and its point, which carries no edge


def one():
    h, bare = head(21, 2)
    g = {**ff.grid(COIL, PAL), **ff.grid(NECK, PAL), **h, **ff.grid(TAIL, PAL)}
    bare |= set(ff.grid(TAIL, PAL))
    return ff.outline(g, bare), bare


def back():
    """From behind: the blade's plain face (no ridge below the point, no eyes), the tail's end at the other side."""
    h, bare = head(21, 2)
    h = {p: ('O' if c in 'WYK' and 4 <= p[1] - 2 <= 9 else c) for p, c in h.items()}
    g = {**ff.grid(COIL, PAL), **ff.grid(NECK, PAL), **h, **ff.grid(TAIL_L, PAL)}
    bare |= set(ff.grid(TAIL_L, PAL))
    return ff.outline(g, bare), bare


def side():
    tail = ff.grid(TAIL_L, PAL, *SIDE_AT)
    g = {**ff.grid(COIL, PAL, *SIDE_AT), **ff.grid(NECK_SIDE, PAL), **ff.grid(HEAD_SIDE, PAL), **tail}
    bare = set(tail) | POINT_SIDE
    return ff.outline(g, bare), bare


def three():
    g, bare = dict(ff.grid(COIL, PAL, *COIL_AT)), set()
    g.update(ff.grid(TAIL, PAL, *COIL_AT)); bare |= set(ff.grid(TAIL, PAL, *COIL_AT))
    for part in (LEFT_NECK, RIGHT_NECK, STEM): g.update(ff.grid(part, PAL))
    for side, (c, r) in TIPS.items():
        h, b = head(c, r)
        g.update(h); bare |= b
    return ff.outline(g, bare), bare


def checked(name, g, bare, size, old):
    print(name, flush=True)
    for line in ff.checks(g, PAL, *size, open_ok=lambda p, c: p in bare, old=old): print(' ', line, flush=True)


def fight_points(one_headed, g3):
    for name, g in one_headed:
        assert max(y for (x, y), c in g.items() if c != 'K') == BELLY_ROW, f"{name}: the coil's underside moved off the fight's row"
    for side_, (c, r) in TIPS.items():
        assert g3.get((c, r)) == 'W' and g3.get((c + 1, r)) == 'W' and (c, r - 1) not in g3, f"the {side_} head's point is off the fight's pixel"
    print(f'fight points: coil underside on row {BELLY_ROW} in every view; head points at '
          + ', '.join(f'({c}-{c + 1}, {r})' for c, r in TIPS.values()), flush=True)


# name, draft file, the drawing, frame, the old sheet and the direction of it this replaces, the old drawn box
VIEWS = [('front', '24_zoureg_frame0_draft', one, ONE, ('24_zoureg', 0), '22 x 26 (columns 11-32, rows 2-27)'),
         ('side', '24_zoureg_side_frame0_draft', side, ONE, ('24_zoureg', 2), '36 x 20 (columns 3-38, rows 8-27)'),
         ('back', '24_zoureg_back_frame0_draft', back, ONE, ('24_zoureg', 4), '22 x 26 (columns 11-32, rows 2-27)'),
         ('three heads', '24_zoureg_three_frame0_draft', three, THREE, ('24_zoureg_three', 0), '38 x 31 (columns 12-49, rows 3-33)')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    drawn = [(name, file, *draw(), size, old, box) for name, file, draw, size, old, box in VIEWS]
    for name, file, g, bare, size, old, box in drawn: checked(name, g, bare, size, box)
    fight_points([(name, g) for name, file, g, bare, size, old, box in drawn if size == ONE], drawn[-1][2])
    panels = []
    for name, file, g, bare, size, (sheet, d), box in drawn:
        im = ff.image(g, PAL, *size) if look else ff.draft(g, PAL, *size, HERE / file)
        if not look: ff.style_check(im, scratch, file)
        was = Image.open(ROOT / f'assets/enemies/{sheet}.png').convert('RGBA').crop((d * 3 * size[0], 0, d * 3 * size[0] + size[0], size[1]))
        panels += [(name.upper(), im), ('was', was)]
    ff.review(panels + [('PLAYER', ff.player())] + [(name + ' shape', ff.silhouette(ff.image(g, PAL, *size))) for name, file, g, bare, size, old, box in drawn],
              scratch / '24_look.png' if look else HERE / '24_review.png')
