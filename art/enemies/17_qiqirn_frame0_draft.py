"""Qiqirn review still, manually placed pixels drawn by the Aseprite MCP plugin.

No game sheets are modified. Numeric spans describe a single composed silhouette;
they are authored pixel placements, not a projected model or resampled image.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'art/direction'))
from mcpc import Pixel

BASE = Path(__file__).with_suffix('')
PAL = dict(K='000000', M='d7a175', S='f0b890', D='8d6b4f', B='633e1b', T='341e10')

# One silhouette, with deliberately staggered feet and a shared shoulder/neck.
SHAPE = {
    3: [(29, 30), (34, 35)],
    4: [(29, 31), (34, 36)],
    5: [(29, 31), (33, 36)],
    6: [(29, 32), (33, 36)],
    7: [(29, 36)],
    8: [(28, 37)],
    9: [(28, 38)],
    10: [(3, 6), (28, 39)],
    11: [(3, 8), (28, 40)],
    12: [(3, 8), (27, 40)],
    13: [(4, 8), (26, 40)],
    14: [(5, 8), (25, 39)],
    15: [(6, 8), (14, 19), (23, 38)],
    16: [(7, 9), (12, 38)],
    17: [(8, 11), (11, 35), (37, 37)],
    18: [(9, 35)],
    19: [(10, 35)],
    20: [(11, 35)],
    21: [(12, 34)],
    22: [(12, 18), (20, 24), (28, 34)],
    23: [(12, 16), (20, 23), (28, 31), (33, 35)],
    24: [(12, 15), (20, 23), (28, 31), (33, 35)],
    25: [(12, 15), (20, 22), (28, 31), (33, 35)],
    26: [(12, 15), (19, 22), (28, 31), (33, 35)],
    27: [(11, 14), (19, 22), (28, 31), (33, 35)],
    28: [(11, 14), (19, 22), (28, 31), (33, 35)],
    29: [(11, 14), (18, 22), (28, 31), (33, 35)],
    30: [(10, 15), (18, 23), (27, 32), (33, 37)],
    31: [(9, 16), (18, 24), (27, 32), (33, 38)],
    32: [(8, 17), (26, 35)],
    33: [(9, 10), (12, 13), (15, 16), (27, 28), (30, 31), (33, 34)],
}


def design():
    occupied = {(x, y) for y, spans in SHAPE.items() for a, b in spans for x in range(a, b + 1)}
    g = {p: ('K' if any((p[0] + dx, p[1] + dy) not in occupied
                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) else 'M')
         for p in occupied}

    def paint(color, rows):
        for y, spans in rows.items():
            for a, b in spans:
                for x in range(a, b + 1):
                    assert (x, y) in g, (x, y)
                    g[x, y] = color

    # Upper-facing cheek/neck and the near haunch; no row-band shading.
    paint('S', {7: [(30, 30)], 8: [(30, 32)], 9: [(29, 33)],
                10: [(29, 33)], 11: [(29, 32)], 12: [(28, 30)],
                13: [(27, 29)], 14: [(26, 28)], 15: [(25, 27)],
                16: [(15, 23), (25, 27)], 17: [(13, 19), (25, 27)],
                18: [(12, 16), (26, 27)], 19: [(13, 14)]})
    paint('D', {18: [(20, 24)], 19: [(18, 25), (32, 34)],
                20: [(16, 25), (31, 34)], 21: [(14, 17), (21, 23), (30, 33)],
                22: [(14, 16), (21, 23), (30, 32)],
                23: [(21, 22), (34, 34)], 24: [(21, 22), (34, 34)],
                25: [(21, 21), (34, 34)], 26: [(20, 21), (34, 34)],
                27: [(20, 21), (34, 34)], 28: [(20, 21), (34, 34)],
                29: [(19, 21), (34, 34)],
                30: [(11, 14), (19, 22), (28, 31), (34, 36)],
                31: [(10, 15), (19, 23), (28, 31), (34, 37)]})

    # Fur is a few broad dark clusters; the jagged edge carries its character.
    paint('B', {11: [(4, 6)], 12: [(4, 7)], 13: [(5, 6)],
                32: [(9, 10), (12, 13), (15, 16), (27, 28), (30, 31), (33, 34)]})
    paint('T', {4: [(30, 30), (35, 35)], 5: [(30, 30), (34, 35)],
                6: [(30, 30), (34, 34)], 7: [(34, 34)],
                12: [(35, 39)], 13: [(34, 39)], 14: [(34, 38)],
                15: [(34, 37)], 16: [(35, 37)],
                32: [(11, 11), (14, 14), (29, 29), (32, 32)]})

    # One eye, one nostril, a shared jaw boundary and sparse joint separators.
    paint('K', {9: [(35, 35)], 11: [(39, 39)], 12: [(32, 34)],
                13: [(32, 32)], 14: [(31, 31)], 15: [(30, 30)],
                19: [(29, 29)], 20: [(29, 29)], 21: [(29, 29)],
                22: [(29, 29)], 23: [(29, 29)]})
    return g


def main():
    from PIL import Image
    g = design()
    original_paths = sorted((ROOT / 'assets/enemies').glob('17_*')) + [ROOT / 'art/enemies/17_views.aseprite', ROOT / 'art/enemies/17_views.png', ROOT / 'art/enemies/17_qiqirn.txt']
    originals = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in original_paths}
    p = Pixel()
    try:
        source = p.call('create_canvas', width=42, height=34, color_mode='rgb')['file_path']
        p.call('set_palette', sprite_path=source, colors=['#' + c for c in PAL.values()])
        pixels = [dict(x=x, y=y, color='#' + PAL[c]) for (x, y), c in sorted(g.items(), key=lambda e: (e[0][1], e[0][0]))]
        result = p.call('draw_pixels', sprite_path=source, layer_name='Layer 1', frame_number=1, pixels=pixels)
        assert result['pixels_drawn'] == len(g), result
        p.call('save_as', sprite_path=source, output_path=BASE.with_suffix('.aseprite').as_posix())
        info = p.call('get_sprite_info', sprite_path=BASE.with_suffix('.aseprite').as_posix())
        p.call('export_sprite', sprite_path=BASE.with_suffix('.aseprite').as_posix(), output_path=BASE.with_suffix('.png').as_posix(), format='png', frame_number=1)
    finally:
        p.p.terminate()
    im = Image.open(BASE.with_suffix('.png')).convert('RGBA')
    expected = {(x, y): tuple(bytes.fromhex(PAL[c])) + (255,) for (x, y), c in g.items()}
    actual = {(x, y): im.getpixel((x, y)) for y in range(34) for x in range(42) if im.getpixel((x, y))[3]}
    assert actual == expected, 'Plugin export differs from authored pixels'
    assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in originals.items())
    report = dict(enemy=17, direction='DR', palette=PAL, info=info, occupied_bounds=im.getchannel('A').getbbox(),
                  plugin_pixels_drawn=len(g), export_mismatches=0, original_sha256=originals)
    BASE.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
