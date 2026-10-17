"""Palette and one-pixel silhouette cleanup of the immutable PixelLab result.

Pixel data is read locally; all final painting/saving goes through pixel MCP.
"""
from pathlib import Path
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'art/direction'))
from mcpc import Pixel
from fcremap import lab_dist

SOURCE = ROOT / 'pixellab-out/2026-10-17T0232-49-physeter-original-frame0-redraw-physeter-s-fi/49-physeter-frame0-draft.png'
OUT = ROOT / 'art/enemies/49_physeter_frame0_draft.aseprite'
PALETTE = ['000000', '34343e', '595965', '848694', '421618', '792727',
           'e8e0c0', 'b2966a', 'd89830', '84a7e9', 'dcf0ff']


def main():
    if OUT.exists():
        raise RuntimeError(f'Refusing to overwrite {OUT}')
    im = Image.open(SOURCE).convert('RGBA')
    assert im.size == (302, 166)
    palette = [tuple(bytes.fromhex(c)) for c in PALETTE]
    source_colors = {c[:3] for c in im.getdata() if c[3]}
    mapping = {}
    for c in source_colors:
        if max(c) < 20:
            dest = palette[0]
        elif c[0] > 1.8*c[1] and c[0] > 1.5*c[2]:
            dest = min(palette[4:6], key=lambda d: lab_dist(c, d))
        else:
            dest = min(palette, key=lambda d: lab_dist(c, d))
        mapping[c] = '#%02x%02x%02x' % dest
    pixels = []
    edge_count = 0
    for y in range(im.height):
        for x in range(im.width):
            c = im.getpixel((x, y))
            if not c[3]:
                continue
            boundary = any(not (0 <= x+dx < im.width and 0 <= y+dy < im.height)
                           or not im.getpixel((x+dx, y+dy))[3]
                           for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)))
            color = '#000000' if boundary else mapping[c[:3]]
            edge_count += boundary
            pixels.append(dict(x=x, y=y, color=color))
    p = Pixel()
    canvas = p.call('create_canvas', width=302, height=166, color_mode='rgb')['file_path']
    p.call('save_as', sprite_path=canvas.replace('\\', '/'), output_path=OUT.as_posix())
    info = p.call('get_sprite_info', sprite_path=OUT.as_posix())
    for i in range(0, len(pixels), 1500):
        p.call('draw_pixels', sprite_path=OUT.as_posix(), layer_name=info['layers'][0],
               frame_number=1, pixels=pixels[i:i+1500])
    p.call('set_palette', sprite_path=OUT.as_posix(), colors=['#'+c for c in PALETTE])
    p.call('export_sprite', sprite_path=OUT.as_posix(), output_path=OUT.with_suffix('.png').as_posix(),
           format='png', frame_number=1)
    print(json.dumps(p.call('get_sprite_info', sprite_path=OUT.as_posix())))
    p.p.terminate()
    record = {'method': 'Pixel plugin draw_pixels; native geometry and alpha preserved',
              'source': SOURCE.as_posix(), 'output': OUT.as_posix(),
              'black_silhouette_boundary_pixels': edge_count,
              'palette_mapping': {'#%02x%02x%02x' % c:d for c,d in mapping.items()}}
    (ROOT/'build_tmp/physeter_pixellab/palette_cleanup.json').write_text(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
