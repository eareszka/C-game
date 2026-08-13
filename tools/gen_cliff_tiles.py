"""Draw the cliff band and the highland outline into assets/tileset.png.

The reference (Desktop/problem/reference.aseprite) is a plateau seen from
slightly above: its top is the ordinary ground, its north edge is a beaded
black line, and its south, west and east edges are a band of rock — brown,
split top to bottom by black clefts, outlined against the grass, with a
scatter of grains fallen below its foot.

Reproducing that from tiles means solving one problem: the band's silhouette
has to be ragged at a scale of two or three pixels, yet no seam between two
tiles may show.  Both fall out of drawing every cell from the *same* pair of
functions of world position:

  * coverage — a bilinear blend of the four corners of the tile, which is what
    marching squares already gives us.  Two tiles either side of a seam share
    the two corners along it, so the blend agrees exactly there, whatever the
    two cases are.
  * grain — value noise that wraps on a 64x64 pixel torus, sampled at world
    position.  Because it wraps, and because a tile knows its position within
    that torus, neighbours sample a continuous field.

Add them and threshold: the boundary wanders by several pixels, and still
lines up across every seam by construction.  A tile therefore needs an index
of (marching-squares case, position in the 4x4 torus block) — 16 x 16 cells,
laid out one case per sheet row.

The band is only half the picture, because a band is a mask swept in whole
tiles and the least it can draw is a tile of rock.  Down a flank the reference
draws eight pixels, and where the edge turns away north it draws none at all —
neither fits in a mask.  So the band is masked only where the drop is deep
enough to be worth a tile, and everywhere else the outline carries a *bank*:
three, five or seven pixels of the same rock hung off the line itself, cut from
the line's own field so the two cannot come apart.  Which of the two a tile gets
is decided by how far its edge has turned from facing you — see cliff_facing()
in tilemap.cpp, and BANK_FACING below, which has to agree with it.

Run from the repo root:  python tools/gen_cliff_tiles.py [--preview out.png]
"""
import argparse
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- constants

CELL   = 16          # pixels on a side of one sheet cell
# Cells on a side of the noise torus, and so how far the band runs before it
# repeats. Sixteen is not extravagance: at four the repeat was plain to see
# along any face more than a few tiles long, because the eye finds a period of
# 64px in a 1400px window without being asked to. Sixteen puts it at 256px,
# five repeats to a screen rather than twenty, and it is also exactly what fits
# a 4096px sheet row — 256 cells — so a case is one row and no space is wasted.
BLOCK  = 16
TORUS  = CELL * BLOCK

ROCK_ROW0  = 16      # sheet row of case 0 of the band
EDGE_ROW0  = 32      # ... and of the beaded outline
SCREE_ROW0 = 48      # ... and of the spill of grains below a foot
SCREE_STEPS = 2      # how many tiles below the rock the spill reaches
BANK_ROW0  = 64      # ... and of the narrow bank the band thins to at a flank
HAZE_ROW0  = 112     # ... and of the mask that pales the ground on top of it
NCASE      = 16

# How far the rock reaches out from the outline on a bank, in pixels, class by
# class, and how far that far edge wanders.
#
# Seven is what the reference asks for and what there is room to draw. It draws
# eight down its west flank (the rock at x=16..23, y=101..116) and its strictly
# north-south stretches measure two to four across; what this drew there was the
# band, sixteen, a whole tile, and it reads as a second cliff standing alongside
# the first rather than as the side of the first one. Room, because a bank hangs
# off the outline and the outline wanders six pixels inside its own cell: eight
# is more than is left over half the time, and what will not fit is cropped
# against the tile. The narrower classes are there to land the bank into the
# line rather than to be looked at on their own — five is two clefts wide and
# three is one, which is the least that still reads as rock and not as a line
# drawn heavy.
BANK_REACH = (3.0, 5.0, 7.0)
BANK_RAG   = 1.6
BANK_FLOOR = 2.0     # and the least it draws where there is no room for more

# The facing at which each class starts, widest first, and how far the facing is
# measured over.
#
# Facing runs from +1 where the drop is square on to you to -1 where it is the
# back of the hill, and it is what decides how much of the wall there is to see:
# all of it at the front, an edge at the flank, nothing at the rear. A flank
# proper is 0, and the classes are spaced so that it lands on the widest bank
# and the two narrow ones are spent turning the corner into the rear.
BANK_FRONT  = len(BANK_REACH) + 1
BANK_R      = 3
BANK_FACING = (0.35, -0.05, -0.30, -0.55)

KEY   = (255,   0,   0)   # the sheet's colour key
BROWN = (136, 112,   0)   # straight off the reference
INK   = (  0,   0,   0)

# ------------------------------------------------------------------- noise

def lattice(wave_x, wave_y, seed):
    """Random values on a grid of the given wavelength, in pixels.

    Stated as a wavelength rather than as a count so the numbers below say
    how big a feature is and stay saying it if the torus is ever resized;
    the count is whatever divides the torus nearest to that.
    """
    nx = max(1, int(round(TORUS / float(wave_x))))
    ny = max(1, int(round(TORUS / float(wave_y))))
    return np.random.RandomState(seed).rand(ny, nx)


def noise(lat, x, y):
    """Value noise sampled at world pixel (x, y), wrapping on the torus."""
    ny, nx = lat.shape
    fx = np.asarray(x, dtype=np.float64) / TORUS * nx
    fy = np.asarray(y, dtype=np.float64) / TORUS * ny
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    tx, ty = fx - x0, fy - y0
    sx = tx * tx * (3 - 2 * tx)
    sy = ty * ty * (3 - 2 * ty)
    x0m, x1m = x0 % nx, (x0 + 1) % nx
    y0m, y1m = y0 % ny, (y0 + 1) % ny
    a = lat[y0m, x0m] + (lat[y0m, x1m] - lat[y0m, x0m]) * sx
    b = lat[y1m, x0m] + (lat[y1m, x1m] - lat[y1m, x0m]) * sx
    return a + (b - a) * sy


def signed(lat, x, y):
    return noise(lat, x, y) * 2.0 - 1.0


# Every lattice below is a fixed draw, so the whole sheet is reproducible.
# The pair of numbers is the size of one feature in pixels, across and down.
L_JAG_C  = lattice(16, 16, 101)   # the slow rise and fall of the band's edge
L_JAG_M  = lattice( 7,  7, 103)   # the bites out of that
L_JAG_F  = lattice( 3,  3, 102)   # and the three-pixel teeth on those
L_SWAY_C = lattice(16, 11, 111)   # the slow lean of a whole run of clefts
L_SWAY_M = lattice( 7,  5, 112)   # and the wander of each one within it
L_SWAY_F = lattice(3.5, 3, 121)   # and the kinks in that
L_GRIT   = lattice(2.7, 6, 122)   # grain that roughens their walls
L_PINCH  = lattice( 5,  4.5, 123) # where a cleft closes up and the rock joins
L_DROP   = lattice( 6, 13, 124)   # how wide each cleft runs, or whether at all
L_SCREE  = lattice(2.7, 2.7, 131) # which grains below the foot survive

# Measured off the reference: inside the mass the ink is 35% of the pixels, in
# veins 2-3px across, separated by 3-6px of brown — so one vein every six.
CLEFT_COUNT  = 48     # veins across the torus — one every 5.3px
CLEFT_HALF   = 0.75   # half-width of a middling vein, in pixels, deep in the mass
CLEFT_VARY   = 5.0    # how unlike one another neighbouring veins come out
CLEFT_SHUT   = 1.55   # below which a vein does not open at all
CLEFT_FLARE  = 1.20   # how much wider it opens where it reaches daylight
CLEFT_REACH  = 4.0    # over how many pixels that opening happens
CLEFT_SWAY   = (5.5, 2.6, 1.0)   # how far each octave shifts a vein sideways
TOOTH_RELIEF = 0.30   # how far a column of brown stands proud of its neighbours
TOOTH_PIVOT  = 0.40   # where along a column the silhouette is left alone
JAG_SCALE    = 0.36   # how far any cliff boundary strays from the polygon
SCREE_DENSITY = 0.62  # how thickly grains lie just below the foot
SCREE_FALLOFF = 0.055 # and how fast they thin out going away from it


def cleft_dist(px, py):
    """Distance in pixels to the nearest vein of ink splitting the rock.

    The veins are a fixed count of vertical stripes, shoved sideways by noise
    at three scales, rather than the contour lines of a noise field. Contours
    were the obvious thing to reach for and they are wrong: a contour of a
    two-dimensional field closes on itself, so the rock came out covered in
    rings and hooks. The reference has none — every cleft there runs from the
    top of the face to the bottom, leaning and forking on the way. A displaced
    stripe cannot close, so it cannot do anything else.

    Whole stripes are added by moving one torus width, so `t` is still periodic
    and the seams still hold. Dividing by the gradient turns the distance to a
    stripe into pixels, which is what lets the caller widen a vein by a stated
    number of them; where the sway crowds two stripes together the gradient
    rises and they merge, which is where the reference's wider clefts are.
    """
    sway = (CLEFT_SWAY[0] * signed(L_SWAY_C, px, py)
          + CLEFT_SWAY[1] * signed(L_SWAY_M, px, py)
          + CLEFT_SWAY[2] * signed(L_SWAY_F, px, py))
    t = (px + sway) * (CLEFT_COUNT / float(TORUS)) + 0.10 * signed(L_GRIT, px, py)
    gy, gx = np.gradient(t)
    k = np.round(t)
    return np.abs((t - k) / (np.hypot(gx, gy) + 1e-6)), k


def cleft_width(k, px, py):
    """How wide the vein nearest each pixel opens, in pixels.

    Two things vary it, and both have to, because a run of stripes all the same
    width is corduroy and reads as fabric rather than as rock. The first is per
    stripe: sampled at the stripe's own nominal position rather than at the
    pixel's, so one value holds all the way down a cleft, and so a fair share
    of stripes come out at or below zero and vanish — which is what leaves the
    reference with columns of brown three pixels wide next to columns of ten.
    The second is local, and closes a cleft here and there so the rock either
    side joins across it.
    """
    strength = noise(L_DROP, k * (float(TORUS) / CLEFT_COUNT), py)
    pinch = noise(L_PINCH, px, py)
    w = CLEFT_HALF * (CLEFT_VARY * strength - CLEFT_SHUT) * (0.55 + 0.90 * pinch)
    return np.clip(w, 0.0, None)


def blur3(a):
    """Three-by-three box blur, wrapping — good enough to take the pixel-scale
    jitter off a field without moving anything that matters."""
    out = np.zeros_like(a)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out += np.roll(np.roll(a, dy, axis=0), dx, axis=1)
    return out / 9.0


def depth_in(mask, limit):
    """How many pixels deep into `mask` each pixel lies, capped at `limit`."""
    d = np.zeros(mask.shape, dtype=np.float64)
    for r in range(1, limit + 1):
        d += erode(mask, r)
    return d


# Weighted well away from the finest octave: at a three-pixel wavelength the
# boundary stops reading as teeth and starts reading as fur.
JAG_ROCK = (0.52, 0.38, 0.10)


def jag(px, py, scale, mix=JAG_ROCK):
    return scale * (mix[0] * signed(L_JAG_C, px, py)
                  + mix[1] * signed(L_JAG_M, px, py)
                  + mix[2] * signed(L_JAG_F, px, py))


# --------------------------------------------------------------- geometry

PAD = 4   # how far outside the cell the field is evaluated, for the outline


def corner_blend(case, u, v):
    """Bilinear blend of the four corner coverages.

    Bit order matches cliff_face_code() in tilemap.cpp: 1 = north-west,
    2 = north-east, 4 = south-west, 8 = south-east.
    """
    c00 = (case >> 0) & 1
    c10 = (case >> 1) & 1
    c01 = (case >> 2) & 1
    c11 = (case >> 3) & 1
    return (c00 * (1 - u) * (1 - v) + c10 * u * (1 - v)
          + c01 * (1 - u) * v       + c11 * u * v)


def padded_grid(bx, by):
    """Local and world pixel coordinates over the cell plus its PAD margin."""
    r = np.arange(-PAD, CELL + PAD)
    lx, ly = np.meshgrid(r, r)
    return lx, ly, lx + bx * CELL, ly + by * CELL


def boundary_field(case, lx, ly, px, py, vein, sign=1.0):
    """Where a boundary of the cliff system falls, in this cell.

    One function for both the band and the outline of the height above it, and
    that is the point rather than a tidiness. The two are one line in the world
    — the lip of the drop — so anything that moves one has to move the other by
    the same amount, or a thread of grass opens between them and the outline
    reads as a hairline lying alongside the cliff.

    Hence `sign`, which is the whole subtlety. Along their shared edge the two
    coverages are complements: in the last tile of a height the outline's blend
    is `u` where the band's is `1 - u`. Their gradients point opposite ways, so
    adding the same displacement to both fields moves the two edges *apart* by
    twice it — which is what drawing them from one field, the obvious fix, still
    got wrong. Subtracting it from the one and adding it to the other moves both
    the same way in the world, and the edges stay welded however far the grain
    throws them. The outline passes -1.
    """
    u = (lx + 0.5) / CELL
    v = (ly + 0.5) / CELL
    return corner_blend(case, u, v) - 0.5 + sign * grain_shift(px, py, vein)


def grain_shift(px, py, vein):
    """How far the grain throws a boundary off its polygon, in field units."""
    tooth = np.clip(blur3(vein) / 3.0, 0.0, 1.0)
    return jag(px, py, JAG_SCALE) + TOOTH_RELIEF * (tooth - TOOTH_PIVOT)


def erode(mask, radius):
    """True only where every pixel within `radius` (chebyshev-ish disk) is set."""
    out = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > radius * radius + 1:
                continue
            out &= np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    return out


def crop(a):
    return a[PAD:PAD + CELL, PAD:PAD + CELL]


# ------------------------------------------------------------- the two sets

def rock_cell(case, bx, by):
    """One cell of the band of rock."""
    img = np.zeros((CELL, CELL, 3), dtype=np.uint8)
    img[:, :] = KEY
    if case == 0:
        return img

    lx, ly, px, py = padded_grid(bx, by)

    # Rock wherever coverage, pushed about either way by the grain, clears
    # half — and pushed out again along the middle of every brown column.
    #
    # That last term is what gives the band its teeth. In the reference the
    # top of a face is not a wavy line but a row of points, one to each column
    # of brown, with a black wedge driven down between them; the same at the
    # foot, upside down. Tying the silhouette to the same field that draws the
    # clefts gets both for free, and gets them lined up, which is the part that
    # reads as rock rather than as a torn edge.
    vein, stripe = cleft_dist(px, py)
    rock = boundary_field(case, lx, ly, px, py, vein) > 0.0
    if not rock.any():
        return img

    # One pixel of ink held back from every edge of the mass, and the clefts
    # opening out as they reach it. The heavy black along the top and the foot
    # of a face in the reference is not an outline drawn thicker there — it is
    # the clefts arriving, which is why brown teeth stand through it. Drawing
    # it as an outline instead is what made the band read as a shape with a
    # line around it.
    #
    # A cleft also closes in places and lets the rock either side join up, so
    # the columns come out lumpy and broken rather than as ruled stripes.
    deep = depth_in(rock, int(CLEFT_REACH))
    flare = np.clip(1.0 - deep / CLEFT_REACH, 0.0, 1.0)
    width = cleft_width(stripe, px, py) + CLEFT_FLARE * flare
    ink = rock & (~erode(rock, 1) | (vein < width))

    fill = crop(rock & ~ink)
    line = crop(ink)
    img[fill] = BROWN
    img[line] = INK

    # Grains fallen below the foot. Only under a column that actually has rock
    # in it, thinning as they get further from it, and laid along one diagonal
    # so they read as spill down a slope rather than as scattered dirt.
    rc = crop(rock)
    grain = np.zeros((CELL, CELL), dtype=bool)
    for i in range(CELL):
        col = np.nonzero(rc[:, i])[0]
        if col.size == 0:
            continue
        foot = col.max()
        for j in range(foot + 2, CELL):
            if rc[j, i] or (i + j) % 3:
                continue
            gx, gy = i + bx * CELL, j + by * CELL
            if noise(L_SCREE, gx, gy) < SCREE_DENSITY - SCREE_FALLOFF * (j - foot):
                grain[j, i] = True
    img[grain] = BROWN
    return img


def scree_cell(step, bx, by):
    """Grains lying on the ground below the foot of a face.

    A cell of its own because most of the spill in the reference falls clear
    of the rock altogether — a tile or two of open ground below it, thinning
    with distance. Inside the band's own cells there is nowhere to put it.

    `step` is how many tiles below the rock this is, and only decides how much
    survives; the pattern itself is the same field, so a two-tile spill reads
    as one drift rather than as two bands.
    """
    img = np.zeros((CELL, CELL, 3), dtype=np.uint8)
    img[:, :] = KEY
    j, i = np.mgrid[0:CELL, 0:CELL]
    px, py = i + bx * CELL, j + by * CELL
    fall = SCREE_FALLOFF * (j + step * CELL + 1)
    grain = ((i + j) % 3 == 0) & (noise(L_SCREE, px, py) < SCREE_DENSITY - fall)
    img[grain] = BROWN
    return img


def edge_cell(case, bx, by, reach=None):
    """One cell of the outline along the edge of a height.

    `reach` hangs a bank of rock off it, that many pixels of it, on the low
    side. That is the whole of a cliff where its drop runs away from you —
    where the band proper has stopped, because the mask it is cut from has run
    out — and it is drawn here rather than there for two reasons.

    It cannot be a narrowed band cell. Narrowing means gating cells, and the
    band's cells only join up because every one of them is drawn: a cell whose
    neighbour is missing spills its mass to the tile edge and stops square, and
    a plateau ends up with a brown brick at each shoulder. Whatever is dropped
    has to be dropped from the mask, before the cases are taken off it.

    And it belongs to the line. A bank is the last few pixels of a wall seen
    along its length, so it is the line thickening rather than a band lying
    beside it — which is exactly what the reference draws, its outline running
    down the west flank at x=16 with the rock filling east of it as far as x=23
    and the same line carrying on north with nothing beside it at all. Cutting
    it from the field the line is cut from is what welds the two.
    """
    img = np.zeros((CELL, CELL, 3), dtype=np.uint8)
    img[:, :] = KEY
    if case == 0 or case == 15:
        return img

    lx, ly, px, py = padded_grid(bx, by)

    # Exactly the field the band is cut from, mirrored — see boundary_field.
    # The height's edge and the top of the rock hanging off it are one line in
    # the world, so they had better be one line here.
    u = (lx + 0.5) / CELL
    v = (ly + 0.5) / CELL
    vein, stripe = cleft_dist(px, py)
    shift = grain_shift(px, py, vein)
    field = corner_blend(case, u, v) - 0.5 - shift
    high = field > 0.0
    if not high.any() or high.all():
        return img

    if reach is not None:
        # How far outside the edge a pixel is allowed to be, as a value of the
        # field rather than as a distance measured in it.
        #
        # A distance would want the field's gradient to scale by, and the
        # gradient is the one thing about a bilinear that does *not* survive a
        # seam. Two cells share the two corners along their edge, so they agree
        # on the field there exactly — that is what the whole scheme rests on —
        # but the derivative across the edge is taken from the corners they do
        # not share, and disagrees. Measured, that put the bank's far edge in
        # two different places either side of every horizontal seam and drew the
        # tile grid: the rate at which the picture changes across a row boundary
        # went from level with its surroundings to 1.4 times them.
        #
        # A flat cut in field units has no such term. On the cases a flank is
        # actually made of — a covered pair, where the blend runs 0 to 1 straight
        # across the cell — one pixel is one sixteenth of the field and the cut
        # is in pixels after all. On the corner cases it is not, and the bank
        # widens and narrows through a corner, which is no bad thing.
        far = reach + jag(px, py, BANK_RAG, (0.30, 0.45, 0.25))
        # And it has to stop short of the cell.
        #
        # A bank hangs off the outline, and the grain throws the outline about
        # by six pixels inside its own cell — so on the half of a flank where it
        # has wandered outward there is no room left to hang seven pixels of
        # rock in, and nothing outside this cell will draw the rest. The first
        # pass simply ran off the edge and was cropped, which is where the long
        # dead-straight sides came from: the bank was showing the tile grid.
        #
        # Room runs out at blend zero, which the field puts at 0.5 + grain, so
        # keep a pixel or two inside that, and let the edge it stops at wander
        # because the margin does.
        #
        # Never below BANK_FLOOR, though. Letting it pinch to nothing left a
        # tile of bare line between the bank above and the band below at the
        # shoulders, which reads as the rock breaking rather than as the drop
        # turning away. Two pixels always draw; where there is genuinely no room
        # for them the crop takes one back, and one pixel of tile edge on a
        # two-pixel bank is nothing to see.
        margin = 0.5 + 1.5 * noise(L_PINCH, py, px)
        room = np.maximum(0.5 + shift - margin / CELL, BANK_FLOOR / CELL)
        rock = ~high & (-field < np.minimum(far / CELL, room))
        if rock.any():
            # The ink a bank carries is not the ink the band carries, and it
            # took two passes to see why. The band holds a pixel back from every
            # edge and flares its clefts where they reach daylight, which is
            # what puts the heavy black along the top and the foot of a face.
            # A bank is seven pixels across at its widest and every pixel of it
            # is an edge, so both fire everywhere at once: it came out 94% ink
            # at three pixels and 66% at eight, which is the outline drawn heavy
            # and not rock at all.
            #
            # The reference says where the black in a flank actually goes. Down
            # its west side the rock runs x=16..23 with the four pixels nearest
            # the height inked and the four against the grass bare brown — no
            # rim on the outer edge, and no flare. So: one pixel against the
            # line, the clefts, and nothing else.
            width = cleft_width(stripe, px, py)
            inner = rock & ~erode(~high, 1)
            ink = rock & (inner | (vein < width))
            img[crop(rock & ~ink)] = BROWN
            img[crop(ink)] = INK

    # One unbroken pixel of ink just inside the edge.
    #
    # Unbroken is measured, not assumed: tools/bead_stats.py on the reference
    # finds the line present in 221 of 224 columns, with three gaps of a single
    # pixel between them. It looks beaded because it is one pixel wide and
    # climbs in steps, not because anything is missing from it. Breaking it on
    # purpose — which is what the first pass did, at about one column in four —
    # gives a dotted rule, and a dotted rule lying along a plateau's north edge
    # reads as litter dropped in the grass rather than as the edge of anything.
    rim = high & ~erode(high, 1)
    img[crop(rim)] = INK
    return img


def haze_cell(case, bx, by):
    """Where the height's own surface lies in this cell, as a solid mask.

    The game lays a pale wash over the ground a plateau stands on, one step
    paler for each storey up, and the wash has to stop where the outline does.
    A tile-sized quad will not do it: the height is a mask in whole tiles but
    the outline wanders six pixels either side of it, so a quad leaves a ragged
    pale fringe outside the line on one stretch and dark ground inside it on the
    next — the tile grid, showing in the colour.

    So the wash is cut from the same field the outline is, and lands on the same
    pixels. Case 15 fills the cell, which is what a tile well inside a plateau
    wants, so the caller has no special case to write.
    """
    img = np.zeros((CELL, CELL, 3), dtype=np.uint8)
    img[:, :] = KEY
    if case == 0:
        return img
    lx, ly, px, py = padded_grid(bx, by)
    u = (lx + 0.5) / CELL
    v = (ly + 0.5) / CELL
    vein, _ = cleft_dist(px, py)
    high = corner_blend(case, u, v) - 0.5 - grain_shift(px, py, vein) > 0.0
    img[crop(high)] = (255, 255, 255)
    return img


# ------------------------------------------------------------------- sheet

def stamp(sheet, row0, maker, rows=NCASE):
    for case in range(rows):
        for by in range(BLOCK):
            for bx in range(BLOCK):
                col = by * BLOCK + bx
                cell = maker(case, bx, by)
                sheet[(row0 + case) * CELL:(row0 + case + 1) * CELL,
                      col * CELL:(col + 1) * CELL] = cell


# ----------------------------------------------------------------- preview

def preview(path, sheet):
    """Stamp a plateau out of the cells just generated, the way the game does.

    Worth having: the cells are unreadable one at a time, and the only
    question that matters — does a run of them look like the reference — can
    only be answered on a whole landform.
    """
    W, H = 40, 26
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.random.RandomState(7)
    blob = np.zeros((H, W))
    for cx, cy, rad in [(15, 9, 8.5), (26, 11, 6.5), (9, 13, 5.0), (30, 7, 4.0)]:
        blob += np.clip(1.0 - np.hypot(xx - cx, (yy - cy) * 1.35) / rad, 0, None)
    for _ in range(3):
        blob += 0.16 * r.rand(H, W)
    high = blob > 0.55

    # The band: below and beside the highland, never above it — the same sweep
    # place_cliffs() does, at CLIFF_FACE_D = 2 and CLIFF_FACE_SIDE = 1, narrowing
    # with depth so it comes to a point at each shoulder.
    face = np.zeros((H, W), dtype=bool)
    for y in range(H):
        for x in range(W):
            if high[y, x]:
                continue
            if y + 1 < H and high[y + 1, x]:
                continue
            for dy in range(0, 3):
                w = 1 if dy <= 1 else 0
                for dx in range(-w, w + 1):
                    sx, sy = x - dx, y - dy
                    if 0 <= sx < W and 0 <= sy < H and high[sy, sx]:
                        face[y, x] = True

    def at(m, x, y):
        return 0 <= x < W and 0 <= y < H and m[y, x]

    def facing(x, y):
        """Which way the height's edge faces here: +1 square on to you, -1 the
        back of the hill. The centroid of the height over a window points into
        it, so the outward normal is the other way — see cliff_facing()."""
        n = sy = sx = 0
        for dy in range(-BANK_R, BANK_R + 1):
            for dx in range(-BANK_R, BANK_R + 1):
                if at(high, x + dx, y + dy):
                    n += 1
                    sy += dy
                    sx += dx
        if n == 0:
            return -1.0
        cy, cx = sy / float(n), sx / float(n)
        m = np.hypot(cx, cy)
        return -1.0 if m < 0.05 else -cy / m

    def bank(x, y):
        for k, lo in enumerate(BANK_FACING):
            if facing(x, y) >= lo:
                return len(BANK_FACING) - k
        return 0

    # The band is only masked where the wall it draws is deep enough to want a
    # tile of its own; the rest of the way round, the bank off the outline is
    # the whole of it. Cut here rather than when drawing, because the cases are
    # taken off this mask and every one of them has to be drawn for them to
    # join up.
    for y in range(H):
        for x in range(W):
            if face[y, x] and bank(x, y) < BANK_FRONT:
                face[y, x] = False

    def face_code(x, y):
        def covered(cx, cy):
            box = ((-1, -1), (0, -1), (-1, 0), (0, 0))
            nf = sum(1 for ox, oy in box if at(face, cx + ox, cy + oy))
            if nf >= 3:
                return True
            return nf >= 2 and any(at(high, cx + ox, cy + oy) for ox, oy in box)
        return ((1 if covered(x, y) else 0) | (2 if covered(x + 1, y) else 0)
              | (4 if covered(x, y + 1) else 0) | (8 if covered(x + 1, y + 1) else 0))

    def high_code(x, y):
        def covered(cx, cy):
            box = ((-1, -1), (0, -1), (-1, 0), (0, 0))
            return sum(1 for ox, oy in box if at(high, cx + ox, cy + oy)) >= 3
        return ((1 if covered(x, y) else 0) | (2 if covered(x + 1, y) else 0)
              | (4 if covered(x, y + 1) else 0) | (8 if covered(x + 1, y + 1) else 0))

    def rock_code(x, y):
        if not (at(face, x, y) or at(face, x - 1, y) or at(face, x + 1, y)
                or at(face, x, y - 1) or at(face, x, y + 1)):
            return 0
        return face_code(x, y)

    GRASS = (168, 240, 188)
    out = np.zeros((H * CELL, W * CELL, 3), dtype=np.uint8)
    out[:, :] = GRASS

    def put(row, x, y):
        col = (y % BLOCK) * BLOCK + (x % BLOCK)
        cell = sheet[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL]
        dst = out[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL]
        vis = ~np.all(cell == KEY, axis=2)
        dst[vis] = cell[vis]

    for y in range(H):
        for x in range(W):
            hc = high_code(x, y)
            if hc and hc != 15:
                # The widest bank at the front too, under the band — the mask
                # has holes the facing knows nothing about, and a hole in it
                # with the bare line running through is the cliff breaking.
                b = min(bank(x, y), BANK_FRONT - 1)
                put((BANK_ROW0 + (b - 1) * NCASE if b else EDGE_ROW0) + hc, x, y)
            c = rock_code(x, y)
            if c:
                put(ROCK_ROW0 + c, x, y)
                continue
            for step in range(SCREE_STEPS):
                if y - 1 - step >= 0 and rock_code(x, y - 1 - step):
                    put(SCREE_ROW0 + step, x, y)
                    break
    Image.fromarray(out).save(path)
    print('preview ->', path)


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', default='assets/tileset.png')
    ap.add_argument('--preview')
    ap.add_argument('--no-write', action='store_true')
    a = ap.parse_args()

    img = Image.open(a.sheet).convert('RGB')
    sheet = np.array(img)
    need = (HAZE_ROW0 + NCASE) * CELL
    if sheet.shape[0] < need:
        raise SystemExit('sheet is only %d px tall, need %d' % (sheet.shape[0], need))

    stamp(sheet, ROCK_ROW0, rock_cell)
    stamp(sheet, EDGE_ROW0, edge_cell)
    stamp(sheet, SCREE_ROW0, scree_cell, SCREE_STEPS)
    for k, reach in enumerate(BANK_REACH):
        stamp(sheet, BANK_ROW0 + k * NCASE,
              lambda case, bx, by, r=reach: edge_cell(case, bx, by, r))
    stamp(sheet, HAZE_ROW0, haze_cell)

    if a.preview:
        preview(a.preview, sheet)
    if not a.no_write:
        Image.fromarray(sheet).save(a.sheet)
        print('wrote %s: band rows %d-%d, outline %d-%d, spill %d-%d, banks %d-%d, '
              'height mask %d-%d'
              % (a.sheet, ROCK_ROW0, ROCK_ROW0 + NCASE - 1,
                 EDGE_ROW0, EDGE_ROW0 + NCASE - 1,
                 SCREE_ROW0, SCREE_ROW0 + SCREE_STEPS - 1,
                 BANK_ROW0, BANK_ROW0 + NCASE * len(BANK_REACH) - 1,
                 HAZE_ROW0, HAZE_ROW0 + NCASE - 1))


if __name__ == '__main__':
    main()
