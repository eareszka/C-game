"""Enemy 72 Mahwot, its two sheets: swimming, and firing. One side view each; the left is its mirror.

The first frames are art/enemies/72_mahwot_pose_first.py: the swim is the user's drawing, the shooting
frame is theirs with its head retyped at their word. Every frame here is made from those pixels.

    swim  6 frames x 105 ms = 0.63 s, half of its up-and-down weave in the fight (class Mahwot):
          a wave running head to tail -- each column of the drawing rides it, so plates and limbs go
          with the body; the head holds still, the tail's end moves up to 3 pixels. And its arms and
          legs paddle (the user): the free end of each swings forward and back, fore and hind in turn.
    fire  6 frames x 105 ms: it breathes and is otherwise still (the user). Chest and head rise a pixel
          (the chest first, then the trunk with it), the tail and hips and its feet staying put.

Drawn through the Aseprite pixel plugin into one draft a sheet. The game's assets are not touched.

    python art/enemies/72_mahwot_design.py look DIR   # the GIFs only
    python art/enemies/72_mahwot_design.py            # check, draw the drafts, write the GIFs
"""
from pathlib import Path
import importlib, math, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
A = importlib.import_module('72_mahwot_pose_first')
W, H, PAL = A.W, A.H, A.PAL

N, MS = 6, 105
STILL, REACH, LENGTH = 68, 1.5, 60.0      # the head from this column holds still; the tail's end swings REACH px either way; the wave's length
PADDLE = (0.0, 0.87, 0.87, 0.0, -0.87, -0.87)                            # a limb's swing by frame: forward, held, back, held
# the free end of each limb, hanging below the belly: how far each of its rows swings, and the columns it hangs in
FORE, HIND = ({41: 1, 42: 2, 43: 3}, (47, 62)), ({39: 1, 40: 2, 41: 3, 42: 3}, (22, 37))
BREATH = (None, None, 52, 44, 52, None)   # firing: everything from this column on is a row up; the row at CUT stretches
CUT = 46
DRAFT = {'swim': '72_mahwot_swim_frame0_draft', 'fire': '72_mahwot_fire_frame0_draft'}
FIRST = {'swim': A.SWIM, 'fire': A.FIRE}


def wave(d, f):
    """The swim: every column of the drawing moved up or down with a wave running head to tail; none on frame 0."""
    def dy(x):
        if x >= STILL: return 0
        a, at = REACH * (STILL - x) / (STILL - 5), 2 * math.pi * x / LENGTH
        return round(a * (math.sin(at + 2 * math.pi * f / N) - math.sin(at)))
    return {(x, y + dy(x)): c for (x, y), c in d.items()}


def paddle(d, f):
    """The swim: the free end of each limb sheared forward or back, the hind pair against the fore; none on frame 0."""
    out = dict(d)
    for (reach, (x0, x1)), way in ((FORE, 1), (HIND, -1)):
        limb = {q: c for q, c in d.items() if q[1] in reach and x0 <= q[0] <= x1}
        for q in limb: del out[q]
        out.update({(x + round(way * PADDLE[f] * reach[y]), y): c for (x, y), c in limb.items()})
    return out


def breath(d, f):
    """Firing: from column BREATH[f] on, all above row CUT is a row up and row CUT is doubled, so its feet stay down."""
    x0 = BREATH[f]
    if x0 is None: return d
    out = {(x, y - 1 if x >= x0 and y < CUT else y): c for (x, y), c in d.items()}
    out.update({(x, y - 1): c for (x, y), c in d.items() if x >= x0 and y == CUT})
    return out


px = lambda parts: ff.grid(parts[0][0], PAL)
SHEETS = {'swim': (lambda f: wave(paddle(px(A.SWIM), f), f), N, MS), 'fire': (lambda f: breath(px(A.FIRE), f), N, MS)}


def build():
    for name, parts in FIRST.items():                               # the drafts must still be these drawings
        assert ff.saved(HERE / (DRAFT[name] + '.aseprite')).tobytes() == ff.image(A.view(parts)[0], PAL, W, H).tobytes(), \
            f'{DRAFT[name]} was edited: read it back before animating'
    out = {}
    for name, (make, n, ms) in SHEETS.items():
        frames = out[name] = [make(f) for f in range(n)]
        assert frames[0] == A.view(FIRST[name])[0], f'{name}: frame 1 is not the first-frame drawing'
        for g in frames:
            ff.checks(g, PAL, W, H, open_ok=lambda p, c: True, cap=70)        # the user's pixels: palette, colour count, height
        if name == 'swim':
            assert all(len(g) == len(frames[0]) for g in frames), 'swim: a pixel was lost or doubled'
            assert all(a != b for a, b in zip(frames, frames[1:] + frames[:1])), 'swim: two frames in a row are the same'
        else: assert len({tuple(sorted(g.items())) for g in frames}) == 3, 'fire: at rest, the chest up, the trunk up'
    return out


def bare(g):
    """Colour pixels that meet empty space: how open the outline is."""
    return sum(1 for (x, y), c in g.items() if c != 'K' and any((x + dx, y + dy) not in g for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    sheets = build()
    for name, (make, n, ms) in SHEETS.items():
        frames = sheets[name]
        boxes = [f'{max(x for x, y in g) - min(x for x, y in g) + 1}x{max(y for x, y in g) - min(y for x, y in g) + 1}' for g in frames]
        print(f'{name}: {n} frames x {ms} ms = {n * ms / 1000:.2f} s; frame 1 is the first-frame drawing; drawn ' + ' '.join(boxes), flush=True)
        print(f'  colour pixels on the open edge, by frame: ' + ' '.join(str(bare(g)) for g in frames), flush=True)
        if not look:
            base = HERE / f'72_mahwot_{name}_draft'
            if base.with_suffix('.aseprite').exists():
                assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                    f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
                print(f'{base.name}: already drawn, unchanged', flush=True)
            else:
                ff.draw_frames(frames, PAL, W, H, base, ms, {'R': (1, n)})
        ff.gif([ff.image(g, PAL, W, H, bg=(0, 0, 0, 255)) for g in frames], out / f'72_{name}.gif', ms, PAL, scale=6)
        if look:
            strip = Image.new('RGBA', (W * 3, H * 2), (0, 0, 0, 255))
            for i, g in enumerate(frames): strip.alpha_composite(ff.image(g, PAL, W, H), ((i % 3) * W, (i // 3) * H))
            strip.resize((strip.width * 5, strip.height * 5), Image.Resampling.NEAREST).save(out / f'72_{name}_strip.png')
