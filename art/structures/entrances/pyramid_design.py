"""The pyramid entrance, two ways, laid out for tools/draw_views.py.

    python art/structures/entrances/pyramid_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/pyramid

    x   0..159  in the desert: the Dajna's pyramid
    x 160..319  anywhere else: a step pyramid after Chichen Itza

Each is 160x112, ten cells by seven -- a monument, far larger than its way
in, which is still the 2x2 stamp in the bottom two rows of the middle two
columns and a doorway the player's size. The stone beside the doorway is
solid and the rows above are walked behind (gen_entrance_art.py works that out,
as for a building).

The desert one is the pyramid the Dajna (enemy 30) rises carrying -- art/
enemies/30_views.aseprite -- seen from the overworld: the same sandstone,
courses of staggered blocks, a lit face toward the light and the other in
shade, a dark doorway between side pillars under a lintel. Drawn in the houses'
oblique projection (entrance_shapes.Scene). The courses run level across both
faces, as the Dajna's do -- laid in true 3D, the right face's climbed at
forty-five degrees and broke up into noise. Four colours a cell: the lintel
and pillars are the face's sandstone rather than the Dajna's paler lintel
stone, which would be a fifth in the doorway's cells.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Scene, check, rect, fill, oblique, weather, depth_layers

W, H = 160, 112
B = 109                      # the ground row under the front faces
CX = 80                      # the doorway's middle: the middle of the stamp

# The Dajna's colours as the game palette has them (art/direction/fcremap.py's
# lookup of its 232,200,128 / 184,148,88 / 124,96,56 / 44,32,20): outline,
# mortar, lit sandstone, shaded sandstone, doorway
PAL = {'K': '000000', 'D': '785830', 'M': 'f4ce80', 'S': 'b29e5c', 'X': '241c0a'}


def stone(z, along, course_h=4, block=8):
    """Sandstone in courses: a mortar bed every course_h, and the joints of
    each course a half block along from the last."""
    zi = int(z)
    course = zi // course_h
    if zi % course_h == course_h - 1:
        return 'D'
    return 'D' if (int(along) + (course % 2) * (block // 2)) % block == 0 else None


def pyramid():
    X0, X1, D1 = CX - 55, CX + 55, 20        # the base: across, and how far back
    XM, DM, TOP = CX, 10, 84                 # the apex: over the base's middle, this high
    sc = Scene(W, H, B)
    front, right = [], []
    steps = 260
    for i in range(steps + 1):
        t = i / steps                                    # up the face, 0 at the ground
        for j in range(steps + 1):
            u = j / steps                                # along the base edge
            # front face: from the front edge of the base up to the apex
            x = (X0 + u * (X1 - X0)) * (1 - t) + XM * t
            d, z = DM * t, TOP * t
            front.append((x, d, z, stone(z, x) or 'M'))
            # right face: from the right edge of the base up to the apex,
            # its courses level by screen row as the Dajna's are
            x = X1 * (1 - t) + XM * t
            d = (u * D1) * (1 - t) + DM * t
            right.append((x, d, z, stone(z + d, x + d, block=6) or 'S'))
    sc.points(0, front)
    sc.points(1, right)
    sc.ground(X0, X1, 0, D1)

    def doorway(g):
        fill(g, rect(CX - 7, B - 18, CX + 6, B), 'X')    # the dark way in
        fill(g, rect(CX - 7, B - 18, CX + 6, B - 18), 'K')   # shadow under the lintel
        fill(g, rect(CX - 7, B - 18, CX - 7, B), 'K')    # and inside the left post
    sc.flat(2, doorway, -0.5, opening=16)
    sc.carve(CX - 7, CX + 6, -1, 8)                              # a step into the dark

    def frame(g):
        for x0 in (CX - 10, CX + 7):                     # side pillars
            fill(g, rect(x0, B - 20, x0 + 2, B), 'M')
            fill(g, rect(x0 + 2, B - 20, x0 + 2, B), 'D')
        fill(g, rect(CX - 11, B - 23, CX + 10, B - 20), 'M')   # the lintel
        fill(g, rect(CX - 11, B - 20, CX + 10, B - 20), 'D')
    sc.flat(3, frame, -0.6)
    g = sc.render()
    # its age: corners knocked off, cracks through the blocks; the doorway whole
    weather(g, 30, 'MS', 'D', chips=14, cracks=16, keep=[(CX - 12, B - 24, CX + 11, B)])
    return g


def step_pyramid():
    """Anywhere but the desert: a step pyramid after Chichen Itza. Six
    terraces stacking back and narrowing, each with its ledge lit; a temple on
    the top with a dark door; a staircase climbing the front to it; and the way
    in at the stairs' foot, between two serpent heads -- the stair runs whole
    from the ground to the temple's dark door. In the ruins' grey stone."""
    C, TIER, N = 'courses', 11, 6
    sc = Scene(W, H, B)
    for i in range(N):                                   # the terraces, bottom up
        sc.box(i, CX - 60 + 7 * i, CX + 59 - 7 * i, 2 * i, 18 - i, TIER * i, TIER * (i + 1), C)
    zt = TIER * N                                        # the top terrace's floor
    dt = 2 * (N - 1)                                     # and its front
    sc.box(N, CX - 14, CX + 13, dt, dt + 3, zt, zt + 13, C)          # the temple
    sc.box(N + 1, CX - 17, CX + 16, dt - 1, dt + 4, zt + 13, zt + 17, C)  # its roof

    def temple_door(g):
        x0, y0 = oblique(CX - 4, dt, zt + 9, B)
        x1, y1 = oblique(CX + 3, dt, zt, B)
        fill(g, rect(x0, y0, x1, y1), 'K')
    sc.flat(N + 2, temple_door, dt - 0.5)

    # The stair: a plane from the ground up to the temple, unbroken, treads
    # lit and risers in shade, a balustrade of shade either side.
    pts = []
    n = 400
    for i in range(n + 1):
        t = i / n
        z = zt * t
        d = dt * t
        x0, x1 = CX - 8 + 2 * t, CX + 7 - 2 * t
        k = 0
        while x0 + k <= x1:
            x = x0 + k
            edge = x - x0 < 1.5 or x1 - x < 1.5
            pts.append((x, d - 0.3, z, 'D' if edge or int(z) % 3 == 0 else 'L'))
            k += 0.25
    sc.points(N + 3, pts, nearer=4)                       # built out in front of the terraces
    sc.carve(CX - 8, CX + 7, -4, 5)                       # its foot, where the way in is

    for pid, x in ((N + 5, CX - 12), (N + 6, CX + 8)):   # the serpent heads
        sc.box(pid, x, x + 3, 0, 2, 0, 5, 'M')

    def eyes(g):
        for x in (CX - 11, CX + 9):
            g.put(x, B - 4, 'K')
    sc.flat(N + 7, eyes, -0.9)
    g = sc.render()
    # its age, as the desert one's; the stair and the temple door whole
    weather(g, 31, 'ML', 'D', chips=16, cracks=18,
            keep=[(CX - 13, 0, CX + 12, B), (CX - 18, 0, CX + 30, 30)])
    # its own letters for the grey stone, so both pyramids share one palette
    g.g = [[{'D': 'd', 'M': 'm', 'L': 'l'}.get(c, c) for c in row] for row in g.g]
    return g


def design():
    g, s = pyramid(), step_pyramid()
    check(g, 'pyramid')
    check(s, 'step pyramid')
    pal = dict(PAL, d='595965', m='9797aa', l='c6ccda')
    return {'pal': pal, 'view_w': W, 'order': ['pyramid', 'step'],
            'views': {'pyramid': g.rows(), 'step': s.rows()},
            'depth': depth_layers(2 * W, H, [(0, 0, g), (W, 0, s)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
