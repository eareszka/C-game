"""40 Slide-Rock Bolter redrawn by Claude as a GIANT, front view only (the user, 2026-10-30: "have it be giant size
and front facing only; this is a good reference but it should be facing down more"; reference_user.png, the
user's find: EvolutionsVoid's Slide-Rock Bolter on DeviantArt). The great slate whale of the Catskills that
slides down the mountainside on the grease of its own slime, mouth agape, its tail hooked over the summit by
great claws: here diving straight down at the player, its jaws open, its hooked tail curled above.

No PixelLab (out of credits; the user: "make results on par with PixelLab, follow the bible to a tea"). Each
step a rule of art/direction/approved_enemy_study/STYLE_BRIEF.md:
1. The drawing cut from its white ground, turned ANGLE degrees so its snout points down at us, fitted to the
   giant frame (FRAME, as 98 Boiuna's front-only sheet) with padding, feet -- its jaw -- on the ground line.
2. The project's exact palette, one ramp a material (the giant tier's budget, the Physeter's nine-odd): its
   slate hide light/mid/dark, its dark mottled underside two steps, teeth, claws two steps (the eye shares
   their yellow), tongue two steps; near-blacks black. Colours by part, not nearest-only: pinks the tongue,
   yellows the claws and eye, the pale greys the hide.
3. No texture: the pencil hatching and the underside's mottling folded into flat clusters (patches of FEW
   pixels or fewer take the colour round them; teeth, eye and claw tips spared as drawn details), each pixel
   then the colour most of its neighbours share (a mode filter) -- chunky clusters, no noise.
4. One-pixel black outline, closed; no lone pixels.
Writes 40_giant_frame0.png. Interior black, eyes and anatomy are checked by bible_check.py and at review.

    python art/enemies/claude/40_slide_rock_bolter/giant.py
"""
from pathlib import Path
from collections import Counter
import colorsys
import sys
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
import fcremap

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
ANGLE = 40
FRAME = (192, 176)
FIT = (176, 168)
HIDE = [h('c6ccda'), h('a4aaba'), h('848694')]
UNDER = [h('595965'), h('34343e')]
TOOTH = h('e8e0c0')
CLAW = [h('f0bc3c'), h('c9a433')]
TONGUE = [h('fc74b4'), h('b6433d')]
KEEP = HIDE + UNDER + [TOOTH] + CLAW + TONGUE
SPARE = {TOOTH, CLAW[0], CLAW[1]}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def cut():
    im = Image.open(HERE / 'reference_user.png').convert('RGB')
    a = im.convert('L').point(lambda v: 255 if v < 225 else 0).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    rgba = im.convert('RGBA'); rgba.putalpha(a)
    rgba = rgba.rotate(ANGLE, expand=True, resample=Image.BICUBIC)
    return rgba.crop(rgba.getbbox())


def colour(p):
    hu, sa, va = colorsys.rgb_to_hsv(*(c / 255 for c in p))
    hu *= 360
    if va < 0.16: return (0, 0, 0)
    if sa > 0.3 and (hu >= 300 or hu <= 15): return TONGUE[0] if va > 0.7 else TONGUE[1]
    if sa > 0.35 and 30 <= hu <= 65: return CLAW[0] if va > 0.75 else CLAW[1]
    if sa < 0.12 and va > 0.8: return TOOTH
    return min(HIDE + UNDER, key=lambda k: fcremap.lab_dist(p, k))


def shrink(rg):
    s = min(FIT[0] / rg.width, FIT[1] / rg.height)
    sm = rg.resize((round(rg.width * s), round(rg.height * s)), Image.LANCZOS)
    out = Image.new('RGBA', FRAME)
    px = sm.load()
    for y in range(sm.height):
        for x in range(sm.width):
            p = px[x, y]
            if p[3] < 150: continue
            out.putpixel(((FRAME[0] - sm.width) // 2 + x, FRAME[1] - 1 - sm.height + y), colour(p[:3]) + (255,))
    return out


def flat(im, few=6):
    px, w, hh = im.load(), im.width, im.height
    for _ in range(3):
        seen = set()
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if (x, y) in seen or not c[3] or c[:3] == (0, 0, 0) or c[:3] in SPARE: continue
                comp, todo = [(x, y)], [(x, y)]; seen.add((x, y))
                while todo:
                    a, b = todo.pop()
                    for dx, dy in N4:
                        q = (a + dx, b + dy)
                        if 0 <= q[0] < w and 0 <= q[1] < hh and q not in seen and px[q] == c:
                            seen.add(q); comp.append(q); todo.append(q)
                if len(comp) > few: continue
                nb = Counter(px[q][:3] for a, b in comp for q in ((a + dx, b + dy) for dx, dy in N4)
                             if 0 <= q[0] < w and 0 <= q[1] < hh and px[q][3] and px[q] != c and px[q][:3] != (0, 0, 0))
                if nb:
                    for p in comp: px[p] = nb.most_common(1)[0][0] + (255,)
    return im


def mode(im, passes=2):
    px, w, hh = im.load(), im.width, im.height
    for _ in range(passes):
        new = {}
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if not c[3] or c[:3] == (0, 0, 0) or c[:3] in SPARE: continue
                n = Counter(px[x + dx, y + dy][:3] for dx, dy in N8 if 0 <= x + dx < w and 0 <= y + dy < hh
                            and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] != (0, 0, 0))
                top = n.most_common(1)
                if top and top[0][1] >= 5 and top[0][0] != c[:3]: new[x, y] = top[0][0]
        for p, c in new.items(): px[p] = c + (255,)
    return im


def outline(im):
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    for x, y in [(x, y) for y in range(hh) for x in range(w) if not px[x, y][3]
                 and any(at(x + dx, y + dy)[3] and at(x + dx, y + dy)[:3] != (0, 0, 0) for dx, dy in N4)]:
        px[x, y] = (0, 0, 0, 255)
    for x in range(w):
        if px[x, hh - 1][3] and px[x, hh - 1][:3] != (0, 0, 0): px[x, hh - 1] = (0, 0, 0, 255)
    return im


def lone(im):
    px, w, hh = im.load(), im.width, im.height
    for y in range(hh):
        for x in range(w):
            c = px[x, y]
            if not c[3] or c[:3] == (0, 0, 0): continue
            near = [px[x + dx, y + dy] for dx, dy in N8 if 0 <= x + dx < w and 0 <= y + dy < hh]
            if any(n[3] and n[:3] == c[:3] for n in near): continue
            pick = Counter(n[:3] for n in near if n[3] and n[:3] != (0, 0, 0)).most_common(1)
            px[x, y] = (pick[0][0] if pick else (0, 0, 0)) + (255,)
    return im


if __name__ == '__main__':
    im = lone(outline(mode(flat(shrink(cut())))))
    im.save(HERE / '40_giant_frame0.png')
    print(im.getbbox(), len({p[:3] for p in im.get_flattened_data() if p[3]}), 'colours with black')
