"""The wasteland's causeways: the bridges' deck in stone (the user, 2026-10-27,
the wasteland overhaul; the mock-up art/concept/wasteland/).

    python tools/stone_deck.py          then  python tools/palette_pass.py --write

The deck over the void is the deck over water -- the same cells, the same
geometry, the same floor -- in the maze's stone instead of the graveyard's
planks. tools/town1_layout.py bakes the planks into the sheet's row
TOWN1_DECK_ROW0 (192); this copies that row into the row below it (193) with
the wood's three tones swapped for stone's (lit, base, dark), black kept.
The game draws a deck cell from the row below wherever the deck stands in the
wasteland (src/tilemap.cpp, stone_deck_at). town1_layout.py --write clears
rows 192-193, so run this again after it.
"""
import os
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SHEET = os.path.join(ROOT, 'assets', 'tileset.png')
DECK_ROW0, COLS, T = 192, 256, 16
WOOD_TO_STONE = {(0x96, 0x74, 0x48): (0x97, 0x97, 0xaa),     # wood's lit -> stone's lit (waste stone)
                 (0x78, 0x58, 0x30): (0x59, 0x59, 0x65),     # its base -> base
                 (0x49, 0x37, 0x12): (0x34, 0x34, 0x3e)}     # its dark -> dark

if __name__ == '__main__':
    sheet = Image.open(SHEET).convert('RGBA')
    row = sheet.crop((0, DECK_ROW0 * T, COLS * T, (DECK_ROW0 + 1) * T))
    q = row.load()
    left = set()
    for y in range(row.height):
        for x in range(row.width):
            p = q[x, y]
            if p[:3] in WOOD_TO_STONE:
                q[x, y] = WOOD_TO_STONE[p[:3]] + (p[3],)
            elif p[3] and p[:3] not in ((0, 0, 0), (255, 0, 0)):
                left.add(p[:3])
    assert not left, 'colours in the deck that are neither wood nor black: %s' % left
    sheet.paste(row, (0, (DECK_ROW0 + 1) * T))
    sheet.save(SHEET)
    print('stone deck written to row %d' % (DECK_ROW0 + 1))
