"""Cut a sheet room's furniture into its pieces (connected, at least 20
pixels), each padded to sides in fours for PixelLab's edit, with its box in
the room's frame.

    python tools/interior_pieces.py N OUTDIR
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interior_render import rooms, ROOT
from PIL import Image

n, out = int(sys.argv[1]), sys.argv[2]
sheet = Image.open(os.path.join(ROOT, 'assets', 'tileset.png')).convert('RGBA')
sheet.putdata([(0, 0, 0, 0) if p[:3] == (255, 0, 0) else p for p in sheet.get_flattened_data()])
r = rooms()[n]
im = Image.new('RGBA', (320, 240))
for y, row in enumerate(r['furn']):
    for x, v in enumerate(row):
        if v >= 6:
            i = v - 6
            im.alpha_composite(sheet.crop(((i % 256) * 16, (i // 256) * 16, (i % 256) * 16 + 16, (i // 256) * 16 + 16)), (x * 16, y * 16))
f = im.crop((32, 49, 288, 193))
a = f.getchannel('A').load()
seen, comps = set(), []
for y in range(144):
    for x in range(256):
        if a[x, y] and (x, y) not in seen:
            st, c = [(x, y)], []
            seen.add((x, y))
            while st:
                p = st.pop()
                c.append(p)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (p[0] + dx, p[1] + dy)
                        if 0 <= q[0] < 256 and 0 <= q[1] < 144 and a[q] and q not in seen:
                            seen.add(q)
                            st.append(q)
            comps.append(c)
os.makedirs(out, exist_ok=True)
for k, c in enumerate(sorted([c for c in comps if len(c) >= 20], key=lambda c: min(p[0] for p in c))):
    box = (min(p[0] for p in c), min(p[1] for p in c), max(p[0] for p in c) + 1, max(p[1] for p in c) + 1)
    p = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
    for (x, y) in c:
        p.putpixel((x - box[0], y - box[1]), f.getpixel((x, y)))
    cc = Image.new('RGBA', ((p.width + 3) // 4 * 4, (p.height + 3) // 4 * 4))
    cc.paste(p, (0, 0))
    cc.save(os.path.join(out, 'p%d.png' % k))
    print(k, box)
