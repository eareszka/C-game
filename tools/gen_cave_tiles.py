"""Lay the cave rock into assets/tileset.png, one block per Material.

A cave is drawn from its own ore's block of the sheet (src/dungeon.cpp
cave_bake), picked by the cave's Material:

    cols 28-32  master, hand-painted, rows 0-7        (input, never written)
    cols 33-37  MAT_STONE                             (output)
    cols 38-42  MAT_BRONZE
    ...
    cols 63-67  MAT_REALITY_SHARD

A block holds the rock's 16 x 16 pieces (see "the rock" below: from
art/structures/dungeon_walls/cave_rock.png, in the ore's tones), a cell
of the hand-painted master recoloured, the gem, and the node to mine
(art/structures/nodes/nodes.png, in the ore). The colour is
baked, not a colour-mod in the game: a multiply can darken a hue but never add
one, so golden rock was out of reach.

RECOLOURING (the gem). The master holds 11 distinct colours. Each is placed on the target
material's ramp by its own relative luminance, so the art keeps its exact tonal
structure and only its hue changes -- a rank-ordered placement was tried first and
flattens the contrast, because the 11 are not evenly spread in luminance (six of
them sit below the midpoint). Placement is then separated so two source colours
can never land on the same output: collapsing two is invisible in a palette dump
and shows up only as lost detail in the render.

Transparency is the colour key (255,0,0), never alpha -- the atlas is opaque RGBA
throughout, and tools/gen_islands.py round-trips the whole sheet through
.convert('RGB'), so an alpha-blanked pixel would come back as opaque black and
stop matching the key. Key pixels are copied through untouched, which is also
what makes the footprint assertion below meaningful.

CROSS-LANGUAGE PAIRING. OUT_COL0 / BLOCK_COLS must agree with
CAVE_ART_COL0 / CAVE_ART_COLS in src/dungeon.cpp. There is no
way to check that from here; it is the same standing arrangement gen_islands.py
has with tilemap.cpp's ISLAND_ROW0.

Run from the repo root:

    python tools/gen_cave_tiles.py                      # stamp all seven
    python tools/gen_cave_tiles.py --only bronze        # restamp just one
    python tools/gen_cave_tiles.py --identity           # seven exact copies
    python tools/gen_cave_tiles.py --preview strip.png  # zoomed comparison strip
"""
import argparse
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- constants

CELL = 16            # pixels on a side of one sheet cell
KEY = (255, 0, 0)    # the atlas colour key -- transparency, and never alpha

MASTER_COL0 = 28     # the hand-painted block this reads
BLOCK_COLS = 5       # cols 28-32
BLOCK_ROWS = 8       # rows 0-7
OUT_COL0 = 33        # first generated block, immediately right of the master

# Names in Material order (include/entity.h). The index into this list IS the
# enum value, which is what makes the block position derivable rather than a
# table someone has to keep in sync.
MATERIALS = ['stone', 'bronze', 'emerald', 'veyrite',
             'dravium', 'kharvite', 'reality_shard']

# Dark to light. Each ramp ends on the colour the bead/gem highlights take, so
# the top stop doubles as the material's gem. Tuned against the flat floor fill
# in MATERIALS[] in src/dungeon.cpp so rock and floor read as the same stone --
# that pairing is the whole point, and is easiest to check on --preview.
#
# `None` means identity: copy the master through unchanged.
RAMPS = {
    'stone':         [(30, 30, 36), (58, 58, 68), (92, 92, 104),
                      (134, 136, 150), (188, 190, 202)],
    'bronze':        [(34, 20, 12), (78, 46, 22), (134, 88, 36),
                      (196, 140, 58), (244, 206, 128)],
    'emerald':       [(14, 32, 22), (28, 68, 44), (46, 112, 70),
                      (80, 168, 104), (158, 232, 176)],
    'veyrite':       None,
    'dravium':       [(32, 12, 14), (74, 24, 26), (126, 40, 40),
                      (184, 68, 62), (236, 132, 118)],
    'kharvite':      [(36, 28, 10), (82, 62, 20), (140, 110, 32),
                      (204, 166, 52), (250, 228, 136)],
    'reality_shard': [(12, 10, 18), (32, 24, 48), (62, 44, 92),
                      (104, 76, 152), (182, 156, 238)],
}

# ---------------------------------------------------------------- recolouring


def ramp_at(ramp, t):
    """Sample a ramp at t in [0,1], linearly between its stops."""
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = min(int(t), len(ramp) - 2)
    f = t - i
    a, b = ramp[i], ramp[i + 1]
    return tuple(int(round(a[c] + (b[c] - a[c]) * f)) for c in range(3))


def placements(lums):
    """Where each source colour sits on the ramp, given their luminances.

    Relative luminance, so the art's tonal structure survives the recolour, but
    with a floor on the gap between neighbours so two source colours an eyelash
    apart in luminance still come out as two colours. Both halves matter: drop
    the first and the contrast flattens, drop the second and detail silently
    merges.
    """
    n = len(lums)
    if n == 1:
        return [0.0]
    lo, hi = min(lums), max(lums)
    span = hi - lo
    t = [(l - lo) / span if span else 0.0 for l in lums]

    order = sorted(range(n), key=lambda i: t[i])
    gap = 1.0 / (2 * (n - 1))    # half of what an even spread would give
    for k in range(1, n):
        a, b = order[k - 1], order[k]
        if t[b] - t[a] < gap:
            t[b] = t[a] + gap
    scale = max(t)
    if scale > 1.0:              # the pushes can overflow; renormalise
        t = [v / scale for v in t]
    return t


def colour_map(block, ramp):
    """Each of the block's colours and what the ramp makes of it (itself, with no ramp)."""
    rgb = block[:, :, :3]
    fg = ~np.all(rgb == np.array(KEY, dtype=np.uint8), axis=2)
    cols = [tuple(int(v) for v in c) for c in np.unique(rgb[fg].reshape(-1, 3), axis=0)]
    if ramp is None:
        return {c: c for c in cols}
    lums = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in cols]
    return {c: ramp_at(ramp, t) for c, t in zip(cols, placements(lums))}


def recolour(block, ramp):
    """Return a recoloured copy of `block`, key pixels passed straight through."""
    out = block.copy()
    rgb = block[:, :, :3]
    fg = ~np.all(rgb == np.array(KEY, dtype=np.uint8), axis=2)
    for c, to in colour_map(block, ramp).items():
        out[:, :, :3][fg & np.all(rgb == c, axis=2)] = to
    return out


# ---------------------------------------------------------------- stamping


def block_at(sheet, col0):
    r0 = 0
    return sheet[r0:r0 + BLOCK_ROWS * CELL, col0 * CELL:(col0 + BLOCK_COLS) * CELL]


def footprint(block):
    """Which pixels are art rather than colour key."""
    return ~np.all(block[:, :, :3] == np.array(KEY, dtype=np.uint8), axis=2)


def preview(path, sheet, zoom=6):
    """The master and all seven blocks side by side, zoomed.

    One block at a time is unreadable and a palette dump cannot answer the only
    question that matters -- does this read as rock of that material, next to
    the others. Labelled by nothing: the order is the Material order, master
    first.
    """
    cols = [MASTER_COL0] + [OUT_COL0 + i * BLOCK_COLS for i in range(len(MATERIALS))]
    gap = 2
    strip = []
    for c in cols:
        strip.append(block_at(sheet, c)[:, :, :3])
        strip.append(np.full((BLOCK_ROWS * CELL, gap, 3), 40, dtype=np.uint8))
    img = np.concatenate(strip[:-1], axis=1)
    img = np.repeat(np.repeat(img, zoom, axis=0), zoom, axis=1)
    Image.fromarray(img).save(path)


# ---------------------------------------------------------------- the rock
#
# The caves' walls are laid from the 16 x 16 pieces of
# art/structures/dungeon_walls/cave_rock.png (cave_rock_design.py: the pieces,
# and where each sits in a block). Each ore's block takes them in the ore's own
# tones -- the ones its cave mouth, its ladder and the mountain outside are in
# (art/structures/gen_cave_entrances.py TONES: line, shade, base, lit) -- the
# rock's base and shade a tone each, its lines black. Of the hand-painted
# master only the gem is still drawn, left as it stands in each block: the
# palette pass has since cut it to four colours a cell, and stamping the
# master's eleven back would have it choose again and not the same (--crystals
# does it, when the master changes).
#
# The node to mine (cell (4, 0), src/dungeon.cpp draw_cave) is the overworld's
# (art/structures/nodes/nodes_design.py): the gold ore vein with the cave's own
# ore in it, its lit and base for the gold's (the user, 2026-10-15); a stone
# cave's is the plain stone rock, stone in stone being no vein at all.
# Its three twinkling frames (a nugget flared) go in a row of their own; a stone
# cave's, the rock again, so the game plays every cave's node alike.
NODE_CELLS = ((4, 0), (0, 6), (1, 6), (2, 6))   # plain, then the frames: nodes.png cells 1-4
ROCK_KEEP = NODE_CELLS + ((3, 7),)              # the node and the gem: not laid with rock
NODE_ART = 'art/structures/nodes/nodes.png'
NODE_GOLD = {(250, 228, 136): 3, (201, 164, 51): 2}   # the vein's gold (kharvite's lit, base): which tone of the ore
ROCK_INC = 'src/cave_rock.inc'
ROCK_ART = 'art/structures/dungeon_walls/cave_rock.png'


def rock_pieces():
    """(name, cell x, cell y, cells wide, cells tall) of the pieces the game draws."""
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'structures', 'dungeon_walls'))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'structures'))
    from cave_rock_design import CELLS, SIZE, PAL, ground_cobbles
    from gen_cave_entrances import TONES
    pieces = [(k, cx, cy) + SIZE.get(k, (1, 1)) for k, (cx, cy) in CELLS.items() if k != 'floor0']
    for k, cx, cy, w, h in pieces:
        assert not any((cx + i, cy + j) in ROCK_KEEP for i in range(w) for j in range(h)), k
    return pieces, PAL, dict(TONES), ground_cobbles()


def lay_rock(block, name, pieces, pal, tones, rock, master):
    """The block with every cell but the node's and the gem's cleared, and the rock's pieces laid."""
    art = np.array(Image.open(rock).convert('RGBA'))
    hx = lambda c: tuple(int(pal[c][i:i + 2], 16) for i in (0, 2, 4))
    line, shade, base, lit = tones[name]
    to = dict(master)                                # a draft in the hand-drawn master's own colours: as its gem goes
    to.update({hx('K'): line, hx('M'): base, hx('D'): shade, hx('S'): shade, hx('G'): lit,   # a gem in the rock: the ore's lit tone
               hx('F'): KEY})                                                                # the floor is the game's fill: clear
    for cy in range(BLOCK_ROWS):
        for cx in range(BLOCK_COLS):
            if (cx, cy) not in ROCK_KEEP:
                block[cy * CELL:(cy + 1) * CELL, cx * CELL:(cx + 1) * CELL, :3] = KEY
    for k, cx, cy, w, h in pieces:
        src = art[cy * CELL:(cy + h) * CELL, cx * CELL:(cx + w) * CELL]
        dst = block[cy * CELL:(cy + h) * CELL, cx * CELL:(cx + w) * CELL]
        for y in range(src.shape[0]):
            for x in range(src.shape[1]):
                if src[y, x, 3]:
                    dst[y, x, :3] = to[tuple(int(v) for v in src[y, x, :3])]
    return block


def lay_node(block, name, tones, art=NODE_ART):
    """The block with its node's cells drawn: stone's the rock, every other ore's the vein in that ore."""
    art = np.array(Image.open(art).convert('RGBA'))
    for i, (cx, cy) in enumerate(NODE_CELLS):
        k = 0 if name == 'stone' else 1 + i
        src = art[:, k * CELL:(k + 1) * CELL]
        dst = block[cy * CELL:(cy + 1) * CELL, cx * CELL:(cx + 1) * CELL]
        for y in range(CELL):
            for x in range(CELL):
                c = tuple(int(v) for v in src[y, x, :3])
                dst[y, x, :3] = (tones[name][NODE_GOLD[c]] if c in NODE_GOLD else c) if src[y, x, 3] else KEY
    return block


def write_rock_inc(pieces, cobbles, path):
    with open(path, 'w', newline='\n') as f:
        f.write('// Generated by tools/gen_cave_tiles.py -- do not edit.\n'
                '// The cave rock\'s pieces (art/structures/dungeon_walls/cave_rock_design.py): where each\n'
                '// sits in a cave\'s block of the sheet, in cells from the block\'s corner.\n'
                'enum CavePiece { %s, CP_COUNT };\n' % ', '.join('CP_' + k.upper() for k, *_ in pieces))
        f.write('static const unsigned char CAVE_PIECE[CP_COUNT][2] = { %s };\n'
                % ', '.join('{%d, %d}' % (cx, cy) for _, cx, cy, _, _ in pieces))
        f.write('// The node to mine, in a cave\'s block: (4, 0) plain, then its twinkle\'s frames from\n'
                '// (0, CAVE_FLARE_ROW) across.\n'
                'enum { CAVE_FLARE_ROW = %d };\n' % NODE_CELLS[1][1])
        w, h = len(cobbles[0]), len(cobbles)
        f.write('// Reality shard\'s floor (cave_rock_design.ground_cobbles): a bit a pixel, set on the lines\n'
                '// between its stones -- pixel (x, y) is bit x %% 8 of CAVE_COBBLE[y][x / 8].\n'
                'enum { CAVE_COBBLE_W = %d, CAVE_COBBLE_H = %d };\n'
                'static const unsigned char CAVE_COBBLE[CAVE_COBBLE_H][CAVE_COBBLE_W / 8] = {\n' % (w, h))
        for r in cobbles:
            f.write('    { %s },\n' % ', '.join(str(sum(1 << i for i in range(8) if r[x + i] == '1')) for x in range(0, w, 8)))
        f.write('};\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', default='assets/tileset.png')
    ap.add_argument('--only', choices=MATERIALS,
                    help='restamp one material, leaving blocks a human has '
                         'since repainted alone')
    ap.add_argument('--identity', action='store_true',
                    help='copy the master into all seven blocks unrecoloured, '
                         'so a render diff isolates the plumbing from the art')
    ap.add_argument('--rock', default=ROCK_ART, help='the rock sheet to lay (a draft, onto a copy of --sheet, for a mock)')
    ap.add_argument('--inc', default=ROCK_INC, help='where the piece table goes (elsewhere, for a mock)')
    ap.add_argument('--crystals', action='store_true',
                    help='restamp the gem from the master too '
                         '(after repainting it; run the palette pass after)')
    ap.add_argument('--preview')
    ap.add_argument('--no-write', action='store_true')
    a = ap.parse_args()

    sheet = np.array(Image.open(a.sheet))

    need = (OUT_COL0 + len(MATERIALS) * BLOCK_COLS) * CELL
    if sheet.shape[1] < need:
        raise SystemExit('sheet is only %d px wide, need %d' % (sheet.shape[1], need))

    master = block_at(sheet, MASTER_COL0).copy()
    want = footprint(master)
    print('master at cols %d-%d rows 0-%d: %d art px, %d key px, %d colours' % (
        MASTER_COL0, MASTER_COL0 + BLOCK_COLS - 1, BLOCK_ROWS - 1,
        int(want.sum()), int((~want).sum()),
        len(np.unique(master[:, :, :3][want].reshape(-1, 3), axis=0))))

    pieces, pal, tones, cobbles = rock_pieces()
    for i, name in enumerate(MATERIALS):
        if a.only and name != a.only:
            continue
        col0 = OUT_COL0 + i * BLOCK_COLS
        ramp = None if a.identity else RAMPS[name]
        out = recolour(master, ramp)

        # The footprint must survive the recolour exactly: recolouring must
        # never move a pixel between art and colour key.
        if not np.array_equal(footprint(out), want):
            raise SystemExit('%s: recolour changed the art/key footprint' % name)

        if not a.crystals:                           # as they stand in the sheet
            now = block_at(sheet, col0)
            for cx, cy in ROCK_KEEP:
                out[cy * CELL:(cy + 1) * CELL, cx * CELL:(cx + 1) * CELL] = now[cy * CELL:(cy + 1) * CELL, cx * CELL:(cx + 1) * CELL]
        out = lay_rock(out, name, pieces, pal, tones, a.rock, colour_map(master, ramp))
        out = lay_node(out, name, tones)
        sheet[0:BLOCK_ROWS * CELL, col0 * CELL:(col0 + BLOCK_COLS) * CELL] = out
        n = len(np.unique(out[:, :, :3][footprint(out)].reshape(-1, 3), axis=0))
        print('  %-14s cols %2d-%2d  %2d colours%s' % (
            name, col0, col0 + BLOCK_COLS - 1, n,
            '  (gem as painted)' if ramp is None else ''))

    if not a.no_write:
        write_rock_inc(pieces, cobbles, a.inc)
        print('wrote %s' % a.inc)
    if a.preview:
        preview(a.preview, sheet)
        print('preview -> %s' % a.preview)
    if not a.no_write:
        Image.fromarray(sheet).save(a.sheet)
        print('wrote %s' % a.sheet)


if __name__ == '__main__':
    main()
