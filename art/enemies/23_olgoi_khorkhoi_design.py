"""Enemy 23 Olgoi-Khorkhoi, its idle: the approved frame moved -- it heaves and leans on its tail, the head dips
and the maw's lobes spread, the feelers whip.

Frame 0 is the user's first-frame draft (23_olgoi_khorkhoi_frame0_draft.aseprite) as they saved it -- they took the
trailing whip off and retouched the arch -- out of the sand since 2026-10-19: the sand and the acid drops taken off,
the body carried on down and out along the ground to the right, its tip curling up under a fin
(23_olgoi_khorkhoi_frame0_ground.aseprite, made by 23_olgoi_khorkhoi_back.py: their pixels plus the back; the sand version is in art/_backup/23_sand_20261019). Every frame here moves those pixels. The five
whip feelers are rebuilt each frame instead (23_olgoi_khorkhoi_pose_first's whip(), its points waved), because they
are thin lines that tear when sheared.

    12 frames x 170 ms = 2.04 s, the fight's 2.0 s beat between rings.
    heave   LIFT: everything above the ground row a row up, the row there doubled so it stays rooted; the tail stays
    lean    SWAY: a shear, the arch's top up to 2 px either way, the legs still; the head goes with the leg it hangs on
    lunge   BOB: the head block (ring, lobes, spines) dips up to 2 px; GAPE: each lobe stretches outward by doubling
            its hinge row -- the maw spreading on frames 3-7, widest on 4-6 (the spit beat)
    feelers a wave travelling out to the tips, WHIP px there

Sheet two (the user: "the head spinning around while idling", "the 2 white blades ... should spin with the head",
"the body breath really fast and hyper"): the same loop with the body on LIFT_SPIN / SWAY_SPIN (three heaves and
two leans a loop, 2 px), no dip or gape, and the head -- the mouth, its four lobes and the two blades -- turning
SPIN degrees a frame about the mouth, a full turn a loop so it joins up. The lobes are turned as shapes and filled
again by the first frame's rule so the light stays up and to the left; the blades are drawn again at each angle.

    python art/enemies/23_olgoi_khorkhoi_design.py look DIR   # PIL only: the GIFs and strips into DIR
    python art/enemies/23_olgoi_khorkhoi_design.py            # check, draw both drafts, write the GIFs
"""
from pathlib import Path
import importlib, math, sys, tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE))
import first_frame as ff
import flat_parts
A = importlib.import_module('23_olgoi_khorkhoi_pose_first')
R = importlib.import_module('23_olgoi_khorkhoi_rings')
PAL = A.PAL
W, H, OX, OY = 320, 124, 95, 12   # the sheets' frame: the first frame's 225x112 drawing set OX, OY in from the top left. 320 wide is the whole arena
                                  # (drawn 2x about its middle): the body runs off the screen's right edge (2026-10-19). OX 95 keeps the worm where
                                  # the 152-wide sheet had it (OX 11 there), so the fight's numbers, measured on that sheet about its middle 76, still hold
MASTER = HERE / '23_olgoi_khorkhoi_frame0_ground.aseprite'
DRAFT = HERE / '23_olgoi_khorkhoi_idle_draft'
N, MS = 12, 170
#        frame  0  1  2  3  4  5  6  7   8   9  10 11
LIFT = (        0, 0, 1, 1, 1, 1, 0, 0,  0,  0,  0, 0)    # px the worm heaves up
SWAY = (        0, 1, 2, 2, 1, 0, 0, -1, -2, -2, -1, 0)   # px the arch's top leans to our right
BOB  = (        0, 0, 0, 1, 2, 2, 1, 0,  0,  0,  0, 0)    # px the head dips
GAPE = (        0, 0, 0, 1, 2, 2, 2, 1,  0,  0,  0, 0)    # px each lobe of the maw spreads outward
SAND_ROW, TOP = 70, 4                                     # the ground row (the old sand line), the arch's top row: the lean is 0 at the first, full at the second
AMP, WAVE, EASE = 1.0, 90.0, 30.0                         # the back's slither: px across, wavelength along it, and how far from the arch it takes to come in full
WHIP = 3.0                                                # the feelers' tips swing this far across
HEAD_PARTS = ('ring', 'petal0', 'petal1', 'petal2', 'petal3', 'horn0', 'horn1', 'barbs0', 'barbs1')
SPIN = 30.0                                                      # degrees the head turns a frame on the second sheet: a full turn a loop, so it joins up
SPIN_DRAFT = HERE / '23_olgoi_khorkhoi_spin_draft'
#             frame  0  1  2  3   4   5  6  7  8  9  10  11      the second sheet's body: hyper -- three heaves a loop, two leans
LIFT_SPIN = (        0, 1, 2, 1,  0,  1, 2, 1, 0, 1,  2,  1)
SWAY_SPIN = (        0, 1, 1, 0, -1, -1, 0, 1, 1, 0, -1, -1)
# The two blades on the second sheet, turning with the head: from the mouth's middle, their angles at frame 0 (the
# left one and the right, measured off their roots and tips), where they start and end along that line, and how
# thick they are at the root. Both get the right blade's reach (the user), the same at every angle; the sweep is
# a full circle, which is why the sheets' frame is bigger than the first frame's.
BLADE_ANGLES, BLADE_ROOT, BLADE_TIP, BLADE_W = (188.0, -11.0), 18.0, 59.0, 3.5
# Sheet three, the spin firing up (the user: "so it doesnt go from 1-100 speed"): played once as it enrages, before the
# spin loop. Its turn per frame climbs evenly from nearly nothing to the loop's SPIN, so it turns 15 j (j + 1) / M
# degrees by frame j and ends half a turn round -- the spin loop's frame UP_TO, where the fight picks the loop up. The
# body's heave and lean blend from the idle's to the spin's over it, the spin's counted so they meet frame UP_TO too.
M_UP, UP_TO = 11, 6
SPINUP_DRAFT = HERE / '23_olgoi_khorkhoi_spinup_draft'
_w = lambda j: j / M_UP
_s = lambda j: (j - M_UP + UP_TO) % N                              # the spin loop's frame this one is heading for
LIFT_UP = tuple((1 - _w(j)) * LIFT[j % N] + _w(j) * LIFT_SPIN[_s(j)] for j in range(M_UP))
SWAY_UP = tuple((1 - _w(j)) * SWAY[j % N] + _w(j) * SWAY_SPIN[_s(j)] for j in range(M_UP))
THETA_UP = tuple(15.0 * j * (j + 1) / M_UP for j in range(M_UP))


def theta(f, spin):
    """How far the maw and blades are turned on frame f of a spinning sheet."""
    return THETA_UP[f] if spin == 'up' else SPIN * f


def phase(f, spin):
    """Where frame f is in the 12-frame loop's waves (the slither, the feelers): the spin-up runs on into the spin
    loop's frame UP_TO."""
    if spin == 'up': return f * (N + UP_TO) / (N * M_UP)              # from the idle's first frame on round to the spin's UP_TO
    return f / N
LOOSE = tuple(f'feeler{i}' for i in range(len(A.FEELERS))) + ('trail',)   # rebuilt (or gone) each frame
# Each lobe's hinge: the row (or column) that is doubled when it spreads, and which way outward is.
HINGE = {'petal0': ('y', 41, -1), 'petal1': ('x', 33, -1), 'petal2': ('x', 70, 1), 'petal3': ('y', 59, 1)}
rnd = lambda v: int(math.floor(v + 0.5))


def split():
    """The master cut by the part that drew each pixel: {part name: {(x, y): letter}} for the head's parts. The body
    is not kept as pixels: every frame draws it again on its moved spine (23_olgoi_khorkhoi_rings.body), and the
    feelers are rebuilt each frame too."""
    theirs = ff.read(MASTER, PAL)
    _, over = R.parts()
    _, _, owner = A.layer(A.parts()[0])
    out = {}
    for p, c in over.items():
        who = owner.get(p)
        if who in HEAD_PARTS: out.setdefault(who, {})[p] = c
    return theirs, out, []


def lean(y, sway):
    return rnd(sway * (SAND_ROW - y) / (SAND_ROW - TOP)) if y <= SAND_ROW else 0


def tables(spin):
    """The sheet's heave and lean, by frame."""
    return (LIFT_UP, SWAY_UP) if spin == 'up' else (LIFT_SPIN, SWAY_SPIN) if spin else (LIFT, SWAY)


def spine_at(f, spin=False):
    """The body's spine on frame f: the arch heaves and leans as before; the back slithers -- a wave running along it
    toward the off-screen end, AMP px across, coming in over EASE px from the arch so the bend never tears -- and
    none of it moves on frame 0."""
    lift, sway = tables(spin)
    sp, n = R.spine0()
    d, out = [0.0] * n, []
    for k in range(n - 1, -1, -1):                                 # each back point's distance along from the arch
        nxt = sp[k + 1]
        d[k] = (d[k + 1] if k < n - 1 else 0.0) + math.dist(sp[k][:2], nxt[:2])
    for k, (x, y, r) in enumerate(sp):
        ax = sway[f] * (SAND_ROW - y) / (SAND_ROW - TOP) if y <= SAND_ROW else 0.0
        ay = -lift[f]
        if k >= n:
            out.append((x + ax, y + ay, r)); continue
        w = min(1.0, d[k] / EASE)
        a, b = sp[max(k - 1, 0)], sp[k + 1]
        m = math.dist(a[:2], b[:2]) or 1
        nx, ny = (b[1] - a[1]) / m, -(b[0] - a[0]) / m             # across the back
        wv = AMP * w * (math.sin(2 * math.pi * (phase(f, spin) - d[k] / WAVE)) - math.sin(2 * math.pi * (-d[k] / WAVE)))
        out.append((x + (1 - w) * ax + nx * wv, y + (1 - w) * ay + ny * wv, r))
    return out, n


def blades(theta):
    """The two blades turned `theta` degrees about the mouth with the head: bone, shaded on the side away from the
    light, barbs on the side that was up at frame 0, a line round them where they are thick (the solid rule of
    tools/flat_parts). In the first frame's coordinates, which they may leave: the sheet's frame is bigger."""
    cx, cy = A.HEAD[0] + A.RING[0], A.HEAD[1] + A.RING[1]
    out = {}
    for a0 in BLADE_ANGLES:
        a = math.radians(a0 + theta); ux, uy = math.cos(a), math.sin(a)
        b = math.radians(a0); bx, by = -math.sin(b), math.cos(b)          # across the blade at frame 0...
        if by > 0: bx, by = -bx, -by                                      # ...the side that is up
        t = math.radians(theta); bx, by = bx * math.cos(t) - by * math.sin(t), bx * math.sin(t) + by * math.cos(t)
        root, tip = (cx + ux * BLADE_ROOT, cy + uy * BLADE_ROOT), (cx + ux * BLADE_TIP, cy + uy * BLADE_TIP)
        away = -1 if bx * A.LIGHT3[0] + by * A.LIGHT3[1] > 0 else 1       # the shaded side: the barbed one, or the other
        px = {}
        for p in flat_parts.stroke(root, tip, BLADE_W, 1.2):
            s = (p[0] - root[0]) * bx + (p[1] - root[1]) * by
            px[p] = 's' if s * away > 0.4 else 'S'
        inner = lambda q: q in px and all((q[0] + dx, q[1] + dy) in px for dx, dy in ff.N4)
        for p, c in px.items():
            nb = [(p[0] + dx, p[1] + dy) for dx, dy in ff.N4]
            out[p] = 'K' if any(q not in px for q in nb) and any(inner(q) for q in nb) else c
        n = math.dist(root, tip)
        for k in range(4, int(n * 0.7), 5):
            w = (BLADE_W + (1.2 - BLADE_W) * k / n) / 2
            out[round(root[0] + ux * k + bx * (w + 0.6)), round(root[1] + uy * k + by * (w + 0.6))] = 'S'
    return out


def head_at(p, name, f):
    """Where a head pixel goes: with the leg it hangs on, down on the lunge, and outward past its lobe's hinge."""
    x, y = p
    dx, dy = lean(50, SWAY[f]), BOB[f] - LIFT[f]
    if name in HINGE and GAPE[f]:
        axis, at, way = HINGE[name]
        if (y if axis == 'y' else x) * way > at * way:
            if axis == 'y': dy += way * GAPE[f]
            else: dx += way * GAPE[f]
    return x + dx, y + dy


def maw(theta):
    """The mouth and its four lobes turned `theta` degrees about the mouth's middle: the ring's teeth turned, each
    lobe's shape turned (nearest pixel) and filled again by the first frame's rule -- the line round it, a lip three
    pixels in, a tooth every third pixel along each lip, the dark lining -- with the lip's tone from where it faces
    now, so the light stays up and to the left while the maw spins."""
    cx, cy = A.HEAD[0] + A.RING[0], A.HEAD[1] + A.RING[1]
    t = math.radians(theta); cs, sn = math.cos(t), math.sin(t)
    out = {}
    ring = A.ring(theta)
    for p, c in ring.items():
        out[p] = 'K' if any((p[0] + dx, p[1] + dy) not in ring for dx, dy in ff.N4) else c
    for along, edges, lip in A.PETALS:
        local = {(A.HEAD[0] + (i if along == 'y' else k), A.HEAD[1] + (k if along == 'y' else i))
                 for k, (a, b) in edges.items() for i in range(a, b + 1)}
        mx, my = sum(x for x, y in local) / len(local) - cx, sum(y for x, y in local) / len(local) - cy
        n = math.hypot(mx, my)
        ax, ay = (mx / n) * cs - (my / n) * sn, (mx / n) * sn + (my / n) * cs     # the lobe's axis, outward, turned
        mask = set()
        for y in range(cy - 26, cy + 27):
            for x in range(cx - 26, cx + 27):
                sx, sy = x - cx, y - cy
                if (round(cx + sx * cs + sy * sn), round(cy - sx * sn + sy * cs)) in local: mask.add((x, y))
        dist, edge = {}, [p for p in mask if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in ff.N4)]
        for p in edge: dist[p] = 0
        while edge:                                                 # how far in from the line each pixel is
            edge, prev = [], edge
            for p in prev:
                for dx, dy in ff.N4:
                    q = (p[0] + dx, p[1] + dy)
                    if q in mask and q not in dist: dist[q] = dist[p] + 1; edge.append(q)
        for p, d in dist.items():
            if d == 0: out[p] = 'K'; continue
            rx, ry = p[0] - cx, p[1] - cy
            side = 1 if rx * -ay + ry * ax >= 0 else -1              # which lip: across the axis
            if d <= 3:
                lit = -ay * side * A.LIGHT3[0] + ax * side * A.LIGHT3[1]
                out[p] = 'L' if lit > 0.35 else 'D' if lit < -0.35 else 'M'
            elif d in (4, 5) and int(rx * ax + ry * ay) % 3 == (0 if side < 0 else 1): out[p] = 'S'
            else: out[p] = 'D'
    return out


def feelers(f, bob, spin=False):
    """The five whips rebuilt: each point past the root swung across its feeler by a wave running out to the tip
    (none on frame 0), the whole feeler carried with the head so the roots stay under the lobes."""
    lift, sway = tables(spin)
    dx, dy = lean(50, sway[f]), bob - lift[f]
    out = {}
    for pts in A.FEELERS:
        moved = []
        for k, (x, y) in enumerate(pts):
            if k:
                px, py = pts[k - 1]
                n = math.hypot(x - px, y - py) or 1
                nx, ny = -(y - py) / n, (x - px) / n
                amp = WHIP * k / (len(pts) - 1)
                d = amp * (math.sin(2 * math.pi * (phase(f, spin) - k / 4)) - math.sin(2 * math.pi * (-k / 4)))
                x, y = x + nx * d, y + ny * d
            moved.append((min(max(x + dx, 2.0), W - 3.0), max(y + dy, 2.0)))   # kept off the frame's top and sides
        out.update(A.whip(moved, 2.4, 1.0))
    return out


def frame(f, theirs, by_part, spin=False):
    """Frame f, in the sheet's frame (the first frame's drawing OX, OY in from its top left), and the pixels allowed
    to meet empty space: the rebuilt thin parts, and whatever was open in theirs.
    spin: the second sheet -- no dip or gape; the maw and the blades turn SPIN degrees a frame, the blades over the
    body and under the lobes."""
    open_theirs = {p for p, c in theirs.items() if c != 'K' and any((p[0] + dx, p[1] + dy) not in theirs for dx, dy in ff.N4)}
    lift, sway = tables(spin)
    g, ok = {}, set()
    bod = R.body(*spine_at(f, spin))                                 # the whole body, drawn again on its moved spine
    g.update(bod)
    loose = feelers(f, 0 if spin else BOB[f], spin); g.update(loose); ok |= set(loose)
    if spin and not (spin == 'up' and f == 0):                      # the spin-up's first frame is the idle's own: their head, at rest
        dx, dy = lean(50, sway[f]), -rnd(lift[f])
        turned = blades(theta(f, spin))                             # over the body...
        turned.update(maw(theta(f, spin)))                          # ...and under the lobes
        g.update({(p[0] + dx, p[1] + dy): c for p, c in turned.items()})
        ok |= {(p[0] + dx, p[1] + dy) for p, c in turned.items() if c in 'Ss'}   # the blades' bare ends and barbs
    else:
        for name in HEAD_PARTS:
            for p, c in by_part.get(name, {}).items():
                q = head_at(p, name, f); g[q] = c
                if p in open_theirs or name.startswith('barbs'): ok.add(q)
                if name in HINGE and GAPE[f]:                          # the hinge row doubled into the gap
                    axis, at, way = HINGE[name]
                    if (p[1] if axis == 'y' else p[0]) == at:
                        for k in range(1, GAPE[f] + 1):
                            g[(q[0], q[1] + way * k) if axis == 'y' else (q[0] + way * k, q[1])] = c
    g = R.compose(bod, {p: c for p, c in g.items() if p not in bod or g[p] != bod[p]})
    g = {(x + OX, y + OY): c for (x, y), c in g.items()}           # into the sheet's frame
    ok = {(x + OX, y + OY) for x, y in ok}
    for p, c in list(g.items()):                                    # a lean's row step can open a diagonal edge: closed
        if c != 'K' and p not in ok:
            for dx, dy in ff.N4:
                if p[0] + dx < W: g.setdefault((p[0] + dx, p[1] + dy), 'K')   # not past the right edge: the body runs on out of view
    return g, ok


def build(spin=False):
    theirs, by_part, left = split()
    if left and not spin: print(f'left behind in their save, not carried: {left} (pixels of the whip they took off)', flush=True)
    frames = []
    for f in range(M_UP if spin == 'up' else N):
        g, ok = frame(f, theirs, by_part, spin)
        try: ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in ok, cap=224, max_colours=24, right_open=True)
        except AssertionError as e: raise AssertionError(f'frame {f}: {e}') from None
        frames.append(g)
    if not spin: assert frames[0] == {(x + OX, y + OY): c for (x, y), c in theirs.items() if (x, y) not in left}, 'frame 1 is not their first frame'
    if spin == 'up': assert frames[0] == build()[0], 'the spin-up does not start on the first idle frame'
    assert all(a != b for a, b in zip(frames, frames[1:] + ([] if spin == 'up' else frames[:1]))), 'two frames in a row are the same'
    return frames


def write(frames, base, name, look, out):
    """The draft (unless it is already this design) and the GIF for one sheet."""
    images = [ff.image(g, PAL, W, H) for g in frames]
    boxes = [f'{max(x for x, y in g) - min(x for x, y in g) + 1}x{max(y for x, y in g) - min(y for x, y in g) + 1}' for g in frames]
    n = len(frames)
    print(f'{name}: {n} frames x {MS} ms = {n * MS / 1000:.2f} s; drawn ' + ' '.join(boxes), flush=True)
    if look:
        ff.review([(str(i), im) for i, im in enumerate(images)], out / f'23_{name}_strip.png', scale=3)
    else:
        if base.with_suffix('.aseprite').exists():
            assert ff.same_as_draft(base.with_suffix('.aseprite'), images), f'{base.name}.aseprite is not this design: edited by hand, not drawn over'
            print(f'{base.name}: already drawn, unchanged', flush=True)
        else:
            ff.draw_frames(frames, PAL, W, H, base, MS, {'D': (1, n)})
        with tempfile.TemporaryDirectory() as d:
            for f in (0, 5): ff.style_check(images[f], d, f'23_{name}_f{f}', tier='giant')
    ff.gif([ff.image(g, PAL, W, H, bg=(0, 0, 0, 255)) for g in frames], out / f'23_{name}.gif', MS, PAL, scale=4)


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    write(build(), DRAFT, 'idle', look, out)              # sheet one: frame 1 is their first frame
    write(build(spin=True), SPIN_DRAFT, 'spin', look, out)  # sheet two: the maw spinning
    write(build(spin='up'), SPINUP_DRAFT, 'spinup', look, out)  # sheet three: the spin firing up, once, between them
