"""93 Chipique's idle, choppy (the user, 2026-11-03: "too smooth ... longer animation/more movement but still be choppy like the other sprites"): every
other frame of the 16-frame loop (f_N, anim.py), so 8 poses at the game's default 260 ms, a 2.1 s loop with bigger steps. The canoe's paddle and figure
are locked to the approved frame (PixelLab's paddle shrank to a stub). Writes c_N.png, review_choppy.png, choppy.gif; choppy.lua makes 93_choppy_review.aseprite.

    python art/enemies/pixellab/93_chipique/redo3/long/choppy.py
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 98, 65, 260
PICK = (0, 2, 4, 7, 9, 11, 13, 15)   # 6 and 8 hardly differ: stepped past
LOCK = (50, 26, 76, 50)         # x0, y0, x1, y1: the paddle, the figure and the canoe's back rim
BASE = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
TAIL = lambda x, y: x >= 70 and y < 42          # the tail keeps moving through the top right of that box; the figure stays whole
out = []
for n, i in enumerate(PICK):
    f = Image.open(HERE / f'f_{i}.png').convert('RGBA')
    for y in range(LOCK[1], LOCK[3]):
        for x in range(LOCK[0], LOCK[2]):
            if not TAIL(x, y): f.putpixel((x, y), BASE.getpixel((x, y)))
    px = f.load()
    for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]]:      # the outline closed again where lock meets tail
        if any(0 <= x + a < W and 0 <= y + b < H and px[x + a, y + b][3] and px[x + a, y + b][:3] != (0, 0, 0) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = (0, 0, 0, 255)
    f.save(HERE / f'c_{n}.png'); out.append(f)
print([f.getbbox() for f in out])
S, G = 3, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 4, H * S * 2), G)
for k, f in enumerate(out): b.alpha_composite(f.resize((W * S, H * S), 0), ((k % 4) * W * S, (k // 4) * H * S))
b.save(HERE / 'review_choppy.png')
big = []
for f in out:
    bg = Image.new('RGBA', (W, H), G); bg.alpha_composite(f); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / 'choppy.gif', save_all=True, append_images=big[1:], duration=MS, loop=0)
