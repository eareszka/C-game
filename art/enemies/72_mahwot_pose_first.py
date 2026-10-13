"""Enemy 72 Mahwot, first frames: one side view, two poses. Both are the user's drawings.

The mahwot of the Meuse as a small swimming Godzilla. The user: "left and right swimming. and firing from
its mouth idle" -- both from the side only (facing right; the left is its mirror). I drew a first frame of
each; they edited both in Aseprite (2026-10-12), and those are held here pixel for pixel:

    swim  stretched out in its S, jaws shut, a black eye
    fire  "looking forward with their body turned and their eyes lit up from shooting laser": reared, the
          head turned to face us, eyes and plates lit blue, the mouth open below

Then: "the face when turned during shooting needs updating. the head area to fix the enemys design more".
So the shooting frame's HEAD is typed here (F_HEAD) over their frame; its body is still their pixels, and
the head still joins the neck with no line, as they drew it. Nothing else redraws them. Writes only a review; the drafts are theirs and are not drawn over, and the
game's assets are not touched. (My own typed first drafts: scratch 72_pose_first_my_typed_parts.py.)

    python art/enemies/72_mahwot_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/72_mahwot_pose_first.py [SCRATCH]  # check against the drafts; write the review
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

W, H = 98, 65                 # the old sheets' frame
OLD_FRAMES = 5
PAL = {'K': '000000',
       'D': '142e1f', 'M': '235436', 'L': '2c6c44',   # green: shade, body, light
       'B': 'b29e5c',                                 # belly
       'P': 'c6ccda',                                 # bone: the plates' tips
       'R': '792727',                                 # inside its mouth
       'G': '84a7e9'}                                 # the glow of its breath: eyes and plates

S_MOUTH = (93, 27)            # swimming: the tip of its snout
F_MOUTH = (74, 29)            # firing: the glow in its throat, where the breath leaves (the middle is 75.0, 30.0)
S_USER = [
    (14, 42, 'K'),
    (15, 41, 'KPK'),
    (16, 33, 'K.......KPPK'),
    (17, 32, 'KPKK.....KPPPK......K.....K'),
    (18, 32, 'KPPPK.....KPPPK....KPK...KPKK'),
    (19, 33, 'KPPPK...KPPPPPK...KPPKK.KPPPK..K'),
    (20, 33, 'KPPPPK...KPPPPK....KPPPK.KPPPKKPKK.......KKKKK'),
    (21, 32, 'KPPPPPK...KLLPPPK..KPPPPK.KLPPPKPPPK....KKLLLLLKK'),
    (22, 33, 'KLLPPPK.KLLLLLPK...KLPPPKLKKKKKKKPPK.KKLLLLDDDLLKKKK'),
    (23, 27, 'K......KLLLPK..KLLLLLK..KLLLLPKKLLLLLLLKKKKMLLLLDKKKLLLLLLKKKK'),
    (24, 26, 'KPKK...KLLLKKKKKKMLLLLK...KLLKKLLLLLLLLLLLMMLLLLLDKKKLLLLLLLLLLKKK'),
    (25, 26, 'KPPPK...KKKLLLLLLKKKLLK...KKKLLLLMMMMMMMLMMMMLLLLLLLLLLLLLLLLLLLKMK'),
    (26, 27, 'KPPPKKKLLLLLLLLLLLLKKKKKKLLLLLMMMMMMMMMMMMMMMMLLLLLLLLLLLLLLLLLLLMK'),
    (27, 5, 'LKK.............K.....KLPKKLLLLLMMMMMMLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLLLLLLLMK'),
    (28, 5, 'KMMKK..K.......KPKK..KLKKLLLLMMMMMMMMMMMMLLLLLLMMMMMMMMMMMMMMMMMMMMMMKKKKKKKKKKKKKKKKKKKK'),
    (29, 6, 'KKMMKKPK......KPPPK.KKLLLLMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMBBBBBBBBBBBBBBBBBK'),
    (30, 8, 'KKMMKKK..K...KPPKKLLLLMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDDKMMMMMMBBBBBBBBBBBBBBKK'),
    (31, 10, 'KMMMKKKPK..KKKLLMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDDBBBKKMMMMMBBBBBBBBBKKKK'),
    (32, 11, 'KKMMMMKKKKLLLMMMMDDDDMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDBBBBBBBKKKKKKKKKKKKKK'),
    (33, 13, 'KMMMMMMMMMMMMMMBBBBDMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDBBBBBBKKB'),
    (34, 14, 'KKMMMMMBBBBBBBBBBDMMMMMKDDDMMMMMMMMMMMMMMMMMMMMMDBBBBKKK'),
    (35, 16, 'KKMMMBBBBBBBBBDMMMMMKBBBBDDDDMMMMMMMMDDDMMMMMDBBBKK'),
    (36, 18, 'KKKKKKKKKKKKMMMMMKBBBBBBBBBDDDDDDDDBBMMMMMKBBKK'),
    (37, 28, 'KMMMMMKKBBBBBBBBBBBBBBBBBBKMMMMKKKKDK'),
    (38, 27, 'KMMMMDKDDKKKKKBBBBBBBBBBBBKMMMMMKDDDK'),
    (39, 26, 'KMMMMDKDDDK....KKKKBBBBBBBKMMMMDKDDDK'),
    (40, 24, 'KKMMMMMKDDKK.........KKKKKKKMMMMDKDDDK'),
    (41, 23, 'KMKMMMKKKKK.DD............KKMMMMMKDDKK'),
    (42, 23, 'MK.KKK.MM................KMKMMMKKKKK.DD'),
    (43, 48, 'MK.KKK.MM'),
]
F_USER = [
    (14, 71, 'KKKK'),
    (15, 69, 'KKLLLLK'),
    (16, 67, 'KKLLLLLLMKK'),
    (17, 66, 'KLLLLLLMMMMKK'),
    (18, 58, 'K......KLLLLLMMMMMMMMKK'),
    (19, 57, 'KGKK...KLLLLMMMDDMMDDDLK'),
    (20, 57, 'KGGGK.KKLLLMMDGGGMMGGGDK'),
    (21, 52, 'K.....KKKKKLLLLMMMDGGGMMGGGDK'),
    (22, 51, 'KGKK..KKLLLLLLLMMMMMMMMMMMMMMK'),
    (23, 51, 'KGGGKKLLLLLLLMMMMMMMMMMKKMMMMK'),
    (24, 52, 'KGGKLLLMMMMMMMMMMMMMMKRRKMMMK'),
    (25, 52, 'KLKLLMMMMMMMMMMMMMMMKRRRRKMMK'),
    (26, 51, 'KLKLLMMMMMMMMMMMMMMMDKRRRRRKMK'),
    (27, 52, 'KLLMMMMMMMMMMMMMMDDKRRRRRRRKK'),
    (28, 46, 'K....KLLMMMMMMMMMMMMMMDBKBRRRRRRRKK'),
    (29, 45, 'KGK..KLLMMMMMMMMMMMMMMDBBKBRRRRRRRBK'),
    (30, 45, 'KGGKKKLMMMMMMMMMMMMMDDBBBKBRRRRRRRBK'),
    (31, 46, 'KGGKLMMMMMMMMMMMMMDBBBBKBKBRRRRRRBK'),
    (32, 38, 'K......KGGKLMMMMMMMMMMMMDDBBBBK..KBRRRRRBKK'),
    (33, 37, 'KGK......KLKLMMMMMMMMMMMDBBBBBK....KBRRRBK'),
    (34, 37, 'KGGK....KLKLMMMMMMMMMMMDBBBBKK.....KBRRRBK'),
    (35, 37, 'KGGGK....KKMMMMMMMMMMMDBBBBK........KBRBK'),
    (36, 38, 'KGGGK...KLMMMMMMMMMMDBBBKK.........KBRBK'),
    (37, 30, 'K......KGGGGGKLKLMMMMMMMMMDDKBK............KBBK'),
    (38, 29, 'KGKK.....KGGGGKKLMMMMMMMMMDDDDK..............KBK'),
    (39, 29, 'KGGGK....KLLGLKLLMMMMMMMMMKDDDK...............K'),
    (40, 30, 'KGGGK..KLLLLKLMMMMMMMMMMMKDDDDK'),
    (41, 30, 'KGGGGK..KLLKLLMMMMMMMMMMMMKDDDDK'),
    (42, 24, 'K....KGGGGGK..KMKLMMMMMMMMMMMMMMKKDDDDK'),
    (43, 23, 'KGKK...KLLGGGK.LKLLMMMMMMMMDBKMMMMKKDDDDK'),
    (44, 23, 'KGGGK...KLLLGK.KLMMMMMMMMMDBBBKMMMMKKDDDDK'),
    (45, 19, 'K....KGGGK.KLLLLKKKLLMMMMMMMMDBBBK.KMMMDKKDDDK'),
    (46, 18, 'KGKK..KLGGGK.KMLKLLLMMMMMMMMMDBBBK...KMMMKKDDDDKK'),
    (47, 14, 'K...KGGGKKLLLLKKKKKKLLLLMMMMMMMMDBBBK....KMMMMKKDDDKDK'),
    (48, 9, 'K...KGK...KGKKKKKKKLLLLLLMMMMMMMMMMDDBBBK....KMKMMMKMKKK.KD'),
    (49, 8, 'KGK.KKKKKKKKKLLLLLLLMMMMMMMMMMMMMMDDBBBBK.....MK.KKK.KM'),
    (50, 5, 'LKKKKKKLLLLLLLLLMMMMMMMMMMMMMMMMMMMMDBBBBBK'),
    (51, 5, 'KMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMBBBBBBBK'),
    (52, 6, 'KKMMMMBBBBBBBBBBBBBBBBBBBKMMMMMMBBBBBBKK'),
    (53, 8, 'KKKKBBBBBBBBBBBBBBBBBBKMMMMMMKBBBBKK'),
    (54, 12, 'KKKKKKKKKKKKKKKKKKKMMMMDKKKKKK'),
    (55, 29, 'KMMMMMMKDDKDK'),
    (56, 28, 'KMKMMMKMKKK.KD'),
    (57, 28, 'MK.KKK.KM'),
]

# ---- the shooting frame's head, facing us: the swim head's heavy brow and blunt snout seen from the front ----
HEAD_AREA = lambda x, y: (x >= 66 and y <= 21) or (x >= 70 and 22 <= y <= 41)     # what of F_USER it replaces
F_HEAD = [
    (14, 70, 'KKKKKKKKKK'),                                          # a flat, heavy skull
    (15, 68, 'KKLLLLLLLLLLKK'),
    (16, 67, 'KLLLLLLLLLLLLLLK'),
    (17, 66, 'KLDDDLLLLLLLLDDDLK'),                                  # the brows, high at the sides
    (18, 66, 'LLMMDDDDLLDDDDMMLK'),                                  # and drawn down to the middle
    (19, 66, 'LMMMGGDDLLDDGGMMMK'),                                  # its eyes, lit, cut by the brow
    (20, 66, 'LMMDGPGDLLDGPGDMMK'),
    (21, 66, 'LMMMDDDMLLMDDDMMMK'),
    (22, 70, 'DMMLLLLMMMMMK'),                                       # the snout coming at us, a lit ridge down it;
    (23, 70, 'DMMLLLLMMMMK'),                                        # shade, not a line, where it meets the neck
    (24, 70, 'DMMKLLKMMMK'),                                         # nostrils
    (25, 70, 'DMMMMMMMMMK'),
    (26, 70, 'KKKKKKKKKKK'),                                         # the upper jaw's edge
    (27, 70, 'KPRPRRPRPK'),                                          # its teeth
    (28, 70, 'KRRRRRRRRK'),
    (29, 70, 'KRRRGGRRRK'),                                          # the glow in its throat
    (30, 70, 'KBRRGGRRBK'),                                          # the lower jaw, dropped
    (31, 70, 'KBRRRRRRBK'),
    (32, 70, 'KBPRRRRPBK'),
    (33, 71, 'KBPRRPBK'),
    (34, 71, 'KBBRRBBK'),
    (35, 72, 'KBBBBK'),
    (36, 73, 'KBBK'),
    (37, 74, 'KK'),
]
_fire = {q: c for q, c in ff.grid(F_USER, PAL).items() if not HEAD_AREA(*q)}
_fire.update(ff.grid(F_HEAD, PAL))
SWIM, FIRE = [(S_USER, 'raw')], [([(y, x, c) for (x, y), c in _fire.items()], 'raw')]


def view(parts=SWIM):
    return ff.layered(parts, PAL, W, H)


# name, draft file, the drawing, the old sheet, the old drawn box
VIEWS = [('swim', '72_mahwot_swim_frame0_draft', SWIM, '72_mahwot.png', '89 x 31 (columns 5-93, rows 13-43)'),
         ('fire', '72_mahwot_fire_frame0_draft', FIRE, '72_mahwot_roar.png', '87 x 41 (columns 4-90, rows 14-54)')]

if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if sys.argv[1:] else HERE); scratch.mkdir(parents=True, exist_ok=True)
    g = view(SWIM)[0]
    assert S_MOUTH in g and (S_MOUTH[0] + 1, S_MOUTH[1]) not in g, 'the snout does not end where S_MOUTH says'
    g = view(FIRE)[0]
    assert all(g.get((F_MOUTH[0] + dx, F_MOUTH[1] + dy)) == 'G' for dx in (0, 1) for dy in (0, 1)), 'the throat glow is not where F_MOUTH says'
    print(f'mouth: swimming, its snout ends at {S_MOUTH}; firing, the glow in its throat is the 2 x 2 at {F_MOUTH}', flush=True)
    panels, shapes = [], []
    for name, file, parts, old, box in VIEWS:
        g, thin = view(parts)
        print(name, flush=True)
        for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old=box, cap=70): print(' ', line, flush=True)
        im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / file)      # asserts the draft is still this drawing
        if not look: ff.style_check(im, scratch, file, tier='big')
        was = Image.open(ROOT / 'assets/enemies' / old).convert('RGBA')
        panels += [(name.upper(), im), ('was', was.crop((2 * OLD_FRAMES * W, 0, 2 * OLD_FRAMES * W + W, H)))]
        shapes.append((name + ' shape', ff.silhouette(im)))
    ff.review(panels + [('PLAYER', ff.player())] + shapes, scratch / '72_look.png' if look else HERE / '72_review.png', scale=4)
