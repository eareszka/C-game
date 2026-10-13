"""71 Namungumi, big tier: the cloaked beast of Lake Malawi, seen from the front only, from the user's frame.

    python art/enemies/71_namungumi_design.py          writes 71_namungumi.txt/.json and 71_namungumi_flash.txt/.json
    python art/enemies/71_namungumi_design.py check    which rows and columns it can lose or bend at without opening its outline

The user (2026-10-11): "have it only have front and front 3/4s sprite. make sure the eyes are still
subject to lasers shooting from them. follow bible make no mistakes and no shapes" -- and, asked:
one glowing eye, every beam leaving from it. Two poses were typed (71_namungumi_pose_first.py) and
put in the old sheet's own colours; they redrew the front in Aseprite; a 3/4 view was typed again
after it; and then: "have it only ever face front but long animation for breathing and moving. eyes
flash and turn pure white before turning into lasers as a warning".

So there is one view, the front, and their drawing (71_namungumi_user_front.png) is frame 0 of it,
pixel for pixel. The other eleven frames move its pixels and draw nothing (RISE, WIDE, STEP, SWAY).
A second sheet, 71_namungumi_flash, is the same twelve frames with the eye pure white: the fight
shows it (Namungumi::alt_pose) flashing, then held, before each beam leaves.

Every beam leaves from its eye (Namungumi::eye in src/enemies.cpp), so the pupil is one pixel, EYE,
that no frame moves."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the frame, as the old sheet's; row 0 stays empty
PAL = {'K': '000000', 'D': '14101e', 'L': '2b1f40',       # outline, and the pupil; its hide, and where it is lit (and the glow round its eye)
       'w': 'c6ccda',                                     # its pale veins; its claws and fangs
       'r': '792727', 'R': 'b6433d',                      # the skirt and the gums: in shadow, and in the light
       'W': 'fcfcfc', 'C': 'bcbeca'}                      # the eye's white; the fangs' shaded side
LETTER = {v: k for k, v in PAL.items()}
EYE = (49, 42)                                            # the pupil: where its beams leave from
EYE_BOX = (47, 40, 51, 44)                                # the eye with the glow round it: all of this goes white on the flash sheet
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# the idle: twelve frames played straight through, 162 ms each -- a long breath, then it shifts its feet
RISE_ROWS = (35, 34)                                      # rows of the cloak, above the eye, repeated to lift its crest: the first, then the second as well
WIDE_COLS = (40, 58)                                      # a column either side of the eye, repeated to spread it as it fills
LEGS = ((21, 31, 55), (67, 77, 58))                       # each leg, the one to our left and the one to our right: its columns, and the row taken out of it to lift that foot a pixel
SWAY_FROM = 56                                            # from this row down, all of it slides when it shifts its weight
RISE  = (0, 1, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0)              # breath in: its crest up a pixel, two on frame 2 (the frame the fight rings on)...
WIDE  = (0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0)              # ...then it spreads a pixel each side, and lets it out
STEP  = (0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 2, 0)              # then its feet: 1 the left one lifted, 2 the right
SWAY  = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, -1)             # and its weight over to one side, back, and to the other

def user_front():
    """The front view as the user saved it: {pixel: letter}."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '71_namungumi_user_front.png')).convert('RGBA'); assert im.size == (W, H), im.size
    return {(x, y): LETTER['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}

def rise(g, n):
    """Its crest n pixels higher: for each of the first n RISE_ROWS, all above that row goes up one and the row is there twice."""
    for r in RISE_ROWS[:n]: g = {**{(x, y - 1): c for (x, y), c in g.items() if y <= r}, **{p: c for p, c in g.items() if p[1] >= r}}
    return g

def wide(g, on):
    """A pixel wider each side: all left of the first WIDE_COLS goes left one, all right of the second goes right one, each column there twice."""
    if not on: return g
    a, b = WIDE_COLS
    return {**{(x - 1, y): c for (x, y), c in g.items() if x <= a}, **{(x + 1, y): c for (x, y), c in g.items() if x >= b}, **{p: c for p, c in g.items() if a <= p[0] <= b}}

def step(g, leg):
    """One foot lifted a pixel: a row is taken out of that leg's columns and what is under it comes up."""
    if not leg: return g
    x0, x1, row = LEGS[leg - 1]
    mine = lambda p: x0 <= p[0] <= x1 and p[1] >= row
    return {**{p: c for p, c in g.items() if not mine(p)}, **{(x, y - 1): c for (x, y), c in g.items() if mine((x, y)) and y > row}}

def sway(g, dx):   return {(x + dx * (y >= SWAY_FROM), y): c for (x, y), c in g.items()}

def flash(g):
    """The eye pure white: pupil, white and glow alike."""
    x0, y0, x1, y1 = EYE_BOX
    return {p: 'W' if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and c in 'KWL' else c for p, c in g.items()}

def bare(g):
    """Colour with nothing beside it: where the outline is open."""
    return {p for p, c in g.items() if c != 'K' and any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}

def FRAMES():
    p = user_front()
    fs = [sway(step(wide(rise(p, r), w), s), d) for r, w, s, d in zip(RISE, WIDE, STEP, SWAY)]
    assert fs[0] == p                                     # the user's frame is frame 0
    for i, f in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in f), i
        assert len(bare(f)) <= len(bare(p)), (i, sorted(bare(f) - bare(p)))     # no move opens the outline
        assert f != fs[i - 1], i                          # each frame moves
        assert f[EYE] == 'K' and all(f[flat_parts.add(EYE, d)] == 'W' for d in flat_parts.N4), i   # the pupil is where it was, in its white
        assert all(f.get((x, y)) == p.get((x, y)) for x in range(EYE_BOX[0], EYE_BOX[2] + 1) for y in range(EYE_BOX[1], EYE_BOX[3] + 1)), i   # and so is the rest of the eye
    return fs

def numbers(g):
    """What the bible measures, of one frame."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'open edge': sorted(bare(g))}

if __name__ == '__main__':
    p = user_front()
    if sys.argv[1:2] == ['check']:
        base = len(bare(p)); ok = lambda f: len(bare(f)) <= base
        print('open at rest', sorted(bare(p)))
        print('veins in each column (a column to repeat should hold few):', {x: sum(1 for (px, y), c in p.items() if px == x and c == 'w') for x in list(range(33, 46)) + list(range(53, 66))})
        print('veins in each row above the eye:', {y: sum(1 for (x, py), c in p.items() if py == y and c == 'w') for y in range(32, 40)})
        for x0, x1, _ in LEGS:
            print('leg', (x0, x1), 'can lose row', [r for r in range(51, 60) if ok({**{q: c for q, c in p.items() if not (x0 <= q[0] <= x1 and q[1] >= r)}, **{(x, y - 1): c for (x, y), c in p.items() if x0 <= x <= x1 and y > r}})])
        print('can slide from row down', [r for r in range(50, 62) if all(ok({(x + d * (y >= r), y): c for (x, y), c in p.items()}) for d in (1, -1))])
    else:
        fr = FRAMES()
        for k, v in numbers(fr[0]).items(): print('%-18s %s' % (k, v))
        flat_parts.write('71_namungumi', fr, PAL, W, H, dirs='down', view='D')
        flat_parts.write('71_namungumi_flash', [flash(f) for f in fr], PAL, W, H, dirs='down', view='D')
