"""The player's battle shots in every ore: assets/battle/player_shots.png.

    python art/battle/gen_shots.py [out.png]

shots.aseprite (exported beside it as shots.png) is drawn through the pixel
plugin from shots_design.py: one 16x16 shot per weapon, WeaponType order, in the
stone base and lit tones and the palette's white. Each ore's row is that
drawing with the two stone tones swapped for the ore's (TONES in
art/structures/gen_cave_entrances.py) -- so a shot is the colour of the weapon
that fired it -- and the white left white. The sheet:

    row m (Material order), column w (WeaponType order)   16x16 each
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "art", "structures"))
from gen_cave_entrances import TONES

ART = os.path.join(HERE, "shots.png")
OUT = os.path.join(ROOT, "assets", "battle", "player_shots.png")


def main(out=OUT):
    art = Image.open(ART).convert("RGBA")
    stone = TONES[0][1]
    key = {stone[2]: 2, stone[3]: 3}   # base, lit
    sheet = Image.new("RGBA", (art.width, art.height * len(TONES)))
    for m, (name, tones) in enumerate(TONES):
        row = art.copy()
        px = row.load()
        for y in range(row.height):
            for x in range(row.width):
                r, g, b, a = px[x, y]
                if a and (r, g, b) in key:
                    px[x, y] = tuple(tones[key[(r, g, b)]]) + (255,)
        sheet.paste(row, (0, m * art.height))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("wrote", out, "(%dx%d)" % sheet.size)


if __name__ == "__main__":
    main(*sys.argv[1:2])
