from pix import *

WH, LT, MD, DK, IN = 'dcf0ff', 'dcf0ff', '84a7e9', '375a94', '37387b'
TG, RD, TH = 'ec8476', 'b6433d', '5d1e1f'

im = canvas(80, 70)


def seam(part, ymin=0):
    """Lay a part over the sprite with a 1 px black line where it crosses earlier parts."""
    pp, ip = part.load(), im.load()
    for y in range(part.height):
        for x in range(part.width):
            if not pp[x, y][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + a, y + b
                if yy >= ymin and 0 <= xx < im.width and 0 <= yy < im.height and not pp[xx, yy][3] and ip[xx, yy][3]:
                    ip[xx, yy] = BLACK
    im.alpha_composite(part)


def line(a, b, c=BLACK):
    ImageDraw.Draw(im).line([a, b], fill=rgba(c))


def limb(part, keys, lit, mid, dark, lit_w=1, dark_w=1):
    """Stepped limb from (y, left, right) keys, lit on the left, dark on the right."""
    for (y0, l0, r0), (y1, l1, r1) in zip(keys, keys[1:]):
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            l = round(l0 + (l1 - l0) * t)
            r = round(r0 + (r1 - r0) * t)
            rect(part, l, y, r - l + 1, 1, mid)
            if r - l >= 3:
                rect(part, l, y, lit_w, 1, lit)
            if r - l >= 2:
                rect(part, r - dark_w + 1, y, dark_w, 1, dark)


def foot_r(part, x, y, a=MD, b=DK):
    """Long toe running right, its tip curling back up."""
    stamp(part, grid(['aa.....a.',
                      'ab....ab.',
                      'ab....ab.',
                      'aab...ab.',
                      '.aaaaaab.',
                      '..bbbbb..'], {'a': a, 'b': b}), x, y)


def foot_l(part, x, y, a=MD, b=DK):
    """Long toe running left, its tip curling back up."""
    stamp(part, grid(['.a.....aa',
                      '.aa....ab',
                      '.aa....ab',
                      '.aa...aab',
                      '.aaaaaab.',
                      '..bbbbb..'], {'a': a, 'b': b}), x, y)


# far legs, in shade
p = canvas(80, 70)
limb(p, [(16, 21, 28), (26, 23, 28), (32, 25, 28), (38, 25, 27), (44, 22, 24), (50, 20, 22)], DK, DK, IN, 1, 2)
foot_r(p, 20, 50, DK, IN)
seam(p)
p = canvas(80, 70)
limb(p, [(18, 31, 37), (28, 32, 37), (34, 33, 36), (40, 32, 34), (46, 29, 31), (50, 27, 29)], DK, DK, IN, 1, 2)
foot_l(p, 21, 50, DK, IN)
seam(p)

# long hunched body: shaggy spine, with jagged edges between the three tones
p = canvas(80, 70)
poly(p, [(3, 18), (6, 11), (12, 6), (22, 3), (36, 3), (44, 6), (52, 11), (52, 24), (44, 26), (34, 23), (24, 21), (16, 24), (8, 27)], MD)
for x, y, w in ((8, 8, 5), (16, 4, 4), (23, 2, 6), (33, 2, 4), (40, 4, 5)):
    poly(p, [(x, y + 2), (x + w // 2, y), (x + w, y + 2)], LT)
for x, y in ((14, 24), (21, 22), (28, 21), (35, 23), (40, 25)):
    poly(p, [(x, y), (x + 4, y), (x + 1, y + 3)], DK)
poly(p, [(5, 14), (12, 7), (22, 4), (36, 4), (44, 7), (42, 9), (39, 7), (36, 10), (33, 7), (29, 10), (26, 7), (23, 10), (20, 8),
         (17, 12), (15, 9), (12, 14), (10, 12), (7, 18)], LT)
poly(p, [(16, 24), (15, 21), (18, 22), (21, 18), (24, 20), (28, 16), (31, 19), (35, 16), (37, 20), (41, 18), (43, 22), (46, 21), (46, 26), (34, 23), (24, 21)], DK)
seam(p)
# fur lines under the longest locks
for a, b in (((36, 14), (37, 17)), ((29, 14), (30, 16)), ((23, 14), (24, 17)), ((17, 16), (18, 20))):
    line(a, b)
line((41, 13), (43, 17))
line((32, 11), (32, 13), BLACK)
line((25, 11), (25, 12), BLACK)

# near rear leg, with a round haunch and a backward hock
p = canvas(80, 70)
limb(p, [(13, 7, 13), (16, 5, 16), (22, 4, 17), (27, 6, 15), (32, 8, 13), (37, 8, 11), (43, 6, 8), (50, 5, 7)], LT, MD, DK, 2, 2)
foot_l(p, 0, 50)
seam(p, 17)
line((9, 24), (12, 29))
line((12, 23), (14, 26))
rect(im, 8, 37, 3, 1, BLACK)

# near front leg, with an elbow
p = canvas(80, 70)
limb(p, [(20, 37, 47), (26, 37, 46), (32, 38, 44), (37, 39, 43), (43, 39, 42), (50, 38, 40)], LT, MD, DK, 1, 2)
foot_r(p, 38, 50)
seam(p, 25)
line((40, 28), (42, 32))
rect(im, 39, 37, 4, 1, BLACK)

# beard, wrapping the jaw and hanging in a shaggy curl
p = canvas(80, 70)
poly(p, [(66, 11), (69, 12), (68, 18), (70, 20), (68, 25), (69, 28), (67, 31), (67, 35), (63, 37), (62, 41), (58, 42), (56, 46), (53, 47),
         (52, 50), (55, 54), (58, 52), (60, 53), (59, 56), (53, 58), (49, 54), (47, 50), (49, 46), (45, 44), (47, 41), (44, 38), (56, 34), (64, 26)], IN)
seam(p)
for a, b in (((68, 14), (68, 17)), ((68, 22), (67, 26)), ((66, 30), (63, 34)), ((61, 36), (57, 39)), ((55, 40), (51, 42)), ((49, 48), (50, 53))):
    line(a, b, DK)
for a, b in (((67, 20), (66, 24)), ((64, 30), (61, 33)), ((56, 37), (52, 39)), ((52, 44), (50, 46))):
    line(a, b)

# head with the huge upturned jaw
p = canvas(80, 70)
poly(p, [(40, 13), (44, 9), (52, 8), (58, 11), (62, 10), (65, 3), (68, 3), (69, 10), (68, 22), (65, 30), (59, 37), (50, 39), (43, 35), (39, 27), (38, 19)], MD)
poly(p, [(40, 14), (44, 10), (52, 9), (56, 11), (46, 11), (42, 15), (41, 24), (39, 22)], LT)
poly(p, [(44, 35), (50, 36), (58, 34), (64, 28), (67, 20), (68, 22), (65, 30), (59, 37), (50, 39)], DK)
poly(p, [(65, 4), (67, 4), (67, 10), (66, 12)], LT)
seam(p)

# mouth
p = canvas(80, 70)
poly(p, [(45, 22), (50, 19), (58, 19), (62, 15), (65, 10), (66, 18), (63, 26), (58, 32), (50, 33), (46, 28)], TH)
poly(p, [(47, 27), (52, 25), (59, 26), (62, 23), (60, 30), (55, 32), (50, 32)], RD)
poly(p, [(49, 29), (53, 27), (58, 28), (57, 31), (51, 31)], TG)
seam(p)
rect(im, 52, 29, 4, 1, RD)
for x, y in ((48, 21), (51, 19), (55, 19), (59, 18), (62, 15)):
    rect(im, x, y, 2, 2, WH)
for x, y in ((47, 26), (65, 13), (64, 19), (62, 25)):
    rect(im, x, y, 1, 2, WH)
for x, y in ((51, 32), (55, 32)):
    rect(im, x, y - 1, 2, 1, WH)

# chin lines on the jaw
for x, y in ((45, 31), (48, 35), (53, 35), (60, 33)):
    rect(im, x, y, 2, 1, BLACK)

# eyes: solid 2 px marks on the lit brow
rect(im, 45, 12, 1, 2, BLACK)
rect(im, 53, 12, 1, 2, BLACK)

# stalk and fur ball
p = canvas(80, 70)
rect(p, 49, 3, 2, 6, DK)
seam(p)
p = canvas(80, 70)
stamp(p, grid(['..a.a..',
               '.aabaa.',
               'aabbbaa',
               '.bbbcb.',
               'aabccba',
               '.b.c.b.'], {'a': WH, 'b': MD, 'c': DK}), 46, 0)
seam(p)

im = outline(im)
save(im)
