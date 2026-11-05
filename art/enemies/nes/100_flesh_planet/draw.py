from pix import *
import math, random

random.seed(100)

SK1, SK2, SK3 = 'f0b890', 'd7a175', '8d6b4f'   # skin: limbs and pale faces
FL1, FL2, FL3 = 'ec8476', 'b6433d', '792727'   # flesh: the globe and red faces
BLUE = '3e91cc'
K = '000000'

im = canvas(300, 300)
CX, CY, R = 150, 150, 108


def line(x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        dot(im, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def blob(x, y, d, c):
    d = max(1, round(d))
    x0, y0 = round(x - d / 2), round(y - d / 2)
    if d <= 2:
        rect(im, x0, y0, d, d, c)
    else:
        oval(im, x0, y0, d, d, c)


def samples(pts, step=1.0):
    out, total = [], 0.0
    for (a, b), (c, d) in zip(pts, pts[1:]):
        L = math.hypot(c - a, d - b)
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            out.append((a + (c - a) * t, b + (d - b) * t, math.atan2(d - b, c - a), total + L * t))
        total += L
    a, b = pts[-1]
    c, d = pts[-2]
    out.append((a, b, math.atan2(b - d, a - c), total))
    return out, total


def tube(pts, w0, w1, ramp, rings=0, ring_from=0.0):
    hi, main, sh = ramp
    ss, total = samples(pts)
    width = lambda d: w0 + (w1 - w0) * d / total
    for x, y, a, d in ss:
        blob(x, y, width(d), sh)
    for x, y, a, d in ss:
        w = width(d)
        blob(x - 1, y - 1, max(1, w - 2), main)
    for x, y, a, d in ss:
        w = width(d)
        if w >= 6:
            blob(x - w * .22, y - w * .22, max(1, w * .28), hi)
    if rings:
        gap = total / (rings + 1)
        for i in range(1, rings + 1):
            d0 = gap * i
            if d0 / total < ring_from:
                continue
            x, y, a, d = min(ss, key=lambda s: abs(s[3] - d0))
            w = width(d) / 2
            nx, ny = -math.sin(a), math.cos(a)
            line(round(x - nx * w), round(y - ny * w), round(x + nx * w), round(y + ny * w), K)


def hand(x, y, ang, s=1.0, ramp=(SK1, SK2, SK3)):
    """Palm and four chunky fingers. ang is the way the hand points."""
    fingers = [(-.72, 11), (-.26, 15), (.2, 16), (.66, 13)]
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    for k, (da, ln) in enumerate(fingers):
        off = (k - 1.5) * 4.2 * s
        fx, fy = x + px * off + ux * 5 * s, y + py * off + uy * 5 * s
        a = ang + da
        tube([(fx, fy), (fx + math.cos(a) * ln * s, fy + math.sin(a) * ln * s)], 6 * s, 5 * s, ramp)
    # thumb, set back on the palm
    a = ang - 1.55
    tx, ty = x - px * 7 * s - ux * 2 * s, y - py * 7 * s - uy * 2 * s
    tube([(tx, ty), (tx + math.cos(a) * 9 * s, ty + math.sin(a) * 9 * s)], 7 * s, 5 * s, ramp)
    blob(x, y, 19 * s, ramp[2])
    blob(x - 1, y - 1, 17 * s, ramp[1])
    blob(x - 3 * s, y - 3 * s, 7 * s, ramp[0])
    # knuckle creases, black lines between the finger roots
    for k in (-1, 0, 1):
        off = k * 4.2 * s
        a0, b0 = x + px * off + ux * 6 * s, y + py * off + uy * 6 * s
        line(round(a0), round(b0), round(a0 + ux * 5 * s), round(b0 + uy * 5 * s), K)
    # palm crease
    line(round(x - px * 5 * s), round(y - py * 5 * s), round(x + px * 3 * s + ux * 2), round(y + py * 3 * s + uy * 2), K)


SKIN = (SK1, SK2, SK3)
PINK = (FL1, FL2, FL3)


def arm(pts, w0, w1, ang=None, s=1.0):
    tube(pts, w0, w1, SKIN, rings=3, ring_from=.3)
    if ang is None:
        (a, b), (c, d) = pts[-2], pts[-1]
        ang = math.atan2(d - b, c - a)
    hand(pts[-1][0], pts[-1][1], ang, s)


def tendril(pts, w0, w1, rings=6):
    tube(pts, w0, w1, PINK, rings=rings)


# ---- limbs and tendrils, behind the globe ----
arm([(138, 62), (130, 40), (137, 28)], 15, 11, s=.8)
arm([(70, 92), (50, 80), (37, 73)], 16, 11, s=.85)
arm([(240, 122), (258, 118), (269, 106)], 16, 11, s=.85)
arm([(226, 214), (243, 233), (256, 237)], 15, 11, s=.8)
arm([(120, 248), (116, 268), (108, 274)], 15, 11, s=.75)
arm([(62, 214), (48, 229), (38, 233)], 14, 10, s=.75)

tendril([(204, 66), (222, 46), (240, 44), (250, 28), (264, 22)], 13, 3, 7)
tendril([(84, 66), (74, 46), (60, 40), (54, 24)], 12, 3, 6)
tendril([(176, 248), (182, 268), (198, 276), (214, 270)], 13, 3, 6)
tendril([(48, 150), (32, 156), (21, 148), (16, 158)], 12, 3, 6)
tendril([(252, 170), (268, 176), (278, 168), (283, 178)], 12, 3, 6)

# ---- the globe goes on its own layer, so its rim can be cut clean ----
limbs = im
im = canvas(300, 300)
LX, LY, LZ = -.55, -.6, .58
oval(im, CX - R - 6, CY - R - 6, R * 2 + 12, R * 2 + 12, FL3)
oval(im, CX - R - 3, CY - R - 3, R * 2 - 26, R * 2 - 26, FL2)

# ---- faces: big ones first, smaller ones fill the gaps, none sit on another ----
faces = []
for size, tries in ((.112, 6000), (.082, 9000), (.056, 12000), (.04, 16000)):
    for _ in range(tries):
        z = random.uniform(.1, 1)
        th = random.uniform(0, math.tau)
        rr = math.sqrt(1 - z * z)
        x, y = math.cos(th) * rr, math.sin(th) * rr
        s = size * random.uniform(.92, 1.08)
        if all((x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 > ((s + d) * .97) ** 2 for a, b, c, d in faces):
            faces.append((x, y, z, s))
faces.sort(key=lambda f: f[2])


def tpl(rows, cx, y, colours):
    x0 = cx - len(rows[0]) // 2
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.':
                dot(im, x0 + i, y + j, colours[ch])


MOUTH_BIG = [
    ['..KKK..', '.KKKKK.', 'KKKKKKK', 'KKKKKKK', 'KKsssKK', '.KsssK.', '..KKK..'],   # wail
    ['..KKK..', '.K...K.', 'K.....K'],                                               # frown
    ['KKKKKKKKK', 'KhKhKhKhK', 'KKKKKKKKK'],                                         # teeth
    ['KKKKKKK', '......K'],                                                          # flat
    ['.KKK.', 'KKKKK', 'KKKKK', '.KKK.'],                                            # gasp
    ['K.....K', '.KKKKK.'],                                                          # smile
    ['.KKKKKKK.', 'KhKKKKKhK', 'KKKsssKKK', '.KKsssKK.', '..KKKKK..'],               # howl
]
MOUTH_MID = [
    ['.KKK.', 'KKKKK', 'KKsKK', '.KKK.'],
    ['.KKK.', 'K...K'],
    ['KKKKK', 'KhKhK', 'KKKKK'],
    ['KKKKK'],
    ['.K.', 'KKK', '.K.'],
    ['K...K', '.KKK.'],
    ['KKKKK', 'KKsKK'],
]
MOUTH_SMALL = [['KKK', 'KKK'], ['.K.', 'K.K'], ['KKK'], ['KK'], ['K', 'K'], ['K.K', '.K.'], ['KKK', '.K.']]


pale_at = []


def face(nx, ny, nz, size):
    fx, fy = round(CX + nx * R), round(CY + ny * R)
    lit = nx * LX + ny * LY + nz * LZ + random.uniform(-.1, .1)
    base = 2 * size * R
    w = max(7, round(base * (.42 + .58 * math.sqrt(max(0, 1 - nx * nx)))))
    h = max(7, round(base * (.42 + .58 * math.sqrt(max(0, 1 - ny * ny)))))
    # pale faces are spread out, never in a clump
    # and none on the rim, where the cut would leave a stray tan chip
    pale = nz > .4 and random.random() < .3 and all((nx - a) ** 2 + (ny - b) ** 2 > .05 for a, b in pale_at)
    if pale:
        pale_at.append((nx, ny))
    if pale:
        main, sh, hi = (SK1, SK2, SK1) if lit > .55 else (SK2, SK3, SK1) if lit > .1 else (SK3, FL3, SK2)
    elif lit > .62:
        main, sh, hi = FL1, FL2, SK1
    elif lit > .12:
        main, sh, hi = FL2, FL3, FL1
    else:
        main, sh, hi = FL3, FL3, FL2
    dark = main in (FL3, SK3)
    eye = random.choice((BLUE, SK1, SK1)) if dark else K
    x0, y0 = fx - w // 2, fy - h // 2
    cx, cy = x0 + w // 2, y0 + h // 2
    # ears, behind the head
    if w >= 14:
        rect(im, x0 - 2, cy - 2, 3, 4, sh if sh != FL3 or main != FL3 else FL2)
        rect(im, x0 + w, cy - 2, 3, 4, sh if sh != FL3 or main != FL3 else FL2)
        dot(im, x0 - 2, cy + 2, K)
        rect(im, x0 + w + 2, cy - 1, 1, 3, K)
    # black line low and right, the crease that sets each head apart
    oval(im, x0, y0, w + 2, h + 2, K)
    oval(im, x0, y0, w + 1, h + 1, sh)
    oval(im, x0, y0, w, h, main)
    # a hard highlight on the upper left of the head
    if w >= 12:
        rect(im, x0 + w // 4, y0 + 2, max(2, w // 4), 1, hi)
        rect(im, x0 + w // 4 - 1, y0 + 3, 2, 2 if h >= 16 else 1, hi)
    col = {'K': K, 's': FL2 if main == FL3 else sh, 'h': hi}
    ex = max(1, round(w * .2))
    ey = cy - round(h * .1)
    kind = random.randrange(7)
    if h >= 17 and w >= 15:
        # brow fold and cheeks
        rect(im, cx - 2, y0 + 3, 5, 1, col['s'])
        rect(im, cx - ex - 3, ey + 4, 2, 1, col['s'])
        rect(im, cx + ex + 2, ey + 4, 2, 1, col['s'])
        # brows give each big face its mood
        if kind in (0, 6):      # wailing, brows up in the middle
            line(cx - ex - 2, ey - 3, cx - ex + 1, ey - 5, K)
            line(cx + ex + 2, ey - 3, cx + ex - 1, ey - 5, K)
        elif kind in (2, 3):    # angry, brows down in the middle
            line(cx - ex - 2, ey - 5, cx - ex + 1, ey - 3, K)
            line(cx + ex + 2, ey - 5, cx + ex - 1, ey - 3, K)
        else:                   # blank stare, flat brows
            rect(im, cx - ex - 1, ey - 3, 3, 1, K)
            rect(im, cx + ex - 1, ey - 3, 3, 1, K)
        rect(im, cx - ex, ey, 1, 2, eye)
        rect(im, cx + ex, ey, 1, 2, eye)
        rect(im, cx, ey + 2, 2, 1, col['s'])
        tpl(MOUTH_BIG[kind], cx, ey + 4, col)
        if random.random() < .22:
            rect(im, cx - ex, ey + 3, 1, 4, BLUE)
    elif h >= 11 and w >= 10:
        rect(im, cx - ex, ey, 1, 2, eye)
        rect(im, cx + ex, ey, 1, 2, eye)
        if kind in (2, 3):
            line(cx - ex - 1, ey - 3, cx - ex + 1, ey - 2, K)
            line(cx + ex + 1, ey - 3, cx + ex - 1, ey - 2, K)
        tpl(MOUTH_MID[kind], cx, ey + 3, col)
    else:
        dot(im, cx - ex, ey, eye)
        dot(im, cx + ex, ey, eye)
        tpl(MOUTH_SMALL[kind], cx, ey + 2, col)


for f in faces:
    face(*f)

# cut the rim: round overall, with short lumpy steps, not one long curve
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        dx, dy = x - CX, y - CY
        a = math.atan2(dy, dx)
        edge = R + 1 + round(2 * math.sin(a * 13) + 1.5 * math.sin(a * 29 + 1))
        if dx * dx + dy * dy > edge * edge:
            px[x, y] = (0, 0, 0, 0)

# creases that reach the rim would thicken the outline: take them back to the fill
while True:
    before = im.tobytes()
    im = strip_outline(im)
    if im.tobytes() == before:
        break

stamp(limbs, im, 0, 0)
im = outline(limbs)
save(im)
