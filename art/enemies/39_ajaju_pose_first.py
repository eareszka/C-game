"""Enemy 39 Ajaju, first-frame drafts: its old design redrawn to the bible. Front, side and back.

A green chameleon high on kneeless bamboo-stalk legs: an orange casque, a turret eye bulging at each
side, and a bunch of red forked tongues hanging from its mouth. Four directions (the user): the side
is drawn facing right, the left is its mirror. The fight fires everything from its mouth, so the
front's mouth stays on the fight's pixel.

Typed as parts, back to front, each its colour pixels; tools/first_frame.py layers them (a part thick
enough to hold one gets a black edge, thin parts stay colour) and draws each view through the Aseprite
pixel plugin. Writes only drafts and a review; the game's assets are not touched.

    python art/enemies/39_ajaju_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/39_ajaju_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 62, 47                 # the old sheet's frame
MOUTH = (31, 16)              # the pixel the fight fires from (class Ajaju: mouth(), art 31.5, 16)
PAL = {'K': '000000',
       'D': '2c6c44', 'M': '4fa667', 'L': 'a8f0bc',   # green: shade, body, light
       'y': 'd0c078', 'Y': 'f0e880',                  # bamboo legs: shade, light
       'R': 'b70000', 'r': '7c0a1b',                  # tongues, and their dark side
       'O': 'fc9838'}                                 # casque
mirror = lambda rows: [(y, 63 - x - len(t), t[::-1]) for y, x, t in rows]      # about column 31, the middle

TAIL = [(20, 40, 'MMMM'), (21, 39, 'M....M'), (22, 39, 'M..M.M'), (23, 40, 'MM..M'), (24, 44, 'M'), (25, 37, 'MMMMMMM')]   # curled in a spiral behind its right leg
LEG = [(y, 23, 'YYYyy') for y in range(16, 23)] + [(y, 22, 'YYYyy') for y in range(23, 31)] + [(y, 21, 'YYYyy') for y in range(31, 39)] \
    + [(y, 21, 'YYyy') for y in range(39, 44)] + [(44, 19, 'YYYyyy'), (45, 19, 'yyyyyy')]  # a stilt: no joint, splaying outward, thinner at the ankle
BODY = [(17, 27, 'DDDDDDDDD'), (18, 26, 'MDDDDDDDDDM'), (19, 26, 'MMDDDDDDDMM'), (20, 26, 'MMMMMMMMMMM'), (21, 26, 'MMMMMMMMMMM'),
        (22, 26, 'MMMMMMMMMMM'), (23, 26, 'MMMMMMMMMMM'), (24, 26, 'DMMMMMMMMMD'), (25, 27, 'DMMMMMMMD'), (26, 28, 'DDMMMDD'),
        (27, 30, 'DDD')]                                                                      # the chest, in shadow under the jaw
CASQUE = [(6, 31, 'O'), (7, 30, 'OOO'), (8, 30, 'OOO'), (9, 29, 'OOOOO'), (10, 29, 'OOOOO')]
HEAD = [(10, 29, 'MLLLM'), (11, 28, 'MLLLLLM'), (12, 27, 'MMLLLLLMM'), (13, 26, 'MMMMLLLMMMM'), (14, 26, 'MMMMMMMMMMM'),
        (15, 26, 'MMMMMMMMMMM'),                                                             # narrowing up to the casque
        (16, 26, 'DKKKKKKKKKD'),                                                             # its mouth
        (17, 27, 'DDDDDDDDD')]
EYE = [(12, 22, 'LLL'), (13, 21, 'LLLLL'), (14, 21, 'LLKLL'), (15, 21, 'LLLMM'), (16, 22, 'MMM')]   # a turret eye, out at the side
TONGUE_MID = [(17, 31, 'r'), (18, 31, 'R'), (19, 31, 'R'), (20, 31, 'R'), (21, 31, 'R'), (22, 31, 'R'), (23, 31, 'R'), (24, 31, 'R'),
              (25, 31, 'R'), (26, 31, 'R'), (27, 31, 'R'), (28, 30, 'RRR'), (29, 29, 'R...R')]                                         # each to a forked tip
TONGUE_IN = [(17, 28, 'rr'), (18, 28, 'rR'), (19, 28, 'rR'), (20, 28, 'rR'), (21, 27, 'rR'), (22, 27, 'rR'), (23, 27, 'R'), (24, 27, 'R'),
             (25, 26, 'RR'), (26, 25, 'R..R')]
TONGUE_OUT = [(17, 26, 'r'), (18, 26, 'R'), (19, 25, 'R'), (20, 25, 'R'), (21, 24, 'R.R')]

FRONT = [(TAIL, 'raw'), (LEG, 'solid'), (mirror(LEG), 'solid'), (BODY, 'solid'), (CASQUE, 'solid'),
         (HEAD, 'solid'), (EYE, 'solid'), (mirror(EYE), 'solid'),
         (TONGUE_OUT, 'raw'), (mirror(TONGUE_OUT), 'raw'), (TONGUE_IN, 'raw'), (mirror(TONGUE_IN), 'raw'), (TONGUE_MID, 'raw')]

# ---- the side, facing right ---------------------------------------------------------------------------
S_MOUTH = (51, 16)            # the front of its mouth
S_TAIL = [(18, 7, 'MMM'), (19, 5, 'MMMMM'), (20, 4, 'MM'), (21, 4, 'M.MMM'), (22, 4, 'M.M..M'), (23, 4, 'M.MM.M'), (24, 4, 'M....M'),
          (25, 5, 'MMMM')]                                                                    # the thin end of its tail, curled in a spiral
S_FAR_LEGS = [(y, 24, 'yyyy') for y in range(21, 38)] + [(y, 24, 'yyy') for y in range(38, 44)] + [(44, 23, 'yyyyy'), (45, 23, 'yyyyy')] \
    + [(y, 29, 'yyyy') for y in range(21, 38)] + [(y, 30, 'yyy') for y in range(38, 44)] + [(44, 29, 'yyyyy'), (45, 29, 'yyyyy')]   # the far pair, in shade, straighter
S_HIND_LEG = [(y, 19, 'YYYYyy') for y in range(19, 26)] + [(y, 19, 'YYYyy') for y in range(26, 31)] + [(y, 18, 'YYYyy') for y in range(31, 36)] \
    + [(y, 18, 'YYyy') for y in range(36, 41)] + [(y, 17, 'YYyy') for y in range(41, 44)] \
    + [(44, 16, 'YYYYyyy'), (45, 15, 'yyyy.yyyy')]                                           # a stilt leaning back, thicker at the hip, a two-toed foot
S_FORE_LEG = [(y, 33, 'YYYYyy') for y in range(19, 26)] + [(y, 34, 'YYYyy') for y in range(26, 31)] + [(y, 35, 'YYYyy') for y in range(31, 36)] \
    + [(y, 36, 'YYyy') for y in range(36, 41)] + [(y, 37, 'YYyy') for y in range(41, 44)] \
    + [(44, 36, 'YYYYyyy'), (45, 35, 'yyyy.yyyy')]                                           # leaning forward
S_BODY = [(11, 27, 'M.MMM.M'), (12, 23, 'M.MMMMMMMMMMMM'), (13, 21, 'MMLLLLLLLLLLLLLLMM'),               # a ridged, arched back,
          (14, 19, 'MMLLLLLLLLLLLLLMMMMM'), (15, 17, 'MMLLMMMMMMMMMMMMMMMMMM'), (16, 15, 'MMLLMMMMMMMMMMMMMMMMMMMM'),      # lit under the ridge;
          (17, 12, 'MMMMMMMMMMMMMMMMMMMMMMMMMMM'), (18, 10, 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMM'), (19, 10, 'MMMDDDMMMMMMMMMMMMMMMMMMMMMMD'),               # the rump narrowing into the root of the tail;
          (20, 13, 'MMMDDMMMMMMMMMMMMMMMMMMMDM'), (21, 16, 'MMDDDDDDMMMMMMMMMMDDDM'), (22, 18, 'MMMDDDDDDMMMMDDDDDM'),   # a belly that sags, dark under
          (23, 21, 'MMMDDDDDDDDDDMM'), (24, 24, 'MMMDDDDMMM'), (25, 27, 'MMMM')]
S_HEAD = [(7, 37, 'OO'), (8, 36, 'OOOOO'), (9, 36, 'OOOOLLL'),                                # the casque: a helmet rising to a point at the back
          (10, 35, 'MMOLLLLLLLM'), (11, 35, 'MMMLLLLLLLLMM'), (12, 35, 'MMMMMMMMMMMMMM'), (13, 35, 'MMMMMMMMMMMMMMMM'),
          (14, 35, 'MMMMMMMMMMMMMMMMM'), (15, 35, 'MMMMMMMMMMMMMMMMM'),                                           # the snout, tapering
          (16, 36, 'DMMMMKKKKKKKKKKK'),                                                         # its mouth
          (17, 36, 'DDMMMDDDDDDDDDD'), (18, 37, 'DDDDDDDDDDDD'), (19, 38, 'DDDDDDDD'), (20, 39, 'DDDDD')]   # the jaw, and its throat pouch
S_EYE = [(11, 41, 'LLL'), (12, 40, 'LLLLL'), (13, 40, 'LLKLL'), (14, 40, 'LLLMM'), (15, 41, 'MMM')]   # the turret eye, on the side of its head
S_TONGUE_FORE = [(17, 49, 'r'), (18, 49, 'R'), (19, 49, 'R'), (20, 49, 'R'), (21, 49, 'R'), (22, 49, 'R'), (23, 49, 'R'), (24, 49, 'R'),
                 (25, 49, 'R'), (26, 49, 'R'), (27, 49, 'R'), (28, 48, 'RRR'), (29, 47, 'R...R')]
S_TONGUE_MID = [(17, 46, 'rr'), (18, 46, 'rR'), (19, 46, 'rR'), (20, 46, 'rR'), (21, 45, 'rR'), (22, 45, 'rR'), (23, 45, 'R'), (24, 45, 'R'),
                (25, 44, 'RR'), (26, 43, 'R..R')]
S_TONGUE_HIND = [(17, 44, 'r'), (18, 44, 'R'), (19, 43, 'R'), (20, 43, 'R'), (21, 42, 'R.R')]
SIDE = [(S_FAR_LEGS, 'solid'), (S_TAIL, 'raw'), (S_HIND_LEG, 'solid'), (S_FORE_LEG, 'solid'), (S_BODY, 'solid'),
        (S_HEAD, 'solid'), (S_EYE, 'solid'), (S_TONGUE_HIND, 'raw'), (S_TONGUE_MID, 'raw'), (S_TONGUE_FORE, 'raw')]

# ---- the back ----------------------------------------------------------------------------------------
swap = lambda rows, a, b: [(y, x, t.replace(a, b)) for y, x, t in rows]
B_BODY = swap(BODY, 'D', 'M')                                                                 # no shadow under a jaw from behind
B_HEAD = [(y, x, t.replace('K', 'M').replace('D', 'M')) for y, x, t in HEAD]                  # no mouth
B_EYE = swap(EYE, 'K', 'L')                                                                   # the turrets, turned away
B_SPINE = [(y, 31, 'D') for y in range(12, 27)]
B_TAIL = mirror(TAIL)                                                                         # the same curl, now nearest us
BACK = [(LEG, 'solid'), (mirror(LEG), 'solid'), (B_BODY, 'solid'), (CASQUE, 'solid'), (B_HEAD, 'solid'),
        (B_EYE, 'solid'), (mirror(B_EYE), 'solid'), (B_SPINE, 'raw'), (B_TAIL, 'raw')]


def view(parts=FRONT):
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet's direction it replaces, the old drawn box
VIEWS = [('front', '39_ajaju_frame0_draft', FRONT, 0, '21 x 40 (columns 21-41, rows 6-45)'),
         ('side', '39_ajaju_side_frame0_draft', SIDE, 2, '41 x 37'),
         ('back', '39_ajaju_back_frame0_draft', BACK, 4, '19 x 40')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / 'assets/enemies/39_ajaju.png').convert('RGBA')
    g = view(FRONT)[0]
    assert g.get(MOUTH) == 'K' and all(g.get((MOUTH[0] + dx, MOUTH[1])) == 'K' for dx in (-4, 4)), 'the front mouth is off the fight pixel'
    g = view(SIDE)[0]
    assert g.get(S_MOUTH) == 'K' and (S_MOUTH[0] + 1, S_MOUTH[1]) not in g, 'the side mouth is not where S_MOUTH says'
    print(f'fight point: the front mouth line is centred on {MOUTH}; the side mouth ends at {S_MOUTH}', flush=True)
    panels, shapes = [], []
    for name, file, parts, d, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)
        if not look: ff.style_check(im, scratch, file)
        panels += [(name.upper(), im), ('was', old.crop((d * 3 * W, 0, d * 3 * W + W, H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '39_look.png' if look else HERE / '39_review.png')
    if look:
        big = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
        for i, (name, file, parts, d, box) in enumerate(VIEWS): big.alpha_composite(ff.image(view(parts)[0], PAL, W, H), (i * W, 0))
        big.resize((big.width * 9, big.height * 9), Image.Resampling.NEAREST).save(scratch / '39_big.png')
