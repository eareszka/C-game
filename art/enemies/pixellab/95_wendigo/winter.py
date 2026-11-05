"""95 Wendigo in the cold (the user, 2026-11-03: "design is perfect but i want it to be more winter/cold themed like the lore"): the approved shapes pixel for pixel (frame0_bone.png), recoloured.
Bone turns frost-pale, its shadows ice blue; every upward-facing edge of a limb carries snow; the hanging tar freezes into icicles, pale at the tips; horns the blue of old ice; eyes stay crimson. Black lines untouched.

    python art/enemies/pixellab/95_wendigo/winter.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_compare.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
K = (0, 0, 0)
PALE, TAN, DKT, DK2, GREY, TAR, RED = (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x78, 0x58, 0x30), (0x46, 0x34, 0x22), (0x84, 0x86, 0x94), (0x37, 0x38, 0x7b), (0xb6, 0x43, 0x3d)
SNOW, FROST, ICE, DEEP, NAVY = (0xfc, 0xfc, 0xfc), (0xc6, 0xcc, 0xda), (0x84, 0xa7, 0xe9), (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b)
MAP = {PALE: SNOW, TAN: FROST, DKT: ICE, DK2: DEEP, GREY: ICE, TAR: NAVY, RED: RED, K: K}
src = Image.open(HERE / 'frame0_bone.png').convert('RGBA')
W, H = src.size
s = src.load()
f = Image.new('RGBA', (W, H)); px = f.load()
for y in range(H):
    for x in range(W):
        if s[x, y][3]: px[x, y] = MAP[s[x, y][:3]] + (255,)
for y in range(1, H):                                           # snow lies on what faces up
    for x in range(W):
        if s[x, y][3] and s[x, y][:3] == TAN and (not s[x, y - 1][3] or s[x, y - 1][:3] == K): px[x, y] = SNOW + (255,)
for x in range(W):                                              # the tar freezes: icicles, paler toward the tips
    ys = [y for y in range(H) if s[x, y][3] and s[x, y][:3] == TAR]
    for y in ys:
        low = max(ys) - y
        px[x, y] = (SNOW if low == 0 else ICE if low <= 2 else DEEP if low <= 5 else NAVY) + (255,)
from collections import Counter
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
for _ in range(3):                                              # the smallest snow flecks merge into what surrounds them (the user: "merge the flecks"); icicle tips kept
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] in (K, RED) or s[x, y][:3] == TAR: continue
            near = [px[x + a, y + b] for a, b in N8]
            if not any(n[3] and n[:3] == c[:3] for n in near):
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                if pick: px[x, y] = pick[0][0] + (255,)
f.save(HERE / 'frame0.png')
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
cmp = Image.new('RGBA', (W * 12 + 12, H * 6), (0, 0, 0, 255))
cmp.alpha_composite(src.resize((W * 6, H * 6), 0), (0, 0)); cmp.alpha_composite(f.resize((W * 6, H * 6), 0), (W * 6 + 12, 0)); cmp.save(HERE / 'frame0_compare.png')
print(sum(1 for a, b in zip(src.get_flattened_data(), f.get_flattened_data()) if bool(a[3]) != bool(b[3])), 'pixels changed shape')
