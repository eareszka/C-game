"""71 Namungumi: how its first two poses were typed (front and 3/4 front), in the old sheet's colours, before the
user redrew the front in Aseprite (no black line round the head, grey fangs and claws, the veins run on) and asked for
the 3/4 view to be "less shape formed and matching the new style". The sheet is built by 71_namungumi_design.py;
this is kept as the record.

    python art/enemies/71_namungumi_pose_first.py show OUT.png   both poses enlarged: on pink, on black, filled black

Every pixel is typed, a row of letters at a time, part by part and back to front; nothing is drawn by a stroke or a curve."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the frame, as the old sheet's; row 0 stays empty
PAL = {'K': '000000', 'D': '14101e', 'L': '2b1f40',       # outline, and the pupil; its hide, and where it is lit
       'w': 'c6ccda',                                     # the pale veins between its plates
       'r': '792727', 'R': 'b6433d',                      # the skirt and the gums: in shadow, and in the light
       'h': '84a7e9',                                     # the glow round its eye
       'W': 'fcfcfc', 'C': 'bcbeca'}                      # the eye's white, fangs and claws; the fangs' shaded side
EYE = {'D': (49, 42), 'DR': (74, 41)}                     # the pupil, in each view: where its beams leave from
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)
block = lambda x0, y0, rows: [(y, x0, r) for y, r in enumerate(rows.split(), y0)]      # a drawing typed whole, set down with its top left at (x0, y0)

# each part: (row, first column, pixels); '.' leaves what is behind
Q_FAR = [(59, 22, 'KKKK'), (60, 22, 'KDDK'), (61, 21, 'KDDDK'), (62, 21, 'KDDDDK'), (63, 21, 'KKKKKK'), (60, 37, 'KKKKK'), (61, 37, 'KDDDK'), (62, 36, 'KDDDDDK'), (63, 36, 'KKKKKKK')]
Q_SKIRT = block(16, 47, """
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
KRRRRRRRKRRRRRRRRRRRRRRRRRRRRRRRR
.KRRRRRK.KRRRRRRRRRKRRRRRRRKRRRRK
..KRRRK...KRRRRRRRK.KRRRRRK.KRRK.
...KKK.....KRRRRRK...KRRRK...KK..
............KKKKK.....KKK........
""")
Q_CREASES = [(54, 24, 'K'), (53, 24, 'K'), (52, 25, 'K'), (55, 35, 'K'), (54, 35, 'K'), (53, 34, 'K'), (52, 34, 'K'), (55, 43, 'K'), (54, 43, 'K'), (53, 44, 'K')]
Q_LEGS = [(50, 12, 'KKKKKKK'), (51, 12, 'KDDDDDK'), (52, 12, 'KDDDDDK'), (53, 12, 'KDDDDDK'), (54, 13, 'KDDDDK'), (55, 13, 'KDDDDK'), (56, 13, 'KDDDDKK'), (57, 13, 'KDDDDDK'), (58, 12, 'KDDDDDDK'), (59, 12, 'KDDDDDDDK'), (60, 11, 'KDDDDDDDDDK'), (61, 11, 'KKWKKWKKWKK'), (62, 12, 'KWKKWKKWK'), (63, 12, 'KKKKKKKKK'), (49, 48, 'KKKKKKKKK'), (50, 48, 'KDDDDDDDK'), (51, 48, 'KDDDDDDDK'), (52, 48, 'KDDDDDDDK'), (53, 49, 'KDDDDDDK'), (54, 49, 'KDDDDDDK'), (55, 49, 'KDDDDDKK'), (56, 49, 'KDDDDDK'), (57, 49, 'KDDDDDDK'), (58, 48, 'KDDDDDDDK'), (59, 48, 'KDDDDDDDDK'), (60, 47, 'KDDDDDDDDDDK'), (61, 47, 'KKWKKWKKWKKK'), (62, 48, 'KWKKWKKWKK'), (63, 48, 'KKKKKKKKKK')]
Q_CLOAK = block(9, 31, """
......................KKKKKKK
...................KKKLLLLLLLKKK
.................KKLLLLLLLLLLLDDKK
...............KKLLLLLLDDDDDDDDDDDKK
.............KKLLLDDDDDDDDDDDDDDDDDDKK
............KLLDDDDDDDDDDDDDDDDDDDDDDDKK
...........KLDDDDDDDDDDDDDDDDDDDDDDDDDDDKK
..........KLDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDKK
.........KLDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDKK
........KLDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDKK
........KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.....KDDDDDDDDDDDDDDDDDDDDDDDKKKKKDDDDDDDDDDDDDDDK
.....KDDDDDDDDKKKKKDDDDDDDDKK.....KKKDDDDDDDDDDDDK
.....KDDDDDKKK.....KKKDDDKK..........KKKKKKKKKKKKK
.....KDDDKK...........KKK
.....KDKK
.....KK
""")
Q_PLATES = [(36, 23, 'w'), (37, 23, 'w'), (38, 22, 'w'), (39, 22, 'w'), (40, 22, 'w'), (41, 22, 'w'), (42, 23, 'w'), (43, 23, 'w'), (44, 24, 'w'), (45, 24, 'w'), (46, 25, 'w'), (47, 25, 'w'), (33, 32, 'w'), (34, 32, 'w'), (35, 32, 'w'), (36, 31, 'w'), (37, 31, 'w'), (38, 31, 'w'), (39, 31, 'w'), (40, 31, 'w'), (41, 32, 'w'), (42, 32, 'w'), (43, 32, 'w'), (44, 33, 'w'), (45, 33, 'w'), (46, 33, 'w'), (47, 33, 'w'), (48, 33, 'w'), (49, 33, 'w'), (34, 42, 'w'), (35, 43, 'w'), (36, 44, 'w'), (37, 44, 'w'), (38, 45, 'w'), (39, 45, 'w'), (40, 45, 'w'), (41, 45, 'w'), (42, 45, 'w'), (43, 45, 'w'), (44, 44, 'w'), (45, 44, 'w'), (46, 44, 'w'), (47, 44, 'w'), (38, 50, 'w'), (39, 51, 'w'), (40, 51, 'w'), (41, 52, 'w'), (42, 52, 'w'), (43, 52, 'w'), (44, 52, 'w'), (45, 52, 'w'), (46, 52, 'w'), (47, 52, 'w'), (48, 52, 'w'), (44, 16, 'wwww'), (43, 20, 'www'), (40, 23, 'wwwww'), (41, 28, 'wwww'), (39, 32, 'wwwwwww'), (40, 39, 'wwwwww'), (43, 46, 'wwwwww'), (41, 53, 'wwwww')]
Q_HEAD = block(57, 34, """
.........KKKKKKK
......KKKLLLLLLLKKK
....KKLLLLLLLLLDDDDKK
...KLLLLLLLDDDDDDDDDDKK
..KLLLLDDDDDDDDKKKKKDDDK
.KLLDDDDDDDDDDDDhhhDDDDDK
.KDDDDDDDDDDDDDhWWWhDDDDDK
KDDDDDDDDDDDDDDhWKWhDDDDDDK
KDDDDDDDDDDDDDDhWWWhDDDDDDDK
KDDDDDDDDDDDDDDDhhhDDDDDDDDK
KDDDDDDDDDDDDDDDDDDDDDDDDDDDK
KDDDDDDDDDDDDDDDDDDDDDDDDDDDK
KDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.KDDDDDDDDDDDDDDDDDDDDDDDDDDK
.KDDDDDDDDDDDDDDDDDDDDDDDDDK
..KDDDDKKKKKKKKKKKKKKKKKKKKK
...KDDKRRRRRRRRRRRRRRRRRRRK
....KKKrrrrrrrrrrrrrrrrrKK
""")
Q_FANGS = block(63, 52, """
KWWCKKWWCKKWWCKKWCK
KWWCKKWWCKKWWCKKWCK
KWWCKKWWCKKWWCKKWK.
KWWK.KWWCKKWWCKKWK.
KWCK.KWWK.KWWK..K..
KWK..KWWK.KWCK.....
.K...KWCK.KWK......
.....KWK..KWK......
.....KWK...K.......
......K............
""")
F_SKIRT = block(28, 48, """
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRK
KRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRK.
.KRRRRRKRRRRRRRRKRRRRRRRRRKRRRRRRRKRRRRRK..
..KRRRK.KRRRRRRK.KRRRRRRRK.KRRRRRK.KRRRK...
...KKK...KRRRKK...KRRRRRK...KRRRK...KKK....
..........KKK......KKKKK.....KKK...........
""")
F_CREASES = [(55, 35, 'K'), (54, 35, 'K'), (53, 36, 'K'), (55, 62, 'K'), (54, 62, 'K'), (53, 61, 'K')]
F_LEGS = [(50, 23, 'KKDDDDDK'), (51, 23, 'KDDDDDDK'), (52, 23, 'KDDDDDDK'), (53, 23, 'KDDDDDDK'), (54, 24, 'KDDDDDK'), (55, 24, 'KDDDDDK'), (56, 24, 'KDDDDDK'), (57, 23, 'KDDDDDDK'), (58, 23, 'KDDDDDDK'), (59, 22, 'KDDDDDDDK'), (60, 21, 'KDDDDDDDDDK'), (61, 21, 'KKWKKWKKWKK'), (62, 22, 'KWKKWKKWK'), (63, 22, 'KKKKKKKKK'), (50, 68, 'KDDDDDKK'), (51, 68, 'KDDDDDDK'), (52, 68, 'KDDDDDDK'), (53, 68, 'KDDDDDDK'), (54, 68, 'KDDDDDK'), (55, 68, 'KDDDDDK'), (56, 68, 'KDDDDDK'), (57, 68, 'KDDDDDDK'), (58, 68, 'KDDDDDDK'), (59, 68, 'KDDDDDDDK'), (60, 67, 'KDDDDDDDDDK'), (61, 67, 'KKWKKWKKWKK'), (62, 68, 'KWKKWKKWK'), (63, 68, 'KKKKKKKKK')]
F_CLOAK = block(20, 31, """
........................KKKKKKKKKKK
....................KKKKLLLLLLLLLLLKKKK
.................KKKLLLLLLLLLLLLLLLLLLLKKK
...............KKLLLLLLLLDDDDDDDDDDDDDDDDDKK
.............KKLLLLDDDDDDDDDDDDDDDDDDDDDDDDDKK
...........KKLLDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDKK
..........KLDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.........KLDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
........KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
......KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
....KDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.....KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
""")
F_PLATES = [(36, 35, 'w'), (37, 34, 'w'), (38, 34, 'w'), (39, 33, 'w'), (40, 33, 'w'), (41, 32, 'w'), (42, 32, 'w'), (43, 32, 'w'), (44, 31, 'w'), (45, 31, 'w'), (46, 31, 'w'), (47, 31, 'w'), (48, 31, 'w'), (33, 42, 'w'), (34, 42, 'w'), (35, 41, 'w'), (36, 41, 'w'), (37, 41, 'w'), (32, 49, 'w'), (33, 49, 'w'), (34, 49, 'w'), (35, 49, 'w'), (33, 56, 'w'), (34, 56, 'w'), (35, 57, 'w'), (36, 57, 'w'), (37, 57, 'w'), (36, 63, 'w'), (37, 64, 'w'), (38, 64, 'w'), (39, 65, 'w'), (40, 65, 'w'), (41, 66, 'w'), (42, 66, 'w'), (43, 66, 'w'), (44, 67, 'w'), (45, 67, 'w'), (46, 67, 'w'), (47, 67, 'w'), (48, 67, 'w'), (42, 27, 'wwwww'), (39, 34, 'wwww'), (40, 66, 'wwwww'), (44, 68, 'wwwww')]
F_HEAD = block(35, 36, """
..........KKKKKKKKK
.......KKKLLLLLLLLLKKK
.....KKLLLLLLLLLLLLLLLKK
...KKLLLLDDDKKKKKDDDDDDDKK
..KLLDDDDDDDDhhhDDDDDDDDDDK
.KLDDDDDDDDDhWWWhDDDDDDDDDDK
.KDDDDDDDDDDhWKWhDDDDDDDDDDK
KDDDDDDDDDDDhWWWhDDDDDDDDDDDK
KDDDDDDDDDDDDhhhDDDDDDDDDDDDK
KDDDDDDDDDDDDDDDDDDDDDDDDDDDK
KDDDDDDDDDDDDDDDDDDDDDDDDDDDK
.KDDDDDDDDDDDDDDDDDDDDDDDDDK
.KDDDDDDDDDDDDDDDDDDDDDDDDDK
..KDDKKKKKKKKKKKKKKKKKKKDDK
...KKKRRRRRRRRRRRRRRRRRKKK
......KrrrrrrrrrrrrrrrK
""")
F_GUM = [(52, 56, 'K')]
F_FANGS = block(42, 52, """
KWCKWWCKWWCKWK
KWCKWWCKWWCKWK
KWKKWWCKWWCKWK
KWKKWWCKWWCKK.
.K.KWWKKWWCK..
...KWCKKWWK...
...KWK.KWCK...
....K..KWK....
.......KWK....
........K.....
""")

VIEWS = {'D': (F_SKIRT, F_CREASES, F_LEGS, F_CLOAK, F_PLATES, F_HEAD, F_GUM, F_FANGS),
         'DR': (Q_FAR, Q_SKIRT, Q_CREASES, Q_LEGS, Q_CLOAK, Q_PLATES, Q_HEAD, Q_FANGS)}

def pose(view):
    """{pixel: letter}: that view's parts set down back to front."""
    g = {}
    for part in VIEWS[view]:
        for y, x0, t in part:
            for x, c in enumerate(t, x0):
                if c != '.': g[(x, y)] = c
    assert all(0 <= x < W and 1 <= y < H for x, y in g), sorted(p for p in g if not (0 <= p[0] < W and 1 <= p[1] < H))
    assert g[EYE[view]] == 'K' and all(g[flat_parts.add(EYE[view], d)] == 'W' for d in flat_parts.N4), view   # the pupil, in its white
    return g

def numbers(g):
    """What the bible measures, of one pose."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    bare = sorted(p for p in edge if g[p] != 'K')
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'edge that is black %': round(100 * (len(edge) - len(bare)) / len(edge), 1), 'open edge': bare}

if __name__ == '__main__':
    for v in VIEWS:
        print(v)
        for k, val in numbers(pose(v)).items(): print('  %-22s %s' % (k, val))
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        panels = [f(pose(v)) for v in VIEWS for f in (lambda g: image(g, (255, 170, 200, 255)), lambda g: image(g, (0, 0, 0, 255)), lambda g: image({p: 'K' for p in g}, (255, 170, 200, 255)))]
        cv = Image.new('RGBA', (3 * (W + 2) - 2, 2 * (H + 2) - 2), (40, 40, 40, 255))
        for i, im in enumerate(panels): cv.alpha_composite(im, ((i % 3) * (W + 2), (i // 3) * (H + 2)))
        cv.resize((cv.width * 6, cv.height * 6), Image.NEAREST).save(sys.argv[2])
        for v in VIEWS: image(pose(v), (255, 170, 200, 255)).crop((0, 26, W, H)).resize((W * 14, (H - 26) * 14), Image.NEAREST).save(sys.argv[2].replace('.png', '_%s_big.png' % v))
    else: sys.exit('this is the record of the first poses; the sheet is built by 71_namungumi_design.py')
