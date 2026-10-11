"""30 Dajna, giant tier (the size of the sprite it replaces), to
art/direction/SPRITE_STYLE.md: one view, carrying the tileset's pyramid.

    python art/enemies/30_dajna_design.py [FRAME.png]
        FRAME: art/enemies/30_dajna_user_frame.png, the frame the user finished
    writes design.json, 30_dajna.txt, draft.png

The Dajna of Maltese lore, the titanic "thunder camel": in the game the player
touches what looks like a pyramid dungeon and this rises out of the ground --
the pyramid is its hump. One fixed view, the same for every direction.

How it was drawn (2026-10-10). The user asked for the tileset's Egyptian
pyramid as the hump; redrew the camel's silhouette themselves in Aseprite;
this script's earlier versions added elephant feet, a fringe, shadows and, once
they allowed a giant a larger palette, three more steps of shading; and between
those rounds the user went over frame 0 by hand three times (the last: round
eyes, a beard, a shorter tail). That finished frame is 30_dajna_user_frame.png
and is the whole drawing: nothing in it is changed here.

All this script does is make the other seven frames follow it (the user's words:
"have all other ones follow to match", "new tail swing left to right"):
- breathing: everything above the belly sinks a pixel and comes back, the neck
  and head a frame behind the body; legs, feet and fringe stand still;
- the tail hangs free below the rump and swings from its root, left then right,
  one full swing over the 8 frames, widest at the tip;
- its hair sways in the wind with the tail: the skirt under the belly and the
  fringe under the throat, their tips the most ("make sure hair sways in the
  wind too");
The eyes never close (a blink was tried and dropped at the user's word); they are
the user's own, redrawn by them last.
Frame 0 is the user's frame (their last pass kept the broken, grown-in pyramid
an earlier version of this script had made, and reworked it), its shading
flattened to three tones: see flatten().

Then drawn into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io, os, sys, math
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PAL = {'K': '000000', 'D': '605028', 'M': 'b2966a', 'L': 'cebe82', 'W': 'fcfcfc',      # the camel, as the user painted it
       'd': '463422', 'm': '967448', 'H': 'e8e0c0',                                    # in the user's frame; flatten() folds them into D, M and L (H stays in the eyes)
       'S': 'f4ce80', 's': 'b29e5c', 'B': '785830', 'k': '241c0a'}                     # the tileset pyramid's own four
W, H, FRAMES = 302, 166, 8                                # the built frame; its top row is empty, so the drawing is rows 1..165
hexrgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
LETTER = {hexrgb(v): k for k, v in PAL.items()}
PIVOT = 123                                               # the belly line: above it the body breathes
NECK_X = 232                                              # from here right is neck and head: it breathes a frame late
TAIL_TOP, TAIL_RIGHT, SWING = 111, 57, 8                  # the tail hangs free from this row, left of this column; px the tip swings each way
BODY_DIP = (0, 0, 1, 1, 1, 1, 0, 0)

def drawing(path):
    im = Image.open(path).convert('RGBA'); px = im.load()
    assert im.size == (W, H), im.size
    return {(x, y): LETTER[px[x, y][:3]] for y in range(H) for x in range(W) if px[x, y][3]}

# The hair that sways in the wind (the user): each fringe hangs below its root row; (columns, root row,
# lowest row, px its tips move each way). Rows at the root stay put, so nothing tears where a fringe joins
# the body or a leg; the tips move the most. It sways in time with the tail.
HAIR = (((100, 169), 141, 153, 5),                        # the skirt under the belly, between the legs (it stops above the feet)
        ((226, 252), 134, 143, 3))                        # the fringe under the throat

def flatten(g):
    """The hide back to the bible's three tones (the user, after a review against it: "flatten the
    shading"): the half-shade joins the mid tone, the deep shade the shade, the bright rim the light.
    The eyes keep their pale insides. Nothing else of the user's frame is touched."""
    merge = {'m': 'M', 'd': 'D', 'H': 'L'}
    in_eye = lambda p: 263 <= p[0] <= 278 and 55 <= p[1] <= 59
    return {p: (c if in_eye(p) else merge.get(c, c)) for p, c in g.items()}

def tail_of(g):
    """The free-hanging tail: in each row from TAIL_TOP down, the runs of pixels that end left of TAIL_RIGHT."""
    out = set()
    for y in range(TAIL_TOP, H):
        x = 0
        while x < TAIL_RIGHT + 1:
            if (x, y) in g:
                s = x
                while (x, y) in g: x += 1
                if x - 1 < TAIL_RIGHT: out |= {(q, y) for q in range(s, x)}
            else: x += 1
    return out

def frame(g, tail, f):
    low = max(y for x, y in tail)
    sway = math.sin(math.tau * f / FRAMES)
    moved = {p: c for p, c in g.items() if p not in tail}
    for (x, y) in sorted(tail):                           # the tail sheared from its root: no swing at the top, the most at the tip
        dx = round(SWING * sway * ((y - TAIL_TOP) / (low - TAIL_TOP)) ** 1.4)
        moved[(x + dx, y)] = g[(x, y)]
    for (xa, xb), root, low_row, amp in HAIR:             # the fringes: each row slides sideways, further the lower it hangs
        hair = {p: moved[p] for p in moved if xa <= p[0] <= xb and root < p[1] <= low_row}
        shift = {y: round(amp * sway * (y - root) / (low_row - root)) for y in range(root, low_row + 1)}
        for p in hair:
            if shift[p[1]]: del moved[p]
        for (x, y), c in hair.items():
            if shift[y]: moved.setdefault((x + shift[y], y), c)        # behind a leg where it reaches one
    body, neck = BODY_DIP[f], BODY_DIP[f - 1]
    out = {}
    for (x, y), c in moved.items():
        d = neck if x >= NECK_X else body
        if y < PIVOT - d: out[(x, y + d)] = c
        elif y >= PIVOT: out[(x, y)] = c                  # the row at the pivot is swallowed as it sinks
    return out

rows = lambda g: [''.join(g.get((x, y + 1), '.') for x in range(W)) for y in range(H - 1)] + ['.' * W]   # rows 1..165: build_enemy always leaves the top row empty
# The user's pyramid reaches the frame's top row, which a built sheet cannot hold. 30_dajna_top_row.json lists those
# pixels per frame, and art/enemies/30_dajna_top_row.py paints them onto the built PNG afterwards.

if __name__ == '__main__':
    g = flatten(drawing(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '30_dajna_user_frame.png')))
    tail = tail_of(g)
    gs = [frame(g, tail, f) for f in range(FRAMES)]
    assert gs[0] == g, 'frame 0 must be the finished frame exactly'
    json.dump({'pal': PAL, 'view_w': W, 'views': {str(i): rows(q) for i, q in enumerate(gs)}, 'order': [str(i) for i in range(FRAMES)]}, open('design.json', 'w'))
    head = ['#BODY', '90', '#POSE', 'frames', '#DIRS', 'down', '#ROWS']
    t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + head
    for i, q in enumerate(gs): t += ['#D' + (f'@{i}' if i else '')] + rows(q)[:-1]
    io.open('30_dajna.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 4, H * 2), (0, 0, 0, 255))
    for i, q in enumerate(gs):
        for (x, y), c in q.items():
            if 0 <= x < W and 0 <= y < H: im.putpixel(((i % 4) * W + x, (i // 4) * H + y), hexrgb(PAL[c]) + (255,))
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save('draft.png')
    json.dump([[[x, PAL[c]] for (x, y), c in sorted(q.items()) if y == 0] for q in gs], open('30_dajna_top_row.json', 'w'))
    out = {p for q in gs for p in q if not (0 <= p[0] < W and 0 <= p[1] < H)}
    assert not out, f'drawn outside the frame: {sorted(out)[:8]}'
    print('tail pixels', len(tail), '| colours', len({c for q in gs for c in q.values()}) - 1, '+ K')
