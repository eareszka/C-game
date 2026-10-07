"""The game's cryptids as the Mayan pyramid's carvers would cut them: each
drawn by hand from its battle sprite (art/enemies/NN_views.png, side view)
but restyled, not copied -- heavy outline, a spiral eye, the body in banded
segments and dots, scrolls for breath and fins -- in the step pyramid's grey
stone: K line, D carved line, S shaded stone, M lit relief, '.' the wall.

    python art/structures/dungeon_walls/maya_cryptids_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/maya_cryptids
    python art/structures/dungeon_walls/maya_cryptids_design.py <design.json> desert
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/desert_cryptids
    SMALL: drawn and outlined with the plugin's own tools (see SMALL below)

Each view is 32 x 20; maya_murals.py carves them into the walls.
"""
import json, sys

PAL = {'K': '000000', 'D': '595965', 'M': 'c6ccda', 'S': '9797aa'}

CRYPTIDS = {
    # the Vatnaormur: a sea serpent in three humps, spines on each, its head
    # raised and jaws open at the right
    'vatnaormur': [
        "........................KKKK....",
        ".......................KMMMMK...",
        "......................KMKKMMMK..",
        "......................KMKMMDDDK.",
        ".....K.........K......KMMMMK.KK.",
        "....KMK.......KMK....KMMDMMK....",
        "...KMDMK.....KMDMK..KMMMMMK.....",
        "..KMMMMMK...KMMMMMK.KMDMMK......",
        ".KMDMMDMMK.KMDMMDMMKMMMMK.......",
        "KMMMKKMMMMKMMMKKMMMMMDMK........",
        "KMDK..KMDMMMDK..KMDMMMK.........",
        "KMMK..KMMMMMMK..KMMMMK..........",
        "KMDK..KMDKKMDK..KMDMMK..........",
        "KMMK..KMMK.KMMK.KMMMMK..........",
        "KMDK..KMDK.KMDK.KMDMMK..........",
        "KMMK..KMMK.KMMK.KMMMMK..........",
        "KSSK..KSSK.KSSK.KSSSSK..........",
        ".KK....KK...KK...KKKK...........",
        "................................",
        "................................"],
    # the Grootslang: an elephant's head and tusk on a serpent's coils
    'grootslang': [
        "...............KKKKKKK..........",
        ".............KKMMMMMMMKK........",
        "............KMMMMMMMMMMMK.......",
        "...........KMMKKKMMMMDMMMK......",
        "...........KMKMMKMMMMMMMMK......",
        "...........KMKKMKMMMMKKMMMK.....",
        "....KK.....KMMMMMMMMK..KMMK.....",
        "...KMMK.....KMMMMMMK...KMMK.KK..",
        "...KMDK......KMMDMK....KMDMKMMK.",
        "...KMMK.......KMMMK.....KMMMMK..",
        "...KMDK.......KMDMK......KKKK...",
        "...KMMKKKKKKKKMMMMMKKKK.........",
        "..KMDMDMDMDMDMDMDMDMDMMK........",
        ".KMMMMMMMMMMMMMMMMMMMMMMK.......",
        "KMDMDMDMDMDMDMDMDMDMDMDMDK......",
        "KMMMMMMMMMMMMMMMMMMMMMMMMK......",
        ".KSSSSSSSSSSSSSSSSSSSSSSK.......",
        "..KKKKKKKKKKKKKKKKKKKKKK........",
        "................................",
        "................................"],
    # the Olgoi-Khorkhoi: the death worm arched, its round mouth ringed in teeth
    'olgoi': [
        "..KKKKK.........................",
        ".KMDMDMK........................",
        "KMDKKKDMK.......................",
        "KDKMKMKDK.......................",
        "KMKKMKKMK.......................",
        "KDKMKMKDK.....KKKKKK............",
        "KMDKKKDMK...KKMMMMMMKK..........",
        ".KMDMDMK...KMMDMDMDMMMK.........",
        "..KMMMK...KMMDMMMMMDMMMK........",
        "..KMDMK..KMMDMKKKKKMDMMMK.......",
        "..KMMMK..KMDMK.....KMDMMK.......",
        "..KMDMK.KMMDMK.....KMMDMK.......",
        "..KMMMKKMMDMK.......KMDMMK......",
        "..KMDMMMMDMK........KMMDMK......",
        "...KMMDMMMK.........KMDMMK......",
        "....KKMMMK..........KMMDMK......",
        ".....KSSK...........KSSSSK......",
        "......KK.............KKKK.......",
        "................................",
        "................................"],
    # the Myrmecoleon: a maned lion's forequarters on an ant's body and legs
    'myrmecoleon': [
        "...................KKKKK........",
        ".................KKDMDMDKK......",
        "................KDMDKKKMDMK.....",
        "...............KMDKMMMMKKMMKKK..",
        "...............KDMKMKMMMMMMMMMK.",
        "....KKKKK......KMDKMMMMMMKKKKK..",
        "...KMDMDMK.....KDMKMMMMMMMMK....",
        "..KMMMMMMMK.....KMDKKMMMMMK.....",
        "..KMDMDMDMKKKKKKKMDMMKKKKK......",
        "..KMMMMMMMMMDMDMMMMMMMK.........",
        "...KMDMDMKKMMMMMMMMMMMK.........",
        "....KKKKK..KMDMKKKMMMK..........",
        "....K.K.K..KMMK..KMMK...........",
        "...K.K.K...KMDK..KMDK...........",
        "..K.K.K....KMMK..KMMK...........",
        "..K.K.K....KMDK..KMDK...........",
        ".K.K.K....KMMMK.KMMMK...........",
        ".K.K.K....KKKKK.KKKKK...........",
        "................................",
        "................................"],
    # the Beast of the Charred Forests: a long low lizard, a crest of flames
    # down its back, a toothed snout
    'charred_beast': [
        "................................",
        "..........M.M.M.M.M.............",
        ".........KMKMKMKMKMK....KKKKK...",
        "........KMMMMMMMMMMMK..KMKMMMK..",
        ".......KMDMDMDMDMDMDMKKMMMMMMMK.",
        "......KMMMMMMMMMMMMMMMMMMDMDMDK.",
        "....KKMDMDMDMDMDMDMDMMMMKMKMKK..",
        "..KKMMMMMMMMMMMMMMMMMMMMMK......",
        "KKMMMKKMMMMMMMMMKKMMMMMMK.......",
        ".KKK..KMDMK..KKKKKMDMK.KK.......",
        "......KMMK.........KMMK.........",
        "......KDDK.........KDDK.........",
        ".....KKKKK........KKKKK.........",
        "................................",
        "................................",
        "................................",
        "................................",
        "................................",
        "................................",
        "................................"],
    # the Lusca: a shark's forequarters over a mass of octopus arms
    'lusca': [
        ".......KK.......................",
        "......KMMK......................",
        ".....KMMMK......................",
        "....KMMMMMKKKKKKK...............",
        "..KKMMMMMMMMMMMMMKK.............",
        ".KMMMKMMMMMMMMMMMMMKK...........",
        "KMMMMMMMMMMMMMMMMDDDMK..........",
        "KDMDMDMDMMMMMMMMKMKMKK..........",
        ".KMMMMMMMMMMMMMMMMMMK...........",
        "..KKSSSSSSSSSSSSSKKK............",
        "...KMDKMDKMDKMDKMDK.............",
        "...KMMKMMKMMKMMKMMK.............",
        "..KMDKKMDKKMDKKMDKMK............",
        "..KMMK.KMMK.KMMK.KMMK...........",
        ".KMDK..KMDK..KMDK.KMDK..........",
        ".KMK...KMMK..KMMK..KMMK.........",
        "KMDK...KDDK...KMDK..KDK.........",
        "KMMK....KK.....KK....K..........",
        ".KK.............................",
        "................................"],
}


# The desert pyramid's corridors carry the same cryptids as hieroglyphs: the
# same drawings in its sandstone (K line, D the carved brown, M lit sandstone,
# S shaded sandstone), drawn as their own .aseprite.
DESERT_PAL = {'K': '000000', 'D': '785830', 'M': 'f4ce80', 'S': 'b29e5c'}

# Small versions for the Mayan staircase walls, where a carved stone must fit
# whole inside the slanted band (48 high: a stone w wide has 48 - w rows
# clear). The body (M) and its carved lines (D) only -- the outline is cut by
# the pixel plugin's own outline tool (apply_outline, 1px black) when drawn,
# so each comes out 18 x 14.
SMALL = {
    'vatnaormur': [
        ".............MM.",
        "............MMMD",
        "...........MDMM.",
        "..M....M...MM...",
        ".MMM..MMM..MM...",
        "MMDMMMMDMMMMM...",
        "MM..MMM..MMM....",
        "MD..MD...MD.....",
        "MM..MM...MM.....",
        "MD..MD...MD.....",
        "................",
        "................"],
    'grootslang': [
        "......MMMMM.....",
        ".....MMDMMMM....",
        ".....MMMMMMMM...",
        "......MMM..MMD..",
        ".MM....MM...M...",
        ".MD....MD.......",
        ".MMMMMMMMM......",
        "MDMDMDMDMDM.....",
        "MMMMMMMMMMMM....",
        "................",
        "................",
        "................"],
    'olgoi': [
        "MMM.............",
        "MDM.............",
        "MMM.....MMMM....",
        ".M.....MMDDMM...",
        ".MM...MM....MM..",
        "..MM.MM.....MD..",
        "...MMM......MM..",
        "............MD..",
        "................",
        "................",
        "................",
        "................"],
    'myrmecoleon': [
        "...........MMM..",
        "..........MDMMM.",
        "..MMMM....MMMMMM",
        ".MDMDMMMMMMMM...",
        ".MMMMMMMMMM.....",
        "..MMMM.M..M.....",
        "..M.M..M..M.....",
        ".M.M...MM.MM....",
        "................",
        "................",
        "................",
        "................"],
    'charred_beast': [
        "....M.M.M.......",
        "...MMMMMMM...MM.",
        "..MMDMDMDMMMMDMM",
        "MMMMMMMMMMMMMM..",
        "..M.....M.......",
        "..MM....MM......",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................"],
    'lusca': [
        "...M............",
        "..MMMMMMM.......",
        "MMMMMMMMMMD.....",
        "MDMDMMMMMM......",
        ".MMMMMMMM.......",
        ".M.M.M.M.M......",
        "M..M..M..M......",
        "................",
        "................",
        "................",
        "................",
        "................"],
}


def design(variant='maya'):
    for k, rows in CRYPTIDS.items():
        assert len(rows) == 20 and all(len(r) == 32 for r in rows), (k, [len(r) for r in rows])
    for k, rows in SMALL.items():
        assert len(rows) == 12 and all(len(r) == 16 for r in rows), (k, [len(r) for r in rows])
    return {'pal': DESERT_PAL if variant == 'desert' else PAL, 'view_w': 32,
            'order': list(CRYPTIDS), 'views': CRYPTIDS}


if __name__ == '__main__':
    # python maya_cryptids_design.py <design.json> [maya|desert]
    json.dump(design(sys.argv[2] if len(sys.argv) > 2 else 'maya'), open(sys.argv[1], 'w'))
