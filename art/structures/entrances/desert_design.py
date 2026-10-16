"""The desert's formations, laid out for tools/draw_views.py.

    python art/structures/entrances/desert_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/desert

Ten things the sand is scattered with (src/tilemap.cpp, "Desert formations"),
side by side, each a column 16 wide and two cells tall: two saguaros, a barrel
cactus and a prickly pear in the trees' greens; a boulder, a pile of three and a
rock spire in the cliffs' rock; a dry shrub in bark; a skull and a ribcage in
bone. Objects, by the overworld bible: one black line round the silhouette and
between parts, three colours and black, one ramp placed by form -- light high
on the left, dark massed low and on the right -- flat fills.

Each is typed as its fills; the outline is laid round them (outline()), so
the drawing is the shape and the line never misses a pixel. What stands has
the ground it stands on as its foot (the bottom three rows, as a gravestone's
plinth); the bones lie flat, each pixel on its own row, and are walked over.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, HERE)
from entrance_shapes import Grid, check, stand, outline, depth_layers

# tools/overworld_style.py MATERIALS: foliage, cliff rock, bark, bone -- light, mid, dark
PAL = {'K': '000000',
       'c': '05c43a', 'g': '058f3a', 'G': '235436',     # foliage
       'r': 'b29e5c', 's': '887000', 't': '493712',     # cliff rock
       'w': '605028', 'x': '463422', 'y': '2d230c',     # bark
       'e': 'e8e0c0', 'n': 'b2966a', 'm': '8d6b4f'}     # bone
E = "................"

# fills only, 16 wide and 32 tall; a 16x16 thing uses the bottom cell
FILLS = {
    'saguaro': [E, E, E,
        ".......cgg......",
        "......ccggG..c..",
        "......cgggG.cG..",
        "......cgggG.gG..",
        "...c..cgggG.gG..",
        "..cG..cgggG.gG..",
        "..gG..cgggG.gG..",
        "..gG..cgGgG.gG..",
        "..gG..cgGgG.gG..",
        "..gggggggGG.gG..",
        "..GGGGggggG.gG..",
        "......cgggG.gG..",
        "......cgggG.gG..",
        "......cgggGggG..",
        "......cgggGGGG..",
        "......cgggG.....",
        "......cgggG.....",
        "......cgGgG.....",
        "......cgGgG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......cgggG.....",
        "......gGGGG.....", E],
    'saguaro small': [E, E, E, E, E, E, E, E, E, E,
        "......ccgG......",
        "......cggG......",
        "......cggG......",
        "..cG..cggG......",
        "..gG..cggG......",
        "..gG..cggG......",
        "..gG..cggG......",
        "..gG..cggG......",
        "..gG..cggG......",
        "..gG..cggG......",
        "..ggggcggG......",
        "..GGGGgggG......",
        "......cggG......",
        "......cggG......",
        "......cggG......",
        "......cggG......",
        "......cggG......",
        "......cggG......",
        "......cggG......",
        "......cggG......",
        "......gGGG......", E],
    'barrel cactus': [E] * 21 + [
        "......cggg......",
        "....ccgGggG.....",
        "...ccggGggGg....",
        "...cgggGggGG....",
        "...cgggGggGG....",
        "...ggggGggGG....",
        "...ggggGggGG....",
        "....gggGggGG....",
        ".....ggGgGG.....",
        "......GGGG......", E],
    'prickly pear': [E] * 16 + [
        "...ccgg.........",
        "..ccggggG.......",
        "..cgggggG.ccgG..",
        "..cggggGG.cggG..",
        "..cggggGG.cggG..",
        "..ggggGGG.cggG..",
        "..gggGGGG.gggG..",
        "...KKKKK..KKKK..",
        "....cggggggGG...",
        "...ccgggggGGGG..",
        "...cggggggGGGG..",
        "...cggggggGGGG..",
        "...gggggggGGGG..",
        "....ggggGGGGG...",
        ".....GGGGGGG....", E],
    'boulder': [E] * 21 + [
        "......rrss......",
        "....rrrsssst....",
        "...rrssssssst...",
        "...rsssssstsst..",
        "...rssssststtt..",
        "...sssssstsstt..",
        "...ssssssssttt..",
        "...sssssstttt...",
        "....ssstttttt...",
        ".....tttttt.....", E],
    'boulders': [E] * 20 + [
        "....rrss........",
        "...rrsssst......",
        "..rrsssssst.....",
        "..rssssssst.....",
        "..rsssssssst....",
        "..sssssssstt....",
        "..ssssssssKrrs..",
        "..ssssssttKrss..",
        "...sssttttKsst..",
        "....ttttt.Kstt..",
        "..........Kttt..", E],
    'spire': [E, E, E,
        "......rrs.......",
        "....rrrssst.....",
        "....rrsssstt....",
        ".....rssstt.....",
        "......rsst......",
        "......rsst......",
        "......rsst......",
        "......rsst......",
        "......rsstt.....",
        ".....rsssst.....",
        ".....rsssst.....",
        ".....rssstt.....",
        ".....rsstst.....",
        ".....rsstst.....",
        ".....rsstst.....",
        ".....rssstt.....",
        ".....rssstt.....",
        ".....sssstt.....",
        ".....sssstt.....",
        ".....sssstt.....",
        ".....sssstt.....",
        ".....sssstt.....",
        "....rssssstt....",
        "....rssssstt....",
        "....sssssstt....",
        "...sssssssttt...",
        "...ssssstttttt..",
        "....ttttttttt...", E],
    'shrub': [E] * 23 + [
        ".....wwx..x.....",
        "....wwxxx.xx....",
        "...wwxxxxxxxy...",
        "...wxxxyxxxyy...",
        "...xxxyxxxyxy...",
        "...xxxxxyxxyyy..",
        "....xxyxxyyyy...",
        ".....yyyyyyy....", E],
    # the Grootslang's skull (enemy 27, an elephant's head on a serpent): the
    # dome, the sockets, the trunk's nasal hole, the tusks curving forward
    'skull': [E] * 18 + [
        ".....eeeen......",
        "....eeennnnm....",
        "...eennnnnnnm...",
        "...enKKnnKKnm...",
        "...enKKnnKKnm...",
        "...ennnnnnnnm...",
        "..eennnKKnnnmm..",
        "..en.nnKKnn.mm..",
        "..en.nnKKnn.mm..",
        "..en..nnnn..mm..",
        "..nn..nnnn..mm..",
        "...n..mmmm..m...",
        "...nn......mm...", E],
    # the Olgoi-Khorkhoi's bones (enemy 23, the death worm): one coil of its
    # spine rising out of the sand as the living worm's does, the ribs hanging
    # from it
    'ribs': [E] * 10 + [
        "......eeee......",
        "....eeeennnn....",
        "...eeennKKnnm...",
        "...eenKKKKKnm...",
        "..eenKKKKKKnmm..",
        "..enKKKKKKKKnm..",
        "..enKKKKKKKKnm..",
        "..en.n.KK.n.nm..",
        "..en.n.KK.n.nm..",
        "..nn.n....n.mm..",
        "..nm........mm..",
        "..nm........mm..",
        "..nm........mm..",
        "..nm........mm..",
        "..nm........mm..",
        "..nm........mm..",
        "..nm........mm..",
        "..mm........mm..",
        "..mm........mm..",
        "..mm........mm..", E, E],
}
LYING = ('skull',)


def standing(g):
    """Stood on its bottom three rows, end to end (a gravestone's plinth), the
    rest rising from the bottom row's ground line."""
    bottom = max(y for y in range(g.h) if any(c != '.' for c in g.g[y]))
    foot = set()
    for y in range(bottom - 2, bottom + 1):
        xs = [x for x in range(g.w) if g.g[y][x] != '.']
        foot |= {(x, y) for x in range(min(xs), max(xs) + 1)}
    return stand(g, lambda x, y: bottom, foot)


def piece(name):
    rows = FILLS[name]
    assert len(rows) == 32 and all(len(r) == 16 for r in rows), name
    g = Grid(16, 32)
    g.g = [list(r) for r in rows]
    outline(g)
    check(g, 'desert ' + name)
    return stand(g, lambda x, y: y) if name in LYING else standing(g)


def design():
    order = list(FILLS)
    grids = [piece(k) for k in order]
    return {'pal': PAL, 'view_w': 16, 'order': order, 'views': {k: g.rows() for k, g in zip(order, grids)},
            'depth': depth_layers(16 * len(order), 32, [(16 * i, 0, g) for i, g in enumerate(grids)])}


if __name__ == '__main__':
    d = design()
    json.dump(d, open(sys.argv[1], 'w'))
    for k in d['order']:
        print(k)
        for r in d['views'][k]:
            print('  ' + r)
