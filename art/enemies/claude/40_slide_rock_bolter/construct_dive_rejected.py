"""40 Slide-Rock Bolter built by Claude as a GIANT, front view only, from its parts (the user, 2026-10-30: "giant
size and front facing only", "facing down more", after reference_user.png -- EvolutionsVoid's slate whale with
its hooked clawed tail, its gaping jaw full of teeth, its pink tongue and its dark mottled underside; shrinking
the drawing itself, giant.py, lost its line work). The great whale of the Catskills sliding down the mountain at
you: its head dived toward the player, jaws gaping, tongue out, its body rising behind in an S to the tail, which
hooks over the top with its two great yellow claws.

Drawn at native size on the giant frame (192x176, 98 Boiuna's front-only frame), each part a filled shape, then
the bible's rules (art/direction/approved_enemy_study/STYLE_BRIEF.md):
- the project's exact palette, one ramp a material: slate hide c6ccda / a4aaba / 848694, its underside 595965 /
  34343e, teeth e8e0c0, claws and eyes f0bc3c / c9a433, tongue fc74b4 / b6433d; black;
- light by form from the upper left on the hide (light under its up-facing edges, dark over its lower and far
  ones), its underside the far, shaded side of its body;
- shared separation lines between overlapping parts (head over body, jaw over jaw, tongue over teeth) and a closed
  one-pixel black outline;
- eyes one solid 2-px mark of the accent on the hide, no glint;
- chunky clusters, no texture, no specks; species detail in the silhouette (its ridged back, a knob line apart
  from the next) and a few strokes (its underside's dark patches, chunky, not a noise).

    python art/enemies/claude/40_slide_rock_bolter/construct.py
"""
from pathlib import Path
from collections import Counter
import math
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
W, H = 192, 176
HL, HM, HD = h('c6ccda'), h('a4aaba'), h('848694')
UL, UD = h('595965'), h('34343e')
TOOTH = h('e8e0c0')
CL, CD = h('f0bc3c'), h('c9a433')
TL, TD = h('fc74b4'), h('b6433d')
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

# Its parts drawn as ids on a part map first (separation lines go where ids meet), coloured after.
BODY, HEAD, MOUTH, TEETH_U, TEETH_L, TONGUE, CLAW, EYE, BLOW, RIDGE = range(1, 11)
ORDER = {BODY: 0, RIDGE: 0.5, HEAD: 1, CLAW: 1, MOUTH: 2, TEETH_U: 3, TEETH_L: 3, TONGUE: 4, EYE: 5, BLOW: 5}


def bezier(pts, n=60):
    k = len(pts) - 1
    return [(sum(math.comb(k, j) * (1 - t) ** (k - j) * t ** j * pts[j][0] for j in range(k + 1)),
             sum(math.comb(k, j) * (1 - t) ** (k - j) * t ** j * pts[j][1] for j in range(k + 1)))
            for t in (i / n for i in range(n + 1))]


def tube(draw, spine, w0, w1, part):
    """A body along the spine, w0 wide at its start to w1 at its end: discs along it."""
    for i, (x, y) in enumerate(spine):
        r = (w0 + (w1 - w0) * i / (len(spine) - 1)) / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=part)


def draw_parts():
    parts = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(parts)
    # its body: from behind its head, up and to the left, over to the right, to the tail's hook at the top
    tube(d, bezier([(96, 112), (58, 70), (70, 34), (118, 16), (138, 26)]), 58, 18, BODY)
    # its ridged back (the reference's ridged hump): knobs along the outer side of its curve, alternate ids so a
    # line parts each from the next
    spine = bezier([(96, 112), (58, 70), (70, 34), (118, 16), (138, 26)])
    for k, i in enumerate(range(8, 40, 6)):
        (x0, y0), (x1, y1) = spine[i - 1], spine[i + 1]
        tx, ty = x1 - x0, y1 - y0
        n = math.hypot(tx, ty) or 1
        nx, ny = ty / n, -tx / n                              # the outer side (left, then up)
        r = (58 + (18 - 58) * i / (len(spine) - 1)) / 2
        cx, cy = spine[i][0] + nx * (r - 1), spine[i][1] + ny * (r - 1)
        rr = 5 if k < 3 else 4
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=RIDGE if k % 2 else BODY)
    # the two claws hooked down from the tail's tip
    for cx in (132, 144):
        d.polygon([(cx - 4, 26), (cx + 4, 25), (cx + 3, 40), (cx - 1, 46), (cx - 1, 38)], fill=CLAW)
    # its head: a broad slate wedge, the snout dived toward us, wider than the body
    d.ellipse((50, 92, 142, 160), fill=HEAD)
    # the gaping mouth: a dark hole in its lower half, the lower jaw's lip below it
    d.ellipse((60, 122, 132, 170), fill=MOUTH)
    d.ellipse((58, 140, 134, 175), fill=HEAD)
    d.ellipse((66, 128, 126, 166), fill=MOUTH)
    # teeth: a row down from the upper jaw, a row up from the lower
    for x in range(66, 128, 6):
        top = 124 + int(10 * ((x - 96) / 34) ** 2)
        d.polygon([(x, top), (x + 4, top), (x + 2, top + 7)], fill=TEETH_U)
    for x in range(70, 124, 6):
        bot = 160 - int(6 * ((x - 96) / 30) ** 2)
        d.polygon([(x, bot), (x + 4, bot), (x + 2, bot - 6)], fill=TEETH_L)
    # the tongue lolling out over the lower jaw, toward us
    d.polygon([(88, 136), (106, 136), (110, 158), (104, 175), (92, 175), (86, 158)], fill=TONGUE)
    # eyes at the head's sides, above the jaw's corners; its blowhole on top
    for ex in (64, 126):
        d.rectangle((ex, 118, ex + 1, 118), fill=EYE)
    d.ellipse((90, 98, 102, 103), fill=BLOW)
    return parts


MOTTLE = [(104, 84, 2), (98, 66, 3), (96, 50, 2), (106, 36, 2), (112, 98, 2), (92, 76, 2)]


def colour(parts):
    P = parts.load()
    col = {BODY: HM, RIDGE: HM, HEAD: HM, MOUTH: K, TEETH_U: TOOTH, TEETH_L: TOOTH, TONGUE: TL, CLAW: CL, EYE: CL, BLOW: UD}
    im = Image.new('RGBA', (W, H))
    px = im.load()
    for y in range(H):
        for x in range(W):
            if P[x, y]: px[x, y] = col[P[x, y]] + (255,)

    same = {BODY: (BODY,), HEAD: (HEAD, EYE, BLOW), TONGUE: (TONGUE,), CLAW: (CLAW,), RIDGE: (RIDGE,)}

    def run(x, y, dx, dy, part):
        n = 0
        while 0 <= x + dx * (n + 1) < W and 0 <= y + dy * (n + 1) < H and P[x + dx * (n + 1), y + dy * (n + 1)] in same[part]:
            n += 1
        return n
    # light by form on the hide (body and head), the light from the upper left
    for part, top_band, bot_band in ((BODY, 3, 5), (HEAD, 3, 4), (RIDGE, 2, 2)):
        for y in range(H):
            for x in range(W):
                if P[x, y] != part: continue
                if run(x, y, 0, -1, part) < top_band or run(x, y, -1, 0, part) <= 1: px[x, y] = HL + (255,)
                elif run(x, y, 0, 1, part) < bot_band or run(x, y, 1, 0, part) <= 2: px[x, y] = HD + (255,)
    # its underside: the body's far (right) side the dark mottled hide, two steps, by how far across the tube
    for y in range(H):
        for x in range(W):
            if P[x, y] != BODY: continue
            lf, rt = run(x, y, -1, 0, BODY), run(x, y, 1, 0, BODY)
            frac = lf / max(1, lf + rt)
            edge = 0.62 + 0.06 * ((y // 3) % 2)                 # a jagged edge, steps of three rows
            if frac > edge: px[x, y] = UL + (255,)
            if frac > 0.86: px[x, y] = UD + (255,)
    for cx, cy, r in MOTTLE:                                      # chunky patches of its darkest step
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 1 and 0 <= x < W and 0 <= y < H and P[x, y] == BODY                         and px[x, y][:3] == UL:
                    px[x, y] = UD + (255,)
    # the tongue's and the claws' shade: their lower or right edge the dark step
    for y in range(H):
        for x in range(W):
            if P[x, y] == TONGUE and (y > 162 or run(x, y, 1, 0, TONGUE) <= 1): px[x, y] = TD + (255,)
            if P[x, y] == CLAW and run(x, y, 1, 0, CLAW) <= 1: px[x, y] = CD + (255,)
    return im, P


def lines(im, P):
    """Separation lines where parts meet (the part drawn later keeps its pixel; the other's goes black), the
    closed outline round everything, then no specks."""
    px = im.load()
    for y in range(H):
        for x in range(W):
            a = P[x, y]
            if not a or a in (MOUTH, EYE, BLOW): continue
            for dx, dy in N4:
                q = (x + dx, y + dy)
                if 0 <= q[0] < W and 0 <= q[1] < H:
                    b = P[q]
                    if b and b != a and b not in (EYE, BLOW) and ORDER[b] > ORDER[a]:
                        px[x, y] = K + (255,)
                        break
    for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]
                 and any(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] != K
                         for dx, dy in N4)]:
        px[x, y] = K + (255,)
    for x in range(W):
        if px[x, H - 1][3] and px[x, H - 1][:3] != K: px[x, H - 1] = K + (255,)
    for y in range(H):
        for x in range(W):
            c = px[x, y]
            if not c[3] or c[:3] in (K, CL): continue
            near = [px[x + dx, y + dy] for dx, dy in N8 if 0 <= x + dx < W and 0 <= y + dy < H]
            if any(n[3] and n[:3] == c[:3] for n in near): continue
            pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
            px[x, y] = (pick[0][0] if pick else K) + (255,)
    return im


if __name__ == '__main__':
    im, P = colour(draw_parts())
    im = lines(im, P)
    im.save(HERE / '40_giant_frame0.png')
    print(im.getbbox())
