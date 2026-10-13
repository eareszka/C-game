"""Enemy 07 Alber, its one sheet: flying. Six frames a view, front, side and back.

The first frame of each view is art/enemies/07_alber_pose_first.py (the front's head, body and feet
are the user's own pixels). From there, a wingbeat: the wings come down from raised, through level,
to lowered, and back; the body rises as they push down and sinks as they lift; the far end of the
tail swings, and the feet sway under it.

Drawn through the Aseprite pixel plugin into one draft, a tag per view. The game's assets are not
touched.

    python art/enemies/07_alber_design.py look DIR   # the GIF only
    python art/enemies/07_alber_design.py            # check, draw the draft, write the GIF
"""
from pathlib import Path
import importlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
A = importlib.import_module('07_alber_pose_first')
W, H, PAL, at, mirror, far = A.W, A.H, A.PAL, A.at, A.mirror, A.far

N, MS = 6, 120                                     # one wingbeat, 0.72 s
WINGS = (0, 1, 2, 2, 1, 0)                         # raised, level, lowered, held, level, raised
RISE = (3, 2, 1, 0, 1, 2)                          # rows below its highest: up on the downstroke, a frame behind the wings
SWING = (0, 1, 2, 1, 0, -1)                        # the tail's far end, px down
SWAY = (0, 1, 1, 0, -1, -1)                        # the feet, px sideways

# ---- the front's wing (ours left), level and lowered; raised is the first frame's ---------------------
WING_LEVEL = at(16, 6, [                           # arm out to the side, the skin hanging under it
    '.....DD',
    '....DDDDDDD',
    '...RDDDDDDDDDD',
    '...RDDRDDDDDDDDDDD',
    '..RDRDRDRRRDDDDDDDDDDD',
    '..RDRDRRDRRRRRDDDDDDDDDD',
    '.RDRRDRRDRRRRRRRRRDDDDDD',
    '.RDRRDRRRDRRRRRRRRRRRRDD',
    'DDRRRDRRRDRRRRRRRRRRRRRR',
    '.RRRRDRRRRDRRRRRRRRRRRRR',
    '..RRRRDRRRDRRRRRRRRRRRRR',
    '...RRRDRRRRDRRRRRRRRRRRR',
    '...RRRDRRRRDRRRRRRRRRRRR',
    '....RRDRRRRRDRRRRRRRRRRR',
    '....RRDRRR..RDRRRRR....R',
    '....RRDRR....RDRRR',
    '.....RDR......DRR',
    '.....RDR......RDR',
    '.....RD........D',
    '......D........D'])
WING_LOW = at(21, 6, [                             # arm down and out, the fingers closing under it
    '.......................D',
    '.....................DDD',
    '...................DDDDD',
    '.................DDDDDDR',
    '................DDDDDRRR',
    '..............DDDDDRRRRR',
    '............DDDDDRRRRRRR',
    '..........DDDDDDRRRRRRRR',
    '........DDDDDDRRRRRRRRRR',
    '.......DDDDDRRRRRRRRRRRR',
    '......DDDDDRRRRRRRRRRRRR',
    '......RDDRRDRRRRRRRRRRRR',
    '......RDDRRRDRRRRRRRRRRR',
    '.....RDRDRRRRDRRRRRRRR',
    '.....RDRRDRRRRDRRRRRR',
    '.....RDRRDRRRRRDRRRR',
    '.....RD..RDRRR..DRRR',
    '....RD....DRR....DR',
    '....RD....RDR.....D',
    '....D......D......D',
    '...........D',
    '...........D'])
F_WINGS = (A.WING, WING_LEVEL, WING_LOW)

# ---- the side's near wing: level; lowered is the raised one turned over about the shoulder ------------
S_LEVEL = at(19, 8, [                              # swept back, seen nearly edge on
    '............DDDDDD',
    '......RRRRRRDDDDDDDD',
    'DDDDDDDDDDDDRRDRDDDDDD',
    '.RRDDDRRRRRRDRRRDRDDDDDDD',
    '...RRRRRRRDRRRRRDRRRDDDDDDD',
    '.....RRRDRRRRRRDRRRRRRDDDDDDDD',
    '......D...RRRRRDRRRRRRRRRDDDDDDD',
    '......D.....RRDRRRRRRRRRRRRDDDDDD',
    '.............D.....RRRRRRRRRRRDDD',
    '.............D............RRRRDDD'])
S_WINGS = (at(5, 8, A.S_WING), S_LEVEL, at(25, 8, A.S_WING[::-1]))

move = lambda rows, dx=0, dy=0: [(y + dy, x + dx, t) for y, x, t in rows]


def swing(rows, down):
    """A tail, each column of it moved down by down(x): the far end swings, the root stays."""
    return [(y + down(x), x, c) for (x, y), c in ff.grid(rows, PAL).items()]


def front(f, back=False):
    wing, dy = F_WINGS[WINGS[f]], RISE[f]
    tail = swing(A.B_TAIL, lambda x: round(SWING[f] * max(0, 31 - x) / 18)) if back else \
        swing(A.F_TAIL, lambda x: round(SWING[f] * max(0, x - 40) / 18))
    wings = [(wing, 'solid'), (mirror(wing), 'solid')]
    foot = A.B_FOOT if back else A.F_FOOT
    feet = [(move(foot, SWAY[f]), 'raw'), (move(mirror(foot), SWAY[f]), 'raw')]
    if back:
        parts = [(A.B_HEAD, 'solid'), (mirror(A.F_HORN), 'raw'), (A.F_HORN, 'raw'), (tail, 'solid'), (A.B_TORSO, 'raw')] + feet \
            + [(A.B_FLAME, 'raw')] + wings
    else:
        parts = [(tail, 'solid')] + wings + [(A.F_TORSO, 'raw'), (A.F_HEAD, 'raw')] + feet
    return ff.layered([(move(rows, 0, dy), kind) for rows, kind in parts], PAL, W, H)


def side(f):
    wing, dy = S_WINGS[WINGS[f]], RISE[f]
    down = lambda x: round(SWING[f] * max(0, 26 - x) / 22)
    parts = [(far(move(wing, 6, 2 if WINGS[f] == 2 else -2)), 'solid'), (A.S_FAR_HORN, 'raw'),   # the far wing: past the near one's leading edge
             (A.S_FLAME, 'raw'), (swing(A.S_TAIL_FLAME, down), 'raw'),
             (swing(A.S_BODY, down), 'solid'), (A.S_THIGH, 'raw'), (move(A.S_SHIN, SWAY[f]), 'solid'), (move(A.S_CLAWS, SWAY[f]), 'raw'),
             (wing, 'solid'), (A.S_HORN, 'raw')]
    return ff.layered([(move(rows, 0, dy), kind) for rows, kind in parts], PAL, W, H)


VIEWS = {'D': front, 'R': side, 'U': lambda f: front(f, back=True)}    # front, side (left is its mirror), back


def build():
    sheet = {v: [make(f) for f in range(N)] for v, make in VIEWS.items()}
    for v, (first, lift) in {'D': (A.FRONT, RISE[0]), 'R': (A.SIDE, RISE[0]), 'U': (A.BACK, RISE[0])}.items():
        g = A.view(first)[0]
        assert sheet[v][0][0] == {(x, y + lift): c for (x, y), c in g.items()}, f'{v}: frame 1 is not the first-frame drawing'
    return sheet


def panel(sheet, i):
    im = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
    for k, v in enumerate(VIEWS): im.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (k * W, 0))
    return im


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    sheet = build()
    print(f'fly: {N} frames x {MS} ms = {N * MS / 1000:.2f} s, 3 drawn views (left = side mirrored); frame 1 of each is the first-frame drawing', flush=True)
    for v in VIEWS:
        boxes = []
        for g, thin in sheet[v]:
            ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, cap=70)
            xs, ys = [x for x, y in g], [y for x, y in g]
            boxes.append(f'{max(xs) - min(xs) + 1}x{max(ys) - min(ys) + 1}')
        print(f'  {v}: palette, colour count, outline and height hold on all {N} frames; drawn ' + ' '.join(boxes), flush=True)
    if not look:
        base = HERE / '07_alber_fly_draft'
        frames = [g for v in VIEWS for g, thin in sheet[v]]
        if base.with_suffix('.aseprite').exists():
            assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
            print(f'{base.name}: already drawn, unchanged', flush=True)
        else:
            ff.draw_frames(frames, PAL, W, H, base, MS, {v: (k * N + 1, k * N + N) for k, v in enumerate(VIEWS)})
    ff.gif([panel(sheet, i) for i in range(N)], out / '07_fly.gif', MS, PAL)
    if look:
        strip = Image.new('RGBA', (W * N, H * len(VIEWS)), (0, 0, 0, 255))
        for k, v in enumerate(VIEWS):
            for i in range(N): strip.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (i * W, k * H))
        strip.resize((strip.width * 4, strip.height * 4), Image.Resampling.NEAREST).save(out / '07_fly_strip.png')
