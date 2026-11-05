"""93 Chipique: frame 0 (the user, 2026-11-03: concept c2, "no water and more prominent canoe with evil spirit wizard inside", then "smaller wizard
like 1/3 size"). A serpent rising tall from its round coil, facing front, a big canoe held in the coil with a tiny evil wizard standing in it.

wizard/w2.png gives the coil and big canoe; its large wizard hid the snake, so everything above the canoe's rim comes from concepts/c2.png (neck, head,
tail), and the wizard is drawn again by hand at a third of the size: PixelLab would not shrink him (wizard/s1, s2), and scaling turned him to mush.
Colours fold onto the palette; the coil's texture flattens. One closed black outline.

    python art/enemies/pixellab/93_chipique/redo4/views.py   # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / '83_beast_of_barrisdale'))
import tidy as tidy_mod

W, H = 98, 65
K = (0, 0, 0)
LIT, DARK = (0x59, 0x59, 0x65), (0x34, 0x34, 0x3e)
CREAM, WOOD, WOOD_D = (0xce, 0xbe, 0x82), (0xc1, 0x8a, 0x39), (0x78, 0x58, 0x30)
ROBE, GLOW, WHITE = (0x5e, 0x48, 0x6a), (0xfa, 0xe4, 0x88), (0xfc, 0xfc, 0xfc)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
RIM = lambda x: 41 - (x - 31) * 8 / 37                  # the canoe's back rim on w2, source coordinates
WIZARD_AT = (47, 29)                                    # source column and row of the drawing's first character
LETTERS = {'K': K, 'R': ROBE, 'G': GLOW, 'S': K}
WIZARD = ('....K.....S.',
          '...KRK...S.S',
          '..KRRRK..S..',
          '.KRRRRRK.S..',
          'KKKKKKKKKS..',
          '.KGKGK...S..',
          '.KKKKK...S..',
          '.KRRRK...S..',
          'KRRRRRK..S..',
          'KRRRRRK..S..')


def fold(p, warm_ok=True):
    r, g, b = p
    v = max(p)
    if v < 0x1e: return K
    if min(p) > 0xd8: return WHITE
    if not warm_ok and r > 0xa8 and g > 0x90 and b > 0x60: return CREAM     # the belly, on the concept's snake only
    if r > g + 12:
        if not warm_ok: return DARK
        return WOOD if r > 0x90 else WOOD_D
    return LIT if v >= 0x48 else DARK


def flat(g, most=8):
    seen, out = set(), dict(g)
    for p, c in g.items():
        if p in seen: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for dx, dy in N4:
                q = (a[0] + dx, a[1] + dy)
                if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
        seen |= piece
        if c in (K, WHITE, CREAM) or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def main():
    w2 = Image.open(HERE / 'wizard/w2.png').convert('RGBA')
    c2 = Image.open(HERE / 'concepts/c2.png').convert('RGBA')
    g = {(x, y): fold(w2.getpixel((x, y))[:3]) for y in range(64) for x in range(96) if w2.getpixel((x, y))[3] > 127}
    for x in range(36, 76):                              # above the canoe's rim: the concept's snake, its smaller canoe and figure gone
        for y in range(0, int(RIM(x))):
            g.pop((x, y), None)
            c = c2.getpixel((x, y))
            if c[3] > 127:
                n = fold(c[:3], warm_ok=False)
                if y >= 32 and n in (WHITE, CREAM) and x < 42: n = DARK   # the concept's skull figure
                g[x, y] = n
    for x in range(44, 62):                              # the old wizard's robe, down inside the canoe
        for y in range(int(RIM(x)), 44):
            if g.get((x, y)) in (K, DARK, LIT) and y < 41: g[x, y] = WOOD_D
    g = flat(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    drawn = {}
    for r, row in enumerate(WIZARD):
        for c, ch in enumerate(row):
            if ch != '.': drawn[WIZARD_AT[0] + c, WIZARD_AT[1] + r] = LETTERS[ch]
    g.update(drawn)
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 2 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = DARK
    tidy_mod.KEEP = {WHITE, GLOW}
    tidy_mod.tidy(out)
    for (x, y), c in drawn.items(): out.putpixel((x + dx, y + dy), c + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
