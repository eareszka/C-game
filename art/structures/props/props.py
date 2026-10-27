"""Every overworld prop the game lays: its biome, the groups it comes in, its
cells, what its feet meet, how it breaks and what it drops.

gen_entrance_art.py --props reads this, packs each prop (every frame or
variant beside the first) into the sheet's band PROP_BAND and writes
src/props.inc; src/tilemap.cpp ("Props") lays them in groups by theme.

A row: (name, export, x, w, h, frames, biome, themes, anchor, weight,
stray, stand, breaks, drops)
  x        the first frame's left edge in the export, pixels (variants of one
           export are rows of their own)
  w, h     cells of one frame
  frames   1, or an animation's frames side by side from x
  themes   the groups it is laid in; a group is one theme and never mixes
  anchor   laid once, at a group's middle, and only there
  weight   how often it is picked among a theme's fillers
  stray    how often it is picked as a lone thing between groups (0: never)
  stand    'lying' walked over; 'low' all of it is ground (a log); or the
           pixels of ground up from each column's lowest -- what the feet meet
  breaks   'axe' (a tree to the weapons), 'stone' (a rock), 'any' (a fixed
           number of blows)
  drops    [(item, n)], existing items only (approved 2026-10-26; the
           desert's proposed with the install)
"""

DESERT, FOREST, PLAINS, SNOW, WASTE = 'PB_DESERT', 'PB_FOREST', 'PB_PLAINS', 'PB_SNOW', 'PB_WASTE'
BIOMES = [DESERT, FOREST, PLAINS, SNOW, WASTE]      # PropBiome's order; a new biome goes on the end

# the groups, by biome; each enum value is a bit in a prop's themes. A new theme goes on the
# end, so the ones before keep their bits.
THEMES = {
    'TH_CACTUS': DESERT, 'TH_ROCK': DESERT, 'TH_TRAIL': DESERT,
    'TH_DEADFALL': FOREST, 'TH_CAMP': FOREST, 'TH_UNDERGROWTH': FOREST,
    'TH_FARM': PLAINS, 'TH_MAYAN': PLAINS,
    'TH_ICE': SNOW, 'TH_EXPEDITION': SNOW, 'TH_MAMMOTH': SNOW,
    'TH_VOLCANO': WASTE, 'TH_RUBBLE': WASTE, 'TH_REMAINS': WASTE,
}

D, F, P, S, W = 'desert/', 'forest/', 'plains/', 'snow/', 'wasteland/'
SNOW_ALL = ['TH_ICE', 'TH_EXPEDITION', 'TH_MAMMOTH']
PROPS = [
    # -- desert: cactus country, rock country, the old trail --
    ('saguaro',       D + 'saguaro_tall.png',     0, 2, 3, 1, DESERT, ['TH_CACTUS'], True,  1, 0, 5,       'axe',   [('VINE', 2)]),
    ('organ_pipe',    D + 'organ_pipe.png',       0, 2, 2, 1, DESERT, ['TH_CACTUS'], False, 2, 0, 5,       'axe',   [('VINE', 2)]),
    ('cholla',        D + 'cholla.png',           0, 2, 2, 1, DESERT, ['TH_CACTUS'], False, 3, 0, 4,       'axe',   [('VINE', 1)]),
    ('barrel_cactus', D + 'barrel_flowering.png', 0, 1, 2, 1, DESERT, ['TH_CACTUS'], False, 4, 0, 5,       'axe',   [('VINE', 1), ('FLOWER', 1)]),
    ('agave',         D + 'agave.png',            0, 2, 2, 1, DESERT, ['TH_CACTUS'], False, 3, 0, 6,       'axe',   [('VINE', 2)]),
    ('mesquite',      D + 'mesquite.png',         0, 2, 2, 1, DESERT, ['TH_CACTUS'], False, 2, 0, 4,       'axe',   [('WOOD', 2), ('VINE', 1)]),
    ('grass_a',       D + 'grass.png',            0, 1, 1, 1, DESERT, ['TH_CACTUS'], False, 3, 3, 'lying', 'any',   [('VINE', 1)]),
    ('grass_b',       D + 'grass.png',           16, 1, 1, 1, DESERT, ['TH_CACTUS'], False, 3, 3, 'lying', 'any',   [('VINE', 1)]),
    ('tumbleweed',    D + 'tumbleweed.png',       0, 1, 1, 8, DESERT, [],            False, 0, 2, 'lying', 'any',   [('WOOD', 1)]),
    ('mesa',          D + 'mesa.png',             0, 4, 3, 1, DESERT, ['TH_ROCK'],   True,  1, 0, 8,       'stone', [('STONE', 5)]),
    ('arch',          D + 'arch.png',             0, 4, 3, 1, DESERT, ['TH_ROCK'],   True,  1, 0, 7,       'stone', [('STONE', 5)]),
    ('balanced_rock', D + 'balanced_rock.png',    0, 3, 3, 1, DESERT, ['TH_ROCK'],   True,  1, 0, 7,       'stone', [('STONE', 4)]),
    ('slab',          D + 'slab.png',             0, 3, 2, 1, DESERT, ['TH_ROCK'],   False, 2, 0, 12,      'stone', [('STONE', 3)]),
    ('pebbles_a',     D + 'pebbles.png',          0, 1, 1, 1, DESERT, ['TH_ROCK'],   False, 3, 2, 'lying', 'stone', [('STONE', 1)]),
    ('pebbles_b',     D + 'pebbles.png',         16, 1, 1, 1, DESERT, ['TH_ROCK'],   False, 3, 2, 'lying', 'stone', [('STONE', 1)]),
    ('pebbles_c',     D + 'pebbles.png',         32, 1, 1, 1, DESERT, ['TH_ROCK'],   False, 3, 2, 'lying', 'stone', [('STONE', 1)]),
    ('wagon_covered', 'wagon_covered.png',        0, 3, 2, 1, DESERT, ['TH_TRAIL'],  True,  1, 0, 9,       'axe',   [('WOOD', 4), ('HIDE', 1)]),
    ('wagon_buried',  'wagon_buried.png',         0, 3, 2, 1, DESERT, ['TH_TRAIL'],  True,  1, 0, 9,       'axe',   [('WOOD', 3)]),
    ('fence_post',    D + 'fence_post.png',       0, 1, 2, 1, DESERT, ['TH_TRAIL'],  False, 3, 0, 4,       'axe',   [('WOOD', 2)]),
    ('fence_rail',    D + 'fence_post.png',      16, 1, 2, 1, DESERT, ['TH_TRAIL'],  False, 3, 0, 4,       'axe',   [('WOOD', 2)]),
    ('fence_plank',   D + 'fence_post.png',      32, 1, 2, 1, DESERT, ['TH_TRAIL'],  False, 2, 0, 'lying', 'axe',   [('WOOD', 2)]),
    ('signpost',      D + 'signpost.png',         0, 1, 2, 1, DESERT, ['TH_TRAIL'],  False, 2, 0, 4,       'axe',   [('WOOD', 2)]),
    ('cattle_skull',  D + 'cattle_skull.png',     0, 2, 1, 1, DESERT, ['TH_TRAIL'],  False, 2, 1, 'lying', 'any',   [('BONE', 1), ('HORN', 1)]),

    # -- forest: deadfall, a woodcutter's camp, undergrowth --
    ('uprooted_tree', F + 'uprooted_tree.png',    0, 3, 2, 1, FOREST, ['TH_DEADFALL'], True,  1, 0, 8,      'axe',   [('WOOD', 5)]),
    ('fallen_log',    F + 'fallen_log.png',       0, 2, 1, 1, FOREST, ['TH_DEADFALL'], False, 3, 0, 'low',  'axe',   [('WOOD', 3)]),
    ('hollow_log',    F + 'hollow_log.png',       0, 3, 1, 1, FOREST, ['TH_DEADFALL'], False, 2, 0, 'low',  'axe',   [('WOOD', 3)]),
    ('mossy_stump',   F + 'mossy_stump.png',      0, 1, 1, 1, FOREST, ['TH_DEADFALL'], False, 3, 0, 'low',  'axe',   [('WOOD', 2), ('VINE', 1)]),
    ('mushrooms',     F + 'mushrooms.png',        0, 1, 1, 1, FOREST, ['TH_DEADFALL'], False, 3, 2, 'lying', 'any',  [('FLOWER', 1)]),
    ('leaf_litter',   F + 'leaf_litter.png',      0, 1, 1, 1, FOREST, ['TH_DEADFALL'], False, 3, 3, 'lying', 'any',  [('VINE', 1)]),
    ('fallen_branch', F + 'fallen_branch.png',    0, 2, 1, 1, FOREST, ['TH_DEADFALL', 'TH_CAMP'], False, 2, 2, 'lying', 'axe', [('WOOD', 1)]),
    ('fern',          F + 'fern.png',             0, 2, 1, 1, FOREST, ['TH_DEADFALL', 'TH_UNDERGROWTH'], False, 2, 3, 'lying', 'any', [('VINE', 1)]),
    ('lean_to',       F + 'lean_to.png',          0, 3, 2, 1, FOREST, ['TH_CAMP'],     True,  1, 0, 10,     'axe',   [('WOOD', 3), ('HIDE', 1)]),
    ('woodpile',      F + 'woodpile.png',         0, 2, 2, 1, FOREST, ['TH_CAMP'],     False, 3, 0, 8,      'axe',   [('WOOD', 5)]),
    ('axe_stump',     F + 'axe_stump.png',        0, 1, 2, 1, FOREST, ['TH_CAMP'],     False, 3, 0, 5,      'axe',   [('WOOD', 2), ('STONE', 1)]),
    ('mossy_boulder', F + 'mossy_boulder.png',    0, 2, 2, 1, FOREST, ['TH_UNDERGROWTH'], True, 1, 0, 8,    'stone', [('STONE', 3)]),
    ('berry_bush',    F + 'berry_bush.png',       0, 1, 2, 1, FOREST, ['TH_UNDERGROWTH'], False, 3, 0, 5,   'axe',   [('VINE', 1), ('FLOWER', 1)]),
    ('bramble',       F + 'bramble.png',          0, 2, 1, 1, FOREST, ['TH_UNDERGROWTH'], False, 3, 0, 'low', 'axe',  [('VINE', 2)]),
    ('nest_stump',    F + 'nest_stump.png',       0, 1, 2, 1, FOREST, ['TH_UNDERGROWTH'], False, 2, 0, 5,   'axe',   [('WOOD', 2), ('FEATHER', 1)]),
    ('sapling',       F + 'sapling.png',          0, 1, 2, 4, FOREST, ['TH_UNDERGROWTH'], False, 3, 0, 3,   'axe',   [('WOOD', 1), ('VINE', 1)]),
    ('deer_skull',    F + 'deer_skull.png',       0, 1, 1, 1, FOREST, ['TH_UNDERGROWTH'], False, 1, 0, 'lying', 'any', [('BONE', 1), ('HORN', 1)]),

    # -- plains: a farmstead, or Mayan ruins; never the two together --
    ('haystack',      P + 'haystack.png',         0, 2, 2, 1, PLAINS, ['TH_FARM'],  True,  1, 0, 8,       'axe',   [('VINE', 3)]),
    ('hay_bale',      P + 'hay_bale.png',         0, 1, 1, 1, PLAINS, ['TH_FARM'],  False, 4, 0, 8,       'axe',   [('VINE', 2)]),
    ('scarecrow',     P + 'scarecrow.png',        0, 1, 2, 1, PLAINS, ['TH_FARM'],  False, 2, 0, 3,       'axe',   [('WOOD', 1), ('VINE', 1)]),
    ('handcart',      P + 'handcart.png',         0, 2, 1, 1, PLAINS, ['TH_FARM'],  False, 2, 0, 6,       'axe',   [('WOOD', 3)]),
    ('wheelbarrow',   P + 'wheelbarrow.png',      0, 2, 1, 1, PLAINS, ['TH_FARM'],  False, 2, 0, 6,       'axe',   [('WOOD', 2)]),
    ('barrel',        P + 'barrel.png',           0, 1, 1, 1, PLAINS, ['TH_FARM'],  False, 3, 0, 8,       'axe',   [('WOOD', 2)]),
    ('trough',        P + 'trough.png',           0, 2, 1, 1, PLAINS, ['TH_FARM'],  False, 2, 0, 8,       'axe',   [('WOOD', 2)]),
    ('field_gate',    P + 'field_gate.png',       0, 2, 2, 1, PLAINS, ['TH_FARM'],  False, 1, 0, 6,       'axe',   [('WOOD', 2)]),
    ('tall_grass_a',  P + 'tall_grass.png',       0, 1, 1, 1, PLAINS, ['TH_FARM'],  False, 3, 3, 'lying', 'any',   [('VINE', 1)]),
    ('tall_grass_b',  P + 'tall_grass.png',      16, 1, 1, 1, PLAINS, ['TH_FARM'],  False, 3, 3, 'lying', 'any',   [('VINE', 1)]),
    ('ball_ring',     P + 'ball_ring.png',        0, 2, 2, 1, PLAINS, ['TH_MAYAN'], True,  1, 0, 8,       'stone', [('STONE', 3)]),
    ('chacmool',      P + 'chacmool.png',         0, 2, 1, 1, PLAINS, ['TH_MAYAN'], True,  1, 0, 8,       'stone', [('STONE', 3)]),
    ('serpent_head',  P + 'serpent_head.png',     0, 2, 1, 1, PLAINS, ['TH_MAYAN'], True,  1, 0, 8,       'stone', [('STONE', 3)]),
    ('stele',         P + 'stele.png',            0, 1, 2, 1, PLAINS, ['TH_MAYAN'], False, 3, 0, 6,       'stone', [('STONE', 3)]),
    ('jaguar',        P + 'jaguar.png',           0, 1, 2, 1, PLAINS, ['TH_MAYAN'], False, 2, 0, 6,       'stone', [('STONE', 2)]),
    ('altar',         P + 'altar.png',            0, 2, 1, 1, PLAINS, ['TH_MAYAN'], False, 2, 0, 8,       'stone', [('STONE', 2), ('EMERALD', 1)]),
    ('clay_pots',     P + 'clay_pots.png',        0, 1, 1, 1, PLAINS, ['TH_MAYAN'], False, 3, 0, 'low',   'any',   [('STONE', 1)]),
    ('fallen_block',  P + 'fallen_block.png',     0, 2, 1, 1, PLAINS, ['TH_MAYAN'], False, 3, 0, 'low',   'stone', [('STONE', 2)]),
    ('maize',         P + 'maize.png',            0, 2, 2, 1, PLAINS, ['TH_MAYAN'], False, 3, 0, 5,       'axe',   [('VINE', 2), ('FLOWER', 1)]),

    # -- snow: the ice field, an abandoned expedition's camp, a mammoth graveyard --
    ('ice_spire',     S + 'ice_spire.png',        0, 2, 3, 4, SNOW, ['TH_ICE'], True,  1, 0, 6,           'stone', [('STONE', 3)]),
    ('ice_cluster',   S + 'ice_cluster.png',      0, 1, 1, 1, SNOW, ['TH_ICE'], False, 3, 1, 'low',       'stone', [('STONE', 1)]),
    ('ice_block',     S + 'ice_block.png',        0, 1, 1, 1, SNOW, ['TH_ICE'], False, 3, 0, 8,           'stone', [('STONE', 1)]),
    ('snow_boulder',  S + 'snow_boulder.png',     0, 2, 2, 1, SNOW, ['TH_ICE'], False, 2, 0, 8,           'stone', [('STONE', 3)]),
    ('icicle_rock',   S + 'icicle_rock.png',      0, 2, 2, 1, SNOW, ['TH_ICE'], False, 2, 0, 8,           'stone', [('STONE', 2)]),
    ('frozen_tufts_a', S + 'frozen_tufts.png',    0, 1, 1, 1, SNOW, SNOW_ALL,   False, 2, 3, 'lying',     'any',   [('VINE', 1)]),
    ('frozen_tufts_b', S + 'frozen_tufts.png',   16, 1, 1, 1, SNOW, SNOW_ALL,   False, 2, 3, 'lying',     'any',   [('VINE', 1)]),
    ('tent',          S + 'tent.png',             0, 3, 2, 1, SNOW, ['TH_EXPEDITION'], True,  1, 0, 10,   'axe',   [('WOOD', 2), ('HIDE', 2)]),
    ('sled',          S + 'sled.png',             0, 2, 1, 1, SNOW, ['TH_EXPEDITION'], False, 2, 0, 'low', 'axe',   [('WOOD', 2)]),
    ('skis',          S + 'skis.png',             0, 1, 2, 1, SNOW, ['TH_EXPEDITION'], False, 2, 0, 3,     'axe',   [('WOOD', 1)]),
    ('crate',         S + 'crate.png',            0, 1, 1, 1, SNOW, ['TH_EXPEDITION'], False, 3, 0, 8,     'axe',   [('WOOD', 2)]),
    ('campfire',      S + 'campfire.png',         0, 2, 1, 1, SNOW, ['TH_EXPEDITION'], False, 1, 0, 'lying', 'any', [('STONE', 1), ('WOOD', 1)]),
    ('snowman',       S + 'snowman.png',          0, 1, 2, 1, SNOW, ['TH_EXPEDITION'], False, 2, 0, 5,     'any',   [('WOOD', 1)]),
    ('mammoth_skull', S + 'mammoth_skull.png',    0, 3, 2, 1, SNOW, ['TH_MAMMOTH'], True,  1, 0, 8,       'stone', [('BONE', 3), ('HORN', 2)]),
    ('ribcage',       S + 'ribcage.png',          0, 2, 2, 1, SNOW, ['TH_MAMMOTH'], False, 2, 0, 6,       'stone', [('BONE', 2)]),
    ('vertebrae',     S + 'vertebrae.png',        0, 2, 1, 1, SNOW, ['TH_MAMMOTH'], False, 3, 1, 'lying', 'any',   [('BONE', 1)]),
    ('frost_bush',    S + 'frost_bush.png',       0, 1, 2, 1, SNOW, ['TH_MAMMOTH'], False, 3, 0, 4,       'axe',   [('WOOD', 1), ('VINE', 1)]),
    ('snowy_log',     S + 'snowy_log.png',        0, 2, 1, 1, SNOW, ['TH_MAMMOTH'], False, 2, 0, 'low',   'axe',   [('WOOD', 3)]),
    ('fur_thornbush', S + 'fur_thornbush.png',    0, 1, 1, 1, SNOW, ['TH_MAMMOTH'], False, 2, 0, 'low',   'axe',   [('WHITE_FUR', 1), ('VINE', 1)]),
    # -- wasteland: the mini volcanoes, in dense groves where the dead trees stood (the user,
    #    2026-10-27; wasteland/volcano_design.py, the mock-up art/concept/wasteland/) --
    ('volcano_big',   W + 'volcano_big.png',      0, 2, 2, 1, WASTE, ['TH_VOLCANO'], True,  1, 0, 4,      'stone', [('STONE', 2)]),
    ('volcano_mid',   W + 'volcano_mid.png',      0, 2, 2, 1, WASTE, ['TH_VOLCANO'], False, 3, 0, 3,      'stone', [('STONE', 2)]),
    ('volcano_small', W + 'volcano_small.png',    0, 2, 1, 1, WASTE, ['TH_VOLCANO'], False, 4, 1, 3,      'stone', [('STONE', 1)]),
    ('volcano_tiny',  W + 'volcano_tiny.png',     0, 1, 1, 1, WASTE, ['TH_VOLCANO'], False, 3, 2, 2,      'stone', [('STONE', 1)]),
    # -- wasteland: the rubble round the void pools (stage 2, 2026-10-27; wasteland/rubble_design.py) --
    ('rubble_pile',    W + 'rubble_pile.png',     0, 2, 1, 1, WASTE, ['TH_RUBBLE'], True,  1, 0, 3,       'stone', [('STONE', 3)]),
    ('rubble_boulder', W + 'rubble_boulder.png',  0, 1, 1, 1, WASTE, ['TH_RUBBLE'], False, 3, 1, 3,       'stone', [('STONE', 1)]),
    ('rubble_pebbles', W + 'rubble_pebbles.png',  0, 1, 1, 1, WASTE, ['TH_RUBBLE'], False, 3, 1, 'lying', 'stone', [('STONE', 1)]),
    ('rubble_stub',    W + 'rubble_stub.png',     0, 1, 1, 1, WASTE, ['TH_RUBBLE'], False, 2, 0, 3,       'stone', [('STONE', 2)]),
    ('rubble_bone',    W + 'rubble_bone.png',     0, 1, 1, 1, WASTE, ['TH_RUBBLE'], False, 2, 1, 'lying', 'any',   [('BONE', 1)]),
    # -- wasteland: the roster filled out, and the remains, rare eerie groups away from the void
    #    (approved by the user 2026-10-27; wasteland/waste_design.py) --
    ('fissure_vent',     W + 'fissure_vent.png',     0, 1, 1, 1, WASTE, ['TH_VOLCANO'], False, 2, 1, 3,     'stone', [('STONE', 1)]),
    ('cinder_shards',    W + 'cinder_shards.png',    0, 1, 1, 1, WASTE, ['TH_VOLCANO'], False, 2, 1, 3,     'stone', [('STONE', 1)]),
    ('scorched_boulder', W + 'scorched_boulder.png', 0, 2, 1, 1, WASTE, ['TH_VOLCANO'], False, 2, 0, 4,     'stone', [('STONE', 2)]),
    ('fallen_wall',      W + 'fallen_wall.png',      0, 3, 1, 1, WASTE, ['TH_RUBBLE'],  True,  1, 0, 5,     'stone', [('STONE', 3)]),
    ('snapped_pillar',   W + 'snapped_pillar.png',   0, 1, 2, 1, WASTE, ['TH_RUBBLE'],  False, 2, 0, 4,     'stone', [('STONE', 2)]),
    ('void_rock',        W + 'void_rock.png',        0, 1, 1, 1, WASTE, ['TH_RUBBLE'],  False, 2, 1, 3,     'stone', [('STONE', 1)]),
    ('bone_pile',        W + 'bone_pile.png',        0, 1, 1, 1, WASTE, ['TH_RUBBLE', 'TH_REMAINS'], False, 2, 1, 'low', 'any', [('BONE', 2)]),
    ('spine_arch',       W + 'spine_arch.png',       0, 3, 2, 1, WASTE, ['TH_REMAINS'], True,  1, 0, 3,     'any',   [('BONE', 3)]),
    ('red_figure',       W + 'red_figure.png',       0, 1, 2, 1, WASTE, ['TH_REMAINS'], False, 1, 0, 3,     'stone', [('STONE', 2)]),
    ('void_lantern',     W + 'void_lantern.png',     0, 1, 2, 1, WASTE, ['TH_REMAINS'], False, 2, 0, 4,     'stone', [('STONE', 2)]),
    ('glyph_obelisk',    W + 'glyph_obelisk.png',    0, 1, 3, 1, WASTE, ['TH_REMAINS'], False, 1, 0, 4,     'stone', [('STONE', 3)]),
    ('spike_row',        W + 'spike_row.png',        0, 2, 1, 1, WASTE, ['TH_REMAINS'], False, 2, 0, 3,     'any',   [('STONE', 1)]),
]

CELL = 16
OVERHANG = 6     # a column whose lowest pixel is this far above the prop's is open beneath (the arch)


def layers(im, stand):
    """(footy, foot, way) for a frame: each pixel's ground line (-1 none), the
    ground the feet cannot go on, and no way in. A column's ground line is its
    lowest pixel; one standing well above the prop's own lowest is open
    beneath, its line the prop's, and no ground."""
    w, h = im.size
    p = im.load()
    footy = [[-1] * w for _ in range(h)]
    foot = [['.'] * w for _ in range(h)]
    way = ['.' * w for _ in range(h)]
    if stand == 'lying':
        return footy, [''.join(r) for r in foot], way
    ink = lambda x, y: p[x, y][3] > 0
    bottom = max((y for y in range(h) for x in range(w) if ink(x, y)), default=-1)
    for x in range(w):
        ys = [y for y in range(h) if ink(x, y)]
        if not ys:
            continue
        base = ys[-1]
        if base < bottom - OVERHANG:
            for y in ys:
                footy[y][x] = bottom
            continue
        for y in ys:
            footy[y][x] = base
            if stand == 'low' or y > base - stand:
                foot[y][x] = '#'
    return footy, [''.join(r) for r in foot], way
