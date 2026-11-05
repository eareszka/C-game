from pix import *

D = '2c6c44'; G = '4fa667'; L = 'a8f0bc'
Y = 'f4ce80'; S = 'c9a433'; B = '94703d'
R = 'b6433d'; O = 'fc9838'
PAL = {'D': D, 'G': G, 'L': L, 'Y': Y, 'S': S, 'B': B, 'R': R, 'O': O}

W, H, cx = 62, 60, 26
im = canvas(W, H)


def inline(part, x=0, y=0):
    """Stamp a part, with a 1 px black line wherever its edge crosses what is already drawn."""
    layer = canvas(W, H)
    stamp(layer, part, x, y)
    src, dst = layer.load(), im.load()
    for yy in range(H):
        for xx in range(W):
            if src[xx, yy][3] or not dst[xx, yy][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= xx + a < W and 0 <= yy + b < H and src[xx + a, yy + b][3]:
                    dst[xx, yy] = BLACK
                    break
    stamp(im, layer, 0, 0)


def leg(x0, y0, x1, y1, w0, w1, lit, shade):
    layer = canvas(W, H)
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        c = x0 + (x1 - x0) * t
        half = (w0 + (w1 - w0) * t) / 2
        a = int(c - half + 0.5)
        b = int(c + half + 0.5)
        rect(layer, a, y, max(b - a, 2), 1, lit)
        rect(layer, a + max(b - a, 2) - 1, y, 1, 1, shade)
    # splayed foot
    rect(layer, x1 - 2, y1 - 1, 5, 1, lit)
    rect(layer, x1 - 3, y1, 3, 1, lit)
    rect(layer, x1 + 1, y1, 3, 1, shade)
    inline(layer)


def tongue(x, y0, yf, kink, step):
    layer = canvas(W, H)
    rect(layer, x - step, y0, 2, kink - y0 + 1, R)
    rect(layer, x, kink, 2, yf - kink, R)
    rect(layer, x - 1, yf, 4, 1, R)
    rect(layer, x - 1, yf + 1, 1, 1, R)
    rect(layer, x + 2, yf + 1, 1, 1, R)
    rect(layer, x - 2, yf + 2, 1, 3, R)
    rect(layer, x + 3, yf + 2, 1, 3, R)
    inline(layer)


TAIL = grid([
    'GGGGGGGGG.......',
    'GGGGGGGGGGGG....',
    'DDDGGGGGGGGGGG..',
    '.....DDDDGGGGGG.',
    '.........DDGGGG.',
    '....GGGG...DGGGG',
    '..GGGGGGGG..DGGG',
    '..GGGDDGGG..DGGG',
    '.GGG...DGG..DGGG',
    '.GGG..GGD...DGGG',
    '.GGG..DD...GGGGD',
    '.DGGG.....GGGGD.',
    '..DGGGGGGGGGGD..',
    '...DDGGGGGGDD...',
    '.....DDDDDD.....',
], PAL)

BODY = grid([
    '....GGGGGGGGGGGGGGD....',
    '..GGGGGGGGGGGGGGGGGDD..',
    '.GGLLGGGGGGGGGGGGGGGDD.',
    'GGLLGGGGGGGGGGGGGGGGGDD',
    'GLLGKGGGLLLLLLLGGGKGGDD',
    'GLLGKGGLLLLLLLLLGGKGGDD',
    'GGGKGGGLLLLLLLLLGGGKGDD',
    'GGGKGGKKKKKKKKKKKGGKGDD',
    '.GGGGGGLLLLLLLLLGGGGDD.',
    '.DGGKGGGLLLLLLLGGGKGDD.',
    '..DDGGGGKKKKKKKGGGDDD..',
    '....DDDGGLLLGGGGDDD....',
    '......DDDDDDDDDDD......',
], PAL)

HEAD = grid([
    '.........LLLLLLGG........',
    '......GLLLLLLLLGGGG......',
    '....GGLLLLLLLLGGGGGGD....',
    '...GGLLLLLLGGGGGGGGGGD...',
    '..GGLLLLKKKGGGKKKGGGGDD..',
    '.GGLLLKKGGGGGGGGGKKGGDDD.',
    '.GGLLKGGGGGGGGGGGGGKGGDD.',
    'GGGLGGGGGDDGGGDDGGGGGGDDD',
    'GGGGGGDGGGGGGGGGGGDGGGDDD',
    'GGGGGDDGGGGGGGGGGGDDGGDDD',
    'KGGGGGDGGGGGGGGGGGDGGGDDK',
    'KKKGGGGGGGGGGGGGGGGGGDKKK',
    'DDKKKKGGGGGGGGGGGGGKKKKDD',
    'DDDDGKKKKKKKKKKKKKKKGDDDD',
    '.DDGGKKKKKKKKKKKKKKKGGDD.',
    '..DDGGGDGGGDGGGDGGGDDDD..',
    '....DDDDDDDDDDDDDDDDD....',
], PAL)

EYE = grid([
    '...LLL...',
    '..LLLLL..',
    '.LLLLLLG.',
    'LLLLLLLLG',
    'LLLLKLLGG',
    'LLLLKLLGG',
    'LLLLLLLGG',
    '.LLLLLGG.',
    '..LGGGD..',
    '...DDD...',
], PAL)

CREST = grid([
    '...O...',
    '...OO..',
    '..OOO..',
    '..OOOR.',
    '.OOORR.',
    '.OOORR.',
], PAL)

CAP = grid([
    '.GGGG.',
    'GLLGGD',
    'GLGGGD',
    'GGGGDD',
    '.DDDD.',
], PAL)

# tail, behind everything
tail = canvas(W, H)
rect(tail, cx + 9, 22, 7, 2, G)
rect(tail, cx + 9, 24, 7, 1, D)
stamp(tail, TAIL, cx + 16, 22)
inline(tail)

# rear stilts, behind the body
leg(cx - 8, 28, cx - 13, 59, 4, 2, S, B)
leg(cx + 8, 28, cx + 13, 59, 4, 2, S, B)

inline(BODY, cx - 11, 19)

# front stilts
leg(cx - 13, 23, cx - 22, 59, 5, 2, Y, S)
leg(cx + 13, 23, cx + 22, 59, 5, 2, Y, S)
inline(CAP, cx - 16, 21)
inline(CAP, cx + 10, 21)

inline(HEAD, cx - 12, 5)
inline(EYE, cx - 19, 9)
inline(EYE, cx + 11, 9)
inline(CREST, cx - 3, 0)

tongue(cx - 5, 18, 41, 31, -1)
tongue(cx + 4, 18, 49, 37, 1)

im = outline(im)
save(im)
