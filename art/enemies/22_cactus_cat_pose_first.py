"""22 Cactus Cat: how its first sitting pose was typed, before the user redrew it (green, eyes shut,
flowers on the tail). The sheet is built by 22_cactus_cat_design.py from their frame; this is kept as the record.

    python art/enemies/22_cactus_cat_pose_first.py show OUT.png   the pose, enlarged"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import flat_parts
W, H = 46, 35                                             # the built frame; row 0 stays empty
PAL = {'K': '000000', 'L': 'f4ce80', 'M': 'b2966a', 'D': '94703d',   # fur: lit, the body of it, under and away
       'I': 'e8e0c0', 'W': 'fcfcfc',                      # thorns, bone blades, muzzle and chest; the eyes' white
       'G': '4fa667', 'g': '2c6c44',                      # the tail, and its far side
       'P': 'ec8476'}                                     # inside the ears, nose, tongue, the drink in its cheeks
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)
block = lambda x0, y0, rows: [(y, x0, r) for y, r in enumerate(rows.split(), y0)]      # a drawing typed whole, set down with its top left at (x0, y0)

# each part: (row, first column, pixels); '.' leaves what is behind
TAIL = [                                                  # armoured in plates, branching, each arm thinning to a thorn
    (3, 9, 'I'), (4, 8, 'KGK'), (5, 8, 'KGK'), (6, 7, 'KGGK'), (7, 7, 'KGgK'), (8, 6, 'KGGgK'), (9, 6, 'KGGgK'), (10, 5, 'KGGgK'),
    (11, 5, 'KKKKK'), (12, 5, 'KGGgK'), (13, 5, 'KGGgK'), (14, 5, 'KGGgK'), (15, 5, 'KKKKK'),
    (16, 5, 'KGGggK'), (17, 5, 'KGGggK'), (18, 5, 'KGGggK'), (19, 6, 'KGGggg'), (20, 6, 'KKKKK'),
    (21, 6, 'KGGgg'), (22, 6, 'KGGg'), (23, 6, 'KGg'), (24, 6, 'KGg'), (25, 7, 'Kg'), (26, 8, 'K'),
    (14, 10, 'KK'), (13, 9, 'gGGK'), (12, 10, 'KGGK'), (11, 11, 'KGGK'), (10, 12, 'KGgK'), (9, 13, 'KGK'), (8, 13, 'KGK'), (7, 14, 'K'), (6, 14, 'I'),   # the arm toward its back
    (19, 3, 'KK'), (18, 2, 'KGGg'), (17, 1, 'KGGK'), (16, 0, 'KGGK'), (15, 0, 'KGgK'), (14, 0, 'KGK'), (13, 0, 'KGK'), (12, 1, 'K'), (11, 1, 'I'),      # the arm away from it
]
BODY = [                                                  # shoulders and chest, the haunch a lump beside them, the forelegs, the hind foot
    (15, 17, 'KK'),
    (16, 15, 'KKLLLL'),
    (17, 14, 'KLLLLMMM'),
    (18, 13, 'KLLLMMMMMMM'),
    (19, 12, 'KLLMMMMMMMMMDDDDDDDDDDDDDK'),
    (20, 11, 'KLLMMMMMMMMMMMMMMIIIIIIIMMMK'),
    (21, 11, 'KKKKKKKKKKMMMMMMIIIIIIIIIMMK'),
    (22, 10, 'KLLLLLLLLLLKKMMMMIIIIIIIIIMMK'),
    (23, 9, 'KLLLLLMMMMMMMMKMMMMIIIIIIIIMMK'),
    (24, 9, 'KLLMMMMMMMMMMMMKMMMIIIIIIIMMMK'),
    (25, 9, 'KLMMMMMMMMMMMMMKMMMMIIIIIMMMMK'),
    (26, 9, 'KMMMMMMMMMMMMMMKMMKMLLLKLLLMMK'),
    (27, 9, 'KMMMMMMMMMMMMMMKDDKMLLLKLLLMMK'),
    (28, 9, 'KDMMMMMMMMMMMMMKDDKMLLLKLLLMMK'),
    (29, 10, 'KDMMMMMMMMMMMKDDDDKMLLKLLLMK'),
    (30, 10, 'KDDMMMMMMMMMMKDDDDKMLLKLLLMK'),
    (31, 10, 'KDDMMMMKKKKKKKKDDDKMLLKLLLMK'),
    (32, 10, 'KDDDMMKLLLLLLLLKDKLLLLKLLLLLK'),
    (33, 11, 'KDDDDKMMKMMKMMKKKLKLLKLKLKLK'),
    (34, 12, 'KKKKKKKKKKKKKKKKKKKKKKKKKKK'),
]
BLADES = [                                                # a curved blade of bone from each foreleg
    (19, 40, 'K'), (20, 39, 'KIK'), (21, 40, 'KIK'), (22, 40, 'KIIK'), (23, 41, 'KIK'), (24, 41, 'KIIK'), (25, 41, 'KIIK'), (26, 41, 'KIIK'),
    (27, 40, 'KIIK'), (28, 39, 'KIIK'), (29, 38, 'KIIK'), (30, 38, 'IIK'), (31, 38, 'KK'),
    (19, 25, 'K'), (20, 24, 'KIK'), (21, 23, 'KIK'), (22, 22, 'KIIK'), (23, 22, 'KIK'), (24, 21, 'KIIK'), (25, 21, 'KIIK'), (26, 21, 'KIIK'),
    (27, 22, 'KIIK'), (28, 23, 'KIIK'), (29, 24, 'KIIK'), (30, 25, 'KII'), (31, 26, 'KK'),
]
HEAD = block(19, 1, """
..I..............I...
...I............I....
...KIK....K....KIK...
..KMPMK...K...KDMK...
..KMPPMK.KKKK.KDDMK..
.KMMPPMKKLLLLKKDDMMK.
.KKKKKKLLLLLLLKKKKKK.
KMMMLLLLLLLLLLLLLLLMK
KMMMMLLLLLLLLLLLLLLMK
KDMMMMLLLLLLLLLLLLMMK
KDMMMMKKKMLLLLLKKKMMK
KDMMMMMWKMLLLLLMWKMMK
KDDMMMMMMMIIIIIIIMMMK
KKDMPPMMMIIIIPPIIMPMK
.KKDMMMMMIIIIIIIIMMKK
..KKDMMMMIIIKPPKIMKK.
...KKKMMMMIIIPPIIKK..
.....KKKKKKKKPPKKK...
.............P.......
""")                                                      # ears and their spines; heavy lids, flushed cheeks, the tongue out
THORNS = [(15, 17, 'I'), (14, 16, 'I'), (13, 16, 'I'), (16, 15, 'I'), (15, 14, 'I'), (18, 13, 'I'), (17, 12, 'I'), (16, 11, 'I')]   # each rooted in the edge of its back

def pose():
    """{pixel: letter}: the parts set down back to front."""
    g = {}
    for part in (TAIL, BODY, BLADES, HEAD, THORNS):
        for y, x0, t in part:
            for x, c in enumerate(t, x0):
                if c != '.': g[(x, y)] = c
    assert all(0 <= x < W and 1 <= y < H for x, y in g), sorted(p for p in g if not (0 <= p[0] < W and 1 <= p[1] < H))
    return g

FRAMES = lambda: [pose()]

if __name__ == '__main__':
    fr = FRAMES()
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        cv = Image.new('RGBA', (W * len(fr) * 2 + 2 * (len(fr) * 2 - 1), H), (40, 40, 40, 255))
        for i, g in enumerate(fr):
            cv.alpha_composite(image(g, (255, 170, 200, 255)), (i * 2 * (W + 2), 0)); cv.alpha_composite(image(g, (0, 0, 0, 255)), ((i * 2 + 1) * (W + 2), 0))
        cv.resize((cv.width * 10, cv.height * 10), Image.NEAREST).save(sys.argv[2])
    else: sys.exit('this is the record of the first pose; the sheet is built by 22_cactus_cat_design.py')
    print(len(fr), 'frames | colours', sorted({c for g in fr for c in g.values()}), '| box', (min(p[0] for g in fr for p in g), min(p[1] for g in fr for p in g), max(p[0] for g in fr for p in g), max(p[1] for g in fr for p in g)))
