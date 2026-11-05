"""40 Slide-Rock Bolter's battle sheet brought to the enemy bible by Claude, with no PixelLab (the user, 2026-10-30:
"make results on par with PixelLab, follow the bible to a tea"; PixelLab's credits were spent). Its design, its
eight drawn directions and its five idle frames are kept (assets/enemies/40_slide_rock_bolter.png: 98x65 cells,
the game's big frame); every cell is redrawn by these steps, each one a rule of
art/direction/approved_enemy_study/STYLE_BRIEF.md:

1. The project's exact palette, eight colours plus black -- one dark/mid/light ramp a material: its stone-grey
   hide (595965 / 848694 / a4aaba, the palette's grey-blue ramp), its pale belly and flukes (cebe82 / e8e0c0),
   its mouth (280e10 / 792727), its eye's accent (f0bc3c). Its two near creams fold into one step.
2. No texture: the old hide was a lattice of single dark flecks ("no dithering, hatching, scale lattices or
   repeated skin textures"); a patch of one colour of four pixels or fewer takes the colour round it, the eye
   spared. Its 1-px lit edge and its shade band, long runs, stay: light by form, not by band.
   Then form(): its hide re-lit by form, from the upper left (light under up-facing edges, dark over the lower
   and far ones), and parts(): a black line where hide meets belly or fluke.
3. One-pixel black outline, closed: an empty pixel touching colour goes black.
4. Interior black separation lines in the bible's 9-14.5% band: measured, then raised where low by blacking the
   dark step of the hide where it borders the mid (the line between body masses) -- never by thickening the
   outline.
5. Eyes: one solid mark of 1-2 px, the accent on the dark hide.
Then every frame checked (bible_check, as for the PixelLab enemies) and the sheet written beside this script as
40_slide_rock_bolter.png for review; nothing installed.

    python art/enemies/claude/40_slide_rock_bolter/restyle.py
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
SRC = ROOT / 'assets/enemies/40_slide_rock_bolter.png'
W, H, FRAMES = 98, 65, 5
MAP = {'7c8494': '848694', '4c5464': '595965', 'a8b0bc': 'a4aaba',          # hide: mid, dark, light
       'f0e8d8': 'e8e0c0', 'c8c0b0': 'cebe82', 'b8b098': 'cebe82',          # belly and flukes: light, mid
       '2c1418': '280e10', '8c3c44': '792727',                              # mouth: dark, mid
       'f0d040': 'f0bc3c', '000000': '000000'}                              # eye accent; black
EYE = h('f0bc3c')
HIDE_D, HIDE_M = h('595965'), h('848694')
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def palette(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            px[x, y] = (h(MAP['%02x%02x%02x' % p[:3]]) + (255,)) if p[3] >= 128 else (0, 0, 0, 0)
    return im


def untexture(im, most=4):
    px, w, hh = im.load(), im.width, im.height
    for _ in range(3):
        seen = set()
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if (x, y) in seen or not c[3] or c[:3] in ((0, 0, 0), EYE): continue
                comp, todo = [(x, y)], [(x, y)]; seen.add((x, y))
                while todo:
                    a, b = todo.pop()
                    for dx, dy in N4:
                        q = (a + dx, b + dy)
                        if 0 <= q[0] < w and 0 <= q[1] < hh and q not in seen and px[q] == c:
                            seen.add(q); comp.append(q); todo.append(q)
                if len(comp) > most: continue
                nb = Counter(px[q][:3] for a, b in comp for q in ((a + dx, b + dy) for dx, dy in N4)
                             if 0 <= q[0] < w and 0 <= q[1] < hh and px[q][3] and px[q] != c and px[q][:3] != (0, 0, 0))
                if nb:
                    for p in comp: px[p] = nb.most_common(1)[0][0] + (255,)
    return im


HIDE_L = h('a4aaba')
BELLY = {h('e8e0c0'), h('cebe82')}


def form(im):
    """Light by form, the light from the upper left ("light on viewer/up-facing surfaces, dark under overhangs and
    on far surfaces"), redone on its hide after the texture is gone: each hide pixel measured to the hide's edge
    up, down, left and right; the three pixels under an upper edge and the one inside a left edge the light step,
    the four over a lower edge and the one inside a right edge the dark step, the rest the mid. It follows each
    mass's own outline -- the tail, the back, the flipper -- so it is form, not a band across the sprite."""
    px, w, hh = im.load(), im.width, im.height
    hide = {HIDE_D, HIDE_M, HIDE_L}
    isin = lambda x, y: 0 <= x < w and 0 <= y < hh and px[x, y][3] and px[x, y][:3] in hide
    def run(x, y, dx, dy):
        n = 0
        while isin(x + dx * (n + 1), y + dy * (n + 1)): n += 1
        return n
    new = {}
    for y in range(hh):
        for x in range(w):
            if not isin(x, y): continue
            up, down, left, right = run(x, y, 0, -1), run(x, y, 0, 1), run(x, y, -1, 0), run(x, y, 1, 0)
            if up <= 2 or (left == 0 and up <= 6): new[x, y] = HIDE_L
            elif down <= 3 or right == 0: new[x, y] = HIDE_D
            else: new[x, y] = HIDE_M
    for p, c in new.items(): px[p] = c + (255,)
    return im


def parts(im):
    """Shared separation lines between overlapping parts: where its hide meets its pale belly or flukes, the
    hide's pixel on the line goes black (the line the old drawing had between its back and its underside)."""
    px, w, hh = im.load(), im.width, im.height
    hide = {HIDE_D, HIDE_M, HIDE_L}
    line = [(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] in hide
            and any(0 <= x + dx < w and 0 <= y + dy < hh and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in BELLY
                    for dx, dy in N4)]
    for p in line: px[p] = (0, 0, 0, 255)
    return im


N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def lone(im):
    """No specks: a pixel with none of its colour among its eight neighbours takes their most common colour (not
    black), the eye and the mouth's dark spared (their drawn details); one with only black round it goes black."""
    px, w, hh = im.load(), im.width, im.height
    keep = {EYE}
    for _ in range(2):
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if not c[3] or c[:3] == (0, 0, 0) or c[:3] in keep: continue
                near = [px[x + dx, y + dy] for dx, dy in N8 if 0 <= x + dx < w and 0 <= y + dy < hh]
                if any(n[3] and n[:3] == c[:3] for n in near): continue
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != (0, 0, 0)).most_common(1)
                px[x, y] = (pick[0][0] if pick else (0, 0, 0)) + (255,)
    return im


def outline(im):
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    for x, y in [(x, y) for y in range(hh) for x in range(w) if not px[x, y][3]
                 and any(at(x + dx, y + dy)[3] and at(x + dx, y + dy)[:3] != (0, 0, 0) for dx, dy in N4)]:
        px[x, y] = (0, 0, 0, 255)
    for x in range(w):                                   # colour on the last row: the outline's place
        if px[x, hh - 1][3] and px[x, hh - 1][:3] != (0, 0, 0): px[x, hh - 1] = (0, 0, 0, 255)
    return im


def interior(im):
    px, w, hh = im.load(), im.width, im.height
    edge = lambda x, y: any(not (0 <= x + dx < w and 0 <= y + dy < hh) or not px[x + dx, y + dy][3] for dx, dy in N4)
    drawn = [(x, y) for y in range(hh) for x in range(w) if px[x, y][3]]
    return sum(1 for x, y in drawn if px[x, y][:3] == (0, 0, 0) and not edge(x, y)) / max(1, len(drawn))


def seams(im, want=0.095):
    """Raise interior black to the band where low: the dark hide step's pixels that border the mid step (the
    line between body masses -- under the neck, the far flipper, the tail's root) go black, one at a time in
    reading order, until the share is in the band."""
    px, w, hh = im.load(), im.width, im.height
    if interior(im) >= want: return im
    cand = [(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] == HIDE_D
            and any(0 <= x + dx < w and 0 <= y + dy < hh and px[x + dx, y + dy][:3] == HIDE_M and px[x + dx, y + dy][3]
                    for dx, dy in N4)]
    total = sum(1 for y in range(hh) for x in range(w) if px[x, y][3])
    need = int((want - interior(im)) * total) + 1
    for p in cand[:need]: px[p] = (0, 0, 0, 255)
    return im


if __name__ == '__main__':
    old = Image.open(SRC).convert('RGBA')
    out = Image.new('RGBA', old.size)
    for i in range(old.width // W):
        c = old.crop((i * W, 0, i * W + W, H))
        out.paste(outline(lone(parts(form(untexture(palette(c)))))), (i * W, 0))
    out.save(HERE / '40_slide_rock_bolter.png')
    for i in range(0, old.width // W, FRAMES):
        out.crop((i * W, 0, i * W + W, H)).save(HERE / f'check_{i // FRAMES}.png')
    print('written', out.size, len({p[:3] for p in out.get_flattened_data() if p[3]}), 'colours with black')
