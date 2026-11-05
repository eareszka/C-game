"""18 Vatnaormur without its water (the user, 2026-11-02: no water under enemies in battle; its mini keeps it). Every cell
of the approved sheet: the pool, the white waterline and the foam taken off, nothing else redrawn, a black line added
only where its coils now end on the ground. Cell size and the body's place in it unchanged, so its shots still leave
from its mouth and humps. Writes no_water.png (the sheet) and no_water_review.png (before and after); the installed sheet
and the original are not touched unless run with --install.

    python art/enemies/pixellab/18_vatnaormur/no_water.py [--install]
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / 'assets/enemies/18_vatnaormur.png'
FW, FH, FRAMES = 114, 59, 5
WATER = {(0x3e, 0x91, 0xcc), (0x84, 0xa7, 0xe9)}
WHITE = (0xfc, 0xfc, 0xfc)
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def cell(im):
    """The water off one cell. The waterline is the row above the pool's first; below it everything goes; white and
    black at it, and white foam in the rows above it, go as well."""
    px = im.load()
    rows = [y for y in range(FH) if any(px[x, y][3] and px[x, y][:3] in WATER for x in range(FW))]
    if not rows: return im
    line = rows[0] - 1
    g = {(x, y): px[x, y][:3] for y in range(FH) for x in range(FW) if px[x, y][3]}
    g = {p: c for p, c in g.items() if p[1] < line and c not in WATER}
    for (x, y), c in list(g.items()):                    # foam: white specks low on the body, filled by what they sat on
        if c == WHITE and y >= line - 8:
            n = [g[x + a, y + b] for a, b in N4 if (x + a, y + b) in g and g[x + a, y + b] not in (WHITE, K)]
            if n: g[x, y] = max(set(n), key=n.count)
            else: del g[x, y]
    out = dict(g)
    for (x, y), c in g.items():                          # the one new edge: black under whatever now ends at the waterline
        if (x, y + 1) not in g and y == line - 1 and c != K: out[x, y + 1] = K
    res = Image.new('RGBA', (FW, FH))
    for (x, y), c in out.items():
        if 0 <= x < FW and 0 <= y < FH: res.putpixel((x, y), c + (255,))
    return res


def main():
    src = Image.open(SRC).convert('RGBA')
    out = Image.new('RGBA', src.size)
    for i in range(src.width // FW):
        out.paste(cell(src.crop((i * FW, 0, (i + 1) * FW, FH))), (i * FW, 0))
    out.save(HERE / 'no_water.png')
    S, G = 5, (0x6f, 0x9e, 0x5c, 255)
    b = Image.new('RGBA', (FW * S * 2, FH * S * 2), G)
    for i, (sheet, n) in enumerate(((src, 0), (out, 0), (src, 7 * FRAMES + 2), (out, 7 * FRAMES + 2))):
        c = sheet.crop((n * FW, 0, (n + 1) * FW, FH)).resize((FW * S, FH * S), 0)
        b.alpha_composite(c, ((i % 2) * FW * S, (i // 2) * FH * S))
    b.save(HERE / 'no_water_review.png')
    cols = {p[:3] for p in out.get_flattened_data() if p[3]}
    print(out.size, len(cols) - 1, 'colours + black', 'water left:', bool(cols & WATER))
    if '--install' in sys.argv:
        sys.path.insert(0, str(ROOT / 'tools'))
        import enemy_sheet
        dest = ROOT / 'assets/enemies/redraws/18_vatnaormur.png'
        enemy_sheet.install(out, str(dest), FRAMES, False, ms=250, palette=sorted('%02x%02x%02x' % c for c in cols))
        print('installed', dest)


main()
