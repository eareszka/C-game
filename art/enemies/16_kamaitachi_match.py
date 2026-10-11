"""Make the rest of the Kamaitachi's frames follow the user's front frame (frame 0 of the .aseprite)."""
import sys
from PIL import Image
W, H = 45, 47
GREY, WHITE = (0xc6, 0xcc, 0xda, 255), (0xfc, 0xfc, 0xfc, 255)
user = Image.open('s.png').convert('RGBA'); mine = Image.open('../mid.png').convert('RGBA')
fr = lambda im, i: im.crop((i * W, 0, (i + 1) * W, H))
key = lambda p: (p[3], p[:3] if p[3] else 0)
u0, m0 = fr(user, 0), fr(mine, 0)
changed = [(x, y) for y in range(H) for x in range(W) if key(u0.getpixel((x, y))) != key(m0.getpixel((x, y)))]
xs = [x for x, y in changed]; ys = [y for x, y in changed]
box = (min(xs) - 3, min(ys) - 3, max(xs) + 4, max(ys) + 4)                 # the head, as they redrew it
out = user.copy()
# 1. the grey cap is gone from the top of their head (shade belongs underneath, not on top): gone from the top of
#    everything, in every frame -- a grey pixel that, going straight up through grey, comes to the outline or the
#    open air. Grey lower down (under the body, between the haunch and the back) says what is in front of what: kept.
px = out.load(); n_grey = 0
K = (0, 0, 0, 255)
for i in range(out.width // W):
    for x in range(i * W, (i + 1) * W):
        for y in range(H):
            if px[x, y] != GREY: continue
            yy = y
            while yy >= 0 and px[x, yy] == GREY: yy -= 1
            if yy < 0 or px[x, yy][3] == 0 or px[x, yy] == K:
                for q in range(yy + 1, y + 1):
                    if px[x, q] == GREY: px[x, q] = WHITE; n_grey += 1
# 2. the other frames of the same drawing (front idle 1 and 2, and the back's three, which share its head's outline):
#    find where the head sits in each, and make the same changes there
def offset(i):
    f = fr(mine, i); best = None
    for dy in range(-4, 5):
        for dx in range(-3, 4):
            bad = sum(1 for y in range(box[1], box[3]) for x in range(box[0], box[2])
                      if 0 <= x + dx < W and 0 <= y + dy < H and (m0.getpixel((x, y))[3] > 0) != (f.getpixel((x + dx, y + dy))[3] > 0))
            if best is None or bad < best[0]: best = (bad, dx, dy)
    return best
for i in (1, 2):
    bad, dx, dy = offset(i)
    for (x, y) in changed: out.putpixel((i * W + x + dx, y + dy), u0.getpixel((x, y)))
    print('front frame', i, 'head offset', (dx, dy), 'outline mismatch', bad)
out.save('matched.png')
print('grey pixels turned white:', n_grey, '| pixels changed in frame 0 by the user:', len(changed), 'box', box)
bg = Image.new('RGBA', (W * 6, H * 4), (0, 0, 0, 255))
for i in range(24): bg.alpha_composite(fr(out, i), ((i % 6) * W, (i // 6) * H))
bg.resize((bg.width * 4, bg.height * 4), Image.NEAREST).save('matched_view.png')
