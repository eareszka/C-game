"""Stamp one recoloured copy of the trail nine-slice into assets/tileset.png per biome.

The trail and the road share a single hand-cut nine-slice, drawn in the colours of
the wasteland it was first worn through. That was right while a trail only ever
existed in wasteland, and it stopped being right twice over: roads join settlements
across grass, meadow, snow and desert, and since the stroke was allowed to lean onto
the ground beside it, a wasteland trail now puts its outer tile on grass as well. A
dark brown track over bright green reads as a mistake rather than as a path.

So the block is recoloured once per ground a track can run over, and a tile picks
its bank from the ground around it:

    cols 24-26  master, hand-cut, rows 5-7        (input, never written)
    cols 68-70  grass                             (output)
    cols 71-73  meadow
    cols 74-76  sand
    cols 77-79  wasteland  -- identity copy, byte-for-byte
    cols 80-82  snow

Wasteland is generated rather than special-cased for the same reason MAT_VEYRITE is
in tools/gen_cave_tiles.py: keeping the rule uniform costs one bank of atlas space
and buys an exact regression test. Its ramp is the identity, so a wasteland track
must render byte-identical to the build before any of this, and anything else is a
bug in the plumbing rather than a judgement about colour.

The master holds only four colours, so each is placed on the target ramp by its
rank in luminance -- with four there is no distribution worth preserving, and rank
keeps them distinct by construction. The colour key (255,0,0) is copied through
untouched; the trail cells happen to be fully opaque, and the footprint assertion
below is what keeps that true if the art is ever redrawn with a transparent margin.

CROSS-LANGUAGE PAIRING. MASTER_COL0 / OUT_COL0 / BANK_COLS and the order of BIOMES
must agree with TRAIL_MASTER_COL0 / TRAIL_BANK_COL0 / TRAIL_BANK_COLS and the
TrailBank enum in src/tilemap.cpp. Nothing can check that from here.

Run from the repo root:

    python tools/gen_trail_tiles.py                     # stamp all five
    python tools/gen_trail_tiles.py --only snow         # restamp just one
    python tools/gen_trail_tiles.py --identity          # five exact copies
    python tools/gen_trail_tiles.py --preview strip.png # zoomed comparison strip
"""
import argparse
import numpy as np
from PIL import Image

CELL = 16
KEY = (255, 0, 0)

MASTER_COL0 = 24     # the hand-cut nine-slice this reads
MASTER_ROW0 = 5
BANK_COLS = 3        # a nine-slice is three by three
BANK_ROWS = 3
OUT_COL0 = 68        # first generated bank; clear of the cave art at cols 33-67

# Order is the TrailBank enum in src/tilemap.cpp. The index IS the bank number.
BIOMES = ['grass', 'meadow', 'sand', 'wasteland', 'snow']

# Dark to light, four stops for the master's four colours. Each is a track worn
# through that ground, so it has to sit against the ground's own colour without
# vanishing into it -- the value to compare against is in the comment.
#
# `None` means identity: copy the master through unchanged.
RAMPS = {
    # ground (78,220,74) bright green -> ordinary brown dirt
    'grass':     [(48, 32, 16), (92, 64, 32), (120, 88, 48), (150, 116, 72)],
    # ground (168,240,188) pale mint -> the same dirt, lifted so it does not
    # read as a hole in a pale field
    'meadow':    [(70, 52, 34), (112, 86, 54), (146, 116, 76), (178, 150, 106)],
    # ground (240,232,128) pale yellow -> sand packed down, darker and greyer
    # than the dune it crosses rather than a different colour from it
    'sand':      [(96, 80, 40), (140, 120, 64), (178, 158, 92), (206, 190, 130)],
    # ground (39,8,0) -- the master's own, so nothing to do
    'wasteland': None,
    # ground (252,252,252) white -> trodden snow, blue-grey, never brown
    'snow':      [(84, 88, 100), (124, 130, 146), (164, 170, 186), (198, 204, 218)],
}


# How deep the ragged band of transparency reaches in from the block's outer
# edge, in pixels of the 16px cell. Settled by looking, not by argument.
MARGIN = 4


def carve(block):
    """Key out a ragged band along the block's outer boundary.

    A track used to be written into the tile, so its art had to be opaque —
    there was nothing behind it to show. Now it is drawn over ground that is
    still there, and the edge is where that matters: a hard rectangle of dirt
    reads as laid down, a ragged one as worn in.

    Carving the whole 3x3 block's boundary gives each cell exactly the treatment
    its role wants, for free. The top cell sits at the block's top edge, so only
    its top is carved; a corner cell sits at two edges and gets both; the centre
    touches no edge and stays solid. That is the same set of sides the nine-slice
    picker exposes each cell on, which is why it lines up without a table.

    Deterministic from the pixel position, so a rerun of this script produces the
    same edge and a render diff stays meaningful.
    """
    out = block.copy()
    h, w = out.shape[0], out.shape[1]
    for py in range(h):
        for px in range(w):
            d = min(px, py, w - 1 - px, h - 1 - py)
            if d >= MARGIN:
                continue
            n = ((px * 73856093) ^ (py * 19349663) ^ ((px * py) * 83492791)) & 0xFFFF
            # Deeper in, more of the track survives: the outermost row is mostly
            # gone, the innermost of the band mostly kept.
            keep = (d + 1) / float(MARGIN + 1)
            if n / 65535.0 > keep:
                out[py, px, :3] = KEY
    return out


def ramp_at(ramp, t):
    """Sample a ramp at t in [0,1], linearly between its stops."""
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = min(int(t), len(ramp) - 2)
    f = t - i
    a, b = ramp[i], ramp[i + 1]
    return tuple(int(round(a[c] + (b[c] - a[c]) * f)) for c in range(3))


def recolour(block, ramp):
    """Return a recoloured copy of `block`, key pixels passed straight through."""
    out = block.copy()
    if ramp is None:
        return out
    rgb = block[:, :, :3]
    fg = ~np.all(rgb == np.array(KEY, dtype=np.uint8), axis=2)
    cols = np.unique(rgb[fg].reshape(-1, 3), axis=0)
    lums = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in cols]
    order = sorted(range(len(cols)), key=lambda i: lums[i])
    n = max(len(cols) - 1, 1)
    for rank, i in enumerate(order):
        hit = fg & np.all(rgb == cols[i], axis=2)
        out[:, :, :3][hit] = ramp_at(ramp, rank / n)
    return out


def block_at(sheet, col0):
    return sheet[MASTER_ROW0 * CELL:(MASTER_ROW0 + BANK_ROWS) * CELL,
                 col0 * CELL:(col0 + BANK_COLS) * CELL]


def footprint(block):
    return ~np.all(block[:, :, :3] == np.array(KEY, dtype=np.uint8), axis=2)


def preview(path, sheet, zoom=8):
    """Master and all five banks side by side, zoomed. Colour is only ever
    settled by looking at them together."""
    cols = [MASTER_COL0] + [OUT_COL0 + i * BANK_COLS for i in range(len(BIOMES))]
    strip = []
    for c in cols:
        strip.append(block_at(sheet, c)[:, :, :3])
        strip.append(np.full((BANK_ROWS * CELL, 2, 3), 255, dtype=np.uint8))
    img = np.concatenate(strip[:-1], axis=1)
    Image.fromarray(np.repeat(np.repeat(img, zoom, 0), zoom, 1)).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', default='assets/tileset.png')
    ap.add_argument('--only', choices=BIOMES)
    ap.add_argument('--identity', action='store_true',
                    help='copy the master into all five banks unrecoloured, so a '
                         'render diff isolates the plumbing from the colour')
    ap.add_argument('--preview')
    ap.add_argument('--no-write', action='store_true')
    ap.add_argument('--no-carve', action='store_true',
                    help='leave the banks fully opaque, as before the track was '
                         'drawn over the ground instead of into it')
    a = ap.parse_args()

    sheet = np.array(Image.open(a.sheet))
    need = (OUT_COL0 + len(BIOMES) * BANK_COLS) * CELL
    if sheet.shape[1] < need:
        raise SystemExit('sheet is only %d px wide, need %d' % (sheet.shape[1], need))

    master = block_at(sheet, MASTER_COL0).copy()
    # The master in the sheet stays the artist's own, fully opaque; the carve
    # happens on the way into the banks. So the footprint every bank must match
    # is the CARVED one, not the master's — the assertion still catches a
    # recolour that moves a pixel between art and key, which is its job.
    if not a.no_carve:
        master = carve(master)
    want = footprint(master)
    print('master at cols %d-%d rows %d-%d: %d art px (%d keyed out), %d colours' % (
        MASTER_COL0, MASTER_COL0 + BANK_COLS - 1, MASTER_ROW0,
        MASTER_ROW0 + BANK_ROWS - 1, int(want.sum()), int((~want).sum()),
        len(np.unique(master[:, :, :3][want].reshape(-1, 3), axis=0))))

    for i, name in enumerate(BIOMES):
        if a.only and name != a.only:
            continue
        col0 = OUT_COL0 + i * BANK_COLS
        ramp = None if a.identity else RAMPS[name]
        out = recolour(master, ramp)
        # Recolouring must never move a pixel between art and colour key: the
        # nine-slice picker reads neighbours, not pixels, but anything measuring
        # the track's width off a render depends on the footprint being the
        # master's exactly.
        if not np.array_equal(footprint(out), want):
            raise SystemExit('%s: recolour changed the art/key footprint' % name)
        sheet[MASTER_ROW0 * CELL:(MASTER_ROW0 + BANK_ROWS) * CELL,
              col0 * CELL:(col0 + BANK_COLS) * CELL] = out
        print('  %-10s cols %2d-%2d%s' % (name, col0, col0 + BANK_COLS - 1,
                                          '   (identity)' if ramp is None else ''))

    if a.preview:
        preview(a.preview, sheet)
        print('preview -> %s' % a.preview)
    if not a.no_write:
        Image.fromarray(sheet).save(a.sheet)
        print('wrote %s' % a.sheet)


if __name__ == '__main__':
    main()
