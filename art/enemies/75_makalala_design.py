"""Enemy 75 Makalala, its two sheets: the idle from the front, and flying from the side.

The first frame of each is art/enemies/75_makalala_pose_first.py.

    idle  5 frames x 260 ms = 1.3 s, the game's own step, so the fight keeps its beat. It breathes in
          (neck and body a row up, the legs planted), SCREAMS on frame 2 -- the frame the fight fires its
          rings on (breath_frame): beak gaping, wings flared -- settles, and blinks.
    fly   4 frames x 70 ms = 0.28 s, the fight's wingbeat (flap_phase): wings raised, level, lowered,
          level; tail and legs swaying a row. The glowing club holds on frame pixel (49, 15) in every
          frame, where the fight fires its lasers from; the side's left is its mirror, and so is that point.

Drawn through the Aseprite pixel plugin into one draft a sheet. The game's assets are not touched.

    python art/enemies/75_makalala_design.py look DIR   # the GIFs only
    python art/enemies/75_makalala_design.py            # check, draw the drafts, write the GIFs
"""
from pathlib import Path
import importlib, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
A = importlib.import_module('75_makalala_pose_first')
W, H, PAL, rows, mirror, move, tone = A.W, A.H, A.PAL, A.rows, A.mirror, A.move, A.tone

IDLE_MS, FLY_MS = 260, 70
LIFT = (0, 1, 1, 1, 0)        # the breath: rows up (the club is a row under the frame's top: one row is all there is)
SCREAM = 2                    # the frame it screams on: Enemy::breath_frame
BLINK = 4
DRAFT = {'idle': '75_makalala_frame0_draft', 'fly': '75_makalala_fly_frame0_draft'}
FIRST = {'idle': A.FRONT, 'fly': A.SIDE}
up = lambda part, n: move(part, 0, -n)

# ---- the idle, from the front ---------------------------------------------------------------------------
GAPE = (49, 17)               # the middle of its gaping beak on the scream frame, before the breath lifts it
F_LEG = A.F_LEG + rows((range(41, 44), 45, 'g3'))                                              # the shank, longer behind the body for when it rises
F_GAPE = rows((range(11, 13), 48, 'Y3'), (range(13, 15), 47, 'Y5'),                           # screaming at us: the upper bill thrown up over its brow,
              (range(15, 19), 46, 'y7'), (19, 47, 'y5'),                                      # the inside of its mouth, dark gold (black would be a hole),
              (range(20, 22), 47, 'Y5'), (22, 48, 'Y3'), (23, 49, 'Y'))                       # the lower bill dropped
F_FLARE = rows((29, 39, 'M5'), (30, 36, 'M4D4'), (31, 34, 'M4D6'), (32, 32, 'M3D8'), (33, 31, 'M3D8'), (34, 30, 'M2D9'),    # ours left: a wing flung out,
               (35, 30, 'M2D8'), (36, 29, 'MD9'), (37, 29, 'D8'), (38, 29, 'D3'), (38, 33, 'D3'), (39, 29, 'D2'))           # its feathers apart at the tip
F_SHUT = [(y, x, t.replace('E', 'D').replace('K', 'D')) for y, x, t in A.F_HEAD]              # its eyes, shut


def idle(f):
    n = LIFT[f]
    wing = F_FLARE if f == SCREAM else A.F_WING
    top = [(A.F_BODY, 'solid'), (wing, 'solid'), (mirror(wing), 'solid'), (A.F_NECK, 'solid'), (F_SHUT if f == BLINK else A.F_HEAD, 'solid'),
           (F_GAPE if f == SCREAM else A.F_BEAK, 'solid'), (A.F_CLUB, 'solid')]
    return ff.layered([(F_LEG, 'solid'), (mirror(F_LEG), 'solid')] + [(up(part, n), kind) for part, kind in top], PAL, W, H)


# ---- flying, from the side ------------------------------------------------------------------------------
WINGS = (0, 1, 2, 1)          # raised, level, lowered, level
SWAY = (0, 1, 0, -1)          # tail and legs, rows down
S_LEVEL = rows((24, 20, 'L19'), (25, 16, 'M22L3'), (26, 15, 'D3M20L3'), (27, 16, 'D21M3'), (28, 19, 'D18'), (29, 23, 'D10'))   # the wing level: seen along it
S_LOW = [(52 - y, x, t) for y, x, t in A.S_WING]                                              # lowered: the raised wing, turned over about its shoulder
WING = (A.S_WING, S_LEVEL, S_LOW)
FAR = ((6, -1), (5, -1), (6, 1))                                                              # where the far wing shows past the near one


def fly(f):
    k, s = WINGS[f], SWAY[f]
    return ff.layered([(tone(move(WING[k], *FAR[k]), 'L', 'D'), 'solid'), (move(A.S_TAIL, 0, s), 'solid'),
                       (move(A.S_LEG, 3, s - 1), 'solid'), (move(A.S_LEG, 0, s), 'solid'), (A.S_BODY, 'solid'),
                       (A.S_HEAD, 'solid'), (A.S_BILL, 'solid'), (A.S_CLUB, 'solid'), (WING[k], 'solid')], PAL, W, H)


def club(g):
    """The middle of the glowing club in a flying frame."""
    px = [q for q, c in g.items() if c in 'WE' and q[1] <= 19 and 42 <= q[0] <= 56]
    xs, ys = [x for x, y in px], [y for x, y in px]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)


SHEETS = {'idle': (idle, len(LIFT), IDLE_MS), 'fly': (fly, len(WINGS), FLY_MS)}


def build():
    for name, parts in FIRST.items():                               # the drafts must still be these drawings
        assert ff.saved(HERE / (DRAFT[name] + '.aseprite')).tobytes() == ff.image(A.view(parts)[0], PAL, W, H).tobytes(), \
            f'{DRAFT[name]} was edited: read it back before animating'
    out = {}
    for name, (make, n, ms) in SHEETS.items():
        frames = out[name] = [make(f) for f in range(n)]
        assert frames[0][0] == A.view(FIRST[name])[0], f'{name}: frame 1 is not the first-frame drawing'
        for g, thin in frames: ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, cap=70)
        assert all(a[0] != b[0] for a, b in zip(frames, frames[1:] + frames[:1])), f'{name}: two frames in a row are the same'
    assert all(club(g) == A.CLUB for g, thin in out['fly']), 'the flying club left the fight pixel'
    g = out['idle'][SCREAM][0]
    assert all(g.get((GAPE[0] + dx, GAPE[1] - LIFT[SCREAM] + dy)) == 'y' for dx in (-1, 0, 1) for dy in (-1, 0, 1)), 'the gape is not where GAPE says'
    return out


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    sheets = build()
    for name, (make, n, ms) in SHEETS.items():
        frames = [g for g, thin in sheets[name]]
        boxes = [f'{max(x for x, y in g) - min(x for x, y in g) + 1}x{max(y for x, y in g) - min(y for x, y in g) + 1}' for g in frames]
        print(f'{name}: {n} frames x {ms} ms = {n * ms / 1000:.2f} s; palette, colour count, outline and height hold; drawn ' + ' '.join(boxes), flush=True)
        if not look:
            base = HERE / f'75_makalala_{name}_draft'
            if base.with_suffix('.aseprite').exists():
                assert ff.same_as_draft(base.with_suffix('.aseprite'), [ff.image(g, PAL, W, H) for g in frames]), \
                    f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
                print(f'{base.name}: already drawn, unchanged', flush=True)
            else:
                ff.draw_frames(frames, PAL, W, H, base, ms, {'D' if name == 'idle' else 'R': (1, n)})
        ff.gif([ff.image(g, PAL, W, H, bg=(0, 0, 0, 255)) for g in frames], out / f'75_{name}.gif', ms, PAL, scale=6)
        if look:
            strip = Image.new('RGBA', (W * n, H), (0, 0, 0, 255))
            for i, g in enumerate(frames): strip.alpha_composite(ff.image(g, PAL, W, H), (i * W, 0))
            strip.resize((strip.width * 4, strip.height * 4), Image.Resampling.NEAREST).save(out / f'75_{name}_strip.png')
    print(f'fight points: the scream\'s gape, frame {SCREAM}: ({GAPE[0] + 0.5}, {GAPE[1] + 0.5 - LIFT[SCREAM]}); the flying club {A.CLUB} on every frame', flush=True)
