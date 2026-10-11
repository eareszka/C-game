"""82 Nadubi, big tier, to art/direction/SPRITE_STYLE.md: standing, crawling and scratching.

    python art/enemies/82_nadubi_design.py            writes 82_nadubi{,_crawl,_scratch}.txt and .json
    python art/enemies/82_nadubi_design.py show OUT.png   every frame, enlarged

The nadubi of western Arnhem Land (Kunwinjku rock art): a malevolent spirit with barbs growing
from its elbows and knees. The design is the old sheet's, kept at the user's word (2026-10-10:
"keep the old design"): gaunt, dark red ochre, on all fours with its limbs sprawled like a
spider's, elbows and knees jutting above its back, bone barbs off them and along its spine, bone
claws, a long skull with empty sockets and a gaping toothed mouth. The old sheet was a 3D skeleton
turned to eight views; this is drawn flat, for the two views the user chose: from the front
(standing, and reared up scratching) and from the side (crawling; the other way is its mirror).

Three sheets, the ones the fight already plays (frame counts and meanings are its):
  82_nadubi          5  standing: at rest, a claw lifting, the claw raised and raking (frame 2,
                        where its pentagram leaves from), the claw coming down, settling
  82_nadubi_scratch  5  reared up: the claw on our right high, slashed down, the claw on our left
                        high, slashed down, both drawn back (a slash fires on frames 1 and 3)
  82_nadubi_crawl    4  from the side: a spider's gait, opposite limbs reaching and pushing

How a frame is made. Its head, body, hands and feet are small drawings, a letter a colour (the
grids below). Its limbs and barbs are laid between joints placed by hand for that frame, thick at
the body and thin at the tip. Everything is then one drawing, set down back to front
(tools/flat_parts.py).

The user went over the first standing frame in Aseprite and said "just repeat that pattern for
the rest". Their pattern, which every frame now follows:
- the body is seamless: no black line where a limb joins the body, crosses another limb or meets
  its own claw -- the outline is round the outside only, and the two ochres tell near limbs from
  far ones. (Where a limb crosses flesh of its own ochre well away from its root, its edge there
  is a tone darker, so a slashing arm still reads against the body.) The head and the barbs keep
  their own edges;
- the head is theirs: long fangs, and bone pupils in the sockets, not white;
- a dark wrist where a limb runs into its claw.
A part too thin to hold an edge (a wrist, a finger, a barb's point) is colour only, since battles
are on black. Standing frame 0 is the user's frame exactly (TOUCH holds the few pixels of theirs
that are not one of those rules)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from flat_parts import stroke, run, grid, add, mid, write
import flat_parts
W, H = 98, 65                                             # the built frame; row 0 stays empty
PAL = {'K': '000000', 'L': '792727', 'F': '5d1e1f', 'f': '280e10', 'C': 'e8e0c0', 'c': 'b29e5c', 'k': '110000'}
DARKER = {'L': 'F', 'F': 'f'}
mir = lambda p: (W - 1 - p[0], p[1])
draw = lambda parts: flat_parts.draw(parts, W, H, DARKER)
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# -- its parts (see tools/flat_parts.py for what a part is) ---------------------------------------
def leg(tone, a, j, b, wa=8.0, wj=5.0, wb=3.2):
    """A limb of two bones: thick at the body (a), a knob at its joint (j), thin at its end (b)."""
    px = stroke(a, j, wa, wj) | stroke(j, b, wj, wb) | stroke(j, j, wj + 1.6, wj + 1.6)
    return ({p: tone for p in px}, 'flesh', a)

def back(tone, *joints_widths):
    """The trunk, through its joints: (point, width), ..."""
    return ({p: tone for p in run(*joints_widths)}, 'flesh', None)

def barb(a, b, w=4.5):
    """A bone barb from its root a to its point b, shaded on its under side."""
    px = stroke(a, b, w, 1.0)
    low = stroke((a[0] + 1, a[1] + 1), (b[0] + 0.5, b[1] + 0.5), w - 2.5, 0.6)
    return ({p: ('c' if p in low else 'C') for p in px}, 'solid', None)

# -- the small drawings ---------------------------------------------------------------------------
HEAD_FRONT = """
....KKKKK....
..KKLLLLLKK..
.KLLLLLLLLLK.
.KLLLLLLLLLK.
KLLLLLLLLLLLK
KLKKKLLLKKKLK
KLKCKLLLKCKLK
KLKKKLLLKKKLK
KLLLLLKLLLLLK
.KLLKCKCKLLK.
.KFCKCKCKCFK.
.KFCkCkCkCFK.
.KFkkkkkkkFK.
.KFkkkkkkkFK.
..KFCkkkkFK..
..KFCkCkCFK..
...KKKKKKK...
""".split()                                               # the user's, as they left it: set down as it is
HEAD_SIDE = """
...LLLLLLLL.....
.LLLLLLLLLLLL...
LLLLLLLLKKKLLL..
LLLLLLLLKCKLLLL.
LLLLLLLLKKKLLLLL
LLLLLLLLLLKCKCKL
.LLLLFKCKCKCKCKK
.LLLFFCkCkCkCkk.
..LFFkkkkkkkkk..
..LFFCkkkCkCk...
...FFFFFFFFFF...
....FFFFFFF.....
""".split()                                               # mine, with their fangs and bone pupil; its outer ring becomes its edge
BODY_FRONT = """
....LLLLLLLLLLLL....
..LLLLLLLLLLLLLLLL..
.LLLLLLLLLLLLLLLLLL.
LLLLLLLLLLLLLLLLLLLL
LLLLLLLLLLLLLLLLLLLL
LFLLLLLLLLLLLLLLLLFL
LFFLLLLLLLLLLLLLLFFL
.LFFFLLLLLLLLLLFFFL.
..LFFFFFFFFFFFFFFL..
...LLFFFFFFFFFFLL...
.....LLLLLLLLLL.....
""".split()
BODY_UP = """
.LLLLLLLLLLLL.
LLLLLLLLLLLLLL
LLLLLLLLLLLLLL
LLLLLLLLLLLLLL
.LFLLLLLLLLFL.
.LFLLLLLLLLFL.
.LFFLLLLLLFFL.
..LFLLLLLLFL..
..LFLLLLLLFL..
..LFFLLLLFFL..
...LFLLLLFL...
...LFLLLLFL...
...LFLLLLFL...
...LFLLLLFL...
..LLFLLLLFLL..
..LLLLLLLLLL..
.LLLLLLLLLLLL.
.LLLLLLLLLLLL.
.LLLLLFFLLLLL.
..LLLLFFLLLL..
...LLLFFLLL...
""".split()
HAND_DOWN = """
...CCCCC...
..CCCCCCC..
.CCCcCcCCC.
CCC.CCC.CCC
CC..CcC..CC
CC..CC...CC
""".split()                                               # a claw planted, fingers splayed
HAND_UP = """
CC...CC..CC
CC..CcC..CC
CCC.CCC.CCC
.CCCcCcCCC.
..CCCCCCC..
...CCCCC...
""".split()                                               # a claw raised, fingers spread
FOOT = """
..CCCC...
.CCCCCC..
CCCCCCCC.
CcCC.cCCC
""".split()                                               # a foot on the ground, toes to the right

# A claw or foot keeps its own edge; one dark pixel of wrist or ankle runs into it (the user's).
dot = lambda x, y, c: ({(round(x), round(y)): c}, 'raw', None)
hand_down = lambda wr: [grid(wr[0] - 5, wr[1] + 1, HAND_DOWN, 'solid'), dot(wr[0], wr[1] + 1, 'F')]     # under its wrist
hand_up = lambda wr: [grid(wr[0] - 5, wr[1] - 6, HAND_UP, 'solid'), dot(wr[0], wr[1] - 1, 'F')]         # over its wrist
def foot(ankle, toes_right=True):
    heel = -1 if toes_right else 1
    return [grid(ankle[0] - (2 if toes_right else 6), ankle[1] + 1, FOOT, 'solid', flip=not toes_right),
            dot(ankle[0], ankle[1] + 1, 'F'), dot(ankle[0] + heel, ankle[1] + 1, 'F'), dot(ankle[0] + 2 * heel, ankle[1] + 1, 'K')]

# The user's own pixels on the standing frame that are not one of the rules: (x, y): (as built, theirs).
# Set wherever a frame still has the same thing there (so not on an arm that has moved).
TOUCH = {(33, 28): ('K', 'F'), (64, 28): ('K', 'F'), (34, 35): ('F', 'K'), (63, 35): ('F', 'K'), (39, 40): ('F', 'K'), (51, 40): ('L', 'K'),
         (58, 40): ('F', 'K'), (38, 41): ('F', 'K'), (59, 41): ('F', 'K'), (42, 42): ('L', 'K'), (55, 42): ('L', 'K'), (54, 43): ('L', 'K')}

def touched(g):
    for p, (was, now) in TOUCH.items():
        if g.get(p, '.') == was:
            if now == '.': g.pop(p, None)
            else: g[p] = now
    return g

# -- standing, from the front ---------------------------------------------------------------------
def standing(arm=None, dip=0):
    """On all fours. arm: (elbow, wrist, claw up?) for the arm on our right; dip: px its body is down."""
    d = (0, dip); L = []
    for a, b in (((45, 36), (42, 24)), ((48.5, 35), (48.5, 20)), ((52, 36), (55, 24))): L.append(barb(add(a, d), add(b, d), 4.0))   # the spine's crest
    for m in (lambda p: p, mir):                          # the hind legs, behind: knees jutting high, a barb off each
        hip, knee, ankle = add(m((41, 38)), d), add(m((28, 27)), d), m((26, 60))
        L.append(barb(knee, add(m((22, 15)), d)))
        L.append(leg('F', hip, knee, ankle))
        L += foot(ankle, toes_right=m is mir)
    L.append(grid(39, 34 + dip, BODY_FRONT))
    for m in (lambda p: p, mir):                          # the arms, in front: elbows up, a barb off each, claws planted
        sh, el, wr, up = add(m((43, 39)), d), add(m((35, 30)), d), m((38, 58)), False
        if m is mir and arm: el, wr, up = arm
        L.append(barb(el, add(el, (3 if m is mir else -3, -12))))
        L.append(leg('L', sh, el, wr))
        L += hand_up(wr) if up else hand_down(wr)
    L.append(grid(42, 40 + dip, HEAD_FRONT, 'raw'))
    return touched(draw(L))

IDLE = lambda: [standing(),
                standing(((63, 29), (64, 49), False)),    # the claw on our right lifting
                standing(((63, 29), (71, 38), True)),     # raised, raking: the pentagram leaves from here
                standing(((63, 30), (67, 45), False)),    # coming down
                standing(dip=1)]                          # settling

# -- reared up, from the front --------------------------------------------------------------------
def reared(right, left, dip=0):
    """Up on its hind legs. right, left: (elbow, wrist, claw up?) for the arm on our right, on our left."""
    d = (0, dip); L = []
    for a, b in (((46, 26), (39, 16)), ((51, 26), (58, 17))): L.append(barb(add(a, d), add(b, d)))            # barbs off its back, behind the shoulders
    for m in (lambda p: p, mir):                          # the legs, squatting wide
        hip, knee, ankle = add(m((45, 44)), d), add(m((32, 40)), d), m((34, 60))
        L.append(barb(knee, add(m((22, 35)), d)))
        L.append(leg('F', hip, knee, ankle, 8.5))
        L += foot(ankle, toes_right=m is mir)
    L.append(grid(42, 23 + dip, BODY_UP))
    for sh, (el, wr, up), out in ((add((44, 26), d), left, -1), (add((54, 26), d), right, 1)):
        L.append(barb(el, add(el, (10 * out, -3))))
        L.append(leg('L', sh, el, wr, 7.0))
        L += hand_up(wr) if up else hand_down(wr)
    L.append(grid(42, 7 + dip, HEAD_FRONT, 'raw'))
    return draw(L)

flipped = lambda g: {mir(p): c for p, c in g.items()}
HIGH, SLASH = ((63, 20), (63, 10), True), ((63, 32), (57, 41), False)        # the arm on our right: raised to strike; swept down
LOW, BACK = ((35, 33), (31, 44), False), ((33, 30), (27, 37), False)         # the arm on our left: hanging; drawn back as the other strikes
def SCRATCH():
    hi, sl = reared(HIGH, LOW), reared(SLASH, BACK)
    return [hi, sl, flipped(hi), flipped(sl), reared((mir(LOW[0]), mir(LOW[1]), False), LOW, dip=1)]

# -- crawling, from the side ------------------------------------------------------------------------
#          reaching: joint, end      pushing: joint, end      the barb off its joint
GAIT = {'near hind': (((36, 21), (42, 60)), ((30, 22), (28, 60)), (-7, -11)),
        'far hind':  (((45, 21), (50, 60)), ((40, 21), (36, 60)), (1, -11)),
        'near arm':  (((64, 27), (74, 58)), ((58, 28), (60, 58)), (-2, -11)),
        'far arm':   (((66, 27), (80, 58)), ((56, 28), (57, 58)), (-3, -11))}
LIFT = 4                                                  # px a limb's end is off the ground as it swings forward

def crawling(f):
    """Frame f of the crawl, facing right: the near arm and far leg move together, the near leg and far arm against them."""
    def at(name):
        (rj, re), (pj, pe), _ = GAIT[name]
        step = f if name in ('near arm', 'far hind') else (f + 2) % 4       # 0 reaching, 1 planted and passing back, 2 pushing, 3 swinging forward
        return ((rj, re), (mid(rj, pj), mid(re, pe)), (pj, pe), (mid(rj, pj, 1), mid(re, pe, LIFT)))[step]
    bob = (0, 1, 0, 1)[f]; d = (0, bob)
    hip, sh = add((38, 32), d), add((61, 39), d)
    L = []
    for name, tone, root, is_arm in (('far hind', 'F', hip, False), ('far arm', 'F', sh, True)):
        j, e = at(name); j = add(j, d)
        L.append(barb(j, add(j, GAIT[name][2]))); L.append(leg(tone, root, j, e)); L += hand_down(e) if is_arm else foot(e)
    for a, b in (((44, 31), (40, 21)), ((50, 33), (47, 23))): L.append(barb(add(a, d), add(b, d)))            # the spine's crest
    L.append(back('L', (hip, 10), (sh, 8), (add((71, 44), d), 6)))                                              # the back, down to the neck
    L.append(grid(69, 39 + bob, HEAD_SIDE, 'solid'))
    for name, tone, root, is_arm in (('near hind', 'L', hip, False), ('near arm', 'L', sh, True)):
        j, e = at(name); j = add(j, d)
        L.append(barb(j, add(j, GAIT[name][2]))); L.append(leg(tone, root, j, e)); L += hand_down(e) if is_arm else foot(e)
    return draw(L)

CRAWL = lambda: [crawling(f) for f in range(4)]
SHEETS = (('82_nadubi', IDLE), ('82_nadubi_scratch', SCRATCH), ('82_nadubi_crawl', CRAWL))

if __name__ == '__main__':
    built = [(name, frames()) for name, frames in SHEETS]
    theirs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '82_nadubi_user_frame.png')     # the standing frame as the user left it
    if os.path.exists(theirs):
        from PIL import Image
        a, b = image(built[0][1][0]), Image.open(theirs).convert('RGBA')
        assert all(a.getpixel((x, y)) == b.getpixel((x, y)) or not (a.getpixel((x, y))[3] or b.getpixel((x, y))[3]) for y in range(H) for x in range(W)), 'standing frame 0 is not the user frame'
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        cv = Image.new('RGBA', (W * 5 + 8, (H * 2 + 2) * 3 + 8), (40, 40, 40, 255))
        for r, (name, fr) in enumerate(built):
            for i, g in enumerate(fr):
                cv.alpha_composite(image(g, (255, 170, 200, 255)), (i * (W + 2), r * (H * 2 + 6))); cv.alpha_composite(image(g, (0, 0, 0, 255)), (i * (W + 2), r * (H * 2 + 6) + H + 2))
        cv.resize((cv.width * 3, cv.height * 3), Image.NEAREST).save(sys.argv[2])
    else:
        for name, fr in built: write(name, fr, PAL, W, H)
    for name, fr in built:
        assert len({tuple(sorted(g.items())) for g in fr}) == len(fr), name + ': two frames the same'
        print(name, len(fr), 'frames | colours', sorted({c for g in fr for c in g.values()}), '| widest', max(max(p[0] for p in g) - min(p[0] for p in g) + 1 for g in fr),
              'tallest', max(max(p[1] for p in g) - min(p[1] for p in g) + 1 for g in fr))
