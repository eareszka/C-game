"""25 Myrmecoleon: how its first front pose was made, before the user redrew parts of it.
The sheet is built by 25_myrmecoleon_design.py from their frame; this is kept as the record.

    python art/enemies/25_myrmecoleon_pose_first.py show OUT.png   the pose, enlarged

The ant-lion of the medieval bestiaries: the forepart of a lion, the hindpart of an ant. The user
sent a picture for its stance (2026-10-10: "have the stance be like this"): the lion's forelegs
planted wide, its head up and roaring out of a heavy mane that is gold above and dark below, the
ant's dark-red abdomen raised behind it and its long jointed legs out to the sides. A first pose
drawn three-quarters on, its body and legs laid along points, was turned down ("redo that. try
not to use shapes and have it directly front"), and a first front view for leaving the bible
("remember the bible rules please": it had no line between its parts, a straight band of light
over dark across the mane, legs of one width and a block for a face).

So it is seen from straight in front and every pixel is set by hand, to the bible: a black line
round the whole of it and between its parts (abdomen, mane, ear, face, chest, each leg), tones by
form (the crown of the mane lit, its ruff dark where it hangs under the jaw; the shell lit on
top, dark where it turns away and under each plate), limbs that taper to a point, feet on a
black base line. The tables below are its left half, back to front; the right half is the mirror."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from flat_parts import write
import flat_parts
W, H = 98, 69                                             # the built frame; row 0 stays empty
MID = W // 2 - 1                                          # the last column of the left half
PAL = {'K': '000000', 'L': 'f4ce80', 'M': 'b2966a',       # the lion's hide: lit, shade (and the lit crown of the mane)
       'N': '94703d', 'n': '633e1b',                      # its mane: gold above, the dark ruff below
       'A': '792727', 'a': '5d1e1f',                      # the ant: its shell, and where the shell turns away
       'R': 'b6433d', 'W': 'fcfcfc'}                      # mouth, and the light on the shell and legs; teeth and eyes
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# row: (first column, the pixels from there to the middle of the frame); '.' leaves what is behind
ABDOMEN = {
    1: (48, 'K'),
    2: (46, 'KKA'),
    3: (44, 'KKAAA'),
    4: (41, 'KKKAARRR'),
    5: (38, 'KKKAAARRRRR'),
    6: (36, 'KKAAAAAAAAAAA'),
    7: (34, 'KKAAAAAAAKKKKKK'),
    8: (33, 'KAAAAAAKKKaaaaaa'),
    9: (33, 'KAAAAKKaaaAAAAAA'),
    10: (33, 'KAAKKaaAAAAAAAAA'),
    11: (33, 'KKKaaAAAAAAAAAAA'),
    12: (34, 'KaaAAAAAAAAKKKK'),
    13: (35, 'KaAAAAAKKKaaaa'),
    14: (36, 'KaAKKKaaaAAAA'),
    15: (37, 'KKaaaaaaaaaa'),
    16: (39, 'KKaaaaaaaa'),
    17: (41, 'KKKaaaaa'),
}

# the ant's legs: (first row, last row, first column, pixels) -- each run the same on every row of it
LEGS = [
    # the upper pair: thigh up and out from behind the mane ...
    (30, 30, 24, 'KRAaK'), (28, 29, 23, 'KRAaK'), (27, 27, 22, 'KRAaK'), (26, 26, 21, 'KRAaK'), (24, 25, 20, 'KRAaK'), (23, 23, 19, 'KRAaK'), (22, 22, 18, 'KRAaK'),
    (21, 21, 18, 'KRaK'), (20, 20, 17, 'KRaK'), (18, 19, 16, 'KRaK'), (17, 17, 15, 'KRaK'), (16, 16, 14, 'KRaK'), (14, 15, 13, 'KRaK'), (13, 13, 12, 'KRaK'), (12, 12, 11, 'KRaK'),
    # ... its knee ...
    (8, 8, 9, 'KKK'), (9, 9, 8, 'KRRAK'), (10, 10, 7, 'KRRAAAK'), (11, 11, 6, 'KRAaKRaK'),
    # ... and the shin down to the ground, thinning
    (12, 20, 6, 'KRAK'), (21, 29, 5, 'KRAK'), (30, 37, 4, 'KRAK'), (38, 45, 4, 'KRK'), (46, 53, 3, 'KRK'), (54, 60, 2, 'KRK'), (61, 66, 2, 'KR'),
    (67, 67, 0, 'KRRAK'), (68, 68, 0, 'KKKKK'),
    # the lower pair, the same
    (42, 42, 23, 'KRAaK'), (41, 41, 22, 'KRAaK'), (39, 40, 21, 'KRAaK'), (38, 38, 20, 'KRAaK'), (37, 37, 19, 'KRAaK'),
    (36, 36, 19, 'KRaK'), (35, 35, 18, 'KRaK'), (34, 34, 17, 'KRaK'), (33, 33, 16, 'KRaK'), (32, 32, 15, 'KRaK'),
    (28, 28, 13, 'KKK'), (29, 29, 12, 'KRRAK'), (30, 30, 11, 'KRRAAAK'), (31, 31, 10, 'KRAaKRaK'),
    (32, 39, 10, 'KRAK'), (40, 47, 9, 'KRAK'), (48, 54, 9, 'KRK'), (55, 61, 8, 'KRK'), (62, 66, 8, 'KR'),
    (67, 67, 6, 'KRRAK'), (68, 68, 6, 'KKKKK'),
]

BODY = {                                                  # chest, forelegs planted wide, paws
    50: (28, 'KLLLLLLLLLLLLLLLLLLLL'),
    51: (28, 'KLLLLLLLLLLLLLLLLLLLL'),
    52: (28, 'KLLLLLLLLLLLLLLLLLLLL'),
    53: (27, 'KLLLLLLLLLLLLLLLLLLLLL'),
    54: (27, 'KLLLLLLLLLMMMMMMMMMMMM'),
    55: (27, 'KLLLLLLLLLLLKMMMMMMMMM'),
    56: (26, 'KLLLLLLLLLMMKLLLLLLLLLL'),
    57: (26, 'KLLLLLLLLLMMKLLLLLLLLLL'),
    58: (26, 'KLLLLLLLLMMKMMMMMMMMMMM'),
    59: (25, 'KLLLLLLLLMMKMMMMKKKKKKKK'),
    60: (25, 'KLLLLLLLMMKKKKKK........'),
    61: (25, 'KLLLLLLMMK..............'),
    62: (24, 'KLLLLLLMMK...............'),
    63: (23, 'KLLLLLLLLLLKK.............'),
    64: (22, 'KLLLLLLLLLLLLLKK...........'),
    65: (22, 'KLLLLLLLLLLLLLLLK..........'),
    66: (22, 'KLLLKLLLKLLLKLLLK..........'),
    67: (22, 'KLLLKLLLKLLLKLLLK..........'),
    68: (23, 'KKKKKKKKKKKKKKK...........'),
}

HEAD = {                                                  # mane, ear, face
    15: (48, 'K'),
    16: (47, 'KM'),
    17: (43, 'K..KMM'),
    18: (42, 'KMKKMMM'),
    19: (39, 'K.KMMMMMMM'),
    20: (38, 'KNKNMMMMMMM'),
    21: (33, 'KKKKKNNNNNNMMMMM'),
    22: (32, 'KLLLLKNNNNNNNMMMM'),
    23: (32, 'KLnnLKNNNNNNNNNMM'),
    24: (32, 'KLnnLKNNNNNNNNNNN'),
    25: (32, 'KLnnKNNNNNNNNNNNN'),
    26: (30, 'KKKKKKNNNNNNKKKKNNN'),
    27: (29, 'KNNNNNNNNNNKKLLLLKKK'),
    28: (28, 'KNNNNNNNNNNKKKLLLLLLL'),
    29: (27, 'KNNNNNNNNNNKLLKKLLLLLL'),
    30: (26, 'KNNNNNNNNNNNKLLWWKKLLLL'),
    31: (26, 'KKNNNNNNNNNNKLLWKMMKKLL'),
    32: (28, 'KNNNNNNNNNKLMMMMLLLLL'),
    33: (27, 'KNNNNNNNNNNKLLLLLLLKKK'),
    34: (27, 'KNNNNNNNNNNKLLLLLLLLKK'),
    35: (26, 'KNNNNNNNNNNNKLLLLLLLLLK'),
    36: (25, 'KNNNNNNNNNNNNKLLLLLLLLLK'),
    37: (25, 'KKNNNNNNNNNNNKLLKKKKKKKK'),
    38: (27, 'KNNNNNNNNNNKLLKWWaWWWW'),
    39: (27, 'KnNNNNNNNNNKLLKWWaaaaa'),
    40: (26, 'KnnnNNNNNNNNKLMKaWaaaaa'),
    41: (26, 'KnnnnNNNNNNNKLMKaaaaaaa'),
    42: (26, 'KnnnnNNnNNNNNKMKaaRRRRR'),
    43: (25, 'KKnnnnnNnnNNNNKMKaaWRRRR'),
    44: (27, 'KnnnnnnnNNNNNKMKaWRRRR'),
    45: (27, 'KnnnnnnnnNnNNNKMKRRRRR'),
    46: (28, 'KnnnnnnnNnnNNNKMKKKKK'),
    47: (28, 'KnnnnnnnnnnnNNKMMMMMM'),
    48: (28, 'KnnnnnnnnnnnnnnKKKKKK'),
    49: (27, 'KKKnnnnnnnnnnnnnnnnnnn'),
    50: (30, 'Knnnnnnnnnnnnnnnnnn'),
    51: (30, 'Knnnnnnnnnnnnnnnnnn'),
    52: (31, 'Knnnnnnnnnnnnnnnnn'),
    53: (32, 'KnnnnKKKnnnnnnnnn'),
    54: (33, 'KnnK...KnnnnKKnn'),
    55: (34, 'KK.....KnnK..Kn'),
    56: (42, 'KK....K'),
}
# a few strokes of fur in the mane, over it: (row, first column, pixels)
FUR = [(33, 31, 'K'), (34, 32, 'KK'), (23, 40, 'K'), (24, 41, 'K'), (45, 30, 'K'), (46, 31, 'KK'), (50, 36, 'K'), (51, 37, 'KK'), (51, 44, 'K'), (52, 45, 'KK')]
for name in ('ABDOMEN', 'BODY', 'HEAD'):
    wrong = {y: x + len(t) for y, (x, t) in globals()[name].items() if x + len(t) != MID + 1}
    assert not wrong, f'{name}: these rows do not end on the middle column: {wrong}'

def standing():
    """{pixel: letter}: the left half, back to front, and its mirror."""
    g = {}
    def put(y, x0, t):
        for x, c in enumerate(t, x0):
            assert 0 <= x <= MID and 1 <= y < H, (x, y)
            if c != '.': g[(x, y)] = c; g[(W - 1 - x, y)] = c
    for y, (x0, t) in ABDOMEN.items(): put(y, x0, t)
    for y0, y1, x0, t in LEGS:
        for y in range(y0, y1 + 1): put(y, x0, t)
    for part in (BODY, HEAD):
        for y, (x0, t) in part.items(): put(y, x0, t)
    for y, x0, t in FUR: put(y, x0, t)
    return g

FRAMES = lambda: [standing()]

if __name__ == '__main__':
    fr = FRAMES()
    if sys.argv[1:2] == ['show']:
        from PIL import Image
        cv = Image.new('RGBA', (W * len(fr) + 2 * (len(fr) - 1), H * 2 + 2), (40, 40, 40, 255))
        for i, g in enumerate(fr):
            cv.alpha_composite(image(g, (255, 170, 200, 255)), (i * (W + 2), 0)); cv.alpha_composite(image(g, (0, 0, 0, 255)), (i * (W + 2), H + 2))
        cv.resize((cv.width * 6, cv.height * 6), Image.NEAREST).save(sys.argv[2])
    else: write('25_myrmecoleon_pose_first', fr, PAL, W, H)
    print(len(fr), 'frames | colours', sorted({c for g in fr for c in g.values()}), '| box', (min(p[0] for g in fr for p in g), min(p[1] for g in fr for p in g), max(p[0] for g in fr for p in g), max(p[1] for g in fr for p in g)))
