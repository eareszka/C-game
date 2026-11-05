"""95 Witkes from the user's reference (2026-11-03, reference_user.webp: "similar to this using pixellab"): the creature alone, the size silhouette and map painted out, background clear,
shrunk onto the 98x65 frame as a source for PixelLab, feet on the last rows.

    python art/enemies/pixellab/95_witkes/redo/ref/sketch.py   # sketch.png, input.png (padded to 100x68), sketch_x6.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
im = Image.open(HERE / 'reference_user.webp').convert('RGB')
print(im.size)
px = im.load()
sx, sy = im.width / 1024, im.height / 943     # the positions below are read at 1024 wide
for x in range(int(340 * sx), im.width):      # silhouette, person and map, top right
    for y in range(0, int(235 * sy)):
        px[x, y] = (255, 255, 255)
rgba = im.convert('RGBA'); p2 = rgba.load()
# the background is near-white and reached from the edge; the pale gaps under the body are too
todo = [(x, y) for x in (0, im.width - 1) for y in range(im.height)] + [(x, y) for y in (0, im.height - 1) for x in range(im.width)]
seen = set()
pale = lambda c: min(c[:3]) > 232
while todo:
    x, y = todo.pop()
    if (x, y) in seen or not (0 <= x < im.width and 0 <= y < im.height): continue
    seen.add((x, y))
    if not pale(p2[x, y]): continue
    p2[x, y] = (0, 0, 0, 0)
    todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
for x in range(im.width):                      # enclosed pale gaps (under the belly) clear too
    for y in range(im.height):
        if p2[x, y][3] and min(p2[x, y][:3]) > 245: p2[x, y] = (0, 0, 0, 0)
box = rgba.getbbox(); print('creature', box)
c = rgba.crop(box)
s = (H - 2) / c.height
w, h = max(1, round(c.width * s)), H - 2
small = Image.new('RGBA', (w, h))
for y in range(h):
    for x in range(w):
        x0, x1 = int(x / s), max(int(x / s) + 1, int((x + 1) / s))
        y0, y1 = int(y / s), max(int(y / s) + 1, int((y + 1) / s))
        pts = [c.getpixel((i, j)) for j in range(y0, min(y1, c.height)) for i in range(x0, min(x1, c.width))]
        sol = [q for q in pts if q[3]]
        if len(sol) * 2 < len(pts) or not sol: continue
        small.putpixel((x, y), tuple(sum(q[k] for q in sol) // len(sol) for k in range(3)) + (255,))
f = Image.new('RGBA', (W, H)); f.alpha_composite(small, ((W - w) // 2, H - 1 - h))
f.save(HERE / 'sketch.png'); print('frame', f.getbbox())
pad = Image.new('RGBA', (100, 68)); pad.paste(f, (1, 1)); pad.save(HERE / 'input.png')
bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(f); bg.resize((W * 6, H * 6), 0).save(HERE / 'sketch_x6.png')
