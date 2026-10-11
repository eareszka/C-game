"""Paint the Dajna's top row onto its built sheet.

    python art/enemies/30_dajna_top_row.py SHEET.png 30_dajna_top_row.json [unmirrored]

build_enemy.py always leaves a frame's top row empty, and the pyramid the user
drew reaches it. 30_dajna_design.py writes 30_dajna_top_row.json ([[x, "rrggbb"], ...] a
frame); this sets those pixels in row 0 of every frame, in each of the 8
direction rows (the sheet is one row a direction, 8 frames of 302x166)."""
import json, sys
from PIL import Image
W, H = 302, 166
im = Image.open(sys.argv[1]).convert('RGBA'); top = json.load(open(sys.argv[2])); n = 0
mirrored = 'unmirrored' not in sys.argv[3:]           # pass 'unmirrored' once every direction row holds the same frames
for d in range(8):
    for f, px in enumerate(top):
        for x, h in px:
            if d in (5, 6, 7) and mirrored: x = W - 1 - x          # a built sheet's left-facing rows are mirrors
            im.putpixel((f * W + x, d * H), tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)); n += 1
im.save(sys.argv[1]); print('top-row pixels painted:', n)
