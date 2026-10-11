"""69 Bes Chem, big tier, one view (3/4 right), to art/direction/SPRITE_STYLE.md.

The size of the sprite it replaces (its body 43 px tall), at the small end of
the big tier. A hunched egg-bird: the head runs into the body, a round fanged
maw in its chest, glowing eyes under heavy brows, bare thin legs. The wings
grow out of the shoulders as part of the one body shape (no line across the
root, only a fold under the arm), held out and down, their trailing edge cut
into feather tips with a line between each feather.

Drafted as shapes (silhouette, then outline, then tones by form), then drawn
into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io, math
from PIL import Image, ImageDraw
PAL = {'K': '000000', 'D': '583518', 'M': '815423', 'L': 'c18a39', 's': 'd7a175', 'Y': 'f0bc3c', 'W': 'fcfcfc', 'P': '361f42'}
W, H = 59, 44

def mask(draw_fn):
    im = Image.new('1', (W, H), 0); draw_fn(ImageDraw.Draw(im)); px = im.load()
    return {(x, y) for y in range(H) for x in range(W) if px[x, y]}

def line(a, b):
    (x0, y0), (x1, y1) = a, b; n = max(abs(x1 - x0), abs(y1 - y0)) or 1
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]

# -- silhouette ---------------------------------------------------------------
body = mask(lambda d: (d.ellipse((22, 2, 40, 23), fill=1), d.ellipse((20, 9, 43, 34), fill=1),
                       d.polygon([(29, 2), (30, 0), (32, 2), (33, 1), (34, 3)], fill=1)))
NS, NT = (23, 10), (2, 33)                       # near wing: shoulder, tip
near_edge = [NT, (2, 35), (5, 32), (7, 36), (9, 33), (11, 36), (14, 33), (16, 36), (18, 33), (21, 35), (24, 31)]
near = mask(lambda d: d.polygon([NS] + near_edge + [(26, 23)], fill=1))
FS, FT = (40, 11), (56, 28)                      # far wing, foreshortened
far_edge = [FT, (56, 30), (53, 27), (52, 32), (49, 28), (47, 32), (45, 29), (43, 32), (41, 29)]
far = mask(lambda d: d.polygon([FS] + far_edge + [(38, 23)], fill=1))
legs = mask(lambda d: (d.rectangle((26, 33, 28, 41), fill=1), d.rectangle((34, 33, 36, 41), fill=1)))
feet = mask(lambda d: (d.polygon([(25, 41), (31, 41), (32, 43), (24, 43)], fill=1), d.polygon([(33, 41), (39, 41), (40, 43), (32, 43)], fill=1)))
fur = body | near | far
whole = fur | legs | feet
g = {p: 'M' for p in fur}
for p in (legs | feet) - fur: g[p] = 's'

def edge(shape, within=None):
    """The pixels of shape on its rim (4-adjacent to something outside `within`)."""
    within = within or shape
    return {(x, y) for (x, y) in shape if any((x + dx, y + dy) not in within for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}

# -- tones, by form -----------------------------------------------------------
def lit_from_above(shape, n):                    # the top n px of a shape, measured down each column
    return {(x, y) for (x, y) in shape if any((x, y - k) not in whole for k in range(1, n + 1))}
for p in lit_from_above(near - body, 3): g[p] = 'L'                      # the near wing's leading edge
for p in far - body: g[p] = 'D'                                          # the far wing: turned away
for p in lit_from_above(far - body, 3): g[p] = 'M'
chest = mask(lambda d: (d.ellipse((29, 5, 40, 17), fill=1), d.ellipse((27, 12, 41, 32), fill=1)))
for p in chest & body: g[p] = 'L'                                        # the head's brow and the chest, facing us
for (x, y) in body:                                                      # the back, and under the belly
    if any((x - k, y) not in body for k in range(1, 4)) and x < 30: g[(x, y)] = 'D'
    if any((x, y + k) not in body for k in range(1, 3)) and y > 26: g[(x, y)] = 'D'
for (x, y) in near - body:                                               # the wing's root, in the body's shade
    if any((x + k, y) in body for k in range(1, 3)) and y > 20: g[(x, y)] = 'D'

# -- outline and lines --------------------------------------------------------
for p in edge(whole): g[p] = 'K'
for p in edge(legs | feet) - fur: g[p] = 'K'
for a, b in (((24, 31), (23, 23)), ((41, 29), (40, 24))):                # the fold under each arm; the root above it is open
    for p in line(a, b): g[p] = 'K'
for (nx, ny), S in [(p, NS) for p in near_edge[2:-1:2]] + [(p, FS) for p in far_edge[2:-1:2]]:
    end = (round(nx + (S[0] - nx) * 0.42), round(ny + (S[1] - ny) * 0.42))   # a line up between each pair of feathers
    for p in line((nx, ny), end):
        if p in fur and p not in body: g[p] = 'K'
for p in ((28, 42), (36, 42)): g[p] = 'K'                                 # toes

# -- the maw ------------------------------------------------------------------
MX, MY = 33.5, 19.5
maw = mask(lambda d: d.ellipse((27, 13, 40, 26), fill=1))
for p in maw: g[p] = 'P'
for p in edge(maw): g[p] = 'K'
inner = maw - edge(maw)
teeth = mask(lambda d: [d.polygon([(MX + 6.2 * math.cos(a) - 1.25 * math.sin(a), MY + 6.2 * math.sin(a) + 1.25 * math.cos(a)),
                                    (MX + 6.2 * math.cos(a) + 1.25 * math.sin(a), MY + 6.2 * math.sin(a) - 1.25 * math.cos(a)),
                                    (MX + 3.9 * math.cos(a), MY + 3.9 * math.sin(a))], fill=1)
                         for a in (math.tau * (i + 0.5) / 8 for i in range(8))])     # a ring of eight fangs pointing in
for p in teeth & inner: g[p] = 'W'

# -- eyes ---------------------------------------------------------------------
for ex, slope in ((28, 1), (36, -1)):                                    # glowing, each in a black socket under a slanted brow
    for dx in range(-1, 3):
        for dy in range(-1, 3): g[(ex + dx, 8 + dy)] = 'Y' if dx in (0, 1) and dy in (0, 1) else 'K'
    for dx in range(-2, 4): g[(ex + dx, 6 + (dx if slope > 0 else 1 - dx) // 3)] = 'K'

DR = [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]
if __name__ == '__main__':
    json.dump({'pal': PAL, 'view_w': W, 'views': {'DR': DR}, 'order': ['DR']}, open('design.json', 'w'))
    t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + ['#BODY', '30', '#DIRS', 'quarter', '#DR'] + DR
    io.open('69_bes_chem.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 2 + 2, H), (255, 170, 200, 255))
    for (x, y), c in g.items():
        im.putpixel((x, y), tuple(int(PAL[c][k:k + 2], 16) for k in (0, 2, 4)) + (255,)); im.putpixel((W + 2 + x, y), (0, 0, 0, 255))
    im.resize((im.width * 10, im.height * 10), Image.NEAREST).save('draft.png')
    bw = [x for (x, y) in body]; print('body', max(bw) - min(bw) + 1, 'wide; whole', max(x for x, y in whole) - min(x for x, y in whole) + 1, 'x', max(y for x, y in whole) + 1)
