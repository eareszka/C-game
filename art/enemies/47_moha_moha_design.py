"""47 Moha Moha: corrected jaws and continuous tail, approved head/neck motion.

Original user keys remain untouched. Seven flat pixel poses are authored via
47_moha_moha_correct.py into 47_moha_moha_corrected_poses.aseprite/.png.
This generator reads that verified export, applies the existing 24-frame
breathing/timing schedule, and writes the build inputs beside this source.

    python art/enemies/47_moha_moha_design.py
"""
from pathlib import Path
import math
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tools'))
import flat_parts

W, H = 98, 65
PAL = {'K': '000000', 'g': '2c6c44', 'G': '4fa667', 'B': 'cebe82',
       's': '474751', 'm': '595965', 'S': '848694', 'T': '633e1b', 'W': 'fcfcfc'}
RGB = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, h in PAL.items()}
LETTER = {rgb: c for c, rgb in RGB.items()}
FRAME_MS = 100
EASE = lambda u: (1 - math.cos(math.pi * u)) / 2
UP = [EASE(i / 6) for i in range(1, 7)]
POSE_STEPS = [0, *UP]
MOVE = [0] * 6 + UP + [1] * 4 + UP[::-1][1:] + [0] * 3
BREATH_ROW = 52
BREATH = [round(EASE(1 - abs(((i / 12) % 1) * 2 - 1))) for i in range(24)]
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)


def POSES():
    im = Image.open(HERE / '47_moha_moha_corrected_poses.png').convert('RGBA')
    assert im.size == (7 * W, H), im.size
    poses = []
    for i in range(7):
        g = {}
        for y in range(H):
            for x in range(W):
                p = im.getpixel((i * W + x, y))
                assert p[3] in (0, 255), ('partial alpha', i, x, y)
                if p[3]:
                    assert p[:3] in LETTER, ('off-palette pixel', i, x, y, p)
                    g[x, y] = LETTER[p[:3]]
        poses.append(g)
    return poses


def breathe(g, b):
    # Preserve the existing one-pixel dip above the legs; feet remain planted.
    return {**{p: c for p, c in g.items() if p[1] > BREATH_ROW},
            **{(x, y + b): c for (x, y), c in g.items() if y < BREATH_ROW}} if b else dict(g)


def FRAMES():
    poses = POSES()
    fs = [breathe(poses[POSE_STEPS.index(s)], b) for s, b in zip(MOVE, BREATH)]
    assert len(fs) == 24
    for i, g in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in g), ('clipped frame', i)
    assert fs[0] == fs[-1], 'Loop seam must return to the same rest pose'
    assert len({tuple(sorted(g.items())) for g in fs}) > 1
    return fs


def write_sources():
    frames = FRAMES()
    flat_parts.write(str(HERE / '47_moha_moha'), frames, PAL, W, H,
                     dirs='profile', view=('R', 'L'), rows_sheet=True)
    print(f'47 Moha Moha: {len(frames)} frames, {W}x{H}, {FRAME_MS} ms, always facing right')
    return frames


if __name__ == '__main__':
    write_sources()
