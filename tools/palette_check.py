"""Is a rendered frame on the palette?

    python tools/palette_check.py shot.png [more.png ...]

For each image: how many pixels are not one of the 64 (art/direction/fcremap.py),
and which colours they are. A frame from shot.exe or dngshot.exe should report
none; anything it does report is a colour the renderer made up at run time
rather than took from the art -- a blend, a multiply, a literal nobody snapped.
Exits non-zero if any image has off-palette pixels.
"""
import os, sys
from collections import Counter
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "art", "direction"))
import fcremap as fc

PAL = set(fc.PALETTE)
bad_any = False
for path in sys.argv[1:]:
    im = Image.open(path).convert("RGB")
    counts = Counter(im.getdata())
    off = {c: n for c, n in counts.items() if c not in PAL}
    total = im.width * im.height
    n_off = sum(off.values())
    used = len([c for c in counts if c in PAL])
    print(f"{os.path.basename(path)}: {len(counts)} colours, {used} of the palette; "
          f"{n_off} of {total} pixels off it ({100 * n_off / total:.2f}%)")
    for c, n in sorted(off.items(), key=lambda e: -e[1])[:8]:
        print("    #%02x%02x%02x  %d" % (*c, n))
    bad_any |= n_off > 0
sys.exit(1 if bad_any else 0)
