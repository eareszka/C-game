"""Battle sheets moved onto the bible's colours after the lineup review of 2026-10-29 (the user: "fix 26 and
colour count"). Reinstalls each sheet through enemy_sheet.install (its .aseprite repacked, the build recorded); the
folds only remove colours, so running it again changes nothing.

26 Akhekh: all eight of its colours were off the game palette -- each to its nearest game colour, but the teal
   of its wings to the light blue (the nearest, a pale mint, washed the wings out).
9 Questing Beast: eleven colours -- its belly tan into its legs' olive, the brown shade and the dark-green spots
   on its neck into the body's spot brown (its walk sheet too).
51 Aspidochelone: ten -- the shell's mid brown into its dark brown, the island's vivid green into its mid green.
64 Dungavenhooter: nine -- the pink of its nostrils into its dark brown.

    python art/enemies/colour_folds.py
"""
from pathlib import Path
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

LAYOUT = {p: (f, r) for p, f, r in enemy_sheet.battle_sheets()}
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
FOLDS = {
    'assets/enemies/redraws/26_akhekh.png': {'e0c088': 'cebe82', '4c9c50': '4fa667', '2c5cc8': '2850a0', '3cbcb4': '5c94fc',
                                             'd8a800': 'f0bc3c', '3c2c20': '463422', 'b89858': 'b29e5c', 'b71c00': 'b70000'},
    'assets/enemies/09_questing_beast.png': {'967448': '876a1f', '463422': '3c2412', '14301f': '3c2412'},
    'assets/enemies/09_questing_beast_walk.png': {'967448': '876a1f', '463422': '3c2412', '14301f': '3c2412'},
    'assets/enemies/redraws/51_aspidochelone.png': {'633e1b': '463422', '058f3a': '4fa667'},
    'assets/enemies/redraws/64_dungavenhooter.png': {'ec8476': '362a0e'},
}
for path, fold in FOLDS.items():
    im = Image.open(ROOT / path).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            k = '%02x%02x%02x' % p[:3]
            if p[3] and k in fold:
                px[x, y] = h(fold[k]) + (255,)
    frames, rows = LAYOUT[path]
    png = str(ROOT / path)
    enemy_sheet.built(png)     # the sheet as it stands is ours, not a hand edit to keep
    enemy_sheet.install(im, png, frames, rows, ms=250, palette=sorted('%02x%02x%02x' % c for c in {q[:3] for q in im.get_flattened_data() if q[3]}))
    print(path, len({q[:3] for q in im.get_flattened_data() if q[3]} - {(0, 0, 0)}), 'colours + black')
