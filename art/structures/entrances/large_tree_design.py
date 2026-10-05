"""The large tree's entrance, laid out for tools/draw_views.py.

    python art/structures/entrances/large_tree_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/large_tree

144x96, nine cells by six, over a 1x1 stamp in the bottom middle cell. Its
roots and trunk beside the stamp are solid and everything above is walked
behind (gen_entrance_art.py works that out, as for a building).

A giant oak, long dead, far bigger than the forest round it: a thick gnarled
trunk of weathered bark on roots spread over the ground, its limbs bare,
forking into thinner limbs and at last into the dark twigs the game's own
dead tree is drawn with. Bark lit on the left of each limb, in shade on the
right. In the trunk's foot, the way in: a hollow open to the ground, with no
ladder -- the one 1x1 way in that is not the ladder hole, by the user's word --
its lip of bark lit and shaded like the limbs. The branching is seeded, so the
tree is the same every build.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, outline, stand, depth_layers

W, H, B = 144, 96, 95
CX = 72                       # the trunk's middle: the middle of the stamp
PAL = {'K': '000000', 'D': '463422', 'M': '8d6b4f', 'L': 'b2966a'}     # weathered bark


def taper(g, x0, y0, x1, y1, w0, w1):
    """A length of wood from (x0, y0), w0 thick, to (x1, y1), w1 thick: round,
    lit where its surface turns to the upper left and in shade where it turns
    away, grain running along it where it is thick. Trunk, limbs and roots are
    all this, so where one grows out of another they are one piece of wood."""
    steps = int(math.hypot(x1 - x0, y1 - y0) * 2) + 1
    for i in range(steps + 1):
        t = i / steps
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        r = (w0 + (w1 - w0) * t) / 2
        for yy in range(int(cy - r) - 1, int(cy + r) + 2):
            for xx in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = xx + .5 - cx, yy + .5 - cy
                if dx * dx + dy * dy > r * r or not (2 <= xx < W - 2 and 2 <= yy <= B):
                    continue
                v = (dx * .6 + dy * .8) / max(r, .5)
                c = 'L' if v < -.45 else 'D' if v > .35 else 'M'
                if c == 'M' and r > 5 and (round(dx) % 6 == 0):
                    c = 'D'                                   # the grain
                g.put(xx, yy, c)


def limb(g, twigs, x, y, ang, length, width, rng):
    """One limb from (x, y) at ang degrees (90 is straight up), then its
    forks; below a finger's width a limb is a twig, drawn later in line."""
    a = math.radians(ang)
    x1, y1 = x + math.cos(a) * length, y - math.sin(a) * length
    if width < 1.6:
        twigs.append((x, y, x1, y1))
        return
    taper(g, x, y, x1, y1, width, width * .75)
    n = 2 if rng.random() < .8 else 3
    for k in range(n):
        spread = rng.uniform(22, 38)
        da = (k - (n - 1) / 2) * spread * 2 / max(n - 1, 1) + rng.uniform(-8, 8)
        limb(g, twigs, x1, y1, ang + da, length * rng.uniform(.62, .78), width * .64, rng)


def trunk(g):
    """The trunk, narrowing from its roots up to where it forks, and the
    roots reaching out over the ground."""
    taper(g, CX, B, CX, 60, 40, 24)
    for x1 in (CX - 34, CX + 34):
        taper(g, CX + (x1 - CX) * .35, B - 7, x1, B - 1, 12, 3)
    for x1 in (CX - 22, CX + 22):
        taper(g, CX + (x1 - CX) * .4, B - 3, x1, B, 8, 3)


def hollow(g):
    """The way in: a hollow in the trunk's foot, open to the ground. A tall
    arch, a little wider where it meets the ground and not quite regular, as
    rot leaves it; a raised lip of bark round it, lit along its top and left
    and in shade on its right, parted from the trunk by a dark line; inside,
    dark, but for the hollow's inner right wall catching a little light."""
    TOP, CY = 74, 86
    def half(y):
        if y < TOP:
            return -1
        if y < TOP + 7:
            return round(6 * math.sqrt((y - TOP + 1) / 7))
        return 6 + (y - TOP - 7) // 7
    opening = set()
    for y in range(TOP, B + 1):
        hw = half(y)
        mid = CX + (1 if y < TOP + 4 else 0)                  # rot leans the top a touch
        for x in range(mid - hw, mid + hw):
            opening.add((x, y))
    # the lip: two pixels of bark round the opening, then a dark line
    near = lambda p, n: any((p[0] + dx, p[1] + dy) in opening
                            for dx in range(-n, n + 1) for dy in range(-n, n + 1)
                            if abs(dx) + abs(dy) <= n)
    for y in range(TOP - 4, B + 1):
        for x in range(CX - 12, CX + 12):
            p = (x, y)
            if p in opening or not near(p, 3) or g.get(x, y) == '.':
                continue
            if near(p, 2):
                v = ((x + .5 - CX) * .6 + (y + .5 - CY) * .8) / max(1, math.hypot(x + .5 - CX, y + .5 - CY))
                g.put(x, y, 'L' if v < -.2 else 'D' if v > .35 else 'M')
            else:
                g.put(x, y, 'K')
    for x, y in opening:
        inner_right = (x + 2, y) not in opening and y > TOP + 3
        g.put(x, y, 'D' if inner_right else 'K')
    return opening


def tree():
    g = Grid(W, H)
    rng = random.Random(1234)
    twigs = []
    trunk(g)
    # the great limbs, grown from inside the top of the trunk so they leave it
    # as it narrows rather than sitting on it: up, and out to either side
    for ang, length, width in ((150, 18, 13), (112, 22, 14), (72, 22, 14), (32, 18, 13)):
        limb(g, twigs, CX + (ang < 90) * 5 - (ang > 90) * 5, 66, ang, length, width, rng)
    g.hollow = hollow(g)
    outline(g)
    # the twigs last, in the dark line the game's dead tree is drawn in,
    # each grown from a limb so none floats free
    for x0, y0, x1, y1 in twigs:
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        px, py = None, None
        for i in range(steps + 1):
            t = i / steps
            x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
            if not (2 <= x < W - 2 and 2 <= y < H):
                break
            if px is not None and x != px and y != py:
                g.put(x, py, 'K')                         # never a diagonal step
            g.put(x, y, 'K')
            px, py = x, y
    return g


# The ground the trunk stands on: an ellipse across its foot, as wide as the
# trunk there and as deep as it reads; the hollow in its front is the stamp,
# which is the way in whatever stands on it.
FOOT_CY, FOOT_RX, FOOT_RY = B - 8, 18, 8


def ground(g):
    """Every pixel of the tree -- trunk, limbs, twigs -- stands where the
    trunk does: on the front of its foot in that column, or its middle beyond
    the foot (roots beyond it lie on the ground, each pixel on its own row --
    stand() never puts a pixel's ground above it). The hollow is a way in: what
    shows in it is the back of the foot, so whoever steps in is seen in it."""
    def footy(x, y):
        u = (x + .5 - CX) / FOOT_RX
        return round(FOOT_CY + FOOT_RY * math.sqrt(1 - u * u)) if abs(u) < 1 else FOOT_CY
    foot = {(x, y) for y in range(H) for x in range(W)
            if ((x + .5 - CX) / FOOT_RX) ** 2 + ((y + .5 - FOOT_CY) / FOOT_RY) ** 2 <= 1}
    way = {(x, y) for x, y in g.hollow if y >= FOOT_CY}             # in, to the middle of the foot
    stand(g, footy, foot - way, way)
    for x, y in g.hollow:                                          # the dark is the back of it
        g.footy[y][x] = FOOT_CY - FOOT_RY
    return g


def design():
    g = ground(tree())
    check(g, 'large tree')
    return {'pal': PAL, 'view_w': W, 'order': ['tree'], 'views': {'tree': g.rows()},
            'depth': depth_layers(W, H, [(0, 0, g)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
