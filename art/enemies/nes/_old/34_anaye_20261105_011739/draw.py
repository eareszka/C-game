from pix import *
import math

K = '000000'
GD, GM, GL = '3b2a58', '595965', '848694'   # armour shadow, base, light
PD, PM, PL = '3b2a58', '664b95', 'b69cee'   # robe / axe
BN, BS = 'e8e0c0', 'b2966a'                 # bone, bone shade / gold
GR = '058f3a'

im = canvas(204, 150)
draw = ImageDraw.Draw(im)


def L(pts, c=K):
    draw.line(pts, fill=rgba(c), width=1)


def plate(pts, base=GM, li=GL, da=GD, lw=2, dw=3, edge=True):
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    m, px = mask.load(), im.load()
    W, H = im.size
    def on(x, y):
        return 0 <= x < W and 0 <= y < H and m[x, y]
    for y in range(H):
        for x in range(W):
            if not m[x, y]:
                continue
            c = base
            if dw and not on(x + dw, y + dw):
                c = da
            if lw and not on(x - lw, y - lw):
                c = li
            px[x, y] = rgba(c)
    if edge:
        draw.line(list(pts) + [pts[0]], fill=BLACK, width=1)


def M(pts):
    return [(230 - x, y) for x, y in pts]


def rivet(x, y, c=GL):
    # a 2 px stud with a black underside
    rect(im, x, y, 2, 2, c)
    L([(x, y + 2), (x + 2, y + 2), (x + 2, y)], GD)


def feather(tip, w, base=(115, 52)):
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    n = math.hypot(dx, dy)
    nx, ny = -dy / n, dx / n
    def P(t, s):
        return (round(bx + dx * t + nx * s), round(by + dy * t + ny * s))
    pts = [P(.3, -w * .3), P(.62, -w * .5), P(.84, -w * .36), P(1, 0), P(.84, w * .36), P(.62, w * .5), P(.3, w * .3)]
    plate(pts, BN, BN, BS, 0, 2)
    # tan root, quill and barb nicks
    poly(im, [P(.3, -w * .3), P(.5, -w * .42), P(.5, w * .42), P(.3, w * .3)], BS)
    L(pts + [pts[0]])
    L([P(.34, 0), P(.86, 0)])
    L([P(.5, -w * .42), P(.5, w * .42)])
    L([P(.66, 0), P(.76, -w * .42)])
    L([P(.66, 0), P(.76, w * .42)])


# ---------- axe blade ----------
blade = [(36, 0), (30, 6), (24, 6), (18, 12), (13, 13), (8, 20), (4, 24), (3, 31), (0, 36), (0, 46),
         (3, 52), (4, 59), (8, 64), (11, 72), (16, 76), (19, 84), (27, 93),
         (28, 82), (30, 74), (33, 66), (38, 58), (42, 50), (42, 24), (38, 20), (37, 12)]
poly(im, blade, PL)
# mid purple shard facets towards the shaft
poly(im, [(35, 5), (37, 12), (38, 20), (42, 24), (42, 50), (34, 62), (30, 72), (27, 86), (24, 68), (17, 62), (22, 50), (14, 41), (23, 33), (19, 22), (29, 19)], PM)
# dark core against the socket
poly(im, [(42, 22), (42, 50), (35, 58), (34, 47), (29, 41), (35, 33), (33, 25)], PD)
# light shard flecks in the mid tone
# long thin shards pointing back at the socket
poly(im, [(38, 35), (19, 30), (24, 37)], PL)
poly(im, [(38, 38), (20, 46), (26, 47)], PL)
poly(im, [(37, 24), (25, 10), (27, 20)], PL)
poly(im, [(35, 52), (22, 62), (27, 64)], PL)
# dark shards running out into the bright rim
poly(im, [(14, 41), (5, 34), (9, 42)], PD)
poly(im, [(19, 22), (10, 19), (15, 26)], PD)
poly(im, [(17, 62), (8, 58), (12, 65)], PD)
# facet lines, radiating from the socket to the rim
L([(14, 41), (0, 41)])
L([(14, 41), (23, 33), (19, 22), (29, 19), (35, 5)])
L([(14, 41), (22, 50), (17, 62), (24, 68), (27, 86)])
L([(19, 22), (13, 13)])
L([(17, 62), (4, 59)])
L([(23, 33), (3, 28)])
L([(22, 50), (3, 52)])
L([(24, 68), (11, 72)])
L([(29, 19), (24, 6)])
L([(22, 50), (34, 47)])
L([(29, 19), (38, 20)])
L(blade + [blade[0]])

# ---------- axe shaft ----------
plate([(47, 0), (51, 10), (50, 24), (43, 24), (42, 10)], GM, GL, GD, 1, 2)
L([(47, 4), (47, 20)])
plate([(44, 24), (50, 24), (50, 134), (44, 134)], GM, GL, GD, 1, 2)
for y in range(56, 132, 6):
    L([(44, y), (50, y)])
# socket with collars
plate([(39, 24), (55, 24), (57, 28), (55, 34), (39, 34), (37, 28)])
plate([(41, 34), (53, 34), (53, 42), (41, 42)])
plate([(38, 42), (55, 42), (58, 46), (55, 52), (39, 52), (36, 46)])
for y in (26, 44):
    L([(44, y), (44, y + 6)])
    L([(50, y), (50, y + 6)])
rivet(46, 37)
plate([(54, 35), (62, 38), (54, 41)], GM, GL, GD, 1, 1)
# pommel
plate([(44, 130), (50, 130), (54, 134), (54, 140), (50, 144), (44, 144), (40, 140), (40, 134)], GM, GL, GD, 2, 3)
rect(im, 45, 135, 3, 3, GL)
L([(40, 133), (54, 133)])

# ---------- right (viewer) arm: huge plated gauntlet ----------
plate([(152, 70), (176, 68), (182, 84), (174, 94), (156, 90)])
# claws, drawn behind the cuff
for f in ([(170, 116), (178, 116), (178, 130), (174, 139), (169, 133), (167, 124)],
          [(178, 118), (187, 118), (188, 133), (184, 144), (178, 135)],
          [(187, 116), (197, 114), (200, 127), (195, 141), (189, 134), (188, 125)]):
    plate(f, GM, GL, GD, 2, 2)
    L([(f[0][0] + 1, 125), (f[1][0] - 1, 125)])
for tip in ([(168, 130), (174, 139), (177, 130)], [(179, 134), (184, 144), (187, 134)], [(190, 132), (195, 141), (198, 131)]):
    poly(im, tip, BS)
    L(tip + [tip[0]])
# thumb
plate([(162, 106), (170, 106), (173, 116), (169, 130), (164, 126), (161, 116)], GM, GL, GD, 2, 2)
poly(im, [(165, 122), (169, 130), (171, 122)], BS)
L([(165, 122), (169, 130), (171, 122), (165, 122)])
# flared cuff
plate([(168, 96), (194, 94), (200, 108), (196, 120), (172, 120), (164, 110)])
L([(167, 108), (198, 106)])
for x in (172, 180, 188):
    rivet(x, 112)
    L([(x + 5, 109), (x + 5, 119)])
    rivet(x, 100)
# forearm and elbow bands, each stepped out from the one above
plate([(172, 78), (190, 74), (197, 88), (193, 98), (170, 98), (166, 90)])
plate([(170, 60), (186, 56), (193, 68), (190, 78), (172, 82), (164, 72)])
L([(170, 88), (195, 84)])
L([(168, 70), (192, 66)])
for x in (176, 184):
    rivet(x, 90 - (x - 172) // 4)
    rivet(x, 73 - (x - 172) // 4)
# outer elbow spike
plate([(191, 62), (199, 56), (195, 74)], GM, GL, GD, 1, 2)

# ---------- legs ----------
def leg(flip):
    t = M if flip else (lambda p: p)
    plate(t([(72, 92), (102, 92), (102, 110), (94, 120), (76, 120), (68, 108)]))
    # knee cop
    plate(t([(68, 110), (78, 103), (94, 103), (100, 112), (94, 124), (76, 124), (68, 118)]))
    # shin
    plate(t([(74, 122), (96, 122), (98, 136), (72, 136)]))
    for x in (80, 86, 92):
        L(t([(x, 126), (x, 134)]))
    # boot and toes
    plate(t([(68, 134), (100, 134), (104, 139), (104, 144), (60, 144), (62, 138)]), GM, GL, GD, 2, 2)
    for x in (70, 78, 86, 95):
        L(t([(x, 138), (x, 144)]))
    for x in (62, 72, 80, 89, 98):
        q = t([(x, 141), (x + 3, 141), (x + 3, 144), (x, 144)])
        poly(im, q, BS)
    # gold curl on the knee
    curl = [(73, 119), (73, 113), (77, 108), (87, 108), (93, 112), (93, 116), (89, 118), (85, 115)]
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        L(t([(x + dx, y + dy) for x, y in curl]), BS)


leg(False)
leg(True)

# ---------- spikes behind pauldrons and crest ----------
for s in ([(60, 46), (54, 26), (74, 38)], [(170, 46), (176, 26), (156, 38)]):
    plate(s, GM, GL, GD, 1, 2)

# ---------- crest ----------
for s in ([(108, 24), (115, 0), (122, 24)], [(90, 30), (86, 4), (102, 22)], [(140, 30), (144, 4), (128, 22)],
          [(78, 44), (62, 28), (88, 32)], [(152, 44), (168, 28), (142, 32)]):
    plate(s, GM, GL, GD, 1, 2)
L([(115, 5), (115, 22)])
for tip, w in (((70, 46), 13), ((160, 46), 13), ((72, 34), 14), ((158, 34), 14),
               ((78, 16), 14), ((152, 16), 14), ((95, 6), 14), ((135, 6), 14)):
    feather(tip, w)
feather((106, 10), 11)
feather((124, 10), 11)
feather((115, 8), 12)

# ---------- robe ----------
robe = [(88, 54), (142, 54), (150, 84), (148, 98), (138, 114), (115, 118), (92, 114), (82, 98), (80, 84)]
plate(robe, PM, PL, PD, 0, 4)
# fringe hanging between the legs
rows = ((100, 14), (104, 22), (108, 17), (112, 27), (116, 19), (120, 26), (124, 16), (128, 20))
for i, (x, n) in enumerate(rows):
    rect(im, x, 112, 3, n, PM if i % 3 else PD)
    rect(im, x + 3, 112, 1, n, K)
    rect(im, x, 112 + n - 3, 3, 3, PL if i % 3 == 1 else PD)
# fold lines and shadow pleats
for x0, y0, x1, y1 in ((85, 84, 86, 100), (91, 78, 92, 110), (145, 84, 144, 100), (139, 78, 138, 110)):
    L([(x0, y0), (x1, y1)])
    L([(x0 + 1, y0), (x1 + 1, y1)], PD)
for x0, x1 in ((94, 94), (136, 136)):
    L([(x0, 60), (x1, 84)], PD)
# bright hem steps at the robe's lower edge
for pts in ([(84, 98), (88, 106), (92, 112)], [(146, 98), (142, 106), (138, 112)]):
    L(pts, PL)
for x, y in ((87, 92), (95, 106), (133, 106), (141, 92)):
    rect(im, x, y, 2, 4, PD)

# ---------- breast plate ----------
plate([(100, 94), (130, 94), (136, 104), (130, 116), (100, 116), (94, 104)])
L([(115, 96), (115, 116)])
L([(97, 104), (133, 104)])
L([(100, 110), (130, 110)])
for x in (102, 108, 120, 126):
    rivet(x, 98)
    L([(x + 1, 111), (x + 1, 115)])

# ---------- left (viewer) arm reaching the shaft ----------
plate([(58, 72), (86, 78), (84, 96), (66, 106), (54, 100), (52, 84)])
L([(56, 84), (84, 90)])
L([(58, 92), (80, 98)])
L([(68, 76), (66, 86)])
for x, y in ((60, 87), (68, 89), (76, 91)):
    rivet(x, y)
# fist round the shaft
plate([(52, 90), (66, 92), (66, 110), (52, 112), (46, 104)], GM, GL, GD, 2, 2)
rivet(58, 100)
for y, x0 in ((88, 36), (94, 34), (100, 34), (106, 36)):
    plate([(x0 + 3, y), (54, y), (54, y + 6), (x0 + 3, y + 6), (x0, y + 3)], GM, GL, GD, 1, 2)
    poly(im, [(x0, y + 3), (x0 + 3, y + 1), (x0 + 3, y + 5)], BS)
    L([(x0 + 9, y + 1), (x0 + 9, y + 5)])
plate([(46, 80), (56, 82), (58, 90), (46, 90), (42, 86)], GM, GL, GD, 1, 2)

# ---------- pauldrons ----------
left = [(58, 46), (68, 38), (84, 38), (94, 46), (98, 60), (94, 74), (80, 82), (64, 80), (55, 68)]
right = M(left)
plate(left, GM, GL, GD, 3, 4)
plate(right, GM, GL, GD, 3, 4)
for side, f in ((left, False), (right, True)):
    t = M if f else (lambda p: p)
    # lower lame and rim
    L(t([(56, 64), (70, 70), (86, 70), (97, 62)]))
    L(t([(57, 70), (70, 76), (86, 76), (95, 70)]))
    for x, y in ((63, 71), (71, 73), (80, 73), (88, 69)):
        q = t([(x, y)])[0]
        rivet(q[0], q[1])
    # crown ridge
    L(t([(76, 39), (76, 69)]))
    for x, y in ((62, 56), (68, 45), (86, 48), (90, 60)):
        q = t([(x, y)])[0]
        rivet(q[0], q[1])
    # shard scratches and dented plate facets
    L(t([(66, 62), (72, 60), (73, 54)]), GD)
    L(t([(80, 44), (84, 54), (82, 62)]), GD)
    poly(im, t([(78, 42), (84, 42), (90, 48), (80, 50)]), GL)
    poly(im, t([(60, 60), (66, 64), (60, 66)]), GD)
    poly(im, t([(88, 62), (94, 56), (95, 62)]), GD)
    L(t([(58, 52), (66, 44)]), K)
# gold war marks: a large gash right, a small one left
for q in ([(146, 50), (152, 46), (156, 52), (153, 54), (158, 60), (152, 62), (150, 56), (146, 56)],
          [(66, 50), (72, 48), (74, 54), (70, 56), (68, 60), (64, 56)]):
    poly(im, q, BS)

# ---------- hood and cords ----------
hoodL = [(92, 44), (102, 40), (104, 62), (112, 78), (112, 94), (94, 82), (86, 64)]
plate(hoodL, PM, PL, PD, 1, 3)
plate(M(hoodL), PM, PL, PD, 1, 3)
L([(97, 48), (98, 62), (104, 76)], PD)
L([(133, 48), (132, 62), (126, 76)], PD)
L([(92, 56), (92, 66), (98, 78)], PD)
L([(138, 56), (138, 66), (132, 78)], PD)
# cords and collar loops
for r in range(0, 3):
    L([(92 + r * 2, 70 + r * 3), (104 + r, 86 + r * 2), (115, 92 + r * 2), (126 - r, 86 + r * 2), (138 - r * 2, 70 + r * 3)], K if r % 2 else PL)
# gem
gem = [(108, 84), (122, 84), (115, 97)]
plate(gem, GR, BN, PD, 1, 2)

# ---------- green band and mask ----------
cx, cy = 115, 58
for a in range(-168, -10, 18):
    ang1, ang2 = math.radians(a), math.radians(a + 15)
    r1, r2 = 16, 27
    q = [(round(cx + math.cos(ang1) * r1), round(cy + math.sin(ang1) * r1)),
         (round(cx + math.cos(ang1) * r2), round(cy + math.sin(ang1) * r2)),
         (round(cx + math.cos(ang2) * r2), round(cy + math.sin(ang2) * r2)),
         (round(cx + math.cos(ang2) * r1), round(cy + math.sin(ang2) * r1))]
    plate(q, GR, BN, GD, 1, 0)

mask = [(103, 44), (108, 39), (122, 39), (127, 44), (130, 52), (130, 60), (127, 68), (120, 75), (115, 79), (110, 75), (103, 68), (100, 60), (100, 52)]
plate(mask, BN, BN, BS, 0, 3)
# forehead and cheek lines
L([(115, 42), (115, 49)], BS)
L([(108, 44), (112, 47)], BS)
L([(122, 44), (118, 47)], BS)
L([(110, 66), (113, 70)], BS)
L([(120, 66), (117, 70)], BS)
L([(115, 62), (115, 67)], BS)
# slanted eye sockets, solid black, 2 px thick
for x0, x1 in ((104, 111), (126, 119)):
    L([(x0, 53), (x1, 57)])
    L([(x0, 54), (x1, 58)])
# mouth slit
L([(112, 72), (118, 72)])

# ---------- tidy: a black pixel on the silhouette would double the outline ----------
px = im.load()
W, H = im.size
changed = True
while changed:
    changed = False
    for y in range(H):
        for x in range(W):
            if px[x, y][3] and px[x, y][:3] == (0, 0, 0):
                if any(not (0 <= x + a < W and 0 <= y + b < H) or not px[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[x, y] = CLEAR
                    changed = True

im = outline(im)
save(im)
