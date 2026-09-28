"""Trees and houses in FC World's style, stamped into assets/tileset.png.

    python art/structures/build_fc_structures.py            # preview only
    python art/structures/build_fc_structures.py --stamp    # also write the sheet

Run from the repo root. See art/direction/ART_DIRECTION.md for the mood this
follows; this script is where that direction becomes the game's actual trees
and houses.

INPUT. master.png is the sheet's top-left corner (cols 0-20, rows 0-5) as it
was before this existed, frozen so the script can be re-run: the houses are
repainted from it, and it is what the stamp diffs against. It is never written.

HOUSES keep their drawing and change their materials. Every black pixel of the
master stays black and every key pixel stays key, so the silhouette, the
footprint the town collision layouts were written against, and the door cells
the interior doors are registered at (1288, 1294 in towns.h) are all exactly as
before. What is inside the lines is repainted by role:

    roof        shingles; wood for the stone house, slate for the white one
    front wall  khaki brick (stone house), lavender siding (white house)
    side, gable one flat shade darker than its front wall
    door        wood planks
    window      dark glass behind bars

The roles come from the master's own structure, not from coordinates: pixels
are split into regions by the black lines between them, and each region is
named by where it sits and what it holds. See house_roles().

TREES are drawn fresh, in FC World's tree language -- a hard black outline,
three sage greens, shadow massed low and right and broken up with black,
highlights sparse and high on the left -- but they are original drawings, not
copies of Yume Nikki's sprites. The dead tree (col 20) is left as it is: its
maroons are already FC World's wasteland palette.

The renderer picks cells as follows (src/tilemap.cpp, tilemap_draw_impl):
    (15,1)          solo tree, single tile; also the tree resource node
    (16,0)+(16,1)   tall tree, canopy + trunk
    (17,0)+(17,1)   tall tree, the other variant
    (18,*),(19,*)   trees on snow
Transparency is the colour key (255,0,0), never alpha.
"""
import os, sys
from collections import deque
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/direction")
import fcremap

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEET = ROOT + "/assets/tileset.png"
KEY = (255, 0, 0)
K = (0, 0, 0)


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


# ── Palette ─────────────────────────────────────────────────────────────────
# All from FC World's own sprites, except snow: a cap is the ground it fell
# from, so it is the snow tile's own colour, and whatever recolours the ground
# recolours the caps with it.
PAL = {
    "k": K,
    "D": hx("#325a23"), "M": hx("#649655"), "L": hx("#82b473"),   # foliage
    "S": fcremap.lookup(hx("#fcfcfc")),   # the snow ground's colour, wherever it goes
    ".": KEY,
}

# Each house is one NES sub-palette: black and three colours, shared by every
# cell of it, so no tile of a house can hold more than four (see the rule in
# tools/palette_pass.py). Roles, light to dark:
def materials(light, mid, dark):
    return dict(face=light, roof=(mid, dark), side=mid, line=dark,
                plank=mid, gap=dark, knob=light, glass=K, bar=mid)

STONE = materials(hx("#b1bf7f"), hx("#8d6b4f"), hx("#4e3633"))   # khaki brick, wood
WHITE = dict(materials(hx("#9b94b3"), hx("#726f8d"), hx("#504b70")),
             side=hx("#504b70"))                                  # lavender, slate


# ── Trees ───────────────────────────────────────────────────────────────────
SOLO = """
................
......kkkk......
....kkMLMMkk....
...kMLLMMMMDk...
..kMLMMMMMDMDk..
..kMMMMMDMMDDk..
..kMLMMDMMDkDk..
..kkMMMMDMDDkk..
..kMkkDMDDkkDk..
..kMMMkkkkMDDk..
...kMDMMDMDDk...
....kkDDkDkk....
......kkkk......
.......kkk......
......kkkkk.....
.....k..kk.k....
"""

OVAL = """
................
................
................
................
......kkkk......
.....kMLMMk.....
....kMLLMMDk....
....kLLMMMDk....
...kMLMMMDMDk...
...kMLMMMMDDk...
..kMMMMMMDMDDk..
..kMLMMMMMDMDk..
..kMMMMMDMDDDk..
..kMMLMMMMDDkk..
.kMMMMMMMDMDDDk.
.kMMMMMMDMDkDDk.
.kMMMMMDMMDDDkk.
.kMMDMMMMDMDkDk.
.kMMMMMDMDDDDDk.
.kMDMMDMDMDkDkk.
.kMMDMDMDDDDkDk.
.kDMDDMDDDkDDkk.
..kDDMDDDkDkDk..
..kkDDDkDkDkk...
...kkDkDkkkk....
.....kkkkkk.....
.......kkk......
.......kkk......
.......kkkk.....
......kkkkk.....
.....k.kkkk.k...
................
"""

CLUMPS = """
................
......kkkk......
....kkMLMMkk....
...kMMLLMMMDk...
...kMLMMMMDDk...
...kMMMMDMDkk...
...kkMDMDDkDk...
..kMMkkDDkkMMk..
.kMLMMMkkkMMDDk.
.kMLMMMMDkMMDDk.
.kMMMMMDDkMDDkk.
.kkMMDMDDkkDkDk.
.kMkkDDDkkDDkkk.
.kMMMkkkMMkkkMk.
kMLMMMMMMMMDkMDk
kMLMMMMMMMDDDkDk
kMMMMMMMMDMDDkDk
kMMMDMMMDMDDkDDk
kkMMMDMDMDDDkDkk
kMkkMDDDDDDkkkMk
kMMMkkkkkkkkMMDk
kMLMMMMMMMMMMDDk
kMMMMMMMMMDMDDkk
kkMMDMMDMDDDkDDk
.kkDDMDDDDDkDkk.
..kkkkDDDkkkkk..
.....kkkkkk.....
.......kkk......
.......kkk......
......kkkkk.....
.....k.kkk.k....
................
"""

CONIFER_SMALL = """
................
................
................
................
................
................
.......kk.......
......kSSk......
......kMDk......
.....kSMMDk.....
.....kkMDkk.....
....kSSkkDDk....
....kMMSSDDk....
...kkkMMDDkkk...
...kSSkkkDDDk...
..kSSMMMSDDDDk..
..kMMMDMMDDkDk..
..kkkkMMDDkkkk..
..kSSSkkkDDDDk..
.kSSMMMMSSDDDDk.
.kMMMDMMMDDkDDk.
.kkkkMMDMDkkkkk.
....kkkkkkkk....
.......kkk......
.......kkk......
......kkkkk.....
.....k.kkk.k....
................
................
................
................
................
"""

CONIFER_TALL = """
................
.......kk.......
......kSSk......
......kMDk......
.....kSMMDk.....
.....kMMDDk.....
....kSSkkDDk....
....kkMSSkkk....
....kSMMMDDk....
...kSMMDMDDDk...
...kkkkMDDkkk...
...kSSSkkkDDk...
..kSSMMMMDDDDk..
..kMMMDMMDDkDk..
..kkkkMMDDkkkk..
..kSSSkkkDDDDk..
.kSSMMMMSDDDDDk.
.kMMMMDMMMDDkDk.
.kkkkMMMDDkkkkk.
.kSSSkkkDDDDDDk.
kSSMMMMMSSDDDDDk
kMMMMDMMMMDDDkDk
kMMDMMMDMDDkDDDk
kkkkMMMDMDDkkkkk
...kkkkkkkkkk...
.......kkk......
.......kkk......
......kkkkk.....
.....k.kkk.k....
................
................
................
"""

# (sprite, cell col, top cell row). Tall sprites span rows 0-1, solo only row 1.
TREES = [(SOLO, 15, 1), (OVAL, 16, 0), (CLUMPS, 17, 0),
         (CONIFER_SMALL, 18, 0), (CONIFER_TALL, 19, 0)]


def parse(art):
    rows = [r for r in art.strip("\n").split("\n")]
    assert all(len(r) == 16 for r in rows), [len(r) for r in rows]
    assert len(rows) in (16, 32), len(rows)
    return [[PAL[c] for c in r] for r in rows]


# ── Houses ──────────────────────────────────────────────────────────────────
# Each house: its box in master.png, a point inside its side wall, the row of
# the eave (last roof row), and its materials.
HOUSES = [
    dict(name="stone", box=(16, 0, 96, 96), side_seed=(85, 70), eave=50,
         mat=STONE, wall="brick"),
    dict(name="white", box=(96, 0, 234, 96), side_seed=(215, 70), eave=50,
         mat=WHITE, wall="siding"),
]


def flood(seed, ok, diagonal=False):
    """Pixels connected to seed through pixels where ok(p) holds."""
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen, q = {seed}, deque([seed])
    while q:
        a, b = q.popleft()
        for dx, dy in steps:
            n = (a + dx, b + dy)
            if n not in seen and ok(n):
                seen.add(n)
                q.append(n)
    return seen


def silhouette(px, h):
    """The house itself: every non-key pixel joined to its side wall. The box
    alone is not enough -- the white house's box clips the water tile at (14,0)
    and the stump at (14,2)."""
    x0, y0, x1, y1 = h["box"]
    return flood(h["side_seed"], lambda p: x0 <= p[0] < x1 and y0 <= p[1] < y1
                 and px[p] != KEY, diagonal=True)


def regions(px, mask):
    """4-connected regions of non-black pixels within mask."""
    seen, out = set(), []
    for p in sorted(mask, key=lambda p: (p[1], p[0])):
        if p in seen or px[p] == K:
            continue
        comp = flood(p, lambda n: n in mask and px[n] != K)
        seen |= comp
        out.append(list(comp))
    return out


def house_roles(px, h):
    """Name every pixel of a house: roof, wall, side, door, window. Black and
    key pixels are left out -- they are never repainted, except that black
    lines *inside* the roof belong to the old tiling and are repainted too."""
    x0, y0, x1, y1 = h["box"]
    body = silhouette(px, h)
    comps = regions(px, body)
    side = next(c for c in comps if h["side_seed"] in set(c))
    side_set = set(side)
    below = [c for c in comps if c is not side and min(y for _, y in c) > h["eave"]]
    wall = max(below, key=len)
    role = {p: "side" for p in side}
    for p in wall:
        role[p] = "wall"
    for c in below:
        if c is wall:
            continue
        # The master's glass is pale green; a door is anything else walled off.
        glassy = any(px[p] == (168, 240, 188) for p in c)
        for p in c:
            role[p] = "window" if glassy else "door"
    # Glass on the side wall sits in its own framed regions above the eave line
    # of the wall too; catch any glass region not yet named.
    for c in comps:
        if c is side or c is wall or c[0] in role:
            continue
        if any(px[p] == (168, 240, 188) for p in c):
            for p in c:
                role[p] = "window"
    # Roof: in each row above the eave, the run from the house's left edge up
    # to the black line before the gable. Its outline is kept: the leading
    # black pixels on the left and the trailing ones against the gable.
    for y in range(y0, h["eave"] + 1):
        xs = [x for x in range(x0, x1) if (x, y) in body]
        if not xs:
            continue
        gable = [x for x in xs if (x, y) in side_set]
        end = (min(gable) if gable else max(xs) + 1)
        span = [x for x in xs if x < end]
        if not span or all(px[x, y] == K for x in span):
            continue                                # ridge rows stay solid
        lo = 0
        while lo < len(span) and px[span[lo], y] == K:
            lo += 1
        hi = len(span)
        while hi > lo and px[span[hi - 1], y] == K:
            hi -= 1
        for x in span[lo:hi]:
            if (x, y) not in role:
                role[(x, y)] = "roof"
    return role, body


def shingle(x, y, x0, y0, light, dark):
    """Overlapping shingle courses: 6 rows tall, tiles 8 wide, alternate courses
    offset half a tile. Each tile is lit at the top and shaded at its lower
    right, with a black seam below it and between it and its neighbour."""
    course, r = divmod(y - y0, 6)
    c = (x - x0 + (4 if course % 2 else 0)) % 8
    if r == 5 or c == 7:
        return K
    if r == 4 or (c == 6 and r >= 2):
        return dark
    return light


def paint_house(src, dst, h):
    px, out = src.load(), dst.load()
    role, _ = house_roles(px, h)
    x0, y0 = h["box"][0], h["box"][1]
    m = h["mat"]
    brick = h["wall"] == "brick"
    for (x, y), r in role.items():
        c = px[x, y]
        if r == "roof":
            out[x, y] = shingle(x, y, x0, y0, *m["roof"])
        elif r == "side":
            out[x, y] = m["side"]
        elif r == "wall":
            if brick:
                # Keep the master's brick bond: white faces, grey mortar.
                out[x, y] = m["face"] if c == (255, 255, 255) else m["line"]
            else:
                # Vertical siding boards, 6 wide, a shaded edge on each.
                out[x, y] = m["line"] if (x - x0) % 6 == 5 else m["face"]
        elif r == "door":
            # Planks: the master's light stripes become the dark gaps.
            if c in ((255, 255, 255), (168, 240, 188)):
                out[x, y] = m["knob"]
            elif c == (151, 151, 170):
                out[x, y] = m["gap"]
            else:
                out[x, y] = m["plank"]
        elif r == "window":
            # Dark glass behind bars, FC World's window.
            out[x, y] = m["bar"] if (x - x0) % 3 == 0 else m["glass"]
    # The old roof tiling left black bits outside the new courses' pattern on
    # the stone house; those were repainted above. Add an outline wherever a
    # roof pixel meets the key, so the slope edge is a hard black line.
    for (x, y), r in role.items():
        if r == "roof" and any(px[n] == KEY for n in ((x - 1, y), (x, y - 1))):
            out[x, y] = K


def build():
    # Worked in RGB: the atlas is opaque throughout, transparency is the key.
    master = Image.open(HERE + "/master.png").convert("RGB")
    fc = master.copy()
    for h in HOUSES:
        paint_house(master, fc, h)
    out = fc.load()
    for art, col, row in TREES:
        grid = parse(art)
        for y, r in enumerate(grid):
            for x, c in enumerate(r):
                out[col * 16 + x, row * 16 + y] = c
    check(master, fc)
    return master, fc


def owned(master):
    """Every pixel this script paints: each house's silhouette and each tree
    cell, whole. Everything else in master's area belongs to other art."""
    mp = master.load()
    out = set()
    for h in HOUSES:
        out |= silhouette(mp, h)
    for _, col, row in TREES:
        out |= {(col * 16 + x, row * 16 + y) for x in range(16)
                for y in range(32 if row == 0 else 16)}
    return out


def check(master, fc):
    """The houses' lines and footprint must not move, and nothing outside what
    this script owns may change."""
    mp, fp = master.load(), fc.load()
    for h in HOUSES:
        role, body = house_roles(mp, h)
        for p in body:
            if mp[p] == K and p not in role:
                assert fp[p] == K, (h["name"], "a line moved", p)
    mine = owned(master)
    for y in range(master.height):
        for x in range(master.width):
            if (x, y) not in mine:
                assert fp[x, y] == mp[x, y], ("outside the houses and trees", x, y)
    # The 8-bit rules (tools/palette_pass.py): the palette, and four colours a
    # cell. Art that meets them is left alone by the pass, so the two scripts
    # agree instead of undoing each other.
    cells = {}
    for x, y in mine:
        c = fp[x, y]
        if c != KEY:
            assert c in fcremap.PALETTE, ("off the palette", x, y, c)
            cells.setdefault((x // 16, y // 16), set()).add(c)
    over = {k: len(v) for k, v in cells.items() if len(v) > 4}
    assert not over, ("more than four colours", over)


def preview(master, fc, path):
    """Before/after on the grounds these sit on in game: grass, meadow, snow."""
    grounds = [fcremap.lookup(hx(c)) for c in ("#4edc4a", "#a8f0bc", "#fcfcfc")]
    w, h = master.size
    board = Image.new("RGB", (w * 2 + 8, (h + 4) * len(grounds)), (32, 32, 32))
    for i, g in enumerate(grounds):
        for j, im in enumerate((master, fc)):
            tile = Image.new("RGB", im.size, g)
            p, t = im.load(), tile.load()
            for y in range(h):
                for x in range(w):
                    if p[x, y] != KEY:
                        t[x, y] = p[x, y]
            board.paste(tile, (j * (w + 8), i * (h + 4)))
    board = board.resize((board.width * 3, board.height * 3), Image.NEAREST)
    board.save(path)


def aseprite_source(master, fc):
    """fc_structures.aseprite: the original and the FC art as two layers over
    the same cells, built through the pixel-plugin's server. The script, not
    this file, is the source of truth; the file is for looking and comparing,
    and for sketching changes to bring back into the ASCII above."""
    from mcpc import Pixel
    work = HERE + "/_work"
    os.makedirs(work, exist_ok=True)
    master.convert("RGBA").save(work + "/master.png")
    fc.convert("RGBA").save(work + "/fc.png")
    px = Pixel()
    spr = px.call("create_canvas", width=master.width, height=master.height,
                  color_mode="rgb")["file_path"]
    px.call("import_image", sprite_path=spr, image_path=work + "/master.png",
            layer_name="original", frame_number=1, position={"x": 0, "y": 0})
    px.call("import_image", sprite_path=spr, image_path=work + "/fc.png",
            layer_name="fc world", frame_number=1, position={"x": 0, "y": 0})
    try:
        px.call("delete_layer", sprite_path=spr, layer_name="Layer 1")
    except Exception:
        pass
    px.call("save_as", sprite_path=spr, output_path=HERE + "/fc_structures.aseprite")


def stamp(master, fc):
    """Write the owned pixels into the sheet. This script is their source of
    truth -- a hand edit to a tree or house in the sheet is overwritten, so
    make it in the art above. The pixels around them are not its to touch.
    Those may since have been recoloured (tools/palette_pass.py) or blanked
    (tools/prune_sheet.py); what the stamp refuses is new art next to its
    own, where master had only key, because a stamp would then be painting
    into someone's work without knowing it."""
    sheet = Image.open(SHEET).convert("RGB")
    sp, mp, fp = sheet.load(), master.load(), fc.load()
    mine = owned(master)
    for y in range(master.height):
        for x in range(master.width):
            if (x, y) not in mine and mp[x, y] == KEY and sp[x, y] != KEY:
                sys.exit(f"tileset.png at {x},{y} (cell {x // 16},{y // 16}) has art "
                         "where master.png has none, next to the houses or trees. "
                         "Fold it into master.png first.")
    n = 0
    for x, y in mine:
        if sp[x, y] != fp[x, y]:
            sp[x, y] = fp[x, y]
            n += 1
    sheet.convert("RGBA").save(SHEET)
    print(f"stamped {n} changed pixels into {SHEET}")


if __name__ == "__main__":
    master, fc = build()
    fc.convert("RGBA").save(HERE + "/fc_structures.png")
    preview(master, fc, HERE + "/_preview.png")
    aseprite_source(master, fc)
    print("wrote fc_structures.png, fc_structures.aseprite and _preview.png")
    if "--stamp" in sys.argv:
        stamp(master, fc)
