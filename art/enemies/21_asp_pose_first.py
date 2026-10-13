"""Enemy 21 Asp, first-frame drafts: its old design redrawn to the bible. Front, side and back.

The asp of the bestiaries: a green serpent coiled in place, pale-bellied, with pointed pink-lined ears and
fangs, its tail curling up out of the coils toward its ear (it stops its ear with it against the charmer).
Medium tier, the old frame and drawn size. Four directions (the user): the side is drawn facing right,
the left is its mirror.

Typed as parts, back to front, each its colour pixels (a letter and a count is a run of that letter);
tools/first_frame.py layers them (a part thick enough to hold one gets a black edge, thin parts stay
colour) and draws each view through the Aseprite pixel plugin. Writes only drafts and a review; the
game's assets are not touched.

    python art/enemies/21_asp_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/21_asp_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import re, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 42, 35                 # the old sheet's frame
OLD_FRAMES = 3
PAL = {'K': '000000',
       'D': '235436', 'M': '2c6c44', 'L': '4fa667',   # green: shade, body, light (the old greens were off the palette)
       'Y': 'd0c078',                                 # belly
       'P': 'ec8476',                                 # inside its ears
       'W': 'fcfcfc',                                 # fangs
       'R': 'b70000'}                                 # its tongue (21_asp_design.py)
r = lambda s: ''.join(c * int(n or 1) for c, n in re.findall(r'([A-Za-z.])(\d*)', s))     # 'M3D2' -> 'MMMDD'
rows = lambda *spec: [(y, x, r(t)) for ys, x, t in spec for y in (ys if isinstance(ys, range) else [ys])]
mirror = lambda part: [(y, 43 - x - len(t), t[::-1]) for y, x, t in part]                 # about column 21, the middle
tone = lambda part, pairs: [(y, x, ''.join(pairs.get(c, c) for c in t)) for y, x, t in part]

# Every row is typed as it is drawn, its black lines with it (K), so nothing is left to a rule.
# ---- its coils, the same from every side: three, stacked; green over, the pale belly a line along each -----
COILS = rows((23, 14, 'KL13K'), (24, 12, 'KM17K'), (25, 13, 'KM2Y11M2K'),                     # each rounded off at its ends
             (26, 12, 'K19'), (27, 11, 'KL19K'), (28, 9, 'KM23K'), (29, 10, 'KM2Y17M2K'),
             (30, 10, 'K23'), (31, 9, 'KL23K'), (32, 7, 'KM27K'), (33, 8, 'KM2Y21M2K'), (34, 9, 'K25'))

# ---- the front ------------------------------------------------------------------------------------------
MOUTH = (21, 11)              # the middle of its mouth line
F_TAIL = rows((range(22, 29), 33, 'LM'), (range(16, 22), 32, 'LM'), (range(10, 16), 31, 'LM'), (range(6, 10), 30, 'LM'), (5, 30, 'M'))   # up out of the coils to its ear
F_HEAD = rows((1, 13, 'K'), (1, 29, 'K'), (2, 12, 'KMK'), (2, 28, 'KMK'), (3, 12, 'KPMK'), (3, 18, 'K7'), (3, 27, 'KMPK'),            # pointed ears, pink inside
              (4, 12, 'KP2MK2L7K2MP2K'), (5, 13, 'KPML11MPK'), (6, 14, 'KL13K'),
              (7, 14, 'KMKM9KMK'), (8, 14, 'KM13K'), (9, 15, 'KM11K'), (10, 15, 'KM3KM3KM3K'),                                       # an eye a side; nostrils
              (11, 16, 'KMK7MK'), (12, 16, 'KMWM5WMK'), (13, 17, 'K9'))                                                             # its mouth, and the fangs; a green chin
F_NECK = rows((14, 18, 'KMY3MK'), (15, 17, 'KM2Y3MK'), (16, 17, 'KLMK3MK'), (17, 17, 'KLMY3M2K'), (18, 18, 'KM2Y3MK'),               # risen in an S, its belly scales to us
              (19, 18, 'KLMK3MK'), (20, 18, 'KLMY3MK'), (21, 17, 'KLM2Y3MK'), (22, 13, 'K4LM2Y3MK5'))
FRONT = [(F_TAIL, 'raw'), (F_HEAD + F_NECK + COILS, 'raw')]

# ---- the side, facing right ---------------------------------------------------------------------------
S_MOUTH = (34, 9)             # the front end of its mouth line
S_TAIL = rows((range(22, 29), 8, 'ML'), (range(16, 22), 9, 'ML'), (range(10, 16), 10, 'ML'), (range(6, 10), 12, 'ML'), (5, 13, 'ML'),   # up behind it to its ear
              (4, 14, 'ML'), (3, 15, 'M'))
S_HEAD = rows((1, 18, 'K'), (2, 17, 'KMK'), (3, 17, 'KPMK'), (3, 22, 'K6'), (4, 17, 'KP2MKL6K3'), (5, 18, 'KPML9MK2'),               # its ear, at the back of its head
              (6, 19, 'KL8MKM3K2'), (7, 19, 'KM14K'), (8, 19, 'KM12KMK'),                                                            # an eye; a nostril
              (9, 19, 'KM4K11'), (10, 20, 'KM2Y8WK'), (11, 21, 'K2Y7K2'))                                                           # the mouth line; the pale jaw, a fang over its lip
S_NECK = rows((12, 19, 'KLM2Y2K5'), (13, 18, 'KLM2Y3K'), (14, 17, 'KLM2K4'), (15, 16, 'KLM2Y3K'), (16, 15, 'KLM2Y3K'),               # leaning back over its coils, then forward
              (17, 15, 'KLM2K4'), (18, 15, 'KLM2Y3K'), (19, 16, 'KLM2Y3K'), (20, 16, 'KLM2K4'), (21, 17, 'KLM2Y3K'), (22, 13, 'K4LM2Y3K8'))
SIDE = [(S_TAIL, 'raw'), (S_HEAD + S_NECK + COILS, 'raw')]

# ---- the back: the front with no face, no belly, no pink; the tail on the other side ----------------------
B_HEAD = rows((1, 13, 'K'), (1, 29, 'K'), (2, 12, 'KMK'), (2, 28, 'KMK'), (3, 12, 'KDMK'), (3, 18, 'K7'), (3, 27, 'KMDK'),
              (4, 12, 'KD2MK2L7K2MD2K'), (5, 13, 'KDML11MDK'), (6, 14, 'KL13K'), (range(7, 9), 14, 'KM13K'), (range(9, 11), 15, 'KM11K'),
              (range(11, 13), 16, 'KM9K'), (13, 17, 'K2M5K2'))
B_NECK = rows((14, 18, 'KM2DM2K'), (15, 17, 'KM3DM2K'), (16, 17, 'KLM2DM2K'), (17, 17, 'KLM2DM3K'), (18, 18, 'KM3DM2K'),             # its spine
              (range(19, 21), 18, 'KLM2DM2K'), (21, 17, 'KLM3DM2K'), (22, 13, 'K4LM2MDM2K5'))
BACK = [(mirror(F_TAIL), 'raw'), (B_HEAD + B_NECK + COILS, 'raw')]


def view(parts=FRONT):
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet's direction it replaces, the old drawn box
VIEWS = [('front', '21_asp_frame0_draft', FRONT, 0, '29 x 34 (columns 7-35, rows 1-34)'),
         ('side', '21_asp_side_frame0_draft', SIDE, 2, '33 x 34 (columns 4-36, rows 1-34)'),
         ('back', '21_asp_back_frame0_draft', BACK, 4, '28 x 34')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / 'assets/enemies/21_asp.png').convert('RGBA')
    g = view(FRONT)[0]
    assert all(g.get((MOUTH[0] + dx, MOUTH[1])) == 'K' for dx in (-3, 0, 3)), 'the front mouth is not where MOUTH says'
    g = view(SIDE)[0]
    assert g.get(S_MOUTH) == 'K' and (S_MOUTH[0] + 1, S_MOUTH[1]) not in g, 'the side mouth is not where S_MOUTH says'
    print(f'mouth: the front line is centred on {MOUTH}; the side line ends at {S_MOUTH}', flush=True)
    panels, shapes = [], []
    for name, file, parts, d, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)
        if not look: ff.style_check(im, scratch, file)
        panels += [(name.upper(), im), ('was', old.crop((d * OLD_FRAMES * W, 0, d * OLD_FRAMES * W + W, H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '21_look.png' if look else HERE / '21_review.png')
    if look:
        big = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
        for i, (name, file, parts, d, box) in enumerate(VIEWS): big.alpha_composite(ff.image(view(parts)[0], PAL, W, H), (i * W, 0))
        big.resize((big.width * 10, big.height * 10), Image.Resampling.NEAREST).save(scratch / '21_big.png')
