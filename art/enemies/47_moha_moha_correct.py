"""Correct Moha Moha through the Aseprite pixel plugin; preserve original keys.

python art/enemies/47_moha_moha_correct.py
"""
import importlib.util
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'art/enemies'
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(ROOT / 'tools'))
from mcpc import Pixel
# Reuse the palette/timing constants; pose authoring does not depend on backups.
spec = importlib.util.spec_from_file_location('moha_design', HERE / '47_moha_moha_design.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)
import flat_parts
from types import SimpleNamespace


def read_user_frame(name='47_moha_moha_user_frame.png'):
    from PIL import Image
    im = Image.open(HERE / name).convert('RGBA')
    assert im.size == (design.W, design.H)
    g = {}
    for y in range(design.H):
        for x in range(design.W):
            p = im.getpixel((x, y))
            if not p[3]:
                continue
            rgb = p[:3]
            if rgb in design.LETTER:
                c = design.LETTER[rgb]
            elif rgb == (255, 255, 255):
                c = 'W'
            else:
                assert max(rgb) < 0x20, rgb
                c = 'K'
            g[x, y] = c
    return g


def close(out, moved):
    """Where moved colour now meets nothing, the outline comes out with it."""
    for p in moved:
        if out.get(p, 'K') not in 'KW':
            for q in (flat_parts.add(p, d) for d in flat_parts.N4):
                if q not in out: out[q] = 'K'
    return out

def turn(g, mine, pivot, deg):
    """The pixels `mine` picks turned deg degrees about pivot (positive: clockwise as seen, which swings a tail
    pointing left up). Each pixel of the turned part is the part's pixel that lands there (nearest, so nothing is
    blended or redrawn); returns (the turned part, the rest)."""
    import math
    part = {p: c for p, c in g.items() if mine(p)}
    rest = {p: c for p, c in g.items() if p not in part}
    if not deg: return part, rest
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    px, py = pivot
    ends = [(px + (x - px) * ca - (y - py) * sa, py + (x - px) * sa + (y - py) * ca) for x, y in part]
    out = {}
    for y in range(int(min(e[1] for e in ends)) - 1, int(max(e[1] for e in ends)) + 2):
        for x in range(int(min(e[0] for e in ends)) - 1, int(max(e[0] for e in ends)) + 2):
            dx, dy = x - px, y - py                       # where this pixel comes from: turned back
            q = (round(px + dx * ca + dy * sa), round(py - dx * sa + dy * ca))
            if q in part: out[(x, y)] = part[q]
    return out, rest

# These are the existing approved head transform and jaw-selection coordinates.
original = SimpleNamespace(W=design.W, H=design.H, PAL=design.PAL, UP=design.UP,
                           user_frame=read_user_frame, close=close, turn=turn,
                           HEAD_X=55, HEAD_ROWS=22, JAW_X=83, JAW_BOTTOM=25,
                           HEAD_PIVOT=(79, 23), HEAD_SWING=70, image=design.image)

# Literal pixel drawings: the same fluke lobes and material sides throughout.
TAIL_DRAWINGS = {
1: (32, '''
KK
KTKK
.KTTKK
.KTTTK
..KTTTK
..KTTTTK
...KTTTTK
...KKTTTTK
....KKTTKKKKKK
.....KTTKgggggKKK
....KKTTTKGGGggggKKK
....KTTTTKKBGGGGGggggKK
...KTTTTK..KBGGGGGGGgggK
...KTTTK....KBBGGGGGGGGK
..KTTTK......KKBBBGGGGGG
..KTTK.........KKBBBBGGGG
.KTKK............KKBBBBG
.KK................KKBBs
.....................KBB
.....................KKK
'''),
2: (28, '''
KK
KTKK
.KTTKK
..KTTTK
..KTTTTK
...KTTTTK
....KTTTTK
.....KTTTTK
......KTTTKggK
.......KTTKGGggKK
.......KTTKBGGGggK
......KTTK.KBGGGGggK
......KTTK..KBGGGGGgKK
......KK.....KBBGGGGggK
..............KBBGGGGggK
...............KBBGGGGgK
................KKBBGGgK
..................KBGGGK
...................KBGGK
....................KBGG
.....................KBG
......................KB
.....................KBs
.....................KKK
'''),
3: (23, '''
.KK
.KTKK
..KTTKK
...KTTTK
....KTTTTK
.....KTTTTK
......KTTTTK.......KK
.......KTTTTK...KKTTK
........KTTTTKKKTTTK
.........KTTTTKTTTK
..........KTTTTTK
...........KTTTK
............KKgKK
............KGGgK
............KGGgK
............KBGgKK
.............KBGGgK
.............KBGGggK
..............KBGGGgK
..............KKBGGggK
...............KBGGGggKK
...............KKBGGGggg
................KBGGGggK
.................KBBGGGK
..................KBBGGG
...................KBBGG
....................KBBG
.....................KBs
.....................KKK
'''),
4: (19, '''
...KK
...KTKK
....KTTKK............KK
.....KTTTK.........KKTK
......KTTTKK.....KKTTTK
.......KTTTTKKKKKTTTTK
........KTTTTKKTTTTTK
.........KTTTTTTTTTK
..........KTTTTTTTK
...........KTTKKTK
............KKgKK
'''),
5: (17, '''
.....KK
.....KTKK
......KTTKK..........KK
......KTTTTK.......KKTK
.......KTTTTKK..KKKTTK
........KTTTTKKKTTTTTK
.........KTTTTKTTTTTK
..........KTTTTTTTTK
...........KTTTTTTK
............KTTTKK
............KKgKK
'''),
}


def in_tail(p):
    # The raised fluke crosses the old x=23 mask. Move its entire tip.
    x, y = p
    return (x <= 23 and y <= 51) or (x < 40 and y < 31)


def tail_drawing(keys, index):
    if index in (0, 6):
        return {p: c for p, c in keys['A' if index == 0 else 'B'].items() if in_tail(p)}
    y0, text = TAIL_DRAWINGS[index]
    rows = text.split()
    g = {(x, y): c for y, row in enumerate(rows, y0) for x, c in enumerate(row) if c != '.'}
    if index in (4, 5):
        g.update({p: c for p, c in keys['B'].items() if in_tail(p) and p[1] >= y0 + len(rows)})
    return g


def lower_jaw(p, key):
    x, y = p
    if key == 'A':
        return (x >= 84 and 16 <= y <= 22) or (x >= 86 and 23 <= y <= 24)
    return x >= 68 and y <= 10


def jaw_source(src, key, opening):
    if opening == 1:
        return dict(src)
    if key == 'A' and opening < 0.1:
        # Hand-drawn meshed muzzle. Keep the upper snout and eye unchanged;
        # one dark mouth line, a green underside, and no transparent jaw gap.
        rows = '''
GGGGGGGKgK
GGGGGGKgK
GGGGGKgK
GGGGKgK
GGGKgK
GGKgK
GKgK
KgK
gK
gK
K
K
K
K
K
.
.
.
.
'''.split()
        rest = {p: c for p, c in src.items() if not (p[0] >= 84 and 7 <= p[1] <= 25)}
        for y, row in enumerate(rows, 7):
            for x, c in enumerate(row, 84):
                if c != '.':
                    rest[x, y] = c
        return rest
    pivot = (82, 16) if key == 'A' else (67, 11)
    jaw, rest = original.turn(src, lambda p: lower_jaw(p, key), pivot, -70 * (1 - opening))
    if opening == 0:
        # Teeth disappear inside the meshed jaws; the eye is outside this mask.
        rest = {p: ('K' if c == 'W' and p[0] >= 84 and p[1] <= 17 else c) for p, c in rest.items()}
        jaw = {p: ('g' if c == 'W' else c) for p, c in jaw.items()}
    return original.close({**jaw, **rest}, set(jaw))


def head_with_original_motion(g, src, deg):
    mine = lambda p: p[0] >= original.HEAD_X and (p[1] <= original.HEAD_ROWS or (p[0] > original.JAW_X and p[1] <= original.JAW_BOTTOM))
    old_head, _ = original.turn(src, mine, original.HEAD_PIVOT, deg)
    part, rest = original.turn(g, mine, original.HEAD_PIVOT, deg)
    if deg:
        # Preserve the original vertical correction independent of jaw edits.
        drop = max(0, 1 - min(y for x, y in old_head))
        part = {(x, y + drop): c for (x, y), c in part.items()}
    return original.close({**rest, **part}, set(part) | set(rest)) if deg else g


def make_poses():
    keys = {'A': original.user_frame(), 'B': original.user_frame('47_moha_moha_user_key.png')}
    poses = []
    for index, s in enumerate([0, *original.UP]):
        key = 'A' if s < 0.5 else 'B'
        src = keys[key]
        g = jaw_source(src, key, s)
        body = {p: c for p, c in g.items() if not in_tail(p)}
        tail = tail_drawing(keys, index)
        g = original.close({**tail, **body}, set(tail) | set(body)) if 0 < s < 1 else {**tail, **body}
        deg = -original.HEAD_SWING * s if s < 0.5 else original.HEAD_SWING * (1 - s)
        g = head_with_original_motion(g, src, deg)
        assert all(0 <= x < original.W and 1 <= y < original.H for x, y in g), (index, sorted(p for p in g if not (0 <= p[0] < original.W and 1 <= p[1] < original.H)))
        poses.append(g)
    assert poses[-1] == keys['B'], 'Backward open key must remain unchanged'
    return poses


def plugin_draw(frames, out_base, tag):
    """Paint via the plugin; verify every exported pixel, including transparency."""
    from PIL import Image
    px = Pixel()
    try:
        path = px.call('create_canvas', width=original.W, height=original.H, color_mode='rgb')['file_path']
        px.call('set_palette', sprite_path=path, colors=['#' + c for c in original.PAL.values()])
        seen = {}
        for i, g in enumerate(frames, 1):
            if i > 1:
                px.call('add_frame', sprite_path=path, duration_ms=100)
            else:
                px.call('set_frame_duration', sprite_path=path, frame_number=1, duration_ms=100)
            signature = tuple(sorted(g.items()))
            if signature in seen:
                px.call('link_cel', sprite_path=path, layer_name='Layer 1', source_frame=seen[signature], target_frame=i)
            else:
                if i > 1:
                    clear = [{'x': x, 'y': y, 'color': '#00000000'} for y in range(original.H) for x in range(original.W)]
                    for start in range(0, len(clear), 800):
                        px.call('draw_pixels', sprite_path=path, layer_name='Layer 1', frame_number=i, pixels=clear[start:start+800])
                pix = [{'x': x, 'y': y, 'color': '#' + original.PAL[c]} for (x, y), c in g.items()]
                for start in range(0, len(pix), 800):
                    px.call('draw_pixels', sprite_path=path, layer_name='Layer 1', frame_number=i, pixels=pix[start:start+800])
                seen[signature] = i
            print(f'{tag} frame {i}/{len(frames)}', flush=True)
        px.call('create_tag', sprite_path=path, tag_name=tag, from_frame=1, to_frame=len(frames), direction='forward')
        ase = str(out_base.with_suffix('.aseprite')).replace('\\', '/')
        png = str(out_base.with_suffix('.png')).replace('\\', '/')
        px.call('save_as', sprite_path=path, output_path=ase)
        px.call('export_spritesheet', sprite_path=ase, output_path=png, layout='horizontal', padding=0, include_json=False)
        im = Image.open(png).convert('RGBA')
        assert im.size == (len(frames) * original.W, original.H), im.size
        for i, g in enumerate(frames):
            actual = im.crop((i*original.W, 0, (i+1)*original.W, original.H))
            assert actual.tobytes() == original.image(g).tobytes(), f'Plugin mismatch in frame {i}'
        print(f'{out_base.name}: 0 pixel mismatches', flush=True)
    finally:
        px.p.terminate()


def export_review(frames, design):
    from PIL import Image, ImageDraw
    # Read the plugin's verified pixels, not a separately painted animation.
    strip = Image.open(HERE / '47_moha_moha_corrected.png').convert('RGBA')
    colours = list(design.RGB.values())
    colour_index = {rgb: i for i, rgb in enumerate(colours)}
    palette = [channel for rgb in colours for channel in rgb] + [0] * (768 - len(colours) * 3)
    gif_frames = []
    board = Image.new('RGB', (6 * design.W, 4 * (design.H + 10)), (0, 0, 0))
    draw = ImageDraw.Draw(board)
    for i in range(len(frames)):
        cell = strip.crop((i * design.W, 0, (i + 1) * design.W, design.H))
        indexed = Image.new('P', cell.size)
        indexed.putpalette(palette)
        indexed.putdata([colour_index[p[:3]] if p[3] else 0 for p in cell.getdata()])
        gif_frames.append(indexed.resize((design.W * 5, design.H * 5), Image.Resampling.NEAREST))
        x, y = (i % 6) * design.W, (i // 6) * (design.H + 10)
        board.paste(indexed.convert('RGB'), (x, y + 10))
        draw.text((x + 2, y), str(i + 1), fill=(252, 252, 252))
    gif_frames[0].save(HERE / '47_review.gif', save_all=True, append_images=gif_frames[1:],
                       duration=design.FRAME_MS, loop=0, disposal=2, optimize=False)
    board.resize((board.width * 3, board.height * 3), Image.Resampling.NEAREST).save(HERE / '47_review.png')
    # Same right-facing view in all game directions, for style checking only.
    sheet = Image.new('RGBA', (24 * design.W, 8 * design.H))
    for direction in range(8):
        sheet.paste(strip, (0, direction * design.H))
    sheet.save(HERE / '47_moha_moha_corrected_sheet.png')
    print('Exported full 2.4-second GIF at 5x on black', flush=True)


if __name__ == '__main__':
    plugin_draw(make_poses(), HERE / '47_moha_moha_corrected_poses', 'Poses')
    spec = importlib.util.spec_from_file_location('moha_corrected', HERE / '47_moha_moha_design.py')
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    frames = design.write_sources()
    plugin_draw(frames, HERE / '47_moha_moha_corrected', 'R')
    export_review(frames, design)

