"""10 Grand'Goule's detail against the cast (the user, 2026-11-03: "show how detailed it is compared to other sized sprites"): first frames of approved enemies, small to giant, all at 3x on black,
labelled with drawn size, colours and how many pixels each flat patch has on average (bigger = flatter). Read off the sheets the game loads.

    python art/enemies/pixellab/10_grand_goule/redo2/anim/detail_board.py   # detail_board.png, prints the table
"""
from pathlib import Path
import re
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
src = (ROOT / 'src/battle.cpp').read_text(encoding='utf-8')
rows = re.findall(r'\{ "(assets/enemies/(?:redraws/)?(\d\d)_(\w+)\.png)",\s*\{[^}]*\}(?:, (\d+))?(?:, (true|false))?', src)
sheets = {int(n): (p, name, int(f or 3), r == 'true') for p, n, name, f, r in rows}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
def first(n):
    p, name, f, r = sheets[n]
    im = Image.open(ROOT / p).convert('RGBA')
    fw, fh = (im.width // f, im.height // 8) if r else (im.width // (8 * f), im.height)
    c = im.crop((0, 0, fw, fh))
    return name, c.crop(c.getbbox())
def stats(im):
    g = {(x, y): im.getpixel((x, y))[:3] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}
    seen, n = set(), 0
    for p, c in g.items():
        if p in seen: continue
        n += 1; todo = [p]; seen.add(p)
        while todo:
            a = todo.pop()
            for d in N4:
                q = (a[0] + d[0], a[1] + d[1])
                if q not in seen and g.get(q) == c: seen.add(q); todo.append(q)
    return len(g), len(set(g.values())), n, len(g) / n
items = [(f'{i}', *first(i)) for i in (4, 54, 53, 17, 21, 22, 90, 92, 46, 91, 45, 94, 95, 96, 7, 41)]
def me(path):
    c = Image.open(HERE / path).convert('RGBA'); return c.crop(c.getbbox())
items = [('10 now', "grand goule, before", me('c_0.png')), ('10 flat', "grand goule, flat", me('flat_0.png'))] + items
S = 3
cols = 6
cw, ch = 100 * S, 80 * S + 34
board = Image.new('RGBA', (cols * cw, ch * ((len(items) + cols - 1) // cols)), (0, 0, 0, 255))
d = ImageDraw.Draw(board)
print(f"{'':8}{'name':22}{'drawn':>9}{'cols':>6}{'patches':>9}{'px/patch':>10}")
for i, (tag, name, im) in enumerate(items):
    px, col, n, avg = stats(im)
    x, y = (i % cols) * cw, (i // cols) * ch
    board.alpha_composite(im.resize((im.width * S, im.height * S), 0), (x + 4, y + 30))
    d.text((x + 4, y + 2), f'{tag} {name[:20]}', fill=(255, 255, 255, 255))
    d.text((x + 4, y + 15), f'{im.width}x{im.height}  {col} cols  {avg:.1f} px/patch', fill=(255, 220, 120, 255))
    print(f"{tag:8}{name[:21]:22}{im.width:>4}x{im.height:<4}{col:>6}{n:>9}{avg:>10.1f}")
board.save(HERE / 'detail_board.png'); print(board.size)
