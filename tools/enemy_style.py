"""The measurable half of the enemy bible, art/direction/SPRITE_STYLE.md.

    python tools/enemy_style.py ID [ID ...]            every sheet the game loads for that enemy
    python tools/enemy_style.py --anchors              the anchors, which should all come out clean
    python tools/enemy_style.py --queue                the restyle queue and where each one stands
    python tools/enemy_style.py FILE.png [--tier LOW]  a draft: one frame on a transparent ground
    python tools/enemy_style.py --board                rebuild the PixelLab style board

It reads frame 0 facing the player. FAIL breaks a hard rule (palette, alpha, colour count); WARN is a
number outside the range the approved sprites sit in, for a person to look at. It does not approve
anything: eyes, anatomy and whether the shade shapes follow the body still need looking at.
"""
import argparse
import json
import math
import os
import re
import sys

from PIL import Image

import enemy_tier_sheet as ets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'art', 'direction'))
import fcremap

# Replaced later on 2026-11-04 by NES style at every size (the user): see NES_ANCHORS and check_nes() below.
# These lists, QUEUE and check() describe the old rule and are kept for the record.
# The two styles every enemy is drawn in, as sorted in the audit of 2026-11-04 (the user: "ALL enemies
# from here on out will be a combination of B and C"). 42, 47 and 64 left these lists for the queue that day.
STYLE_B = [7, 16, 18, 21, 22, 25, 26, 28, 29, 32, 33, 36, 39, 40, 44, 56, 57, 58, 59, 60, 62, 69, 70,
           71, 72, 73, 74, 76, 77, 78, 82, 86, 88, 89, 91, 93, 94]
STYLE_C = [10, 17, 19, 20, 27, 35, 37, 38, 41, 45, 61, 67, 75, 79, 81, 83, 85, 87, 90, 92, 96]
ANCHORS = [29, 77, 93, 87, 92, 45]
# Bosses the user is keeping as they are, outside both styles.
KEPT_BOSSES = [6, 23, 30, 49, 52, 98, 100]
# Others the user is keeping as they are, outside both styles (2026-11-04).
KEPT = [12, 13, 31, 46, 63, 65, 99]
# Everything else, to be redrawn, in tier order. The user added 42 (it must get larger), 47 and 64.
QUEUE = [0, 1, 2, 3, 4, 5, 50, 53, 54, 55, 66, 68, 8, 9, 11, 14, 15, 24, 64, 80, 42, 43, 84, 47,
         48, 51, 95, 97, 34]
# The style image PixelLab gets: B and C sprites that come out clean here, with nothing left to fix.
# Left out by eye: 33 and 94 read as emblems, 21 as a diagram of a snake, 22 as chibi, and 81 is meant
# to be nearly invisible.
BOARD_IDS = [18, 25, 28, 29, 32, 36, 44, 57, 60, 62, 72, 77, 82, 86, 88, 89, 93,
             27, 45, 83, 87, 92]
BOARD_PATH = 'art/direction/approved_enemy_study/style_bc_native_512.png'
BOARD_SIDE = 512

# Drawn height by tier: (lowest, highest or None).
HEIGHT = {'STARTER': (30, 45), 'LOW': (30, 45), 'MEDIUM': (30, 60), 'UPPER': (30, 60), 'HARD': (35, 65),
          'SEVERE': (45, 80), 'ELITE': (50, None), 'BOSS1': (50, None), 'BOSS2': (50, None), 'BOSS3': (50, None)}
TONES = 3                         # shades of one colour
COLOURS = 9                       # 8 plus black
INTERIOR = (0.05, 0.15)           # share of drawn pixels that are black lines inside the outline
DOUBLED = 0.4                     # share of the second ring in that is black: a doubled outline
SOFT = 0.5                        # share of colour edges that are a small step in lightness
CLUMPS = 0.3                      # share of the fill in patches of 6 px or fewer
NEAR_BLACK_L, NEAR_BLACK = 17.5, 0.5   # that lightness and darker, over that share of the colour
DARKEST_MEAN_L = 25               # a body this dark on average is lost on the arena
BLACK_PART = 6                    # px of black with no colour beside it: gone on the black arena


def linear(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(rgb):
    r, g, b = (linear(c) for c in rgb)
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def sheets():
    """ENEMY_SHEETS in src/battle.cpp, one dict an enemy."""
    src = re.sub(r'//[^\n]*', '', ets.table('src/battle.cpp', 'ENEMY_SHEETS[] = {').split('{', 1)[1])
    entries, depth, cur = [], 0, ''
    for ch in src:
        if ch == '{':
            depth += 1
            if depth == 1:
                cur = ''
                continue
        if ch == '}':
            depth -= 1
            if depth == 0:
                entries.append(cur)
                continue
        if depth:
            cur += ch
    out = []
    for e in entries:
        vals, part, d = [], '', 0
        for ch in e:
            d += (ch == '{') - (ch == '}')
            if ch == ',' and d == 0:
                vals.append(part.strip())
                part = ''
            else:
                part += ch
        vals.append(part.strip())
        vals += [''] * 6
        name = lambda v: v.strip('"') if v.startswith('"') else None
        out.append(dict(path=name(vals[0]), frames=int(vals[2]) if vals[2] else 3, rows=vals[3] == 'true', flap=name(vals[4]), alt=name(vals[5])))
    return out


def tiers():
    return re.findall(r'T_([A-Z0-9]+)', ets.table('include/enemy.h', 'ENEMY_TIERS[] = {'))


def names():
    return re.findall(r'"([^"]+)"', ets.table('src/main.cpp', 'ENEMY_NAMES[] = {'))


def first_frame(path, frames=None, rows=False, cell_w=None):
    """Frame 0 facing the player, trimmed to what is drawn."""
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    if cell_w:                     # a flap sheet: the idle's cell width sets how many frames it has
        fw, fh = cell_w, (im.height // 8 if rows else im.height)
    elif frames:
        fw, fh = (im.width // frames, im.height // 8) if rows else (im.width // (8 * frames), im.height)
    else:
        fw, fh = im.size
    frame = im.crop((0, 0, fw, fh))
    return frame.crop(frame.getbbox() or (0, 0, fw, fh)), (fw, fh)


def blobs(cells):
    """4-connected patches of a set of (x, y)."""
    left, out = set(cells), []
    while left:
        stack = [left.pop()]
        patch = list(stack)
        while stack:
            x, y = stack.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in left:
                    left.remove(n)
                    stack.append(n)
                    patch.append(n)
        out.append(patch)
    return out


def measure(frame):
    w, h = frame.size
    px = frame.load()
    drawn = {(x, y): px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3]}
    partial = sum(1 for y in range(h) for x in range(w) if 0 < px[x, y][3] < 255)
    black = {p for p, c in drawn.items() if c == (0, 0, 0)}
    fill = {p: c for p, c in drawn.items() if c != (0, 0, 0)}
    n, nfill = max(1, len(drawn)), max(1, len(fill))
    by_colour = {}
    for p, c in fill.items():
        by_colour.setdefault(c, []).append(p)
    labs = {c: lab(c) for c in by_colour}

    # the outline and the ring inside it
    def rim(cells):
        return {(x, y) for x, y in cells if any(q not in cells for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))}
    edge = rim(set(drawn))
    inner = set(drawn) - edge
    second = rim(inner)
    interior = len(black - edge) / n
    doubled = len(second & black) / max(1, len(second))

    # black with no colour beside it, in any of the eight directions: nothing shows there on the arena
    lone = {(x, y) for x, y in black if not any((x + dx, y + dy) in fill for dx in (-1, 0, 1) for dy in (-1, 0, 1))}
    # A run on the outer edge lying along another black line is the outline gone thick. Anything else
    # is a part drawn only in black, or a socket: where it is tells which.
    parts, thick = [], []
    for b in blobs(lone):
        beside = sum(1 for x, y in b if any(q in black and q not in lone for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))))
        if all(p in edge for p in b) and beside >= 0.6 * len(b):
            thick.append(len(b))
        else:
            parts.append((len(b), min(x for x, y in b), min(y for x, y in b)))
    parts.sort(reverse=True)
    thick.sort(reverse=True)

    # shades of one colour: hue families, each colour counting from 2 % of the colour area
    families = {}
    for c, cells in by_colour.items():
        L, a, b = labs[c]
        hue = 'grey' if math.hypot(a, b) < 10 else int(((math.degrees(math.atan2(b, a)) + 360) % 360) // 40)
        if len(cells) / nfill >= 0.02:
            families.setdefault(hue, []).append(c)
    tones = max((len(v) for v in families.values()), default=0)

    # small steps of lightness between neighbouring colours read as soft, rendered shading
    steps = soft = 0
    for (x, y), c in fill.items():
        for q in ((x + 1, y), (x, y + 1)):
            d = fill.get(q)
            if d is not None and d != c:
                steps += 1
                soft += abs(labs[c][0] - labs[d][0]) < 12

    clumps = 0
    for c, cells in by_colour.items():
        clumps += sum(len(b) for b in blobs(cells) if len(b) <= 6)
    return dict(w=w, h=h, drawn=len(drawn), partial=partial, colours=len({*fill.values()}) + bool(black),
                off=sorted({'%02x%02x%02x' % c for c in drawn.values() if c not in fcremap.PALETTE}),
                interior=interior, doubled=doubled, black_parts=[p for p in parts if p[0] >= BLACK_PART],
                thick_edges=[t for t in thick if t >= BLACK_PART], tones=tones,
                soft=soft / max(1, steps), clumps=clumps / nfill,
                near_black=sum(len(v) for c, v in by_colour.items() if labs[c][0] < NEAR_BLACK_L) / nfill,
                mean_l=sum(labs[c][0] * len(v) for c, v in by_colour.items()) / nfill,
                saturation=sum(math.hypot(labs[c][1], labs[c][2]) * len(v) for c, v in by_colour.items()) / nfill)


def check(frame, tier=None):
    m = measure(frame)
    bad = []
    if m['off']:
        bad.append(('FAIL', 'off the palette: ' + ' '.join(m['off'][:8])))
    if m['partial']:
        bad.append(('FAIL', '%d half-transparent pixels' % m['partial']))
    if m['colours'] > COLOURS:
        bad.append(('FAIL', '%d colours, the limit is 8 plus black' % m['colours']))
    if m['tones'] > TONES:
        bad.append(('WARN', '%d shades of one colour, the limit is %d (materials sharing a hue count together)' % (m['tones'], TONES)))
    if not INTERIOR[0] <= m['interior'] <= INTERIOR[1]:
        bad.append(('WARN', '%.0f%% interior black, about %d to %d%% is right' % (m['interior'] * 100, INTERIOR[0] * 100, INTERIOR[1] * 100)))
    if m['doubled'] > DOUBLED:
        bad.append(('WARN', 'doubled outline'))
    if m['black_parts']:
        bad.append(('WARN', 'black-only parts vanish on the arena (fine for a skull socket): %s, measured from the top left of the drawing'
                    % ', '.join('%d px at %d,%d' % p for p in m['black_parts'][:6])))
    if m['thick_edges']:
        bad.append(('WARN', 'outer outline thicker than 1 px in places: runs of %s px' % ', '.join(map(str, m['thick_edges'][:6]))))
    if m['near_black'] > NEAR_BLACK:
        bad.append(('WARN', '%.0f%% of its colour is close to arena black' % (m['near_black'] * 100)))
    if m['mean_l'] < DARKEST_MEAN_L:
        bad.append(('WARN', 'too dark on average (lightness %.0f, the floor is %d)' % (m['mean_l'], DARKEST_MEAN_L)))
    if m['soft'] > SOFT:
        bad.append(('WARN', '%.0f%% of its colour edges are small soft steps' % (m['soft'] * 100)))
    if m['clumps'] > CLUMPS:
        bad.append(('WARN', '%.0f%% of its fill is in clumps of 6 px or fewer' % (m['clumps'] * 100)))
    if tier in HEIGHT:
        lo, hi = HEIGHT[tier]
        if m['h'] < lo or (hi and m['h'] > hi):
            bad.append(('WARN', '%d px tall, %s wants %d%s' % (m['h'], tier.title(), lo, ' to %d' % hi if hi else ' or more')))
    return m, bad


# ---- NES style at every size (the user, 2026-11-04): art/direction/SPRITE_STYLE.md. The limits are measured from these
# 26, which the user picked as what the game's enemies should look like.
NES_ANCHORS = [0, 1, 2, 3, 4, 5, 8, 9, 11, 14, 15, 21, 24, 26, 34, 42, 44, 50, 53, 54, 55, 66, 68, 78, 83, 95]
# Picks well under their tier's size: they keep their look and get drawn larger (the user, 2026-11-04).
# 34 left this list on 2026-11-05: the user kept the original at 101 px, over the 130 px redraw.
NES_RESIZE = [8, 9, 11, 14, 15, 21, 24, 42, 44, 78, 95]  # 95 added 2026-11-05: the user approved it larger, 110 px
TIER_NAMES = {'STARTER': 'Starter', 'LOW': 'Low', 'MEDIUM': 'Medium', 'UPPER': 'Upper', 'HARD': 'Hard', 'SEVERE': 'Severe',
              'ELITE': 'Elite', 'BOSS1': 'Boss 1', 'BOSS2': 'Boss 2', 'BOSS3': 'Boss 3'}
# Longer side, px. Each tier starts just above the one before it (the user, 2026-11-04).
NES_SIDE = {'STARTER': (20, 20), 'LOW': (21, 31), 'MEDIUM': (33, 44), 'UPPER': (45, 56), 'HARD': (57, 66), 'SEVERE': (67, 80),
            'ELITE': (81, 96), 'BOSS1': (100, 150), 'BOSS2': (160, 260), 'BOSS3': (280, 280)}
NES_COLOURS = 8                   # plus black
NES_TONES = 4                     # shades of one colour
NES_INTERIOR = (0.07, 0.16)       # black inside the outline, share of drawn pixels
NES_RIM = 0.65                    # share of the outer edge that is black
NES_DETAIL = (4.5, 40)              # patches of one colour per 100 px of fill: under this is smooth vector art, over it is noise
NES_SOFT = 0.5                    # share of colour edges that are a small step in lightness
NES_CLUMPS = {44: 0.5, 9999: 0.35}   # share of the fill in patches of 6 px or fewer, by longer side
# The tightened rule of 2026-11-05 (jobs with rule_version 2): big flat shapes, few lines, no copied patterns.
NES2_COLOURS = 5                  # plus black; a brief can raise it to 8
NES2_TONES = 2                    # base and one shadow
NES2_BIG = 45                     # rule_version 2 only: from this longer side up, a sprite may have as few inner lines as it likes.
                                  # Rule version 3 (closed parts, same day) asks for inner lines at every size, as the picks have.
NES2_REPEAT = 0.30                # share of detailed blocks repeated elsewhere. High on purpose: straight edges count too, so a plain flat sprite
                                  # (90, 0.22) outscored the brick one it replaced (0.18). It only catches the extreme: 6 at 0.58. Copying is for the eye.
NES2_REPEAT_FROM = 28             # under this a sprite is too small for repeats to mean a copied pattern


def enemy_hp():
    """Each enemy's HP from its class in src/enemies.cpp: the difficulty order within a tier. Missing ones are left out."""
    with open(os.path.join(ROOT, 'src', 'enemies.cpp'), encoding='utf-8') as f:
        src = f.read()
    out = {}
    for i, cls in re.findall(r'case (\d+): return new (\w+)\(\);', src):
        m = re.search(r'\b%s\(\)\s*:\s*Enemy\([^,]+,\s*[^,]+,\s*([0-9.]+)f?,' % cls, src)
        if m and float(m.group(1)) > 0:
            out[int(i)] = float(m.group(1))
    return out


def nes_lore():
    """tools/sprite_agent/lore_sizes.json: where each enemy falls in its tier's range, by its size in lore."""
    with open(os.path.join(ROOT, 'tools', 'sprite_agent', 'lore_sizes.json'), encoding='utf-8') as f:
        return {int(k): v for k, v in json.load(f).items() if k != '_'}


def nes_target(i):
    """(longer side, colours) for enemy i. Upper and up: its lore size places it in the tier's range. Below that: its HP rank does."""
    all_tiers = tiers()
    lo, hi = NES_SIDE[all_tiers[i]]
    lore = nes_lore().get(i)
    if lore:
        if 'side' in lore:              # a size the user set by hand: it overrides lore and the tier's range
            return lore['side'], NES_COLOURS
        side = int(round(lo + (hi - lo) * lore['pos']))
        assert lo * 0.9 <= side <= hi * 1.1, (i, side, 'more than 10% past its range')
        return side, NES_COLOURS
    hp = enemy_hp()
    known = sorted(hp.values())
    middle = known[len(known) // 2] if known else 0
    same = [j for j in range(len(all_tiers)) if all_tiers[j] == all_tiers[i]]
    tier_hp = sorted(hp[j] for j in same if j in hp)
    mine = hp.get(i, tier_hp[len(tier_hp) // 2] if tier_hp else middle)
    order = sorted(same, key=lambda j: (hp.get(j, mine if j == i else (tier_hp[len(tier_hp) // 2] if tier_hp else middle)), j))
    rank = order.index(i) / max(1, len(order) - 1)
    return int(round(lo + (hi - lo) * rank)), NES_COLOURS


def nes_tolerance(side):
    return max(2, int(round(side * 0.05)))      # tight enough that lore order survives within a narrow tier


def nes_loose_tolerance(side):
    return max(2, int(round(side * 0.1)))       # what Low and Medium, and jobs made before lore sizes, were drawn to


def nes_fits(i, longer):
    """Is a drawing with this longer side the right size for enemy i today? Low and Medium stay as drawn, so they keep the looser check."""
    side = nes_target(i)[0]
    return abs(longer - side) <= (nes_tolerance(side) if i in nes_lore() else nes_loose_tolerance(side))


def repeats(frame, size=5):
    """Share of detailed blocks (3 colours or more, counting black) that repeat exactly elsewhere without overlapping. A mirror image isn't a repeat."""
    px = frame.convert('RGBA').load()
    w, h = frame.size
    seen = {}
    for y in range(h - size + 1):
        for x in range(w - size + 1):
            block = tuple(px[x + a, y + b] if px[x + a, y + b][3] else None for b in range(size) for a in range(size))
            if len(set(block) - {None}) >= 3:
                seen.setdefault(block, []).append((x, y))
    total = copied = 0
    for places in seen.values():
        total += len(places)
        kept = []
        for p in places:
            if all(abs(p[0] - q[0]) >= size or abs(p[1] - q[1]) >= size for q in kept):
                kept.append(p)
                if len(kept) > 1:
                    copied += len(places)
                    break
    return copied / max(1, total)


def check_nes(frame, side=None, colours=NES_COLOURS, tolerance=None, strict=False):
    """[(FAIL or LOOK, text)] for a sprite against the NES rule. FAIL breaks it. LOOK is a number outside what the 26 picks do.
    strict is the tightened rule for jobs with rule_version 2."""
    m = measure(frame)
    px = frame.load()
    w, h = frame.size
    drawn = {(x, y) for y in range(h) for x in range(w) if px[x, y][3]}
    rim = [p for p in drawn if any(q not in drawn for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)))]
    rim_black = sum(px[p][:3] == (0, 0, 0) for p in rim) / max(1, len(rim))
    by = {}
    for p in drawn:
        if px[p][:3] != (0, 0, 0):
            by.setdefault(px[p][:3], []).append(p)
    fill = sum(len(v) for v in by.values())
    detail = 100 * sum(len(blobs(v)) for v in by.values()) / max(1, fill)
    longer = max(w, h)
    out = []
    if m['off']:
        out.append(('FAIL', 'off the palette: ' + ' '.join(m['off'][:8])))
    if m['partial']:
        out.append(('FAIL', '%d half-transparent pixels' % m['partial']))
    if len(by) > colours:
        out.append(('FAIL', '%d colours plus black, the limit is %d' % (len(by), colours)))
    allowed = nes_tolerance(side) if side and tolerance is None else tolerance
    if side and abs(longer - side) > allowed:
        out.append(('FAIL', 'longer side is %d px, it should be %d, within %d' % (longer, side, allowed)))
    if rim_black < NES_RIM:
        out.append(('LOOK', 'only %.0f%% of the outer edge is black' % (rim_black * 100)))
    tones = NES2_TONES if strict else NES_TONES
    if m['tones'] > tones:
        out.append(('LOOK', '%d shades of one colour, the limit is %d (materials sharing a hue count together)' % (m['tones'], tones)))
    if strict:
        if m['interior'] > NES_INTERIOR[1]:
            out.append(('LOOK', '%.0f%% black inside the outline, which is too many lines' % (m['interior'] * 100)))
        elif m['interior'] < NES_INTERIOR[0] and (strict == 3 or longer < NES2_BIG):
            out.append(('LOOK', '%.0f%% black inside the outline, the rule asks for about 9 to 14%%' % (m['interior'] * 100)))
        copied = repeats(frame) if longer >= NES2_REPEAT_FROM else 0
        if copied > NES2_REPEAT:
            out.append(('LOOK', '%.2f of its detailed 5x5 blocks repeat exactly elsewhere, which reads as a copied pattern (the limit is %.2f)' % (copied, NES2_REPEAT)))
    elif not NES_INTERIOR[0] <= m['interior'] <= NES_INTERIOR[1]:
        out.append(('LOOK', '%.0f%% black inside the outline, about 8 to 15%% is right' % (m['interior'] * 100)))
    if m['doubled'] > DOUBLED:
        out.append(('LOOK', 'doubled outline'))
    if m['thick_edges']:
        out.append(('LOOK', 'outer outline thicker than 1 px in places: runs of %s px' % ', '.join(map(str, m['thick_edges'][:6]))))
    if m['black_parts']:
        out.append(('LOOK', 'parts drawn only in black vanish on the arena (fine for a skull socket): %s, from the top left'
                    % ', '.join('%d px at %d,%d' % p for p in m['black_parts'][:6])))
    if m['near_black'] > NEAR_BLACK:
        out.append(('LOOK', '%.0f%% of its colour is close to arena black' % (m['near_black'] * 100)))
    if m['mean_l'] < DARKEST_MEAN_L:
        out.append(('LOOK', 'too dark on average (lightness %.0f, the floor is %d)' % (m['mean_l'], DARKEST_MEAN_L)))
    if m['soft'] > NES_SOFT:
        out.append(('LOOK', '%.0f%% of its colour edges are small soft steps' % (m['soft'] * 100)))
    limit = next(v for k, v in sorted(NES_CLUMPS.items()) if longer <= k)
    if m['clumps'] > limit:
        out.append(('LOOK', '%.0f%% of its fill is in patches of 6 px or fewer, which reads as noise at this size' % (m['clumps'] * 100)))
    if detail < NES_DETAIL[0] and not strict:
        out.append(('LOOK', 'too smooth: %.1f colour patches per 100 px, the picks have at least %d' % (detail, NES_DETAIL[0])))
    if detail > NES_DETAIL[1]:
        out.append(('LOOK', 'too noisy: %.1f colour patches per 100 px, the picks have at most %d' % (detail, NES_DETAIL[1])))
    return out


def report(label, frame, tier=None):
    m, bad = check(frame, tier)
    print('%-34s %3dx%-3d %d colours, %d shades, %2.0f%% lines   %s' % (
        label[:34], m['w'], m['h'], m['colours'], m['tones'], m['interior'] * 100, 'clean' if not bad else ''))
    for level, text in bad:
        print('    %s  %s' % (level, text))
    return bad


def report_id(i, all_sheets, all_tiers, all_names):
    s = all_sheets[i]
    frame, cell = first_frame(s['path'], s['frames'], s['rows'])
    bad = report('%d %s' % (i, all_names[i]), frame, all_tiers[i])
    if s['flap']:
        bad += report('  flap', first_frame(s['flap'], rows=s['rows'], cell_w=cell[0])[0])
    if s['alt']:
        bad += report('  alt', first_frame(s['alt'], s['frames'], s['rows'])[0])
    return bad


def build_board(all_sheets, all_names):
    """The style image: native pixels on transparent, nothing scaled, shelf-packed tallest first."""
    items = sorted(((i, first_frame(all_sheets[i]['path'], all_sheets[i]['frames'], all_sheets[i]['rows'])[0]) for i in BOARD_IDS),
                   key=lambda t: -t[1].height)
    board, placements = Image.new('RGBA', (BOARD_SIDE, BOARD_SIDE)), []
    x = y = shelf = 0
    for i, im in items:
        if x + im.width > BOARD_SIDE:
            x, y, shelf = 0, y + shelf + 2, 0
        assert y + im.height <= BOARD_SIDE, 'the board is full at %d' % i
        board.paste(im, (x, y))
        placements.append(dict(id=i, name=all_names[i], rect=[x, y, im.width, im.height]))
        x += im.width + 2
        shelf = max(shelf, im.height)
    path = os.path.join(ROOT, BOARD_PATH)
    board.save(path)
    with open(path.replace('.png', '.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(image=os.path.basename(path), native_pixels=True, placements=placements), f, indent=1)
    off = {c[:3] for _, c in board.getcolors(BOARD_SIDE * BOARD_SIDE) if c[3]} - set(fcremap.PALETTE)
    print('%s: %d sprites, used %d rows of %d, %s' % (BOARD_PATH, len(items), y + shelf, BOARD_SIDE, 'off palette: %s' % off if off else 'on the palette'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('what', nargs='*', help='enemy ids, or a PNG')
    ap.add_argument('--anchors', action='store_true')
    ap.add_argument('--queue', action='store_true')
    ap.add_argument('--board', action='store_true')
    ap.add_argument('--tier', help='the tier a draft is for: STARTER, LOW, MEDIUM, UPPER, HARD, SEVERE, ELITE, BOSS2')
    args = ap.parse_args()
    all_sheets, all_tiers, all_names = sheets(), tiers(), names()
    if args.board:
        build_board(all_sheets, all_names)
        return 0
    if args.queue:
        with open(os.path.join(ROOT, 'art', 'enemies', 'redraw_status.json'), encoding='utf-8') as f:
            done = set(json.load(f)['done'])
        left = [i for i in QUEUE if i not in done]
        print('%d of %d left, in order:' % (len(left), len(QUEUE)))
        for i in QUEUE:
            print('  %-4s %3d %s' % ('done' if i in done else '', i, all_names[i]))
        return 0
    failed = False
    for item in (ANCHORS if args.anchors else args.what):
        item = str(item)
        if item.isdigit():
            bad = report_id(int(item), all_sheets, all_tiers, all_names)
        else:
            bad = report(os.path.basename(item), first_frame(item)[0], args.tier)
        failed = failed or any(level == 'FAIL' for level, _ in bad)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
