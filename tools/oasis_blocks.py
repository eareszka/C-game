"""The oasis's rock, from the user's reference (a Mother 1 cave map, its
ground standing for the water the player swims): the reference cut into its
16 px sprites, each classed, recoloured into the dark oasis, and laid into
levels the way the artist laid the reference (level()) -- so
every lobe, rim and boulder is the artist's, recombined (user: the oasis's
rocks and collision should look like this).

    python tools/oasis_blocks.py design <design.json>   # the recoloured sprites, for draw_views
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/oasis_rock

The reference's tones and what they become:
    olive 887000   the rock                    -> 887000, as the overworld's island rock (user)
    black          the rock's clumps, the rims -> black
    sand fce4a0    the ground: the water       -> 2b1f40
    olive on sand  the ground's dot lattice    -> 3b2a58, faint in the water
    orange fc9838  a boulder's warm side       -> 785830
    (transparent)  a boulder's pale body       -> b2966a
"""
import json, os, struct, sys, zlib
import numpy as np


REF = os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop', 'reference', 'oasis reference.aseprite')
CELL = 16
PHASE = (12, 14)          # the reference's sprite grid (x, y): the offset with fewest distinct cells
OLIVE, SAND, BLACK, ORANGE = (136, 112, 0), (252, 228, 160), (0, 0, 0), (252, 152, 56)
TONES = {'R': '887000', 'K': '000000', 'W': '2b1f40', 'd': '3b2a58', 'O': '785830', 'B': 'b2966a'}
WATER, ROCK, RIM, BOULDER = 0, 1, 2, 3
# The ground's dots (the water's, here): one 8 x 8 lattice over the whole
# picture, at these (x % 8, y % 8) of the sprite grid. They are a texture, not
# a shape -- they do not line up with the 16 px sprites, so a sprite holding
# them comes in a variant per row -- so the sprites are cut with the dots
# taken out (plain water) and the dots laid back over every level by position
# (dots()), which lets any two water sprites meet.
DOTS = {(0, 1), (0, 6), (1, 4), (2, 0), (4, 2), (5, 5), (6, 3), (7, 0)}
CLASS_NAMES = ('water', 'rock', 'rim', 'boulder')


def read_aseprite(path):
    """The first frame of an RGBA .aseprite, flattened (compressed cels)."""
    d = open(path, 'rb').read()
    W, H = struct.unpack_from('<HH', d, 8)
    pos = 128
    nold = struct.unpack_from('<H', d, pos + 6)[0]
    n = struct.unpack_from('<I', d, pos + 12)[0] or nold
    cp = pos + 16
    a = np.zeros((H, W, 4), np.uint8)
    for _ in range(n):
        size, kind = struct.unpack_from('<IH', d, cp)
        if kind == 0x2005:
            _, x, y, _, ct = struct.unpack_from('<HhhBH', d, cp + 6)
            if ct == 2:
                w, h = struct.unpack_from('<HH', d, cp + 22)
                raw = np.frombuffer(zlib.decompress(d[cp + 26:cp + size]), np.uint8).reshape(h, w, 4)
                ys, ye, xs, xe = max(0, y), min(H, y + h), max(0, x), min(W, x + w)
                sub = raw[ys - y:ye - y, xs - x:xe - x]
                a[ys:ye, xs:xe][sub[..., 3] > 0] = sub[sub[..., 3] > 0]
        cp += size
    return a


def letters(a):
    """The reference as tone letters (see the module's table)."""
    rgb, alpha = a[..., :3], a[..., 3] > 0
    is_ = lambda c: np.all(rgb == c, axis=2) & alpha
    g = np.full(a.shape[:2], 'W', '<U1')
    g[is_(OLIVE)] = 'R'
    g[is_(BLACK)] = 'K'
    g[is_(ORANGE)] = 'O'
    g[~alpha] = 'B'
    # an olive pixel standing in the sand is the ground's dot, not rock
    sand = is_(SAND)
    nb = sum(np.roll(sand, s, ax) for s in (1, -1) for ax in (0, 1))
    g[is_(OLIVE) & (nb >= 3)] = 'd'
    return g


def vocabulary():
    """(sprites, classes, grids): every distinct 16 px sprite of the reference
    and of its mirror, as letter arrays, each one's class, and the two
    reference pictures as grids of sprite ids."""
    g = letters(read_aseprite(REF))
    g[g == 'd'] = 'W'                                 # the dots come back by position (dots())
    ox, oy = PHASE
    H, W = (g.shape[0] - oy) // CELL, (g.shape[1] - ox) // CELL
    g = g[oy:oy + H * CELL, ox:ox + W * CELL]
    sprites, ids, grids = [], {}, []
    for pic in (g, g[:, ::-1]):                       # its mirror: the reference faces either way
        grid = np.zeros((H, W), int)
        for y in range(H):
            for x in range(W):
                t = pic[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]
                k = t.tobytes()
                if k not in ids:
                    ids[k] = len(sprites); sprites.append(t.copy())
                grid[y, x] = ids[k]
        grids.append(grid)
    classes = []
    for t in sprites:
        if np.isin(t, ['O', 'B']).any():
            classes.append(BOULDER)
            t[t == 'd'] = 'W'                             # four tones: the lattice gives way to the boulder
        elif (t == 'W').all():
            classes.append(WATER)
        elif not (t == 'W').any():
            classes.append(ROCK)
        else:
            classes.append(RIM)
    return sprites, classes, grids


def level(W, rng):
    """A level W sprites long, the reference's height: the reference and its
    mirror, end to end, again and again -- every join a mirror's seam, so the
    rock's outline runs on unbroken and the passage goes wide, narrow and wide
    again as the reference does -- from a random place in the run. The
    reference's boulders are lifted off: the water is left open (user: no
    rock in the swimming area). Returns (grid,
    narrow): narrow[x] is True where the floor has stepped up."""
    sprites, classes, (ref, mir) = vocabulary()
    cls = np.array(classes)
    Wr = ref.shape[1]
    reps = W // (2 * Wr) + 3
    # from its third column on: the first two hold a nook of ground in the
    # bottom corner that a mirror's seam would double into a dip in the floor
    core = ref[:, 2:]
    run = np.concatenate([core, mir[:, :-2]] * reps, axis=1)   # mir[:, :-2]: the core, mirrored
    # start and end in the narrow passage: a dead end tapers well out of it
    # and badly out of the open water (user), so the run is cut where both ends
    # of the level land in the narrow stretch
    period = 2 * (Wr - 2)
    narrow_col = np.isin(cls[run], [WATER, BOULDER]).sum(axis=0) < 4
    ok = [x for x in range(period) if narrow_col[x + 6] and narrow_col[x + W - 7]]
    x0 = ok[rng.randint(len(ok))] if ok else rng.randint(period)
    g = run[:, x0:x0 + W].copy()
    # lift the boulders: each cell back to the water its row holds elsewhere
    water_of = {}
    for y in range(ref.shape[0]):
        row = [v for v in ref[y] if cls[v] == WATER]
        if row:
            water_of[y] = max(set(row), key=row.count)
    for y, x in zip(*np.nonzero(cls[g] == BOULDER)):
        g[y, x] = water_of[y]
    water = np.isin(cls[g], [WATER, BOULDER]).sum(axis=0)
    return g, water < 4


def dots(letters_img):
    """A level's picture (tone letters) with the water's dot lattice laid over
    its plain water, by position, as the reference's runs."""
    out = letters_img.copy()
    yy, xx = np.mgrid[0:out.shape[0], 0:out.shape[1]]
    on = np.zeros(out.shape, bool)
    for dx, dy in DOTS:
        on |= (xx % 8 == dx) & (yy % 8 == dy)
    out[on & (out == 'W')] = 'd'
    return out


def design():
    sprites, classes, _ = vocabulary()
    views = {'s%d' % i: [''.join(r) for r in t] for i, t in enumerate(sprites)}
    for name, rows in views.items():
        assert len(set(''.join(rows))) <= 4, (name, set(''.join(rows)))
    return {'pal': TONES, 'view_w': CELL, 'order': list(views), 'views': views}


if __name__ == '__main__':
    if sys.argv[1] == 'design':
        json.dump(design(), open(sys.argv[2], 'w'))
