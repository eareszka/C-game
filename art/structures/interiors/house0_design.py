"""The first house's room -- the stone house the game starts in -- laid out for
tools/draw_views.py.

    python art/structures/interiors/house0_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house0

A room as simple as Mother 1 draws one -- flat colours, thin black lines, one
screen, the back wall square on and the side walls and floor running back at
45 degrees (the shape of art/reference/interiors_reference.png) -- but this
house's own: walls of the stone house's white brick, a floor of boards in its
door's brown, its plank door on the left wall (the way out), two windows in
wooden frames with sky in them. A stone fireplace in the back wall with a rug
before it, a bed in the back right corner, a table and two chairs, a plant in
the front right corner.

Drawn at 1:1 in the reference's 256x128 frame, set on the screen at (OX, OY)
-- on a tile row, so its tiles keep to four colours. Each thing drawn says
the floor row it stands on (Grid.footy) and what ground it covers, for the
game's collision and for what goes over the player.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, stand, depth_layers, four_per_cell

PAL = {'K': '000000',
       'W': 'fcfcfc', 'm': '9797aa',                     # the house's brick and mortar
       'n': 'c6ccda',                                    # the fireplace's stone
       'F': '94703d',                                    # the door's wood: door, frames, furniture
       'T': 'b2966a', 'e': '8d6b4f',                     # the floor's boards, their seams
       'L': 'd7a175',                                    # a table's or chair's top
       'U': '5c94fc',                                    # sky
       'R': 'b70000', 'Y': 'f0bc3c',                     # red cloth, gold, the fire
       'G': '058f3a', 'g': '235436'}                     # the plant
W, H = 320, 240
OX, OY = 32, 48                  # the frame's place on the screen
EDGE0, EDGE1 = 8, 247            # the room across the frame
BX0, BX1, BACK = 72, 183, 63     # the back wall's corners and the floor's back row
FRONT = 127                      # the floor's near row
COURSE, BRICK = 4, 10            # a brick course's height, a brick's length


def foot_of(x):
    """The floor row at the foot of the wall over column x."""
    return BACK + max(0, BX0 - x, x - BX1)


def part(x, y):
    if not (EDGE0 <= x <= EDGE1 and 0 <= y <= FRONT):
        return None
    if y < foot_of(x):
        return 'back' if BX0 <= x <= BX1 else 'left' if x < BX0 else 'right'
    return 'floor'


class Room:
    """The frame's pixels, what row each stands on, and the ground covered."""
    def __init__(self):
        self.c, self.fy, self.foot = {}, {}, set()

    def put(self, x, y, c, fy):
        self.c[(x, y)], self.fy[(x, y)] = c, fy

    def box(self, x0, y0, x1, y1, c, fy):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c, fy(x, y) if callable(fy) else fy)

    def outline(self, x0, y0, x1, y1, fy):
        for x in range(x0, x1 + 1):
            self.put(x, y0, 'K', fy); self.put(x, y1, 'K', fy)
        for y in range(y0, y1 + 1):
            self.put(x0, y, 'K', fy); self.put(x1, y, 'K', fy)

    def covers(self, x0, x1, y0, y1):
        self.foot |= {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def shell(r):
    for y in range(FRONT + 1):
        for x in range(EDGE0, EDGE1 + 1):
            p = part(x, y)
            if p is None:
                continue
            if p == 'floor':
                # boards across the room, six rows wide, their ends staggered
                row = (y - BACK) // 6
                seam = (y - BACK) % 6 == 5 or (x + row * 17) % 48 == 0
                r.put(x, y, 'e' if seam else 'T', y)
                continue
            f = foot_of(x)
            up = f - 1 - y                                   # how far up the wall
            if up == 0:
                c = 'K'                                      # the line at the wall's foot
            elif up <= 2:
                c = 'm'                                      # a grey band above it
            elif p != 'back':
                c = 'W'                                      # the side walls flat, as the house's own side face
            else:
                course = (up - 3) // COURSE
                bed = (up - 3) % COURSE == COURSE - 1
                head = (x + (course % 2) * (BRICK // 2)) % BRICK == 0
                c = 'm' if bed or head else 'W'
            r.put(x, y, c, f)
    for y in range(BACK):                                    # the back corners
        r.put(BX0, y, 'K', BACK); r.put(BX1, y, 'K', BACK)


def window(r, x0, y0):
    """A small window in the back wall, the reference's size: a wooden frame
    and cross, sky behind -- the frame its own edge, so the brick round it
    keeps its mortar."""
    x1, y1 = x0 + 11, y0 + 11
    r.box(x0, y0, x1, y1, 'F', BACK)
    r.box(x0 + 1, y0 + 1, x1 - 1, y1 - 1, 'U', BACK)
    r.box(x0 + 5, y0 + 1, x0 + 6, y1 - 1, 'F', BACK)
    r.box(x0 + 1, y0 + 5, x1 - 1, y0 + 6, 'F', BACK)


def door(r):
    """The house's plank door on the left wall, slanting back with it: dark
    seams between its planks, black round it, a knob."""
    x0, x1, tall = 34, 45, 24
    for x in range(x0, x1 + 1):
        f = foot_of(x)
        for y in range(f - tall, f + 1):
            edge = x in (x0, x1) or y in (f - tall, f)
            seam = (x - x0) % 4 == 0
            r.put(x, y, 'K' if edge or seam else 'F', f)
    kx = x1 - 2
    r.put(kx, foot_of(kx) - 11, 'W', foot_of(kx))


def fireplace(r):
    """A small stone fireplace in the back wall, a fire in its firebox; a
    stone hearth on the floor before it."""
    x0, x1, top = 108, 131, 42
    for y in range(top, BACK):
        for x in range(x0, x1 + 1):
            joint = (y - top) % 5 == 4 or (x + ((y - top) // 5 % 2) * 3) % 6 == 0
            r.put(x, y, 'm' if joint else 'n', BACK)            # jointed in the brick's mortar
    r.box(x0 - 1, top - 2, x1 + 1, top, 'n', BACK)          # the mantel
    r.outline(x0 - 1, top - 2, x1 + 1, top, BACK)
    r.outline(x0, top, x1, BACK - 1, BACK)
    fx0, fx1, fy0 = 115, 124, 51                             # the firebox
    r.box(fx0, fy0, fx1, BACK - 1, 'K', BACK)
    for y in range(55, BACK - 1):
        for x in range(fx0 + 2, fx1 - 1):
            dx = abs(x - (fx0 + fx1) / 2)
            if dx < (y - 54) * .6:
                r.put(x, y, 'Y' if dx < (y - 55) * .3 else 'R', BACK)
    r.box(x0 - 2, BACK, x1 + 2, BACK + 2, 'n', lambda x, y: BACK + 2)   # the hearth
    r.outline(x0 - 2, BACK, x1 + 2, BACK + 2, BACK + 2)
    r.covers(x0 - 2, x1 + 2, BACK, BACK + 2)


def rug(r):
    """Lying before the fire: red, a gold border."""
    x0, x1, y0, y1 = 104, 135, 82, 89                       # clear of the hearth's tiles
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y in (y0, y1)
            border = x in (x0 + 2, x1 - 2) or y in (y0 + 2, y1 - 2)
            r.put(x, y, 'K' if edge else 'Y' if border else 'R', y)


def bed(r):
    """In the back right corner, its head against the back wall, low as the
    reference's: a wooden headboard, a white pillow and a red blanket, the
    wooden foot."""
    x0, x1, back, front, high = 149, 175, BACK, 80, 4        # ends on a tile's edge, clear of the corner
    r.box(x0, BACK - 9, x1, BACK - 1, 'F', BACK)             # the headboard
    r.outline(x0, BACK - 9, x1, BACK - 1, BACK)
    for y in range(back - high, front - high + 1):           # its top, as it runs forward
        for x in range(x0, x1 + 1):
            d = y + high                                     # the row it stands over
            r.put(x, y, 'W' if d < back + 5 else 'R', d)
    r.box(x0, front - high, x1, front, 'F', front)           # its foot
    r.outline(x0, back - high, x1, front, front)
    r.covers(x0, x1, back, front)


def table(r):
    """A small wooden table, a chair at each side."""
    x0, x1, back, front, high = 160, 183, 102, 108, 6
    for y in range(back - high, front - high + 1):
        for x in range(x0, x1 + 1):
            r.put(x, y, 'L', y + high)
    for y in range(front - high + 1, front + 1):             # its front and legs
        for x in range(x0, x1 + 1):
            if y <= front - high + 1 or x in (x0 + 1, x1 - 1):
                r.put(x, y, 'F', front)
    r.outline(x0, back - high, x1, front - high + 1, front)
    r.covers(x0, x1, back, front)
    for cx in (150, 186):                                    # the chairs: back, seat, legs
        cx1, cb, cf, seat = cx + 7, 103, 108, 3
        top = cf - seat - 8
        r.box(cx, top, cx1, cf - seat - 3, 'F', cb)          # the back
        r.box(cx, cf - seat - 2, cx1, cf - seat, 'L', cf)    # the seat
        r.box(cx, cf - seat + 1, cx1, cf, 'F', cf)           # its front
        for y in range(cf - seat + 2, cf + 1):
            for x in range(cx + 2, cx1 - 1):
                r.put(x, y, 'T', y)                          # the floor between its legs
        r.outline(cx, top, cx1, cf, cf)
        r.covers(cx, cx1, cb, cf)


def plant(r):
    """A small pot and a round bush in the right corner."""
    cx, base = 222, 100
    r.box(cx - 3, base - 4, cx + 3, base, 'F', base)
    r.outline(cx - 3, base - 4, cx + 3, base, base)
    for y in range(base - 15, base - 4):
        for x in range(cx - 6, cx + 7):
            nx, ny = (x + .5 - cx) / 6, (y + .5 - (base - 10)) / 5.5
            d = nx * nx + ny * ny
            if d <= 1:
                r.put(x, y, 'K' if d > .66 else 'G' if nx * .6 + ny * .8 < 0 else 'g', base)
    r.covers(cx - 3, cx + 3, base - 2, base)


def room():
    r = Room()
    shell(r)
    window(r, 80, 30)                                        # each on tiles of its own, clear of the mantel
    window(r, 148, 30)
    fireplace(r)
    door(r)
    rug(r)
    bed(r)
    table(r)
    plant(r)
    g = Grid(W, H)
    for (x, y), c in r.c.items():
        g.put(OX + x, OY + y, c)
    walk = {(OX + x, OY + y) for y in range(FRONT + 1) for x in range(EDGE0, EDGE1 + 1)
            if part(x, y) == 'floor' and (x, y) not in r.foot}
    foot = {(x, y) for y in range(H) for x in range(W) if (x, y) not in walk}
    fy = {(OX + x, OY + y): v + OY for (x, y), v in r.fy.items()}
    stand(g, lambda x, y: fy.get((x, y), y), foot)
    four_per_cell(g, [('e', 'T'), ('m', 'W'), ('g', 'G'), ('Y', 'R'), ('L', 'T')], by_count=False)
    return g


# the way out: the floor before the door in the left wall (interiors.h 'E')
EXIT = [(4, 9), (5, 9)]


def design():
    g = room()
    check(g, 'house 0', objects=True)
    return {'pal': PAL, 'view_w': W, 'order': ['room'], 'views': {'room': g.rows()},
            'depth': depth_layers(W, H, [(0, 0, g)]), 'exit': EXIT}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
