"""Enemy 86 Leucrocotta, its two sheets: the idle (front, side, back) and the run (side only).

The first frame of each view is art/enemies/86_leucrocotta_pose_first.py (the front is the user's pixels).

    idle  5 frames x 170 ms = 0.85 s, the beat of its call (CALL_EVERY in class Leucrocotta):
          a breath (head and body a pixel up on 1-2, the legs planted), its mouth gaping on its two
          ridges of bone on 2-3 (the call), its tail swinging out and back
    run   4 frames, the game's count for a moving sheet: a gallop -- gathered in the air, hind legs down
          and pushing, stretched out, fore legs down -- the tail streaming behind. Drawn from the
          side only (the user): it runs off and back in sideways, and from the front and the back
          it keeps its idle.

Drawn through the Aseprite pixel plugin into one draft a sheet, a tag per view drawn. The game's assets are
not touched.

    python art/enemies/86_leucrocotta_design.py look DIR   # the GIFs only
    python art/enemies/86_leucrocotta_design.py            # check, draw the drafts, write the GIFs
"""
from pathlib import Path
import importlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff, flat_parts
A = importlib.import_module('86_leucrocotta_pose_first')
W, H, PAL, rows = A.W, A.H, A.PAL, A.rows

IDLE_MS, RUN_MS = 170, 80
LIFT = (0, 1, 1, 0, 0)        # the breath: rows up
CALL = (0, 0, 1, 1, 0)        # its mouth gaping
SWING = (0, 1, 2, 2, 1)       # the tail's end, pixels out
CALL_FRAME = 2                # the first frame its mouth is open
DRAFT = {'D': '86_leucrocotta_frame0_draft', 'R': '86_leucrocotta_side_frame0_draft', 'U': '86_leucrocotta_back_frame0_draft'}
FIRST = {'D': A.FRONT, 'R': A.SIDE, 'U': A.BACK}

# ---- pixels moved about: a drawing as {(x, y): letter} -------------------------------------------------
px = lambda part: ff.grid(part, PAL)
back = lambda d: [(y, x, c) for (x, y), c in d.items()]              # as a part again, a pixel a row
up = lambda d, n: {(x, y - n): c for (x, y), c in d.items()}


def lift(d, n, cut):
    """The breath: everything above row `cut` n rows up, the legs that much longer (row `cut` repeated)."""
    out = {(x, y - n if y < cut else y): c for (x, y), c in d.items()}
    for (x, y), c in d.items():
        if y == cut:
            for k in range(1, n + 1): out[x, y - k] = c
    return out


def sway(d, k, mid, low, sign, inside=lambda p: True):
    """A hanging tail swung k pixels: all of it from row `low` down, half of that from row `mid`."""
    move = lambda y: sign * (k if y >= low else k // 2 if y >= mid else 0)
    out = {p: c for p, c in d.items() if not inside(p)}
    out.update({(x + move(y), y): c for (x, y), c in d.items() if inside((x, y))})
    return out


# ---- the call: its jaw dropped, the mouth open on two ridges of bone ----------------------------------
F_CALL = [(20, 46, 'KWWWWWWWWK'), (21, 46, 'KmmmmmmmmK'), (22, 46, 'KmmRRRRmmK'), (23, 46, 'KWWWWWWWWK'), (24, 47, 'KkkkkkkK'), (25, 48, 'KKKKKK')]
S_HEAD_CALL = [r for r in A.S_HEAD if r[0] <= 17] + rows(
    (18, 65, 'k5m12k'), (19, 66, 'k2W4m2R6m2k'), (20, 67, 'k5W5m5k'), (21, 68, 'k9W5k'), (22, 69, 'k14'), (23, 72, 'k10'))
F_TAIL = lambda p: p[0] <= 38 and 34 <= p[1] <= 55                  # the user's front: its tail, left of the body


def idle(v, f):
    k = SWING[f]
    if v == 'D':
        g = sway(px(A.F_USER), k, 41, 48, -1, F_TAIL)
        if CALL[f]: g.update(px(F_CALL))
        g = lift(g, LIFT[f], 58)
        return g, set(g)
    if v == 'R':
        g, thin = ff.layered([(A.S_FAR, 'solid'), (back(sway(px(A.S_TAIL), k, 34, 41, -1)), 'solid'), (A.S_BODY, 'solid'),
                              (S_HEAD_CALL if CALL[f] else A.S_HEAD, 'solid')], PAL, W, H)
    else:
        g, thin = ff.layered(A.BACK[:-1] + [(back(sway(px(A.B_TAIL), k, 32, 40, 1)), 'solid')], PAL, W, H)
    return lift(g, LIFT[f], 56), set(lift({p: 1 for p in thin}, LIFT[f], 56))


# ---- the run, from the side: a torso without legs, and the legs by their joints -------------------------
S_TORSO = [r for r in A.S_BODY if r[0] <= 36 or (r[0] <= 39 and r[1] >= 43)]
S_STREAM = rows((22, 16, 'a4'), (23, 16, 'b3a4'), (24, 19, 'b3a3'), (25, 22, 'b2a2'), (26, 24, 'b2'),          # the tail, flying out behind
                (20, 12, 'h3'), (21, 11, 'h6'), (range(22, 24), 11, 'h5'), (24, 12, 'h3'))
BOB = (-2, -1, 0, -1)         # the body's height: gathered in the air, pushing, stretched low, landing
HIP, ELBOW = (32, 32), (56, 36)
# stifle, hock, fetlock, hoof tip of the near hind leg; knee, fetlock, hoof tip of the near fore leg -- frame pixels
HIND = (((38, 36), (35, 44), (42, 51), (45, 53)),       # tucked forward under the belly
        ((37, 38), (31, 46), (33, 58), (36, 61)),       # down, pushing
        ((31, 39), (23, 45), (15, 52), (12, 54)),       # stretched out behind
        ((37, 37), (31, 44), (37, 51), (40, 53)))       # swinging forward
FORE = (((53, 44), (49, 50), (46, 52)),                 # folded back
        ((63, 42), (70, 49), (73, 51)),                 # reaching
        ((62, 46), (66, 57), (69, 61)),                 # coming down ahead
        ((57, 47), (55, 58), (58, 61)))                 # down, under the shoulder
FAR = (5, 0), (2, -1)         # the far pair: its hip and elbow that much along, its lower joints a little further


def leg(joints, widths, tone, shade):
    """A leg through its joints, tapering; the last length is the hoof. Lit on the near side, shaded behind and under."""
    pts = [(p, w) for p, w in zip(joints[:-1], widths)]
    limb = flat_parts.run(*pts)
    d = {p: shade if (p[0] + 2, p[1]) not in limb or (p[0], p[1] + 2) not in limb else tone for p in limb}
    d.update({p: 'h' for p in flat_parts.stroke(joints[-2], joints[-1], 4.2, 4.2)})
    return d


def run(v, f):
    dy = BOB[f]
    at = lambda p, d=(0, 0): (p[0] + d[0], p[1] + d[1])
    hip, elbow = at(HIP, (0, dy)), at(ELBOW, (0, dy))
    far = lambda js: [at(at(j, FAR[0]), FAR[1]) for j in js]
    hind = lambda top, js, t, s: leg([top] + list(js), (8, 6, 4.2, 3.6), t, s)
    fore = lambda top, js, t, s: leg([top] + list(js), (5.5, 4.4, 3.6), t, s)
    legs_far = {**hind(at(hip, FAR[0]), far(HIND[f]), 'b', 'h'), **fore(at(elbow, FAR[0]), far(FORE[f]), 'b', 'h')}
    body = {**up(px(S_TORSO), -dy), **hind(hip, HIND[f], 'a', 'b'), **fore(elbow, FORE[f], 'a', 'b')}   # one part: no line where a leg joins
    return ff.layered([(back(legs_far), 'solid'), (back(up(px(S_STREAM), -BOB[f - 1])), 'solid'), (back(body), 'solid'),
                       (back(up(px(A.S_HEAD), -dy)), 'solid')], PAL, W, H)


SHEETS = {'idle': (idle, len(LIFT), IDLE_MS, 'DRU'), 'run': (run, len(BOB), RUN_MS, 'R')}     # what makes a frame, frames, ms, the views drawn


def build():
    for v, parts in FIRST.items():                                  # the drafts must still be these drawings
        assert ff.saved(HERE / (DRAFT[v] + '.aseprite')).tobytes() == ff.image(A.view(parts)[0], PAL, W, H).tobytes(), \
            f'{DRAFT[v]} was edited: read it back before animating'
    out = {}
    for name, (make, n, ms, views) in SHEETS.items():
        out[name] = {v: [make(v, f) for f in range(n)] for v in views}
        for v, frames in out[name].items():
            for g, thin in frames: ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, cap=70)
            assert all(a[0] != b[0] for a, b in zip(frames, frames[1:] + frames[:1])), f'{name} {v}: two frames in a row are the same'
    for v, parts in FIRST.items(): assert out['idle'][v][0][0] == A.view(parts)[0], f'{v}: the idle does not start on the first-frame drawing'
    return out


def panel(sheet, i):
    im = Image.new('RGBA', (W * len(sheet), H), (0, 0, 0, 255))
    for k, v in enumerate(sheet): im.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (k * W, 0))
    return im


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    sheets = build()
    for name, (make, n, ms, views) in SHEETS.items():
        print(f'{name}: {n} frames x {ms} ms = {n * ms / 1000:.2f} s, views {" ".join(views)} (left = side mirrored)', flush=True)
        for v in views:
            boxes = []
            for g, thin in sheets[name][v]:
                xs, ys = [x for x, y in g], [y for x, y in g]
                boxes.append(f'{max(xs) - min(xs) + 1}x{max(ys) - min(ys) + 1}')
            print(f'  {v}: palette, colour count, outline and height hold on all {n} frames; drawn ' + ' '.join(boxes), flush=True)
        if not look:
            base = HERE / f'86_leucrocotta_{name}_draft'
            frames = [g for v in views for g, thin in sheets[name][v]]
            if base.with_suffix('.aseprite').exists():
                assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                    f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
                print(f'{base.name}: already drawn, unchanged', flush=True)
            else:
                ff.draw_frames(frames, PAL, W, H, base, ms, {v: (k * n + 1, k * n + n) for k, v in enumerate(views)})
        ff.gif([panel(sheets[name], i) for i in range(n)], out / f'86_{name}.gif', ms, PAL, scale=5)
        if look:
            strip = Image.new('RGBA', (W * n, H * len(views)), (0, 0, 0, 255))
            for k, v in enumerate(views):
                for i in range(n): strip.alpha_composite(ff.image(sheets[name][v][i][0], PAL, W, H), (i * W, k * H))
            strip.resize((strip.width * 4, strip.height * 4), Image.Resampling.NEAREST).save(out / f'86_{name}_strip.png')
