"""The weapon icons in every ore: assets/weapon_icons.png.

    python art/items/gen_weapon_icons.py [out.png]

weapons.aseprite (exported beside it as weapons.png) is drawn through the
pixel plugin from weapons_design.py: one 16x16 weapon per column, WeaponType
order, its metal in the four stone tones and its wood in fixed browns. Each
ore's row is that drawing with the stone tones swapped for the ore's ramp
(TONES in art/structures/gen_cave_entrances.py) -- the same swap as the battle
shots, so a weapon's icon is the colour of the shots it fires. The sheet:

    row m (Material order), column w (WeaponType order)   16x16 each
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "art", "structures"))
from gen_cave_entrances import TONES

ART = os.path.join(HERE, "weapons.png")
OUT = os.path.join(ROOT, "assets", "weapon_icons.png")


def main(out=OUT):
    art = Image.open(ART).convert("RGBA")
    stone = TONES[0][1]
    sheet = Image.new("RGBA", (art.width, art.height * len(TONES)))
    for m, (name, tones) in enumerate(TONES):
        row = art.copy()
        px = row.load()
        for y in range(row.height):
            for x in range(row.width):
                r, g, b, a = px[x, y]
                if a and (r, g, b) in stone:
                    px[x, y] = tuple(tones[stone.index((r, g, b))]) + (255,)
        sheet.paste(row, (0, m * art.height))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("wrote", out, "(%dx%d)" % sheet.size)


if __name__ == "__main__":
    main(*sys.argv[1:2])
