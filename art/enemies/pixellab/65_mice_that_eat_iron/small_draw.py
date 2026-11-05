"""65 at the small sprites' size, the concept's three mice and their iron beam (the user: "small sized like the small
sized sprites"; 01 and 03 are 20x20). PixelLab and a plain shrink both lost the mice at this size (small_review.png), so
it is drawn here at size, fill only, the approved colours, one black outline round it. The middle mouse stands two
rows taller; the beam runs through their paws with a bite out of its right end.

    python art/enemies/pixellab/65_mice_that_eat_iron/small_draw.py     # writes small0.png, small0_x10.png
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
PAL = {'K': '000000', 'F': '848694', 'S': '474751', 'M': 'c6ccda', 'P': 'ec8476', 'T': 'd7a175', 'I': 'bcbeca'}
W, H = 38, 22
MOUSE = """
.PPP...PPP.
PPPPF.FPPPP
PPPFFFFFPPP
.PFFFFFFFP.
..FKFFFKF..
..FFFMFFF..
..SFMMMFS..
..SSFFFSS..
.SFTTTTTFS.
.SFTTTTTFS.
..PP...PP..
""".strip().split(chr(10))
BEAM_ROW = 6                     # the mouse row the beam crosses
BOTTOM = H - 2                   # last fill row: the outline takes the frame's bottom row
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def draw():
    g = {}
    # left, right, then the middle over them (it stands taller)
    for ox, oy in ((2, 8), (21, 8), (11, 6)):
        for y, r in enumerate(MOUSE):
            for x, c in enumerate(r):
                if c != '.': g[ox + x, oy + y] = c
    for x, y in ((1, 16), (0, 15), (0, 14), (32, 16), (33, 15), (33, 14)):      # the two outer tails, curling up
        g[x, y] = 'S'
    beam_y = 15
    for x in range(2, 32):
        g[x, beam_y] = 'I'
    g.pop((28, beam_y)); g.pop((29, beam_y))          # the bite, leaving the beam's chewed tip
    g[28, beam_y] = g[29, beam_y] = 'K'
    return g


def outlined(g):
    out = dict(g)
    for x, y in g:
        for dx, dy in N4:
            if (x + dx, y + dy) not in g: out[x + dx, y + dy] = 'K'
    return out


def main():
    g = outlined(draw())
    ys = [y for x, y in g]
    drop = H - 1 - max(ys)
    im = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x + 2 < W and 0 <= y + drop < H:
            im.putpixel((x + 2, y + drop), tuple(int(PAL[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    im.save(HERE / 'small0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(im)
    bg.resize((W * 12, H * 12), 0).save(HERE / 'small0_x12.png')
    print(im.getbbox())


main()
