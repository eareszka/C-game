"""22 Cactus Cat, medium tier: its one 3/4 view, from the user's frame.

    python art/enemies/22_cactus_cat_design.py                 writes 22_cactus_cat.txt and .json
    python art/enemies/22_cactus_cat_design.py show OUT.png    the frame as built from, enlarged, beside the user's
    python art/enemies/22_cactus_cat_design.py check           each frame as letters, and any hide left without its outline

A first sitting pose was typed by hand (22_cactus_cat_pose_first.py); the user then redrew it --
green all over, eyes shut, a flower on each tip of the tail -- and asked (2026-10-11): "make it
slightly smaller and have the palletes match and pass the test". Their drawing
(22_cactus_cat_user_frame.png) is kept pixel for pixel but for this:

  smaller   three rows and one column are taken out, each chosen so that every pixel in it is
            repeated beside it and nothing of theirs is lost (TAKEN, below): the stems of the
            tail a pixel shorter, the body and the legs a pixel each, the tail a pixel nearer.
            It was 39x35 and used the frame's top row, which the build keeps empty; it is 38x32.
  palette   nothing to change: its five colours are all on the game palette already.

Then (2026-10-11): "make the movement be more smooth, have the cactus tail sway as well". So the
idle is eight frames played straight through, not the build's three: frame 0 is the pose above
and every other frame moves its pixels, one thing a pixel at a time (SWAY, BREATH).

It stays put in its fight and its rings and spines leave from the middle of the frame (class
CactusCat has no art coordinates), so the frame is cut to put the cat's body on that point."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
PAL = {'K': '000000', 'G': '4fa667', 'g': '2c6c44',       # outline; its hide, and the far side of it
       'I': 'e8e0c0', 'P': 'ec8476'}                      # chest, forelegs, blades and spines; flowers, ears, cheeks
LETTER = {v: k for k, v in PAL.items()}

# what is taken out of the user's frame, in its own rows and columns
TAIL = 22                                                 # the tail is all of the frame up to this column, above the body
TAKEN = {'tail row': 7, 'rows': (23, 26), 'column': 10}
W, H = 50, 35                                             # the built frame; row 0 stays empty. Cut so the body sits on its middle (PLACE)
PLACE = -6                                                # where the user's column 0 lands in it
BODY = 26                                                 # the row of the legs the breath doubles and drops

# the idle, in the built frame's rows and columns
SWAYS = (15, 16)                                          # the tail that sways: everything up to this column and down to this row...
BACK_FLOWER = {(14, 14), (13, 15), (14, 15), (15, 15), (14, 16)}   # ...but the flower on its back, which stays with the cat
LEAN = {1: ((8, 1),), 0: (), -1: ((8, -1),), -2: ((8, -2), (12, -1))}   # how far the tail's tip is over -> (down to this row, this many columns), top first
SWAY   = (0, 1, 1, 0, -1, -2, -2, -1)                     # the tip, a frame: toward its head, back through rest, away, and back
BREATH = (0, 0, 1, 1, 0, 0, -1, -1)                       # 1 the chest lifted, -1 settled: a step behind the tail, so each frame moves one thing
SETTLED = {(8, 26): 'K'}                                  # the outline under its hind leg, put back by hand where the settled breath drops it
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

def user():
    """The user's frame as they saved it: {pixel: letter}, 46x35."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '22_cactus_cat_user_frame.png')).convert('RGBA'); assert im.size == (46, 35), im.size
    return {(x, y): LETTER['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(35) for x in range(46) if im.getpixel((x, y))[3]}

def smaller(u):
    """Their pixels with TAKEN out: what was above a row comes down to close it, what was left of the column comes right."""
    for (x, y), c in u.items():                           # nothing is lost that is not repeated beside it
        if y == TAKEN['tail row'] and x <= TAIL: assert c in (u.get((x, y - 1)), u.get((x, y + 1))), (x, y)
        if y in TAKEN['rows']: assert c in (u.get((x, y - 1)), u.get((x, y + 1))), (x, y)
        if x == TAKEN['column']: assert c in (u.get((x - 1, y)), u.get((x + 1, y))), (x, y)
    g = {}
    for (x, y), c in u.items():
        if (y == TAKEN['tail row'] and x <= TAIL) or y in TAKEN['rows'] or x == TAKEN['column']: continue
        down = (x <= TAIL and y < TAKEN['tail row']) + sum(y < r for r in TAKEN['rows'])
        g[(x + (x < TAKEN['column']), y + down)] = c
    return g

def pose():
    """The smaller cat set in the built frame."""
    g = {(x + PLACE, y): c for (x, y), c in smaller(user()).items()}
    assert all(0 <= x < W and 1 <= y < H for x, y in g), sorted(p for p in g if not (0 <= p[0] < W and 1 <= p[1] < H))[:5]
    return g

def sway(g, tip):
    """The tail leaned: each of its rows goes over by what LEAN gives that row, the rest of the cat as it was."""
    over = lambda y: next((dx for row, dx in LEAN[tip] if y <= row), 0)
    tail = {p for p in g if p[0] <= SWAYS[0] and p[1] <= SWAYS[1] and p not in BACK_FLOWER}
    out = {p: c for p, c in g.items() if p not in tail}
    for (x, y) in tail:
        q = (x + over(y), y); assert q not in out, ('the tail runs into the cat', tip, q)
        out[q] = g[(x, y)]
    return out

def breath(g, k):
    """As the build breathes a still about row BODY: 1 everything above it up a pixel and that row doubled, -1 down a pixel and that row gone."""
    if k > 0: return {**g, **{(x, y - 1): c for (x, y), c in g.items() if y <= BODY}}
    if k < 0: return {**{(x, y + (y < BODY)): c for (x, y), c in g.items() if y != BODY}, **SETTLED}
    return g

def bare(g):
    """Hide with nothing beside it: where an outline is missing."""
    return {p for p, c in g.items() if c in 'Gg' and any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}

def FRAMES():
    p = pose()
    fs = [breath(sway(p, s), b) for s, b in zip(SWAY, BREATH)]
    assert fs[0] == p                                     # the user's frame is frame 0
    for i, f in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in f), i
        assert len(bare(f)) <= len(bare(p)), (i, sorted(bare(f)))     # no lean or breath opens the outline
        assert f != fs[i - 1], i                          # each frame moves
    return fs

if __name__ == '__main__':
    g = pose()
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    coat = [p for p in g if p[0] - PLACE > TAIL and g[p] in 'Gg']                 # head and body, not the tail
    print('drawn', (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'rows', (min(ys), max(ys)), 'cols', (min(xs), max(xs)), '| colours', sorted(set(g.values())))
    print('middle of its coat (%.1f, %.1f) | middle of the frame, where its shots leave from (%.1f, %.1f)' % (sum(p[0] for p in coat) / len(coat) + 0.5, sum(p[1] for p in coat) / len(coat) + 0.5, W / 2, H / 2))
    if sys.argv[1:2] == ['check']:
        print('bare at rest', sorted(bare(g)))
        for tip in LEAN:
            f = sway(g, tip); print('tip', tip, 'bare', sorted(bare(f) - bare(g)))
            for y in range(1, 23): print('  ' + ''.join(f.get((x, y), '.') for x in range(24)))
    elif sys.argv[1:2] == ['show']:
        from PIL import Image
        u = {(x + PLACE, y): c for (x, y), c in user().items()}
        cv = Image.new('RGBA', (W * 2 + 2, H), (40, 40, 40, 255))
        for i, d in enumerate((u, g)):
            im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
            for (x, y), c in d.items():
                if 0 <= x < W and 0 <= y < H: im.putpixel((x, y), tuple(int(PAL[c][i2:i2 + 2], 16) for i2 in (0, 2, 4)) + (255,))
            cv.paste(im, (i * (W + 2), 0))
        cv.resize((cv.width * 8, cv.height * 8), Image.NEAREST).save(sys.argv[2])
    else: flat_parts.write('22_cactus_cat', FRAMES(), PAL, W, H, body=BODY - 1, dirs='quarter', view='DR')
