"""The overworld style bible's measurable half (art/direction/OVERWORLD_STYLE.md):
the materials the overworld draws with, its pieces, and the checker.

    python tools/overworld_style.py                   # every piece: PASS/FAIL a rule, a row a piece
    python tools/overworld_style.py grass ruins       # some
    python tools/overworld_style.py --measure         # the figures the thresholds are set from
    python tools/overworld_style.py --board out.png   # the pieces side by side, their verdicts under them

Measured from the pieces the user is happy with (REFERENCE). The interiors'
half is tools/interior_style.py, and what the two share -- stone, sandstone,
the palette and four-colour rules, the board -- is taken from there.
"""
import functools, glob, json, os, re, runpy, sys
from collections import Counter
import interior_style
from interior_style import ROOT, crop

ART = os.path.join(ROOT, 'art', 'structures')
SHEET = 'assets/tileset.png'
KEY = 'ff0000'          # the sheet's clear colour
HOUSES = sorted(os.path.basename(f)[:-10] for f in glob.glob(os.path.join(ART, 'houses', '*_design.py')))

# A material: its tones from lit to dark, and its joint (interior_style.py). A
# ground is its fill and then what is laid on it. Where the reference or the
# interiors already draw a material, that is the one; the rest are a piece's
# own tones, named here once.
MATERIALS = {k: interior_style.MATERIALS[k] for k in ('stone', 'sandstone', 'wood', 'bark', 'brick', 'dark stone', 'dirt')}
MATERIALS.update({
    'grass':     {'tones': ('4edc4a', '00881b'), 'joint': '000000'},
    'meadow':    {'tones': ('a8f0bc', 'fc74b4', '00a800'), 'joint': '000000'},
    'snow':      {'tones': ('fcfcfc', 'f0bc3c'), 'joint': '000000'},
    'sand':      {'tones': ('f0e880', 'e8e0c0', 'd0c078'), 'joint': '000000'},
    'water':     {'tones': ('5c94fc', 'fcfcfc'), 'joint': '000000'},
    'foliage':   {'tones': ('05c43a', '058f3a', '235436'), 'joint': '000000'},   # every tree's greens
    # not in the reference: each piece's own
    'wasteland': {'tones': ('341e10', '110000', '583518'), 'joint': '000000'},   # cracked earth: fill, crack, clod (2026-10-14)
    'lava':      {'tones': ('b70000', '7c0a1b'), 'joint': '000000'},
    # the interiors' bone (the catacombs' walls) with the roster's bone white above it: the desert's bones
    'bone':      {'tones': ('e8e0c0', 'b2966a', '8d6b4f'), 'joint': '000000'},
    # the villages' (art/structures/villages/): thatch on the grass cottages, rust on the wasteland huts' stovepipes
    'thatch':    {'tones': ('c9a433', '876a1f'), 'joint': '000000'},
    'rust':      {'tones': ('764c20', '3e1c0e'), 'joint': '000000'},
    'yellow paint': {'tones': ('fae488', 'f0bc3c'), 'joint': '000000'},     # the meadow farms' boards
    # A track -- a road, a trail, a town's street -- is in the trail tones of the
    # ground it lies on (paving, edge; GroundBiome::track in src/tilemap.cpp).
    # Grass's are the start town's street, read off the sheet; the rest are
    # drawn, not on the sheet, and named here so the game's table cites a material.
    'town pad':  {'tones': ('d7a175', '8d6b4f'), 'joint': '000000'},             # trail grass
    'trail meadow':    {'tones': ('b2966a', '967448'), 'joint': '000000'},
    'trail sand':      {'tones': ('cebe82', 'b29e5c'), 'joint': '000000'},
    'trail wasteland': {'tones': ('463422', '110000'), 'joint': '000000'},
    'trail snow':      {'tones': ('c6ccda', 'a4aaba'), 'joint': '000000'},
    'oasis water': {'tones': ('84a7e9', '3e91cc'), 'joint': '000000'},
    # rock that holds ore is in its ore's ramp (gen_cave_entrances.py TONES);
    # this is stone's, and DEFAULT is the cliffs' with no cave in them
    'ore rock':   {'tones': ('bcbeca', '848694', '474751'), 'joint': '000000'},
    'cliff rock': {'tones': ('b29e5c', '887000', '493712'), 'joint': '000000'},
    'gold':       {'tones': ('fae488', 'c9a433', '685018'), 'joint': '000000'},  # kharvite's: the gold ore vein's, the gold icon's
    'glass':  {'tones': ('5c94fc', 'b70000'), 'joint': '000000'},                # the church's windows
    'doorway': {'tones': ('241c0a',), 'joint': '000000'},                        # the pyramid's
    'sign':   {'tones': ('e8e0c0', '94703d', '633e1b'), 'joint': '000000'},
    'player': {'tones': ('f0b890', 'b6433d', '633e1b'), 'joint': '000000'},
    # the coastal town's (art/structures/coast/): boards and towers are painted, not laid in a material
    'white paint': {'tones': ('fcfcfc', 'c6ccda', '9797aa'), 'joint': '000000'},
    'red paint':   {'tones': ('b70000', '7c0a1b'), 'joint': '000000'},
    'green paint': {'tones': ('235436',), 'joint': '000000'},
    'navy paint':  {'tones': ('2850a0',), 'joint': '000000'},
    'black paint': {'tones': ('34343e',), 'joint': '000000'},
    'slate':       {'tones': ('595965', '474751'), 'joint': '000000'},      # roofs, and ironwork
    'lamplight':   {'tones': ('fae488',), 'joint': '000000'},
    'lantern glass': {'tones': ('5c94fc',), 'joint': '000000'},             # the church's glass, without its red
})
for h in HOUSES:        # brick (and side face), its shade (and door), mortar (and trim and panes), roof
    pal = runpy.run_path(os.path.join(ART, 'houses', h + '_design.py'))['PAL']
    MATERIALS[h + ' brick'] = {'tones': (pal['B'], pal['S']), 'joint': pal['M']}
    MATERIALS[h + ' roof'] = {'tones': (pal['R'],), 'joint': '000000'}

# The rock texture is read as the game paints it: the packed rows of
# src/cliff_texture.inc (art/cliffs/gen_cliff_texture.py, each stone one flat
# tone), a digit a pixel -- crack, shade, base -- here in the cliffs' own ramp.
CLIFF = ('000000', '493712', '887000')

# piece: (its drawing -- a PNG, (col, row, cols, rows) of the sheet's cells, or
# (png, x, y, w, h) a piece of a PNG in pixels; its kind; the materials it is
# made of; colours to swap as the game does).
PIECES = {
    'grass':     ((18, 2, 3, 2), 'ground', ('grass',)),
    'meadow':    ((21, 2, 3, 2), 'ground', ('meadow',)),
    'snow':      ((24, 2, 3, 2), 'ground', ('snow',)),
    'sand':      ((21, 0, 3, 2), 'ground', ('sand',)),
    'water':     ((14, 0, 1, 1), 'ground', ('water',)),
    'tree three lobe': ('art/structures/trees/tree_three_lobe.png', 'object', ('foliage',)),
    'tree clumps':     ('art/structures/trees/tree_clumps.png', 'object', ('foliage',)),
    'ruins':      ('art/structures/entrances/ruins.png', 'built', ('stone',)),
    'mausoleum':  ('art/structures/entrances/mausoleum.png', 'built', ('stone',)),
    'stonehenge': ('art/structures/entrances/stonehenge.png', 'built', ('stone',)),
    'church':     ('art/structures/entrances/church.png', 'built', ('stone', 'glass')),
}
PIECES.update({h: ('art/structures/houses/%s.png' % h, 'built', (h + ' brick', h + ' roof')) for h in HOUSES})
REFERENCE = tuple(PIECES)
PIECES.update({
    'wasteland':   ('art/ground/wasteland.png', 'ground', ('wasteland',)),   # sheet cols 27-29 rows 4-5
    'lava':        ((15, 0, 1, 1), 'ground', ('lava',)),
    'town pads':   ((0, 6, 15, 5), 'ground', ('town pad',)),
    'oasis water': ('art/structures/entrances/oasis_water.png', 'ground', ('oasis water',)),
    'conifer a':   ((18, 0, 1, 2), 'object', ('foliage', 'snow')),
    'conifer b':   ((19, 0, 1, 2), 'object', ('foliage', 'snow')),
    'dead tree':   ((20, 0, 1, 2), 'object', ('bark',)),
    'palm':        ('art/structures/entrances/palm.png', 'object', ('foliage',)),
    'large tree':  ('art/structures/entrances/large_tree.png', 'object', ('bark',)),
    'sign':        ('art/structures/town/sign.png', 'object', ('sign',)),
    'player':      ('assets/player_small.png', 'object', ('player',)),
    'gravestones': ('art/structures/entrances/gravestones.png', 'built', ('stone',)),
    'pyramid':     ('art/structures/entrances/pyramid.png', 'built', ('sandstone', 'stone', 'doorway')),
    'oasis':       ('art/structures/entrances/oasis.png', 'built', ('ore rock', 'stone', 'foliage', 'snow')),
    'yard walls':  ('art/structures/entrances/yard_walls.png', 'built', ('wood', 'stone')),
    'cave mouth':  ('art/structures/cave_entrance.png', 'built', ('ore rock',)),
    'cliff rock':  ('src/cliff_texture.inc', 'built', ('cliff rock',)),
})
# the villages' sets (art/structures/villages/<set>_design.py): three houses and a well a strip,
# each on its own cells, standing on the strip's bottom row
VILLAGE_SETS = {
    'grass':  ('white paint', 'bark', 'thatch', 'brick', 'stone', 'wood'),
    'meadow': ('yellow paint', 'white paint', 'red paint', 'green paint', 'slate', 'brick', 'stone', 'wood', 'dirt', 'foliage'),
    'sand':   ('sandstone', 'thatch', 'wood'),
    'snow':   ('wood', 'white paint', 'stone'),
    'waste':  ('dark stone', 'slate', 'rust', 'wood'),
}
VILLAGE_PIECES = {s: (('small', 0, 4), ('middle', 4, 5), ('large', 9, 6), ('well', 15, 2)) for s in VILLAGE_SETS}
VILLAGE_PIECES['meadow'] = (('shed', 0, 4), ('cottage', 4, 5), ('farmhouse', 9, 6), ('barn', 15, 6), ('well', 21, 2), ('field', 23, 1))
VILLAGE_ROWS = {'meadow': 7}                          # a strip's cells tall (5 unless its barn makes it more)
for _set, _mats in VILLAGE_SETS.items():
    _png = 'art/structures/villages/%s.png' % _set
    for _name, _x, _w in VILLAGE_PIECES[_set]:
        PIECES['%s %s' % (_set, _name)] = ((_png, _x * 16, 0, _w * 16, VILLAGE_ROWS.get(_set, 5) * 16), 'built', _mats)
# the desert's formations (art/structures/entrances/desert_design.py), a column of the strip each
DESERT = (('saguaro', 'foliage'), ('saguaro small', 'foliage'), ('barrel cactus', 'foliage'), ('prickly pear', 'foliage'),
          ('boulder', 'cliff rock'), ('boulders', 'cliff rock'), ('spire', 'cliff rock'), ('shrub', 'bark'),
          ('skull', 'bone'), ('ribs', 'bone'))
PIECES.update({n: (('art/structures/entrances/desert.png', 16 * i, 0, 16, 32), 'object', (m,)) for i, (n, m) in enumerate(DESERT)})
# The country's landmarks (art/structures/landmarks/*_design.py; gen_entrance_art.py
# LANDMARKS): the place, built or an object; every cache is the one chest, shut and open.
PIECES.update({
    'old well':          (('art/structures/landmarks/well.png', 0, 0, 32, 32), 'built', ('stone', 'wood')),
    'chest':             (('art/structures/landmarks/chest.png', 0, 0, 16, 16), 'object', ('wood', 'stone')),
    'chest open':        (('art/structures/landmarks/chest.png', 16, 0, 16, 16), 'object', ('wood', 'stone')),
    'woodshed':          (('art/structures/landmarks/camp.png', 0, 0, 48, 48), 'built', ('wood', 'bark')),
    'camp fire':         (('art/structures/landmarks/camp.png', 48, 32, 16, 16), 'object', ('stone',)),
    'statue head':       (('art/structures/landmarks/statue.png', 0, 0, 32, 32), 'object', ('stone',)),
    'cairn':             (('art/structures/landmarks/cairn.png', 0, 0, 32, 32), 'object', ('stone', 'snow')),
    'burnt wagon':       (('art/structures/landmarks/wagon.png', 0, 0, 48, 32), 'object', ('bark',)),
    'wrecked boat':      (('art/structures/landmarks/boat.png', 0, 0, 48, 32), 'object', ('wood',)),
})
# The overworld's props (art/structures/props/props.py, laid by worldgen's "Props"), read from
# the registry: each one's first frame or variant, built if it is drawn in the houses' projection,
# its materials those whose tones it is drawn in. The tufts -- ground cover drawn as the ground
# draws its grass, with no line round it -- are let off the outline (TUFTS).
PROP_BUILT = {'arch', 'balanced_rock', 'mesa', 'slab', 'wagon_covered', 'wagon_buried', 'woodpile',
              'lean_to', 'hay_bale', 'handcart', 'wheelbarrow', 'barrel', 'trough', 'field_gate',
              'stele', 'serpent_head', 'jaguar', 'altar', 'ball_ring', 'fallen_block', 'chacmool'}
TUFTS = ('grass_a', 'grass_b', 'leaf_litter', 'tall_grass_a', 'tall_grass_b')


def _prop_pieces():
    from PIL import Image
    sys.path.insert(0, os.path.join(ROOT, 'art', 'structures', 'props'))
    import props
    mats = {k: set(v['tones']) for k, v in MATERIALS.items() if not k.startswith('mini') and k != 'player'}
    out = {}
    for name, path, x, w, h, *_ in props.PROPS:
        src = ('art/structures/props/' + path, x, 0, w * 16, h * 16)
        im = Image.open(os.path.join(ROOT, src[0])).convert('RGBA').crop((x, 0, x + w * 16, h * 16))
        cols = {'%02x%02x%02x' % p[:3] for p in im.get_flattened_data() if p[3]} - {'000000'}
        need, made = set(cols), []
        while need:                                         # fewest materials that cover its colours
            best = max(sorted(mats), key=lambda m: (len(mats[m] & need), -len(mats[m] - cols)))
            if not mats[best] & need:
                break
            made.append(best)
            need -= mats[best]
        out[name] = (src, 'built' if name in PROP_BUILT else 'object', tuple(made))
    return out


PIECES.update(_prop_pieces())
# The things to mine (art/structures/nodes/nodes_design.py): the stone rock, and the vein -- the
# overworld's gold ore, and in a cave its ore's (tools/gen_cave_tiles.py; the gold read here).
PIECES.update({
    'stone node':  (('art/structures/nodes/nodes.png', 0, 0, 16, 16), 'object', ('ore rock',)),
    'ore vein':    (('art/structures/nodes/nodes.png', 16, 0, 16, 16), 'object', ('ore rock', 'gold')),
})
PIECES.update({'ore vein ' + k: (('art/structures/nodes/nodes.png', 16 * i, 0, 16, 16), 'object', ('ore rock', 'gold'))
               for i, k in ((2, 'a'), (3, 'b'), (4, 'c'))})     # its twinkle: a nugget flared
# The coastal town's (art/structures/coast/*_design.py), read where they lie on
# the sheet: the user edits them there (2026-10-12), so the sheet is the drawing.
COAST = {
    'cape':       ((0, 184, 7, 7), ('green paint', 'slate', 'brick')),
    'winged':     ((8, 182, 8, 9), ('black paint', 'slate', 'brick')),
    'captain':    ((17, 182, 9, 9), ('navy paint', 'black paint', 'brick')),
    'inn':        ((27, 182, 11, 9), ('green paint', 'slate', 'brick')),
    'store':      ((39, 184, 8, 7), ('red paint', 'slate')),
    'shack':      ((48, 186, 4, 5), ('slate',)),
    'boathouse':  ((53, 185, 8, 6), ('red paint', 'slate')),
    'meeting':    ((62, 180, 7, 11), ('black paint', 'slate')),
    'townhall':   ((70, 181, 9, 10), ('navy paint', 'slate')),
    'lighthouse': ((80, 180, 6, 11), ('red paint', 'lantern glass', 'lamplight', 'slate')),
    'gazebo':     ((87, 186, 5, 5), ('slate',)),
}
PIECES.update({n: (at, 'built', ('white paint',) + made) for n, (at, made) in COAST.items()})
PIECES.update({                                     # the green's things: art/structures/coast/park_design.py
    'bench':        ((93, 190, 1, 1), 'object', ('wood',)),
    'street lamp':  ((94, 188, 1, 3), 'object', ('slate', 'lamplight')),
    'fountain':     ((95, 188, 3, 3), 'object', ('stone', 'water')),
    'picket fence': ((98, 190, 1, 1), 'object', ('white paint',)),
    'flower bed':   ((99, 190, 1, 1), 'object', ('foliage', 'meadow')),
    # the wharf: the graveyard dungeon's boardwalk (its planks, and the face and posts under them), and
    # the cells tools/town1_layout.py bakes from it for the wharf's deck in the houses' projection
    'boardwalk':    ((232, 44, 4, 4), 'built', ('wood',)),
    'wharf deck':   ((0, 192, 96, 1), 'built', ('wood',)),
})

# The map minis (tools/minis.py): each enemy's chaser, an object in three of its own battle colours.
for _f in sorted(glob.glob(os.path.join(ROOT, 'art', 'enemies', 'minis', '*_mini.json'))):
    _n = 'mini ' + os.path.basename(_f)[:2]
    MATERIALS[_n] = {'tones': tuple(v for v in json.load(open(_f))['pal'].values() if v != '000000'), 'joint': '000000'}
    PIECES[_n] = (os.path.relpath(_f[:-5] + '.png', ROOT), 'object', (_n,))


@functools.lru_cache(None)
def _open(path):
    from PIL import Image
    return Image.open(os.path.join(ROOT, path)).convert('RGBA')


def swatch(name):
    """A piece as rows of 'rrggbb' or None."""
    src = PIECES[name][0]
    if isinstance(src, str) and src.endswith('.inc'):
        return [[CLIFF[int(c)] for c in r] for r in re.findall(r'"(\d+)"', open(os.path.join(ROOT, src)).read())]
    swap = {KEY: None, **(PIECES[name][3] if len(PIECES[name]) > 3 else {})}
    if isinstance(src, tuple) and len(src) == 5:
        im = _open(src[0]).crop((src[1], src[2], src[1] + src[3], src[2] + src[4]))
    elif isinstance(src, tuple):
        c, r, w, h = src
        im = _open(SHEET).crop((c * 16, r * 16, (c + w) * 16, (r + h) * 16))
    else:
        im = _open(src)
    hexes = [('%02x%02x%02x' % p[:3]) if p[3] else None for p in im.get_flattened_data()]
    return [[swap.get(c, c) for c in hexes[y * im.width:(y + 1) * im.width]] for y in range(im.height)]


# ---------------------------------------------------------------- the checker

RULES = {'pal': 'off palette', 'col': 'over 4 colours', 'ramp': 'undeclared colours', 'speck': 'specks',
         'lit': 'highlight', 'flat': 'busy ground', 'line': 'lined ground', 'out': 'open outline', 'tones': 'over 3 tones'}

# Each set just outside the reference's worst case.
FLAT = 0.85      # the least of a ground its fill covers: the water's 85.9%
LINE = 0.012     # the most of a ground that is black: the grass's and the snow's 1.1% (the dots under their tufts)
SPECK = {'ground': 0.03,     # lone pixels a piece may hold: the sand's grains are 2.9% of it,
         'built': 0.014}     # the church's 1.36%; an object is too few pixels to count them in
OUT = 0.99       # the least of a silhouette's edge that is black: every reference piece's is all of it
JOINED = ('yard walls', 'picket fence', 'wharf deck', 'meadow field')     # a deck cut into cells; its posts are 3 px, too thin to line     # drawn as pieces that join in the game: open where they meet, by design
TONES = 3        # an object's colours besides black: the trees' three greens


def measure(px):
    """What the rules of a kind read off a piece: flat, the share its
    commonest colour fills; line, the share that is black; out, the share of
    its silhouette's edge that is black (an edge is a pixel beside a clear
    one; where its canvas cuts it is not one); tones, its colours besides
    black."""
    h, w = len(px), len(px[0])
    count = Counter(c for r in px for c in r if c)
    n = sum(count.values())
    edge = [px[y][x] for y in range(h) for x in range(w) if px[y][x] and any(
        0 <= y + j < h and 0 <= x + i < w and not px[y + j][x + i] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    return {'flat': count.most_common(1)[0][1] / n, 'line': count['000000'] / n,
            'out': edge.count('000000') / len(edge) if edge else 1.0, 'tones': len(set(count) - {'000000'})}


def check(name):
    """A piece against its kind's rules -> {rule: how many pixels, cells or
    materials break it; 0 a pass}. The first five are the interiors' own
    (interior_style.check), read against the piece's materials."""
    kind, px = PIECES[name][1], swatch(name)
    res = interior_style.check(px, materials={m: MATERIALS[m] for m in PIECES[name][2]}, speck=SPECK.get(kind, 1))
    m = measure(px)
    return {'pal': res['pal'], 'col': res['col'], 'ramp': res['ramp'], 'speck': res['speck'],
            'lit': res['lit'] if kind == 'built' else 0,       # a ground's and an object's lightest tone may be a mark
            'flat': int(kind == 'ground' and m['flat'] < FLAT),
            'line': int(kind == 'ground' and m['line'] > LINE),
            'out': int(kind != 'ground' and name not in JOINED + TUFTS and m['out'] < OUT),
            'tones': m['tones'] if kind == 'object' and m['tones'] > TONES else 0}


def board(names, out):
    """The pieces at 2x, a row a kind -- the reference's, then the rest's --
    what each breaks written under it."""
    rows = {}
    for n in names:
        rows.setdefault(PIECES[n][1] if n in REFERENCE else PIECES[n][1] + ', held to it', []).append(n)
    interior_style.board(list(rows), out, swatches=lambda row: {n: swatch(n) for n in rows[row]},
                         verdict=lambda row, n, px: [RULES[k] for k, v in check(n).items() if v],
                         reference=KINDS, cut=(512, 160))


KINDS = ('ground', 'object', 'built')

if __name__ == '__main__':
    args = sys.argv[1:]
    out = args.pop(args.index('--board') + 1) if '--board' in args else None
    names = [a for a in args if not a.startswith('--')] or list(PIECES)
    if out:
        board(names, out)
        sys.exit()
    if '--measure' in args:
        for name in names:
            m = measure(swatch(name))
            print('%-16s %-7s flat %5.1f%%  line %4.1f%%  out %5.1f%%  tones %d' % (
                name, PIECES[name][1], 100 * m['flat'], 100 * m['line'], 100 * m['out'], m['tones']))
        sys.exit()
    fails = 0
    print('%-24s' % 'piece' + ''.join('%7s' % r for r in RULES))
    for name in names:
        res = check(name)
        fails += any(res.values())
        print('%-24s' % (name + (' *' if name in REFERENCE else '')) + ''.join('%7s' % (res[r] or '.') for r in RULES))
    print('* the reference')
    print('FAIL: %d pieces' % fails if fails else 'PASS')
    sys.exit(1 if fails else 0)
