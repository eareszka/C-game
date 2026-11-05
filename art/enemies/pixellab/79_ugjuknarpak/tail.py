"""79 Ugjuknarpak's long rat tail, drawn by hand onto frame 0 (the user, 2026-10-28: "have it have a long rat
tail", then "should be pink and curled. think of a rats tail"): pink and bare, out of the stub behind its
left hind flipper (the stub goes pink too), sweeping out along the ground and curling up and over at the
end. Two pixels thick near the body, one toward the tip; painted only where the frame is empty (it is behind
the body), one black outline. From idle_frame0_notail.png (the approved draft) to idle_frame0_clean.png.

    python art/enemies/pixellab/79_ugjuknarpak/tail.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
PINK, BLACK = (0xec, 0x84, 0x76), (0, 0, 0)
STUB = {(0x84, 0x86, 0x94), (0x47, 0x47, 0x51), (0x59, 0x59, 0x65)}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
# Its line: a cubic from the stub out and round -- low along the ground, then up and curling back over.
P = ((31, 58), (12, 64), (2, 50), (11, 46))


def at(t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(*P))


im = Image.open(HERE / 'idle_frame0_notail.png').convert('RGBA')
for y in range(54, 61):                       # the stub, pink
    for x in range(28, 34):
        p = im.getpixel((x, y))
        if p[3] and p[:3] in STUB:
            im.putpixel((x, y), PINK + (255,))
tail = set()
for i in range(400):
    t = i / 399
    x, y = at(t)
    tail.add((round(x), round(y)))
    if t < 0.45:
        tail.add((round(x), round(y) + 1))   # thicker near the body
tail.add((12, 47))                            # the curl's tip turning back down
painted = {p for p in tail if not im.getpixel(p)[3]}
for p in painted:
    im.putpixel(p, PINK + (255,))
for (x, y) in painted:
    for dx, dy in N4:
        q = (x + dx, y + dy)
        if 0 <= q[0] < im.width and 0 <= q[1] < im.height and not im.getpixel(q)[3]:
            im.putpixel(q, BLACK + (255,))
im.save(HERE / 'idle_frame0_clean.png')
print(len(painted), 'tail px', im.getbbox(), len({p[:3] for p in im.get_flattened_data() if p[3]}) - 1, 'colours + black')
