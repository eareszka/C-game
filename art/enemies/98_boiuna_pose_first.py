"""Enemy 98 Boiuna, first frame: its long winding body laid out behind, its front reared up. One view, the front.

Three things from the user, joined. Their first frame (art/_backup/98_user_first_frame_20261013/
boiuna_idle_source.png): the great snake laid out in winding passes, the thin tail at the top. Their reference
(boiuna_reference.png beside it): reared, the neck rising up and left, arching over and coming down to a head
that hangs open-mouthed, the pale belly along the inside of the neck. And: "have it still be in the snake like
pose from earlier but with the front up like it is now". Size, greens, yellow slit eyes and the head are those
of the frame they sent first and chose to halve. (The two drawings this replaces: art/_backup/
98_flat_pose_20261013, all passes and no rearing; 98_coil_pose_20261013, the reference's two fat coils.)

The whole snake is ONE run of spine, tail tip to the back of the head: a line of points with a thickness,
drawn as a flat-toned tube -- light where it faces up and left, dark underneath, a 1-px black line round it.
PASSES is their first frame's layout (its curves, in that frame's own 384x336 pixels), halved and squashed
to SQUASH of its height: ground seen at an angle, so the neck stands against black above it. NECK carries on
from the front pass. Where the body lies over itself the part nearer the head is in front and its edge is a
line. Tones go by form, a part at a time (see GROUND_LIGHT). The belly is a flat band on the neck's inner side.
The head is typed (HEAD) and joins the
neck with no line. The tail's thin end is colour alone. Draws the draft through the Aseprite pixel plugin;
the game's assets are not touched.

    python art/enemies/98_boiuna_pose_first.py look DIR   # PIL render only, for looking at
    python art/enemies/98_boiuna_pose_first.py [SCRATCH]  # check, draw the draft, write the review
"""
from pathlib import Path
import math, sys, tempfile
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff

THEIRS = ROOT / 'art/_backup/98_user_first_frame_20261013/boiuna_idle_source.png'
REFERENCE = ROOT / 'art/_backup/98_user_first_frame_20261013/boiuna_reference.png'
W, H = 192, 176
PAL = {'K': '000000',
       'D': '142e1f', 'M': '235436', 'L': '29633e',   # their greens: underside, body, the light
       'B': 'b29e5c', 'S': '605028',                  # belly, and its shade
       'Y': 'f0bc3c',                                 # the eyes
       'T': 'e8e0c0'}                                 # fangs and teeth
# their first frame's passes, tail tip to the last turn: curves (four points each, in that frame's pixels) and the thickness at each end
PASSES = [(((30, 44), (106, 15), (243, 67), (315, 45)), 2, 12), (((315, 45), (383, 23), (378, 100), (298, 97)), 12, 16),
          (((298, 97), (205, 105), (168, 65), (79, 81)), 16, 18), (((79, 81), (5, 85), (5, 148), (100, 140)), 18, 20),
          (((100, 140), (184, 123), (235, 139), (295, 119)), 20, 22), (((295, 119), (374, 91), (386, 181), (302, 181)), 22, 24),
          (((302, 181), (224, 186), (174, 148), (93, 160)), 24, 25), (((93, 160), (8, 173), (41, 223), (116, 208)), 25, 27),
          (((116, 208), (178, 192), (235, 226), (286, 207)), 27, 29), (((286, 207), (352, 185), (337, 254), (265, 245)), 29, 30)]
NARROW, SQUASH, TOP, THICK = 0.9, 0.33, 91, 0.30     # their passes: this share as wide about the middle, this share as tall, the tail's row, thickness
NECK = [(122, 160, 10.5), (113, 156, 11), (108, 146, 11.5), (106, 132, 12), (102, 112, 11.5), (94, 92, 11), (84, 72, 10.5), (75, 52, 10.5),
        (70, 35, 10.5), (72, 24, 10.5), (81, 19, 10.5), (94, 22, 10.5), (104, 34, 11), (110, 48, 11.5), (114, 62, 12)]   # from the front pass round and up in one wide bend (wider than the body is thick, so no crease), over, and down to the back of the head
THIN = 2.2                    # thinner than this the tail cannot hold a line with green inside it: colour alone
TICK = 7                      # a line inside the body shorter than this, joined to no other line, is not drawn
OVER = 40                     # two parts of the run this far apart along it and on one pixel: the one nearer the head is in front
# Tones by form, a part at a time (the bible: no lit band and dark band laid along every part):
#   the passes behind  flat body tone; dark only within SHADOW px of a part that lies over them
#   the front pass     nearest us on the ground: light where it faces up, dark underneath (GROUND_LIGHT, from above)
#   the neck           its back the dark side, the arch's top and the side toward us light (NECK_LIGHT, from the front right);
#                      the belly a flat pale band on its inner side, shaded under the arch. No scale strokes.
GROUND_LIGHT, NECK_LIGHT, SHADOW, EASE, TURN = (-0.45, -0.6, 0.66), (0.5, -0.5, 0.7), 2, 70, 30
BELLY = ((0, 1.0), (8, 1.0), (20, 0.72), (34, 0.4), (50, 0.22), (150, 0.3))   # along the neck (px from where it leaves the ground): the belly is the inner side past this share of the width -- it comes round into view in a long curve
HEAD_AT = (93, 65)            # where HEAD's first column and row go
HEAD = [                      # hanging, facing us and a little right; from just above the eyes down
    (0, '.........KDDMMLLLLLLLLLLLLLLLLLLLLLLK'),
    (1, '..........KDDMLLLLLLLLLLLLLLLLLLLLLLLK'),
    (2, '...........KKMLLLLLLLLLLLLLLLLLLLLLLLLK'),
    (3, '............KKKLLLLLLLLLLLLLLLLLLLLLLLK'),
    (4, '.............KKLLLLLLLYYLLLLLLLLLLLYYLK'),
    (5, '.............KKKLLLLLLYYYYLLLLLLLYYYLLK'),
    (6, '..............KKKLLLLLLLYYYLLLLLYYLLLKK'),
    (7, '...............KKKLLLLLLLLLLLLLLLLLLLKK'),
    (8, '...............KKKKLLLLLLLLDLLDLLLLLKKK'),
    (9, '................KKKKTLLLLLLLLLLLLLTKKKK'),
    (10, '.................KKKTKKLLLLLLLLLLKTKKKK'),
    (11, '.................KKKTKKKLLLLLLLLKKTKKKK'),
    (12, '..................KKKKKKTKKKTKKTKKTKKK'),
    (13, '..................KKKDDDTDDDTDDTDDDDKK'),
    (14, '...................KKDDTDDDDDDDDDTDKK'),
    (15, '....................KKDTDDDDDDDDDTDKK'),
    (16, '....................KKKTDDDDDDDDDDKK'),
    (17, '.....................KKDDDDDDDDDDDKK'),
    (18, '.....................KKKDDDDDDDDDKKK'),
    (19, '......................KKKTDDTDDTDKK'),
    (20, '.......................KKTDDTDDTKKK'),
    (21, '.......................KKKKKKKKKKK'),
    (22, '........................KKKKKKKKK'),
]
MOUTH = (121.5, 81.0)         # the middle of its open mouth, in frame pixels (the frame's middle is 96, 88)


path = ff.path                # a smooth line through (x, y, thickness) points, shared with 23 since 2026-10-14


def spine():
    """The run's points, tail tip to the back of the head, and how far along it the front pass and the neck start."""
    points = []
    for (p0, p1, p2, p3), r0, r1 in PASSES:
        for t in (0, 1 / 3, 2 / 3):
            u = 1 - t
            x, y = (u ** 3 * p0[c] + 3 * u * u * t * p1[c] + 3 * u * t * t * p2[c] + t ** 3 * p3[c] for c in (0, 1))
            points.append((96 + (x / 2 - 97) * NARROW, TOP + (y - 44) * SQUASH, max(0.8, THICK * (r0 + (r1 - r0) * t))))
    run = path(points + NECK)
    at = lambda p: min(run, key=lambda q: math.hypot(q[0] - p[0], q[1] - p[1]))[3]
    return run, (at(points[-6]), at(NECK[2]))                       # where the front pass starts, and where the neck leaves the ground


def tube(run, marks):
    """The run as pixels {(x, y): letter}, with the pixels too thin to carry a line."""
    (front, foot), end, near = marks, run[-1][3], {}
    for i, (cx, cy, r, along) in enumerate(run):                     # tail first: a part far enough on along the run takes
        if r < THIN:                                                 # a pixel from the part behind it; within a part, the nearest point
            n = max(1, round(2 * r - 0.6))                           # (the thin tail: a solid line this many pixels thick, not a disc,
            px, py = run[max(i - 1, 0)][:2]                          # and unbroken from the point before)
            for k in range(1, 5):
                x, mid = round(px + (cx - px) * k / 4), py + (cy - py) * k / 4
                for y in range(round(mid - (n - 1) / 2), round(mid - (n - 1) / 2) + n): near.setdefault((x, y), (1.0, i))
            continue
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                q = ((x - cx) ** 2 + (y - cy) ** 2) / (r * r)
                if q <= 1:
                    was = near.get((x, y))
                    if not was or along - run[was[1]][3] > OVER or q < was[0]: near[x, y] = (q, i)
    over = lambda along, o: o and run[o[1]][3] - along > OVER        # is the part on that pixel one that lies over this one?
    out, bare = {}, set()
    for (x, y), (q, i) in near.items():
        cx, cy, r, along = run[i]
        a, b = run[max(i - 2, 0)], run[min(i + 2, len(run) - 1)]
        n = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        tx, ty = (b[0] - a[0]) / n, (b[1] - a[1]) / n
        v = max(-1.0, min(1.0, ((x - cx) * -ty + (y - cy) * tx) / r))        # across the tube: -1 its left side going along, 1 its right
        lit = lambda light: -ty * v * light[0] + tx * v * light[1] + math.sqrt(1 - v * v) * light[2]
        beside = [near.get((x + dx, y + dy)) for dx, dy in ff.N4]
        if r < THIN: out[x, y] = 'M'; bare.add((x, y))
        elif any(not o or along - run[o[1]][3] > OVER for o in beside): out[x, y] = 'K'     # beside nothing, or beside a part it lies over
        elif any(over(along, near.get((x + dx, y + dy))) for dx in range(-SHADOW, SHADOW + 1) for dy in range(-SHADOW, SHADOW + 1)):
            out[x, y] = 'D'                                          # under a part that lies over it
        elif along < front: out[x, y] = 'M'
        else:
            w = max(0.0, min(1.0, (along - foot + TURN) / (2 * TURN)))                # round the bend the light turns from the ground's
            w = w * w * (3 - 2 * w)                                                   # to the neck's, so no tone stops at a line
            tone = lit([a + (b - a) * w for a, b in zip(GROUND_LIGHT, NECK_LIGHT)]) + 0.4 * max(0.0, 1 - (end - along) / 16)   # and the neck lightens into the head
            new = max(0.0, 1 - (along - front) / EASE)               # the front pass's light and dark widen from nothing over its first EASE px
            if foot <= along < end - 5 and v > belly_from(along - foot): out[x, y] = 'S' if tone < -0.05 else 'B'
            else: out[x, y] = 'L' if tone > 0.75 + 0.2 * new else 'D' if tone < 0.15 - 0.9 * new else 'M'
    return out, bare


def belly_from(along):
    for (a0, v0), (a1, v1) in zip(BELLY, BELLY[1:]):
        if along <= a1: return v0 + (v1 - v0) * max(0.0, along - a0) / (a1 - a0)
    return BELLY[-1][1]


def draw(run, marks, head=(0, 0)):
    """The frame from the run and where the head hangs: {(x, y): letter}, and the thin pixels drawn without a line."""
    g, bare = tube(run, marks)
    top = ff.grid([(y + HEAD_AT[1] + head[1], HEAD_AT[0] + head[0], row) for y, row in HEAD], PAL)
    g.update(top)
    bare -= set(top)
    for (x, y), c in list(g.items()):                                # the head joins the neck with no line: where it stands
        if c != 'K' and (x, y) not in bare and any((x + dx, y + dy) not in g for dx, dy in ff.N4): g[x, y] = 'K'   # proud of it, it is closed
    inside = {p for p, c in g.items() if c == 'K' and all((p[0] + dx, p[1] + dy) in g for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
    while inside:                                                    # a crease's line shorter than TICK px is a stray tick: body tone
        tick, stack = [], [inside.pop()]
        while stack:
            q = stack.pop(); tick.append(q)
            for o in ((q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if o in inside: inside.remove(o); stack.append(o)
        if len(tick) < TICK and not any(g.get((q[0] + dx, q[1] + dy)) == 'K' and (q[0] + dx, q[1] + dy) not in tick
                                        for q in tick for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            for q in tick: g[q] = 'M'
    for (x, y), c in list(g.items()):                                # the line is 1 px: black that touches no colour is not line
        if c == 'K' and all(g.get((x + dx, y + dy), 'K') == 'K' for dx in (-1, 0, 1) for dy in (-1, 0, 1)): del g[x, y]
    return g, bare


def frame():
    return draw(*spine())


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp())
    scratch.mkdir(parents=True, exist_ok=True)
    g, bare = frame()
    for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in bare, old='130 x 81 frame', cap=224, max_colours=25):
        print(' ', line, flush=True)
    im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / '98_boiuna_first_draft')
    if not look: ff.style_check(im, scratch, '98_boiuna_first', tier='giant')
    panels = [Image.open(THEIRS).convert('RGBA'), Image.open(REFERENCE).convert('RGBA'), im.resize((2 * W, 2 * H), Image.Resampling.NEAREST)]
    sheet = Image.new('RGBA', (sum(q.width for q in panels) + 16, max(q.height for q in panels) + 8), (0, 0, 0, 255))
    x = 4
    for q in panels: sheet.alpha_composite(q, (x, 4)); x += q.width + 4
    sheet.save(scratch / '98_look.png' if look else HERE / '98_review.png')
    print("left: their first frame; middle: the reference; right: the sprite at the game's 2x", flush=True)
