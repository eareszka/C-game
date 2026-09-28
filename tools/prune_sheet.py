"""Blank the art in assets/tileset.png that nothing draws.

    make sheetcensus && ./sheetcensus.exe          # writes art/_work/sheet_usage.png
    python tools/prune_sheet.py [--write]

Each entry below is a whole object that no draw reads, named so the reason
survives. The census has the final say: an entry any draw reads is refused,
so a list that has gone stale cannot blank art the game now uses. What the
census cannot rule on is the other direction -- art drawn but not wired in
yet -- which is why this is a list someone chose and not "every cell the
census missed". Pruned cells become the key colour, so the sheet's layout,
and every cell id in the code, stays where it was.
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = os.path.join(ROOT, "assets", "tileset.png")
USAGE = os.path.join(ROOT, "art", "_work", "sheet_usage.png")
KEY = (255, 0, 0)


def cells(c0, c1, r0, r1):
    return [(c, r) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


PRUNE = {
    "hollow stump, dark bush and palm":        cells(14, 17, 2, 3),
    "wasteland's spotty variants (see COVER_WASTE)": [(24, 4), (26, 4)],
    "stone steps":                             cells(1, 3, 11, 11) + cells(0, 3, 12, 12)
                                               + cells(0, 2, 13, 13),
    "retired grass/snow ladder (see cliff_top_cover)": cells(18, 29, 12, 14),
    "retired waste ladder":                    cells(31, 31, 12, 14),
}


def main(write):
    used = np.asarray(Image.open(USAGE).convert("L")) > 127
    a = np.array(Image.open(SHEET).convert("RGB"))
    n = 0
    for name, cs in PRUNE.items():
        drawn = [(c, r) for c, r in cs if used[r, c]]
        if drawn:
            sys.exit(f"{name}: the census saw {drawn} drawn; not pruning")
        for c, r in cs:
            a[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = KEY
        n += len(cs)
        print(f"  {name}: {len(cs)} cells")
    print(f"{n} cells {'blanked' if write else 'would be blanked; --write to apply'}")
    if write:
        Image.fromarray(a).convert("RGBA").save(SHEET)


if __name__ == "__main__":
    main("--write" in sys.argv)
