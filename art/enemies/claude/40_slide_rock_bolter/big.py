"""40 Slide-Rock Bolter redone from scratch by Claude on the BIG frame (98x65, the cast's standard big cell), head
on, after the user's second reference (reference_user2.jpg, 2026-10-30: "big size but this type of big,
completely redo the sprite using the bible"): the great whale of the Catskills seen coming down the mountain at
you -- a broad blunt head filling the front, two glowing eyes under a heavy brow, a wide maw ringed with teeth
and black inside, the long body receding up behind the head in a curve, tapering to a snake's point (the user: no flipper), a line
of spines down its back. No PixelLab (out of credits).

Built as a part map (each part a filled shape, the parts overlapping in draw order), then the bible
(art/direction/approved_enemy_study/STYLE_BRIEF.md) applied part by part:
- the project's exact palette, eight colours plus black, one ramp a material: stone-grey hide bcbeca / 848694 /
  595965 (the Man-Eating Boulder's), green moss 4fa667 on it, teeth e8e0c0, eyes f0bc3c (an accent, one solid mark), mouth 7c0a1b deep in the throat, b6433d toward the lip (the cast's two reds: 49, 87);
- light by form from the upper left: each mass's upper-left plane lit, its lower and far side dark;
- shared separation lines where parts overlap (head over body, brow over eye, spines), the closed one-pixel
  outline;
- chunky clusters, no texture, no specks; interior black in the 9-14% band.
Writes big_frame0.png (its D view); bible_check.py checks it.

    python art/enemies/claude/40_slide_rock_bolter/big.py
"""
from pathlib import Path
from collections import Counter
import math
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
W, H = 98, 65
HL, HM, HD = h('bcbeca'), h('848694'), h('595965')      # stony rock (the user: "stony rock with moss"), the Boulder's greys on the palette
UD = h('595965')                                        # its underside and sockets share the dark step (eight colours)
MOSS_C = h('4fa667')                                    # the Boulder's moss, green on the grey
TOOTH, EYE_C, MOUTH_C, GUM = h('e8e0c0'), h('f0bc3c'), h('7c0a1b'), h('b6433d')
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

NONE, BODY, FLUKE, HEAD, BROW, MOUTH, TEETH, EYE, SPINE, LIP, SOCKET, MOSS, CRACK = range(13)
ORDER = {BODY: 0, SPINE: 1, FLUKE: 1, HEAD: 2, LIP: 3, MOUTH: 3, SOCKET: 3, TEETH: 4, BROW: 4, EYE: 5, MOSS: 6, CRACK: 7}


def bezier(pts, n=80):
    k = len(pts) - 1
    return [(sum(math.comb(k, j) * (1 - t) ** (k - j) * t ** j * pts[j][0] for j in range(k + 1)),
             sum(math.comb(k, j) * (1 - t) ** (k - j) * t ** j * pts[j][1] for j in range(k + 1)))
            for t in (i / n for i in range(n + 1))]


def ell_y(cx, cy, rx, ry, x, lower=False):
    """The y of an ellipse's edge at column x (its upper edge, or its lower)."""
    t = 1 - ((x - cx) / rx) ** 2
    if t < 0: return None
    return cy + (1 if lower else -1) * ry * math.sqrt(t)


def parts_map():
    P = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(P)
    # the body: from behind the head's crown up and right in a curve to the tail, narrowing as it recedes
    # (the user: "much longer and thicker to thin") -- as wide as the head's crown where it leaves it, an S up and
    # across the whole frame to a thin tail at the far right
    spine = bezier([(49, 44), (22, 33), (30, 11), (60, 9), (78, 20), (92, 14)], n=120)   # ending smoothly, a snake's tip
    for i, (x, y) in enumerate(spine):
        r = (36 - 33 * (i / len(spine)) ** 0.8) / 2
        d.ellipse((x - r, y - r, x + r, y + r), fill=BODY)
    # spines down its back: small spikes standing out from the body's outer (upper-left) edge
    for i in range(14, len(spine) - 16, 10):
        (x0, y0), (x1, y1) = spine[i - 2], spine[i + 2]
        tx, ty = x1 - x0, y1 - y0
        n = math.hypot(tx, ty) or 1
        nx, ny = ty / n, -tx / n                                  # outward: left/up of the travel
        r = (36 - 31 * (i / len(spine)) ** 0.8) / 2
        bx, by = spine[i][0] + nx * (r - 1), spine[i][1] + ny * (r - 1)
        d.polygon([(bx - 2 * (-ny), by - 2 * nx), (bx + 2 * (-ny), by + 2 * nx), (bx + 3 * nx, by + 3 * ny)], fill=SPINE)
    # the tail's flukes at the top, spread left and right
    # the head: a broad blunt dome, wide at the jaw, sitting on the ground line
    d.ellipse((15, 20, 83, 76), fill=HEAD)
    # the brow: two heavy eyebrow ridges, each low at the middle and rising outward (a scowl), two rows thick
    for x in range(26, 47):
        top = 37 - (x - 26) // 5
        d.rectangle((x, top, x, top + 1), fill=BROW)
    for x in range(52, 73):
        top = 33 + (x - 52) // 5
        d.rectangle((x, top, x, top + 1), fill=BROW)
    # eye sockets: a dark hollow under each brow, the glowing eye a 2-px mark in it
    for ex in (33, 60):
        d.rectangle((ex, 38, ex + 5, 41), fill=SOCKET)
    for ex in (34, 62):
        d.rectangle((ex, 39, ex + 1, 40), fill=EYE)
    # the maw: wide across the lower head, black inside; the lower lip a rim of hide under it
    d.ellipse((22, 42, 76, 66), fill=MOUTH)
    d.ellipse((26, 57, 72, 70), fill=LIP)
    # teeth: triangles hanging from the maw's upper edge and standing from the lip, following the curve
    for x in range(26, 71, 6):
        top = ell_y(49, 54, 27, 12, x + 2)
        if top is None: continue
        top = int(top) + 1
        d.polygon([(x, top), (x + 4, top), (x + 2, top + 5)], fill=TEETH)
    for x in range(29, 68, 6):
        bot = ell_y(49, 63.5, 23, 6.5, x + 2)
        if bot is None: continue
        bot = int(bot)
        d.polygon([(x, bot), (x + 4, bot), (x + 2, bot - 4)], fill=TEETH)
    # the Man-Eating Boulder's texture (the user): dark moss in ragged clumps over the crown and along the tail's
    # back, and black crevice lines across the stone -- short, angular, a few pixels, chunky not hatched
    T = Image.new('L', (W, H), 0)                                    # texture layer: kept only over the stone
    d = ImageDraw.Draw(T)
    for x0, w in ((22, 9), (34, 7), (44, 10), (58, 8), (69, 7)):
        for x in range(x0, x0 + w):
            top = ell_y(49, 48, 34, 28, x)
            if top is None or top > 31: continue                        # the crown only, not down the cheeks
            depth = 3 + ((x * 7) % 3)                                   # a ragged lower edge
            d.rectangle((x, int(top), x, int(top) + depth), fill=MOSS)
    for i0, i1 in ((6, 16), (24, 32), (42, 50), (60, 66)):               # moss clumps along the tail's back
        for i in range(i0, i1):
            (x0, y0), (x1, y1) = spine[i - 2], spine[i + 2]
            tx, ty = x1 - x0, y1 - y0
            n = math.hypot(tx, ty) or 1
            nx, ny = ty / n, -tx / n
            r = (36 - 33 * (i / len(spine)) ** 0.8) / 2
            depth = 3 + ((i * 5) % 3) - (1 if i in (i0, i1 - 1) else 0)   # ragged inner edge, thinner at the ends
            for k in range(1, depth + 1):
                bx, by = spine[i][0] + nx * (r - k), spine[i][1] + ny * (r - k)
                d.rectangle((int(bx), int(by), int(bx), int(by)), fill=MOSS)
    for pts in (((20, 50), (23, 53), (22, 57)), ((76, 50), (73, 54), (74, 58)), ((40, 27), (43, 30), (47, 29)),
                ((56, 26), (59, 24), (62, 27)), ((30, 44), (27, 48)), ((67, 44), (70, 48)),
                ((36, 20), (33, 23)), ((62, 16), (66, 18)), ((48, 12), (51, 14))):
        d.line(pts, fill=CRACK, width=1)
    pp, tt = P.load(), T.load()
    for y in range(H):
        for x in range(W):
            if tt[x, y] and pp[x, y] in (HEAD, BODY): pp[x, y] = tt[x, y]
    return P


def paint(P):
    px_ = P.load()
    g = {(x, y): px_[x, y] for y in range(H) for x in range(W) if px_[x, y]}
    im = Image.new('RGBA', (W, H))
    px = im.load()
    col = {BODY: HM, SPINE: HM, FLUKE: HM, HEAD: HM, LIP: HM, BROW: HD, SOCKET: UD, MOUTH: MOUTH_C, TEETH: TOOTH, EYE: EYE_C,
           MOSS: MOSS_C, CRACK: K}
    for p, c in g.items(): px[p] = col[c] + (255,)

    def run(x, y, dx, dy, parts):
        n = 0
        while g.get((x + dx * (n + 1), y + dy * (n + 1))) in parts: n += 1
        return n
    # light by form: each hide mass lit on its upper-left plane, dark on its lower and far side
    for p, c in g.items():
        x, y = p
        if c in (BODY, HEAD, FLUKE, SPINE, LIP):
            same = {BODY: (BODY, SPINE, MOSS, CRACK), HEAD: (HEAD, BROW, EYE, LIP, SOCKET, MOSS, CRACK), FLUKE: (FLUKE,), SPINE: (SPINE,), LIP: (LIP,)}[c]
            up, dn, lf, rt = run(x, y, 0, -1, same), run(x, y, 0, 1, same), run(x, y, -1, 0, same), run(x, y, 1, 0, same)
            v, u = up / max(1, up + dn), lf / max(1, lf + rt)
            if c == LIP: px[p] = (HD if dn < 2 else HM) + (255,)
            elif (v < 0.3 and u < 0.75) or lf < 2: px[p] = HL + (255,)
            elif v > 0.74 or rt < 2: px[p] = HD + (255,)
            if c == HEAD and y > 56 and dn < 4: px[p] = UD + (255,)         # its chin under the maw, in shadow
        elif c == MOUTH:
            up, dn = run(x, y, 0, -1, (MOUTH, TEETH)), run(x, y, 0, 1, (MOUTH, TEETH))
            if up / max(1, up + dn) > 0.45: px[p] = GUM + (255,)             # the mouth's lower half, toward the lip
            if c == BODY and dn < 3 and y > 8: px[p] = UD + (255,)           # the body's underside along its curve
    return im, g


def lines(im, g):
    """Separation lines where a part lies over another (the later-drawn keeps its pixel, the one under it goes
    black on the edge), the closed outline, no specks."""
    px = im.load()
    for (x, y), c in g.items():
        if c in (MOUTH, EYE, SOCKET, MOSS, CRACK): continue
        for dx, dy in N4:
            b = g.get((x + dx, y + dy))
            if b and b != c and b not in (EYE, SOCKET, MOSS, CRACK) and ORDER[b] > ORDER[c]:
                px[x, y] = K + (255,)
                break
    for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]
                 and any(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] != K
                         for dx, dy in N4)]:
        px[x, y] = K + (255,)
    for x in range(W):
        if px[x, H - 1][3] and px[x, H - 1][:3] != K: px[x, H - 1] = K + (255,)
    for _ in range(2):
        for y in range(H):
            for x in range(W):
                c = px[x, y]
                if not c[3] or c[:3] in (K, EYE_C): continue
                near = [px[x + dx, y + dy] for dx, dy in N8 if 0 <= x + dx < W and 0 <= y + dy < H]
                if any(n[3] and n[:3] == c[:3] for n in near): continue
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                px[x, y] = (pick[0][0] if pick else K) + (255,)
    return im


if __name__ == '__main__':
    im, g = paint(parts_map())
    im = lines(im, g)
    im.save(HERE / 'big_frame0.png')
    print(im.getbbox())
