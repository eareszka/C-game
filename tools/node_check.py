"""Check every cave rock node sits on floor rather than on a hole.

A dungeon rock node has no sprite of its own -- it IS the TALL_BAND_SOLO (32:0)
wall tile (see cave_tile_is_rock_candidate). That art is a shaped cluster with
transparent margins and a wall tile gets no base fill, so its margins used to
show the renderer's raw clear colour: the node read as a hole punched in the
passage. This measures that directly, per node tile:

  clear   pixels still showing the clear colour     -- must reach 0
  floor   pixels showing the cave floor colour      -- the new backdrop
  other   the sprite itself

Node identification mirrors cave_wall_classify()'s tall_band_standalone, which is
NOT the same as "floor north and south" -- the cardinal>=3 arm also makes a node
out of a tile with floor N/E/W and WALL to the south. Both kinds are counted and
reported separately, because a check that only found the first kind is exactly
how the earlier cave_is_solo_boulder() gap stayed invisible.

Usage:
  python tools/node_check.py <map.txt> <map_ox> <map_oy> <cam_tx> <cam_ty> <tw> <th> <render.png> [ore]

`ore` is the Material index the render was made with (DNGSHOT_ORE), and it
matters: the backdrop is painted in the cave's OWN floor colour, so checking a
Bronze render against Veyrite's floor reports every backdrop pixel as sprite and
quietly stops measuring the thing this script exists to measure. Defaults to 3
(Veyrite), which is what an un-forced cave used to be.
"""
import sys
import numpy as np
from PIL import Image

TILE = 32
CLEAR = (5, 5, 8)        # main.cpp STATE_DUNGEON clear

# MaterialDef::floor from src/dungeon.cpp, in Material order.
FLOORS = [(108, 108, 116),   # Stone
          (110, 88, 58),     # Bronze
          (70, 105, 78),     # Emerald
          (90, 80, 74),      # Veyrite
          (110, 64, 60),     # Dravium
          (120, 105, 55),    # Kharvite
          (30, 28, 34)]      # Reality Shard


def main():
    rows = [ln.rstrip('\n') for ln in open(sys.argv[1]) if ln.strip()]
    ox, oy, cam_tx, cam_ty, tw, th = (int(a) for a in sys.argv[2:8])
    im = np.array(Image.open(sys.argv[8]).convert('RGB'))
    floor_rgb = FLOORS[int(sys.argv[9]) if len(sys.argv) > 9 else 3]
    H, W = im.shape[:2]

    def floor_at(x, y):
        lx, ly = x - ox, y - oy
        if not (0 <= lx < len(rows[0]) and 0 <= ly < len(rows)):
            raise IndexError(f"tile ({x},{y}) outside dumped window")
        return rows[ly][lx] == '.'

    bad = 0
    counts = {'floor N+S': 0, 'cardinal>=3': 0}
    for ty in range(cam_ty, cam_ty + th):
        for tx in range(cam_tx, cam_tx + tw):
            if floor_at(tx, ty):
                continue
            fs, fn = floor_at(tx, ty + 1), floor_at(tx, ty - 1)
            fe, fw = floor_at(tx + 1, ty), floor_at(tx - 1, ty)
            if not ((fs or (fs + fn + fe + fw) >= 3) and fn):
                continue
            kind = 'floor N+S' if fs else 'cardinal>=3'
            counts[kind] += 1
            px, py = (tx - cam_tx) * TILE, (ty - cam_ty) * TILE
            if px + TILE > W or py + TILE > H:
                continue
            cell = im[py:py + TILE, px:px + TILE]
            clear = int(np.all(cell == CLEAR, axis=2).sum())
            floor = int(np.all(cell == floor_rgb, axis=2).sum())
            if clear:
                bad += 1
                print(f"  FAIL node({tx},{ty}) [{kind}] still shows {clear}/1024 clear px")
            else:
                print(f"  ok   node({tx},{ty}) [{kind}] clear=0 floor={floor}/1024")

    total = sum(counts.values())
    print(f"{total} nodes ({counts['floor N+S']} floor N+S, "
          f"{counts['cardinal>=3']} cardinal>=3), {bad} still holed")
    if bad:
        sys.exit(1)


main()
