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
    """The old sprite's pose (the user: "this model but the original sprite pose" -- its first sheet's front view,
    assets/enemies/40_slide_rock_bolter.png): head on and squat, its mouth wide across its front, its tail standing
    straight up behind it and splitting at the top into two hooks curling out and down -- the hooks the reference's
    two great yellow claws, the tail ridged in plates as the reference's hump is."""
    parts = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(parts)
    # its tail, standing up behind its head: thick at its root, tapering, leaning a little; three broad plates
    # across it (alternate ids, so a line parts each from the next), as the reference's ridged hump
    spine = bezier([(96, 108), (94, 80), (99, 58), (96, 44)])
    for i, (x, y) in enumerate(spine):
        r = (34 + (16 - 34) * i / (len(spine) - 1)) / 2
        d.ellipse((x - r, y - r, x + r, y + r), fill=RIDGE if (int(y) // 12) % 2 else BODY)
    # the two claws hooked out and down from the tail's top, curling like the old flukes
    for sgn in (-1, 1):
        pts = [(96 + sgn * a, b) for a, b in ((3, 46), (8, 39), (16, 35), (25, 37), (30, 44), (30, 54), (26, 49),
                                               (20, 44), (12, 44), (6, 50))]
        d.polygon(pts, fill=CLAW)
    # its head: a broad, squat slate dome, sitting on the ground
    d.ellipse((38, 82, 154, 178), fill=HEAD)
    # the gaping mouth wide across its front, the lower jaw's lip below it
    d.ellipse((48, 124, 144, 170), fill=MOUTH)
    d.ellipse((50, 148, 142, 182), fill=HEAD)
    d.ellipse((56, 130, 136, 164), fill=MOUTH)
    # teeth: a row down from the upper jaw, a row up from the lower
    for x in range(56, 136, 6):
        top = 126 + int(12 * ((x + 2 - 96) / 42) ** 2)
        d.polygon([(x, top), (x + 4, top), (x + 2, top + 7)], fill=TEETH_U)
    for x in range(62, 130, 6):
        bot = 160 - int(8 * ((x + 2 - 96) / 36) ** 2)
        d.polygon([(x, bot), (x + 4, bot), (x + 2, bot - 6)], fill=TEETH_L)
    # the tongue lolling out over the lower jaw, toward us
    d.polygon([(87, 138), (105, 138), (110, 160), (104, 175), (92, 175), (86, 160)], fill=TONGUE)
    # eyes at the dome's sides, above the jaw's corners; its blowhole on top, in front of the tail
    for ex in (52, 138):
        d.rectangle((ex, 116, ex + 1, 116), fill=EYE)
    d.ellipse((88, 100, 104, 105), fill=BLOW)
    return parts


MOTTLE = [(142, 140, 3), (136, 156, 2), (146, 128, 2), (50, 150, 2), (130, 168, 2), (102, 64, 2)]


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
    for part, top_band, bot_band in ((BODY, 2, 2), (HEAD, 3, 4), (RIDGE, 2, 2)):
        for y in range(H):
            for x in range(W):
                if P[x, y] != part: continue
                if run(x, y, 0, -1, part) < top_band or run(x, y, -1, 0, part) <= 1: px[x, y] = HL + (255,)
                elif run(x, y, 0, 1, part) < bot_band or run(x, y, 1, 0, part) <= 2: px[x, y] = HD + (255,)
    # its underside: the body's far (right) side the dark mottled hide, two steps, by how far across the tube
    for y in range(H):
        for x in range(W):
            if P[x, y] == BODY or P[x, y] == RIDGE:              # the tail's far (right) side
                lf, rt = run(x, y, -1, 0, P[x, y]), run(x, y, 1, 0, P[x, y])
                if lf / max(1, lf + rt) > 0.7: px[x, y] = UL + (255,)
            elif P[x, y] == HEAD and (y > 136 + 2 * ((x // 6) % 2)) and (x > 132 - (y - 136) // 3 or x < 60 or y > 170):
                px[x, y] = (UD if (x > 144 or y > 173) else UL) + (255,)    # the dome's underside, mottled at its edge
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
