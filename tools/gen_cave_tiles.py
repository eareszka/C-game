"""Stamp one recoloured copy of the cave rock art into assets/tileset.png per Material.

Every cave used to draw from a single hand-painted block and be told apart by a
multiplicative SDL_SetTextureColorMod. That has a hard ceiling: the master art is
blue-dominant with red never above 132, and a multiply can shift or darken a hue
but never add one, so golden rock was simply out of gamut and the flat floor fill
had to carry each material's identity on its own.

Baking the colour instead removes the ceiling. The master block stays exactly
where the artist drew it and becomes this script's INPUT; the renderer reads one
of seven generated blocks laid out to its right, picked by the cave's Material.

    cols 28-32  master, hand-painted, rows 0-7        (input, never written)
    cols 33-37  MAT_STONE                             (output)
    cols 38-42  MAT_BRONZE
    ...
    cols 48-52  MAT_VEYRITE   -- identity copy, byte-for-byte
    cols 63-67  MAT_REALITY_SHARD

MAT_VEYRITE is deliberately still generated rather than special-cased to read the
master directly. Keeping the rule uniform costs one block of atlas space and buys
an exact regression test: its ramp is the identity, its old rock_mod was already
255,255,255, so a Veyrite cave must render byte-identical to the build before this
existed. Anything else is a bug in the plumbing, not a judgement call about art.

RECOLOURING. The master holds 11 distinct colours. Each is placed on the target
material's ramp by its own relative luminance, so the art keeps its exact tonal
structure and only its hue changes -- a rank-ordered placement was tried first and
flattens the contrast, because the 11 are not evenly spread in luminance (six of
them sit below the midpoint). Placement is then separated so two source colours
can never land on the same output: collapsing two is invisible in a palette dump
and shows up only as lost detail in the render.

Transparency is the colour key (255,0,0), never alpha -- the atlas is opaque RGBA
throughout, and tools/gen_cliff_tiles.py round-trips the whole sheet through
.convert('RGB'), so an alpha-blanked pixel would come back as opaque black and
stop matching the key. Key pixels are copied through untouched, which is also
what makes the footprint assertion below meaningful.

CROSS-LANGUAGE PAIRING. MASTER_COL0 / OUT_COL0 / BLOCK_COLS must agree with
CAVE_MASTER_COL0 / CAVE_ART_COL0 / CAVE_ART_COLS in src/dungeon.cpp. There is no
way to check that from here; it is the same standing arrangement gen_cliff_tiles.py
has with tilemap.cpp's *_ROW0 constants.

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
BLOCK_COLS = 5       # cols 28-32: TALL_BAND, TRIM_S, TRIM_WE, TRIM_TRANS_L, SOLO
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


def recolour(block, ramp):
    """Return a recoloured copy of `block`, key pixels passed straight through."""
    out = block.copy()
    if ramp is None:
        return out

    rgb = block[:, :, :3]
    fg = ~np.all(rgb == np.array(KEY, dtype=np.uint8), axis=2)
    cols = np.unique(rgb[fg].reshape(-1, 3), axis=0)
    lums = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in cols]

    for c, t in zip(cols, placements(lums)):
        hit = fg & np.all(rgb == c, axis=2)
        out[:, :, :3][hit] = ramp_at(ramp, t)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', default='assets/tileset.png')
    ap.add_argument('--only', choices=MATERIALS,
                    help='restamp one material, leaving blocks a human has '
                         'since repainted alone')
    ap.add_argument('--identity', action='store_true',
                    help='copy the master into all seven blocks unrecoloured, '
                         'so a render diff isolates the plumbing from the art')
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

    for i, name in enumerate(MATERIALS):
        if a.only and name != a.only:
            continue
        col0 = OUT_COL0 + i * BLOCK_COLS
        ramp = None if a.identity else RAMPS[name]
        out = recolour(master, ramp)

        # The footprint must survive the recolour exactly. Every downstream
        # checker -- node_check.py's clear-pixel count, any blank-tile sweep --
        # is really asking about this mask, so asserting it here is what makes
        # the art swap provably geometry-neutral rather than probably.
        if not np.array_equal(footprint(out), want):
            raise SystemExit('%s: recolour changed the art/key footprint' % name)

        sheet[0:BLOCK_ROWS * CELL, col0 * CELL:(col0 + BLOCK_COLS) * CELL] = out
        n = len(np.unique(out[:, :, :3][want].reshape(-1, 3), axis=0))
        print('  %-14s cols %2d-%2d  %2d colours%s' % (
            name, col0, col0 + BLOCK_COLS - 1, n,
            '  (identity)' if ramp is None else ''))

    if a.preview:
        preview(a.preview, sheet)
        print('preview -> %s' % a.preview)
    if not a.no_write:
        Image.fromarray(sheet).save(a.sheet)
        print('wrote %s' % a.sheet)


if __name__ == '__main__':
    main()
