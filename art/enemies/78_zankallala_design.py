"""Enemy 78 Zankallala, its animations: the idle and the dash, each from the front, the side and behind.

The user (2026-10-12): idle, it raises its staff, on the frame the fight fires from it; and it needs a
dashing animation in its four directions (the left is the side mirrored).

    idle  10 frames x 130 ms = 1.3 s, the fight's own loop. The snake staff goes up on frames 2-5 and is
          full height on frames 3 and 4 (390-650 ms: where the old sheet's boast frame was shown, 400-650).
          The bees circle the hat. Everything else is the approved frame.
    dash  4 frames (the engine's flap sheet): the jerboa bounding -- crouched, pushed off, tucked in the
          air, coming down -- ears laid back, tail and snake streaming, the staff levelled like a lance
          from the side.

Frames are the first-frame script's own parts, with the few that move swapped for the ones typed here.

    python art/enemies/78_zankallala_design.py look DIR   # PIL only: the GIFs into DIR
    python art/enemies/78_zankallala_design.py            # draw both sheets through the plugin, write the GIFs
"""
from pathlib import Path
import importlib, sys
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
Z = importlib.import_module('78_zankallala_pose_first')
ff, PAL, W, H = Z.ff, Z.PAL, Z.W, Z.H
IDLE_MS, DASH_MS = 130, 60
DRAFT = {'D': '78_zankallala_front_frame0_draft', 'R': '78_zankallala_side_frame0_draft', 'U': '78_zankallala_back_frame0_draft'}
shift = lambda rows, dx=0, dy=0: [(y + dy, x + dx, t) for y, x, t in rows]
dark = lambda rows: [(y, x, ''.join('D' if c in 'ML' else c for c in t)) for y, x, t in rows]      # a far limb


def swap(parts, changes):
    """A view's parts with some replaced: {id(old rows): new rows, (new rows, new kind), or None to drop}."""
    out = []
    for rows, kind in parts:
        new = changes.get(id(rows), rows)
        if new is None: continue
        out.append(new if isinstance(new, tuple) else (new, kind))
    return out


def raised(snake, k, hand_row, x):
    """The snake staff k px higher: all of it above the hand moved up, the length under it made up."""
    return [(y - k if y <= hand_row else y, x0, t) for y, x0, t in snake] + [(y, x, 'S') for y in range(hand_row + 1 - k, hand_row + 1)]


# -- idle ---------------------------------------------------------------------------------------------
#          frame  0  1  2  3  4  5  6  7  8  9
RAISE = (         0, 0, 2, 5, 5, 2, 0, 0, 0, 0)       # px the staff is up; 5 = the frame the fight fires on
BEES  = (         0, 1, 2, 0, 1, 2, 0, 1, 2, 1)
S_ARMS = {0: Z.S_HAND, 2: [(24, 31, 'H'), (24, 32, 'H'), (25, 33, 'HH')], 5: [(24, 31, 'H'), (23, 32, 'H'), (22, 33, 'HH')]}
F_ARMS = {0: Z.F_HAND, 2: [(24, 35, 'H'), (25, 36, 'HH'), (25, 38, 'HH'), (26, 40, 'HH'), (26, 42, 'H')],
          5: [(24, 35, 'H'), (24, 36, 'HH'), (24, 38, 'HH'), (23, 40, 'HH'), (23, 42, 'H')]}
S_BEES = [Z.S_BEES, [(13, 20, 'hG'), (12, 31, 'Gh'), (16, 32, 'G')], [(15, 18, 'G'), (11, 27, 'Gh'), (14, 32, 'hG')]]
F_BEES = [Z.F_BEES, [(13, 22, 'hG'), (12, 36, 'Gh'), (17, 35, 'G')], [(15, 20, 'G'), (11, 32, 'Gh'), (15, 37, 'hG')]]


def idle(v, f):
    k, b = RAISE[f], BEES[f]
    if v == 'R':
        return swap(Z.SIDE, {id(Z.S_SNAKE): raised(Z.S_SNAKE, k, 27, 35), id(Z.S_HAND): S_ARMS[k], id(Z.S_BEES): S_BEES[b]})
    snake, arm = raised(Z.F_SNAKE, k, 28, 43), F_ARMS[k]
    if v == 'D':
        return swap(Z.FRONT, {id(Z.F_SNAKE): snake, id(Z.F_HAND): arm, id(Z.F_BEES): F_BEES[b]})
    out = []                                              # behind: the same staff on the other side
    for rows, kind in Z.BACK:
        if rows == Z.mirror(Z.F_SNAKE): rows = Z.mirror(snake)
        elif rows == Z.mirror(Z.F_HAND): rows = Z.mirror(arm)
        elif rows is Z.F_BEES: rows = F_BEES[b]
        out.append((rows, kind))
    return out


# -- dash: typed. From the side ------------------------------------------------------------------------
UP      = (0, 4, 7, 2)                                # px off the ground: crouched, pushed off, in the air, coming down
FEET_UP = (0, 0, 5, 0)                                # front and back: how far its feet have left the ground
LEGS    = ('stand', 'push', 'tuck', 'stand')
S_LEG_PUSH = [(36, 21, 'MMMMMMM'), (37, 20, 'MMMMMMMM'), (38, 19, 'MMMMMMMM'), (39, 18, 'MMMMMMMM'), (40, 17, 'MMMMMMM'),   # straight out behind,
              (41, 16, 'MMMMMMM'), (42, 15, 'MMMMMM'), (43, 14, 'MMMMMM'), (44, 13, 'MMMMM'), (45, 12, 'MMMMM'),           # thick at the hip,
              (46, 11, 'MMMMM'), (47, 10, 'MMMM'), (48, 9, 'MMMM'), (49, 7, 'MMMMM'), (50, 5, 'LLLLLL'), (51, 4, 'MMMMM')]  # toes last off the ground
S_LEG_TUCK = [(36, 21, 'MMMMMMMM'), (37, 20, 'MMMMMMMMMM'), (38, 20, 'MMMMMMMMMM'), (39, 20, 'MMMMMMMMMM'), (40, 21, 'MMMMMMMMM'),
              (41, 22, 'MMMMMMMM'), (42, 23, 'MMMMMMMMMMM'), (43, 25, 'MMMMMMMMMMM'), (44, 27, 'LLLLLLLLLLL'), (45, 29, 'MMMMMMMMM')]   # folded forward under the belly
S_ARM_RUN = [(40, 38, 'MM'), (41, 39, 'MM'), (42, 40, 'MM'), (43, 41, 'ML'), (44, 42, 'LL')]                                # forepaws reaching
S_TAIL_RUN = [(35, 14, 'MMMM'), (36, 15, 'MM'), (34, 10, 'MMMMM'), (35, 11, 'MMM'), (33, 6, 'MMMMM'), (34, 7, 'MMM')]       # streaming out behind
S_TUFT_RUN = [(31, 2, 'HHH'), (32, 1, 'HHHHH'), (33, 1, 'HHHHH'), (34, 2, 'HHH')]
S_EAR_RUN = [(24, 32, 'MMM'), (25, 32, 'MMMMM'), (26, 33, 'MDDMMM'), (27, 35, 'MDDMM'), (28, 37, 'MMMMM'), (29, 39, 'MMM')]  # laid back
S_LANCE = [(27, 33, 'SS'), (26, 34, 'SS'), (25, 36, 'SS'), (24, 38, 'SS'), (23, 40, 'SS'), (22, 42, 'SS'), (21, 44, 'SS'),    # the staff levelled ahead,
           (20, 46, 'SSS'), (19, 47, 'SS'),
           (28, 30, 'SSSS'), (29, 24, 'SSSSSSS'), (30, 17, 'SSSSSSSS'), (31, 11, 'SSSSSSS'), (32, 7, 'SSSSS')]               # the rest of it streaming
S_HAND_RUN = [(24, 31, 'H'), (25, 32, 'H'), (26, 33, 'H')]
S_BEES_RUN = [[(14, 18, 'Gh'), (12, 15, 'hG'), (16, 13, 'G')], [(13, 17, 'hG'), (15, 14, 'Gh'), (11, 19, 'G')]]            # left behind the hat
S_LEGS = {'stand': ((Z.S_LEG, 'raw'), Z.S_FAR_LEG, Z.S_ARM, Z.S_FAR_ARM),
          'push': ((S_LEG_PUSH, 'solid'), dark(shift(S_LEG_PUSH, -3)), S_ARM_RUN, dark(shift(S_ARM_RUN, 2))),
          'tuck': ((S_LEG_TUCK, 'solid'), dark(shift(S_LEG_TUCK, -3, -1)), S_ARM_RUN, dark(shift(S_ARM_RUN, 2)))}


def dash(v, f):
    up = UP[f]
    lift = lambda parts: [(shift(rows, 0, -up), kind) for rows, kind in parts]
    if v == 'R':
        leg, far_leg, arm, far_arm = S_LEGS[LEGS[f]]
        return lift(swap(Z.SIDE, {id(Z.S_TAIL): S_TAIL_RUN, id(Z.S_TUFT): S_TUFT_RUN, id(Z.S_EAR): S_EAR_RUN,
                                  id(Z.S_FAR_EAR): dark(shift(S_EAR_RUN, 3, -1)), id(Z.S_LEG): leg, id(Z.S_FAR_LEG): far_leg,
                                  id(Z.S_ARM): arm, id(Z.S_FAR_ARM): far_arm, id(Z.S_SNAKE): S_LANCE, id(Z.S_HAND): S_HAND_RUN,
                                  id(Z.S_BEES): S_BEES_RUN[f % 2]}))
    # front and back: the body bounds up off its feet, which leave the ground only at the top
    feet = (Z.F_FOOT, Z.mirror(Z.F_FOOT))
    parts = idle(v, 0)
    body = lift([(F_BEES[f % 3] if rows is Z.F_BEES else rows, kind) for rows, kind in parts if rows not in feet])
    legs = []                                             # each foot with the leg that has come out above it, as one part
    for foot in feet:
        shank = [(y, foot[0][1], 'MMM') for y in range(45 - up, 46 - FEET_UP[f])] if up > FEET_UP[f] else []
        legs.append((shank + shift(foot, 0, -FEET_UP[f]), 'solid'))
    return legs + body


SHEETS = {'idle': (idle, len(RAISE), IDLE_MS), 'dash': (dash, len(UP), DASH_MS)}


def build():
    for v, parts in (('D', Z.FRONT), ('R', Z.SIDE), ('U', Z.BACK)):     # the approved drafts must still be these drawings
        assert ff.saved(HERE / (DRAFT[v] + '.aseprite')).tobytes() == ff.image(Z.view(parts)[0], PAL, W, H).tobytes(), \
            f'{DRAFT[v]} was edited: read it back before animating from the typed parts'
    out = {}
    for name, (make, n, ms) in SHEETS.items():
        out[name] = {v: [Z.view(make(v, f)) for f in range(n)] for v in DRAFT}
        for v, frames in out[name].items():
            for g, thin in frames: ff.checks(g, PAL, W, H, open_ok=lambda p, c: p in thin)
            assert all(a[0] != b[0] for a, b in zip(frames, frames[1:] + frames[:1])), f'{name} {v}: two frames in a row are the same'
    assert all(out['idle'][v][0][0] == Z.view(parts)[0] for v, parts in (('D', Z.FRONT), ('R', Z.SIDE), ('U', Z.BACK)))
    return out


def staff_tip(g):
    """The top of the snake's head: the middle of its highest green pixels, in frame pixels."""
    top = min(y for (x, y), c in g.items() if c == 'S')
    xs = [x for (x, y), c in g.items() if c == 'S' and y == top]
    return (sum(xs) / len(xs) + 0.5, top + 0.5)


def panel(sheet, i):
    """Frame i of a sheet from all four sides, labelled, at one scale."""
    im = Image.new('RGBA', (4 * (W + 2) + 2, H + 12), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for k, (label, v, mirrored) in enumerate((('FRONT', 'D', False), ('RIGHT', 'R', False), ('BACK', 'U', False), ('LEFT', 'R', True))):
        fr = ff.image(sheet[v][i][0], PAL, W, H)
        d.text((2 + k * (W + 2) + 14, 0), label, fill=(252, 252, 252, 255))
        im.alpha_composite(ImageOps.mirror(fr) if mirrored else fr, (2 + k * (W + 2), 12))
    return im


if __name__ == '__main__':
    sheets = build()
    look = sys.argv[1:2] == ['look']
    out = Path(sys.argv[2]) if look else HERE
    out.mkdir(parents=True, exist_ok=True)
    gif_pal = {**PAL, 'w': 'fcfcfc'}                      # the labels' white
    for name, (make, n, ms) in SHEETS.items():
        print(f'{name}: {n} frames x {ms} ms, 3 drawn views (left = right mirrored)', flush=True)
        if not look:
            frames = [g for v in DRAFT for g, thin in sheets[name][v]]
            ff.draw_frames(frames, PAL, W, H, HERE / f'78_zankallala_{name}_draft', ms, {v: (k * n + 1, k * n + n) for k, v in enumerate(DRAFT)})
        ff.gif([panel(sheets[name], i) for i in range(n)], out / f'78_{name}.gif', ms, gif_pal)
        for v in DRAFT:
            print(f'  {v} staff tip by frame: ' + ' '.join('(%.1f, %.1f)' % staff_tip(g) for g, thin in sheets[name][v]), flush=True)
    # from the side, in the order the fight shows them: a stop with its boast, then the dash
    side = lambda name, i: ff.image(sheets[name]['R'][i][0], PAL, W, H)
    seq = [(side('idle', i), IDLE_MS) for i in range(10)] + [(side('dash', i % 4), DASH_MS) for i in range(12)]
    ff.gif([im for im, ms in seq], out / '78_stop_then_dash_side.gif', [ms for im, ms in seq], PAL, scale=7)
