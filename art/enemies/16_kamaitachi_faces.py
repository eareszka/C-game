"""16 Kamaitachi: the user's front face and shading carried to the 3/4 and side views.

    python art/enemies/16_kamaitachi_faces.py assets/enemies/16_kamaitachi.png

The user redrew the front head (2026-10-10): no grey cap on top, two slanted eyes of three pixels, a
one-pixel mouth. "Including the side views too. Remember the bible rules." So, on every frame that is not
the front view (frames 0-2 are theirs and are left alone):
- shading by form (SPRITE_STYLE.md): the ermine is white, and shaded only on its underside -- the two
  pixels above its lower outline, under body, chin and tail. The grey that lay along the tops of its head
  and back is gone;
- the 3/4 views get the front's two eyes and mouth, the side views one eye and the mouth, drawn the same
  way; the back views have no face.
The sheet is 8 directions x 3 frames of 45x47; a view's frames differ by where the head rides, found by
matching the head's outline."""
import sys
from PIL import Image
W, H = 45, 47
K, WHITE, GREY = (0, 0, 0, 255), (0xfc, 0xfc, 0xfc, 255), (0xc6, 0xcc, 0xda, 255)
BODY_ROWS = 25                                    # the ermine is above this row; below are the sickles' blades and the whirlwind
# per view: its first frame, the head's box there, the old face pixels to clear, the new face
FACES = {
    'DR': (3, (24, 6, 37, 21), [(27, 15), (31, 15), (32, 16), (30, 18)],
           [(27, 15), (27, 16), (28, 16), (31, 15), (31, 16), (30, 16), (29, 18)]),
    'R':  (6, (27, 8, 40, 23), [(34, 14), (35, 16)], [(34, 15), (34, 16), (35, 16), (36, 18)]),
}
MIRROR = {'DL': ('DR', 21), 'L': ('R', 18)}       # the left views are stored too: the same, mirrored

def run(path):
    im = Image.open(path).convert('RGBA'); px = im.load()
    def offset(i, base, box, flip):
        """How far frame i's head is from where it is in the view's first frame."""
        bx = (W - box[2], box[1], W - box[0], box[3]) if flip else box
        best = None
        for dy in range(-4, 5):
            for dx in range(-3, 4):
                bad = sum(1 for y in range(bx[1], bx[3]) for x in range(bx[0], bx[2])
                          if 0 <= x + dx < W and 0 <= y + dy < H and
                          (px[base * W + x, y][3] > 0) != (px[i * W + x + dx, y + dy][3] > 0))
                if best is None or bad < best[0]: best = (bad, dx, dy)
        return best[1], best[2]
    plans = [(v, f0, box, old, new, False) for v, (f0, box, old, new) in FACES.items()]
    plans += [(v, f0, FACES[src][1], FACES[src][2], FACES[src][3], True) for v, (src, f0) in MIRROR.items()]
    offs = {(f0 + k): offset(f0 + k, f0, box, flip) for v, f0, box, old, new, flip in plans for k in range(3)}   # before anything is changed
    # shading: every frame but the front's three
    for i in range(3, im.width // W):
        for y in range(BODY_ROWS):
            for x in range(W):
                if px[i * W + x, y] == GREY: px[i * W + x, y] = WHITE
        for x in range(W):
            for y in range(BODY_ROWS - 1):
                if px[i * W + x, y] == WHITE and px[i * W + x, y + 1] == K and px[i * W + x, y + 2] != WHITE:
                    for q in (y, y - 1):
                        if q >= 0 and px[i * W + x, q] == WHITE: px[i * W + x, q] = GREY
    # faces
    for v, f0, box, old, new, flip in plans:
        for k in range(3):
            dx, dy = offs[f0 + k]
            at = lambda p: ((f0 + k) * W + ((W - 1 - p[0]) if flip else p[0]) + dx, p[1] + dy)
            for p in old:
                x, y = at(p)
                if px[x, y] == K: px[x, y] = WHITE
            for p in new: px[at(p)] = K
            print(v, 'frame', k, 'head rides', (dx, dy))
    im.save(path)

if __name__ == '__main__':
    run(sys.argv[1])
