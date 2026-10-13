"""74 Bes Rap, big tier: its one pose, typed by hand to art/direction/SPRITE_STYLE.md.

    python art/enemies/74_bes_rap_design.py show OUT.png     the pose, enlarged, on black
    python art/enemies/74_bes_rap_design.py frame OUT.png    the pose alone, 98x65

The pig spirit of the Jah Hut: a skinny pig ghoul squatting at the roots of the fig tree. The user,
2026-10-11: "do bes rap. follow bible. have its pose just be it sitting in the front current pose, try
not to use shapes". So this is the old sheet's front view -- sat on its haunches, knees up, long arms
set wide and planted on the ground, a long neck, the big pig head turned a little so the snout shows --
drawn again flat, and every pixel of it is typed: no stroke, line or curve is worked out by code. The
tables are rows of letters. The body is typed as its left half and mirrored (the last letter of a row
is its middle column); the head, which is turned, is typed whole.

Tones by form: light on what faces up (the skull, the bridge of the snout, the shoulders, the tops of
the knees, hands and feet), dark under the jaw, in the hollow belly between its knees and on the
haunches behind its legs. Seven colours and black."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the built frame; row 0 stays empty
PAL = {'K': '000000', 'L': 'f0b890', 'F': 'ec8476', 'f': 'b6433d',   # skin: lit, the body of it, under and away
       's': 'a4aaba', 'T': 'e8e0c0', 'P': 'fc74b4', 'w': 'fcfcfc'}   # spines, teeth, the snout's disc, the eye (and its foam)
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# The trunk and legs, their left half: (row, pixels), the first letter at column BODY_X, the last on the middle
# column MID; the right half is this mirrored. Shoulder, chest, the knee up in front of it, the shin sloping in
# to the foot, the haunch on the ground behind, the belly a dark wedge between the knees.
BODY_X, MID = 30, 52
BODY = [
    (31, '...............KKKKKFFF'),                      # the shoulders: hunched, lit along the top
    (32, '...........KKKKLLLLFFFF'),
    (33, '.........KKLLLLLLLFFFFF'),
    (34, '........KLLLLFFFFFFFFFF'),
    (35, '........KLLFFFFFFFFFFFF'),
    (36, '........KLFFFKFFFFFFFFF'),                      # the armpit: from here the arm hangs clear (ARM)
    (37, '..............KFFFFFFFF'),
    (38, '..............KfFFFFFFF'),
    (39, '..............KffFFFfff'),                      # the chest falls away into the hollow belly
    (40, '............KKKKKKKKfff'),
    (41, '...........KLLLLLLLKfff'),                      # the knee, up in front of the chest
    (42, '...........KLLLFFFFKfff'),
    (43, '...........KLFFFFFFKfff'),
    (44, '...........KFFFFFFfKfff'),
    (45, '............KFFFFFFfKff'),                      # the shin, sloping in and narrowing to the ankle
    (46, '.............KFFFFFfKff'),
    (47, '.............KFFFFFfKff'),
    (48, '..............KFFFFFfKf'),
    (49, '..............KFFFFFfKf'),
    (50, '.........KKKKKKKFFFFfKf'),                      # the haunch on the ground behind the leg
    (51, '........KFFFFFFfKFFFFfK'),                      # the two shins meet
    (52, '.......KFFFFFFffKFFFFfK'),
    (53, '.......KFFFFFFffKFFFFfK'),
    (54, '.......KFFFFFfffKFFFFfK'),
    (55, '.......KFFFFfffffKFFFfK'),
    (56, '.......KFFFffffffKFFFfK'),
    (57, '.......KFffffffffKFFFfK'),
    (58, '........KffffffKKLFFFFK'),                      # the foot, flat, its toes toward us
    (59, '........KffffKKLFFFFFFK'),
    (60, '........KfffKLFFFFFFFFK'),
    (61, '........KfffKFFKFFKFFFK'),
    (62, '........KfffKFFKFFKFFFK'),
    (63, '........KKKKKKKKKKKKKKK'),
]
assert all(len(t) == MID - BODY_X + 1 for y, t in BODY), [y for y, t in BODY if len(t) != MID - BODY_X + 1]

# The near arm, typed whole: (row, first column, pixels). Out from the shoulder to a knobbed elbow, straight down
# to a long hand flat on the ground. The far arm is this one mirrored, its lit edge dark (FAR).
ARM = [(37, 38, 'KLFFK'), (38, 37, 'KLFFK'), (39, 37, 'KLFFK'), (40, 36, 'KLFFK'), (41, 36, 'KLFFK'), (42, 35, 'KLFFK'),
       (43, 35, 'KLFFK'), (44, 34, 'KLFFK'), (45, 33, 'KLFFFK'), (46, 33, 'KLFFFK')] + \
      [(y, 34, 'KLFK') for y in range(47, 57)] + \
      [(57, 34, 'KFFK'), (58, 32, 'KKLFFK'), (59, 30, 'KKKLFFFK'), (60, 30, 'KLFFFFFFK'),
       (61, 30, 'KFFKFFKFK'), (62, 30, 'KFFKFFKFK'), (63, 30, 'KKKKKKKKK')]
FAR = {'L': 'f'}

# The neck, leaning to the right as it rises, dark under the jaw and down its far side.
NECK = [(26, 52, 'KfffffK'), (27, 51, 'KFffffK'), (28, 51, 'KFFfffK'), (29, 50, 'KFFFffK'), (30, 50, 'KFFFFfK')]

# The spines down its back, showing over the shoulders either side of the neck.
SPINES = [(26, 47, 'K'), (27, 46, 'KsK'), (28, 43, 'K..KsK'), (29, 42, 'KsKKssK'), (30, 41, 'KssKKssK'), (31, 41, 'KssK'),
          (28, 61, 'K'), (29, 60, 'KsK'), (30, 60, 'KssK'), (31, 60, 'KssK')]

# The head, typed whole: turned toward the right, the snout's disc at the end of it, the grin under.
HEAD_X, HEAD_Y = 46, 9
HEAD = [
    '...KK.......KK............',                         # the ears: the near one, and the far one behind the skull
    '..KFFK.....KFFK...........',
    '..KFfFK.KKKKFfFK..........',
    '..KFfFKKLLLLKFFK..........',
    '...KFFLLLLLLLKKKKKKK......',                         # the skull, lit; the bridge of the snout
    '...KLLLLLFFFFFFLLLLLKKKK..',
    '..KLLKKKKFFFFKKFFLLLLPPPK.',                         # the brows
    '..KLFKwwKFFFFwKFFFFFPPfPPK',                         # the eyes, sunk under them; the disc and a nostril
    '..KFFFKKKFFFFKFFFFFFPPPPPK',
    '..KFFFFFFFFFFFFFFFFFPPfPPK',
    '..KFFFFKKKKKKKKKKKKKKPPPK.',                         # the grin: its line from the cheek to the disc
    '...KfFFKTTKTTKTTKTTKTKKK..',                         # square teeth
    '...KffFKTTKTTKTTKTTKTK....',
    '....KfffKKKKKKKKKKKKKK....',
    '....KKfFFFFFFFFFFFFFFK....',                         # the lower jaw
    '......KKfffffffffffffK....',
    '......KfKKKKKKKKKKKKK.....',                         # (the neck comes up into it here)
]
assert all(len(t) == 26 for t in HEAD), [i for i, t in enumerate(HEAD) if len(t) != 26]

def pose():
    """{pixel: letter}: spines, the trunk and its mirror, the arms, the neck, the head over them."""
    g = {}
    def put(x, y, c):
        if c != '.': g[(x, y)] = c
    for y, x0, t in SPINES:
        for x, c in enumerate(t, x0): put(x, y, c)
    for y, t in BODY:
        for x, c in enumerate(t, BODY_X): put(x, y, c); put(2 * MID - x, y, c)
    for y, x0, t in ARM:
        for x, c in enumerate(t, x0): put(x, y, c); put(2 * MID - x, y, FAR.get(c, c))
    for y, x0, t in NECK:
        for x, c in enumerate(t, x0): put(x, y, c)
    for j, t in enumerate(HEAD):
        for x, c in enumerate(t, HEAD_X): put(x, HEAD_Y + j, c)
    return g

def check(g):
    """The bible's countable rules, on one frame. Returns (open edge pixels, share of black inside the edge)."""
    assert all(0 <= x < W and 1 <= y < H for x, y in g), 'a pixel is outside the frame or on row 0'
    assert len(set(g.values()) - {'K'}) <= 8, set(g.values())
    edge = lambda p: any((p[0] + dx, p[1] + dy) not in g for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    open_ = sorted(p for p, c in g.items() if c != 'K' and edge(p))          # a colour with nothing round it: the outline is open there
    inside = sum(1 for p, c in g.items() if c == 'K' and not edge(p))
    return open_, inside / len(g)

if __name__ == '__main__':
    g = pose(); open_, black = check(g)
    xs = [x for x, y in g]; ys = [y for x, y in g]
    print('box x %d-%d, y %d-%d (%d tall) | colours %s | black inside %.1f%% | open edge %s' % (
        min(xs), max(xs), min(ys), max(ys), max(ys) - min(ys) + 1, ''.join(sorted(set(g.values()))), 100 * black, open_))
    if sys.argv[1:2] == ['frame']: image(g).save(sys.argv[2])
    if sys.argv[1:2] == ['show']: image(g, (0, 0, 0, 255)).resize((W * 6, H * 6), 0).save(sys.argv[2])
