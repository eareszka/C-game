"""47 Moha-moha: the side view typed from the user's reference (2026-10-11), before any redraw by them.

    python art/enemies/47_moha_moha_pose_first.py show OUT.png   the pose enlarged: on pink, on black, filled black

The reference: a turtle-shelled plesiosaur -- a slate domed shell, a long green neck rising to a head with its
jaws open, brown spots, clawed flipper-legs, a long lavender-grey tail ending in a brown fluke. The user: "have it
face the side with the pose represented", "dont use shapes", the bible's rules; always facing right as drawn;
big, at the old sheet's size.

Every pixel is typed, a row at a time, part by part and back to front -- tail, fluke, far leg, body, neck and
head, near legs, shell -- each row either a run list ('K1 g2 G6': a letter and how many) or a row of letters.
Nothing is drawn by a stroke, a curve or an ellipse. Light comes from up and to our right, where it looks."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the frame, as the old sheet's; row 0 stays empty
PAL = {'K': '000000',
       'g': '2c6c44', 'G': '4fa667', 'B': 'cebe82',       # skin: away and under, the body of it, the throat and the lit front of each leg (and its claws)
       's': '474751', 'm': '595965', 'S': '848694',       # shell, and the tail with it: under and behind, the body of it, the top of the dome
       'T': '633e1b',                                     # the fluke, the spots on its head, inside its mouth
       'W': 'fcfcfc'}                                     # teeth, the eye's white
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

def runs(y, x0, spec):
    """One row typed as runs: 'K1 g2 G6' -> KggGGGGGG, starting at column x0. '.' leaves what is behind."""
    return (y, x0, ''.join(t[0] * int(t[1:]) for t in spec.split()))

def block(x0, y0, rows):
    """A drawing typed whole, set down with its top left at (x0, y0)."""
    return [(y, x0, r) for y, r in enumerate(rows.split(), y0)]

FLUKE = block(0, 44, """
KK.........
KTKK.......
.KTTK......
.KTTTK.....
..KTTTK....
..KTTTTK...
...KTTTTK..
...KKTTTTK.
....KKTTTK.
.....KTTTK.
....KKTTTK.
...KKTTTTK.
...KTTTTK..
..KTTTTK...
..KTTTK....
.KTTTK.....
.KTTKK.....
KTKK.......
KK.........
""")                                                      # two lobes swept back, the notch between them
TAIL = block(8, 43, """
................KKKKKKK
.............KKKSSSSSSS
...........KKSSSSSSmmmm
.........KKSSSSSmmmmmmm
.......KKSSSSmmmmmmmmmm
.....KKSSSmmmmmmmmmmsss
....KSSmmmmmmmmmsssssss
...KSmmmmmmmssssssssKKK
..KSmmmmmssssssKKKKK...
.KmmmssssssKKKK........
KsssssKKKKK............
KKKKKK.................
""")                                                      # long, out from under the shell's back and sloping down to the fluke
FAR_LEG = block(44, 47, """
..KgggggggK.....
..KggggggggK....
...KggggggggK...
...KgggggggggK..
....KggggggggK..
....KgggggggggK.
.....KggggggggK.
.....KgggggKBKBK
.....KKKKKKKKKKK
""")                                                      # the far fore leg, in the body's shade, reaching forward
BODY = [runs(48, 27, 'K1 G38 K1'), runs(49, 28, 'K1 g36 K1'), runs(50, 29, 'K1 g34 K1'), runs(51, 30, 'K35')]   # under the shell, between the legs
NECK = [runs(46, 60, 'K14')] + [runs(y, l, f'K1 g2 G{r - l - 5} B2 K1') for y, l, r in (
    (45, 60, 73), (44, 61, 74), (43, 62, 74), (42, 62, 75), (41, 63, 76), (40, 64, 76), (39, 65, 77), (38, 66, 78),
    (37, 67, 78), (36, 68, 79), (35, 69, 80), (34, 70, 80), (33, 70, 81), (32, 71, 81), (31, 72, 82), (30, 73, 82),
    (29, 73, 83), (28, 74, 83), (27, 74, 84), (26, 75, 84), (25, 75, 85), (24, 76, 85), (23, 76, 85), (22, 76, 86),
    (21, 77, 86), (20, 77, 86), (19, 77, 86))]          # leaning far forward out of the shell, rising straighter as it goes up
HEAD = block(74, 2, """
................KK..
...............KGBK.
..............KGGWK.
......KKKK...KGGWTK.
.....KGGGGKKKGGWTTK.
....KGGGGGGGGGWTTTK.
...KGGGGWKGGGGTTTTK.
...KgGGGKKGGGGWTWTKK
..KggGGGGGGGGGGGGGBK
..KgGGGTTGGGGGBBBBK.
..KgGGGGGGGTBBBBKK..
..KggGGGGGGBBBBK....
...KgGGGGGGBBBK.....
...KggGGGGGBBK......
...KgGGGGGGBBK......
...KggGGGGGBBK......
...KgGGGGGGBBK......
""")                                                      # small, tipped back, jaws open up and to our right, teeth on both; the eye; brown spots on its cheek
REAR_LEG = block(19, 45, """
.........KGGGGGGGGGK..
........KgGGGGGGGGGBK.
.......KggGGGGGGGGBBK.
......KggGGGGGGGGBBK..
.....KggGGGGGGGGBBK...
.....KggGGGGGGGBBK....
....KggGGGGGGGGBK.....
...KgggGGGGGGGBBK.....
..KggggGGGGGGGBK......
.KKgggggGGGGGBBK......
KgggggggggggggggK.....
KBKBKBKKKKKKKKKKK.....
KKKKKK................
""")                                                      # the near hind leg, splayed back, the foot flat, three claws
FRONT_LEG = block(52, 45, """
..KGGGGGGGGGK...........
..KgGGGGGGGGBK..........
..KggGGGGGGGBBK.........
...KggGGGGGGGBBK........
....KggGGGGGGGBBK.......
....KggGGGGGGGGBBK......
.....KggGGGGGGGGBK......
.....KggGGGGGGGGBBK.....
......KggGGGGGGGGBK.....
......KgggGGGGGGGGBKK...
......KggggggggggggBBKK.
......KggggggggggggKBKBK
......KKKKKKKKKKKKKKKKKK
""")                                                      # the near fore leg, reaching forward, three claws
SHELL = [runs(31, 40, 'K15'),
         runs(32, 35, 'K5 S15 K5'),
         runs(33, 32, 'K3 m4 S19 m2 K3'),
         runs(34, 30, 'K2 m5 K1 S10 K1 S9 m5 K2'),
         runs(35, 28, 'K2 s1 m5 K1 m3 S7 K1 S6 m11 K2'),
         runs(36, 27, 'K1 s2 m5 K1 m5 S5 K1 m3 S3 m14 K1'),
         runs(37, 26, 'K1 s3 m4 K1 m11 K1 m21 K1'),
         runs(38, 25, 'K1 s5 m37 s1 K1'),
         runs(39, 25, 'K1 s6 m35 s2 K1'),
         runs(40, 24, 'K1 s7 m35 s3 K1'),
         runs(41, 24, 'K1 s9 m32 s4 K1'),
         runs(42, 24, 'K1 s11 m29 s5 K1'),
         runs(43, 24, 'K1 s14 m24 s7 K1'),
         runs(44, 23, 'K8 s30 K11'),                      # the line above the rim, sagging in the middle
         runs(45, 23, 'K1 m7 K30 m10 K1'),
         runs(46, 23, 'K1 m47 K1'),
         runs(47, 24, 'K1 s45 K1'),
         runs(48, 25, 'K45')]                             # long and low, highest behind the middle, two seams between its plates; its rim over the tail and the neck
PARTS = (FLUKE, TAIL, FAR_LEG, BODY, NECK, HEAD, REAR_LEG, FRONT_LEG, SHELL)

def pose():
    """{pixel: letter}: the parts set down back to front."""
    g = {}
    for part in PARTS:
        for y, x0, t in part:
            for x, c in enumerate(t, x0):
                if c != '.': g[(x, y)] = c
    assert all(0 <= x < W and 1 <= y < H for x, y in g), sorted(p for p in g if not (0 <= p[0] < W and 1 <= p[1] < H))
    return g

FRAMES = lambda: [pose()]

def numbers(g):
    """What the bible measures, of one frame."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    bare = sorted(p for p in edge if g[p] != 'K')
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1),
            'colours': len(set(g.values()) - {'K'}), 'black inside %': round(100 * inner / len(g), 1), 'bare edge': bare[:12]}

if __name__ == '__main__':
    g = pose()
    for k, v in numbers(g).items(): print('%-16s %s' % (k, v))
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        panels = [image(g, (255, 170, 200, 255)), image(g, (0, 0, 0, 255)), image({p: 'K' for p in g}, (255, 170, 200, 255))]
        cv = Image.new('RGBA', (len(panels) * (W + 2) - 2, H), (40, 40, 40, 255))
        for i, im in enumerate(panels): cv.alpha_composite(im, (i * (W + 2), 0))
        cv.resize((cv.width * 6, cv.height * 6), Image.NEAREST).save(sys.argv[2])
