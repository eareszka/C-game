"""A wall torch (user: caves and ruins have torches; the catacombs none for
now): a bronze cup on a wooden handle, its flame in six frames -- it gutters
left, sinks low, gutters right.

    python art/structures/dungeon_walls/torch_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/torch
    then copy torch.png to assets/torch.png

Views 16 apart, each 16 x 32: the flame in the upper cell (rows 4-15), the cup
and handle in the lower (rows 16-27) -- four colours a cell. A drawn thing, not
a texture: outlined black, as the sprites are.

Nothing in it is a wall's tone (user: "the torches should match the them of the
dungeon but not look exactly like the stone or walls"). The flame is drawn as
fire; the game shows the upper cell's three tones in a dungeon's own flame
colours, lightest for lightest (torch_tex in src/dungeon.cpp: the ruins fire,
a green cave white). It reads how many frames there are off the sheet's width,
and sizes each frame's glow by how tall its flame is.
"""
import json, sys

PAL = {'K': '000000', 'Y': 'f4ce80', 'G': 'd89830', 'R': 'b6433d',   # the flame: heart, body, edge
       'I': 'c18a39', 'W': '967448', 'V': '785830'}                  # the cup, bronze; the handle, wood and its shade

CENTRE = ["................",
          ".......KK.......",
          "......KRRK......",
          "......KRRK......",
          ".....KRGGRK.....",
          ".....KRGGRK.....",
          "....KRGGGGRK....",
          "....KRGYYGRK....",
          "....KRGYYGRK....",
          "....KRGYYGRK....",
          "....KRGYYGRK....",
          "....KRRGGRRK...."]
LEAN = ["................",
        "......KK........",
        "......KRK.......",
        "......KRRK......",
        ".....KRGGRK.....",
        ".....KRGGRK.....",
        "....KRGGGGRK....",
        "....KRGYYGRK....",
        "....KRGYYGRK....",
        "....KRGYYGRK....",
        "....KRGYYGRK....",
        "....KRRGGRRK...."]
TALL = [".....KK.........",
        ".....KRK........",
        ".....KRRK.......",
        "......KRRK......",
        ".....KRGGRK.....",
        "....KRGGGRK.....",
        "....KRGGGGRK....",
        "....KRGYYGRK....",
        "....KRGYYGRK....",
        "....KRGYYGRK....",
        "....KRGYYGRK....",
        "....KRRGGRRK...."]
SHORT = ["................",
         "................",
         "................",
         ".......KK.......",
         "......KRRK......",
         ".....KRGGRK.....",
         "....KRGGGGRK....",
         "...KRGGYYGGRK...",
         "...KRGYYYYGRK...",
         "...KRGYYYYGRK...",
         "....KRGYYGRK....",
         "....KRRGGRRK...."]
flip = lambda f: [r[::-1] for r in f]
FLAME = [CENTRE, LEAN, TALL, SHORT, flip(LEAN), flip(TALL)]
HOLD = ["....KKKKKKKK....",
        "....KIIIIIIK....",
        ".....KIIIIK.....",
        "......KKKK......",
        "......KWVK......",
        "......KWVK......",
        "......KWVK......",
        "......KWVK......",
        "......KWVK......",
        "......KWVK......",
        "......KWVK......",
        ".......KK......."]


def design():
    views = {'flame_%d' % i: ['.' * 16] * 4 + f + HOLD + ['.' * 16] * 4 for i, f in enumerate(FLAME)}
    for name, rows in views.items():                         # four colours a cell
        assert len(rows) == 32 and all(len(r) == 16 for r in rows), name
        for cy in (0, 16):
            assert len({c for r in rows[cy:cy + 16] for c in r} - {'.'}) <= 4, (name, cy)
    return {'pal': PAL, 'view_w': 16, 'order': list(views), 'views': views}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
