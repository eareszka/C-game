"""Enemy 21 Asp, its idle: coiled in place, swaying, stopping its ear with its tail, its tongue flicking.

Ten frames a view (front, side, back), 130 ms each: 1.3 s, the length of the old sheet's loop, so the
fight keeps its beat. The first frame of each view is art/enemies/21_asp_pose_first.py. The old sheet's
three poses, in the order it showed them:

    sway    its head and the top of its neck a pixel one way on 1-2, the other on 6-7
    bounce  on 1 and 6 its body dips a pixel (the neck a row shorter) and its tail springs a pixel out (the user)
    breath  its coils a pixel wider at each end on 3-5, the tail riding out with them (the user)
    ear     its tail's tip reaching its ear on 3, pressed into it on 4, letting go on 5 (the old frame 1)
    tongue  forked, out on 8, drawing back on 9 (the old frame 2: the frame the hiss leaves on)

Drawn through the Aseprite pixel plugin into one draft, a tag per view. The game's assets are not
touched.

    python art/enemies/21_asp_design.py look DIR   # the GIF only
    python art/enemies/21_asp_design.py            # check, draw the draft, write the GIF
"""
from pathlib import Path
import importlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
A = importlib.import_module('21_asp_pose_first')
W, H, PAL, rows, mirror = A.W, A.H, A.PAL, A.rows, A.mirror

N, MS = 10, 130
SWAY = (0, 1, 1, 0, 0, 0, -1, -1, 0, 0)            # its head: columns across
DIP = (0, 1, 0, 0, 0, 0, 1, 0, 0, 0)               # the bounce: its body rows down, its tail columns out
SWELL = (0, 0, 0, 1, 1, 1, 0, 0, 0, 0)             # the breath: its coils a pixel wider at each end
EAR = (0, 0, 0, 1, 2, 1, 0, 0, 0, 0)               # its tail's tip: away, reaching, in its ear
TONGUE = (0, 0, 0, 0, 0, 0, 0, 0, 2, 1)            # in, drawing back, out
HISS_FRAME = 8                                     # the first frame its tongue is out
BEND = 18                                          # the neck from this row down stays with the coils
DRAFT = {'D': '21_asp_frame0_draft', 'R': '21_asp_side_frame0_draft', 'U': '21_asp_back_frame0_draft'}
FIRST = {'D': A.FRONT, 'R': A.SIDE, 'U': A.BACK}
move = lambda part, dx, dy=0: [(y + dy, x + dx, t) for y, x, t in part]
OUT = {'D': 1, 'R': -1, 'U': -1}                  # the side its tail is on: columns outward
SPRING = 16                                        # the tail above this row springs out on the bounce

# the tail's tip (none, reaching, in the ear) and the tongue (none, drawing back, out), a view each; from behind
# the ear is the other one and the tongue is out of sight
F_PLUG = ([], rows((5, 29, 'LM')), rows((5, 29, 'LM'), (4, 28, 'LM'), (3, 28, 'L')))
S_PLUG = ([], rows((4, 16, 'ML')), rows((4, 16, 'MLL'), (3, 16, 'MLL')))
F_TONGUE = ([], rows((12, 21, 'R'), (13, 20, 'R.R')), rows((range(12, 14), 21, 'R'), (14, 20, 'R.R')))
S_TONGUE = ([], rows((9, 35, 'R'), (8, 36, 'R'), (10, 36, 'R')), rows((9, 35, 'RR'), (8, 37, 'R'), (10, 37, 'R')))
PARTS = {'D': (A.F_TAIL, A.F_HEAD, A.F_NECK, F_PLUG, F_TONGUE),
         'R': (A.S_TAIL, A.S_HEAD, A.S_NECK, S_PLUG, S_TONGUE),
         'U': (mirror(A.F_TAIL), A.B_HEAD, A.B_NECK, tuple(mirror(p) for p in F_PLUG), ([], [], []))}


def swell(part):
    """A breath in: each coil a pixel wider at both ends (its middle run two longer); the top line, row 22, longer by its ends."""
    return [(y, x - 1, 'K' + t + 'K') if y == 22 else (y, x - 1, t[:len(t) // 2] + t[len(t) // 2] * 2 + t[len(t) // 2:]) if y > 22 else (y, x, t)
            for y, x, t in part]


def idle(v, f):
    tail, head, neck, plug, tongue = PARTS[v]
    dx, dy, wide = SWAY[f], DIP[f], SWELL[f]
    tail = [(y, x + OUT[v] * (wide + (dy if y < SPRING else 0)), t) for y, x, t in tail]      # riding the coils out; springing on the bounce
    low, high = [r for r in neck if r[0] >= BEND + dy], [r for r in neck if r[0] < BEND]      # dipping, the neck loses a row at the bend
    base = low + A.COILS
    return ff.layered([(tail, 'raw'), (swell(base) if wide else base, 'raw'), (move(high + head, dx, dy), 'raw'),
                       (move(plug[EAR[f]], dx, dy), 'raw'), (move(tongue[TONGUE[f]], dx, dy), 'raw')], PAL, W, H)


def tip(v, f):
    """The tongue's tip on frame f: the middle of its fork's ends, in frame pixels (None with the tongue in or out of sight)."""
    red = [q for q, c in idle(v, f)[0].items() if c == 'R']
    if not red: return None
    far = max(y for x, y in red) if v == 'D' else max(x for x, y in red)
    ends = [q for q in red if (q[1] if v == 'D' else q[0]) == far]
    return (sum(x for x, y in ends) / len(ends) + 0.5, sum(y for x, y in ends) / len(ends) + 0.5)


def build():
    for v, parts in FIRST.items():                                  # the drafts must still be these drawings
        assert ff.saved(HERE / (DRAFT[v] + '.aseprite')).tobytes() == ff.image(A.view(parts)[0], PAL, W, H).tobytes(), \
            f'{DRAFT[v]} was edited: read it back before animating'
    out = {v: [idle(v, f) for f in range(N)] for v in DRAFT}
    for v, frames in out.items():
        assert frames[0][0] == A.view(FIRST[v])[0], f'{v}: frame 1 is not the first-frame drawing'
        for g, thin in frames: ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin)
    return out


def panel(sheet, i):
    im = Image.new('RGBA', (W * len(DRAFT), H), (0, 0, 0, 255))
    for k, v in enumerate(DRAFT): im.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (k * W, 0))
    return im


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    sheet = build()
    print(f'idle: {N} frames x {MS} ms = {N * MS / 1000:.2f} s, 3 drawn views (left = side mirrored); frame 1 of each is the first-frame drawing', flush=True)
    for v in DRAFT:
        boxes = [f'{max(x for x, y in g) - min(x for x, y in g) + 1}x{max(y for x, y in g) - min(y for x, y in g) + 1}' for g, thin in sheet[v]]
        print(f'  {v}: palette, colour count and height hold on all {N} frames; drawn ' + ' '.join(boxes), flush=True)
        print(f'     tongue tip on frame {HISS_FRAME}: {tip(v, HISS_FRAME)}', flush=True)
    if not look:
        base = HERE / '21_asp_idle_draft'
        frames = [g for v in DRAFT for g, thin in sheet[v]]
        if base.with_suffix('.aseprite').exists():
            assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
            print(f'{base.name}: already drawn, unchanged', flush=True)
        else:
            ff.draw_frames(frames, PAL, W, H, base, MS, {v: (k * N + 1, k * N + N) for k, v in enumerate(DRAFT)})
    ff.gif([panel(sheet, i) for i in range(N)], out / '21_idle.gif', MS, PAL, scale=8)
    if look:
        strip = Image.new('RGBA', (W * N, H * len(DRAFT)), (0, 0, 0, 255))
        for k, v in enumerate(DRAFT):
            for i in range(N): strip.alpha_composite(ff.image(sheet[v][i][0], PAL, W, H), (i * W, k * H))
        strip.resize((strip.width * 4, strip.height * 4), Image.Resampling.NEAREST).save(out / '21_idle_strip.png')
