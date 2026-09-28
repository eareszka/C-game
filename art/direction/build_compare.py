"""Before/after board: the game as it first looked, and as it renders now.
Same three views, same seeds, same places.

    python art/direction/build_compare.py

Run from the repo root, after `make shot`. The befores are frozen in before/
(the original game, cut from the first version of this board); the afters are
rendered fresh by shot.exe, so the board always shows the current build.

Everything is assembled through the pixel-plugin's pixel-mcp server (mcpc.py):
  fc_compare.aseprite / .png  the board, one layer per view and side, with
                              the game's palette set as the sprite's own
  fc_palette.aseprite         the palette (game_palette.gpl) as swatches, one
                              row per hue family -- open it and use it as the
                              palette for new art, and whatever is painted is
                              on the palette already
"""
import os, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
sys.path.insert(0, HERE)
from mcpc import Pixel
import fcremap as fc

ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = HERE + "/_work"
os.makedirs(WORK, exist_ok=True)

# (label, seed, tile x, tile y) -- a field and coast, a cliff, the waste edge.
# The befores in before/ were rendered from exactly these.
VIEWS = [
    ("meadow and coast", 630, 1480, 1380),
    ("cliff and plateau", 678, 990, 1665),
    ("meadow into wasteland", 630, 2960, 2480),
]
TW, TH = 40, 25                      # tiles per view: 1280x800 rendered, 640x400 art pixels


def hexc(c):
    return "#%02x%02x%02x" % c


pairs = []
for i, (label, seed, x, y) in enumerate(VIEWS):
    raw = f"{WORK}/view{i}.png"
    subprocess.run([ROOT + "/shot.exe", str(seed), raw, str(x), str(y), str(TW), str(TH)],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    # The renderer draws every art pixel as 2x2; halve back to art pixels.
    im = Image.open(raw).convert("RGBA")
    im = im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    after = f"{WORK}/after{i}.png"
    im.save(after)
    off = {c for c in im.convert("RGB").getdata() if c not in set(fc.PALETTE)}
    if off:
        print(f"{label}: {len(off)} colours off the palette, e.g. {sorted(off)[:4]}")
    pairs.append((label, f"{HERE}/before/view{i}.png", after, im.width, im.height))

px = Pixel()
palette = [hexc(c) for c in fc.PALETTE]

GAP = 8
W = pairs[0][3] * 2 + GAP
H = sum(p[4] for p in pairs) + GAP * (len(pairs) - 1)
spr = px.call("create_canvas", width=W, height=H, color_mode="rgb")["file_path"]
y = 0
for i, (label, before, after, w, h) in enumerate(pairs):
    px.call("import_image", sprite_path=spr, image_path=before, layer_name=f"before {i+1}",
            frame_number=1, position={"x": 0, "y": y})
    px.call("import_image", sprite_path=spr, image_path=after, layer_name=f"fc {i+1}",
            frame_number=1, position={"x": w + GAP, "y": y})
    y += h + GAP
try:
    px.call("delete_layer", sprite_path=spr, layer_name="Layer 1")
except Exception:
    pass
px.call("set_palette", sprite_path=spr, colors=palette)
board = HERE + "/fc_compare.aseprite"
px.call("save_as", sprite_path=spr, output_path=board)
px.call("export_sprite", sprite_path=board, output_path=HERE + "/fc_compare.png", format="png",
        frame_number=0)

# The palette as a swatch sheet: one row per hue family, dark to light, so the
# ramps the art is built from can be read off it.
def family(c):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[u / 255 for u in c])
    if s < 0.2 or v < 0.1:
        return 0                                      # greys and near-blacks
    return 1 + int(((h * 360 + 15) % 360) // 60)       # six hue bands
rows = {}
for c in fc.PALETTE:
    rows.setdefault(family(c), []).append(c)
SW = 16
width = SW * max(len(r) for r in rows.values())
sheet = px.call("create_canvas", width=width, height=SW * len(rows), color_mode="rgb")["file_path"]
px.call("set_palette", sprite_path=sheet, colors=palette)
for ry, key in enumerate(sorted(rows)):
    for rx, c in enumerate(sorted(rows[key], key=fc.luma)):
        px.call("draw_rectangle", sprite_path=sheet, layer_name="Layer 1", frame_number=1,
                x=rx * SW, y=ry * SW, width=SW, height=SW, color=hexc(c), filled=True)
px.call("save_as", sprite_path=sheet, output_path=HERE + "/fc_palette.aseprite")
print("wrote", board, "and fc_palette.aseprite")
