"""Enemy 86 Leucrocotta, first-frame drafts: its old design redrawn to the bible. Front, side and back.

Pliny's leucrocotta: a lion's body, neck, mane and tufted tail on a stag's long thin legs and cloven
hooves, with a badger's striped head and a mouth slit back to its ears on one ridge of bone. Big tier,
the old frame and drawn size. Four directions (the user): the side is drawn facing right, the left is
its mirror.

The front is the user's drawing: they narrowed it in Aseprite, and it is held here pixel for pixel. The side
and back are typed as parts, back to front, each its colour pixels (a letter and a count is a run of that letter);
tools/first_frame.py layers them (a part thick enough to hold one gets a black edge, thin parts stay
colour) and draws each view through the Aseprite pixel plugin. Writes only drafts and a review; the
game's assets are not touched.

    python art/enemies/86_leucrocotta_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/86_leucrocotta_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import re, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 98, 65                 # the old sheet's frame
OLD_FRAMES = 5
PAL = {'K': '000000',
       'A': 'd89830', 'a': 'c18a39', 'b': '815423', 'h': '583518',   # tawny: light, body; brown: mane and shade, deep shade and hooves
       'W': 'e8e0c0', 'k': '282828',                                  # the badger head: bone white, black
       'm': '531b1c', 'R': 'b6433d'}                                  # inside its mouth, when it calls (86_leucrocotta_design.py)
r = lambda s: ''.join(c * int(n or 1) for c, n in re.findall(r'([A-Za-z.])(\d*)', s))     # 'a3b2' -> 'aaabb'
rows = lambda *spec: [(y, x, r(t)) for ys, x, t in spec for y in (ys if isinstance(ys, range) else [ys])]

# ---- the side, facing right ---------------------------------------------------------------------------
S_MOUTH = (83, 16)            # the front end of its mouth line
S_FAR = rows(                 # the far legs, in shade: the hind one under the belly, the fore one stepping ahead
    (range(34, 37), 38, 'b5h3'), (range(37, 39), 37, 'b5h3'), (range(39, 41), 37, 'b4h3'), (range(41, 43), 36, 'b4h3'),
    (range(43, 45), 35, 'b3h3'), (45, 34, 'b3h3'), (46, 35, 'b3h2'), (range(47, 53), 36, 'b2h2'), (range(53, 60), 37, 'b2h2'),
    (range(60, 62), 37, 'h5'), (62, 37, 'h2Kh2'), (63, 37, 'h5'),
    (range(36, 49), 59, 'b3h2'), (range(49, 51), 60, 'b3h2'), (range(51, 55), 61, 'b2h2'), (range(55, 60), 62, 'b2h2'),
    (range(60, 62), 62, 'h5'), (62, 62, 'h2Kh2'), (63, 62, 'h5'))
S_TAIL = rows(                # a lion's tail hanging off the rump to its dark tuft
    (27, 24, 'ab'), (28, 23, 'ab'), (29, 22, 'ab'), (range(30, 34), 21, 'ab'), (range(34, 41), 20, 'ab'), (range(41, 45), 21, 'ab'),
    (45, 20, 'h4'), (range(46, 49), 20, 'h5'), (49, 21, 'h4'), (50, 22, 'h2'))
S_BODY = rows(
    (10, 63, 'b4'), (11, 61, 'b7'), (12, 62, 'b7'), (13, 59, 'b11'), (14, 60, 'b10'), (15, 58, 'b13'),          # the mane up the back of its neck, ragged
    (16, 56, 'b15'), (17, 57, 'b14'), (18, 54, 'b17'), (19, 53, 'b18'),
    (20, 52, 'A3b16'),                                                                                         # the withers
    (21, 32, 'A4'), (21, 50, 'A6b15'),                                                                         # the croup, and a back that dips between
    (22, 30, 'A9'), (22, 47, 'A7a2b8h7'),
    (23, 29, 'A23a5b8h7'), (24, 28, 'A4a4A14a8b13'), (25, 27, 'A3a9A8a10b14'), (26, 26, 'A3a30b11'), (27, 26, 'A2a31b12'),
    (28, 26, 'a25ba6b11'), (29, 26, 'a26ba7b9'),                                                               # the shoulder's back edge,
    (30, 26, 'a12ba13ba7b5h3'), (31, 26, 'a12ba13ba6b6h3'),                                                    # the thigh's front edge
    (32, 26, 'a12b5a10ba7b4h3'), (33, 26, 'a12b8a7ba7b3h3'), (34, 27, 'a10b11a5ba7b3h3'),                      # the belly, dark under, tucked up to the flank
    (35, 27, 'a9b3'), (35, 43, 'b7a3ba8b2h2'), (36, 28, 'a7b3'), (36, 46, 'b6aba8bh2'),
    (37, 28, 'a6b3'), (37, 48, 'b7a7h2'), (38, 28, 'a6b3'), (38, 50, 'b5a5h2'),
    (39, 28, 'a5b3'), (39, 52, 'b3a3b2'),                                                                      # the deep chest, into the fore leg
    (40, 28, 'a4b3'), (41, 27, 'a4b3'), (42, 27, 'a3b3'), (43, 26, 'a3b3'), (44, 26, 'a3b2'),                  # a stag's hind leg: down and back
    (45, 25, 'a4b2'), (46, 26, 'a3b2'),                                                                        # to the hock,
    (range(47, 51), 27, 'a2b2'), (range(51, 60), 28, 'a2b2'),                                                  # then a thin cannon bone
    (range(60, 62), 28, 'h5'), (62, 28, 'h2Kh2'), (63, 28, 'h5'),                                              # to a cloven hoof
    (range(40, 45), 55, 'a3b2'), (range(45, 49), 55, 'a2b2'), (range(49, 51), 55, 'a3b2'),                     # the fore leg, a knee,
    (range(51, 60), 56, 'a2b2'), (range(60, 62), 56, 'h5'), (62, 56, 'h2Kh2'), (63, 56, 'h5'))
S_HEAD = rows(                # a badger's: a white-tipped ear, the black stripe through its eye to the nose, the mouth back to the ear
    (6, 66, 'k3'), (7, 65, 'kW3k'), (8, 64, 'k6W6'), (9, 64, 'k6W9'), (10, 63, 'W3k6W9'), (11, 63, 'W5k7W8'),
    (12, 63, 'W6k4WKk4W5'), (13, 63, 'W7k14'), (14, 63, 'W17k4'),
    (15, 63, 'W4K4W11k2'), (16, 64, 'k7K13'),                                                                  # the slit
    (17, 64, 'k8W10k'),                                                                                        # its ridge of bone
    (18, 65, 'k18'), (19, 66, 'k15'), (20, 67, 'k10'), (21, 68, 'k5'))
SIDE = [(S_FAR, 'solid'), (S_TAIL, 'solid'), (S_BODY, 'solid'), (S_HEAD, 'solid')]

# ---- the front: the user's pixels (they narrowed it, 2026-10-12), every one as they saved it ----------------
MOUTH = (50, 19)              # the middle of its mouth line (columns 45-56)
F_USER = [
    (6, 45, 'KKK......KKK'),
    (7, 44, 'KWWWKKKKKKWWWK'),
    (8, 43, 'KkkkkkWWWWkkkkkK'),
    (9, 43, 'KWkkkkWWWWkkkkWK'),
    (10, 41, 'KKWWkkkkWWWWkkkkWWKK'),
    (11, 40, 'KbKWWkkkkWWWWkkkkWWKbK'),
    (12, 39, 'KbbKWWkWKkkWWkkKWkWWKbbK'),
    (13, 39, 'KbbKWWWkkkkWWkkkkWWWKbbK'),
    (14, 38, 'KbbbWKWWWkkkWWkkkWWWKWbbbK'),
    (15, 38, 'KbbbbbKWWWkkWWkkWWWKbbbbbK'),
    (16, 39, 'KbbbbKWWWWkWWkWWWWKbbbbK'),
    (17, 38, 'KbbbbbbKWWWWkkWWWWKbbbbbbK'),
    (18, 37, 'KbbbbbbbKWWWWWWWWWWKbbbbbbbK'),
    (19, 38, 'KbbbbbbKKKKKKKKKKKKbbbbbbK'),
    (20, 39, 'KbbbbbbKWWWWWWWWKbbbbbbK'),
    (21, 38, 'KbbbbbbbbKKkkkkKKbbbbbbbbK'),
    (22, 39, 'KbbbbbbbbbKKKKbbbbbbbbbK'),
    (23, 40, 'KbbbhhhhhhhhhhhhhhbbbK'),
    (24, 40, 'KKbbbhhhhhhhhhhhhbbbKK'),
    (25, 39, 'KAKbbbbbhhhhhhhhbbbbbKAK'),
    (26, 39, 'KaaKbbbbbbbbbbbbbbbbKaaK'),
    (27, 39, 'KaaKbbbbbbbbbbbbbbbbKaaK'),
    (28, 39, 'KaaaKbbbbbbbbbbbbbbKaaaK'),
    (29, 39, 'KaaaKbbbbbbbbbbbbbbKaaaK'),
    (30, 39, 'KaaaaKbbbbbbbbbbbbKaaaaK'),
    (31, 39, 'KaaaaKbbbbbbbbbbbbKaaaaK'),
    (32, 39, 'KaaaaaKbbbbbbbbbbKaaaaaK'),
    (33, 39, 'KaaaaaaKbbbbbbbbKaaaaaaK'),
    (34, 37, 'abaKKKKbaaKbbbbbbKaabKKKKa'),
    (35, 37, 'abKaaabKaaaKbbbbKaaaKbaaaK'),
    (36, 37, 'abKaaabKbbbbKKKKbbbbKbaaaK'),
    (37, 37, 'abKaaabKbbbbbbbbbbbbKbaaaK'),
    (38, 37, 'abKaaabKbbbbbbbbbbbbKbaaaK'),
    (39, 37, 'abKaaabKbbbbbbbbbbbbKbaaaK'),
    (40, 37, 'abKaaabKKKbbbbbbbbKKKbaaaK'),
    (41, 36, 'ab.KaaabK.KKbbbbbbKK.KbaaaK'),
    (42, 36, 'ab..KaabK.KbKKKKKKbK.KbaaK'),
    (43, 36, 'ab..KaabK.KhbK..KbhK.KbaaK'),
    (44, 36, 'ab..KaabK.KhbK..KbhK.KbaaK'),
    (45, 36, 'ab..KaabK.KhbK..KbhK.KbaaK'),
    (46, 36, 'ab..KaabK.KhbK..KbhK.KbaaK'),
    (47, 36, 'ab.KaaabK.KhbK..KbhK.KbaaaK'),
    (48, 35, 'ab..KaaabK.KhbK..KbhK.KbaaaK'),
    (49, 35, 'ab..KaaabK.KhbK..KbhK.KbaaaK'),
    (50, 35, 'KK...KabK..KhbK..KbhK..KbaK'),
    (51, 34, 'KhhK..KabK..KhbK..KbhK..KbaK'),
    (52, 33, 'KhhhK..KabK..KhbK..KbhK..KbaK'),
    (53, 33, 'KhhhK..KabK..KhbK..KbhK..KbaK'),
    (54, 34, 'KhhK..KabK..KhbK..KbhK..KbaK'),
    (55, 35, 'KK...KabK..KhbK..KbhK..KbaK'),
    (56, 40, 'KabK..KhbK..KbhK..KbaK'),
    (57, 40, 'KabK..KhhK..KhhK..KbaK'),
    (58, 40, 'KabK..KhhK..KhhK..KbaK'),
    (59, 40, 'KabK..KhhK..KhhK..KbaK'),
    (60, 40, 'KhhhK.hKKh..hKKh.KhhhK'),
    (61, 40, 'KhhhK............KhhhK'),
    (62, 40, 'KhKhK............KhKhK'),
    (63, 40, 'hKKKh............hKKKh'),
]
FRONT = [(F_USER, 'raw')]

# ---- the back, to the front's width: about column 50.5, the middle of the user's front ------------------
mirror2 = lambda part: [(y, 102 - x - len(t), t[::-1]) for y, x, t in part]
B_FORE = rows((range(42, 58), 46, 'h2b2'), (range(58, 61), 46, 'h4'))                                          # a fore leg, far off between the hind ones
B_HEAD = rows((6, 45, 'k3'), (6, 54, 'k3'), (7, 44, 'kW3kW4kW3k'), (range(8, 10), 43, 'k6W4k6'),
              (range(10, 15), 42, 'W3k4W4k4W3'), (15, 43, 'W2k4W4k4W2'))                                       # the stripes, running back off its crown
B_MANE = rows((12, 45, 'b12'), (13, 44, 'b14'), (14, 44, 'b14'), (15, 43, 'b16'), (16, 44, 'b14'), (17, 42, 'b18'), (18, 43, 'b16'),
              (19, 41, 'b20'), (20, 42, 'b18'), (21, 41, 'b20'), (22, 42, 'b18'), (23, 43, 'b16'), (24, 44, 'b14'))   # the neck, narrower than the rump
B_SPINE = rows((range(14, 21), 50, 'hh'))                                                                      # the mane's parting
B_BODY = rows((21, 45, 'A12'), (22, 43, 'A16'), (23, 41, 'A20'), (24, 40, 'A22'), (25, 39, 'A24'),             # the croup, round over the top
              (range(26, 28), 39, 'a24'), (range(28, 37), 38, 'a26'), (range(37, 40), 39, 'a24'),              # the haunches, widest in the middle
              (range(40, 42), 39, 'a7b10a7'),                                                                  # dark between the thighs
              (range(42, 45), 39, 'a4b2'), (range(42, 45), 57, 'b2a4'), (range(45, 50), 40, 'a3b2'), (range(45, 50), 57, 'b2a3'),
              (range(50, 60), 41, 'a2b2'), (range(50, 60), 57, 'b2a2'),
              (range(60, 62), 40, 'h5'), (range(60, 62), 57, 'h5'), (62, 40, 'h2Kh2'), (62, 57, 'h2Kh2'), (63, 40, 'h5'), (63, 57, 'h5'))
B_TAIL = rows((range(24, 32), 48, 'a2b2'), (range(32, 40), 49, 'a2b2'), (range(40, 47), 50, 'a2b2'),            # down the middle of the rump, nearest us
              (47, 49, 'h5'), (range(48, 51), 48, 'h6'), (51, 49, 'h5'), (52, 50, 'h3'))
BACK = [(B_FORE, 'solid'), (mirror2(B_FORE), 'solid'), (B_HEAD, 'solid'), (B_MANE, 'solid'), (B_SPINE, 'raw'), (B_BODY, 'solid'), (B_TAIL, 'solid')]


def view(parts=FRONT):
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet's direction it replaces, the old drawn box
VIEWS = [('front', '86_leucrocotta_frame0_draft', FRONT, 0, '33 x 58 (columns 33-65, rows 6-63)'),
         ('side', '86_leucrocotta_side_frame0_draft', SIDE, 2, '64 x 58 (columns 20-83, rows 6-63)'),
         ('back', '86_leucrocotta_back_frame0_draft', BACK, 4, '33 x 58')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / 'assets/enemies/86_leucrocotta.png').convert('RGBA')
    g = view(FRONT)[0]
    assert all(g.get((MOUTH[0] + dx, MOUTH[1])) == 'K' for dx in (-5, 0, 5)), 'the front mouth is not where MOUTH says'
    g = view(SIDE)[0]
    assert g.get(S_MOUTH) == 'K' and (S_MOUTH[0] + 1, S_MOUTH[1]) not in g, 'the side mouth is not where S_MOUTH says'
    print(f'mouth: the front line is centred on {MOUTH}; the side line ends at {S_MOUTH}', flush=True)
    panels, shapes = [], []
    for name, file, parts, d, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box, cap=70): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)
        if not look: ff.style_check(im, scratch, file, tier='big')
        panels += [(name.upper(), im), ('was', old.crop((d * OLD_FRAMES * W, 0, d * OLD_FRAMES * W + W, H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '86_look.png' if look else HERE / '86_review.png', scale=4)
    if look:
        big = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
        for i, (name, file, parts, d, box) in enumerate(VIEWS): big.alpha_composite(ff.image(view(parts)[0], PAL, W, H), (i * W, 0))
        big.resize((big.width * 6, big.height * 6), Image.Resampling.NEAREST).save(scratch / '86_big.png')
