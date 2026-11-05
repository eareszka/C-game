"""85 Nanabolele's eyes to the bible's tiny marks (the user, 2026-10-29: eyes consistent across every enemy;
PixelLab's were rendered eyeballs -- a black ring, orange iris, white glint, a brown pixel). As the approved
enemies on dark hide do (63 Hidebehind, 78 Zankallala): each eye one solid 2 px mark of its accent orange,
the brow line above kept, the ring and glints filled with the skin's dark green.
Run after views.py; rewrites the views in place.

    python art/enemies/pixellab/85_nanabolele/eyes.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
EYE, SKIN = (0xfc, 0x98, 0x38, 255), (0x14, 0x2e, 0x1f, 255)
# per view: (box to clear, x0, y0, x1, y1 inclusive), then the eye's mark pixels
FIX = {'idle_frame0_clean.png': [((43, 36, 43, 37), [(43, 36), (43, 37)]),        # head on: each eye 1x2, in its socket
                                 ((53, 36, 54, 38), [(54, 36), (54, 37)])],
       'idle_view_DR.png': [((68, 34, 72, 36), [(68, 34), (69, 34)])],
       'idle_view_R.png': [((75, 34, 79, 36), [(75, 34), (76, 34)])]}
for f, eyes in FIX.items():
    im = Image.open(HERE / f).convert('RGBA')
    px = im.load()
    for (x0, y0, x1, y1), mark in eyes:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if px[x, y][3]:
                    px[x, y] = SKIN
        for p in mark:
            px[p] = EYE
    im.save(HERE / f)
    print(f, 'eyes set')
