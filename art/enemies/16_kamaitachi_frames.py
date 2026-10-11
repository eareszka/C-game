"""16 Kamaitachi: each view's frames 1 and 2 remade from its frame 0, above the whirlwind.

    python art/enemies/16_kamaitachi_frames.py SHEET.png

Enlarging the old sheet (16_kamaitachi_grow.py) rounded each frame on its own, so small things -- ears, the
face -- came out a different shape on frame 1 than on frame 0, and carrying the user's edits across by
offset left holes. A view's three frames are the same ermine: on frame 1 it rides the gust a pixel higher,
on frame 2 it is where it was. So rows above SPLIT of frames 1 and 2 are frame 0's rows (a pixel up for
frame 1); from SPLIT down each frame keeps its own whirlwind and sickles (and its belly, shaded as frame 0's is). Frame 0 of every view is untouched.
The sheet is 8 directions x 3 frames of 45x47."""
import sys
from PIL import Image
W, H, SPLIT, BELLY = 45, 47, 20, 25           # the ermine's own rows end at BELLY; below are sickles and whirlwind
GREY, WHITE = (0xc6, 0xcc, 0xda, 255), (0xfc, 0xfc, 0xfc, 255)
RIDE = {1: -1, 2: 0}

def run(path):
    im = Image.open(path).convert('RGBA'); src = im.copy()
    for d in range(im.width // (3 * W)):
        base = src.crop((d * 3 * W, 0, d * 3 * W + W, H))
        for k, dy in RIDE.items():
            x0 = (d * 3 + k) * W
            im.paste((0, 0, 0, 0), (x0, 0, x0 + W, SPLIT))
            im.paste(base.crop((0, -dy, W, SPLIT - dy)), (x0, 0))
            # Just under SPLIT the frame's own body carries on, with the shading it had: a grey pixel there stays
            # only where frame 0 is grey too -- else frame 1 alone had a grey band across its belly, flickering.
            px = im.load(); b = base.load()
            for y in range(SPLIT, BELLY):
                for x in range(W):
                    if px[x0 + x, y] == GREY and not (0 <= y - dy < H and b[x, y - dy] == GREY): px[x0 + x, y] = WHITE
    im.save(path)

if __name__ == '__main__':
    run(sys.argv[1])
