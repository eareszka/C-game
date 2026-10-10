"""The item icons in their colours: assets/items.png.

    python art/items/gen_items.py [out.png]

items.aseprite (exported beside it as items.png) holds one 16x16 drawing per
kind of icon, in the stone key tones -- see items_design.py. Each column of the
sheet is that drawing with the key swapped for a ramp of the game's ore tones
(TONES in art/structures/gen_cave_entrances.py, all palette colours), so the
ore lump comes out once per ore. Columns follow `enum Item` in
include/crafting.h.
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "art", "structures"))
sys.path.insert(0, HERE)
from gen_cave_entrances import TONES, DEFAULT
from items_design import ORDER

ART = os.path.join(HERE, "items.png")
OUT = os.path.join(ROOT, "assets", "items.png")
T = dict(TONES)
# White fur: line, then the stone ramp's base and lit as shade and base, and
# the palette's white as its light -- all palette colours.
WHITE = [T["stone"][0], T["stone"][2], T["stone"][3], (252, 252, 252)]

# (drawing, ramp) per column, in enum Item order.
COLUMNS = [
    ("wood", DEFAULT), ("ore", T["stone"]), ("gold", T["kharvite"]),
    ("flower", T["dravium"]), ("gravestone", T["stone"]), ("oilbloom", T["bronze"]),
    ("hide", T["bronze"]), ("bone", T["stone"]), ("essence", T["reality_shard"]),
] + [("ore", T[n]) for n in ("bronze", "emerald", "veyrite", "dravium", "kharvite", "reality_shard")] + [
    ("vine", T["emerald"]), ("raft_book", T["bronze"]), ("raft", T["bronze"]),
    ("spearhead", T["stone"]), ("moon_steel", T["veyrite"]), ("reapers_edge", T["reality_shard"]),
    # The weapon books: the raft book's drawing, each in its own cover.
    ("raft_book", T["dravium"]), ("raft_book", T["veyrite"]), ("raft_book", T["reality_shard"]),
    # The feather Qique drops, in its purple; the polar bear king's white fur,
    # the hide's drawing in WHITE; the sleeping bag in the hide's leather.
    ("feather", T["reality_shard"]), ("hide", WHITE), ("sleeping_bag", T["bronze"]),
]


def main(out=OUT):
    art = Image.open(ART).convert("RGBA")
    key = T["stone"]
    sheet = Image.new("RGBA", (16 * len(COLUMNS), 16))
    for col, (name, ramp) in enumerate(COLUMNS):
        cell = art.crop((ORDER.index(name) * 16, 0, ORDER.index(name) * 16 + 16, 16))
        px = cell.load()
        for y in range(16):
            for x in range(16):
                r, g, b, a = px[x, y]
                if a and (r, g, b) in key:
                    px[x, y] = tuple(ramp[key.index((r, g, b))]) + (255,)
        sheet.paste(cell, (col * 16, 0))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("wrote", out, "(%dx%d)" % sheet.size)


if __name__ == "__main__":
    main(*sys.argv[1:2])
