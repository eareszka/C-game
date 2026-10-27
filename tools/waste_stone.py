"""The wasteland's built stone a step darker (the user, 2026-10-27, the
wasteland overhaul, stage 2; the mock-up art/concept/wasteland/).

    python tools/waste_stone.py          then  python tools/palette_pass.py --write

The catacombs' stone yard walls and the ruins entrance stand in other biomes
too, so their own cells stay as they are: this copies them, recoloured to
waste stone, into empty rows of the sheet, and the game draws the copy for a
cell standing in the wasteland (src/tilemap.cpp, art_src). The copies sit
outside every generator's band (rows 194-200, from col 24), so nothing else
writes there; run this again after gen_entrance_art.py --stamp moves the
originals, and update WASTE_COPIES in src/tilemap.cpp to match.
"""
import os
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SHEET = os.path.join(ROOT, 'assets', 'tileset.png')
T = 16
STONE_TO_WASTE = {(0xc6, 0xcc, 0xda): (0x97, 0x97, 0xaa),    # stone's lit -> waste stone's lit
                  (0x97, 0x97, 0xaa): (0x59, 0x59, 0x65),    # its base -> base
                  (0x59, 0x59, 0x65): (0x34, 0x34, 0x3e)}    # its dark -> dark
# (col, row, w, h) of the original -> (col, row) of its copy; as WASTE_COPIES in src/tilemap.cpp
COPIES = [((101, 20, 16, 2), (24, 199)),     # the stone yard walls: 16 pieces, two cells tall
          ((0, 20, 6, 5), (40, 194)),        # the large ruins
          ((6, 20, 3, 3), (46, 194))]        # the small ruins

if __name__ == '__main__':
    sheet = Image.open(SHEET).convert('RGBA')
    for (c, r, w, h), (dc, dr) in COPIES:
        block = sheet.crop((c * T, r * T, (c + w) * T, (r + h) * T))
        q = block.load()
        left = set()
        for y in range(block.height):
            for x in range(block.width):
                p = q[x, y]
                if p[:3] in STONE_TO_WASTE:
                    q[x, y] = STONE_TO_WASTE[p[:3]] + (p[3],)
                elif p[3] and p[:3] not in ((0, 0, 0), (255, 0, 0)):
                    left.add(p[:3])
        assert not left, 'colours in %s that are neither stone nor black: %s' % ((c, r), left)
        sheet.paste(block, (dc * T, dr * T))
        print('copied (%d,%d %dx%d) to (%d,%d)' % (c, r, w, h, dc, dr))
    sheet.save(SHEET)
