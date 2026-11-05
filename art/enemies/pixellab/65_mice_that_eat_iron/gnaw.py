"""65's gnaw: the approved small drawing (small_draw.py's small0.png) animated, four frames at 150 ms. Each mouse's head
dips to the beam and its mouth opens, out of step with the others; bodies and feet stay planted, the beam jolts a row
as a bite lands, and the outer tails flick. The first frame is the approved drawing's pose.

    python art/enemies/pixellab/65_mice_that_eat_iron/gnaw.py    # writes gnaw/gnaw_N.png, gnaw_review.png, gnaw.gif
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
PAL = {'K': '000000', 'F': '848694', 'S': '474751', 'M': 'c6ccda', 'P': 'ec8476', 'T': 'd7a175', 'I': 'bcbeca'}
W, H = 38, 22
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
HEAD = """
.PPP...PPP.
PPPPF.FPPPP
PPPFFFFFPPP
.PFFFFFFFP.
..FKFFFKF..
..FFFMFFF..
..SFMMMFS..
..SSFFFSS..
""".strip().split(chr(10))
BODY = """
.SFTTTTTFS.
.SFTTTTTFS.
..PP...PP..
""".strip().split(chr(10))
OPEN = {6: '..SFMKMFS..'}             # the head dipped: its mouth open on the beam
SPOTS = ((2, 8), (21, 8), (11, 6))    # left, right, then the middle over them
DIP = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))   # frame: which of (left, right, middle) has its head down
JOLT = (0, 1, 0, 1)                   # the beam, a row lower as a bite lands
TAIL = (0, 0, 1, 1)                   # the outer tails, curled or flicked


def frame(f):
    g = {}
    for m, (ox, oy) in enumerate(SPOTS):
        d = DIP[f][m]
        for y, r in enumerate(BODY):
            for x, c in enumerate(r):
                if c != '.': g[ox + x, oy + len(HEAD) + y] = c
        for y, r in enumerate(HEAD):
            if d and y in OPEN: r = OPEN[y]
            for x, c in enumerate(r):
                if c != '.': g[ox + x, oy + y + d] = c
    tail = ((1, 16), (0, 15), (0, 14), (32, 16), (33, 15), (33, 14))
    if TAIL[f]: tail = ((1, 16), (0, 16), (0, 15), (32, 16), (33, 16), (33, 15))
    for p in tail: g[p] = 'S'
    by = 15 + JOLT[f]
    for x in range(2, 32): g[x, by] = 'I'
    g[28, by] = g[29, by] = 'K'       # the bite
    out = dict(g)
    for x, y in g:
        for dx, dy in N4:
            if (x + dx, y + dy) not in g: out[x + dx, y + dy] = 'K'
    return out


def image(g, drop):
    im = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x + 2 < W and 0 <= y + drop < H:
            im.putpixel((x + 2, y + drop), tuple(int(PAL[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    return im


def main():
    gs = [frame(f) for f in range(4)]
    drop = H - 1 - max(y for g in gs for x, y in g)      # one ground line for all four: no sliding
    frames = [image(g, drop) for g in gs]
    (HERE / 'gnaw').mkdir(exist_ok=True)
    for i, im in enumerate(frames): im.save(HERE / 'gnaw' / f'gnaw_{i}.png')
    S, GREEN = 8, (0x6f, 0x9e, 0x5c, 255)
    b = Image.new('RGBA', (W * S * 2, H * S * 2), GREEN)
    for i, im in enumerate(frames):
        b.alpha_composite(im.resize((W * S, H * S), 0), ((i % 2) * W * S, (i // 2) * H * S))
        print(i, im.getbbox())
    b.save(HERE / 'gnaw_review.png')
    big = []
    for im in frames:
        bg = Image.new('RGBA', (W, H), GREEN); bg.alpha_composite(im)
        big.append(bg.resize((W * 8, H * 8), 0))
    big[0].save(HERE / 'gnaw.gif', save_all=True, append_images=big[1:], duration=150, loop=0, disposal=1)


main()
