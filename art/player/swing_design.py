"""The player swinging a weapon on the map: frames 24 on of
assets/player_small.png, 72 of them, each 14 x 20 --

    frame = 24 + facing * 9 + phase * 3 + arm

    facing  down, up, left, right, down-left, down-right, up-left, up-right
    phase   0 standing, 1 and 2 the two steps of the walk
    arm     0 drawn back to the side the swing starts on, 1 struck out the way
            the player faces, 2 raised beside the head (the scythe is whirled
            from it)

    python art/player/swing_design.py              # report: does the sheet match this?
    python art/player/swing_design.py --json F     # the 72 frames as a design for tools/draw_views.py
    python art/player/swing_design.py --write      # redraw the sheet through the pixel plugin,
                                                   # and write src/player_swing.inc

Every frame is one of the sheet's own walk frames (0-23, read from the sheet
and never changed) with the weapon arm pixelled by hand: K line, H hair, R
shirt, S skin, the sheet's four colours. Standing, the struck frames also
crouch a pixel (facing down) or lean one over planted feet (to the side). On a
step they do not: the walk frame already carries the body's movement, so the
legs, the bob and the free arm all keep walking and only the weapon arm is in
the swing (the user, 2026-10-12).

--write replaces frames 24 on. A frame hand-edited in Aseprite has to be
carried into this script first, or it is lost.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PNG, SRC = os.path.join(ROOT, 'assets', 'player_small.png'), os.path.join(ROOT, 'assets', 'player_small.aseprite')
INC = os.path.join(ROOT, 'src', 'player_swing.inc')
PAL = {'K': '000000', 'H': '633e1b', 'R': 'b6433d', 'S': 'f0b890'}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for k, v in PAL.items()}
W, H, WALK, SWING0 = 14, 20, 24, 24
FACINGS = ['down', 'up', 'left', 'right', 'down_left', 'down_right', 'up_left', 'up_right']
ARMS = ['back', 'struck', 'raised']
# facing: its three walk frames (standing, step, step) and the side its weapon hand is on
WALKS = {'down': ((0, 1, 2), 'r'), 'up': ((3, 4, 5), 'l'), 'left': ((6, 7, 23), 'l'), 'right': ((8, 9, 22), 'r'),
         'down_left': ((10, 11, 12), 'l'), 'down_right': ((13, 14, 15), 'r'),
         'up_left': ((16, 17, 18), 'l'), 'up_right': ((19, 20, 21), 'r')}


def walk_frame(f):
    """Frame f of the sheet as rows of letters."""
    from PIL import Image
    im = Image.open(PNG).convert('RGBA')
    let = {v: k for k, v in RGB.items()}
    return [[let[im.getpixel((f * W + x, y))[:3]] if im.getpixel((f * W + x, y))[3] else '.' for x in range(W)] for y in range(H)]


def apply(g, ops, flip=False, dy=0):
    """Paint ops -- [(letter, [(x, y), ...]), ...], drawn for the right side --
    onto g; flip mirrors them to the left (the body is centred on column 7)."""
    for ch, pts in ops:
        for x, y in pts:
            g[y + dy][14 - x if flip else x] = ch
    return g


def at(pt, flip=False, dy=0):
    return (14 - pt[0] if flip else pt[0], pt[1] + dy)


# ---------------------------------------------------------- front and back views
# The six facings seen from the front or the back share one body. Each arm is
# (its pixels, the hand's pixel), for the right side.
OUT = ([('S', [(11, 14), (12, 14)]), ('K', [(13, 14), (11, 13), (12, 13), (11, 15), (12, 15)])], (12, 14))    # straight out at the shoulder
UP = ([('S', [(11, 13), (12, 12), (12, 11)]), ('K', [(12, 13), (13, 12), (13, 11)]), ('.', [(11, 15), (12, 15)])], (12, 11))   # raised beside the head
REACH = ([('S', [(12, 16)]), ('K', [(13, 16), (12, 17), (11, 17)])], (12, 16))                               # out and down from the hip
LOW = ([('S', [(12, 17)]), ('K', [(13, 17), (12, 18), (11, 17)])], (12, 17))                                 # the same, crouched
FRONT = ([('.', [(11, 16), (12, 16)]), ('S', [(6, 17), (7, 17)])], (6, 17))                                  # crouched, the hand brought round to the front
# facing: (back, struck, raised) standing -- the arm, and whether the body crouches a pixel into it
STANDING = {'down': ((REACH, 0), (FRONT, 1), (UP, 0)), 'up': ((OUT, 0), (UP, 0), (UP, 0)),
            'down_left': ((OUT, 0), (LOW, 1), (UP, 0)), 'down_right': ((OUT, 0), (LOW, 1), (UP, 0)),
            'up_left': ((UP, 0), (OUT, 0), (UP, 0)), 'up_right': ((UP, 0), (OUT, 0), (UP, 0))}

# On a step the body is a pixel down and the arms swing: one hand high beside
# the chest, the other low by the belt. The weapon hand comes off wherever the
# walk has it, then the arm goes on -- the standing arms a pixel down, drawn
# for a right hand.
OUT_S = ([('S', [(11, 15), (12, 15)]), ('K', [(13, 15), (11, 14), (12, 14), (11, 16), (12, 16)])], (12, 15))
UP_S = ([('S', [(11, 14), (12, 13), (12, 12)]), ('K', [(12, 14), (13, 13), (13, 12), (11, 15)])], (12, 12))
REACH_S = ([('S', [(11, 16), (12, 17)]), ('K', [(11, 15), (12, 16), (13, 17), (12, 18), (11, 17)])], (12, 17))
STEP_ARM = {id(OUT): OUT_S, id(UP): UP_S, id(REACH): REACH_S, id(LOW): REACH_S}
HAND_HIGH = [('.', [(11, 15), (12, 15)])]                           # the walk's right hand, when it is the high one
HAND_LOW = [('.', [(11, 17), (12, 17), (11, 16), (12, 16)])]        # and when it is the low one


def crouch(g):
    """Head and body a pixel down over planted feet: the belt row goes."""
    for y in range(16, 5, -1):
        g[y] = g[y - 1][:]
    g[5] = ['.'] * W
    return g


def front_back(face):
    """The nine frames of a front or back facing -> [(rows, hand), ...] in block order."""
    walks, side = WALKS[face]
    flip = side == 'l'
    out = []
    for phase, f in enumerate(walks):
        for arm, crouched in STANDING[face]:
            g = walk_frame(f)
            if phase == 0:
                ops, hand = arm
                apply(crouch(g) if crouched else g, ops, flip)
                for x in (3, 11):       # crouched, a hand hangs past the belt: the line under it
                    if crouched and g[16][x] == 'S' and g[17][x] == '.':
                        g[17][x] = 'K'
                out.append((g, at(hand, flip)))
                continue
            # which of the walk's hands is the high one: the weapon side's, or the other
            high = g[15][at((11, 15), flip)[0]] == 'S'
            assert high or g[17][at((11, 17), flip)[0]] == 'S', (face, f)
            apply(g, HAND_HIGH if high else HAND_LOW, flip)
            if arm is FRONT:
                # the hand at the front of the belt, over the line between the shoes
                x = next(x for x in (6, 7) if g[18][x] == 'K' and g[18][x + 1] == 'K')
                g[17][x] = g[17][x + 1] = 'S'
                out.append((g, (x, 17)))
            else:
                ops, hand = STEP_ARM[id(arm)]
                out.append((apply(g, ops, flip), at(hand, flip)))
    return out


# ------------------------------------------------------------------- side views
E = '.' * W
# standing, facing right, whole: the arm raised ahead; leaning a pixel over planted feet, the arm straight out
SIDE_BACK = [E, E, E, E, E,
             '.....KK.KK....',
             '....KHHKHHK...',
             '...KHHHHHHHK..',
             '..KHHHHHHHHHK.',
             '..KHHHHHHHSHK.',
             '..KHHHHHSSSK..',
             '...KHHSSKKSKK.',
             '....KHSSSSKSK.',
             '....KKRSRKSK..',
             '....KRSRSRK...',
             '....KSRSRK....',
             '....KKKKKK....',
             '.....KKKK.....',
             '.....KRRRK....',
             '.....KKKKK....']
SIDE_STRUCK = [E, E, E, E, E,
               '......KK.KK...',
               '.....KHHKHHK..',
               '....KHHHHHHHK.',
               '...KHHHHHHHHHK',
               '...KHHHHHHHSHK',
               '...KHHHHHSSSK.',
               '....KHHSSKKSK.',
               '.....KHSSSSK..',
               '.....KKRSRKKKK',
               '.....KRSRSRSSK',
               '.....KSRSRKKK.',
               '....KKKKKK....',
               '.....KKKK.....',
               '.....KRRRK....',
               '.....KKKKK....']
SIDE_STANDING = ((SIDE_BACK, (11, 12)), (SIDE_STRUCK, (12, 14)), (SIDE_BACK, (11, 12)))
# on a stride: the front hand off the hip, then the arm, for a player facing right
SIDE_HAND = [('K', [(9, 16)]), ('.', [(10, 16)]), ('R', [(8, 16)])]
SIDE_BACK_S = ([('K', [(12, 12), (12, 13), (11, 14)]), ('S', [(11, 13), (10, 14)])], (11, 13))
SIDE_STRUCK_S = ([('S', [(10, 15), (11, 15)]), ('K', [(12, 15), (10, 14), (11, 14), (10, 16), (11, 16)])], (11, 15))
SIDE_STEP = (SIDE_BACK_S, SIDE_STRUCK_S, SIDE_BACK_S)


def side(face):
    walks, hand_side = WALKS[face]
    flip = hand_side == 'l'
    mirror = lambda rows: [list('.' + r[::-1][:-1]) for r in rows] if flip else [list(r) for r in rows]
    out = []
    for phase, f in enumerate(walks):
        for a in range(3):
            if phase == 0:
                rows, hand = SIDE_STANDING[a]
                out.append((mirror(rows), at(hand, flip)))
            else:
                ops, hand = SIDE_STEP[a]
                out.append((apply(apply(walk_frame(f), SIDE_HAND, flip), ops, flip), at(hand, flip)))
    return out


# -------------------------------------------------------------------- the block
def block():
    """The 72 frames in sheet order -> [(rows of str, hand pixel), ...], each checked."""
    out = []
    for face in FACINGS:
        for g, hand in (side(face) if face in ('left', 'right') else front_back(face)):
            rows = [''.join(r) for r in g]
            assert len(rows) == H and all(len(r) == W for r in rows), face
            assert rows[hand[1]][hand[0]] == 'S', (face, hand, 'the hand is not skin')
            # the line goes all the way round: no colour touches the clear, inside the frame
            open_px = [(x, y) for y in range(H) for x in range(W) if rows[y][x] not in '.K' and any(
                0 <= y + j < H and 0 <= x + i < W and rows[y + j][x + i] == '.' for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
            assert not open_px, (face, len(out) % 9, 'unoutlined at', open_px)
            out.append((rows, hand))
    assert len(out) == 72
    return out


def name(i):
    return '%s_%s_%s' % (FACINGS[i // 9], ('stand', 'step_a', 'step_b')[i % 9 // 3], ARMS[i % 3])


def sheet_image():
    """The whole sheet as it should be: the walk frames as they are, then the block."""
    from PIL import Image
    walk = Image.open(PNG).convert('RGBA').crop((0, 0, WALK * W, H))
    im = Image.new('RGBA', ((WALK + 72) * W, H))
    im.paste(walk, (0, 0))
    for i, (rows, _) in enumerate(block()):
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.':
                    im.putpixel(((WALK + i) * W + x, y), RGB[c] + (255,))
    return im


def inc_text():
    hands = [h for _, h in block()]
    lines = ['// Generated by art/player/swing_design.py --write. Do not edit; change that and re-run.',
             '// The pixel of each swing frame the weapon is held from, in the 14x20 frame:',
             '// frame SWING_FRAME0 + facing * 9 + phase * 3 + arm (entity.h), a row a facing.',
             'static const SDL_Point SWING_HAND[72] = {']
    for f in range(8):
        lines.append('    ' + ' '.join('{%2d,%3d},' % h for h in hands[f * 9:f * 9 + 9]) + '   // ' + FACINGS[f].replace('_', '-'))
    return '\n'.join(lines + ['};', ''])


if __name__ == '__main__':
    from PIL import Image
    args = sys.argv[1:]
    if '--json' in args:
        import json
        frames = block()
        json.dump({'pal': PAL, 'view_w': W, 'order': [name(i) for i in range(72)],
                   'views': {name(i): rows for i, (rows, _) in enumerate(frames)},
                   'hands': [list(h) for _, h in frames]}, open(args[args.index('--json') + 1], 'w'))
        sys.exit()
    want, have = sheet_image(), Image.open(PNG).convert('RGBA')
    if '--write' in args:
        sys.path.insert(0, os.path.join(ROOT, 'art', 'direction'))
        from mcpc import Pixel
        px = Pixel()
        path = px.call('create_canvas', width=want.width, height=H, color_mode='rgb')['file_path']
        pix = [{'x': x, 'y': y, 'color': '#%02x%02x%02x' % want.getpixel((x, y))[:3]}
               for y in range(H) for x in range(want.width) if want.getpixel((x, y))[3]]
        for i in range(0, len(pix), 800):
            px.call('draw_pixels', sprite_path=path, layer_name='Layer 1', frame_number=1, pixels=pix[i:i + 800])
        px.call('save_as', sprite_path=path, output_path=SRC.replace(os.sep, '/'))
        px.call('export_sprite', sprite_path=SRC.replace(os.sep, '/'), output_path=PNG.replace(os.sep, '/'), format='png', frame_number=0)
        got = Image.open(PNG).convert('RGBA')
        assert got.tobytes() == want.tobytes(), 'the export is not what was drawn'
        assert got.crop((0, 0, WALK * W, H)).tobytes() == have.crop((0, 0, WALK * W, H)).tobytes(), 'the walk frames changed'
        open(INC, 'w', encoding='utf-8', newline='\n').write(inc_text())
        print('wrote %s (%d frames, %d pixels) and %s' % (os.path.relpath(PNG, ROOT), want.width // W, len(pix), os.path.relpath(INC, ROOT)))
        sys.exit()
    # report
    off = [name(i) for i in range(72) if have.width < (WALK + i + 1) * W or
           have.crop(((WALK + i) * W, 0, (WALK + i + 1) * W, H)).tobytes() != want.crop(((WALK + i) * W, 0, (WALK + i + 1) * W, H)).tobytes()]
    inc_ok = os.path.exists(INC) and open(INC, encoding='utf-8').read() == inc_text()
    print('sheet: %d frames, the design: %d' % (have.width // W, want.width // W))
    print('frames that differ from the design: %d%s' % (len(off), (' (' + ', '.join(off[:6]) + (' ...' if len(off) > 6 else '') + ')') if off else ''))
    print('src/player_swing.inc: %s' % ('matches' if inc_ok else 'missing or stale'))
    print('report only; --write to apply')
    sys.exit(1 if off or have.width != want.width or not inc_ok else 0)
