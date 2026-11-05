"""96 Bregdi: back to design b4 (the user, 2026-11-03: "go back to old design but with the colors i described"): the same shapes (frame0_green.png), in the colours of the user's description --
hide gray with muddy-brown shade, fins taupe, belly and jaw faded beige, charcoal dorsal ridge, mouth dark crimson with magenta at its back, ivory needle teeth along both jaws.

    python art/enemies/pixellab/96_bregdi/redo/colours.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_compare.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
K = (0, 0, 0)
HIDE, SHADE, PALE, PALE_D, MOUTH, TOOTH = (0x2c, 0x6c, 0x44), (0x16, 0x36, 0x23), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x7c, 0x0a, 0x1b), (0xfc, 0xfc, 0xfc)
GRAY, BROWN, TAUPE, BEIGE, IVORY, CHAR = (0x84, 0x86, 0x94), (0x46, 0x34, 0x22), (0x8d, 0x6b, 0x4f), (0xb2, 0x96, 0x6a), (0xe8, 0xe0, 0xc0), (0x34, 0x34, 0x3e)
MAG = (0xfc, 0x74, 0xb4)                                 # the palette has no dark magenta: its one vivid magenta, kept small
src = Image.open(HERE / 'frame0_green.png').convert('RGBA')
W, H = src.size
s = src.load()
f = Image.new('RGBA', (W, H)); px = f.load()
FIN = lambda x, y: x >= 66 and y >= 38                   # the near fin, by its place in the frame
for y in range(H):
    for x in range(W):
        c = s[x, y]
        if not c[3]: continue
        n = c[:3]
        if n == HIDE: n = TAUPE if FIN(x, y) else GRAY
        elif n == SHADE: n = BROWN
        elif n == PALE: n = BEIGE
        elif n == PALE_D: n = BEIGE
        elif n == MOUTH: n = MOUTH
        elif n == TOOTH: n = IVORY
        px[x, y] = n + (255,)
for x in range(W):                                       # the charcoal ridge: the back's top edge, behind the head
    if x < 40 or x > 76: continue
    for y in range(H):
        c = s[x, y]
        if c[3] and c[:3] == HIDE:
            px[x, y] = CHAR + (255,)
            break
# the mouth's back is magenta
ms = [(x, y) for y in range(H) for x in range(W) if s[x, y][3] and s[x, y][:3] == MOUTH]
mid = sorted(p[0] for p in ms)[len(ms) // 2]
for x, y in ms:
    if x >= mid: px[x, y] = MAG + (255,)
# ivory needle teeth on both jaws, every other column, in the black of the open mouth: only where the jaws are
for x in range(25, 34, 2):
    for y in range(13, 23):
        if s[x, y][3] and s[x, y][:3] == K and s[x, y - 1][3] and s[x, y - 1][:3] != K and s[x, y + 1][3] and s[x, y + 1][:3] == K:
            px[x, y] = IVORY + (255,); break
for x in range(26, 37, 2):
    for y in range(28, 21, -1):
        if s[x, y][3] and s[x, y][:3] == K and s[x, y + 1][3] and s[x, y + 1][:3] != K and s[x, y - 1][3] and s[x, y - 1][:3] == K:
            px[x, y] = IVORY + (255,); break
for y in range(H):                                       # the eye takes the ivory: eight colours and black
    for x in range(W):
        if px[x, y][3] and px[x, y][:3] == (0xfa, 0xe4, 0x88): px[x, y] = IVORY + (255,)
from collections import Counter
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
for x, y in [(31, 17), (29, 24), (74, 42)]:              # the three lone pixels the check found
    near = [px[x + a, y + b] for a, b in N8]
    pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
    if pick and px[x, y][3]: px[x, y] = pick[0][0] + (255,)
f.save(HERE / 'frame0.png')
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
cmp = Image.new('RGBA', (W * 12 + 12, H * 6), (0, 0, 0, 255))
cmp.alpha_composite(src.resize((W * 6, H * 6), 0), (0, 0)); cmp.alpha_composite(f.resize((W * 6, H * 6), 0), (W * 6 + 12, 0)); cmp.save(HERE / 'frame0_compare.png')
print(len({p[:3] for p in f.get_flattened_data() if p[3]}), 'colours with black')
