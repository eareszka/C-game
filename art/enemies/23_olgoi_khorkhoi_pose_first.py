"""Enemy 23 Olgoi-Khorkhoi, the Mongolian death worm: its first frame, the front view, to art/direction/SPRITE_STYLE.md.

Drawn to the user's reference (art/_backup/23_reference_20261014/death_worm_reference.jpg, 2026-10-14: "pose and
design", "a few, 4-6" feelers): the ringed body rears up on its tail -- the tail lies along the ground under
the arch, the body rises on the right, arches high over the top and comes down on the left behind the head, which
lunges at us -- a maw split into four toothed petals round a mouth, a crown of whip feelers behind it, a long barbed
spine out of each side, one feeler trailing down to the left. Out of the sand since 2026-10-19 (the user: being in
the sand "makes it very different from the rest"); the sand version is in art/_backup/23_sand_20261019. Red, giant, in the old sheet's 140x83 frame at about the old height (the
first drawing, a ring maw on a straight neck, is in art/_backup/23_ring_pose_20261014).

Drawn flat, as the bible asks: the body is one beaded tube on a hand-set spine (SPINE: its thickness dips every
PERIOD px along it, so the segments read as beads in the silhouette, not as a ring pattern), toned by form from the
light (LIGHT3); each petal of the maw is a hand-set edge list (PETALS) filled by rule -- a lit lip two pixels inside
the line, the dark lining within, a tooth every third pixel along each lip; the spines and feelers are set
down round the head. Parts are layered back to
front by tools/flat_parts (a 'solid' part takes its own black edge where thick enough; parts in front interrupt the
parts behind, one shared line; thin whips carry a line on their shadow side only, as the bible allows thin parts).

Nothing in assets/ or src/ is touched. The draft goes through the Aseprite pixel plugin.

    python art/enemies/23_olgoi_khorkhoi_pose_first.py look [SCRATCH]   # PIL render only, for looking at
    python art/enemies/23_olgoi_khorkhoi_pose_first.py [SCRATCH]        # check, draw the draft, write the review
"""
from pathlib import Path
import math, sys, tempfile
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import first_frame as ff
import flat_parts

OLD = ROOT / 'assets/enemies/23_olgoi_khorkhoi.png'
REFERENCE = ROOT / 'art/_backup/23_reference_20261014/death_worm_reference.jpg'
W, H = 225, 112               # 140x83 until 2026-10-19: the body now runs down-right and off the frame's right edge (the sheet's, the screen's)
OFF = 40                      # how far past the right edge the tube is drawn before it is cut there, so it has no edge of its own
PAL = {'K': '000000',
       'D': '792727', 'M': 'b6433d', 'L': 'ec8476',   # the worm: under and away, the body of it, lit
       'm': '421618',                                 # inside the mouth (dark red, never black: black is a hole on the battle floor)
       'S': 'e8e0c0', 's': 'b29e5c',                  # spines, teeth and drops, their shade -- and the sand's shade
       'T': 'd0c078'}                                 # the sand
LIGHT3 = (-0.6, -0.8, 0.45)   # where the light comes from: up, to the left, and a little from us
MOUTH = (51, 50)              # the middle of the mouth, frame pixels -- for the fight's shots later
MAW = MOUTH

# The body: one tube on this spine, (x, y, radius), from the tail's tip curled up at the far right, back along the
# ground and up the right, over, and down on the left to the back of the head (its end is under the head).
TAIL = [(240, 67, 8.5), (224, 72.5, 8.5), (216, 76, 8.5),   # the rest of the body, from off the right edge: its course and
        (208, 79.5, 8.0), (200, 82, 9.0), (192, 84.5, 10.5),     # thickness fitted to the user's hand-drawn shape (their sketch,
        (184, 88, 11.0), (176, 90.5, 11.5), (168, 90.5, 11.5),   # then their reshape, 2026-10-19), thinning as it rises off the
        (160, 88, 13.0), (152, 84.5, 13.0), (140, 79, 14.0),    # screen, down-right out of the arch's leg
        (128, 71.5, 15.5)]
SPINE = TAIL + [(118, 63, 16.0), (118, 58, 16.0), (117, 52, 16.0), (114, 42, 15.5), (109, 33, 15.0), (101, 25, 14.5),
         (91, 20, 14.0), (80, 18, 14.0), (69, 20, 14.0), (59, 25, 14.5), (52, 32, 15.0), (48, 40, 15.5), (46, 48, 16.0)]
PERIOD, DEPTH = 11.0, 3.0     # a segment every this far along the spine; the groove between two is this much thinner
STROKE = 4                    # the grooves' strokes: this many black pixels in from each edge

# The head, lunging at us: its left and top are at HEAD in the frame; the maw's centre is at (21, 20) of it.
HEAD = (30, 30)
RING = (21, 20)               # the mouth: throat, a ring of teeth, the dark rim the petals grow from
# Each petal of the maw as hand-set edges: 'y' lobes (the top and bottom ones) as row -> (left, right), 'x' lobes
# (left and right) as column -> (top, bottom); the two lip tones (first edge, second edge), lit from the upper left.
PETALS = [
    ('y', {0: (16, 17), 1: (15, 19), 2: (14, 20), 3: (13, 22), 4: (12, 23), 5: (12, 24), 6: (12, 25), 7: (12, 25), 8: (12, 25),
           9: (12, 25), 10: (12, 25), 11: (13, 26), 12: (13, 26), 13: (14, 26)}, ('L', 'M')),
    ('x', {0: (18, 19), 1: (17, 21), 2: (16, 22), 3: (15, 24), 4: (15, 25), 5: (14, 26), 6: (14, 26), 7: (14, 27), 8: (14, 27),
           9: (14, 27), 10: (14, 27), 11: (14, 28), 12: (15, 28)}, ('L', 'M')),
    ('x', {43: (22, 23), 42: (21, 25), 41: (20, 26), 40: (18, 27), 39: (17, 28), 38: (16, 29), 37: (16, 29), 36: (15, 29),
           35: (15, 29), 34: (15, 29), 33: (15, 29), 32: (15, 28), 31: (14, 28), 30: (14, 28)}, ('M', 'D')),
    ('y', {41: (24, 25), 40: (23, 27), 39: (22, 28), 38: (20, 29), 37: (19, 30), 36: (18, 31), 35: (18, 31), 34: (17, 31),
           33: (17, 31), 32: (16, 31), 31: (16, 30), 30: (16, 30), 29: (15, 30), 28: (15, 30), 27: (15, 30)}, ('M', 'D')),
]
# The barbed spines out of each side of the head: root (under the side petal), tip, thickness at the root.
HORNS = [((32, 49), (4, 43), 3.5), ((70, 50), (110, 42), 3.5)]
# The feelers: whips from behind the head's top, as points, thick at the root and thin at the tip; and one trailing
# down to the left from under the head.
FEELERS = [[(45, 34), (38, 26), (28, 18), (16, 14), (7, 18)], [(48, 32), (44, 22), (36, 12), (25, 6), (14, 8)],
           [(52, 32), (55, 22), (52, 12), (44, 5), (33, 4)], [(42, 37), (31, 33), (19, 30), (9, 33), (4, 39)],
           [(56, 34), (63, 25), (66, 15), (62, 6)]]
TRAIL = [(52, 67), (40, 70), (28, 72), (18, 75), (11, 78)]   # from under the bottom petal


def tube():
    """The body: pixels toned by form -- the light where the tube's surface faces up, left and us, the dark where
    it turns under or away -- its thickness dipping DEPTH every PERIOD px along the spine (the beads). Every pixel
    belongs to the spine point nearest it, so the grooves between beads are cut as set. Also returns the grooves'
    strokes: two black pixels in from the lit edge at each one."""
    body = SPINE[len(TAIL):]                                        # the approved body, sampled exactly as it was...
    tail = ff.path(TAIL + body[:1])                                 # ...and the tail up to where it met the sand, its beads counted back from there
    run = [(x, y, r, s - tail[-1][3]) for x, y, r, s in tail[:-1]] + [tuple(q) for q in ff.path(body)]
    bead = lambda s: DEPTH * (1 - math.cos(2 * math.pi * s / PERIOD)) / 2
    cand = {(x, y) for cx, cy, r, s in run for y in range(int(cy - r - 1), int(cy + r + 2)) for x in range(int(cx - r - 1), int(cx + r + 2))}
    px, ticks = {}, set()
    across = lambda i: (lambda a, b: (lambda n: ((b[0] - a[0]) / n, (b[1] - a[1]) / n))(math.hypot(b[0] - a[0], b[1] - a[1]) or 1))(run[max(i - 2, 0)], run[min(i + 2, len(run) - 1)])
    tone = lambda tx, ty, v: (lambda lit: 'L' if lit > 0.62 else 'D' if lit < 0.12 else 'M')(-ty * v * LIGHT3[0] + tx * v * LIGHT3[1] + math.sqrt(1 - v * v) * LIGHT3[2])
    for x, y in cand:
        i = min(range(len(run)), key=lambda i: (x - run[i][0]) ** 2 + (y - run[i][1]) ** 2)
        cx, cy, r, s = run[i]
        re = r - bead(s)
        if (x - cx) ** 2 + (y - cy) ** 2 > re * re: continue
        tx, ty = across(i)
        v = max(-1.0, min(1.0, ((x - cx) * -ty + (y - cy) * tx) / re))
        px[x, y] = tone(tx, ty, v)
    for i, (cx, cy, r, s) in enumerate(run):                        # the grooves' strokes, in from both edges
        if abs((s + PERIOD / 2) % PERIOD - PERIOD / 2) > 0.5 or bead(s) < DEPTH * 0.9: continue
        tx, ty = across(i)
        re = r - bead(s)
        for side in (-1, 1):
            for k in range(1, STROKE + 1): ticks.add((round(cx + -ty * side * (re - k)), round(cy + tx * side * (re - k))))
    return px, ticks


def ring(turn=0.0):
    """The mouth: the throat, a ring of teeth in it (turned `turn` degrees), and the dark rim round it that the
    petals grow from."""
    cx, cy = HEAD[0] + RING[0], HEAD[1] + RING[1]
    px = {}
    for y in range(cy - 10, cy + 11):
        for x in range(cx - 10, cx + 11):
            r = math.hypot(x - cx, y - cy)
            if r > 9.6: continue
            a = (math.degrees(math.atan2(y - cy, x - cx)) - turn) % 360
            tooth = 4.2 < r <= 6.5 and min(abs((a - k * 45 + 180) % 360 - 180) for k in range(8)) < 12
            px[x, y] = 'S' if tooth else 'm' if r <= 6.5 else 'D'
    return px


def petal(along, edges, lip):
    """A lobe of the maw from its edges: the lip two pixels inside the line (the line itself comes from the layering),
    the mouth's dark lining within, a tooth every third pixel along each lip, the two lips' teeth staggered."""
    px = {}
    for k, (a, b) in edges.items():
        for i in range(a, b + 1):
            d, first = min(i - a, b - i), i - a < b - i
            p = (HEAD[0] + i, HEAD[1] + k) if along == 'y' else (HEAD[0] + k, HEAD[1] + i)
            if d <= 3: px[p] = lip[0] if first else lip[1]
            elif d in (4, 5) and (k % 3 == 0 if first else k % 3 == 1): px[p] = 'S'
            else: px[p] = 'D'
    return px


def horn(root, tip, w0):
    """A barbed spine: bone, shaded on its underside, a barb up off its top edge every few pixels."""
    (ax, ay), (bx, by) = root, tip
    n = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / n, (by - ay) / n
    px = {}
    for p in flat_parts.stroke(root, tip, w0, 1.2):
        s = (p[0] - ax) * -uy + (p[1] - ay) * ux           # across: below the axis is positive (y down)
        px[p] = 's' if s > 0.4 else 'S'
    nx, ny = (-uy, ux) if ux < 0 else (uy, -ux)              # across it, upward
    barbs = {}
    for k in range(4, int(n * 0.7), 5):                     # along the thick part only; the tip is bare
        t = k / n
        x, y = ax + ux * k, ay + uy * k
        w = (w0 + (1.2 - w0) * t) / 2
        barbs[round(x + nx * (w + 0.6)), round(y + ny * (w + 0.6))] = 'S'    # one pixel up off the top edge
    return px, barbs


def whip(points, w0, w1):
    """A feeler: a thin whip, mid tone, with the line on its shadow side only (right and under)."""
    px = {p: 'M' for p in flat_parts.run(*[(p, w0 + (w1 - w0) * i / (len(points) - 1)) for i, p in enumerate(points)])}
    for (x, y) in list(px):
        for q in ((x + 1, y), (x, y + 1)): px.setdefault(q, 'K')
    return px


def parts():
    """The frame's parts, back to front: [(name, pixels, kind)], and the body's groove strokes."""
    body, ticks = tube()
    out = [('body', body, 'solid')]
    out += [(f'feeler{i}', whip(f, 2.4, 1.0), 'raw') for i, f in enumerate(FEELERS)] + [('trail', whip(TRAIL, 3.0, 1.2), 'raw')]
    for i, (root, tip, w0) in enumerate(HORNS):
        bone, barbs = horn(root, tip, w0)
        out += [(f'horn{i}', bone, 'solid'), (f'barbs{i}', barbs, 'raw')]
    out += [('ring', ring(), 'solid')] + [(f'petal{i}', petal(*p), 'solid') for i, p in enumerate(PETALS)]
    return out, ticks


def layer(named):
    """Those parts laid down: the frame, the colour pixels drawn without a line of their own, and which part
    each pixel of the frame belongs to."""
    as_rows = lambda px: [(y, x, c) for (x, y), c in px.items()]
    g, thin = ff.layered([(as_rows(px), kind) for name, px, kind in named], PAL, W + OFF, H)
    g = {p: c for p, c in g.items() if p[0] < W}                    # cut at the right edge: the body runs on out of view
    owner = {}
    for name, px, kind in named:
        for p in px:
            if p[0] < W: owner[p] = name
    return g, thin, owner


def frame():
    """The frame {(x, y): letter} and the colour pixels drawn without a line of their own."""
    named, ticks = parts()
    g, thin, owner = layer(named)
    for p in ticks:                                                 # the grooves' strokes, where the body still shows
        if owner.get(p) == 'body' and g.get(p) in 'DML': g[p] = 'K'
    return g, thin


if __name__ == '__main__':
    look = sys.argv[1:2] == ['look']
    scratch = Path(sys.argv[2] if look else sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp())
    scratch.mkdir(parents=True, exist_ok=True)
    g, thin = frame()
    assert g.get(MOUTH) == 'm', 'MOUTH is not inside the mouth'
    assert ff.pieces(set(g)) == 1, 'the drawing is in pieces'
    for line in ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin, old='140x83 frame, worm 120x65 (132x74 with the sand)', right_open=True,
                          cap=224, max_colours=24):
        print(' ', line, flush=True)
    ys = [y for x, y in g]
    assert 60 <= max(ys) - min(ys) + 1 <= 108, 'not about the old height'
    im = ff.image(g, PAL, W, H) if look else ff.draft(g, PAL, W, H, HERE / '23_olgoi_khorkhoi_frame0_draft')
    if not look: ff.style_check(im, scratch, '23_olgoi_khorkhoi_first', tier='giant')
    old = Image.open(OLD).convert('RGBA').crop((0, 0, W, H))
    ff.review([('old front', old), ('new', im), ('silhouette', ff.silhouette(im)), ('player', ff.player())],
              scratch / '23_look.png' if look else HERE / '23_review.png', scale=4)
    print('review: old front, the new frame, its silhouette, the player, at 4x on black', flush=True)
