"""74 Bes Rap, big tier: its idle, built from the user's own frame (74_bes_rap_user_frame.png).

    python art/enemies/74_bes_rap_design.py              the frames, checked; writes 74_bes_rap.json/.txt here
    python art/enemies/74_bes_rap_design.py check        which rows can be repeated or taken out without opening the outline
    python art/enemies/74_bes_rap_design.py show OUT.png  the frames side by side, enlarged, on black

The pig spirit of the Jah Hut, squatting at the roots of the fig tree. My typed pose is kept in
74_bes_rap_pose_first.py; the user redrew its face in Aseprite (2026-10-11) and that frame is frame 0,
pixel for pixel. The user, same day: "first frame looks good now just make it have idle animation to match
its bullet patterns". Five frames at the sheet's 260 ms (1.3 s, as before); it always sits as drawn.

The fight (class BesRap) blows its spit on idle frame 2, "head lunges, jaw drops". So:
  0  at rest                                the user's frame
  1  winds up: draws breath, head back      the upper body up a row, the head a pixel back
  2  spits: head lunged, jaw dropped        head 2 right 1 down, the mouth open 3 rows (MOUTH[3]), foam at the lip
  3  the jaw comes up                       head 1 right, the mouth open 1 row (MOUTH[1]), spit hanging off the chin
  4  breathes out                           the upper body down a row, the last drop falling
Every other pixel is the user's, moved; the open mouths are typed. Only the foam is left without an outline
(a white strand, as the drool on 25 and 06)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65
PAL = {'K': '000000', 'L': 'f0b890', 'F': 'ec8476', 'f': 'b6433d',   # skin: lit, the body of it, under and away
       's': 'a4aaba', 'T': 'e8e0c0', 'P': 'fc74b4', 'w': 'fcfcfc'}   # spines, teeth, the snout's disc (and the tongue), the eye (and its foam)
LETTER = {v: k for k, v in PAL.items()}
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

HEAD_BOTTOM = 25                                          # rows down to here are the head; the neck starts under it
NECK_COLS = range(49, 60)                                 # the neck's columns in rows 26-30 (the spines are either side)
LIFT_ROW = 39                                             # repeated to lift the upper body a row, taken out to sink it (tested clean in `check`)

# The mouth, typed open: rows from MOUTH_Y, columns from MOUTH_X, replacing the head there. The cheek's hinge
# stays at the left (x 50-53), the upper teeth stay up, the lower teeth, lip and chin come down with the jaw.
MOUTH_X, MOUTH_Y = 48, 20
MOUTH = {
    1: ['.KfFFFKKKKKKTTKTTKTKKK.',                        # the upper lip and teeth, as drawn
        '.KffFKfffffffffffffK...',                        # a row of throat
        '..KffKTTKTTKTTKTTKTK...',                        # the lower teeth
        '..KfffKKKKKKKKKKKKKK...',
        '..KKfFFFFFFFFFFFFFFK...',                        # the lower jaw, as drawn, a row down
        '....KKfffffffffffffK...',
        '....KfKKKKKKKKKKKKK....'],
    3: ['.KfFFFKKKKKKTTKTTKTKKK.',
        '.KffFKfffffffffffffK...',                        # the throat, the cheek's hinge going down its left side
        '..KffKfffffPPPfffwfK...',                        # the tongue coming up, foam on it
        '..KffKffwPPPPPPPfffK...',
        '..KffKTTKTTKTTKTTKTK...',                        # the lower teeth, three rows down
        '..KfffKKKKKKKKKKKKKK...',
        '..KKfFFFFFFFFFFFFFFK...',
        '....KKfffffffffffffK...',
        '....KfKKKKKKKKKKKKK....'],
}
for m in MOUTH.values(): assert all(len(t) == 23 for t in m), [len(t) for t in m]

# Foam with no outline: head pixels (they move with the head), or pixels in the frame for the drop that has let go.
FOAM = {2: [(68, 22), (68, 23), (69, 23), (68, 24)],      # flecks at the lip as it spits
        3: [(68, y) for y in range(23, 28)]}              # a strand off the chin
DROP = {4: [(69, 31), (69, 32)]}                          # ...and the drop falling from it

#        head dx, dy, mouth, neck shear for rows 26-30, lift (+1 a row up, -1 a row down)
POSES = [(0, 0, 0, (0, 0, 0, 0, 0), 0),
         (-1, 0, 0, (-1, -1, -1, 0, 0), 1),
         (2, 1, 3, (2, 2, 1, 1, 0), 0),
         (1, 0, 1, (1, 1, 1, 1, 0), 0),
         (0, 0, 0, (0, 0, 0, 0, 0), -1)]

def user_frame():
    """Frame 0 as the user saved it: {pixel: letter}."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '74_bes_rap_user_frame.png')).convert('RGBA'); assert im.size == (W, H), im.size
    return {(x, y): LETTER['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}

def lift(g, n):
    """n = 1: all above LIFT_ROW up a row, that row there twice. n = -1: that row taken out, all above down a row."""
    if n > 0: return {**{(x, y - 1): c for (x, y), c in g.items() if y <= LIFT_ROW}, **{p: c for p, c in g.items() if p[1] >= LIFT_ROW}}
    if n < 0: return {**{p: c for p, c in g.items() if p[1] > LIFT_ROW}, **{(x, y + 1): c for (x, y), c in g.items() if y < LIFT_ROW}}
    return g

def pose(u, f):
    """Frame f: the head moved and its mouth opened, the neck sheared under it, the foam, the body lifted."""
    dx, dy, m, shear, n = POSES[f]
    head = {p: c for p, c in u.items() if p[1] <= HEAD_BOTTOM}
    if m:
        head = {p: c for p, c in head.items() if not (p[1] >= MOUTH_Y and MOUTH_X <= p[0] < MOUTH_X + 23)}
        head.update({(x, y): c for y, t in enumerate(MOUTH[m], MOUTH_Y) for x, c in enumerate(t, MOUTH_X) if c != '.'})
    body = {(x + (shear[y - 26] if 26 <= y <= 30 and x in NECK_COLS else 0), y): c for (x, y), c in u.items() if y > HEAD_BOTTOM}
    g = {**body, **{(x + dx, y + dy): c for (x, y), c in head.items()}}
    g.update({(x + dx, y + dy): 'w' for x, y in FOAM.get(f, ())})
    g.update({p: 'w' for p in DROP.get(f, ())})
    return lift(g, n)

def foam(f):
    """Frame f's foam pixels, where they land."""
    dx, dy, _, _, n = POSES[f]
    return set(lift({**{(x + dx, y + dy): 'w' for x, y in FOAM.get(f, ())}, **{p: 'w' for p in DROP.get(f, ())}}, n))

def bare(g):
    """Colour with nothing beside it: where the outline is open."""
    return {p for p, c in g.items() if c != 'K' and any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}

def FRAMES():
    u = user_frame()
    fs = [pose(u, f) for f in range(len(POSES))]
    assert fs[0] == u                                     # the user's frame is frame 0
    for i, f in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in f), i
        assert set(f.values()) <= set(PAL), i
        assert bare(f) - foam(i) <= bare(u), (i, sorted(bare(f) - foam(i) - bare(u)))   # nothing opens the outline but the foam
        assert f != fs[i - 1], i                          # each frame moves
    return fs

def numbers(g):
    """What the bible measures, of one frame."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'open edge': sorted(bare(g))}

if __name__ == '__main__':
    u = user_frame()
    if sys.argv[1:2] == ['check']:
        base = len(bare(u))
        print('open at rest', sorted(bare(u)))
        print('can repeat row', [r for r in range(27, 58) if len(bare({**{(x, y - 1): c for (x, y), c in u.items() if y <= r}, **{p: c for p, c in u.items() if p[1] >= r}})) <= base])
        print('can take out row', [r for r in range(27, 58) if len(bare({**{p: c for p, c in u.items() if p[1] > r}, **{(x, y + 1): c for (x, y), c in u.items() if y < r}})) <= base])
    elif sys.argv[1:2] == ['show']:
        from PIL import Image
        fr = FRAMES(); sheet = Image.new('RGBA', (W * len(fr), H), (0, 0, 0, 255))
        for i, f in enumerate(fr): sheet.paste(image(f, (0, 0, 0, 255)), (W * i, 0))
        sheet.resize((sheet.width * 5, H * 5), 0).save(sys.argv[2])
    else:
        fr = FRAMES()
        for k, v in numbers(fr[0]).items(): print('%-18s %s' % (k, v))
        flat_parts.write('74_bes_rap', fr, PAL, W, H, dirs='down', view=('D', 'DL', 'L', 'UL'))
