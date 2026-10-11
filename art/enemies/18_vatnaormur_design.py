"""18 Vatnaormur, big tier, to art/direction/SPRITE_STYLE.md.

    python art/enemies/18_vatnaormur_design.py              writes 18_vatnaormur.txt, .json and 18_vatnaormur_pool.png
    python art/enemies/18_vatnaormur_design.py show OUT.png   its frames, enlarged
        reads 18_vatnaormur_user_frame.png beside it: the frame the user finished

Iceland's lake serpent (A Book of Creatures): a heath-worm -- a slug -- laid on a gold ring that
grew, was thrown into the lake and grew into a monster, its humps rising from the water. The old
sheet was a dark green horse-headed serpent, cut-out layers with generated water and six colours
off the palette. The pose is still its (the user, 2026-10-10: "keep the old design"): the neck
reared out of the water in the middle, a spiked coil looping out either side, the tip of its tail
up behind it, seen from the front -- the only way it is ever seen. Then the user sent the book's
own picture, a giant slug: "have the enemies sprite color be closer to this and its head looking
more like a slug", and then "go back to the slug look but more intimidating". So it is slate
blue-grey with a pink underside, a slug's head made to frighten -- teeth, staring eyes on stalks,
its mantle flared behind head and neck like a hood -- and the user then went over head and eyes
themselves in Aseprite. That frame is frame 0, exactly.

One sheet of five frames, played in order. The user: "have it simply sway and bob and the tails
just keep rotating". So:
- head and neck sway out to one side and back to the other, and bob a pixel as they go. They are
  the user's own pixels, moved: the head as one piece, the neck and hood under it leaning from the
  water up (nothing of it is redrawn);
- the coils turn: their spikes travel round each arch, up out of the water on our right and down
  into it on our left, each reaching the next one's place as the loop comes round;
- its mouth closes and opens a little (open as it spits, on frame 1);
- the tip of the tail wags against the head;
- the white water at the coils' feet splashes as they turn (SPLASH).

Coils, spikes and tail are laid along points placed by hand (tools/flat_parts.py), seamless, the
black edge round the outside only. first_front() is head and neck as first drawn: it is kept
because it says which pixels of the user's frame are head and neck."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from flat_parts import stroke, run, grid, write
import flat_parts
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 114, 59                                            # the built frame; row 0 stays empty
PAL = {'K': '000000', 'D': '474751', 'M': '595965', 'L': '848694', 'H': 'a4aaba',      # slate: shade, the coils, the neck and head, the light on top
       'P': 'ec8476',                                                                  # its pink underside
       'W': 'fcfcfc', 'A': '3e91cc', 'a': '84a7e9'}                                    # foam, teeth and eyes; the water and its marks
DARKER = {'L': 'M', 'M': 'D'}
WATER = 48                                                # the water's top row
SWAY = (0, 3, 2, -2, -3)                                  # px the head is over to our right, by frame
BOB = (0, 1, 1, 0, -1)                                    # px it is up
SHUT = (0, 0, 1, 2, 1)                                    # rows its mouth has closed: open on frames 0 and 1 (it spits on 1), shut on 3
MOUTH = (51, 63, 21, 23)                                  # the user's mouth in their frame: its columns; its first row that can go, and its last row
CHIN, PIVOT = 29, 45                                      # rows: down to CHIN the head moves as one piece; below PIVOT the neck stands still
RING = (15, 60, 120, 165, 210, 255, 300, 345)             # degrees round a coil where its spikes are at rest (0 our right, 90 the top); under the water from 180 on
draw = lambda parts: flat_parts.draw(parts, W, H, DARKER)
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)
flesh = lambda px, tone, root=None: ({p: tone for p in px}, 'flesh', root)

# The water in the sprite itself: (row, first column, last column). The battle draws the pool (below)
# behind the enemy; this patch is the same blue with no outline, so it disappears into it -- and
# still stands as a small lake if the pool is not drawn.
LAKE = ((48, 6, 109), (49, 4, 111), (50, 3, 112), (51, 4, 111), (52, 6, 109), (53, 9, 106), (54, 15, 100), (55, 23, 92), (56, 37, 78))
RIPPLES = ((50, 24), (50, 90), (52, 46), (52, 72), (54, 32), (54, 86))      # (row, first column) of a short lighter mark

def spike(a, b, tone, w=4.5):
    """A spike from its root a to its point b: the body's slate, pale at the point."""
    px = stroke(a, b, w, 1.0)
    tip = stroke(((a[0] + 2 * b[0]) / 3, (a[1] + 2 * b[1]) / 3), b, w, 1.0)
    return ({p: ('H' if p in tip else tone) for p in px}, 'solid', None)

def coil(cx, f=0):
    """A coil looping out of the water round column cx, at frame f of its turning: an arch, pink along its under side, spikes round it."""
    top = WATER - 1
    at = lambda deg, r: (cx + r * math.cos(math.radians(deg)), top - r * math.sin(math.radians(deg)))
    arch = [(cx - 12, WATER + 1)] + [at(deg, 12) for deg in range(180, -1, -15)] + [(cx + 12, WATER + 1)]
    under = [(cx - 7.5, WATER + 1)] + [at(deg, 7.5) for deg in range(180, -1, -15)] + [(cx + 7.5, WATER + 1)]
    body = run(*[(p, 12) for p in arch]); belly = run(*[(p, 3.2) for p in under]) & body
    spikes = []
    for a, b in zip(RING, RING[1:] + (RING[0] + 360,)):   # each spike a step of the way to the next one's place
        deg = (a + (b - a) * f / len(SWAY) + 90) % 360 - 90
        if -8 < deg < 188: spikes.append(spike(at(deg, 17), at(deg, 26), 'M'))
    return spikes + [({p: ('P' if p in belly else 'M') for p in body}, 'flesh', None)]

def tail(sway=0):
    """The tip of its tail, up behind it, leaning against the head's sway."""
    return flesh(stroke((47, 27), (39 - sway / 2, 16), 6, 1.5), 'M')

HEAD = """
.....HHHHHHH.....
...HHHHHHHHHHH...
..LLLLLLLLLLLLL..
.LLLLLLLLLLLLLLL.
.LLLLLLLLLLLLLLL.
LLLLLLLLLLLLLLLLL
LLLLLLLLLLLLLLLLL
LLLLLLLLLLLLLLLLL
LLLMMMMMMMMMMMLLL
LLMWKWKWKWKWKWMLL
LLMWKWKWKWKWKWMLL
LLMKKKKKKKKKKKMLL
LLMKWKWKWKWKWKMLL
.LLMMMMMMMMMMMLL.
.LLLLHLLLLLHLLLL.
..LLLHLLLLLHLLL..
..LLLPPPPPPPLLL..
...LPPPPPPPPPL...
""".split()

def first_front():
    """Head and neck as first drawn (the user redrew the head and eyes): the mantle, the neck, the eye stalks, the feelers, the head."""
    hx, hy = 56.5, CHIN
    L = [flesh(stroke((hx, hy - 9), (hx, hy + 7), 27, 19), 'D')]
    neck = [((56.5, WATER + 1), 17), ((56.5, 40), 15), ((hx, hy + 1), 14)]
    body = {p for p in run(*neck) if p[1] <= LAKE[-1][0]}; belly = run(*[(p, 5.2) for p, w in neck]); under = {p for p in body if hy <= p[1] <= hy + 2}
    L.append(({p: ('P' if p in belly else 'M' if p in under else 'L') for p in body}, 'flesh', None))
    eyes = {}
    for out in (-1, 1):
        root, tip = (hx + 5 * out, hy - 16), (hx + 12 * out, hy - 24)
        L.append(flesh(stroke(root, tip, 4.2, 2.6) | stroke(tip, tip, 5.6, 5.6), 'L'))
        tx, ty = round(tip[0]), round(tip[1])
        eyes.update({(tx + dx, ty + dy): 'W' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}); eyes[(tx, ty)] = 'K'
        L.append(flesh(stroke((hx + 7 * out, hy - 6), (hx + 12 * out, hy), 3.2, 1.6), 'L'))
    return L + [grid(hx - 8.5, hy - 18, HEAD), (eyes, 'raw', None)]

# The white water where a coil stands in the lake (the user: "make sure white water around tails make
# a splash due to movement"): each step is the white pixels about the coil's foot, (px along the water
# from the foot's middle, px above it). At rest it is a line of foam; as the coil turns it bursts up
# either side of the foot, flies out in drops, falls and spreads.
FOAM = {(x, 0) for x in range(-5, 6)}
SPLASH = (FOAM,
          FOAM | {(-6, 1), (-7, 1), (-6, 2), (-7, 2), (-7, 3), (6, 1), (7, 1), (6, 2), (7, 2), (7, 3)},                                  # bursting up either side
          {(x, 0) for x in range(-7, 8)} | {(-8, 2), (-8, 3), (-7, 4), (-10, 4), (-9, 5), (8, 2), (8, 3), (7, 4), (10, 4), (9, 5)},     # drops flying
          {(x, 0) for x in range(-9, 10)} | {(-10, 1), (-11, 2), (-9, 3), (10, 1), (11, 2), (9, 3)},                                    # falling
          {(x, 0) for x in range(-8, 9)})                                                                                               # spreading
GOING_IN = (0, 1, 2, 3, 4)                                # the step by frame where a coil goes down into the water (its foot on our left) ...
COMING_UP = (0, 4, 0, 1, 2)                               # ... and where it comes up out of it (on our right), a beat behind

def water(f=0):
    lake = {(x, y): 'A' for y, a, b in LAKE for x in range(a, b + 1)}                            # the water round it, over what stands in it
    marks = {(x, y): 'a' for y, x0 in RIPPLES for x in range(x0, x0 + 5)}
    foam = {(x, WATER): 'W' for x in range(49, 65)}                                              # round the neck: it stands still
    for cx in (30, 84):
        for side, steps in ((-12, GOING_IN), (12, COMING_UP)):
            foam.update({(cx + side + dx, WATER - up): 'W' for dx, up in SPLASH[steps[f]]})
    return [(lake, 'raw', None), (marks, 'raw', None), (foam, 'raw', None)]

def user_front():
    """{pixel: letter}: the user's head, eyes, mantle and neck, above the water -- their frame where head and
    neck were first drawn, and wherever they drew beyond that."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '18_vatnaormur_user_frame.png')).convert('RGBA'); assert im.size == (W, H)
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in PAL.items()}
    theirs = {(x, y): letter[im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}
    region = {p for px, kind, root in first_front() for p in px}
    mine = draw([tail()] + coil(30) + coil(84) + first_front() + water())
    region |= {p for p in set(theirs) | set(mine) if theirs.get(p) != mine.get(p)}
    return {p: c for p, c in theirs.items() if p in region and p[1] < WATER}, theirs

def jaw(front, shut):
    """The mouth closing (the user: "have mouth move slightly, closing and opening"): rows go from the top
    of its dark inside, the lower teeth and lip come up, and plain face fills in under them."""
    x0, x1, top, low = MOUTH
    out = dict(front)
    for x in range(x0, x1 + 1):
        for y in range(top, low + 1): out[(x, y)] = front[(x, y + shut)] if y + shut <= low else 'L'
    return out

def moved(front, sway, bob):
    """Head and neck swayed and bobbed: the head (down to CHIN) as one piece, the neck under it leaning less
    the nearer the water, everything above PIVOT up or down with the bob."""
    lean = lambda y: sway if y <= CHIN else round(sway * (WATER - 1 - y) / (WATER - 1 - CHIN)) if y < WATER else 0
    out = {}
    for (x, y), c in front.items():
        if y > PIVOT: out[(x, y)] = c
        elif y - bob <= PIVOT: out[(x + lean(y), y - bob)] = c           # (sinking, the row at the pivot is swallowed)
        if y == PIVOT and bob > 0:                                        # rising, it is drawn again under itself
            for k in range(bob): out[(x + lean(y), y - k)] = c
    return out

def tidy(g):
    """Nothing of the body shows below the water line: a coil's foot ran a pixel past the lake's edge (in the
    user's frame too -- two dark specks under the water, mine, which would show against the pool)."""
    return {p: c for p, c in g.items() if p[1] <= WATER or c in 'AaW'}

def frame(f, front, theirs=None):
    """Frame f. theirs: the user's frame -- a pixel of tail or coil whose edge comes out differently beside
    their head than it did beside the first one is set as they have it (frame 0 only: it is one pixel)."""
    g = tidy(draw([tail(SWAY[f])] + coil(30, f) + coil(84, f) + [(moved(jaw(front, SHUT[f]), SWAY[f], BOB[f]), 'raw', None)] + water(f)))
    if theirs:
        odd = [p for p in set(g) | set(theirs) if g.get(p) != theirs.get(p)]
        assert len(odd) <= 2, f'frame 0 is not the user frame: {sorted(odd)[:8]}'
        for p in odd: g[p] = theirs[p]
    return g

def FRAMES():
    front, theirs = user_front(); theirs = tidy(theirs)
    fr = [frame(f, front, theirs if f == 0 else None) for f in range(len(SWAY))]
    assert fr[0] == theirs
    return fr

# -- the pool ---------------------------------------------------------------------------------------
# The user, of the first pose (2026-10-10): "have the pool it sits in go to the far left and far
# right and all north of the screen from where the enemy is". That is wider than a sprite, so it is
# a picture of its own, 18_vatnaormur_pool.png, for the battle to draw behind the enemy: 2x, its top
# left at the screen's top left -- the whole width of the arena, from the top down to a shore just
# below the serpent (the serpent stands at 320, 140, its water line at screen row 177).
POOL_W, POOL_H = 320, 100
SHORE = (0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 2, 2, 1, 1, 1, 0, 0, 1, 1, 2, 3, 3, 2, 2, 2, 1, 0, 0, 0, 1, 1, 0)   # px the shore dips, along it, repeating
POOL_MARKS = ((14, 9), (58, 5), (101, 12), (151, 7), (203, 11), (248, 4), (291, 9), (33, 24), (84, 29), (132, 22), (183, 27), (229, 23), (276, 30),
              (8, 43), (52, 47), (110, 41), (232, 44), (286, 48), (27, 62), (73, 66), (124, 71), (196, 69), (247, 63), (300, 68), (46, 83), (97, 86),
              (156, 88), (214, 84), (268, 87))            # (column, row) of a short lighter mark: few, and nowhere in a pattern

def pool():
    """{pixel: letter}: flat water, a lighter line along its shore, a few marks."""
    g = {}
    for x in range(POOL_W):
        low = POOL_H - 4 + SHORE[x % len(SHORE)]
        for y in range(low + 1): g[(x, y)] = 'a' if y == low else 'A'
    for x0, y0 in POOL_MARKS:
        for x in range(x0, x0 + 5): g[(x, y0)] = 'a'
    return g

if __name__ == '__main__':
    fr = FRAMES()
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        cv = Image.new('RGBA', (W * len(fr) + 2 * (len(fr) - 1), H * 2 + 2), (40, 40, 40, 255))
        for i, g in enumerate(fr):
            cv.alpha_composite(image(g, (255, 170, 200, 255)), (i * (W + 2), 0)); cv.alpha_composite(image(g, (0, 0, 0, 255)), (i * (W + 2), H + 2))
        cv.resize((cv.width * 3, cv.height * 3), Image.NEAREST).save(sys.argv[2])
    else:
        write('18_vatnaormur', fr, PAL, W, H)
        flat_parts.image(pool(), PAL, POOL_W, POOL_H).save('18_vatnaormur_pool.png')
    assert len({tuple(sorted(g.items())) for g in fr}) == len(fr), 'two frames the same'
    print(len(fr), 'frames | colours', sorted({c for g in fr for c in g.values()}), '| tallest', max(max(p[1] for p in g) - min(p[1] for p in g) + 1 for g in fr))
