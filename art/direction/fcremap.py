"""The game's palette, and where every old colour goes on it.

PALETTE is FC World's own: the 64 colours of its tileset
(fc_world_reference.png, from The Spriters Resource), less the three key
colours the sheet is laid out on. Nothing the game draws should be anything
else -- that single constraint is most of what makes it read as 8-bit rather
than 16-bit. The other part is how many of them one tile uses; see
tools/palette_pass.py, which applies this module to the art.

REMAP says where the old colours go, family by family. Two rules keep the
drawing intact:

- Within a family the light-to-dark order is kept, so a tuft is still darker
  than the grass it sits on and a crack is still darker than its rock.
- Grounds that meet stay apart. Grass and meadow, sand and rock, sand and
  trail are all neighbours in the world, and the biome edges are drawn in the
  grounds' own colours, so two that landed on one colour would lose their
  border.

A colour REMAP does not name goes to the nearest palette colour (CIELAB),
never to an accent: the saturated few FC World uses once per screen, which
only a deliberate REMAP entry may pick.
"""
import os
from functools import lru_cache
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = {(255, 0, 0), (0, 0, 255), (255, 0, 255)}


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _load_palette():
    ref = Image.open(os.path.join(HERE, "fc_world_reference.png")).convert("RGB")
    counts = {}
    for c in ref.getdata():
        counts[c] = counts.get(c, 0) + 1
    return sorted((c for c in counts if c not in KEYS), key=lambda c: -counts[c])


PALETTE = _load_palette()
ACCENTS = {hx(c) for c in ("#00fc00", "#00c100", "#ffff00", "#661dde", "#8c69e8", "#7c007c")}

REMAP = {
    # grounds: bright NES greens -> FC olives, meadow the lightest field
    "#a8f0bc": "#9aaa7a",   # meadow
    "#86e389": "#9aaa7a",   # raised grass (only the retired ladder used it)
    "#6de06d": "#6e834f",   # forest grass
    "#4edc4a": "#6e834f",   # grass
    "#54ac6a": "#649655",   # tuft light
    "#2f9c47": "#325a23",   # tuft
    "#05c43a": "#649655",
    "#00a800": "#6e834f",   # meadow sprig, one step under the meadow
    "#058f3a": "#325a23",   # tree body
    "#00881b": "#325a23",   # grass tuft
    "#fc74b4": "#75264f",   # blossom: still the brightest thing in a meadow
    # the sea: sky blue with white foam -> the violet void with violet foam.
    # White is foam only inside the water cell; see palette_pass.WATER_CELLS.
    "#5c94fc": "#18003b",
    # snow: white -> pale lavender stone; its gold scrub dims to old brass
    "#fcfcfc": "#9b94b3",
    "#eaf0f7": "#9b94b3",
    "#dcf0ff": "#9797aa",
    "#f0bc3c": "#8c7747",
    # desert: pale yellow sand -> FC's khaki and browns, never yellow
    "#e8e0c0": "#b1bf7f",
    "#f0e880": "#8c7747",
    "#e0b954": "#8c7747",
    "#d0c078": "#725a37",
    # town paths: tan -> the khaki FC World floors its rooms with
    "#d7a175": "#b1bf7f",
    # (trail banks and cave rock are ramps per block: palette_pass.RAMPS)
    "#b2966a": "#8d6b4f",
    "#92744c": "#725a37",
    "#9b8773": "#725a37",
    # cliff rock: olive-brown -> FC boulder brown; the cracks stay black
    "#887000": "#60413d",
    "#4b4137": "#4e3633",
    "#82662a": "#725a37",
    "#23180c": "#260e00",
    # cool greys (stones, dead wood)
    "#54565a": "#5d5a5a",
    "#2f3032": "#3c3c3c",
    "#141a21": "#151e37",
    # the player: skin to FC's pale pink, orange hair and coat to warm brown,
    # blue to FC's blue, near-black to its charcoal
    "#f0b890": "#ffe3ff",
    "#d89830": "#8d6b4f",
    "#2850a0": "#4f53a9",
    "#282828": "#3c3c3c",
    # wasteland: FC World's own ground already
    "#2e1109": "#270800", "#351a11": "#3e1c0e", "#1a0a09": "#110000",
    "#221311": "#260e00", "#280000": "#270800",
}
LUT = {hx(k): hx(v) for k, v in REMAP.items()}
assert all(v in PALETTE for v in LUT.values()), \
    [k for k, v in REMAP.items() if hx(v) not in PALETTE]


def _lab(c):
    def lin(u):
        u /= 255
        return ((u + 0.055) / 1.055) ** 2.4 if u > 0.04045 else u / 12.92
    r, g, b = map(lin, c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


_AUTO = [(c, _lab(c)) for c in PALETTE if c not in ACCENTS]


def lab_dist(a, b):
    la, lb = _lab(a), _lab(b)
    return sum((p - q) ** 2 for p, q in zip(la, lb))


@lru_cache(maxsize=None)
def nearest(c):
    """The closest palette colour to c that is not an accent."""
    lc = _lab(c)
    return min(_AUTO, key=lambda e: sum((p - q) ** 2 for p, q in zip(lc, e[1])))[0]


def lookup(c):
    """Where colour c goes: itself if already on the palette, else REMAP's
    choice, else the nearest non-accent palette colour."""
    if c in KEYS or c in PALETTE:
        return c
    return LUT.get(c) or nearest(c)


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def remap_image(im):
    """Recolour an RGB(A) PIL image onto the palette. Returns the image and the
    colours REMAP did not name (they went to their nearest), so a family the
    table ought to cover shows up rather than being quietly approximated."""
    im = im.convert("RGBA")
    px = im.load()
    missed = {}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            c = (r, g, b)
            if c not in KEYS and c not in PALETTE and c not in LUT:
                missed[c] = missed.get(c, 0) + 1
            px[x, y] = (*lookup(c), a)
    return im, missed
