"""Draw an enemy's hand-designed views into an .aseprite through the pixel plugin.

    python tools/draw_views.py design.json art/enemies/NN_views

design.json: {"pal": {letter: "rrggbb"}, "view_w": W, "views": {"D": [rows], ...},
              "order": ["D", "DR", "R", "UR", "U"], "extras": [[x, y, [rows]], ...]}

The views go side by side on row 0 (view_w apart); extras (open mouths and the
like) at their own x, y. Drawing goes through the plugin's draw_pixels (pixel-mcp
via art/direction/mcpc.py), then save_as + export_sprite; the exported PNG is
checked pixel by pixel against the design."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'direction'))
from mcpc import Pixel
from PIL import Image

def main(design, out_base):
    d = json.load(open(design))
    pal, vw, order = d['pal'], d['view_w'], d['order']
    pieces = [(i * vw, 0, d['views'][k]) for i, k in enumerate(order)] + [tuple(e) for e in d.get('extras', [])]
    w = max(x + len(rows[0]) for x, y, rows in pieces)
    h = max(y + len(rows) for x, y, rows in pieces)
    px = Pixel()
    path = px.call('create_canvas', width=w, height=h, color_mode='rgb')['file_path']
    n = 0
    for ox, oy, rows in pieces:
        pix = [{'x': ox + x, 'y': oy + y, 'color': '#' + pal[c]} for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.']
        for i in range(0, len(pix), 800):
            px.call('draw_pixels', sprite_path=path, layer_name='Layer 1', frame_number=1, pixels=pix[i:i + 800])
        n += len(pix)
    ase, png = out_base + '.aseprite', out_base + '.png'
    px.call('save_as', sprite_path=path, output_path=ase.replace('\\', '/'))
    px.call('export_sprite', sprite_path=ase.replace('\\', '/'), output_path=png.replace('\\', '/'), format='png', frame_number=0)
    # the plugin has dropped pixels before (a paste lost a row): check the export against the design
    im = Image.open(png).convert('RGBA')
    letter = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in pal.items()}
    bad = sum(1 for ox, oy, rows in pieces for y, r in enumerate(rows) for x, c in enumerate(r)
              if ('.' if im.getpixel((ox + x, oy + y))[3] == 0 else letter.get(im.getpixel((ox + x, oy + y))[:3], '?')) != c)
    print(f'{ase}: {n} pixels drawn, {bad} mismatches')
    assert bad == 0

if __name__ == '__main__':
    main(*sys.argv[1:3])
