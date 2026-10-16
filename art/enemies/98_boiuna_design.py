"""Enemy 98 Boiuna, its idle: winding body behind, front reared, it slithers -- more in the back than the front -- and breathes.

The first frame is art/enemies/98_boiuna_pose_first.py: one run of spine, tail tip to the back of the head,
and a typed head. Every frame here moves that spine and draws it the same way. The user: "have it slither more
in the back then the front"; before that, "have it breath and the further back tail slither around".

    idle  12 frames x 130 ms = 1.56 s, one breath.
          slither  a wave runs back along its body to the tail's tip, each point of the spine moving across
                   its own line: TIP px either way at the tail's tip, BACK px on the rear passes, falling to
                   FRONT px where the neck leaves the ground; the neck bows NECK px at its middle and the
                   back of the head does not move.
          breath   the body swells a little and settles; the head lifts a pixel with it (LIFT).

Drawn through the Aseprite pixel plugin into one draft. The game's assets are not touched.

    python art/enemies/98_boiuna_design.py look DIR   # the GIF only
    python art/enemies/98_boiuna_design.py            # check, draw the draft, write the GIF
"""
from pathlib import Path
import importlib, math, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
A = importlib.import_module('98_boiuna_pose_first')
W, H, PAL = A.W, A.H, A.PAL

N, MS = 12, 130
TIP, BACK, FRONT, REACH, LENGTH = 5.0, 3.0, 1.5, 60.0, 60.0   # the wave's size: at the tail's tip, REACH px on, and at the neck's foot; its length
NECK, NECK_LENGTH = 1.0, 160.0                    # the neck's bow at its middle; the wave is this long on the neck, so it sways and does not wriggle
SWELL = 0.05                                      # how much fatter the body is at the top of a breath
LIFT = (0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0)       # the head a row up; the last HANG px of neck go with it
HANG = 30.0
DRAFT = '98_boiuna_first_draft'


def across(run, i):
    """The unit line across the spine at a point."""
    a, b = run[max(i - 2, 0)], run[min(i + 2, len(run) - 1)]
    n = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    return -(b[1] - a[1]) / n, (b[0] - a[0]) / n


def moved(run, f, reach, turns, fat=1.0, lift=0):
    """A run with each point moved across its line by a wave running back toward the run's start; none on frame 0.
    reach(along) is the wave's size there, turns(along) how many waves along it that point is."""
    end, out = run[-1][3], []
    for i, (x, y, r, along) in enumerate(run):
        nx, ny = across(run, i)
        d = reach(along) * (math.sin(2 * math.pi * (turns(along) + f / N)) - math.sin(2 * math.pi * turns(along)))
        up = lift * max(0.0, 1 - (end - along) / HANG)
        out.append([x + nx * d, y + ny * d - up, r * fat if r >= 5 else r, along])
    return out


def pose(f):
    run, marks = A.spine()
    foot, end = marks[1], run[-1][3]

    def reach(a):
        if a >= foot:                                                # the neck: what the foot has dies away as its own bow comes in
            u = (a - foot) / (end - foot)
            return -FRONT * (1 - u) ** 2 - NECK * math.sin(math.pi * u)
        back = BACK + (TIP - BACK) * max(0.0, 1 - a / REACH) ** 1.2
        return -(back if a < REACH else BACK + (FRONT - BACK) * (a - REACH) / (foot - REACH))    # (minus: the tail's swing is up from where it lies)
    breath = (1 - math.cos(2 * math.pi * f / N)) / 2
    turns = lambda a: a / LENGTH if a < foot else foot / LENGTH + (a - foot) / NECK_LENGTH
    return moved(run, f, reach, turns, fat=1 + SWELL * breath, lift=LIFT[f]), marks, (0, -LIFT[f])


def build():
    first, bare = A.frame()
    assert ff.saved(HERE / (DRAFT + '.aseprite')).tobytes() == ff.image(first, PAL, W, H).tobytes(), \
        f'{DRAFT} was edited: read it back before animating'
    frames = []
    for f in range(N):
        g, thin = A.draw(*pose(f))
        ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, cap=224, max_colours=25)
        frames.append(g)
    assert frames[0] == first, 'frame 1 is not the first-frame drawing'
    assert all(a != b for a, b in zip(frames, frames[1:] + frames[:1])), 'two frames in a row are the same'
    return frames


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    frames = build()
    boxes = [f'{max(x for x, y in g) - min(x for x, y in g) + 1}x{max(y for x, y in g) - min(y for x, y in g) + 1}' for g in frames]
    print(f'idle: {N} frames x {MS} ms = {N * MS / 1000:.2f} s; frame 1 is the first-frame drawing; drawn ' + ' '.join(boxes), flush=True)
    if not look:
        base = HERE / '98_boiuna_idle_draft'
        if base.with_suffix('.aseprite').exists():
            assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
            print(f'{base.name}: already drawn, unchanged', flush=True)
        else:
            ff.draw_frames(frames, PAL, W, H, base, MS, {'D': (1, N)})
    ff.gif([ff.image(g, PAL, W, H, bg=(0, 0, 0, 255)) for g in frames], out / '98_idle.gif', MS, PAL, scale=4)
