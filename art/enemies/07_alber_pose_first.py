"""Enemy 07 Alber, first-frame drafts: its old design redrawn to the bible and larger (big tier).

A great fiery dragon "glowing like an electric fire", always in flight: bat wings, horns, fangs, a belly
lit from within, flame along its back. Four directions (the user): front, side and back are drawn, the
left is the side mirrored. This frame is the wings spread and raised.

The front's head, body and feet are the user's own pixels: they edited the first draft in Aseprite
(2026-10-12: orange eyes between black, yellow fangs, a smaller mouth, the thighs joined to the body
with no line over them), so those parts are set down exactly as they left them, and the side and back
were brought to match.

Typed as parts, back to front, each its colour pixels; tools/first_frame.py layers them (a part thick
enough to hold one gets a black edge, thin parts stay colour) and draws each view through the Aseprite
pixel plugin. Writes only drafts and a review; the game's assets are not touched.

    python art/enemies/07_alber_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/07_alber_pose_first.py [SCRATCH]  # check; draw the drafts that are not there yet
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 72, 64                 # room for the wings raised and lowered
OLD_W, OLD_H = 40, 41         # the old sheet's frame
PAL = {'K': '000000',
       'D': '7c0a1b', 'R': 'b70000',                  # red: back and bones, hide
       'O': 'fc9838', 'Y': 'fae488'}                  # the glow, and its eyes: orange; horns, fangs, claws: yellow
at = lambda y0, x0, lines: [(y0 + i, x0, t) for i, t in enumerate(lines)]       # a typed drawing, its top left at (x0, y0)
mirror = lambda rows: [(y, W - x - len(t), t[::-1]) for y, x, t in rows]

# ---- the front ---------------------------------------------------------------------------------------
WING = at(6, 6, [                                  # our left: arm up to the wrist, three fingers down, the skin scalloped between
    '........D...............',
    '.......DDD..............',
    '.......DDDD.............',
    '......DDDDDD............',
    '......DDDDDDD...........',
    '.....RDRDDRDDD..........',
    '.....RDRDDRRDDD.........',
    '....RDRRDRDRRDDD........',
    '....RDRRDRDRRRDDD.......',
    '...RDRRRDRDRRRRDDD......',
    '...RDRRRDRDRRRRRDDD.....',
    '..RDRRRRDRRDRRRRRDDD....',
    '..RDRRRRDRRDRRRRRRDDD...',
    '.RDRRRRRDRRDRRRRRRRDDD..',
    'DDRRRRRRDRRDRRRRRRRRDDD.',
    '.RRRRRRRDRRRDRRRRRRRRDDD',
    '..RRRRRRDRRRDRRRRRRRRRDD',
    '...RRRRDRRRRDRRRRRRRRRRD',
    '....RRRDRRRRDRRRRRRRRRRR',
    '....RRRDRRRRRDRRRRRRRRRR',
    '.....RRDRRRRRDRRRRRRRRRR',
    '.....RRDRRRRRDRRRRRRRRRR',
    '......RDRRRRRDRRRRRRRRRR',
    '......RDRRRRRRDRRRRRRRRR',
    '......RDRRRRRRDRRRRRRRRR',
    '......RDRRR..RDRRRRR...R',
    '......RDRR....DRRRR.....',
    '......RDR.....RDRRR.....',
    '......RDR......DRR......',
    '.......D.......DRR......',
    '.......D........D.......',
    '................D.......'])
F_TAIL = [(40, 32, 'RRROORRR'), (41, 32, 'RRROORRR'), (42, 32, 'RRROORRR'), (43, 33, 'RRROORRR'), (44, 33, 'RRROORRRR'), (45, 34, 'RRROORRRR'),
          (46, 35, 'RRRORRRRRR'), (47, 36, 'RRRRRRRRRRR'), (48, 37, 'RRRRRRRRRRRRR'), (49, 39, 'RRRRRRRRRRRRRRRRRRRR'), (50, 40, 'RRRRRRRRRRRRRRRRRRR'),
          (51, 42, 'DDDRRRRRRRRRRRRR'), (52, 45, 'DDDDDDDDDDDD'), (53, 48, 'DDDDDDD'),
          (43, 58, 'R'), (44, 57, 'RR'), (45, 56, 'RRR'), (46, 56, 'RRRR'), (47, 55, 'RRRRR'), (48, 55, 'RRRRR')]   # down between its feet, round to our right, the tip hooked up
F_HORN = [(2, 24, 'Y'), (3, 24, 'YY'), (4, 24, 'YYY'), (5, 25, 'YYY'), (6, 26, 'YYY'), (7, 27, 'OOO'), (8, 28, 'OOO')]
# The user's pixels, black and all (raw): horns and head; the body with its thighs; a foot.
F_HEAD = [(2, 24, 'Y......................Y'), (3, 24, 'YY....................YY'), (4, 24, 'YYY..................YYY'), (5, 25, 'YYY................YYY'),
    (6, 26, 'YYY..............YYY'), (7, 27, 'OOO..KKKKKKKK..OOO'), (8, 28, 'OOKKRRRRRRRRKKOO'), (9, 29, 'KRRRRRRRRRRRRK'),
    (10, 28, 'KRDDRRRRRRRRDDRK'), (11, 28, 'KRRDDDDRRDDDDRRK'), (12, 28, 'KRRKOKRRRRKOKRRK'), (13, 28, 'KRRRRRRRRRRRRRRK'),
    (14, 29, 'KRRRRRRRRRRRRK'), (15, 30, 'KRRRRRRRRRRK'), (16, 31, 'KRRRRRRRRK'), (17, 31, 'KRKRRRRKRK'),
    (18, 31, 'KRRRRRRRRK'), (19, 32, 'KKRRRRKK'), (20, 31, 'KYDKKKKDYK'), (21, 32, 'KDDDDDDK')]
F_TORSO = [(22, 31, 'KKKKKKKKKK'), (23, 29, 'KKRRRRRRRRRRKK'), (24, 28, 'KRRRROOOOOORRRRK'), (25, 27, 'KRRRROOOOOOOORRRRK'),
    (26, 27, 'KRRROOOYYYYOOORRRK'), (27, 27, 'KRRROOYYYYYYOORRRK'), (28, 27, 'KRRROOYYYYYYOORRRK'), (29, 27, 'KRRROOYYYYYYOORRRK'),
    (30, 27, 'KRRROOYYYYYYOORRRK'), (31, 27, 'KRRROOYYYYYYOORRRK'), (32, 27, 'KRRROOYYYYYYOORRRK'), (33, 27, 'KRRROOOYYYYOOORRRK'),
    (34, 27, 'KRRRROOYYYYOORRRRK'), (35, 27, 'KRRRROOOYYOOORRRKK'), (36, 26, 'KRRRRRROOOOOORRRRRRK'), (37, 25, 'KRRRRRRRROOOORRRRRRRRK'),
    (38, 25, 'KRRRRRRRRROORRRRRRRRRK'), (39, 25, 'KRRRRRKRRRRRRRRKRRRRRK'), (40, 25, 'KDRRRKKKDKKKKDKKKRRRDK'), (41, 33, 'K....K')]
F_FOOT = [(41, 26, 'KDRRK'), (42, 26, 'KRRRK'), (43, 25, 'KRRRRRK'), (44, 25, 'RKKKKKR'),
    (45, 25, 'Y..Y..Y'), (46, 28, 'Y')]
FRONT = [(F_TAIL, 'solid'), (WING, 'solid'), (mirror(WING), 'solid'), (F_TORSO, 'raw'), (F_HEAD, 'raw'),
         (F_FOOT, 'raw'), (mirror(F_FOOT), 'raw')]

# ---- the side, facing right ---------------------------------------------------------------------------
S_WING = [                                         # the near wing, up over its back: arm to the wrist, fingers trailing behind
    '.................DD',
    '.............RRRRDD',
    '..........RRRDDDDDDD',
    '......RRRRDDDRRRDRDDD',
    '..RRRRDDDDRRRRRDRRDDD',
    'DDDDDDRRRRRRRRDRRRDDDD',
    '..RRRRRRRRRRRDRRRDRRDDD',
    '...RRRRRRRRRDRRRRDRRDDD',
    '....RRRRRRRDRRRRRDRRRDDD',
    '.....RRRRRDRRRRRDRRRRRDDD',
    '.....RRRDRRRRRRRDRRRRRDDD',
    '.....RRDRRRRRRRRDRRRRRRDDD',
    '.....RDRRRRRRRRDRRRRRRRRDDD',
    '....RDRRRRRRRRRDRRRRRRRRDDD',
    '...RDRRRRRRRRRRDRRRRRRRRRDDD',
    '..RD...RRRRRRRDRRRRRRRRRRRDDD',
    '.RD.....RRRRRRDRRRRRRRRRRRDDD',
    '.........RRRRRDRRRRRRRRRRRRDDD',
    '.........RRRRDRRRRRRRRRRRRRRDDD',
    '..........RRRDR...RRRRRRRRRRDDD',
    '..........RRRD......RRRRRRRRRDDD',
    '..........RRD.........RRRRRRRRDDD',
    '...........RD...........RRRRRRDDD',
    '...........D..............RRRRDDD',
    '...........D']
far = lambda rows: [(y, x, t.replace('R', 'D')) for y, x, t in rows]              # the far wing: in shadow
S_BODY = [                                         # head, neck, body and tail in one: back dark, belly lit
    (9, 51, 'RRRRRR'),
    (10, 49, 'RRRRRRRRRR'),
    (11, 48, 'RRRRRRRRRRRR'),
    (12, 47, 'RRRRRDDDDRRRRRR'),
    (13, 47, 'RRRRRKOKRRRRRRRR'),
    (14, 46, 'RRRRRRRRRRRRRRRRRR'),
    (15, 46, 'RRRRRRRRRRRRRRRKRR'),
    (16, 46, 'RRRRRRRRRRRRRRRRRR'),
    (17, 46, 'RRRRRRRRRRRRRRRRRR'),
    (18, 45, 'RRRRRRKKKKKKKKKKKKK'),
    (19, 45, 'DRRRRRDYDDDDYDDDDD'),
    (20, 44, 'RDRRRRRDDDDDDDDDDD'),
    (21, 43, 'RDRRRRRRDDDDDDDD'),
    (22, 43, 'DDRRRRRRRDDDD'),
    (23, 42, 'RDRRRRRRRRRR'),
    (24, 41, 'RDRRRRRROOYR'),
    (25, 40, 'RDDRRRRRROOYR'),
    (26, 39, 'RDDRRRRRROOYR'),
    (27, 36, 'RRRDDRRRRRRROOYR'),
    (28, 34, 'RRDDDDRRRRRRRROOYR'),
    (29, 31, 'RRRDDDDDRRRRRRRRROOYR'),
    (30, 28, 'RRRDDDDDRRRRRRRRRRRROOYR'),
    (31, 26, 'RRDDDDDDRRRRRRRRRRRRRROOYR'),
    (32, 24, 'RRDDDDDRRRRRRRRRRRRRRRRROOYO'),
    (33, 22, 'RRDDDDRRRRRRRRRRRRRRRRRRRROOYO'),
    (34, 20, 'RRDDDDRRRRRRRRRRRRRRRRRRRRRROOYY'),
    (35, 18, 'RRDDDDRRRRRRRRRRRRRRRRRRRRRRRROOYR'),
    (36, 16, 'RRDDDDRRRRRRRRRRRRRRRRRRRRRRRRROOYY'),
    (37, 15, 'RDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRROOR'),
    (38, 13, 'RRDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRROOY'),
    (39, 6, 'R....RRDDRRRRRRRRRRRROORRRRRRRRRRRRRRRRROOYR'),
    (40, 4, 'RRRR.RRDDRRRRRRRRROOOOOOOOORRRRRRRRRRRRROOOYR'),
    (41, 4, 'RRRRRDDRRRRROOOOOORRRRRYYOOOOOOOOOOOOOOOOOYR'),
    (42, 4, 'RRRRRRRRRRRORRRRRR.....RRYYOOOOOOOOOOOOOYYR'),
    (43, 5, 'RRRRRRRRROR.............RRYYYYYYYYYYYYYRR'),
    (44, 6, 'RRRRRRRRR................RRRRRRRRRRRRR'),
    (45, 9, 'RR')]
S_THIGH = [(38, 31, 'RRRRRR'), (39, 30, 'RRRRRRRR'), (40, 29, 'DRRRRRRRRR'), (41, 29, 'DRRRRRRRRR'), (42, 29, 'DDRRRRRRR')]   # joined to the body: no line over it
S_SHIN = [(43, 30, 'DDRRRRRR'), (44, 30, 'DDRRRR'), (45, 29, 'DRRRRR'), (46, 27, 'DRRRRRR'), (47, 26, 'RRRRRRR')]              # its foot trailing
S_CLAWS = [(48, 25, 'YY.YY.Y'), (49, 24, 'Y..Y')]
S_HORN = [(9, 48, 'OOO'), (8, 47, 'OOO'), (7, 46, 'YYY'), (6, 45, 'YYY'), (5, 44, 'YYY'), (4, 44, 'YY'), (3, 44, 'Y')]   # up and back
S_FAR_HORN = [(8, 52, 'OO'), (7, 51, 'OOO'), (6, 50, 'OO'), (5, 49, 'OO'), (4, 49, 'O')]
tongue = lambda x, y: [(y - 2, x, 'Y'), (y - 1, x, 'YO'), (y, x, 'OO')]                        # a flame, blown back
S_FLAME = tongue(43, 18) + tongue(41, 22) + tongue(34, 27) + tongue(28, 29)                   # off its neck and back,
S_TAIL_FLAME = tongue(20, 33) + tongue(14, 36) + tongue(9, 39)                                # and its tail
SIDE = [(far(at(3, 14, S_WING)), 'solid'), (S_FAR_HORN, 'raw'), (S_FLAME, 'raw'), (S_TAIL_FLAME, 'raw'), (S_BODY, 'solid'),
        (S_THIGH, 'raw'), (S_SHIN, 'solid'), (S_CLAWS, 'raw'), (at(5, 8, S_WING), 'solid'), (S_HORN, 'raw')]

# ---- the back ----------------------------------------------------------------------------------------
B_HEAD = at(7, 28, [                               # the back of its head and neck
    '....RRRRRRRR....',
    '..RRRRRRRRRRRR..',
    '.RRRRRRRRRRRRRR.',
    'RRRRRRRRRRRRRRRR',
    'RRRRRRRRRRRRRRRR',
    'RRRRRRRRRRRRRRRR',
    'RRRRRRRRRRRRRRRR',
    '.RRRRRRRRRRRRRR.',
    '..DRRRRRRRRRRD..',
    '...DDRRRRRRDD...',
    '....DRRRRRRD....',
    '....DRRRRRRD....',
    '....DRRRRRRD....',
    '...DRRRRRRRRD...',
    '...DRRRRRRRRD...',
    '...DRRRRRRRRD...'])
plain = lambda rows: [(y, x, t.replace('O', 'R').replace('Y', 'R')) for y, x, t in rows]       # no glow from behind
B_TORSO = plain(F_TORSO)
B_FOOT = [r for r in F_FOOT if r[0] < 45]                                                      # its claws point away
B_TAIL = mirror(F_TAIL)                                                                        # round to our left
B_FLAME = [(12, 35, 'Y'), (13, 35, 'YY'), (14, 35, 'YY'), (15, 35, 'OY')] + [(y, 35, 'OO') for y in range(16, 40)]     + [(17, 34, 'Y'), (18, 34, 'Y'), (24, 37, 'Y'), (25, 37, 'Y'), (32, 34, 'Y'), (33, 34, 'Y')]    # its spine alight, from the back of the head down to the tail
BACK = [(B_HEAD, 'solid'), (mirror(F_HORN), 'raw'), (F_HORN, 'raw'), (B_TAIL, 'solid'), (B_TORSO, 'raw'),
        (B_FOOT, 'raw'), (mirror(B_FOOT), 'raw'), (B_FLAME, 'raw'), (WING, 'solid'), (mirror(WING), 'solid')]


def view(parts):
    """The frame, and the colour pixels on it that carry no black edge (thin parts, tips, raw parts)."""
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet's direction it replaces, the old drawn box
VIEWS = [('front', '07_alber_front_frame0_draft', FRONT, 0, '39 x 33'),
         ('side', '07_alber_side_frame0_draft', SIDE, 2, '36 x 32'),
         ('back', '07_alber_back_frame0_draft', BACK, 4, '39 x 33')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    old = Image.open(ROOT / 'assets/enemies/07_alber.png').convert('RGBA')
    panels, shapes = [], []
    for name, file, parts, d, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box, cap=70): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)
        if not look: ff.style_check(im, scratch, file, tier='big')
        panels += [(name.upper(), im), ('was', old.crop((d * 3 * OLD_W, 0, d * 3 * OLD_W + OLD_W, OLD_H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '07_look.png' if look else HERE / '07_review.png')
    if look:
        big = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
        for i, (name, file, parts, d, box) in enumerate(VIEWS): big.alpha_composite(ff.image(view(parts)[0], PAL, W, H), (i * W, 0))
        big.resize((big.width * 9, big.height * 9), Image.Resampling.NEAREST).save(scratch / '07_big.png')
