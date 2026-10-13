"""Enemy 24 Zoureg, its animations: idle, wind-up and dash, each from the front, the side and behind.

The user (2026-10-12): four directions in phase 1 (the left is the side mirrored); dashing frames, since
it moves fast then; in phase 2 it keeps its one head and stays idle (the three heads are dropped).

    idle     6 frames  the approved frames moved: the neck a row longer, then a row shorter; the blade
                       glowing at the top of the breath; the tail's end dropping
    wind-up  6 frames  the head drawn back and the whole snake a tone hotter, flickering -- what shows
                       before a thrust
    dash     4 frames  uncoiled and thrown like a knife: the blade leading, the body a ribbon behind it,
                       waving one way, straight, the other way, straight

Idle and wind-up are the drafts' own pixels moved (read from the .aseprite files, so an edit there
carries through). The dash is a new pose: typed here, from the head already drawn.

    python art/enemies/24_zoureg_design.py look DIR   # PIL only: the GIFs into DIR
    python art/enemies/24_zoureg_design.py            # draw the three sheets through the plugin, write the GIFs
"""
from pathlib import Path
import importlib, sys
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
Z = importlib.import_module('24_zoureg_pose_first')   # the palette, the head, the drafts' names
ff, PAL, (W, H) = Z.ff, Z.PAL, Z.ONE
IDLE_MS, DASH_MS = 170, 70
DRAFT = {'D': '24_zoureg_frame0_draft', 'R': '24_zoureg_side_frame0_draft', 'U': '24_zoureg_back_frame0_draft'}
BARE = {'D': Z.one, 'R': Z.side, 'U': Z.back}          # ...and which of their pixels carry no edge
HOT = {'r': 'R', 'R': 'O', 'O': 'Y', 'Y': 'W'}          # a tone hotter
# Per view: is a pixel of frame 0 on the head; the tail's last pixel and where it drops to;
# the neck rows that can be doubled or dropped (each is the same as the row beside it).
HEAD = {'D': lambda p: p[1] <= 11, 'U': lambda p: p[1] <= 11, 'R': lambda p: p[0] >= 24 and p[1] <= 12}
TAIL_TIP = {'D': ((34, 21), (34, 22)), 'U': ((9, 21), (9, 22)), 'R': ((2, 21), (2, 22))}
LONGER, SHORTER = 14, {14}
DRAWN_BACK = {'D': ({14, 17, 19}, ()), 'U': ({14, 17, 19}, ()), 'R': ({16, 18}, (20, 21, 22))}   # rows out of the neck; columns out of its arch
QUIVER = {'D': ({14, 17}, ()), 'U': ({14, 17}, ()), 'R': ({16, 18}, (20, 21))}                  # ...a pixel less drawn back
ARCH = 13                                               # side view: the rows down to here hold the arch and head

# -- moving a frame's pixels: an op takes a pixel to where it goes (nowhere, one place, or two) ------------
drop_rows = lambda rows: lambda p: [] if p[1] in rows else [(p[0], p[1] + sum(r > p[1] for r in rows))]
double_row = lambda row: lambda p: [p] if p[1] > row else [(p[0], p[1] - 1)] + ([p] if p[1] == row else [])
drop_cols = lambda cols: lambda p: [p] if not cols or p[1] > ARCH or p[0] < min(cols) else [] if p[0] in cols else [(p[0] - len(cols), p[1])]
move = lambda a, b: lambda p: [b] if p == a else [p]


def moved(frame, *ops):
    g, bare = frame
    for op in ops:
        g, bare = {q: c for p, c in g.items() for q in op(p)}, {q for p in bare for q in op(p)}
    return g, bare


def hotter(frame, where=lambda p: True):
    g, bare = frame
    return {p: HOT.get(c, c) if where(p) else c for p, c in g.items()}, bare


def masters():
    out = {}
    for v, name in DRAFT.items():
        g, bare = ff.read(HERE / (name + '.aseprite'), PAL), BARE[v]()[1]
        assert all(p in g and g[p] != 'K' for p in bare), f'{name}: a point or tail end is not where it was drawn'
        out[v] = (g, bare)
    return out


def idle(v, m):
    up, down, flick = double_row(LONGER), drop_rows(SHORTER), move(*TAIL_TIP[v])
    return [m, moved(m, up), moved(hotter(m, HEAD[v]), up), moved(m, flick), moved(m, flick, down), moved(m, down)]


def windup(v, m):
    (rows, cols), (qrows, qcols) = DRAWN_BACK[v], QUIVER[v]
    a = moved(hotter(m), drop_cols(cols), drop_rows(rows))
    b = moved(hotter(hotter(m), HEAD[v]), drop_cols(qcols), drop_rows(qrows))
    return [a, b, a, b, a, b]


# -- the dash: typed. (row, first column, letters); the body's ribbon is straight here and waved by WAVE -----
RIBBON_SIDE = [(13, 20, 'OOOOOO'),                       # thick at the head, a pixel at the tail
               (14, 8, 'O' * 18),
               (15, 5, 'R' * 21),
               (16, 12, 'r' * 14)]
HEAD_DASH_SIDE = [(y + 4, x + 2, t) for y, x, t in Z.HEAD_SIDE]
BARE_SIDE = {(38, 15), (39, 15), (5, 15), (6, 15), (7, 15)}
WAVE_SIDE = {x: d for xs, d in (((19, 20, 21, 22), -1), ((13, 14, 15, 16), 1), ((8, 9, 10), -1)) for x in xs}   # column -> rows it is lifted
RIBBON_DOWN = [(2, 21, 'R'), (3, 21, 'R')] + [(y, 21, 'OR') for y in (4, 5, 6)] + [(y, 20, 'ORr') for y in range(7, 12)] \
            + [(y, 20, 'OORr') for y in range(12, 16)]   # heading down the screen: the tail at the top
BARE_DOWN = {(21, 2), (21, 3)}
WAVE_DOWN = {y: d for ys, d in (((10, 11, 12), 1), ((5, 6, 7), -1)) for y in ys}                             # row -> columns it is pushed right
POINT_DOWN = 26                                          # the row its point reaches


def dash(v):
    frames = []
    for sign in (1, 0, -1, 0):
        if v == 'R':
            body = {(x, y + sign * WAVE_SIDE.get(x, 0)): c for (x, y), c in ff.grid(RIBBON_SIDE, PAL).items()}
            g, bare = {**body, **ff.grid(HEAD_DASH_SIDE, PAL)}, {(x, y + sign * WAVE_SIDE.get(x, 0)) for x, y in BARE_SIDE}
        else:
            body = {(x + sign * WAVE_DOWN.get(y, 0), y): c for (x, y), c in ff.grid(RIBBON_DOWN, PAL).items()}
            head = {(x, POINT_DOWN - (y - 2)): c for (x, y), c in Z.head(21, 2)[0].items()}        # the drawn head, point down
            g = {**body, **head}
            bare = {(x + sign * WAVE_DOWN.get(y, 0), y) for x, y in BARE_DOWN} | {(21, POINT_DOWN), (22, POINT_DOWN)}
            if v == 'U':                                 # heading up: the same turned over, the blade's plain back
                g = {(x, H - 1 - y): ('O' if c in 'WYK' and POINT_DOWN - 9 <= y <= POINT_DOWN - 4 else c) for (x, y), c in g.items()}
                bare = {(x, H - 1 - y) for x, y in bare}
        g = ff.outline(g, bare)
        assert ff.pieces(g) == 1, f'dash {v}: the body came apart'
        frames.append(hotter((g, bare)))
    return frames


SHEETS = {'idle': (idle, IDLE_MS), 'windup': (windup, IDLE_MS), 'dash': (lambda v, m: dash(v), DASH_MS)}


def build():
    m = masters()
    out = {}
    for name, (make, ms) in SHEETS.items():
        out[name] = {v: make(v, m[v]) for v in DRAFT}
        for v, frames in out[name].items():
            for i, (g, bare) in enumerate(frames):
                assert all(p in g for p in bare), (name, v, i)
                ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in bare)          # in the frame, on the palette, outline closed
            assert all(a[0] != b[0] for a, b in zip(frames, frames[1:] + frames[:1])), f'{name} {v}: two frames in a row are the same'
    assert out['idle']['D'][0][0] == m['D'][0]
    return out


def panel(sheet, i):
    """Frame i of a sheet from all four sides, labelled, at one scale."""
    im = Image.new('RGBA', (4 * (W + 2) + 2, H + 12), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for k, (label, v, mirror) in enumerate((('FRONT', 'D', False), ('RIGHT', 'R', False), ('BACK', 'U', False), ('LEFT', 'R', True))):
        fr = ff.image(sheet[v][i][0], PAL, W, H)
        d.text((2 + k * (W + 2) + 8, 0), label, fill=(252, 252, 252, 255))
        im.alpha_composite(ImageOps.mirror(fr) if mirror else fr, (2 + k * (W + 2), 12))
    return im


if __name__ == '__main__':
    sheets = build()
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    for name, (make, ms) in SHEETS.items():
        n = len(sheets[name]['D'])
        print(f'{name}: {n} frames x {ms} ms, 3 drawn views (left = right mirrored)', flush=True)
        if not look:
            frames = [g for v in DRAFT for g, bare in sheets[name][v]]
            ff.draw_frames(frames, PAL, W, H, HERE / f'24_zoureg_{name}_draft', ms, {v: (k * n + 1, k * n + n) for k, v in enumerate(DRAFT)})
        ff.gif([panel(sheets[name], i) for i in range(n)], out / f'24_{name}.gif', ms, PAL)
    # how phase 1 reads in order, from the side: resting, drawn back for the fight's 0.6 s, the dash, resting again
    side = lambda name, i: ff.image(sheets[name]['R'][i][0], PAL, W, H)
    seq = [(side('idle', i), IDLE_MS) for i in range(6)] + [(side('windup', i), 150) for i in range(4)] \
        + [(side('dash', i % 4), DASH_MS) for i in range(8)] + [(side('idle', i), IDLE_MS) for i in range(6)]
    ff.gif([im for im, ms in seq], out / '24_phase1_side.gif', [ms for im, ms in seq], PAL, scale=8)
