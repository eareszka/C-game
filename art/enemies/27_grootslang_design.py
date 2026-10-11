"""27 Grootslang, big tier: its front pose, typed by hand to art/direction/SPRITE_STYLE.md, and its five frames.

    python art/enemies/27_grootslang_design.py                        writes 27_grootslang.txt and .json
    python art/enemies/27_grootslang_design.py show OUT.png [OUT.gif]   its frames, enlarged

The great snake with an elephant's head. The user, 2026-10-10: "front facing only but similar
pose with elephant head and pile of snake and tail", and "make sure not to use shapes and follow
the bible". So this is the old sheet's layout -- the head on a mound of coils, the tail up beside
it with its rattle -- drawn again flat, and every pixel of it is typed: no stroke, line or curve
is worked out by code. The tables are rows of letters. The pile and the tail are typed whole; the
head is its left half and is mirrored.

The pile is one body wound three times round, so the lines between its turns climb to the right
and its two sides bulge at different heights; the last turn's end comes up on the right as the tail.

The fight fires from fixed spots in the 98x65 frame (class Grootslang), so the drawing ends on
them: the tusk tips, the trunk's tip and the rattle's tip (SPOTS, checked below).

The user took the pose as typed ("honestly it looks perfect show entire gif"), so it is frame 0.
The other four draw nothing new; they move its pixels: it sinks a pixel or two as it breathes,
the ears flap a column wider and narrower, the end of the trunk swings, the rattle's tip shakes."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the built frame; row 0 stays empty
MID = W // 2 - 1                                          # the last column of the left half
PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda',   # hide: under and away, the body of it, lit
       'I': 'e8e0c0', 'i': 'b2966a',                      # tusks and rattle, and their shade
       'P': 'ec8476', 'W': 'fcfcfc'}                      # inside the ears; the eyes
SPOTS = {'left tusk': (37, 34), 'right tusk': (60, 34), 'trunk': (48, 47), 'rattle': (80, 8)}   # where the fight's shots leave
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# the pile: row -> (first column, pixels). Lit on the shoulder of each turn, dark under the turn above and where it turns under.
PILE = {
    31: (36, 'K' * 27),
    32: (34, 'KK' + 'LLL' + 'D' * 20 + 'MMMM' + 'KK'),     # the dark under the jaw
    33: (32, 'KK' + 'LLLLL' + 'M' + 'D' * 18 + 'M' * 7 + 'KK'),
    34: (30, 'KK' + 'LLLLL' + 'MMMM' + 'D' * 16 + 'M' * 10 + 'K'),
    35: (29, 'K' + 'LLLL' + 'M' * 34 + 'K'),
    36: (28, 'K' + 'LL' + 'M' * 38 + 'K'),
    37: (28, 'K' + 'M' * 40 + 'K'),
    38: (28, 'K' + 'M' * 36 + 'DDD' + 'K'),
    39: (28, 'K' + 'M' * 30 + 'D' * 7 + 'K' * 8),          # the top turn ends; the shoulder of the middle one
    40: (29, 'KD' + 'M' * 19 + 'D' * 9 + 'K' * 8 + 'L' * 7 + 'KKK'),
    41: (30, 'K' + 'DD' + 'M' * 8 + 'D' * 9 + 'K' * 9 + 'D' * 8 + 'L' * 10 + 'KK'),
    42: (31, 'K' + 'D' * 9 + 'K' * 9 + 'D' * 9 + 'M' * 12 + 'L' * 8 + 'K'),
    43: (24, 'K' * 17 + 'D' * 9 + 'M' * 30 + 'K'),
    44: (21, 'KKK' + 'L' * 8 + 'D' * 9 + 'M' * 39 + 'K'),
    45: (19, 'KK' + 'L' * 10 + 'M' * 49 + 'K'),
    46: (18, 'K' + 'L' * 6 + 'M' * 55 + 'K'),
    47: (17, 'K' + 'LL' + 'M' * 56 + 'DDD' + 'K'),
    48: (17, 'K' + 'M' * 54 + 'D' * 5 + 'KK'),
    49: (17, 'K' + 'M' * 49 + 'D' * 11 + 'K' * 6),         # the middle turn ends; the shoulder of the lowest
    50: (17, 'K' + 'M' * 36 + 'D' * 13 + 'K' * 11 + 'L' * 6 + 'KK'),
    51: (18, 'KD' + 'M' * 21 + 'D' * 13 + 'K' * 13 + 'D' * 11 + 'L' * 8 + 'K'),
    52: (19, 'K' + 'DDD' + 'M' * 5 + 'D' * 13 + 'K' * 13 + 'D' * 13 + 'M' * 12 + 'L' * 8 + 'K'),
    53: (20, 'K' + 'D' * 7 + 'K' * 13 + 'D' * 13 + 'M' * 33 + 'K'),
    54: (14, 'K' * 14 + 'D' * 13 + 'M' * 46 + 'K'),
    55: (12, 'KK' + 'L' * 7 + 'D' * 7 + 'M' * 59 + 'K'),
    56: (11, 'K' + 'L' * 9 + 'M' * 66 + 'K'),
    57: (10, 'K' + 'L' * 5 + 'M' * 71 + 'K'),
    58: (10, 'K' + 'M' * 76 + 'K'),
    59: (10, 'K' + 'M' * 76 + 'K'),
    60: (10, 'KD' + 'M' * 73 + 'DD' + 'K'),
    61: (11, 'K' + 'DDD' + 'M' * 68 + 'DDD' + 'K'),
    62: (12, 'KKK' + 'D' * 68 + 'KKK'),
    63: (15, 'K' * 68),                                    # the base line
}

# the head, in front of the pile: ear, skull, eye, tusk, jaw, trunk -- one drawing, row by row, its left half
# ('.' leaves what is behind; every row runs to the middle of the frame)
HEAD = {
    4: (27, 'KKKKK.................'),
    5: (24, 'KKKLLLLLKK......KKKKKK...'),
    6: (22, 'KKLLLLMMMMMMK...KKLLLLLLKKK'),
    7: (21, 'KLLMMMMMMMMMMMKKKLLLLLLLLLMM'),
    8: (20, 'KLMMMMMMMMMMMMDDKMLLLLLLLLLMM'),
    9: (20, 'KMMMMPPPPPMMMMDDKDMLLLLLLLMMM'),
    10: (20, 'KMMMPPPPPPPMMMDDKDMMLLLLLMMMM'),
    11: (20, 'KMMPPPPPPPPPMMDDKDMMMLLLMMMMM'),
    12: (20, 'KMMPPPPPPPPPMMDDKDMMMMMMMMMMM'),
    13: (20, 'KMMPPPPPPPPPMDDDKDMMMMMMMMMMM'),
    14: (20, 'KMMPPPPPPPPPMDDDDKDMMMMMMMMMM'),
    15: (21, 'KMMPPPPPPPPMDDDDKDKKMMMMMMMM'),               # the brow ...
    16: (21, 'KMMPPPPPPPPMDDDDKDMMKKMMMMMM'),
    17: (22, 'KMMPPPPPPPMDDDDKDMWKDMMMMMM'),                # ... and the eye under it
    18: (21, 'KMMMPPPPPPPMDDDKDMMMMMMMMMMM'),
    19: (21, 'KMMMPPPPPPPMDDDKDMMMMMMMMMMM'),
    20: (22, 'KMMMPPPPPPMDDDKDMMMMMKMMMLL'),                # the trunk's side begins
    21: (22, 'KMMMMPPPPPMDDDKDMMMMMKMMMLL'),
    22: (23, 'KMMMMPPPPMDDDDKDMMMMKMMMLL'),
    23: (24, 'KMMMMPPPMDDDDKDMMMMKMMMLL'),
    24: (25, 'KMMMMMMMDDDDDKDMMMKKKKLL'),                   # a crease
    25: (26, 'KMMMMMMMDDDDKKKKKKMMMLL'),                    # the cheek's under-edge; the tusk leaves it
    26: (27, 'KKMMMMMDDDKIIiKDKMMMLL'),
    27: (29, 'KMMMMDDDKIIiKDKMMMLL'),
    28: (30, 'KKMMDDKIIiKDDKMMMLL'),
    29: (32, 'KKDDKIIiKDDDKMMMM'),
    30: (34, 'KKIiKKKKKKKKKMM'),                            # the jaw's under-edge; a crease
    31: (35, 'KIiK.....KMMMM'),
    32: (35, 'KIK......KMMMM'),
    33: (36, 'KIK.....KMMMM'),
    34: (37, 'K......KMMMM'),                               # the tusk's tip
    35: (45, 'KMMM'),
    36: (45, 'KKMM'),
    37: (45, 'KMMM'),
    38: (45, 'KMMM'),
    39: (45, 'KMMM'),
    40: (45, 'KMMM'),
    41: (46, 'KMM'),
    42: (46, 'KMM'),
    43: (46, 'KKM'),
    44: (46, 'KMM'),
    45: (46, 'KMM'),
    46: (46, 'KMM'),
    47: (47, 'KK'),                                         # the trunk's tip
}
wrong = {y: x + len(t) for y, (x, t) in HEAD.items() if x + len(t) != MID + 1}
assert not wrong, f'HEAD: these rows do not end on the middle column: {wrong}'

# the tail, in front of the ear: the end of the lowest turn, up the right side to its rattle. Typed whole.
TAIL = {
    8: (80, 'KK'),                                        # the rattle: four beads, the smallest at the tip
    9: (79, 'KIIK'),
    10: (79, 'KIiK'),
    11: (78, 'KKKKKK'),
    12: (78, 'KIIIiK'),
    13: (78, 'KIIIiK'),
    14: (77, 'KKKKKKKK'),
    15: (77, 'KIIIIiiK'),
    16: (77, 'KIIIIiiK'),
    17: (76, 'KKKKKKKKKK'),
    18: (76, 'KIIIIIiiiK'),
    19: (76, 'KIIIIIiiiK'),
    20: (76, 'KiiiiiiiiK'),
    21: (76, 'KKKKKKKKKK'),
    22: (77, 'KMMMMDDK'),                                 # the tail under it, bowing out and thickening down to the pile
    23: (77, 'KMMMMDDK'),
    24: (77, 'KMMMMDDK'),
    25: (78, 'KMMMMDDK'),
    26: (78, 'KMMMMDDKK'),
    27: (79, 'KMMMMMDDK'),
    28: (79, 'KMMMMMDDK'),
    29: (80, 'KMMMMMDDK'),
    30: (80, 'KMMMMMDDK'),
    31: (80, 'KMMMMMDDK'),
    32: (81, 'KMMMMMDDK'),
    33: (81, 'KMMMMMDDK'),
    34: (81, 'KMMMMMDDK'),
    35: (81, 'KMMMMMDDK'),
    36: (81, 'KMMMMMDDK'),
    37: (81, 'KMMMMMMDDK'),
    38: (81, 'KMMMMMMDDK'),
    39: (81, 'KMMMMMMDDK'),
    40: (81, 'KMMMMMMDDK'),
    41: (80, 'KMMMMMMMDDK'),
    42: (80, 'MMMMMMMMDDK'),                              # from here down its near side is the pile's own edge
    43: (81, 'MMMMMMMDDK'),
    44: (81, 'MMMMMMMDDK'),
    45: (81, 'MMMMMMMDDK'),
    46: (81, 'MMMMMMMDDK'),
    47: (80, 'MMMMMMMDDK'),
    48: (79, 'MMMMMMMMDDK'),
    49: (84, 'MMMDDK'),
    50: (86, 'MDK'),
    51: (87, 'K'),
}

# what each of the five frames does (the game plays them 0..4 round and round, 260 ms each)
SINK = (0, 1, 2, 1, 0)                                    # the breath: all of it down on the ground, px
FLAP = (0, 1, 0, -1, 0)                                   # the ears: a column wider, a column narrower
SWAY = (0, 2, 1, -1, -2)                                  # the trunk's tip, px to the right
SHAKE = (0, 1, -1, 1, -1)                                 # the rattle's tip, px to the right

GIVEN = (58, 59)                                          # the rows of the lowest turn given up as it sinks (two alike)
EAR = (6, 22, 24)                                         # the ear's rows that flap, and the column of it doubled or dropped
EAR_MEND = {5: 23, 23: 23}                                # wider: the edge closed again above and below, a black pixel in each of these rows
TRUNK = (35, 39, 43)                                      # from the first row the trunk hangs free; from the second it swings half, from the third all
RATTLE = (8, 16)                                          # the rows of the rattle that shake: its three smaller beads

def head(flap):
    """The head's rows with the ears flapped: a column of each ear doubled (wider) or dropped (narrower)."""
    rows = dict(HEAD)
    for y in range(EAR[0], EAR[1] + 1) if flap else ():
        x0, t = rows[y]; i = EAR[2] - x0
        rows[y] = (x0 - 1, t[:i] + t[i] + t[i:]) if flap > 0 else (x0 + 1, t[:i] + t[i + 1:])
    for y, x in EAR_MEND.items() if flap > 0 else ():
        x0, t = rows[y]; rows[y] = (x, 'K' * (x0 - x) + t)
    return rows

def frame(f=0):
    """{pixel: letter}: the pile, the mirrored head over it, the tail over that; then the breath."""
    g, sway, shake = {}, SWAY[f], SHAKE[f]
    for y, (x0, t) in PILE.items():
        for x, c in enumerate(t, x0): g[(x, y)] = c
    for y, (x0, t) in head(FLAP[f]).items():
        dx = 0 if y < TRUNK[1] else int(sway / 2) if y < TRUNK[2] else sway
        for x, c in enumerate(t, x0):
            if c != '.': g[(x + dx, y)] = c; g[(W - 1 - x + dx, y)] = c
    for y, (x0, t) in TAIL.items():
        for x, c in enumerate(t, x0 + (shake if RATTLE[0] <= y <= RATTLE[1] else 0)): g[(x, y)] = c
    old = [None] * SINK[f] + [y for y in range(1, H) if y not in GIVEN[:SINK[f]]]      # the row each row is taken from
    g = {(x, y): g[(x, o)] for y, o in zip(range(1, H), old) if o for x in range(W) if (x, o) in g}
    assert all(0 <= x < W and 1 <= y < H for x, y in g)
    return g

def spots(f):
    """Where the fight's four fire spots are on frame f."""
    move = {'trunk': SWAY[f], 'rattle': SHAKE[f]}
    return {k: (x + move.get(k, 0), y + SINK[f]) for k, (x, y) in SPOTS.items()}

def FRAMES():
    fr = [frame(f) for f in range(5)]
    for f, g in enumerate(fr):
        off = {k: p for k, p in spots(f).items() if g.get(p) != 'K'}
        assert not off, f'frame {f}: a fire spot is not on the tip drawn for it: {off}'
    assert len({tuple(sorted(g.items())) for g in fr}) == 5, 'two frames are the same'
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
            big = [image(g, (0, 0, 0, 255)).resize((W * 5, H * 5), Image.NEAREST) for g in fr]
            big[0].save(sys.argv[3], save_all=True, append_images=big[1:], duration=260, loop=0)
    else: flat_parts.write('27_grootslang', fr, PAL, W, H)
    print(len(fr), 'frames | colours', sorted({c for g in fr for c in g.values()}), '| box', (min(p[0] for g in fr for p in g), min(p[1] for g in fr for p in g), max(p[0] for g in fr for p in g), max(p[1] for g in fr for p in g)))
    for f in range(5): print('  frame', f, spots(f))
