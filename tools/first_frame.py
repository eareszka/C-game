"""A first-frame enemy draft: typed pixel rows -> checks -> the Aseprite pixel plugin -> a review picture.

Shared by art/enemies/NN_name_pose_first.py. A frame is {(x, y): letter}; a palette is {letter: 'rrggbb'},
'K' black. The drawing itself (the rows) stays in each enemy's own script.
"""
from pathlib import Path
import colorsys, json, math, subprocess, sys, tempfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASEPRITE = r'C:\Program Files\Aseprite\Aseprite.exe'
SPRITES = Path('C:/Users/emery/.herdr/worktrees/C-game/sprites')   # the bible and its checker live on this branch
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
rgb = lambda pal: {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, h in pal.items()}


def grid(rows, pal, dx=0, dy=0):
    """rows: {y: [(first column, letters), ...]} or [(y, first column, letters), ...]; '.' is nothing."""
    flat = [(y, x0, t) for y, segs in rows.items() for x0, t in segs] if isinstance(rows, dict) else rows
    g = {}
    for y, x0, text in flat:
        for i, c in enumerate(text):
            if c == '.': continue
            assert c in pal, (y, c)
            assert (x0 + i + dx, y + dy) not in g, f'two segments on ({x0 + i + dx},{y + dy})'
            g[x0 + i + dx, y + dy] = c
    return g


def outline(g, bare=()):
    """Black on every empty pixel beside a colour one; `bare` pixels (a point, a thin tip) get none of their own."""
    out = dict(g)
    for p, c in g.items():
        if c != 'K' and p not in bare:
            for dx, dy in N4: out.setdefault((p[0] + dx, p[1] + dy), 'K')
    return out


def layered(parts, pal, w, h):
    """A frame from typed parts, back to front: [(rows, kind)], kind as tools/flat_parts.py has it ('solid' takes a
    black edge where it is thick enough to hold one, 'raw' is set down as typed). Returns the frame and the colour
    pixels on it that carry no edge: thin parts, tips, raw parts."""
    import flat_parts
    built = [(grid(rows, pal), kind, None) for rows, kind in parts]
    g = flat_parts.draw(built, w, h, {})
    inner = lambda px, q: q in px and all((q[0] + dx, q[1] + dy) in px for dx, dy in N4)
    thin = set()
    for px, kind, _ in built:
        thin |= {p for p in px if kind == 'raw' or not any(inner(px, (p[0] + dx, p[1] + dy)) for dx, dy in N4)}
    return g, thin


def path(points):
    """A smooth line through (x, y, thickness) points, as samples about a pixel apart: [x, y, r, along]."""
    p = [points[0]] + list(points) + [points[-1]]
    fine = []
    for i in range(1, len(p) - 2):
        for k in range(24):
            t = k / 24
            fine.append(tuple(0.5 * (2 * p[i][c] + (p[i + 1][c] - p[i - 1][c]) * t
                                     + (2 * p[i - 1][c] - 5 * p[i][c] + 4 * p[i + 1][c] - p[i + 2][c]) * t * t
                                     + (3 * p[i][c] - p[i - 1][c] - 3 * p[i + 1][c] + p[i + 2][c]) * t ** 3) for c in range(3)))
    fine.append(tuple(points[-1]))
    out, along, last = [], 0.0, None
    for x, y, r in fine:
        if last: along += math.hypot(x - last[0], y - last[1])
        if not out or along - out[-1][3] >= 1 or (x, y, r) == fine[-1]: out.append([x, y, r, along])
        last = (x, y)
    return out


def pieces(px):
    """How many separate pieces a set of pixels is in, diagonals joined."""
    todo, n = set(px), 0
    while todo:
        n += 1; stack = [todo.pop()]
        while stack:
            x, y = stack.pop()
            for q in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if q in todo: todo.remove(q); stack.append(q)
    return n


def game_palette():
    out = set()
    for line in open(ROOT / 'art/direction/game_palette.gpl'):
        s = line.split()
        if len(s) >= 3 and s[0].isdigit(): out.add(tuple(map(int, s[:3])))
    return out


def checks(g, pal, w, h, open_ok=lambda p, c: False, old=None, cap=44, max_colours=8, right_open=False):
    """Asserts what must hold of a frame and returns the numbers to show with it.
    open_ok(p, c): a colour pixel allowed to meet empty space (a plume, a claw, a point).
    right_open: the drawing runs on out of the frame's right edge (cut there, open, no line)."""
    out, RGB = [], rgb(pal)
    assert all(1 <= x < w - (0 if right_open else 1) and 1 <= y < h for x, y in g), 'a part touches the canvas side or the top row'
    used = set(g.values())
    assert all(RGB[c] in game_palette() for c in used), 'off-palette colour'
    assert len(used - {'K'}) <= max_colours
    out.append(f'palette: 0 off-palette pixels; {len(used - {"K"})} colours plus black')
    for c in sorted(used - {'K'}, key=lambda c: colorsys.rgb_to_hsv(*(v / 255 for v in RGB[c]))[2]):
        hh, ss, vv = colorsys.rgb_to_hsv(*(v / 255 for v in RGB[c]))
        out.append(f'  {pal[c]} hue {round(hh * 360)} sat {round(ss * 100)} value {round(vv * 100)}')
    xs, ys = [x for x, y in g], [y for x, y in g]
    out.append(f'drawn box: {max(xs) - min(xs) + 1} wide x {max(ys) - min(ys) + 1} tall (columns {min(xs)}-{max(xs)}, rows {min(ys)}-{max(ys)})'
               + (f'; old {old}' if old else ''))
    assert max(ys) - min(ys) + 1 <= cap, 'taller than its tier'
    open_px = sorted(p for p, c in g.items() if c != 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4))
    stray = [p for p in open_px if not open_ok(p, g[p]) and not (right_open and p[0] == w - 1)]
    assert not stray, f'outline open at {stray}'
    out.append(f'outline: closed ({len(open_px)} colour px on the edge, all on parts drawn without one)')
    edge = {p for p in g if any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4)}
    inner_k = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    out.append(f'interior black: {100 * inner_k / len(g):.1f}% of {len(g)} px (reference 9-14%)')
    return out


def image(g, pal, w, h, bg=(0, 0, 0, 0)):
    RGB, im = rgb(pal), Image.new('RGBA', (w, h), bg)
    for (x, y), c in g.items(): im.putpixel((x, y), RGB[c] + (255,))
    return im


def draw_plugin(g, pal, w, h, base):
    """Draw the frame through the pixel plugin into base.aseprite (+ .png, .json); read it back and compare."""
    sys.path.insert(0, str(ROOT / 'art/direction'))
    from mcpc import Pixel
    base, RGB = Path(base), rgb(pal)
    if plugin_missing():
        aseprite_frames([g], pal, w, h, base.with_suffix('.aseprite'))
        image(g, pal, w, h).save(base.with_suffix('.png'))
        rows = [''.join(g.get((x, y), '.') for x in range(w)) for y in range(h)]
        base.with_suffix('.json').write_text(json.dumps({'pal': pal, 'width': w, 'height': h, 'frame0': rows}, indent=2) + '\n')
        print(f'{base.name}: {len(g)} pixels, through the Aseprite command line, read back the same', flush=True)
        return saved(base.with_suffix('.aseprite'))
    px = Pixel()
    try:
        source = px.call('create_canvas', width=w, height=h, color_mode='rgb')['file_path']
        px.call('set_palette', sprite_path=source, colors=['#' + v for v in pal.values()])
        pixels = [{'x': x, 'y': y, 'color': '#' + pal[c]} for (x, y), c in sorted(g.items())]
        for at in range(0, len(pixels), 800):
            px.call('draw_pixels', sprite_path=source, layer_name='Layer 1', frame_number=1, pixels=pixels[at:at + 800])
        ase, png = base.with_suffix('.aseprite').as_posix(), base.with_suffix('.png').as_posix()
        px.call('save_as', sprite_path=source, output_path=ase)
        px.call('export_sprite', sprite_path=ase, output_path=png, format='png', frame_number=1)
    finally:
        px.p.terminate()
    im = Image.open(png).convert('RGBA')
    assert im.size == (w, h)
    inv = {v: k for k, v in RGB.items()}
    actual = {(x, y): inv[im.getpixel((x, y))[:3]] for y in range(h) for x in range(w) if im.getpixel((x, y))[3]}
    assert actual == g, 'the plugin export differs from the design'
    rows = [''.join(g.get((x, y), '.') for x in range(w)) for y in range(h)]
    base.with_suffix('.json').write_text(json.dumps({'pal': pal, 'width': w, 'height': h, 'frame0': rows}, indent=2) + '\n')
    print(f'{base.name}: {len(g)} pixels, 0 export mismatches', flush=True)
    return im


def saved(ase):
    """A one-frame .aseprite as it was last saved."""
    with tempfile.TemporaryDirectory() as d:
        png = Path(d) / 'a.png'
        subprocess.run([ASEPRITE, '-b', str(ase), '--save-as', str(png)], check=True)
        im = Image.open(png).convert('RGBA'); im.load()
    return im


def read(ase, pal):
    """A saved frame as {(x, y): letter}: the drawing later frames are made from, the user's edits included."""
    im, inv, g = saved(ase), {v: k for k, v in rgb(pal).items()}, {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3]:
                assert p[:3] in inv, f'{Path(ase).name}: colour {p[:3]} at ({x},{y}) is not one of the sprite\'s'
                g[x, y] = inv[p[:3]]
    return g


def draft(g, pal, w, h, base):
    """draw_plugin, unless base.aseprite is already there: then it must still be this drawing. A draft that
    differs was edited (it is the user's) or the design moved on: read it back, or delete it to redraw."""
    ase = Path(base).with_suffix('.aseprite')
    if not ase.exists(): return draw_plugin(g, pal, w, h, base)
    im = saved(ase)
    assert im.tobytes() == image(g, pal, w, h).tobytes(), f'{ase.name} is not this drawing: not drawn over'
    print(f'{ase.stem}: already drawn, unchanged', flush=True)
    return im


def draw_frames(frames, pal, w, h, base, ms, tags):
    """An animation through the pixel plugin: base.aseprite, `ms` a frame, tags {name: (first, last)} counted
    from 1. Every frame is read back and compared."""
    sys.path.insert(0, str(ROOT / 'art/direction'))
    from mcpc import Pixel
    ase, inv = Path(base).with_suffix('.aseprite').as_posix(), {v: k for k, v in rgb(pal).items()}
    if plugin_missing():
        aseprite_frames(frames, pal, w, h, ase, ms, tags)
        print(f'{Path(base).name}.aseprite: {len(frames)} frames, {ms} ms each, tags {" ".join(tags)}, through the Aseprite command line, read back the same', flush=True)
        return
    px = Pixel()
    try:
        src = px.call('create_canvas', width=w, height=h, color_mode='rgb')['file_path']
        px.call('set_palette', sprite_path=src, colors=['#' + v for v in pal.values()])
        px.call('set_frame_duration', sprite_path=src, frame_number=1, duration_ms=ms)
        for _ in frames[1:]: px.call('add_frame', sprite_path=src, duration_ms=ms)
        for i, g in enumerate(frames, 1):
            pixels = [{'x': x, 'y': y, 'color': '#' + pal[c]} for (x, y), c in sorted(g.items())]
            for at in range(0, len(pixels), 800):
                px.call('draw_pixels', sprite_path=src, layer_name='Layer 1', frame_number=i, pixels=pixels[at:at + 800])
        for name, (a, b) in tags.items():
            px.call('create_tag', sprite_path=src, tag_name=name, from_frame=a, to_frame=b, direction='forward')
        px.call('save_as', sprite_path=src, output_path=ase)
        with tempfile.TemporaryDirectory() as d:
            for i, g in enumerate(frames, 1):
                png = (Path(d) / f'{i}.png').as_posix()
                px.call('export_sprite', sprite_path=ase, output_path=png, format='png', frame_number=i)
                im = Image.open(png).convert('RGBA')
                got = {(x, y): inv[im.getpixel((x, y))[:3]] for y in range(h) for x in range(w) if im.getpixel((x, y))[3]}
                assert got == g, f'frame {i}: the plugin export differs from the design'
    finally:
        px.p.terminate()
    print(f'{Path(base).name}.aseprite: {len(frames)} frames, {ms} ms each, tags {" ".join(tags)}, 0 export mismatches', flush=True)


def same_as_draft(ase, images):
    """Is a drawn animation draft still these frames? (An edited draft is the user's: read it back, do not install the design.)"""
    with tempfile.TemporaryDirectory() as d:
        png = Path(d) / 's.png'
        subprocess.run([ASEPRITE, '-b', str(ase), '--sheet', str(png), '--sheet-type', 'horizontal'], check=True, stdout=subprocess.DEVNULL)
        strip = Image.open(png).convert('RGBA'); strip.load()
    w, h = images[0].size
    return strip.size == (w * len(images), h) and all(strip.crop((i * w, 0, (i + 1) * w, h)).tobytes() == im.tobytes() for i, im in enumerate(images))


def gif(images, path, ms, pal, scale=6):
    """A looping GIF on black from RGBA pictures; ms one number or one a frame. Checked to hold only the sprite's colours."""
    RGB = rgb(pal)
    swatch = Image.new('P', (1, 1)); swatch.putpalette(sum((list(v) for v in RGB.values()), []) + [0] * (768 - 3 * len(RGB)))
    out = []
    for im in images:
        flat = Image.new('RGB', im.size, (0, 0, 0)); flat.paste(im, (0, 0), im)
        out.append(flat.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST).quantize(palette=swatch, dither=Image.Dither.NONE))
    out[0].save(path, save_all=True, append_images=out[1:], duration=ms, loop=0, disposal=1, optimize=False)
    back, seen = Image.open(path), set()
    for i in range(back.n_frames):
        back.seek(i); seen |= {c for n, c in back.convert('RGB').getcolors(1 << 20)}
    assert seen <= set(RGB.values()), f'{Path(path).name} holds colours the sprite does not: {seen - set(RGB.values())}'
    runs = 1 + sum(a.tobytes() != b.tobytes() for a, b in zip(out, out[1:]))     # PIL holds a repeated frame as one, for longer
    assert back.n_frames == runs, (back.n_frames, runs)


def style_check(im, scratch, name, tier='medium'):
    """The bible's checker reads an 8-direction sheet: the one frame, eight times."""
    w, h = im.size
    strip = Image.new('RGBA', (w * 8, h), (0, 0, 0, 0))
    for d in range(8): strip.alpha_composite(im, (d * w, 0))
    p = Path(scratch) / (name + '_strip.png')
    strip.save(p)
    r = subprocess.run([sys.executable, str(SPRITES / 'tools/style_check.py'), '--png', str(p), '--frames', '1',
                        '--class', 'down', '--tier', tier], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip(), flush=True)
    return r.returncode == 0


def silhouette(im):
    s = Image.new('RGBA', im.size, (252, 252, 252, 0)); s.putalpha(im.getchannel('A'))
    return s


def player():
    return Image.open(ROOT / 'assets/player_small.png').convert('RGBA').crop((0, 0, 14, 20))


def review(panels, out, scale=6):
    """[(label, image)] side by side on black at one scale, feet on one line."""
    hh = max(im.height for _, im in panels)
    xs, x = [], 6
    for _, im in panels: xs.append(x); x += max(im.width, 46) + 6
    panel = Image.new('RGBA', (x, hh + 16), (0, 0, 0, 255))
    labels = ImageDraw.Draw(panel)
    for (label, im), px in zip(panels, xs):
        labels.text((px, 1), label, fill=(252, 252, 252, 255))
        panel.alpha_composite(im, (px, 13 + hh - im.height))
    panel.resize((panel.width * scale, panel.height * scale), Image.Resampling.NEAREST).save(out)


def plugin_missing():
    sys.path.insert(0, str(ROOT / 'art/direction'))
    import mcpc, os
    return not os.path.exists(mcpc.EXE)


LUA = """local p = app.params
local w, h, n, ms = tonumber(p.w), tonumber(p.h), tonumber(p.n), tonumber(p.ms)
local spr = Sprite(w, h, ColorMode.RGB)
local pal = Palette(0)
for hex in string.gmatch(p.pal, "%x+") do
  pal:resize(#pal + 1)
  pal:setColor(#pal - 1, Color{ r = tonumber(hex:sub(1, 2), 16), g = tonumber(hex:sub(3, 4), 16), b = tonumber(hex:sub(5, 6), 16) })
end
spr:setPalette(pal)
for i = 1, n do
  if i > 1 then spr:newEmptyFrame() end
  spr:newCel(spr.layers[1], spr.frames[i], Image{ fromFile = p.dir .. "/" .. i .. ".png" }, Point(0, 0))
  spr.frames[i].duration = ms / 1000
end
for tag in string.gmatch(p.tags, "[^;]+") do
  local name, a, b = tag:match("([^,]+),(%d+),(%d+)")
  spr:newTag(tonumber(a), tonumber(b)).name = name
end
spr:saveAs(p.out)
"""


def aseprite_frames(frames, pal, w, h, ase, ms=100, tags=None):
    """The pixel plugin's job done by Aseprite's own command line (the plugin is not installed): the frames as PNGs,
    put into one sprite by a script, with the palette, the frame time and the tags; read back and compared."""
    with tempfile.TemporaryDirectory() as d:
        for i, g in enumerate(frames, 1):
            image(g, pal, w, h).save(Path(d) / f'{i}.png')
        lua = Path(d) / 'make.lua'; lua.write_text(LUA)
        tag = ';'.join(f'{k},{a},{b}' for k, (a, b) in (tags or {}).items())
        cmd = [ASEPRITE, '-b']
        for k, v in {'w': w, 'h': h, 'n': len(frames), 'ms': ms, 'pal': ' '.join(pal.values()), 'dir': Path(d).as_posix(),
                     'tags': tag, 'out': Path(ase).as_posix()}.items():
            cmd += ['--script-param', f'{k}={v}']
        subprocess.run(cmd + ['--script', str(lua)], check=True, stdout=subprocess.DEVNULL)
    assert same_as_draft(ase, [image(g, pal, w, h) for g in frames]), f'{Path(ase).name}: Aseprite\'s save differs from the design'
