"""48 Bjarndyrakongur, giant tier: the polar bear king with the horn, seen from the front only, from the user's frame.

    python art/enemies/48_bjarndyrakongur_design.py          writes 48_bjarndyrakongur.txt/.json
    python art/enemies/48_bjarndyrakongur_design.py check    which rows it can lose or repeat without opening its outline

The user drew it standing, 57x136, in Aseprite (art/enemies/48_bjarndyrakongur_keys_draft_user1.aseprite,
exported as 48_bjarndyrakongur_user_frame.png) and chose (2026-10-11): giant, as drawn; front only; the stray
off-palette pixel at (16, 113) removed; an idle that breathes, moves the paw on its belly, and twinkles the star.

Frame 0 is their drawing, pixel for pixel. The other eleven frames move its pixels (RISE, SWAY) and grow or shrink
the star by its own ring (STAR); nothing else is drawn."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 64, 142                                            # the frame; row 0 stays empty
OX, OY = 38, 30                                           # where the frame sits on the user's canvas
PAL = {'K': '000000', 'W': 'fcfcfc', 'C': 'bcbeca',       # outline; fur in the light, fur turned away
       'O': 'fc9838', 'R': 'b6433d',                      # the ear flaps and the horn: lit, in shadow
       'Y': 'fae488'}                                     # the star's rim
LETTER = {v: k for k, v in PAL.items()}
STRAY = (16, 113)                                         # off-palette c4d7db, by itself left of the bear: the user said remove it

# the idle: twelve frames played straight through, 162 ms each
RISE_ROWS = (136 - OY, 129 - OY)                          # plain rows of the trunk, repeated to lift all above them: the breath
ARM = (52 - OX, 97 - OY, 80 - OX, 120 - OY)               # the forearm across its belly and the paw: x0, y0, x1, y1 (the hanging arm's line at x 82 is outside)
HANG = (82 - OX, 103 - OY, 127 - OY)                      # the hanging arm: from its line at x 82 rightwards, shoulder row to paw row
STAR = (70 - OX, 38 - OY)                                 # the star's middle: a diamond 3 across, W inside a Y rim
RISE = (0, 1, 1, 2, 2, 2, 1, 1, 0, 0, 0, 0)               # breath in and out
SWAY = (0, 0, 1, 1, 1, 0, 0, -1, -1, -1, 0, 0)           # both hands, the same way at once, with the breath: a pixel at the paw (+ to our right); "more subtle" (user)
TWINK = (0, 0, 1, 1, 0, 2, 2, 0, 0, 1, 0, 1)              # the star: 0 as drawn, 1 a ring smaller, 2 a pixel ray out at its top and sides
TUFTS = ((59 - OX, -1), (80 - OX, 1))                     # the orange-and-red tufts either side of the head: the column against the head's line, and outward
TUFT_ROWS = (67 - OY, 78 - OY)                            # their root row (still) to their fringe (moves most)
FLAP = (0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0)               # both tufts flare a pixel at the fringe, as subtle as the hands (user), once a hand swing
# its breath, seen in the cold (user: "have breath blow out the mouth since its cold"): a puff from under its mouth
# (the line at x 69-73, row 74) on the out-breath, drifting off to our left past the tuft and thinning to nothing.
# The one thing drawn here that is not the user's: pale vapour 'i' with a soft rim 'e', no black line round it.
PAL.update({'i': 'c6ccda', 'e': 'a4aaba'})
PUFFS = (None,
         (69 - OX, 75 - OY, ['.eee.',
                             'eiiie',
                             'eiiie',
                             '.eee.']),
         (60 - OX, 74 - OY, ['..eee..',
                             '.eiiie.',
                             'eiiiiie',
                             'eiiiiie',
                             '.eiiie.',
                             '..eee..']),
         (49 - OX, 71 - OY, ['...ee.....',
                             '..eiie.ee.',
                             '.eiiiieiie',
                             'eiiiiiiiie',
                             'eiiiiiiiie',
                             '.eiiiiiie.',
                             '..eeeeee..']),
         (43 - OX, 69 - OY, ['..ee......',
                             '.eiie.....',
                             'eiiie..ee.',
                             '.eee..eiie',
                             '......eiie',
                             '.......ee.']),
         (40 - OX, 67 - OY, ['.e....',
                             'eie...',
                             '.e..e.',
                             '....e.']))
PUFF = (0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0)               # out on the out-breath (RISE coming down), gone by the rest

def user_frame():
    """The front as the user saved it, moved into the frame: {pixel: letter}."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '48_bjarndyrakongur_user_frame.png')).convert('RGBA')
    g = {(x, y): '%02x%02x%02x' % im.getpixel((x, y))[:3] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
    assert g.pop(STRAY) == 'c4d7db'
    return {(x - OX, y - OY): LETTER[c] for (x, y), c in g.items()}

def rise(g, n):
    """n pixels higher above the trunk: for each of the first n RISE_ROWS, all above it goes up one and the row is there twice."""
    for r in RISE_ROWS[:n]: g = {**{(x, y - 1): c for (x, y), c in g.items() if y <= r}, **{p: c for p, c in g.items() if p[1] >= r}}
    return g

def sway(g, dx):
    """Both hands dx pixels over. The forearm on its belly (its lines, and the fur between them) slides whole, the
    fur behind closing in; the hanging arm swings from the shoulder, sheared row by row, dx at the paw."""
    if not dx: return g
    x0, y0, x1, y1 = ARM
    line = {p for p, c in g.items() if c == 'K' and x0 <= p[0] <= x1 and y0 <= p[1] <= y1}
    unit = set(line)
    for x in {p[0] for p in line}:                        # between the forearm's top line and its bottom one, column by column
        ys = [p[1] for p in line if p[0] == x]
        unit |= {(x, y) for y in range(min(ys), max(ys) + 1)}
    out = dict(g)
    side = -1 if dx > 0 else 1                            # the fur behind it is on the side it leaves
    for x, y in unit:
        out[(x, y)] = next(g[(fx, y)] for fx in range(x + side, x + side * 40, side) if (fx, y) not in unit and g.get((fx, y)) not in ('K', None))
    for x, y in unit: out[(x + dx, y)] = g[(x, y)]
    hx, top, bot = HANG
    # each row of it from its own line rightwards -- not the body's edge where the paw hangs free of it
    start = {y: next(x for x in range(hx, hx + 12) if g.get((x, y)) == 'K' and (x + 1, y) in g) for y in range(top, bot + 1)}
    arm = {p for p in g if top <= p[1] <= bot and p[0] >= start[p[1]]}
    shift = lambda y: round(dx * (y - top) / (bot - top))
    left = set()
    for x, y in arm:                                      # what it leaves: the body, where the arm lay over it; else nothing
        if not shift(y): continue
        behind = g.get((start[y] - 1, y))                 # swung right: the body beside its line, if the arm lay over it here
        if x - start[y] < shift(y) and behind: out[(x, y)] = behind; left.add((x, y))
        else: del out[(x, y)]
    for x, y in arm:
        if shift(y): out[(x + shift(y), y)] = g[(x, y)]
    moved = left | {(x + shift(y), y) for x, y in arm}   # where the shear steps out past the row above, and body left at the gap's edge:
    for p in moved:                                       # the colour there takes the outline, as the rest of the edge has it
        if p in out and out[p] != 'K' and any(flat_parts.add(p, d) not in out for d in flat_parts.N4): out[p] = 'K'
    return out

def flap(g, n):
    """Both tufts n pixels out at the fringe, hinged at the root: each row sheared outward, the column against the
    head staying where it is (so the tuft stretches, no gap); where the fringe's colour comes out onto nothing, the
    outline comes out with it."""
    if not n: return g
    top, bot = TUFT_ROWS
    out = dict(g)
    moved = set()
    for ci, d in TUFTS:
        for y in range(top, bot + 1):
            s = round(n * (y - top) / (bot - top))
            if not s: continue
            row = {x: g[(x, y)] for x in range(ci, ci + d * 12, d) if (x, y) in g}
            for x in row:
                if x != ci: del out[(x, y)]
            for x, c in row.items(): out[(x + d * s, y)] = c; moved.add((x + d * s, y))
    for p in moved:
        if out[p] != 'K':
            for q in (flat_parts.add(p, e) for e in flat_parts.N4):
                if q not in out: out[q] = 'K'
    return out

def puff(g, n):
    """Its breath, puff n of PUFFS, in front of everything."""
    if not n: return g
    x0, y0, rows = PUFFS[n]
    return {**g, **flat_parts.grid(x0, y0, rows)[0]}

def twinkle(g, s):
    """The star a ring smaller (1) or with a ray out at its top and sides (2); the ring is the user's rim colour."""
    if not s: return g
    sx, sy = STAR
    d = lambda p: abs(p[0] - sx) + abs(p[1] - sy)
    out = dict(g)
    if s == 1:
        for p in [p for p in g if d(p) == 3 and p[1] <= sy + 2]: del out[p]   # the outer rim goes (not the horn tip under it)
        for p in [p for p in g if d(p) == 2]: out[p] = 'Y'
    else:
        for p in ((sx, sy - 4), (sx - 4, sy), (sx + 4, sy)): out[p] = 'Y'
    return out

def bare(g):
    """Colour with nothing beside it: where the outline is open."""
    return {p for p, c in g.items() if c not in 'KYie' and any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}

def FRAMES():
    p = user_frame()
    fs = [rise(puff(flap(sway(twinkle(p, s), a), t), b), r) for r, a, s, t, b in zip(RISE, SWAY, TWINK, FLAP, PUFF)]
    assert fs[0] == p                                     # the user's frame is frame 0
    for i, f in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in f), i
        assert len(bare(f)) <= len(bare(p)), (i, sorted(bare(f) - bare(p)))     # no move opens the outline
        assert f != fs[i - 1], i                          # each frame moves
        assert set(f.values()) <= set(PAL), i
    return fs

def numbers(g):
    """What the bible measures, of one frame."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'open edge': sorted(bare(g))}

if __name__ == '__main__':
    p = user_frame()
    if sys.argv[1:2] == ['check']:
        base = len(bare(p))
        print('open at rest', sorted(bare(p)))
        print('trunk rows that can be repeated', [r for r in range(90, 135) if len(bare({**{(x, y - 1): c for (x, y), c in p.items() if y <= r}, **{q: c for q, c in p.items() if q[1] >= r}})) <= base])
    else:
        fr = FRAMES()
        for k, v in numbers(fr[0]).items(): print('%-18s %s' % (k, v))
        flat_parts.write('48_bjarndyrakongur', fr, PAL, W, H, dirs='down', view='D', rows_sheet=True)
