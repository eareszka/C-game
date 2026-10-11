"""25 Myrmecoleon, big tier: its five frames, from the user's frame.

    python art/enemies/25_myrmecoleon_design.py                       writes 25_myrmecoleon.txt and .json
    python art/enemies/25_myrmecoleon_design.py show OUT.png [OUT.gif]  its frames, enlarged

The ant-lion, seen from straight in front (the user, 2026-10-10: "have it directly front"). The
first pose was typed by hand (25_myrmecoleon_pose_first.py); the user then redrew its abdomen as
a great ball, its ears, eyes, nose and mouth, and asked: "have it idle breath and close mouth
and wag ant tail behind", then "have the mouth droll a little". Their frame
(25_myrmecoleon_user_frame.png) is frame 0, pixel for pixel but for the drool, and nothing in the
others is redrawn -- their pixels are moved:

  the tail wags   the ball leans left and right about the crown of the mane it rises behind
  it breathes     the whole of it sinks a pixel or two on its planted feet
  the mouth shuts rows of the open mouth are taken out and the jaw comes up under the teeth
  it drools       a white strand runs over the lower lip, lengthens, and lets a drop fall"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from flat_parts import write, N4
import flat_parts
W, H = 98, 79                                             # the built frame; row 0 stays empty
PAL = {'K': '000000', 'L': 'f4ce80', 'M': 'b2966a',       # the lion's hide: lit, shade (and the lit crown of the mane)
       'N': '94703d', 'n': '633e1b',                      # its mane: gold above, the dark ruff below
       'A': '792727', 'a': '5d1e1f',                      # the ant: its shell, and under each plate of it
       'R': 'b6433d', 'W': 'fcfcfc'}                      # tongue, and the light on the legs; teeth
LETTER = {v: k for k, v in PAL.items()}
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# what each of the five frames does (the game plays them 0..4 round and round, 260 ms each)
WAG = (0, 6, 4, -4, -6)                                   # the top of the ball, px to the right
SINK = (0, 1, 2, 1, 0)                                    # the body down on its feet, px
SHUT = (0, 0, 1, 2, 1)                                    # the mouth: open, half shut, shut

BALL = (1, 27, 30, 67)                                    # the abdomen above the mane: rows, columns; it leans about the row under it
JAW = (38, 59, 58)                                        # the face's columns, and the under-edge of the chin
GONE = {1: (52, 53), 2: (51, 52, 53, 54)}                 # the rows of the open mouth taken out, by how shut
MEND = {1: {(39, 52): 'K', (58, 52): 'K'},                # the face's edge closed again where the jaw came up ...
        2: {(39, 51): 'K', (40, 51): 'K', (57, 51): 'K', (58, 51): 'K', (43, 51): 'W', (54, 51): 'W'}}   # ... and the fang tips over the lip
LIP = {0: 55, 1: 53, 2: 51}                               # the lower lip's row, by how shut
DROOL = 52                                                # the column the strand hangs in, by the right fang
SPIT = ((2, 0), (3, 0), (4, 0), (2, 7), (1, 9))           # each frame: the strand's length under the lip; how far under the lip its fallen drop is
GIVEN = (67, 76)                                         # the rows given up as it sinks: one of the chest, then one of the toes

def user():
    from PIL import Image
    im = Image.open(os.path.join(HERE, '25_myrmecoleon_user_frame.png')).convert('RGBA'); assert im.size == (W, H), im.size
    return {(x, y): LETTER['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}

def ball(u):
    """The abdomen alone -- with what the crown's tufts hide of it filled in -- and which of it is seen."""
    fur = lambda p: u[p] in 'MN' or (u[p] == 'K' and any(u.get((p[0] + a, p[1] + b), '.') in 'MN' for a, b in N4))
    whole, seen = {}, set()
    for y in range(BALL[0], BALL[1] + 1):
        xs = [x for x in range(BALL[2], BALL[3] + 1) if (x, y) in u and not fur((x, y))]
        for x in range(min(xs), max(xs) + 1):
            whole[(x, y)] = 'a' if fur((x, y)) else u[(x, y)]
            if not fur((x, y)): seen.add((x, y))
    return whole, seen

def leaning(b, lean):
    """The ball with its top lean px to the right: each row slid, the lowest not at all."""
    return {(x + round(lean * (BALL[1] + 1 - y) / (BALL[1] + 1 - BALL[0])), y): c for (x, y), c in b.items()}

def mouth(u, shut):
    """The jaw brought up: the rows GONE are taken out of the face, chin and lip follow, the ruff fills in under the chin."""
    g = dict(u)
    if not shut: return g
    rows = range(GONE[shut][0], JAW[2] + 1); kept = [y for y in rows if y not in GONE[shut]]
    for x in range(JAW[0], JAW[1] + 1):
        for i, y in enumerate(rows): g[(x, y)] = u[(x, kept[i])] if i < len(kept) else 'n'
    g.update(MEND[shut])
    return g

def drool(g, f):
    """The strand over the lip and down the chin, and the drop that has left it (white: the sheet has no colour to spare)."""
    n, drop = SPIT[f]; lip = LIP[SHUT[f]]
    for y in [*range(lip, lip + n + 1)] + ([lip + drop, lip + drop + 1] if drop else []): g[(DROOL, y)] = 'W'
    return g

def sunk(g, d):
    """All of it d px lower on planted feet: a row is given up for each pixel."""
    old = [None] * d + [y for y in range(1, H) if y not in GIVEN[:d]]         # the row each new row is taken from
    return {(x, y): g[(x, o)] for y, o in zip(range(1, H), old) if o for x in range(W) if (x, o) in g}

def frame(f):
    u = user(); whole, seen = ball(u)
    g = leaning(whole, WAG[f])
    g.update({p: c for p, c in drool(mouth(u, SHUT[f]), f).items() if p not in seen})   # everything else, in front of the ball
    return sunk(g, SINK[f])

def FRAMES():
    fr = [frame(f) for f in range(5)]
    assert fr[0] == drool(user(), 0), 'frame 0 is not the user\'s frame and its drool'
    return fr

if __name__ == '__main__':
    fr = FRAMES()
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        cv = Image.new('RGBA', (W * len(fr) + 2 * (len(fr) - 1), H * 2 + 2), (40, 40, 40, 255))
        for i, g in enumerate(fr):
            cv.alpha_composite(image(g, (255, 170, 200, 255)), (i * (W + 2), 0)); cv.alpha_composite(image(g, (0, 0, 0, 255)), (i * (W + 2), H + 2))
        cv.resize((cv.width * 4, cv.height * 4), Image.NEAREST).save(sys.argv[2])
        if sys.argv[3:]:
            big = [image(g, (0, 0, 0, 255)).resize((W * 4, H * 4), Image.NEAREST) for g in fr]
            big[0].save(sys.argv[3], save_all=True, append_images=big[1:], duration=260, loop=0)
    else: write('25_myrmecoleon', fr, PAL, W, H)
    print(len(fr), 'frames, frame 0 = the user\'s | colours', sorted({c for g in fr for c in g.values()}), '| box', (min(p[0] for g in fr for p in g), min(p[1] for g in fr for p in g), max(p[0] for g in fr for p in g), max(p[1] for g in fr for p in g)))
