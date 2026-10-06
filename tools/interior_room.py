"""The parts every building's room is made of, for the
art/structures/interiors/*_design.py that lay them out for tools/draw_views.py.

A room as simple as Mother 1 draws one -- thin black lines, one screen, the
back wall square on and the side walls and floor running back at 45 degrees
(the shape of art/reference/interiors_reference.png) -- in the house's own
materials: a back wall of its brick -- three tones a brick, as outside: its
base, a shade along each brick's bottom and right edge, the mortar -- over a
wooden wainscot, the side walls plain in its mortar's tone, a floor of bevelled boards running back
into the room, the plank door on the left wall (the way out), windows in
wooden frames. The furniture is boxes in the oblique view, sized against the
player (tools/interior_sizes.py).

Drawn at 1:1 in the reference's 256x128 frame, set on the screen at (OX, OY)
-- a row down from a tile row, so the floor starts one and the wall's tiles
keep to four colours. Each thing drawn says the floor row it stands on
(Grid.footy) and what ground it covers, for the game's collision and for what
goes over the player.

Tones: K line; W brick, Z its shade, m mortar (also the side walls and the
trim); F wood (the wainscot too),
P a lighter wood for tops; T, e, L the floor's boards, seams and lit edges;
U glass; R and C cloth (a blanket, a sofa, books); N iron.
"""
from entrance_shapes import Grid, check, stand, depth_layers, four_per_cell, STEP
from interior_sizes import DOOR, BED, TALL, WINDOW

BASE = {'K': '000000', 'F': '94703d', 'P': 'd7a175',
        'T': 'c18a39', 'e': '815423', 'L': 'd89830',      # honey boards
        'U': '84a7e9', 'N': '474751'}
W, H = 320, 240
OX, OY = 32, 49                  # the frame's place: the floor's back row starts a tile row
EDGE0, EDGE1 = 8, 247            # the room across the frame
BX0, BX1, BACK = 72, 183, 63     # the back wall's corners and the floor's back row
FRONT = 127                      # the floor's near row
COURSE, BRICK = 4, 10            # a brick course's height, a brick's length
BOARD, BOARD_LEN = 8, 36         # a board's width across the screen, how far apart its ends fall
EXIT = [(4, 9), (5, 9)]          # the floor before the door in the left wall (interiors.h 'E')


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
        self.near = {}                                       # the boxes' depth buffer: the floor row each shows

    def put(self, x, y, c, fy):
        self.c[(x, y)], self.fy[(x, y)] = c, fy

    def box(self, x0, y0, x1, y1, c, fy):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c, fy(x, y) if callable(fy) else fy)

    def obox(self, x0, fy, w, dep, high, front, top, side, flip=False):
        """A box in the game's oblique view (entrance_shapes.oblique): its
        front face w wide square on, standing on floor row fy, `high` up; its
        top and right side running back `dep` rows, up and to the right at 45
        degrees -- or, flip, its top and left side up and to the left, as the
        right wall runs. Each face a tone, or a tone for each pixel --
        front(a, z), top(a, k), side(k, z), a across, k back, z up; None
        leaves the floor showing, between legs -- outlined in black. What
        stands STEP or taller covers its ground."""
        tone = lambda c, *p: c(*p) if callable(c) else c
        s = -1 if flip else 1
        x1 = x0 + w - 1
        def put(x, y, c, f):                                 # the nearer -- the lower floor row -- wins
            if c is not None and f >= self.near.get((x, y), -1):
                self.near[(x, y)] = f
                self.put(x, y, c, f)
        for k in range(1, dep + 1):                          # the top, row by row back
            for a in range(w):
                edge = a in (0, w - 1) or k == dep
                put(x0 + a + s * k, fy - high - k, 'K' if edge else tone(top, a, k), fy - k)
        for k in range(1, dep + 1):                          # the side, column by column
            for z in range(high + 1):
                open_ = z == 0 and k < dep and tone(side, k, 1) is None
                put((x0 if flip else x1) + s * k, fy - z - k,
                    None if open_ else 'K' if k == dep or z == 0 else tone(side, k, z), fy - k)
        for z in range(high + 1):                            # the front
            for a in range(w):
                open_ = z == 0 and 0 < a < w - 1 and tone(front, a, 1) is None
                put(x0 + a, fy - z, None if open_ else
                    'K' if a in (0, w - 1) or z in (0, high) else tone(front, a, z), fy)
        if high >= STEP:
            self.foot |= {(x0 + a + s * k, fy - k) for a in range(w) for k in range(dep + 1)}


def floor_tone(x, y):
    """Boards running back into the room in the oblique view, up and to the
    right at 45 degrees as the furniture's depth runs (along a board x + y is
    fixed): a dark seam on one side of each, a lit edge on the other, their
    ends falling a board's length apart, each board's on its own row."""
    along = (x + y) % BOARD
    board = (x + y) // BOARD
    if along == 0 or (y + board * 13) % BOARD_LEN == 0:
        return 'e'
    if along == 1 or (y + board * 13) % BOARD_LEN == 1:
        return 'L'
    return 'T'


WAINSCOT = 47                    # the back wall's lowest tile row, wood: what stands against the
                                 # wall shares its tiles with wood, not brick, so every brick keeps
                                 # its three tones


def shell(r):
    for y in range(FRONT + 1):
        for x in range(EDGE0, EDGE1 + 1):
            p = part(x, y)
            if p is None:
                continue
            if p == 'floor':
                r.put(x, y, floor_tone(x, y), y)
                continue
            f = foot_of(x)
            up = f - 1 - y                                   # how far up the wall
            if up == 0:
                c = 'K'                                      # the line at the wall's foot
            elif up <= 2 or p != 'back':
                c = 'm'                                      # a band above it; the side walls plain, as the gable end outside
            elif y >= WAINSCOT:
                c = 'K' if y == WAINSCOT else 'F'            # the wainscot: plain wood, a black line atop
            else:
                course, rc = (up - 3) // COURSE, (up - 3) % COURSE
                lx = (x + (course % 2) * (BRICK // 2)) % BRICK
                if rc == COURSE - 1 or lx == 0:
                    c = 'm'                                  # mortar: the bed joint, the head joint
                elif rc == 0 or lx == BRICK - 1:
                    c = 'Z'                                  # the brick's shade: its bottom, its right edge
                else:
                    c = 'W'
            r.put(x, y, c, f)
    for y in range(BACK):                                    # the back corners
        r.put(BX0, y, 'K', BACK); r.put(BX1, y, 'K', BACK)


def window(r, x0, y0):
    """A window in the back wall filling a tile, so the brick round it keeps
    its tones: a wooden frame and cross, sky behind, a glint of light in the
    top corner of each pane."""
    x1, y1 = x0 + WINDOW[0] - 1, y0 + WINDOW[1] - 1
    mx, my = x0 + WINDOW[0] // 2 - 1, y0 + WINDOW[1] // 2 - 1
    r.box(x0, y0, x1, y1, 'F', BACK)
    r.box(x0 + 1, y0 + 1, x1 - 1, y1 - 1, 'U', BACK)
    r.box(mx, y0 + 1, mx + 1, y1 - 1, 'F', BACK)
    r.box(x0 + 1, my, x1 - 1, my + 1, 'F', BACK)
    for px in (x0 + 1, mx + 2):
        for py in (y0 + 1, my + 2):
            r.put(px, py, 'm', BACK)


def door(r):
    """The plank door on the left wall, slanting back with it: dark seams
    between its planks, black round it, a knob."""
    x0 = 34
    x1, tall = x0 + DOOR[0] - 1, DOOR[1] - 1
    for x in range(x0, x1 + 1):
        f = foot_of(x)
        for y in range(f - tall, f + 1):
            edge = x in (x0, x1) or y in (f - tall, f)
            seam = (x - x0) % 4 == 0
            r.put(x, y, 'K' if edge or seam else 'F', f)
    kx = x1 - 2
    r.put(kx, foot_of(kx) - tall // 2, 'm', foot_of(kx))


# ---- furniture: boxes in the oblique view --------------------------------

def bed(r, x0, fy, flip=False):
    """Seen side on as Mother 1 draws one: a blanket (R) hanging over its
    front, a pillow at the head, a headboard at the head's end -- the left,
    or with flip the right, the bed running back up and to the left as the
    right wall does. Painted in the trim's tone, so where it stands against
    the brick its tiles keep to the wall's tones and the blanket's. x0 is its
    front's left end."""
    dep, high, head = 8, 5, 10
    w = BED[0] - dep
    hx = x0 + w - 2 if flip else x0                          # the headboard's two columns
    r.obox(hx, fy, 2, dep, head, 'm', 'm', 'm', flip=flip)
    bx = x0 if flip else x0 + 2
    pillow = (lambda a, k: a >= w - 2 - 7) if flip else (lambda a, k: a < 7)
    r.obox(bx, fy, w - 2, dep, high, lambda a, z: 'm' if z < 2 else 'R',
           lambda a, k: 'm' if pillow(a, k) else 'R', 'R', flip=flip)


def dresser(r, x0):
    """Against the back wall: a wooden chest of three drawers, black lines
    between them, a knob on each -- the wood one tone, as the wall's tiles
    hold no more."""
    dep, high = 6, TALL[1] - 7
    w = TALL[0] - dep
    drawer = lambda a, z: 'K' if z in (4, 8) else 'm' if a == w // 2 and z in (2, 6, 10) else 'F'
    r.obox(x0, BACK + dep, w, dep, high, drawer, 'F', 'F')


def legs(w, high):
    """A front face that is an apron and two legs, the floor showing between."""
    return lambda a, z: 'F' if z >= high - 2 or a in (1, w - 2) else None


def low_table(r, x0, fy, w=18):
    """A low table before a sofa, all one wood: it stands on a rug."""
    r.obox(x0, fy, w, 6, 5, legs(w, 5), 'F', lambda k, z: 'F' if z >= 3 or k == 5 else None)


def rug(r, x0, fy, w, dep, border=True):
    """Flat on the floor: cloth (R) with a border in the trim's tone -- or
    none, where something stands on it and its tiles hold no more."""
    r.obox(x0, fy, w, dep, 0, 'K',
           lambda a, k: 'm' if border and (a in (2, w - 3) or k in (2, dep - 2)) else 'R', 'K')


def books(a, z, shelf=8):
    """Shelves of books on a face: a board every `shelf` rows, the books
    between them two wide, black between, in the two cloths by turns."""
    if z % shelf == 0:
        return 'F'
    if a % 3 == 0:
        return 'K'
    return 'R' if (a // 3 + z // shelf) % 2 == 0 else 'C'


def bookcase(r, x0, fy, w=22, high=24, dep=5):
    """A free-standing bookcase, its shelves of books facing the room."""
    r.obox(x0, fy, w, dep, high, books, 'F', 'F')


def wall_shelves(r, x0, x1, y0, y1):
    """Shelves built into the back wall, floor to near the ceiling, full of
    books -- on whole tiles, so the brick's tones never share one with them."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y == y0
            r.put(x, y, 'K' if edge else books(x - x0, y1 - y, 10), BACK)


def counter(r, x0, fy, w=36, dep=8, high=11):
    """A shop counter: wooden panels in front, a lighter top."""
    r.obox(x0, fy, w, dep, high, lambda a, z: 'K' if a % 9 == 0 or z == 2 else 'F', 'P', 'F')


def sofa(r, x0, fy, w=34):
    """A sofa in the second cloth (C): its back, its seat, an arm each end."""
    dep = 8
    # the back, standing at the seat's back edge: that far back in the
    # oblique view is that far to the right as well
    r.obox(x0 + dep - 2, fy - dep + 2, w, 2, 11, 'C', 'C', 'C')
    r.obox(x0, fy, w, dep - 2, 5, 'C', 'C', 'C')               # the seat
    for ax in (x0, x0 + w - 3):                                # the arms
        r.obox(ax, fy, 3, dep - 2, 8, 'C', 'C', 'C')


def stove(r, x0):
    """An iron stove against the back wall: an oven door, burners on top."""
    dep, high, w = 7, 10, 16
    r.obox(x0, BACK + dep, w, dep, high,
           lambda a, z: 'K' if (a in (3, w - 4) or z in (2, 7)) and 3 <= a <= w - 4 and 2 <= z <= 7 else 'N',
           lambda a, k: 'K' if (a in (4, 5, 10, 11) and k in (2, 3, 5)) else 'N', 'N')


def cupboard(r, x0, w=30):
    """A kitchen cupboard against the back wall: two doors and their
    knobs, all one wood, as the wall's tiles hold no more."""
    dep, high = 7, 10
    r.obox(x0, BACK + dep, w, dep, high,
           lambda a, z: 'K' if a in (w // 2, 2, w - 3) and z <= high - 2 else 'm' if a in (w // 2 - 2, w // 2 + 2) and z == 5 else 'F',
           'F', 'F')


# ---- the room as the game takes it ---------------------------------------

def finish(r, name, pal, merge=()):
    """The design for draw_views and gen_entrance_art: the room on the screen,
    its layers -- the floor walkable but where a thing stands on it -- and the
    way out. The four-colour rule is kept by merging the least needed tones
    first: the floor's bevels and seams, then the brick's mortar, then any
    the room adds."""
    pal = dict(BASE, **pal)
    # tones the room gives one colour are one tone: the brick may be the
    # floor's colour, say -- to the four-colour rule and to the drawing
    same = {}
    for k, v in pal.items():
        same.setdefault(v, k)
    one = {k: same[v] for k, v in pal.items()}
    g = Grid(W, H)
    for (x, y), c in r.c.items():
        g.put(OX + x, OY + y, one.get(c, c))
    walk = {(OX + x, OY + y) for y in range(FRONT + 1) for x in range(EDGE0, EDGE1 + 1)
            if part(x, y) == 'floor' and (x, y) not in r.foot}
    foot = {(x, y) for y in range(H) for x in range(W) if (x, y) not in walk}
    fy = {(OX + x, OY + y): v + OY for (x, y), v in r.fy.items()}
    stand(g, lambda x, y: fy.get((x, y), y), foot)
    four_per_cell(g, [('L', 'T'), ('e', 'T')] + list(merge) + [('m', 'W')], by_count=False)
    check(g, name, objects=True)
    return {'pal': {k: v for k, v in pal.items() if one[k] == k}, 'view_w': W, 'order': ['room'], 'views': {'room': g.rows()},
            'depth': depth_layers(W, H, [(0, 0, g)]), 'exit': EXIT}


def new_room(windows=((80, 15), (160, 15))):        # on tiles: x a multiple of 16, y 15 past one
    """The shell, the door and the windows; the design adds its furniture."""
    r = Room()
    shell(r)
    for x, y in windows:
        window(r, x, y)
    door(r)
    return r
