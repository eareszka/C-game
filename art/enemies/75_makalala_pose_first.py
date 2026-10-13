"""Enemy 75 Makalala, first-frame drafts: its old design redrawn to the bible. Two views, a pose each.

The makalala, "the noisy one": a giant slate-grey ground bird that screams, and clubs its prey with the
great bony knob on its head. The user: "front idle. left and right flying".

    front  standing, for its idle: the ivory club over a hooked yellow beak and fierce eyes, a long neck,
           short folded wings, long scaly legs
    side   flying, facing right (the left is its mirror): neck stretched out, wings raised, legs trailing,
           the club glowing. The club's middle is the frame pixel the fight fires its lasers from (49, 15).

Typed as parts, back to front, each its colour pixels (a letter and a count is a run of that letter);
tools/first_frame.py layers them (a part thick enough to hold one gets a black edge, thin parts stay
colour) and draws each view through the Aseprite pixel plugin. Writes only drafts and a review; the
game's assets are not touched.

    python art/enemies/75_makalala_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/75_makalala_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import re, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 98, 65                 # the old sheets' frame
CLUB = (49, 15)               # the middle of its club in the flying sheet: class Makalala, club()
PAL = {'K': '000000',
       'D': '34343e', 'M': '474751', 'L': '595965',   # slate: shade, body, light
       'W': 'e8e0c0',                                 # the club, ivory
       'Y': 'c9a433', 'y': '876a1f',                  # beak, and its underside
       'E': 'f0bc3c',                                 # eye; the club's glow
       'g': '848694'}                                 # scaly legs; the club's shade
r = lambda s: ''.join(c * int(n or 1) for c, n in re.findall(r'([A-Za-z.])(\d*)', s))     # 'M3D2' -> 'MMMDD'
rows = lambda *spec: [(y, x, r(t)) for ys, x, t in spec for y in (ys if isinstance(ys, range) else [ys])]
mirror = lambda part: [(y, 99 - x - len(t), t[::-1]) for y, x, t in part]                 # about column 49, the middle
move = lambda part, dx, dy: [(y + dy, x + dx, t) for y, x, t in part]
tone = lambda part, a, b: [(y, x, t.replace(a, b)) for y, x, t in part]

# ---- the front, standing --------------------------------------------------------------------------------
BEAK = (49, 21)               # the tip of its beak
F_LEG = rows((range(44, 53), 45, 'g3'), (range(53, 55), 44, 'g5'), (range(55, 62), 45, 'g3'),      # ours left: a long scaly shank with a knee,
             (62, 44, 'g5'), (63, 44, 'g.g.g'))                                               # three toes
F_BODY = rows((27, 46, 'M7'), (28, 44, 'M11'), (29, 43, 'M2L9M2'), (30, 42, 'M3L9M3'), (range(31, 38), 41, 'M4L9M4'),       # a plump body, a paler breast
              (range(38, 40), 41, 'M17'), (range(40, 42), 42, 'D15'), (42, 43, 'D13'), (43, 44, 'D11'), (44, 45, 'D9'), (45, 47, 'D5'))
F_WING = rows((30, 41, 'M3'), (31, 40, 'M2D3'), (32, 39, 'M2D4'), (range(33, 37), 38, 'M2D5'), (range(37, 39), 39, 'MD5'),   # ours left: short, folded
              (range(39, 41), 40, 'D5'), (41, 41, 'D4'), (42, 42, 'D3'), (43, 43, 'D2'))       # round against its side, to a point
F_NECK = rows((range(19, 27), 46, 'LM4D2'), (range(27, 30), 45, 'LM5D3'))
F_HEAD = rows((10, 46, 'M7'), (11, 44, 'M11'), (12, 43, 'MD4M3D4M'),                          # heavy brows
              (13, 42, 'M2E2KM5KE2M2'), (14, 42, 'M2E3M5E3M2'),                               # fierce eyes
              (15, 42, 'M15'), (16, 43, 'M13'), (17, 44, 'M11'), (18, 45, 'D9'), (19, 46, 'D7'))
F_BEAK = rows((13, 48, 'Y3'), (range(14, 17), 47, 'Y4y'), (17, 47, 'Y3y2'), (18, 47, 'yY2y2'), (19, 48, 'Y2y'), (20, 48, 'yYy'),
              (21, 48, 'y3'), (22, 49, 'y'))                                                  # hooked, coming down at us
F_CLUB = rows((2, 47, 'W5'), (3, 45, 'W9'), (4, 44, 'W11'), (5, 43, 'W11g2'), (6, 44, 'W8g3'), (7, 43, 'W9g4'), (8, 44, 'W6g5'),
              (9, 45, 'W3g6'), (10, 47, 'g5'))                                                # a mace of bone, knobbed
FRONT = [(F_LEG, 'solid'), (mirror(F_LEG), 'solid'), (F_BODY, 'solid'), (F_WING, 'solid'), (mirror(F_WING), 'solid'),
         (F_NECK, 'solid'), (F_HEAD, 'solid'), (F_BEAK, 'solid'), (F_CLUB, 'solid')]

# ---- the side, flying, facing right ---------------------------------------------------------------------
S_BEAK = (72, 23)             # the tip of its beak
S_WING = rows((5, 19, 'D4'), (6, 17, 'D5M3'), (7, 18, 'D5M4'), (8, 19, 'D4M5'), (9, 18, 'D5M4L2'), (10, 19, 'D4M5L3'),      # raised: feathered
              (11, 20, 'D4M4L3'), (12, 19, 'D5M5L3'), (13, 20, 'D4M6L3'), (14, 21, 'D4M6L3'), (15, 20, 'D5M7L3'),           # down its trailing edge,
              (16, 21, 'D4M8L3'), (17, 22, 'D4M8L3'), (18, 23, 'D3M8L3'), (19, 23, 'D4M8L3'), (20, 25, 'D3M7L3'),           # lit along the leading one
              (21, 25, 'D3M8L3'), (22, 27, 'D2M7L3'), (23, 28, 'D2M7L3'), (24, 29, 'DM7L3'), (25, 31, 'M6L3'), (26, 32, 'M5L3'))
S_TAIL = rows((25, 12, 'M8'), (26, 10, 'M2D9'), (27, 7, 'D14'), (28, 9, 'D12'), (29, 6, 'D15'), (30, 8, 'D13'), (31, 11, 'D9'))   # a shaggy plume, streaming
S_LEG = rows((37, 23, 'g3'), (38, 20, 'g4'), (39, 17, 'g4'), (40, 14, 'g4'), (41, 10, 'g5'), (40, 10, 'g'), (42, 10, 'g'))   # trailing, toes spread
S_BODY = rows((22, 45, 'L6'), (23, 30, 'L7'), (23, 43, 'L8'), (24, 25, 'L26'), (25, 22, 'L29'),                         # a deep chest tapering to the tail,
              (26, 20, 'L4M26'), (27, 19, 'M30'), (28, 18, 'M30'), (29, 18, 'M29'), (30, 18, 'M28'), (31, 19, 'M26'),      # and the outstretched neck: one part
              (32, 20, 'D24'), (33, 22, 'D21'), (34, 25, 'D16'), (35, 28, 'D11'), (36, 31, 'D6'))
S_HEAD = rows((16, 49, 'M8'), (17, 47, 'M12'), (18, 46, 'M14'), (19, 46, 'M7D6M2'),                                      # a brow over its eye
              (20, 46, 'M8E2KM4'), (21, 46, 'M8E2M5'), (22, 46, 'M14'), (23, 47, 'M13'), (24, 47, 'M12'), (25, 48, 'D10'), (26, 49, 'D7'))
S_BILL = rows((19, 60, 'Y7'), (20, 59, 'Y11'), (21, 59, 'Y13'), (range(22, 24), 59, 'Y14'), (24, 60, 'K9Y4'),               # hooked; the lower bill tucked under
              (25, 61, 'y8Y4'), (26, 62, 'y5'), (26, 70, 'Y3'), (27, 71, 'Y2'))
S_CLUB = rows((10, 47, 'E5'), (11, 45, 'E2W5E2'), (12, 44, 'E2W7E2'), (13, 43, 'E2W9E2'), (14, 44, 'E2W7E2'), (15, 43, 'E2W9E2'),
              (16, 44, 'E2W7E2'), (17, 43, 'E2W9E2'), (18, 44, 'E2W7E2'), (19, 45, 'E2W5E2'), (20, 47, 'E5'))               # glowing, as it flies
SIDE = [(tone(move(S_WING, 6, -1), 'L', 'D'), 'solid'), (S_TAIL, 'solid'), (move(S_LEG, 3, -1), 'solid'), (S_LEG, 'solid'), (S_BODY, 'solid'),
        (S_HEAD, 'solid'), (S_BILL, 'solid'), (S_CLUB, 'solid'), (S_WING, 'solid')]


def view(parts=FRONT):
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet, its frames a direction, the old sheet's direction, the old drawn box
VIEWS = [('front', '75_makalala_frame0_draft', FRONT, '75_makalala.png', 5, 0, '23 x 60 (columns 38-60, rows 4-63)'),
         ('fly', '75_makalala_fly_frame0_draft', SIDE, '75_makalala_fly.png', 4, 2, '53 x 30 (columns 13-65, rows 6-35)')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    g = view(SIDE)[0]
    club = [q for q, c in g.items() if c in 'WE' and q[1] <= 19 and 42 <= q[0] <= 56]
    xs, ys = [x for x, y in club], [y for x, y in club]
    assert ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2) == CLUB, 'the flying club is not centred on the fight pixel'
    print(f'fight point: the flying club is centred on {CLUB}; beak tips: front {BEAK}, flying {S_BEAK}', flush=True)
    panels, shapes = [], []
    for name, file, parts, old, n, d, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box, cap=70): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)
        if not look: ff.style_check(im, scratch, file, tier='big')
        was = Image.open(ROOT / 'assets/enemies' / old).convert('RGBA')
        panels += [(name.upper(), im), ('was', was.crop((d * n * W, 0, d * n * W + W, H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '75_look.png' if look else HERE / '75_review.png', scale=4)
    if look:
        big = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
        for i, (name, file, parts, old, n, d, box) in enumerate(VIEWS): big.alpha_composite(ff.image(view(parts)[0], PAL, W, H), (i * W, 0))
        big.resize((big.width * 7, big.height * 7), Image.Resampling.NEAREST).save(scratch / '75_big.png')
