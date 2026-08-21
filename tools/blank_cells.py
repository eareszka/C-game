"""Blank tileset cells by filling them with the colour key.

Blanking a cell something still reads is silent and destructive, so this refuses
to touch a cell listed as USED, and reports what each cell held before it went.
The real safety net is downstream: blanking a genuinely unused cell must change
ZERO rendered pixels, dungeon and overworld alike, so a before/after render diff
proves it either way. Run that, not just this.

Cells are given as col:row. The colour key is (255,0,0) -- see SDL_SetColorKey in
src/tilemap.cpp.

Usage:
  python tools/blank_cells.py <tileset.png> <col:row> [col:row ...] [--dry-run]
"""
import sys
from PIL import Image

KEY = (255, 0, 0)
CELL = 16

# The nine cells the cave wall renderer samples, in MASTER coordinates. Kept here
# as a tripwire, not as documentation -- if a constant moves, this list must move
# with it.
MASTER = {
    (28, 0), (28, 1), (28, 2),   # TALL_BAND, the 3-cell stacked north face
    (29, 7),                     # TRIM_S
    (31, 0), (31, 1), (31, 2),   # TRIM_WE + the run-end outline strip
    (31, 7),                     # TRIM_TRANS_L (the one surviving accent cell)
    (32, 0),                     # TALL_BAND_SOLO, the rock node
}

# tools/gen_cave_tiles.py stamps one recoloured copy of the master block per
# Material at cols 33-67, and those copies are what the renderer actually reads.
# Both halves are protected, and the master half is the one worth explaining:
# nothing samples it at runtime any more, so blanking it would change zero
# rendered pixels and sail through every render diff -- while destroying the
# source all seven blocks are generated from. A downstream check cannot catch
# that, which is exactly why it is named here.
#
# Must agree with MASTER_COL0 / OUT_COL0 / BLOCK_COLS in gen_cave_tiles.py and
# with CAVE_MASTER_COL0 / CAVE_ART_COL0 / CAVE_ART_COLS in src/dungeon.cpp.
MASTER_COL0, OUT_COL0, BLOCK_COLS, N_MATERIALS = 28, 33, 5, 7

USED = set(MASTER) | {
    (c - MASTER_COL0 + OUT_COL0 + m * BLOCK_COLS, r)
    for (c, r) in MASTER for m in range(N_MATERIALS)
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    path, cells = args[0], args[1:]

    targets = []
    for spec in cells:
        c, r = (int(v) for v in spec.split(':'))
        if (c, r) in USED:
            sys.exit(f"REFUSING: ({c},{r}) is in the USED set")
        targets.append((c, r))

    im = Image.open(path).convert('RGBA')
    px = im.load()
    blanked = already = 0
    for c, r in targets:
        n = 0
        for y in range(r * CELL, r * CELL + CELL):
            for x in range(c * CELL, c * CELL + CELL):
                if px[x, y][:3] != KEY:
                    n += 1
        if n == 0:
            already += 1
            print(f"  ({c:2d},{r}) already empty")
            continue
        print(f"  ({c:2d},{r}) blanking {n}/256 painted px")
        blanked += 1
        if not dry:
            for y in range(r * CELL, r * CELL + CELL):
                for x in range(c * CELL, c * CELL + CELL):
                    px[x, y] = (255, 0, 0, 255)

    print(f"\n{len(targets)} cells: {blanked} blanked, {already} already empty"
          + ("  [DRY RUN, nothing written]" if dry else ""))
    if not dry and blanked:
        im.save(path)
        print(f"wrote {path}")


main()
