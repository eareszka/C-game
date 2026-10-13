"""Enemy 78 Zankallala, first-frame drafts after the user's reference: side, front and back.

A hairy little trickster in a beehive hat, red eyes under the brim, riding a jerboa; a snake in its
hand, head raised like a staff and body trailing back over the jerboa's rump; bees round the hat.
Four directions (the user): the side is drawn facing right, the left is its mirror.

Typed as parts, back to front, each its colour pixels: tools/flat_parts.py gives a part thick enough
to hold one a black edge, and leaves thin parts (snake, tail, arms) as colour. Drawn through the
Aseprite pixel plugin. Writes only drafts and a review; the game's assets are not touched.

    python art/enemies/78_zankallala_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/78_zankallala_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 58, 53                 # the old sheet's frame
PAL = {'K': '000000',
       'D': '785830', 'M': 'b29e5c', 'L': 'cebe82',   # jerboa: shade, coat, belly
       'h': '3c2412', 'H': '633e1b',                  # the rider's hair, and its lit side and limbs
       'G': 'd89830',                                 # beehive hat, bees
       'R': 'b70000',                                 # eyes
       'S': '2c6c44'}                                 # snake
N4 = ff.N4

# ---- the side, facing right -------------------------------------------------------------------------
S_TAIL = [(35, 14, 'MMMM'), (36, 12, 'MMMM'), (37, 10, 'MMMM'), (38, 7, 'MMMMM'),      # down off the rump, then up to its tuft
          (37, 5, 'MM'), (36, 4, 'MM'), (35, 4, 'M')]
S_TUFT = [(31, 3, 'HH'), (32, 2, 'HHHH'), (33, 2, 'HHHHH'), (34, 3, 'HHHH'), (35, 3, 'H')]
S_FAR_LEG = [(43, 18, 'DDDD'), (44, 17, 'DDDD'), (45, 16, 'DDDD'), (46, 16, 'DDDD'), (47, 15, 'DDDD'),
             (48, 15, 'DDDDDDDDDD'), (49, 15, 'DDDDDDDDDDDD'), (50, 16, 'DDDDDDDDDDD')]
S_FAR_ARM = [(41, 39, 'DD'), (42, 39, 'DD'), (43, 39, 'DD'), (44, 39, 'DD'), (45, 39, 'DDD')]
S_FAR_EAR = [(20, 42, 'DD'), (21, 41, 'DDDD'), (22, 41, 'DDDD'), (23, 41, 'DDDDD'), (24, 42, 'DDDD'),
             (25, 42, 'DDDDD'), (26, 43, 'DDDD'), (27, 43, 'DDDDD'), (28, 44, 'DDDD'), (29, 44, 'DDDD')]
S_BODY = [(28, 39, 'MMMMMM'),                                       # head and body in one: back, rump, belly, snout
          (29, 38, 'MMMMMMMMM'),
          (30, 24, 'MMMMMMMMMMMMMMMMMMMMMMMM'),
          (31, 20, 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMM'),
          (32, 18, 'MMMMMMMMMMMMMMMMMMMMMMMMMMMKMMMM'),             # its eye
          (33, 17, 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM'),
          (34, 17, 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMD'),            # nose
          (35, 17, 'DMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM'),
          (36, 17, 'DMMMMMMMMMMMMMMMMMMMMMMMMMLLLL'),
          (37, 17, 'DDMMMMMMMMMMMMMMMMMMMMMLLLLL'),
          (38, 17, 'DDMMMMMMMMMMMMMMMMMMLLLLLL'),
          (39, 18, 'DDMMMMMMMMMMMMMMLLLLLLLL'),
          (40, 18, 'DDMMMMMMMMMMLLLLLLLLLLL'),
          (41, 19, 'DDMMMMMLLLLLLLLLLLLLL'),
          (42, 21, 'DDLLLLLLLLLLLLLLL'),
          (43, 23, 'LLLLLLLLLLLL')]
S_EAR = [(19, 38, 'MM'), (20, 37, 'MMMM'), (21, 37, 'MDDM'), (22, 37, 'MDDMM'), (23, 38, 'MDDM'),
         (24, 38, 'MDDMM'), (25, 39, 'MDDM'), (26, 39, 'MDDMM'), (27, 40, 'MMMM'), (28, 40, 'MMMM')]
S_LEG = [(36, 21, 'KKMMMMKK'), (37, 20, 'KMMMMMMMMK'), (38, 20, 'MMMMMMMMMK'),      # the thigh: a line over its top and front only,
         (39, 20, 'MMMMMMMMMK'), (40, 20, 'DMMMMMMMMK'), (41, 21, 'DMMMMMMK'), (42, 21, 'DDMMMMMK'),   # so it stays part of the body;
         (43, 21, 'KDMMMMK'), (44, 21, 'KDMMMK'), (45, 20, 'KDMMMK'), (46, 20, 'KDMMK'), (47, 19, 'KDMMK'),   # the shin back to the heel,
         (48, 19, 'KMMMMKKKKKKKKK'), (49, 19, 'KLLLLLLLLLLLLLLK'), (50, 20, 'KKKKKKKKKKKKKK')]          # the long foot
S_ARM = [(41, 36, 'MM'), (42, 36, 'MM'), (43, 36, 'ML'), (44, 36, 'ML'), (45, 36, 'LLL')]            # the jerboa's small forepaw
S_RIDER = [(19, 23, 'hhHHHHH'),                                                                       # a haystack of hair, ragged at the hem
           (20, 22, 'hhhHHHHHH'),
           (21, 22, 'hhhHHRHRH'),                                                                     # its eyes
           (22, 21, 'hhhhHHHHHHH'),
           (23, 21, 'hhhhhHHHHHH'),
           (24, 21, 'hhhhhHHHHHH'),
           (25, 21, 'hhhhhhHHHHH'),
           (26, 21, 'hhhhhhHHHHH'),
           (27, 21, 'hhhhhhhHHHH'),
           (28, 21, 'hhhhhhhHHHH'),
           (29, 21, 'hhhhhhhhHHH'),
           (30, 21, 'hhhhhhhhhHH'),
           (31, 21, 'hhhhhhhhhhH'),
           (32, 21, 'hh.hhh.hh.h'),
           (33, 21, 'h..h.h..h..')]
S_FOOT = [(33, 27, 'H'), (34, 27, 'H'), (35, 27, 'H'), (36, 27, 'HH'),                                # a leg down the jerboa's side,
          (37, 29, 'hh'), (36, 30, 'h'), (35, 30, 'h')]                                               # a scorpion for a spur
S_HAT = [(12, 25, 'GGG'), (13, 24, 'GGGGG'), (14, 23, 'GDDDDDG'), (15, 23, 'GGGGGGG'),                # a straw beehive, coil on coil
         (16, 22, 'GDDDDDDDG'), (17, 22, 'GGGGGGGGG'), (18, 22, 'GGGGGGGGG')]
S_HAND = [(24, 31, 'H'), (25, 32, 'H'), (26, 33, 'H'), (27, 33, 'HH')]
S_SNAKE = [(13, 35, 'SS'), (14, 35, 'SS'), (15, 35, 'S'), (16, 35, 'S'), (17, 34, 'S'), (18, 34, 'S'), (19, 34, 'S'),   # head up like a staff
           (20, 35, 'S'), (21, 35, 'S'), (22, 35, 'S'), (23, 34, 'S'), (24, 34, 'S'), (25, 34, 'S'), (26, 34, 'S'),
           (27, 35, 'S'), (28, 33, 'SSS'),                                                                              # through the hand,
           (29, 26, 'SSSSSSSS'), (30, 22, 'SSSSSSS'), (31, 19, 'SSSS'), (32, 16, 'SSSS'), (33, 13, 'SSSS'),             # across its lap,
           (34, 11, 'SSS'), (35, 9, 'SS')]                                                                              # and trailing behind
S_BEES = [(14, 19, 'Gh'), (11, 29, 'hG'), (15, 33, 'G')]

SIDE = [(S_TAIL, 'solid'), (S_TUFT, 'solid'), (S_FAR_LEG, 'solid'), (S_FAR_ARM, 'solid'), (S_FAR_EAR, 'solid'),
        (S_BODY, 'solid'), (S_EAR, 'solid'), (S_LEG, 'raw'), (S_ARM, 'solid'), (S_RIDER, 'solid'), (S_FOOT, 'raw'),
        (S_HAT, 'solid'), (S_SNAKE, 'raw'), (S_HAND, 'raw'), (S_BEES, 'raw')]

# ---- the front ---------------------------------------------------------------------------------------
mirror = lambda rows: [(y, W - x - len(t), t[::-1]) for y, x, t in rows]
F_TAIL = [(47, 17, 'MMMM'), (48, 13, 'MMMMMM'), (49, 11, 'MMMM')]                                 # round on the ground to our left
F_TUFT = [(46, 8, 'HHH'), (47, 7, 'HHHHH'), (48, 8, 'HHHH')]
F_EAR = [(16, 17, 'MM'), (17, 16, 'MMMM'), (18, 15, 'MMDDMM'), (19, 15, 'MMDDMM'), (20, 15, 'MMDDDMM'), (21, 16, 'MMDDMM'),   # a tall leaf of an ear, leaning out
         (22, 16, 'MMDDDMM'), (23, 17, 'MMDDMM'), (24, 17, 'MMDDDMM'), (25, 18, 'MMDDMM'), (26, 18, 'MMDDDMM'),
         (27, 19, 'MMDDMM'), (28, 19, 'MMMMMMM'), (29, 20, 'MMMMMM'), (30, 21, 'MMMMM')]
F_RIDER = [(19, 26, 'HHHhhh'), (20, 25, 'HHHHhhhh'), (21, 24, 'HHRRHhRRhh'), (22, 24, 'HHHHHhhhhh'),          # behind the jerboa: only its top shows
           (23, 23, 'HHHHHHhhhhhh'), (24, 23, 'HHHHHHhhhhhh'), (25, 22, 'HHHHHHHhhhhhh'), (26, 23, 'HHHHHHhhhhhh'),
           (27, 23, 'HHHHHHhhhhhhh'), (28, 23, 'HHHHHHhhhhhh'), (29, 22, 'HHHHHHHhhhhhh'), (30, 23, 'HHHHHHhhhhhh')]
F_HAT = [(12, 28, 'GGG'), (13, 27, 'GGGGG'), (14, 26, 'GDDDDDG'), (15, 26, 'GGGGGGG'),
         (16, 25, 'GDDDDDDDG'), (17, 25, 'GGGGGGGGG'), (18, 25, 'GGGGGGGGG')]
F_BODY = [(37, 24, 'MMMMMMMMMM'), (38, 24, 'MMMMMMMMMM'), (39, 24, 'MMMMMMMMMM'),                                # its top is behind the chin
          (40, 24, 'MMLLLLLLMM'), (41, 23, 'MMLLLLLLLLMM'), (42, 22, 'MMMLLLLLLLLMMM'), (43, 22, 'MMMLLLLLLLLMMM'),
          (44, 22, 'MMMLLLLLLLLMMM'), (45, 22, 'MMMLLLLLLLLMMM'), (46, 23, 'MMLLLLLLLLMM'), (47, 24, 'MMLLLLLLMM')]
F_FOOT = [(46, 20, 'MMM'), (47, 19, 'MMMMM'), (48, 19, 'MMMMM'), (49, 19, 'LLLLL'), (50, 19, 'MMMMM')]
F_HEAD = [(27, 26, 'MMMMMM'), (28, 24, 'MMMMMMMMMM'), (29, 22, 'MMMMMMMMMMMMMM'), (30, 21, 'MMMMMMMMMMMMMMMM'),     # a round face narrowing to the muzzle
          (31, 20, 'MMMMMMMMMMMMMMMMMM'), (32, 20, 'MMMMMMMMMMMMMMMMMM'), (33, 20, 'MMMMKMMMMMMMMKMMMM'), (34, 20, 'MMMMMMMMMMMMMMMMMM'),
          (35, 21, 'DMMMMMMMMMMMMMMD'), (36, 22, 'DMMMLLLLLLMMMD'), (37, 23, 'DMLLLLLLLLMD'), (38, 24, 'DLLLDDLLLD'),
          (39, 25, 'DLLLLLLD'), (40, 26, 'DDDDDD')]
F_PAWS = [(43, 26, 'MM'), (44, 26, 'LL'), (43, 30, 'MM'), (44, 30, 'LL')]
F_HAND = [(24, 35, 'H'), (25, 36, 'HH'), (26, 38, 'HH'), (27, 40, 'HH'), (28, 42, 'H')]                         # a long thin arm out past the ear
F_SNAKE = [(13, 43, 'SS'), (14, 43, 'SS'), (15, 43, 'S'), (16, 43, 'S'), (17, 44, 'S'), (18, 44, 'S'), (19, 44, 'S'), (20, 43, 'S'),
           (21, 43, 'S'), (22, 43, 'S'), (23, 44, 'S'), (24, 44, 'S'), (25, 44, 'S'), (26, 43, 'S'), (27, 43, 'S'), (28, 43, 'S'),
           (29, 44, 'S'), (30, 44, 'S'), (31, 45, 'S'), (32, 45, 'S'), (33, 46, 'S'), (34, 46, 'SS'), (35, 47, 'SS'), (36, 48, 'SS'), (37, 49, 'S')]
F_BEES = [(14, 21, 'Gh'), (11, 34, 'hG'), (16, 36, 'G')]
FRONT = [(F_TAIL, 'solid'), (F_TUFT, 'solid'), (F_RIDER, 'solid'), (F_HAT, 'solid'), (F_EAR, 'solid'), (mirror(F_EAR), 'solid'),
         (F_BODY, 'solid'), (F_FOOT, 'solid'), (mirror(F_FOOT), 'solid'), (F_HEAD, 'solid'), (F_PAWS, 'raw'),
         (F_SNAKE, 'raw'), (F_HAND, 'raw'), (F_BEES, 'raw')]

# ---- the back ----------------------------------------------------------------------------------------
plain = lambda rows: [(y, x, t.replace('D', 'M')) for y, x, t in rows]                             # an ear from behind: no inside
B_HEAD = [(26, 25, 'MMMMMMMM'), (27, 23, 'MMMMMMMMMMMM'), (28, 22, 'MMMMMMMMMMMMMM'), (29, 22, 'MMMMMMMMMMMMMM'),
          (30, 22, 'MMMMMMMMMMMMMM'), (31, 22, 'MMMMMMMMMMMMMM')]                                  # the back of its head, between the ears
B_BODY = [(30, 25, 'MMMMMMMM'), (31, 23, 'MMMMMMMMMMMM'), (32, 22, 'MMMMMMMMMMMMMM'), (33, 21, 'MMMMMMMMMMMMMMMM'),   # the rump: a pear, shaded round its right and under
          (34, 20, 'MMMMMMMMMMMMMMMMMM'), (35, 20, 'MMMMMMMMMMMMMMMMMM'), (36, 20, 'MMMMMMMMMMMMMMMMDD'), (37, 20, 'MMMMMMMMMMMMMMMDDD'),
          (38, 20, 'MMMMMMMMMMMMMMMDDD'), (39, 20, 'MMMMMMMMMMMMMMMDDD'), (40, 20, 'MMMMMMMMMMMMMMDDDD'), (41, 20, 'MMMMMMMMMMMMMDDDDD'),
          (42, 21, 'MMMMMMMMMMMDDDDD'), (43, 21, 'MMMMMMMMMDDDDDDD'), (44, 22, 'MMMMMMDDDDDDDD'), (45, 23, 'MMMDDDDDDDDD'), (46, 25, 'DDDDDDDD')]
B_TAIL = [(42, 28, 'MM'), (43, 28, 'MM'), (44, 28, 'MM'), (45, 28, 'MMM'), (46, 29, 'MMM'), (47, 30, 'MMMM'),   # down the rump and round to our right
          (48, 32, 'MMMMMM'), (49, 36, 'MMMMM')]
B_TUFT = [(46, 43, 'HHH'), (47, 41, 'HHHHH'), (48, 40, 'HHHHH'), (49, 41, 'HH')]
B_RIDER = [(19, 26, 'HHHhhh'), (20, 25, 'HHHHhhhh'), (21, 24, 'HHHHHhhhhh'), (22, 24, 'HHHHHhhhhh'),
           (23, 23, 'HHHHHHhhhhhh'), (24, 23, 'HHHHHHhhhhhh'), (25, 22, 'HHHHHHHhhhhhh'), (26, 23, 'HHHHHHhhhhhh'),
           (27, 23, 'HHHHHHhhhhhhh'), (28, 23, 'HHHHHHhhhhhh'), (29, 22, 'HHHHHHHhhhhhh'), (30, 23, 'HHHHHHhhhhhh'),
           (31, 23, 'HHHHHHhhhhhh'), (32, 23, 'HH.HHH.hh.hh'), (33, 23, 'H..H.H..h..h')]
BACK = [(plain(F_EAR), 'solid'), (plain(mirror(F_EAR)), 'solid'), (B_HEAD, 'solid'), (F_FOOT, 'solid'), (mirror(F_FOOT), 'solid'), (B_BODY, 'solid'),
        (B_TAIL, 'solid'), (B_TUFT, 'solid'), (B_RIDER, 'solid'), (F_HAT, 'solid'),
        (mirror(F_SNAKE), 'raw'), (mirror(F_HAND), 'raw'), (F_BEES, 'raw')]


def view(parts):
    """The frame, and the colour pixels on it that carry no black edge (thin parts, tips, raw parts)."""
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet's direction it replaces, the old drawn box
VIEWS = [('side', '78_zankallala_side_frame0_draft', SIDE, 2, '37 x 34 (columns 9-45, rows 17-50)'),
         ('front', '78_zankallala_front_frame0_draft', FRONT, 0, '18 x 34 (columns 20-37, rows 17-50)'),
         ('back', '78_zankallala_back_frame0_draft', BACK, 4, '18 x 34 (columns 20-37, rows 17-50)')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / 'assets/enemies/78_zankallala.png').convert('RGBA')
    panels, shapes = [], []
    for name, file, parts, d, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)
        if not look: ff.style_check(im, scratch, file)
        panels += [(name.upper(), im), ('was', old.crop((d * 3 * W, 0, d * 3 * W + W, H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '78_look.png' if look else HERE / '78_review.png')
    if look:
        big = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
        for i, (name, file, parts, d, box) in enumerate(VIEWS): big.alpha_composite(ff.image(view(parts)[0], PAL, W, H), (i * W, 0))
        big.resize((big.width * 9, big.height * 9), Image.Resampling.NEAREST).save(scratch / '78_big.png')
