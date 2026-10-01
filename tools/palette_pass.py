"""Put the game's art on its palette.

    python tools/palette_pass.py            # report only
    python tools/palette_pass.py --write    # recolour the assets in place

Run from the repo root, and run it LAST: after any tools/gen_*.py or anything
else that paints into the sheet. It is idempotent, so running it on art that
is already through it changes nothing.

Two rules, and this enforces both:

1. ONE PALETTE. Every colour drawn is one of art/direction/game_palette.gpl.
   A colour that is not goes where art/direction/fcremap.py sends it: a merged
   near-duplicate to the colour it was merged into, a leftover FC World colour
   to the old colour playing the same part, anything else to its nearest.

2. FOUR COLOURS A TILE -- the NES's own limit. Where a cell has more, its
   rarest colours merge into their nearest neighbour *within that cell*.
   Rarest is counted across the whole sheet, not the cell, so a colour is
   dropped everywhere or nowhere and a texture that runs across cells does not
   reduce one way on one side of a seam and another way on the other. Black is
   never dropped: it is the line.

Left alone:
  - the generators' hand-painted masters, which are never drawn -- they are
    what the generators read, and keep their full detail for that.
Block positions come from the generators, never restated here.

--write also regenerates src/fc_palette_lut.inc, the same mapping for the
colours the code makes up at run time (see include/fc_palette.h).
"""
import os, sys
from collections import Counter
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "art", "direction"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fcremap as fc
import gen_cave_tiles as cave
import gen_trail_tiles as trail

SHEET = os.path.join(ROOT, "assets", "tileset.png")
SPRITES = [os.path.join(ROOT, "assets", "player_small.png")]
KEY = (255, 0, 0)
BLACK = (0, 0, 0)
MASK_WHITE = (255, 255, 255)
CELL = 16
MAX_COLOURS = 4


def regions():
    """(kind, name, cells) for the blocks the pass leaves alone: the masks and
    the masters. cells is a set of (col, row)."""
    def block(c0, r0, nc, nr):
        return {(c, r) for c in range(c0, c0 + nc) for r in range(r0, r0 + nr)}
    return [
        ("master", "cave", block(cave.MASTER_COL0, 0, cave.BLOCK_COLS, cave.BLOCK_ROWS)),
        ("master", "trail", block(trail.MASTER_COL0, trail.MASTER_ROW0,
                                  trail.BANK_COLS, trail.BANK_ROWS)),
    ]


def colours_of(a, cells):
    got = set()
    for c, r in cells:
        blk = a[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL].reshape(-1, 3)
        got |= {tuple(int(v) for v in p) for p in np.unique(blk, axis=0)}
    return got


def apply_map(a, cells, m):
    for c, r in cells:
        blk = a[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
        flat = blk.reshape(-1, 3)
        uniq, inv = np.unique(flat, axis=0, return_inverse=True)
        new = np.array([m.get(tuple(int(v) for v in u), tuple(int(v) for v in u))
                        for u in uniq], dtype=np.uint8)
        blk[:] = new[inv.reshape(-1)].reshape(blk.shape)


def limit_cells(a, skip, opaque=None):
    """At most MAX_COLOURS non-key colours in any cell not in skip. opaque, if
    given, marks which pixels count (for sprites with real transparency)."""
    h, w = a.shape[0] // CELL, a.shape[1] // CELL
    fg = opaque if opaque is not None else ~np.all(a == KEY, axis=2)
    glob = Counter(map(tuple, a[fg].reshape(-1, 3).tolist()))
    reduced = 0
    for r in range(h):
        for c in range(w):
            if (c, r) in skip:
                continue
            ys, xs = slice(r * CELL, (r + 1) * CELL), slice(c * CELL, (c + 1) * CELL)
            blk, m = a[ys, xs], fg[ys, xs]
            cols = {tuple(int(v) for v in p) for p in np.unique(blk[m].reshape(-1, 3), axis=0)} \
                if m.any() else set()
            if len(cols) <= MAX_COLOURS:
                continue
            reduced += 1
            merge = {}
            live = set(cols)
            while len(live) > MAX_COLOURS:
                victim = min((k for k in live if k != BLACK),
                             key=lambda k: (glob[k], fc.luma(k)))
                live.discard(victim)
                merge[victim] = min(live, key=lambda k: fc.lab_dist(victim, k))
            for v in list(merge):              # chains: a -> b where b also merged
                t = merge[v]
                while t in merge:
                    t = merge[t]
                merge[v] = t
            for v, t in merge.items():
                hit = m & np.all(blk == v, axis=2)
                blk[hit] = t
    return reduced


def pass_sheet(write):
    a = np.array(Image.open(SHEET).convert("RGB"))
    before = len(np.unique(a.reshape(-1, 3), axis=0))
    skip = set()
    for kind, name, cells in regions():
        skip |= cells
        if kind == "mask":
            bad = colours_of(a, cells) - {KEY, MASK_WHITE}
            assert not bad, f"{name} mask holds more than white: {sorted(bad)[:4]}"
    rest = {(c, r) for r in range(a.shape[0] // CELL) for c in range(a.shape[1] // CELL)} - skip
    apply_map(a, rest, {c: fc.lookup(c) for c in colours_of(a, rest)})
    reduced = limit_cells(a, skip)

    drawn = np.ones(a.shape[:2], bool)
    for c, r in skip:
        drawn[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = False
    after = {tuple(int(v) for v in p) for p in np.unique(a[drawn].reshape(-1, 3), axis=0)} - {KEY}
    off = after - set(fc.PALETTE)
    print(f"tileset.png: {before} colours -> {len(after)} on the drawn art, "
          f"{reduced} cells cut to {MAX_COLOURS} colours, {len(off)} off the palette")
    assert not off, sorted(off)[:8]
    if write:
        Image.fromarray(a).convert("RGBA").save(SHEET)
    return a


def pass_sprite(path, write):
    """Sprites carry real transparency; only the opaque pixels are art."""
    rgba = np.array(Image.open(path).convert("RGBA"))
    a, alpha = rgba[:, :, :3].copy(), rgba[:, :, 3]
    op = alpha > 0
    cols = {tuple(int(v) for v in p) for p in np.unique(a[op].reshape(-1, 3), axis=0)}
    m = {c: fc.lookup(c) for c in cols}
    for c, t in m.items():
        a[op & np.all(a == c, axis=2)] = t
    reduced = limit_cells(a, set(), opaque=op)
    rgba[:, :, :3] = a
    after = {tuple(int(v) for v in p) for p in np.unique(a[op].reshape(-1, 3), axis=0)}
    print(f"{os.path.basename(path)}: {len(cols)} colours -> {len(after)}, "
          f"{reduced} cells cut; " + ", ".join("#%02x%02x%02x->#%02x%02x%02x" % (c + t)
                                              for c, t in m.items() if c != t))
    if write:
        Image.fromarray(rgba).save(path)


LUT_INC = os.path.join(ROOT, "src", "fc_palette_lut.inc")


def write_lut():
    """src/fc_palette_lut.inc: the same mapping for the game's own colours.
    See src/fc_palette.cpp for how it is read."""
    pal = fc.PALETTE
    idx = {c: i for i, c in enumerate(pal)}
    exact = {c: idx[c] for c in pal}
    exact.update({k: idx[v] for k, v in fc.LUT.items()})
    lut = []
    for r in range(32):
        for g in range(32):
            for b in range(32):
                c = (r * 8 + 4, g * 8 + 4, b * 8 + 4)
                lut.append(idx[fc.lookup(c) if c not in fc.KEYS else fc.nearest(c)])
    lines = ["// Generated by tools/palette_pass.py from art/direction/game_palette.gpl",
             "// and fcremap.py. Do not edit; change those and re-run --write.",
             f"#define FC_PALETTE_N {len(pal)}",
             f"static const uint8_t FC_PALETTE[FC_PALETTE_N][3] = {{"]
    lines += ["    { %3d, %3d, %3d }," % c for c in pal]
    lines += ["};", f"#define FC_EXACT_N {len(exact)}",
              "static const uint32_t FC_EXACT[FC_EXACT_N] = {"]
    ex = sorted(((c[0] << 16 | c[1] << 8 | c[2]) << 8 | i) for c, i in exact.items())
    lines += ["    " + ", ".join("0x%08xu" % v for v in ex[k:k + 6]) + ","
              for k in range(0, len(ex), 6)]
    lines += ["};", "static const uint8_t FC_LUT[32768] = {"]
    lines += ["    " + ",".join("%d" % v for v in lut[k:k + 32]) + ","
              for k in range(0, len(lut), 32)]
    lines += ["};", ""]
    text = "\n".join(lines)
    old = open(LUT_INC).read() if os.path.exists(LUT_INC) else None
    if old != text:
        with open(LUT_INC, "w", newline="\n") as f:
            f.write(text)
        print("wrote", os.path.relpath(LUT_INC, ROOT))


if __name__ == "__main__":
    write = "--write" in sys.argv
    if write:
        write_lut()
    pass_sheet(write)
    for s in SPRITES:
        pass_sprite(s, write)
    print("written" if write else "report only; --write to apply")
