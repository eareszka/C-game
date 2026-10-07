"""Stamp the dungeons' interior wall art into assets/tileset.png, one block per
interior -- the ruins, the desert pyramid's tomb ('egypt') and the step
pyramid's Mayan one ('maya') -- and write src/dungeon_wall_tiles.inc, where
each piece sits. Every block lays its pieces out the same way, so
src/dungeon.cpp draws them all with one renderer and only the block differs.

    python tools/gen_dungeon_wall_tiles.py       # then python tools/palette_pass.py --write

Everything is baked from the approved designs (art/structures/dungeon_walls).
The barrow (stonehenge): the swatches, carvings, stars, grass bunches and
constellations its maze is composited from in the game. The ruins: their three north faces (whole, cracked, a block fallen out --
ruins_design.py) in the face columns, picked by the game per face, the rim and
the floor. The pyramids: every wall pixel is pyramid_design.pattern /
maya_murals.pattern at its screen column X and its height z, so the pieces are
cut along the patterns' periods and the game only has to pick the phase a
tile is at:

  faces       a 3-tile north face, 6 column phases (X / 16 mod 6) -- corridor
              faces plain, back walls with the desert's hieroglyph frieze
  rim         the wall top's quarter autotile (tools/dungeon_walls.py)
  floor, side the floor; a chamber's slanted side wall, one flat dark tone,
              its diagonal floor edge and its corner line (user's rules)
  flights     a 45-degree flight is one 9-tile strip a column. The strip's
              caps, floor line and 3D steps (pyramid_design.stair_steps) per
              direction and column kind (first, middle, last -- the steps start
              and stop on the projected diagonal and the foot has its floor
              chevron); its wall is upright stone in a separate layer, by
              column phase (X / 16 mod 6) and row phase (column parity: a flight
              rises 16 a column and the stone repeats every 32)
  overlays    pieces the game places whole: the Mayan corridor stones with a
              carved cryptid, the desert's enemy-glyph cartouches, the small
              carved stones up a Mayan flight, the five Mayan murals, and the
              doorway recoloured into the step pyramid's grey stone

Transparent is the sheet's colour key, as everywhere.
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALLS = os.path.join(ROOT, 'art', 'structures', 'dungeon_walls')
sys.path.insert(0, WALLS)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'art', 'structures'))
import pyramid_design as pd
import maya_murals as mm
import ruins_design as rd
import barrow_design as bd
import graveyard_design as gd
import ladder_up_design as lud
from dungeon_walls import sheet_rows
from maya_cryptids_design import CRYPTIDS

SHEET = os.path.join(ROOT, 'assets', 'tileset.png')
INC = os.path.join(ROOT, 'src', 'dungeon_wall_tiles.inc')
CELL, KEY = 16, (255, 0, 0)
# each interior's block: first column and row, and how many of each it spans
BLOCKS = {'egypt': (100, 44, 80, 10), 'maya': (100, 54, 80, 10), 'ruins': (180, 44, 6, 4),
          'barrow': (186, 44, 41, 4), 'graveyard': (228, 44, 26, 8)}
# the floor: its own tone, from the game palette (the mocks' are not on it;
# the ruins' nearest was the wall's own shade, so the nearest brown)
FLOOR = {'egypt': '967448', 'maya': '474751', 'ruins': '8d6b4f', 'barrow': '000000', 'graveyard': '000000'}

# where each piece is, in cells from the block's corner (mirrored in the .inc)
FACE_CORR, FACE_BACK = 0, 6                  # cols, rows 0-2: phase p at col + p
RIM_COL, RIM_ROW = 0, 3                      # outer, vedge, hedge, inner
FLOOR_COL = 4                                # row 3
SIDE_COL = 5                                 # row 3: solid, diag_l, diag_r, end_l, end_r
FLIGHT_COL = 12                              # + dir * 3 + kind, rows 0-8
FWALL_COL = 18                               # + dir * 12 + cp * 2 + rp, rows 1-5
MURAL_COL = 42                               # + i * 7, rows 0-2 (maya)
STONE_COL, STONE_ROW = 42, 3                 # + (i * 2 + flip) * 3, rows 3-4
SMALL_COL, SMALL_ROW = 42, 5                 # + i * 2, row 5 (maya)
DOOR_COL, DOOR_ROW = 42, 6                   # rows 6-7 (maya)
N_FLIGHT, RISE = 16, 256                     # a flight climbs one chamber row: 16 columns
SMALL_W, SMALL_H = mm.SMALL_W + 2, mm.SMALL_H + 2


class Block:
    """A variant's block of cells, as tone letters ('.' the key)."""
    def __init__(self, variant):
        self.v = variant
        pal = (rd.PAL if variant == 'ruins' else bd.PAL if variant == 'barrow'
               else gd.PAL if variant == 'graveyard' else pd.VARIANTS[variant]['pal'])
        self.pal = dict(pal, F=FLOOR[variant])
        self.px = {}

    def put(self, col, row, x, y, c):
        if c != '.':
            self.px[(col * CELL + x, row * CELL + y)] = c

    def cell(self, col, row, rows):
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                self.put(col, row, x, y, c)


def faces(b):
    pat = mm.pattern if b.v == 'maya' else pd.pattern
    for p in range(6):
        for k in range(3):
            for y in range(16):
                for x in range(16):
                    X, z = 16 * p + x, 47 - (16 * k + y)
                    if b.v == 'maya':
                        corr = back = pat(X, z, carved=False)
                    else:
                        corr, back = pat(X, z), pat(X, z, frieze=True)
                    b.put(FACE_CORR + p, k, x, y, corr)
                    b.put(FACE_BACK + p, k, x, y, back)


def rim_floor_side(b):
    v = pd.design(b.v)['views']
    for i, k in enumerate(('outer', 'vedge', 'hedge', 'inner')):
        b.cell(RIM_COL + i, RIM_ROW, v[k])
    b.cell(FLOOR_COL, RIM_ROW, ['F' * 16] * 16)
    side = pd.VARIANTS[b.v]['side']
    def piece(f):
        return [''.join(f(x, y) for x in range(16)) for y in range(16)]
    def diag(left):
        def f(x, y):
            u = (x if left else 15 - x) + y
            return '.' if u > 15 else 'K' if u == 15 else side
        return piece(f)
    b.cell(SIDE_COL + 0, RIM_ROW, piece(lambda x, y: side))
    b.cell(SIDE_COL + 1, RIM_ROW, diag(True))
    b.cell(SIDE_COL + 2, RIM_ROW, diag(False))
    b.cell(SIDE_COL + 3, RIM_ROW, piece(lambda x, y: 'K' if x == 15 else side))
    b.cell(SIDE_COL + 4, RIM_ROW, piece(lambda x, y: 'K' if x == 0 else side))


def ruins(b):
    """The ruins' faces -- whole, cracked, a block fallen out -- in the first
    three face columns, then the rim and the floor where every block has them."""
    v = rd.design()['views']
    for i in range(3):
        b.cell(FACE_CORR + i, 0, v['band%d' % i])
    for i, k in enumerate(('outer', 'vedge', 'hedge', 'inner')):
        b.cell(RIM_COL + i, RIM_ROW, v[k])
    b.cell(FLOOR_COL, RIM_ROW, ['F' * 16] * 16)


# The stonehenge barrow (barrow_design.py): not tiles but the swatches and
# pieces the game composites its maze from (dungeon.cpp barrow_bake), cells
# from the block's corner -- mirrored in the .inc as BARROW_*.
BARROW = {'front': (0, 0), 'side': (6, 0), 'carvings': (9, 0), 'stars': (15, 0), 'grass': (15, 1),
          'bunches': (16, 0), 'const': (23, 0)}


def barrow(b):
    v = bd.design()['views']
    def lay(name, col, row, w, h, x0=0, y0=0):
        rows = v[name]
        for y in range(h):
            for x in range(w):
                b.put(col, row, x, y, rows[y0 + y][x0 + x])
    lay('front', *BARROW['front'], 96, 64)
    lay('side', *BARROW['side'], 48, 64)
    lay('carvings', *BARROW['carvings'], 96, 48)
    lay('stars', *BARROW['stars'], 16, 16)
    b.cell(*BARROW['grass'], ['G' * 16] * 16)
    for k, bunch in enumerate(bd.bunches(bd.tufts())):
        for x, y, c in bunch:
            b.put(BARROW['bunches'][0] + k, 0, x, y, c)
    for k, name in enumerate(bd.CONSTELLATIONS):
        lay('const_' + name, BARROW['const'][0] + 6 * k, 0, 96, 64)


def strip_u(step, x, y):
    """Where a strip pixel lies across a flight: u along its diagonal (see
    pyramid_design.flight_strip): 15-22 the cap, 23-70 the wall, 71 the floor
    line, 72-102 the steps, 103-110 the cap under them."""
    return (x + y if step < 0 else y - x) - 9


def flights(b):
    steps, sbase = pd.stair_steps()
    C0 = 64
    for d, step in enumerate((-1, 1)):                  # 0: climbing right, 1: climbing left
        strip = [r for t in pd.flight_strip(step < 0) for r in t]
        for kind, i in enumerate((0, N_FLIGHT // 2, N_FLIGHT - 1)):
            fx, fy = 0, 40
            top = 16 * (fy + i * step - 5)
            if step > 0:
                xtop, b0, mirror = 16 * fx, 16 * (fy + 2), False
            else:
                xtop, b0, mirror = 16 * (fx + N_FLIGHT), 16 * (fy - N_FLIGHT + 2), True
            for y in range(144):
                for x in range(16):
                    u = strip_u(step, x, y)
                    # the wall is its own layer; the caps over the wall and under the
                    # steps are left off -- the pyramid has no perimeter outline (user)
                    c = '.' if 23 <= u <= 70 or u <= 22 or u >= 104 else strip[y][x]
                    X, Y = 16 * (fx + i) + x, top + y
                    lx, ly = ((xtop - X) if mirror else (X - xtop)), Y - b0
                    d2, x2 = lx - ly, lx + ly
                    if 0 <= d2 < 32:                         # the steps, from the 3D model
                        on = 0 <= x2 < 2 * RISE
                        # the foot's floor chevron (the user's red mark)
                        if step < 0 and X - 16 * fx < min(Y - 16 * fy, 16 * (fy + 2) - Y):
                            on = False
                        if step > 0 and 16 * (fx + N_FLIGHT) - 1 - X < min(Y - 16 * (fy + N_FLIGHT), 16 * (fy + N_FLIGHT + 2) - Y):
                            on = False
                        c = steps(C0 + lx, sbase + C0 + ly) if on else 'F'
                    b.put(FLIGHT_COL + d * 3 + kind, y // 16, x, y % 16, c)
        # the wall over the flight: upright rows, z from the bottom corridor's
        # floor row; column i of a flight sits 16 higher than column i - 1
        for cp in range(6):
            for rp in range(2):
                for y in range(16, 96):
                    for x in range(16):
                        u = strip_u(step, x, y)
                        if not 23 <= u <= 70:
                            continue
                        X = 16 * cp + x
                        z = (79 + 16 * rp - y) if step < 0 else (16 * (21 - rp) - 1 - y)
                        if b.v == 'maya':
                            c = mm.pattern(X, z, carved=False, h=70 - u)
                        else:
                            c = pd.pattern(X, z, h=70 - u, t=u - 23)
                        b.put(FWALL_COL + d * 12 + cp * 2 + rp, y // 16, x, y % 16, c)


def stone(b, rows, w, h, frame, lit):
    """A carving in its stone, w x h: a carved joint round it (frame), a lit
    edge inside top-left (lit, or None), rounded corners left to the wall --
    the lit (Mayan) stones' rounder, as maya_murals._big cuts them."""
    out = []
    for ly in range(h):
        r = ''
        for lx in range(w):
            edge = lx in (0, w - 1) or ly in (0, h - 1)
            if (lx in (0, w - 1) and ly in (0, h - 1)) or                     (lit and edge and lx in (0, 1, w - 2, w - 1) and ly in (0, 1, h - 2, h - 1)):
                r += '.'
            elif lx in (0, w - 1) or ly in (0, h - 1):
                r += frame
            elif lit and (lx == 1 or ly == h - 2):
                r += lit
            else:
                gx, gy = lx - (w - len(rows[0])) // 2, ly - (h - len(rows)) // 2
                c = rows[gy][gx] if 0 <= gy < len(rows) and 0 <= gx < len(rows[0]) else '.'
                r += b.field if c == '.' else c
        out.append(r)
    return out


def overlays(b, sheet):
    names = list(CRYPTIDS)
    for i, name in enumerate(names):
        for flip in (0, 1):
            col = STONE_COL + (i * 2 + flip) * 3
            if b.v == 'maya':
                b.field = 'S'                                  # as maya_murals._big carves it
                rows = stone(b, mm.carving(name, bool(flip)), 34, 22, 'D', 'M')
            else:
                b.field = 'M'                                  # as pyramid_design._cartouche
                rows = stone(b, sheet_rows(os.path.join(WALLS, 'desert_cryptids.png'), pd.PAL, 32, 20, i, bool(flip)),
                             pd.CART_W, pd.CART_H, 'D', None)
            for y, r in enumerate(rows):
                for x, c in enumerate(r):
                    b.put(col, STONE_ROW, x, y, c)
        if b.v == 'maya':
            b.field = 'S'
            rows = stone(b, mm.small_carving(i), SMALL_W, SMALL_H, 'D', None)
            for y, r in enumerate(rows):
                for x, c in enumerate(r):
                    b.put(SMALL_COL + i * 2, SMALL_ROW, x, y, c)
    if b.v != 'maya':
        return
    murals = Image.open(os.path.join(WALLS, 'pyramid_maya_murals.png')).convert('RGBA')
    tone = {tuple(int(v[k:k + 2], 16) for k in (0, 2, 4)): c for c, v in mm.PAL.items()}
    for i in range(murals.width // mm.W):
        for y in range(mm.H):
            for x in range(mm.W):
                p = murals.getpixel((i * mm.W + x, y))
                if p[3]:
                    b.put(MURAL_COL + i * 7, 0, x, y, tone[p[:3]])
    # the doorway, in the step pyramid's grey stone: the desert one's sandstone
    # mapped to its letters, and those to the grey; the daylight through it
    # (every other colour) kept as it is
    sand = {tuple(int(v[k:k + 2], 16) for k in (0, 2, 4)): c for c, v in pd.PAL.items()}
    for y in range(32):
        for x in range(32):
            p = tuple(int(v) for v in sheet[14 * CELL + y, 24 * CELL + x][:3])
            if p == KEY:
                continue
            c = sand.get(p)
            if c is None:
                c = 'x%02x%02x%02x' % p
                b.pal[c] = c[1:]
            b.put(DOOR_COL, DOOR_ROW, x, y, c)


# The graveyard's walkways (graveyard_design.py), composited in the game:
# name -> (col, row, view, x, y, w, h), in cells from the block's corner and
# pixels within the view. Each face has a row of its own (a brick face's
# lit and shaded tones would be five in one cell).
GRAVEYARD = {'top_brick': (0, 0, 'brick', 0, 0, 64, 64), 'top_board': (4, 0, 'board', 0, 0, 64, 64),
             'under_brick': (0, 4, 'under_brick', 0, 0, 64, 24), 'under_board': (4, 4, 'under_board', 0, 0, 64, 24),
             'face_brick_s': (0, 6, 'face_brick_s', 0, 0, 64, 8), 'face_brick_e': (0, 7, 'face_brick_e', 0, 0, 64, 8),
             'face_board_s': (4, 6, 'face_board_s', 0, 0, 64, 8), 'face_board_e': (4, 7, 'face_board_e', 0, 0, 64, 8),
             'wall_brick': (8, 0, 'wall_brick', 0, 0, 72, 64), 'wall_board': (13, 0, 'wall_board', 0, 0, 72, 64),
             'ghost': (18, 0, 'ghosts', 0, 0, 12, 13), 'wisp': (19, 0, 'ghosts', 20, 26, 40, 10),
             'skull0': (22, 0, 'skulls', 0, 0, 8, 8), 'skull1': (23, 0, 'skulls', 10, 0, 8, 8),
             'bone': (24, 0, 'skulls', 0, 12, 10, 3), 'ladder': (25, 0, None, 0, 0, 16, 32)}
# the ladder up a small graveyard's wall: the climb-out ladder (ladder_up_design)
# in the boardwalk's wood, a length over its foot
LADDER_WOOD = {'K': 'K', 's': 'E', 'b': 'V', 'l': 'W'}


def graveyard(b):
    views = gd.design()['views']
    for name, (col, row, view, x0, y0, w, h) in GRAVEYARD.items():
        if view is None:
            rows = lud.MID[:16] + lud.BASE
            rows = [''.join(LADDER_WOOD.get(c, '.') for c in r) for r in rows]
        else:
            rows = [r[x0:x0 + w] for r in views[view][y0:y0 + h]]
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                b.put(col, row, x, y, c)


def stamp(sheet, b):
    c0, r0, NC, ROWS = BLOCKS[b.v]
    rgb = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for k, v in b.pal.items()}
    area = sheet[r0 * CELL:(r0 + ROWS) * CELL, c0 * CELL:(c0 + NC) * CELL]
    area[:, :, :3] = KEY
    area[:, :, 3] = 255
    for (x, y), c in b.px.items():
        area[y, x, :3] = rgb[c]
    # the NES's four colours a cell: where a flight's foot puts its floor
    # chevron beside all four tones of the steps and cap, the cell's rarest
    # colour goes to its nearest -- decided here, in the cell, rather than by
    # palette_pass's sheet-wide rarity, which could take the floor itself
    merged = []
    for cy in range(ROWS):
        for cx in range(NC):
            cell = area[cy * CELL:(cy + 1) * CELL, cx * CELL:(cx + 1) * CELL, :3]
            while True:
                cols, counts = np.unique(cell.reshape(-1, 3), axis=0, return_counts=True)
                keep = [(n, tuple(int(v) for v in c)) for c, n in zip(cols, counts)
                        if tuple(c) != KEY]
                if len(keep) <= 4:
                    break
                n, rare = min(k for k in keep if k[1] != (0, 0, 0))
                to = min((c for _, c in keep if c not in (rare, (0, 0, 0))),
                         key=lambda c: sum((a - b) ** 2 for a, b in zip(c, rare)))
                cell[(cell == rare).all(axis=2)] = to
                merged.append((cx, cy, rare, to))
    print('%s: %d px at cols %d-%d rows %d-%d; merged to 4 colours: %s' % (
        b.v, len(b.px), c0, c0 + NC - 1, r0, r0 + ROWS - 1, merged or 'none'))


INC_TEXT = '''// Generated by tools/gen_dungeon_wall_tiles.py -- do not edit.
// Where the dungeon interiors' wall pieces sit on the sheet: a block per
// interior (WALL_EGYPT the desert tomb, WALL_MAYA the step pyramid's, WALL_RUINS),
// all laid out alike, offsets in cells from the block's corner. See the
// generator for what each piece is.
enum { WALL_EGYPT, WALL_MAYA, WALL_RUINS, WALL_BARROW, WALL_GRAVEYARD };
static const int WALL_COL0[5] = { %d, %d, %d, %d, %d };
static const int WALL_ROW0[5] = { %d, %d, %d, %d, %d };
enum {
    PYR_FACE_CORR = %d, PYR_FACE_BACK = %d,           // + phase, rows 0-2
    PYR_RIM_COL = %d, PYR_RIM_ROW = %d,               // outer, vedge, hedge, inner
    PYR_FLOOR_COL = %d, PYR_SIDE_COL = %d,            // row PYR_RIM_ROW; side: solid, diag_l, diag_r, end_l, end_r
    PYR_FLIGHT_COL = %d,                              // + dir * 3 + kind, rows 0-8
    PYR_FWALL_COL = %d,                               // + dir * 12 + cp * 2 + rp, strip rows 1-5
    PYR_MURAL_COL = %d, PYR_MURAL_W = %d, PYR_MURAL_H = %d, PYR_MURALS = %d,   // + i * 7, row 0
    PYR_STONE_COL = %d, PYR_STONE_ROW = %d,           // + (i * 2 + flip) * 3
    PYR_STONE_W_MAYA = %d, PYR_STONE_H_MAYA = %d, PYR_STONE_W_DESERT = %d, PYR_STONE_H_DESERT = %d,
    PYR_SMALL_COL = %d, PYR_SMALL_ROW = %d, PYR_SMALL_W = %d, PYR_SMALL_H = %d,  // + i * 2
    PYR_DOOR_COL = %d, PYR_DOOR_ROW = %d,             // the Mayan doorway, 2 x 2
    PYR_CRYPTIDS = %d,
};
// The barrow's pieces (WALL_BARROW block), in cells: the front swatch 96 x 64
// (tiles every 96 across), the side 48 x 64, the carvings 24 x 24 (five: four
// to a row), the two stars (a 2 x 2 at 0,0, a cross at 4..6,0..2), a cell of
// plain grass, the grass's bunches (one a cell, top-left), the constellations
// 96 x 64 each.
enum {
    BARROW_FRONT_COL = %d, BARROW_SIDE_COL = %d, BARROW_CARVE_COL = %d, BARROW_CARVINGS = 5,
    BARROW_STAR_COL = %d, BARROW_GRASS_COL = %d, BARROW_GRASS_ROW = %d,
    BARROW_BUNCH_COL = %d, BARROW_BUNCHES = %d, BARROW_CONST_COL = %d, BARROW_CONSTS = %d,
};
// The graveyard's pieces (WALL_GRAVEYARD block): where each sits, in cells, and
// its size in pixels -- tops 64 x 64 (tiling), undersides 64 x 24, faces 64 x 8
// (south lit, east shaded), walls 72 x 64 (a 64 x 48 front at y 16, its top,
// its east end at x 64), the parallax sprites, the wood ladder (a length over
// its foot, 16 x 32).
%s'''


def main():
    im = Image.open(SHEET).convert('RGBA')
    sheet = np.array(im)
    for v in ('egypt', 'maya', 'ruins', 'barrow', 'graveyard'):
        b = Block(v)
        if v == 'barrow':
            barrow(b)
        elif v == 'graveyard':
            graveyard(b)
        elif v == 'ruins':
            ruins(b)
        else:
            faces(b); rim_floor_side(b); flights(b); overlays(b, sheet)
        stamp(sheet, b)
    Image.fromarray(sheet).save(SHEET)
    with open(INC, 'w', newline='\n') as f:
        gy = ('struct GyPiece { int col, row, w, h; };\n'
              'enum GyName { %s, GY_PIECES };\n'
              'static const GyPiece GY_PIECE[GY_PIECES] = {\n%s};\n') % (
            ', '.join('GY_' + k.upper() for k in GRAVEYARD),
            ''.join('    { %d, %d, %d, %d },   // %s\n' % (c, r, w, h, k)
                    for k, (c, r, _, _, _, w, h) in GRAVEYARD.items()))
        V5 = ('egypt', 'maya', 'ruins', 'barrow', 'graveyard')
        f.write(INC_TEXT % (*(BLOCKS[v][0] for v in V5),
                            *(BLOCKS[v][1] for v in V5), FACE_CORR, FACE_BACK, RIM_COL, RIM_ROW,
                            FLOOR_COL, SIDE_COL, FLIGHT_COL, FWALL_COL,
                            MURAL_COL, mm.W, mm.H, 5, STONE_COL, STONE_ROW,
                            34, 22, pd.CART_W, pd.CART_H,
                            SMALL_COL, SMALL_ROW, SMALL_W, SMALL_H, DOOR_COL, DOOR_ROW, len(CRYPTIDS),
                            BARROW['front'][0], BARROW['side'][0], BARROW['carvings'][0], BARROW['stars'][0],
                            BARROW['grass'][0], BARROW['grass'][1], BARROW['bunches'][0],
                            len(bd.bunches(bd.tufts())), BARROW['const'][0], len(bd.CONSTELLATIONS), gy))
    print('wrote', SHEET, 'and', INC)


if __name__ == '__main__':
    main()
