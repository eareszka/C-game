"""Design for the cliff-face rock texture (art/cliffs/cliff_texture.aseprite).

    python art/cliffs/cliff_texture_design.py <out.json>
    python tools/draw_views.py <out.json> art/cliffs/cliff_texture   # through the pixel plugin
    python art/cliffs/gen_cliff_texture.py                           # -> src/cliff_texture.inc

Every cliff wall in the game is painted from this one texture in world
coordinates, so it has to tile with no seam and not read as a repeat. Crude on
purpose, in the manner of Mother 1's cliffs and Yume Nikki's FC world: flat
rock in one tone, heaped in rough rounded lumps with heavy black between them,
a pixel of shade under some, a few pits, almost no light. Four values --
crack, shade, base, lit -- which the game swaps for an island's ore ramp (src/ore_tones.inc).
"""
import json, random, sys

N = 128                                   # everything is periodic in N
PAL = {'K': '000000', 'S': '5c5c68', 'B': '8c8c98', 'L': 'c4c4cc'}   # crack, shade, base, lit (values)
rnd = random.Random(7)

# The lumps: a wrapped Voronoi of short, upright, leaning cells, split by a
# one-pixel crack -- a pixel whose right or lower neighbour is
# another lump -- that thickens to two where a lump's crack is heavy and the
# two lumps are nearly as close, which is at the corners where three meet: so
# the lumps come out rounded, like the boulders of Mother 1's walls.
STRETCH, LEAN = 0.55, 0.35                   # cells run tall, and lean right as they rise
GX, GY = 12, 8                               # lumps on a jittered grid, so they come out of a size
pts = [((gx + 0.15 + rnd.random() * 0.7) * N / GX, (gy + 0.15 + rnd.random() * 0.7) * N / GY)
       for gy in range(GY) for gx in range(GX)]
gapw = [rnd.choice((0, 0, 0.6, 0.9)) for _ in pts]       # how far a lump's crack thickens at its corners
dark = [rnd.random() < 0.12 for _ in pts]                  # a few lumps sit back in shade

def near(x, y):
    """(own lump, distance to it, distance to the next) -- distances wrap every N."""
    ds = []
    for i, (px, py) in enumerate(pts):
        dy = (y - py + N / 2) % N - N / 2
        dx = (x - px + N / 2) % N - N / 2 + dy * LEAN
        ds.append((dx * dx + (dy * STRETCH) ** 2, i))
    ds.sort()
    return ds[0][1], ds[0][0] ** 0.5, ds[1][0] ** 0.5

info = [[near(x + 0.5, y + 0.5) for x in range(N)] for y in range(N)]
grid = [['B'] * N for _ in range(N)]
for y in range(N):
    for x in range(N):
        c, d0, d1 = info[y][x]
        other = lambda dx, dy: info[(y + dy) % N][(x + dx) % N][0] != c
        if other(1, 0) or other(0, 1) or d1 - d0 < gapw[c]: grid[y][x] = 'K'
        elif dark[c]: grid[y][x] = 'S' if (x + y) % 2 else 'B'
for y in range(N):                            # a pixel of shade under each lump's lower-right rim
    for x in range(N):
        if grid[y][x] == 'B' and (grid[(y + 1) % N][x] == 'K' or grid[y][(x + 1) % N] == 'K') and grid[(y + 1) % N][(x + 1) % N] == 'K':
            grid[y][x] = 'S'
for _ in range(N * N // 160):                 # a few black pits in the rock, and rarely a glint
    x, y = rnd.randrange(N), rnd.randrange(N)
    if grid[y][x] == 'B': grid[y][x] = 'K' if rnd.random() < 0.85 else 'L'

if __name__ == '__main__':
    out = sys.argv[1]
    json.dump({'pal': PAL, 'view_w': N, 'order': ['T'], 'views': {'T': [''.join(r) for r in grid]}},
              open(out, 'w'))
