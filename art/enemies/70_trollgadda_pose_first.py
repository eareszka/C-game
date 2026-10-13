"""70 Trollgadda: how its first side view was typed, before the user redrew it (a shorter head, the mouth
gaping round a thick trunk, the canopy drawn in over the head). The sheet is built by 70_trollgadda_design.py
from their frame; this is kept as the record of the typed pose.

    python art/enemies/70_trollgadda_pose_first.py show OUT.png   the pose enlarged: on pink, on black, filled black

Every pixel is typed, a row of letters at a time, part by part and back to front -- canopy, trunk, fish,
fins -- and nothing is drawn by a stroke or a curve."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the frame, as the old sheet's; row 0 stays empty
PAL = {'K': '000000', 'g': '2c6c44', 'G': '4fa667', 'B': 'e8e0c0',   # outline; the fish: its back, its flank, its belly
       'A': '00a800', 'a': '4edc4a',                      # the leaves, and where they are lit (their shade is the fish's back)
       'T': '583518', 't': '815423',                      # wood and fins: under and away, and the body of it
       'W': 'fcfcfc'}                                     # the eye's white, the teeth
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)
block = lambda x0, y0, rows: [(y, x0, r) for y, r in enumerate(rows.split(), y0)]      # a drawing typed whole, set down with its top left at (x0, y0)

# each part: (row, first column, pixels); '.' leaves what is behind
CANOPY = block(23, 1, """
..................KKKKK...................................................
................KKaaaaaKKK..KK................KKKKK...KKK.................
..............KKaaaaaaaaaAKKaaK.............KKaaaaaKKKaaaKK...............
.............KaaaaaaaaaaAAAAaaaK...........KaaaaaaaaaaaaAAAK..............
............KaaaaaaaaaAAAAAAAAAAK..KKKK...KaaaaaaaaaAAAAAAAAK.............
............KaaaaaaaaAAAAAAAAAAAK.KaaaAKK.KaaaaaaaAAAAAAAAAAK.............
...........KaaaaaaaAAAAAAAAAAAAAAKaaaAAAAKaaaaaaAAAAAAAAAAAAAK............
...........KaaaaaaAAAAAAAAAAAAAAAAAAAAAAAAAAAaAAAAAAAAAAAAAAAK.KKKKK......
.....KKK..KaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKaaaaaKK....
...KKaaaKKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAaaaaaAK...
..KaaaaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAaAAAAAK..
.KaaaaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK.
.KaAaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK.
KAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK
KAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK
KAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK
.KAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK.
.KgggggAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK.
..KggggggKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK..
...KggggK.KgggggggAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK..
....KKKK...KgggggggggggKAAAAAAAggggAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgK...
............KgggggggggK.KAAggggggggggKAAAggggggKAAAgAggggggggggggggggK....
.............KKgggggKK...KggggggggggK.KgggggggK.KgggggggggggggggggggK.....
...............KKKKK.....KggggggggggK..KggggKK...KggggggggggggggggKK......
..........................KKggggggKK....KKKK......KKggggggggggggKK........
............................KKKKKK..................KKKKKKKKKKKK..........
""")                                                      # one mass of five lumps of different sizes over the fish, each hanging a little
LUMPS = [                                                 # the line round each lump where it stands in front of the next, and two clumps inside the big ones
    (10, 33, 'K'), (11, 34, 'K'), (12, 34, 'K'), (13, 35, 'K'), (14, 35, 'K'), (15, 35, 'K'), (16, 35, 'K'), (17, 34, 'K'), (18, 33, 'K'),          # the low left lump, in front
    (8, 56, 'K'), (9, 55, 'K'), (10, 55, 'K'), (11, 55, 'K'), (12, 55, 'K'), (13, 56, 'K'), (14, 57, 'K'), (15, 58, 'KKK'), (14, 61, 'KK'),
    (13, 63, 'K'), (12, 64, 'K'), (11, 64, 'K'), (10, 64, 'K'), (9, 64, 'K'), (8, 64, 'K'),                                                       # the small one between the two big ones, in front of both
    (16, 59, 'K'), (17, 60, 'K'), (18, 60, 'K'), (19, 60, 'K'), (20, 60, 'K'), (21, 60, 'K'),                                                     # the two big ones, below it
    (10, 85, 'K'), (11, 85, 'K'), (12, 86, 'K'), (13, 86, 'K'), (14, 87, 'K'), (15, 88, 'K'), (16, 89, 'KK'),                                     # the right one, behind
    (20, 46, 'K'), (19, 47, 'K'), (18, 47, 'K'), (17, 48, 'K'), (16, 49, 'K'), (15, 49, 'K'),
    (21, 70, 'K'), (20, 70, 'K'), (19, 71, 'K'), (18, 71, 'K'), (17, 72, 'K'), (16, 72, 'K'), (25, 79, 'K'), (24, 79, 'K'), (23, 78, 'K'), (22, 78, 'K'),   # up from underneath, where one hangs in front of the next
    (13, 37, 'K'), (12, 38, 'K'), (11, 39, 'KKKK'), (12, 43, 'K'), (13, 44, 'K'), (14, 44, 'K'),                                                  # a clump in the left big one
    (12, 69, 'K'), (11, 70, 'K'), (10, 71, 'KKKK'), (11, 75, 'K'), (12, 76, 'K'), (13, 76, 'K'),                                                  # and in the right
    (13, 27, 'K'), (12, 28, 'KK'), (13, 30, 'K'), (13, 90, 'K'), (12, 91, 'KK'), (13, 93, 'K'),                                                   # and a small one in each end lump
]
LIGHT = [(12, 39, 'aaaa'), (13, 38, 'aaa'), (11, 71, 'aaaa'), (12, 70, 'aaa')]                                    # the tops of those clumps
SHADE = [(16, 57, 'g'), (16, 60, 'gg'), (13, 36, 'g'), (14, 36, 'g'), (15, 36, 'g'), (16, 36, 'g'), (17, 35, 'g'),
         (11, 86, 'g'), (12, 87, 'g'), (13, 87, 'g'), (14, 88, 'g'), (15, 89, 'g')]                               # on the lump behind, beside the one in front
TRUNK = [                                                 # out of the mouth, a knee where it turns up, a broken stub, thinning; it forks under the leaves
    (41, 72, 'KKKKKKKKKKKKKKK'),
    (40, 75, 'TTTTTTTTTTTTKK'),
    (39, 75, 'tttttttttttttTK'),
    (38, 75, 'ttttttttttttttTK'),
    (37, 75, 'KKKKKKKKttttttTTK'),
    (36, 83, 'KtttttTTK'), (35, 84, 'KtttttTK'), (34, 85, 'KttttTK'), (33, 85, 'KttttTK'),
    (32, 86, 'KtttTKK'), (31, 86, 'KtttTttK'), (30, 86, 'KtttTKKK'),                                               # the stub
    (29, 86, 'KttTK'), (28, 85, 'KtttTK'), (27, 85, 'KttTK'), (26, 84, 'KtttTK'), (25, 84, 'KttTK'), (24, 83, 'KttTK'),
    (23, 82, 'KttKtTK'), (22, 81, 'KttKKKtTK'),
    (21, 80, 'KttK'), (20, 79, 'KtKK'), (19, 78, 'KtK'), (18, 77, 'KtK'), (17, 77, 'KK'),                          # the bough back over the fish
    (21, 87, 'KttK'), (20, 88, 'KttK'), (19, 89, 'KtK'), (18, 90, 'KtK'), (17, 91, 'KK'),                          # the bough away from it
]
FISH = block(9, 26, """
KK
KtKK.....................KKKKKKKK
KtttKK..............KKKKKggggggggKKKKK....KKKKK
.KttttKK.........KKKggggggggggggggggggKKKKgggggK
.KttttttKK.....KKggggggggggggggggggggggggggKKKggK
..KtttttttKK.KKgggggggggggggggggggggggggggKWWKKKgK
...KtttttttKKgggggggGGGGGGGGGGGGGGGGGGggggKWKWWKGgKK
....KttttttKgggGGGGGGGGGGGGGGGGGGGGGGGGGGGGKKKKGGGggKKK
.....KtttttKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGgggKKKKKKK
.....KtttttKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGgggggggKKKK
......KttttKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGK
.....KtttttKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGKKKKKKKKKKKKKKK
.....KtttttKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGKttttttttttttttt
....KttttttKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGKttttttttttttttt
...KtttttttKKGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGKTTTTTTTTTTTTTTT
..KtttttttKK.KKBBBBGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGKKKKKKKKKKKKK
.KttttttKK.....KKBBBBBBBBGGGGGGGGGGGGGGGGBBBBBBBBBBBBBBBBBBBBBBK
.KttttKK.........KKBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBKKK
KtttKK.............KKBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBKKKK
KtKK.................KKKBBBBBBBBBBBBBBBBBBBBBBKKKKKKKKKKK
KK......................KKKKBBBBBBBBBBBBBKKKKK
............................KKKKKKKKKKKKK
""")                                                      # forked tail, fat body, a brow, the long flat bill shut on the trunk, the lower jaw a pixel longer
GILL = [(31, 49, 'K'), (32, 48, 'K'), (33, 48, 'K'), (34, 46, 'gK'), (35, 46, 'gK'), (36, 46, 'gK'), (37, 46, 'gK'), (38, 46, 'gK'),
        (39, 48, 'K'), (40, 48, 'K'), (41, 49, 'K'), (42, 49, 'K')]                                               # the gill's edge, and the shade under it
JAW = [(41, 59, 'K'), (42, 58, 'K'), (43, 57, 'K'), (44, 56, 'K')]                                                              # the hinge: lower jaw from cheek
RAYS = [(32, 16, 'K'), (31, 15, 'K'), (30, 14, 'K'), (40, 16, 'K'), (41, 15, 'K'), (42, 14, 'K'),                                # one ray down the middle of each lobe of the tail
        (28, 25, 'K'), (27, 26, 'K'), (26, 27, 'K'), (45, 26, 'K'), (46, 27, 'K'), (41, 44, 'K'), (42, 43, 'K')]                 # and in the fins on its back, under its tail and behind its gill
TEETH = [(38, 63, 'W'), (38, 67, 'W'), (38, 71, 'W'), (40, 65, 'W'), (40, 69, 'W')]                              # biting into the wood
FINS = [
    (24, 27, 'KKK'), (25, 25, 'KKtttK'), (26, 23, 'KKtttttK'), (27, 22, 'KtttttttK'), (28, 21, 'KtttttttK'), (29, 21, 'Ktttt'), (30, 21, 'Ktt'), (31, 21, 'K'),   # on its back, far aft as a pike's
    (43, 23, 'Ktt'), (44, 23, 'Ktttt'), (45, 24, 'Kttttt'), (46, 25, 'KtttttK'), (47, 26, 'KKKKK'),                # under its tail
    (48, 38, 'KTTTTK'), (49, 37, 'KTTTKK'), (50, 37, 'KKKK'),                                                      # under its belly, the far one
    (39, 45, 'KKK'), (40, 43, 'KKttK'), (41, 41, 'KKtttK'), (42, 40, 'KtttTK'), (43, 40, 'KKKKK'),                 # behind the gill
]
PARTS = (CANOPY, LIGHT, SHADE, LUMPS, TRUNK, FISH, GILL, JAW, TEETH, FINS, RAYS)
FISH_ROWS, GILL_AT, TAIL_AT = (24, 50), 47, 9             # the rows the fish is in; the gill's column and the tail's: its head is all of it ahead of the gill

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
    fish = [p for p in g if g[p] in 'GgB' and FISH_ROWS[0] <= p[1] <= FISH_ROWS[1] and p[0] < 75]
    leaves = [p for p in g if g[p] in 'Aa']
    snout = max(p[0] for p in fish)
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'edge that is black %': round(100 * (len(edge) - len(bare)) / len(edge), 1), 'bare edge': bare[:8],
            'head share %': round(100 * (snout - GILL_AT + 1) / (snout - TAIL_AT + 1)),
            'fish middle': (round(sum(p[0] for p in fish) / len(fish) + 0.5, 1), round(sum(p[1] for p in fish) / len(fish) + 0.5, 1)),
            'canopy box': (min(p[0] for p in leaves), min(p[1] for p in leaves), max(p[0] for p in leaves), max(p[1] for p in leaves)), 'frame middle': (W / 2, H / 2)}

if __name__ == '__main__':
    fr = FRAMES()
    for k, v in numbers(fr[0]).items(): print('%-22s %s' % (k, v))
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        g = fr[0]
        black = {p: 'K' for p in g}
        panels = [image(g, (255, 170, 200, 255)), image(g, (0, 0, 0, 255)), image(black, (255, 170, 200, 255))]
        cv = Image.new('RGBA', (len(panels) * (W + 2) - 2, H), (40, 40, 40, 255))
        for i, im in enumerate(panels): cv.alpha_composite(im, (i * (W + 2), 0))
        cv.resize((cv.width * 6, cv.height * 6), Image.NEAREST).save(sys.argv[2])
    else: sys.exit('this is the record of the first pose; the sheet is built by 70_trollgadda_design.py')
