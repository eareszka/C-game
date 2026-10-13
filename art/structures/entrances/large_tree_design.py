"""The large tree's entrance, laid out for tools/draw_views.py.

    python art/structures/entrances/large_tree_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/large_tree

144x96, nine cells by six, over a 1x1 stamp in the bottom middle cell. Its
roots and trunk beside the stamp are solid and everything above is walked
behind (gen_entrance_art.py works that out, as for a building).

A giant oak, long dead, far bigger than the forest round it: a thick gnarled
trunk on roots spread over the ground and four heavy limbs, bare and bent,
each with a short branch or two -- few and bold and spread apart, forking as
the game's own dead tree does (the user, 2026-10-12, over limbs grown from a
seed into a thicket of twigs at the top: "too clustered up top", not the
game's pixel art). The limbs are placed by hand, LIMBS.
Its bark is the bark of its inside (interior_style MATERIALS, as
art/direction/OVERWORLD_STYLE.md has it): the plate tone over most of each
limb, its shade down the right, the furrow tone only where it turns right
away. In the trunk's foot, the way in: a hollow open to the ground, with no
ladder -- the one 1x1 way in that is not the ladder hole, by the user's word --
its lip of bark lit and shaded like the limbs.
"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, outline, stand, depth_layers
from interior_style import MATERIALS

W, H, B = 144, 96, 95
CX = 72                       # the trunk's middle: the middle of the stamp
PAL = dict(zip('LMD', MATERIALS['bark']['tones']), K='000000')        # plate, its shade, furrow

# A limb, then its branches: the points each runs through, (x, y, thickness).
# The four start inside the top of the trunk, so they leave it as it narrows
# rather than sitting on it.
LIMBS = [
    [(63, 67, 14), (46, 60, 11), (30, 50, 8), (20, 36, 5), (16, 24, 3), (10, 18, 2)],
    [(30, 51, 6), (16, 54, 4), (7, 50, 2)],
    [(21, 37, 4), (30, 28, 3), (32, 19, 2)],
    [(68, 62, 14), (62, 44, 10), (64, 28, 7), (58, 14, 4), (60, 5, 2)],
    [(63, 30, 5), (74, 20, 4), (78, 9, 2)],
    [(62, 40, 5), (48, 34, 4), (44, 30, 3)],
    [(78, 62, 14), (88, 48, 10), (86, 32, 7), (94, 18, 4), (92, 8, 2)],
    [(88, 34, 5), (100, 30, 4), (104, 26, 3)],
    [(81, 67, 14), (98, 60, 11), (114, 50, 8), (122, 36, 5), (132, 28, 3), (137, 20, 2)],
    [(114, 51, 6), (128, 54, 4), (137, 50, 2)],
    [(122, 38, 4), (114, 28, 3), (112, 19, 2)],
]


def taper(g, x0, y0, x1, y1, w0, w1):
    """A length of wood from (x0, y0), w0 thick, to (x1, y1), w1 thick: round,
    its plate tone on the half turned to the upper left, in shade where it
    turns away, grain running along it a tone down where it is thick. Trunk, limbs and roots are
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
                c = 'L' if v < -.05 else 'D' if v > .5 else 'M'
                if c != 'D' and r > 5 and (round(dx) % 6 == 0):
                    c = 'M' if c == 'L' else 'D'              # the grain
                g.put(xx, yy, c)


def trunk(g):
    """The trunk, narrowing from its roots up to where it forks, and the
    roots reaching out over the ground."""
    taper(g, CX, B, CX, 60, 40, 24)
    for x1 in (CX - 34, CX + 34):
        taper(g, CX + (x1 - CX) * .35, B - 7, x1, B - 1, 12, 3)
    for x1 in (CX - 22, CX + 22):
        taper(g, CX + (x1 - CX) * .4, B - 3, x1, B, 8, 3)


def hollow(g, cx=CX, bot=B):
    """The way in: a hollow in the trunk's foot, open to the ground. A tall
    arch, a little wider where it meets the ground and not quite regular, as
    rot leaves it; a raised lip of bark round it, lit along its top and left
    and in shade on its right, parted from the trunk by a dark line; inside,
    dark, but for the hollow's inner right wall catching a little light.
    cx, bot: its middle and the ground row -- dungeon_doors_design.py draws
    the same hollow as the tree's way out, seen from inside."""
    TOP, CY = bot - 21, bot - 9
    def half(y):
        if y < TOP:
            return -1
        if y < TOP + 7:
            return round(6 * math.sqrt((y - TOP + 1) / 7))
        return 6 + (y - TOP - 7) // 7
    opening = set()
    for y in range(TOP, bot + 1):
        hw = half(y)
        mid = cx + (1 if y < TOP + 4 else 0)                  # rot leans the top a touch
        for x in range(mid - hw, mid + hw):
            opening.add((x, y))
    # the lip: two pixels of bark round the opening, then a dark line
    near = lambda p, n: any((p[0] + dx, p[1] + dy) in opening
                            for dx in range(-n, n + 1) for dy in range(-n, n + 1)
                            if abs(dx) + abs(dy) <= n)
    for y in range(TOP - 4, bot + 1):
        for x in range(cx - 12, cx + 12):
            p = (x, y)
            if p in opening or not near(p, 3) or g.get(x, y) == '.':
                continue
            if near(p, 2):
                v = ((x + .5 - cx) * .6 + (y + .5 - CY) * .8) / max(1, math.hypot(x + .5 - cx, y + .5 - CY))
                g.put(x, y, 'L' if v < -.2 else 'D' if v > .35 else 'M')
            else:
                g.put(x, y, 'K')
    for x, y in opening:
        inner_right = (x + 2, y) not in opening and y > TOP + 3
        g.put(x, y, 'D' if inner_right else 'K')
    return opening


def tree():
    g = Grid(W, H)
    trunk(g)
    for pts in LIMBS:
        for (x0, y0, w0), (x1, y1, w1) in zip(pts, pts[1:]):
            taper(g, x0, y0, x1, y1, w0, w1)
    g.hollow = hollow(g)
    outline(g)
    return g


# The ground the trunk stands on: an ellipse across its foot, as wide as the
# trunk there and as deep as it reads; the hollow in its front is the stamp,
# which is the way in whatever stands on it.
FOOT_CY, FOOT_RX, FOOT_RY = B - 8, 18, 8


def ground(g):
    """Every pixel of the tree -- trunk and limbs -- stands where the
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
