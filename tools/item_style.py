"""The item style bible's measurable half (art/direction/ITEM_STYLE.md): the
ramps the item and weapon icons are coloured in, the icons, and the checker.

    python tools/item_style.py                   # every icon: PASS/FAIL a rule, a row an icon
    python tools/item_style.py wood knife        # some
    python tools/item_style.py --measure         # the figures the thresholds are set from
    python tools/item_style.py --board out.png   # the icons side by side, their verdicts under them

Measured from the icons the user is happy with (REFERENCE). The palette rule,
the board and the silhouette figures are taken from tools/interior_style.py
and tools/overworld_style.py; the ramps and the drawings' own colours from
the scripts that make the sheets (art/items/, gen_cave_entrances.py).
"""
import os, re, sys
import interior_style, overworld_style
from interior_style import ROOT

for p in ('art/items', 'art/structures'):
    sys.path.insert(0, os.path.join(ROOT, p))
from gen_cave_entrances import TONES
from gen_items import COLUMNS
import items_design, weapons_design

hexes = lambda rgbs: tuple('%02x%02x%02x' % tuple(c) for c in rgbs)
WHITE = 'fcfcfc'        # an accent any icon may carry: a page, a glint

# A ramp, lit to dark: the seven ores' (line, shade, base, lit in
# gen_cave_entrances.py -- the caves', the cliffs' and the shots' own) and the
# cliffs' brown. The stone that is mined is the overworld's 'ore rock'.
RAMPS = {{'stone': 'ore rock'}.get(name, name): hexes(reversed(t[1:])) for name, t in TONES}
RAMPS['cliff rock'] = overworld_style.MATERIALS['cliff rock']['tones']
# What a drawing carries that its ramp does not swap: an item's stems and
# leaves, a weapon's haft and the katana's grip wrap.
STEM = tuple(items_design.PAL[k] for k in 'lbs')
HAFT = tuple(weapons_design.PAL[k] for k in 'uvwk')

ITEMS = [n.lower() for n in re.findall(r'ITEM_(\w+)', re.search(
    r'enum Item \{(.*?)ITEM_COUNT', open(os.path.join(ROOT, 'include', 'crafting.h'), encoding='utf-8').read(), re.S).group(1))]
assert len(ITEMS) == len(COLUMNS), 'enum Item and gen_items.COLUMNS disagree'
RETIRED = ('gravestone',)   # no longer an item (the user, 2026-10-12): its column is still in the sheet

# icon: (its sheet, its column, its ramp -- None for one coloured in tones of
# its own -- and the fixed colours its drawing may carry). Items in `enum
# Item` order (include/crafting.h), the sheet's columns. A weapon is read in
# stone, the drawing unswapped; its other rows are the same drawing in each
# ore's ramp.
ITEM_SHEET, WEAPON_SHEET = 'assets/items.png', 'assets/weapon_icons.png'
ramp_of = lambda tones: next((k for k, v in RAMPS.items() if v == hexes(reversed(tones[1:]))), None)
PIECES = {n: (ITEM_SHEET, i, ramp_of(COLUMNS[i][1]), STEM) for i, n in enumerate(ITEMS) if n not in RETIRED}
PIECES.update({w: (WEAPON_SHEET, i, 'ore rock', HAFT) for i, w in enumerate(weapons_design.ORDER)})
REFERENCE = tuple(n for n in PIECES if n not in ('white_fur', 'feather', 'sleeping_bag'))
# the weapons as held on the map (HELD, HELD_DIAG in weapons_design.py): after the icons on the sheet
PIECES.update({w + ' held': (WEAPON_SHEET, 7 + i, 'ore rock', HAFT) for i, w in enumerate(weapons_design.ORDER)})
PIECES.update({w + ' held diag': (WEAPON_SHEET, 14 + i, 'ore rock', HAFT) for i, w in enumerate(weapons_design.ORDER)})

RULES = {'pal': 'off palette', 'ramp': 'not its ramp', 'tones': 'over 6 tones', 'out': 'open outline', 'light': 'lit from below'}
TONES_MAX = 6    # two materials of three tones (the user, 2026-10-12), besides black and white
OUT = 0.74       # the least of a silhouette's edge that is black: the flower's 75%, its 1-px stem bare
SHADED = 3       # pixels of a ramp's dark tone before it is shading: fewer is a mark (the vine's 1, the dagger's 2)


def swatch(name, sheet=None):
    """An icon -- or a whole sheet -- as rows of 'rrggbb' or None."""
    im = overworld_style._open(sheet or PIECES[name][0])
    if not sheet:
        im = im.crop((PIECES[name][1] * 16, 0, PIECES[name][1] * 16 + 16, 16))
    px = [('%02x%02x%02x' % p[:3]) if p[3] else None for p in im.get_flattened_data()]
    return [px[y * im.width:(y + 1) * im.width] for y in range(im.height)]


def measure(name):
    """overworld_style.measure()'s figures; tones, the icon's colours less
    black and white; stray, the colours that are neither its ramp's nor its
    drawing's own; light, how far its ramp's dark tone lies down and right of
    its lit one (None with too little of either to say)."""
    px = swatch(name)
    ramp = RAMPS.get(PIECES[name][2], ())
    seen = {c for r in px for c in r if c}
    mid = lambda tone: [sum(v) / len(v) for v in zip(*[(x, y) for y, r in enumerate(px) for x, c in enumerate(r) if c == tone])]
    lit, dark = (mid(ramp[0]), mid(ramp[-1])) if ramp else ([], [])
    shaded = sum(r.count(ramp[-1]) for r in px) >= SHADED if ramp else False
    return {**overworld_style.measure(px), 'tones': len(seen - {'000000', WHITE}),
            'stray': sorted(seen - set(ramp) - set(PIECES[name][3]) - {'000000', WHITE}),
            'light': sum(dark) - sum(lit) if lit and shaded else None}


def check(name):
    """An icon against the rules -> {rule: how many pixels or colours break
    it; 0 a pass}."""
    m = measure(name)
    return {'pal': interior_style.check(swatch(name), own=True)['pal'],
            'ramp': len(m['stray']), 'tones': m['tones'] if m['tones'] > TONES_MAX else 0,
            'out': int(m['out'] < OUT), 'light': int(m['light'] is not None and m['light'] < 0)}


def board(names, out):
    """The icons at 4x (interior_style.board draws at 2x: each pixel doubled
    first) -- the reference's items and weapons, then the rest -- what each
    breaks written under it."""
    rows = {}
    for n in names:
        rows.setdefault(('items' if PIECES[n][0] == ITEM_SHEET else 'weapons') if n in REFERENCE else 'held to them', []).append(n)
    twice = lambda px: [[c for c in r for _ in (0, 1)] for r in px for _ in (0, 1)]
    interior_style.board(list(rows), out, swatches=lambda row: {n: twice(swatch(n)) for n in rows[row]},
                         verdict=lambda row, n, px: [RULES[k] for k, v in check(n).items() if v],
                         reference=('items', 'weapons'))


if __name__ == '__main__':
    args = sys.argv[1:]
    out = args.pop(args.index('--board') + 1) if '--board' in args else None
    names = [a for a in args if not a.startswith('--')] or list(PIECES)
    if out:
        board(names, out)
        sys.exit()
    if '--measure' in args:
        for name in names:
            m = measure(name)
            print('%-14s %-13s tones %d  out %5.1f%%  black %4.1f%%  light %5s  %s' % (
                name, PIECES[name][2], m['tones'], 100 * m['out'], 100 * m['line'],
                '-' if m['light'] is None else '%+.1f' % m['light'], 'not its ramp: ' + ' '.join(m['stray']) if m['stray'] else ''))
        sys.exit()
    fails = 0
    print('%-16s' % 'icon' + ''.join('%7s' % r for r in RULES))
    for name in names:
        res = check(name)
        fails += any(res.values())
        print('%-16s' % (name + (' *' if name in REFERENCE else '')) + ''.join('%7s' % (res[r] or '.') for r in RULES))
    # the weapons' other rows: the same drawings in each ore's ramp
    off = interior_style.check(swatch(None, WEAPON_SHEET), own=True)['pal']
    print('weapons, every ore: %s' % ('%d pixels off palette' % off if off else 'on palette'))
    print('* the reference')
    print('FAIL: %d icons' % (fails + bool(off)) if fails or off else 'PASS')
    sys.exit(1 if fails or off else 0)
