"""Enemy 39 Ajaju, its idle: breathing, its tongues flicking out, its tail uncurling and flipping.

Ten frames a view (front, side, back), 130 ms each: 1.3 s, the length of the old sheet's loop, so the
fight's two volleys keep their beat. The first frame of each view is art/enemies/39_ajaju_pose_first.py.

    breath   head and body a pixel up on frames 2-4; the stilts stay planted
    tongues  fan out on 2-3-4 (widest on 3), and a smaller flick on 8
    tail     opens on 5, flipped out on 6-7, back through 8 to its curl

Drawn through the Aseprite pixel plugin into one draft, a tag per view. The game's assets are not
touched.

    python art/enemies/39_ajaju_design.py look DIR   # the GIF only
    python art/enemies/39_ajaju_design.py            # check, draw the draft, write the GIF
"""
from pathlib import Path
import importlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
A = importlib.import_module('39_ajaju_pose_first')
W, H, PAL, mirror = A.W, A.H, A.PAL, A.mirror

N, MS = 10, 130
LIFT = (0, 0, 1, 1, 1, 0, 0, 0, 0, 0)              # the breath: rows up
TONGUES = (0, 0, 1, 2, 1, 0, 0, 0, 1, 0)           # hanging, flicking out, fanned
TAIL = (0, 0, 0, 0, 0, 1, 2, 2, 1, 0)              # curled, opening, flipped out
FAN_FRAME = 3                                      # the tongues at their widest

# ---- the front's tongues (ours left; the right is the mirror), flicking out and fanned ----------------
F_MID = (A.TONGUE_MID,
         [(17, 31, 'r')] + [(y, 31, 'R') for y in range(18, 26)] + [(26, 30, 'RRR'), (27, 29, 'R...R')],
         [(17, 31, 'r')] + [(y, 31, 'R') for y in range(18, 24)] + [(24, 30, 'RRR'), (25, 29, 'R...R')])
F_IN = (A.TONGUE_IN,
        [(17, 28, 'rr'), (18, 27, 'rR'), (19, 26, 'R'), (20, 25, 'R'), (21, 24, 'R'), (22, 23, 'R'), (23, 22, 'R'), (24, 21, 'R.R')],
        [(17, 28, 'rr'), (18, 26, 'RR'), (19, 24, 'RR'), (20, 22, 'RR'), (21, 20, 'RR'), (22, 18, 'RR'), (21, 17, 'R'), (23, 17, 'R')])
F_OUT = (A.TONGUE_OUT,
         [(17, 26, 'r'), (18, 24, 'RR'), (19, 22, 'RR'), (20, 20, 'RR'), (19, 19, 'R'), (21, 19, 'R')],
         [(17, 26, 'r'), (18, 18, 'RRRRRRRR'), (17, 17, 'R'), (16, 16, 'R'), (15, 16, 'R'), (14, 15, 'R.R')])   # out past the eye, curling up
F_TAIL = (A.TAIL,
          [(25, 37, 'MMMMMMMM'), (24, 45, 'M'), (23, 46, 'M'), (22, 46, 'M'), (21, 45, 'M'), (20, 43, 'MM'), (21, 42, 'M')],
          [(25, 37, 'MMMMMM'), (24, 43, 'MM'), (23, 45, 'M'), (22, 46, 'M'), (21, 47, 'M'), (20, 47, 'M'), (19, 46, 'M')])

# ---- the side's ---------------------------------------------------------------------------------------
S_FORE = (A.S_TONGUE_FORE,
          [(17, 49, 'r'), (18, 50, 'R'), (19, 50, 'R'), (20, 51, 'R'), (21, 51, 'R'), (22, 52, 'R'), (23, 52, 'R'), (24, 53, 'R'), (25, 52, 'R.R')],
          [(17, 49, 'r'), (18, 50, 'RR'), (19, 52, 'RRRR'), (18, 56, 'R'), (17, 57, 'R'), (16, 57, 'R'), (15, 56, 'R.R')])   # lashed out ahead, curling up
S_MID = (A.S_TONGUE_MID,
         [(17, 46, 'rr'), (18, 46, 'rR'), (19, 47, 'R'), (20, 47, 'R'), (21, 48, 'R'), (22, 48, 'R'), (23, 48, 'R'), (24, 47, 'R.R')],
         [(17, 46, 'rr'), (18, 47, 'R'), (19, 48, 'R'), (20, 49, 'R'), (21, 50, 'R'), (22, 51, 'R'), (23, 52, 'R'), (24, 53, 'R'), (25, 52, 'R.R')])
S_HIND = (A.S_TONGUE_HIND, A.S_TONGUE_HIND,
          [(17, 44, 'r'), (18, 44, 'R'), (19, 44, 'R'), (20, 45, 'R'), (21, 45, 'R'), (22, 44, 'R.R')])
S_TAIL = (A.S_TAIL,
          [(18, 7, 'MMM'), (19, 5, 'MMMMM'), (20, 3, 'MMM'), (21, 3, 'M'), (22, 3, 'M'), (23, 3, 'M'), (24, 4, 'M'), (25, 5, 'MMM'), (24, 8, 'M'),
           (23, 8, 'M'), (22, 7, 'M')],
          [(18, 7, 'MMM'), (19, 5, 'MMMM'), (20, 4, 'MM'), (21, 3, 'MM'), (22, 2, 'MM'), (23, 2, 'M'), (24, 2, 'M'), (25, 3, 'M'), (26, 4, 'M'), (25, 5, 'M')])

up = lambda rows, n: [(y - n, x, t) for y, x, t in rows]


def front(f):
    k, n = TONGUES[f], LIFT[f]
    body = [(F_TAIL[TAIL[f]], 'raw'), (A.BODY, 'solid'), (A.CASQUE, 'solid'), (A.HEAD, 'solid'), (A.EYE, 'solid'), (mirror(A.EYE), 'solid'),
            (F_OUT[k], 'raw'), (mirror(F_OUT[k]), 'raw'), (F_IN[k], 'raw'), (mirror(F_IN[k]), 'raw'), (F_MID[k], 'raw')]
    parts = [(up(rows, n), kind) for rows, kind in body]
    return ff.layered(parts[:1] + [(A.LEG, 'solid'), (mirror(A.LEG), 'solid')] + parts[1:], PAL, W, H)


def side(f):
    k, n = TONGUES[f], LIFT[f]
    body = [(S_TAIL[TAIL[f]], 'raw'), (A.S_BODY, 'solid'), (A.S_HEAD, 'solid'), (A.S_EYE, 'solid'),
            (S_HIND[k], 'raw'), (S_MID[k], 'raw'), (S_FORE[k], 'raw')]
    parts = [(up(rows, n), kind) for rows, kind in body]
    return ff.layered([(A.S_FAR_LEGS, 'solid')] + parts[:1] + [(A.S_HIND_LEG, 'solid'), (A.S_FORE_LEG, 'solid')] + parts[1:], PAL, W, H)


def back(f):
    n = LIFT[f]
    body = [(A.B_BODY, 'solid'), (A.CASQUE, 'solid'), (A.B_HEAD, 'solid'), (A.B_EYE, 'solid'), (mirror(A.B_EYE), 'solid'),
            (A.B_SPINE, 'raw'), (mirror(F_TAIL[TAIL[f]]), 'raw')]
    return ff.layered([(A.LEG, 'solid'), (mirror(A.LEG), 'solid')] + [(up(rows, n), kind) for rows, kind in body], PAL, W, H)


VIEWS = {'D': front, 'R': side, 'U': back}         # front, side (left is its mirror), back
FIRST = {'D': A.FRONT, 'R': A.SIDE, 'U': A.BACK}


def build():
    sheet = {v: [make(f) for f in range(N)] for v, make in VIEWS.items()}
    for v in VIEWS: assert sheet[v][0][0] == A.view(FIRST[v])[0], f'{v}: frame 1 is not the first-frame drawing'
    return sheet


def mouth(v, f):
    """Where the fight's shots leave on frame f: the middle of the mouth line (front, back), its front end (side)."""
    x, y = A.MOUTH if v != 'R' else A.S_MOUTH
    return (x + (0.5 if v != 'R' else 1.0), y + 0.5 - LIFT[f])


def panel(sheet, i):
    im = Image.new('RGBA', (W * len(VIEWS), H), (0, 0, 0, 255))
    for k, v in enumerate(VIEWS): im.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (k * W, 0))
    return im


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    sheet = build()
    print(f'idle: {N} frames x {MS} ms = {N * MS / 1000:.2f} s, 3 drawn views (left = side mirrored); frame 1 of each is the first-frame drawing', flush=True)
    for v in VIEWS:
        boxes = []
        for f, (g, thin) in enumerate(sheet[v]):
            ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin)
            if v != 'U':
                x, y = (A.MOUTH if v == 'D' else A.S_MOUTH)
                assert g.get((x, y - LIFT[f])) == 'K', f'{v} frame {f}: the mouth is not where mouth() says'
            xs, ys = [x for x, y in g], [y for x, y in g]
            boxes.append(f'{max(xs) - min(xs) + 1}x{max(ys) - min(ys) + 1}')
        print(f'  {v}: palette, colour count, outline and height hold on all {N} frames; drawn ' + ' '.join(boxes), flush=True)
    if not look:
        base = HERE / '39_ajaju_idle_draft'
        frames = [g for v in VIEWS for g, thin in sheet[v]]
        if base.with_suffix('.aseprite').exists():
            assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
            print(f'{base.name}: already drawn, unchanged', flush=True)
        else:
            ff.draw_frames(frames, PAL, W, H, base, MS, {v: (k * N + 1, k * N + N) for k, v in enumerate(VIEWS)})
    ff.gif([panel(sheet, i) for i in range(N)], out / '39_idle.gif', MS, PAL)
    if look:
        strip = Image.new('RGBA', (W * N, H * len(VIEWS)), (0, 0, 0, 255))
        for k, v in enumerate(VIEWS):
            for i in range(N): strip.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (i * W, k * H))
        strip.resize((strip.width * 3, strip.height * 3), Image.Resampling.NEAREST).save(out / '39_idle_strip.png')
