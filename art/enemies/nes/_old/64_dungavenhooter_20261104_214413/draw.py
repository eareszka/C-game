from pix import *

PAL = {
    'l': 'b29e5c',  # hide light
    'a': '7b601d',  # hide mid
    'd': '493712',  # hide dark
    'e': 'f0bc3c',  # amber eyes
    't': 'cebe82',  # claws, horns, throat plate
    'g': 'c6ccda',  # club light
    'h': '848694',  # club mid
    'i': '474751',  # club dark
}


def put(im, rows, x, y):
    """Paste a part in front, with a black line where it overlaps what is behind."""
    part = grid(rows, PAL)
    src, dst = part.load(), im.load()
    for py in range(-1, part.height + 1):
        for px in range(-1, part.width + 1):
            cx, cy = x + px, y + py
            if not (0 <= cx < im.width and 0 <= cy < im.height):
                continue
            inside = 0 <= px < part.width and 0 <= py < part.height
            if inside and src[px, py][3]:
                dst[cx, cy] = src[px, py]
                continue
            if dst[cx, cy][3] == 0:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                qx, qy = px + a, py + b
                if 0 <= qx < part.width and 0 <= qy < part.height and src[qx, qy][3]:
                    dst[cx, cy] = BLACK
                    break


TAIL = [
    '.............lllaaa......',
    '.........lllllaaaaaaa....',
    '......llllaaaaaaaaaaaaa..',
    '....lllaaaaaKaaaaKaaaaad.',
    'lllllaaaaaaKaaaaaaKaaadd.',
    'aaaaaaaaaaaaaddaaaaaaaadd',
    'aaaaaadddddd....ddaaaaadd',
    'dddddd...........daaaaadd',
    '..................aaKKadd',
    '..................aaaaadd',
    '..................aaaaadd',
    '.................aaaaaadd',
    '.................aKKaaadd',
    '................aaaaaaadd',
    '................aaaaaaadd',
    '...............aaKKaaadd.',
    '...............aaaaaaadd.',
    '..............aaaaaaadd..',
    '..............aaaaaadd...',
    '..............aaaaad.....',
]

BODY = [
    '.........l.....l.....l.....',
    '........ll....ll....ll...l.',
    '.......lla...lla...lla..la.',
    '......llaaa.llaaa.llaaalaa.',
    '.....laaaaaaaaaaaaaaaaaaaaa',
    '....lKKKKKKKKKKKKKKKKKKaaaa',
    '...llllllKllllllKlllllKaaad',
    '..laaaaaaKaaaaaaKaaaaaKaaad',
    '.laaaaaaaaaaaaaaaaaaaaaaaad',
    'aaaaKaaaaaaaKaaaaaaaKaaaadd',
    'aaaaaaaaaaaaaaaaaaaaaaaaadd',
    'aaaaaaaaaaaaaaaaaaaaaaaaddd',
    'dddddddddddddddddddddddddd.',
    '.dddddddddddddddddddddddd..',
    '..dddddddddddddddddddddd...',
]

FAR_LEG = [
    '.dddd.',
    '.ddddd',
    'ddddd.',
    't.t.t.',
]

FRONT_LEG = [
    '..llaaa..',
    '.llaaaad.',
    '.laaaaad.',
    '.laaaadd.',
    'laaaaaadd',
    'tt.tt.tt.',
]

REAR_LEG = [
    '..lllaaa.',
    '.llaaaaad',
    '.laaaaaad',
    '.laaaaadd',
    '..aaaaadd',
    '..aaaaadd',
    '.laaaaadd',
    'laaaaaadd',
    'tt.tt.tt.',
]

HEAD = [
    '....t.......t....',
    '....t.......t....',
    '...llll...llaa...',
    '..llKKKl.lKKKaa..',
    '.llKeeKlllKeeKaa.',
    'llaaaaaaKaKaaaaad',
    'laaaaaaaaaaaaaaad',
    '.laaaaaaaaaaaaad.',
    '..llaaaaaaaaadd..',
    '...llaaaaaaadd...',
    '....laaaaaaad....',
    '....laaaaaaad....',
    '....laaaaaaad....',
    '...llaaaaaaadd...',
    '...laKaaaKaaad...',
    '...laaaaaaaaad...',
    '....aaaaaaaad....',
    '.....ddddddd.....',
]

THROAT = [
    't.',
    'tt',
]

CLUB = [
    '........g........',
    '..g.....g.....h..',
    '...g...ggg...h...',
    '....hgggggghh....',
    '....ggggghhhh....',
    '...hgggghhhhhi...',
    '..hhggghhhhhhih..',
    'gggggghhhhhhhiihh',
    '..hhhhhhhhhhiii..',
    '...hhhhhhhhiiii..',
    '....hhhhhiiiii...',
    '....hhiiiiiii....',
    '...h...iii...h...',
    '..h.....h.....h..',
    '........h........',
]

im = canvas(52, 40)
put(im, TAIL, 20, 2)
put(im, FAR_LEG, 27, 29)
put(im, BODY, 12, 16)
put(im, REAR_LEG, 31, 24)
put(im, FRONT_LEG, 18, 27)
put(im, THROAT, 14, 25)
put(im, HEAD, 0, 15)
put(im, CLUB, 6, 0)
im = outline(im)
save(im)
