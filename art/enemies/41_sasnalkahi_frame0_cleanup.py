"""Flatten PixelLab's fur speckles into deliberate form shading via pixel MCP.

The paid source is immutable; its silhouette, pose, eyes and claws are retained.
All painting and saving is performed by the Aseprite pixel plugin.
"""
from pathlib import Path
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'art/direction'))
from mcpc import Pixel

SOURCE = ROOT / 'pixellab-out/2026-10-17T0224-41-sasnalkahi-original-frame0-redraw-only-image/41-sasnalkahi-frame0-draft-00.png'
OUT = ROOT / 'art/enemies/41_sasnalkahi_frame0_draft.aseprite'
PALETTE = {'K': '#000000', 'D': '#3c2412', 'M': '#633e1b',
           'L': '#b2966a', 'E': '#b70000', 'W': '#e8e0c0'}


def inside(x, y, points):
    hit = False
    j = len(points) - 1
    for i, (a, b) in enumerate(points):
        c, d = points[j]
        if (b > y) != (d > y) and x < (c-a)*(y-b)/(d-b)+a:
            hit = not hit
        j = i
    return hit


# These shapes describe visible surfaces, not horizontal shading bands.
SHADOWS = [
    [(56,16),(61,22),(65,30),(65,56),(61,58),(60,45),(61,33),(57,25)],
    [(34,27),(38,30),(38,41),(40,45),(38,51),(34,48)],
    [(41,43),(46,46),(46,57),(42,57),(43,50)],
    [(54,42),(57,44),(57,57),(54,57)],
    [(55,28),(59,29),(58,41),(54,46),(50,47),(52,43),(55,38)],
    [(45,44),(53,44),(54,49),(49,51),(45,48)],
    [(34,58),(45,58),(46,64),(34,64)],
    [(54,58),(65,58),(65,64),(53,64)],
]
LIGHTS = [
    [(40,18),(44,15),(50,15),(53,17),(48,18),(44,21),(41,24),(39,25)],
    [(46,24),(52,24),(55,27),(55,29),(51,28),(48,27),(45,29),(43,30),(43,27)],
    [(46,37),(52,37),(55,39),(53,41),(48,41),(46,43),(44,41),(44,39)],
    [(36,41),(39,41),(41,45),(40,50),(37,53),(36,50)],
    [(57,43),(60,42),(62,46),(61,50),(58,53),(57,50)],
]


def main():
    if OUT.exists():
        raise RuntimeError(f'Refusing to overwrite {OUT}')
    im = Image.open(SOURCE).convert('RGBA')
    assert im.size == (98, 65)
    pixels = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if not a:
                continue
            if max(r, g, b) < 16:
                tone = 'K'
            elif r > 220 and g > 150:
                tone = 'W'
            elif r > 180 and g < 100:
                tone = 'E'
            else:
                tone = 'M'
                if any(inside(x+.5, y+.5, poly) for poly in SHADOWS):
                    tone = 'D'
                if any(inside(x+.5, y+.5, poly) for poly in LIGHTS):
                    tone = 'L'
            pixels.append(dict(x=x, y=y, color=PALETTE[tone]))
    p = Pixel()
    canvas = p.call('create_canvas', width=98, height=65, color_mode='rgb')['file_path']
    p.call('save_as', sprite_path=canvas.replace('\\', '/'), output_path=OUT.as_posix())
    info = p.call('get_sprite_info', sprite_path=OUT.as_posix())
    p.call('draw_pixels', sprite_path=OUT.as_posix(), layer_name=info['layers'][0],
           frame_number=1, pixels=pixels)
    p.call('set_palette', sprite_path=OUT.as_posix(), colors=list(PALETTE.values()))
    p.call('export_sprite', sprite_path=OUT.as_posix(), output_path=OUT.with_suffix('.png').as_posix(),
           format='png', frame_number=1)
    print(json.dumps(p.call('get_sprite_info', sprite_path=OUT.as_posix())))
    p.p.terminate()


if __name__ == '__main__':
    main()
