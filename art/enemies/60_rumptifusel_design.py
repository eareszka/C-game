"""60 Rumptifusel, big tier: the fur pelt that lies like a dropped coat, its one 3/4 view, from the user's frame.

    python art/enemies/60_rumptifusel_design.py          writes 60_rumptifusel.txt and .json

The user (2026-10-11) sent a reference picture; a first pose was typed after it
(60_rumptifusel_pose_first.py); they redrew that and said "updated the first frame have it breath
covering the purple part and eyes blinking". Their drawing (60_rumptifusel_user_frame.png) is
frame 0, pixel for pixel; the other frames move its pixels and draw nothing (HEAVE, LEAN, COVER, BLINK).
Then, of the first idle: "have it still be the same fps, but it takes longer to close the belly and
the eyes" -- so the frames stay 162 ms each and there are more of them: six to close the belly, the
eyes half shut before they shut. Then: "have the rest of the upper right body sway and move more" --
so its back and hood lean back as it breathes in and slump toward its head as it breathes out, and
sink below where they rest while it lies covered (LEAN, HEAVE).

Their drawing faces left, as their picture does, and (the user, after it was installed turning
with the player): "have the enemys pose always be left facing". So the sheet holds the drawing as
it is in every direction -- it is written as the left-facing views as well as the 3/4 one, and
nothing is mirrored -- and it lies the same way round wherever the player stands.

In its fight it throws its pore sheets when the idle comes to frame 2 (breath_frame), "hood reared,
belly bared": the frame its back is highest on and its belly still bare. Twelve frames at 162 ms are
a 1.94 s loop where the old one was 1.3 s, so it throws its sheets that much less often. Sheets and
rings leave from the middle of the frame (class Rumptifusel has no art coordinates)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the frame, as the old sheet's; row 0 stays empty
PAL = {'K': '000000', 'D': '3c2412', 'M': '633e1b', 'L': '94703d',   # outline, and its eyes; its fur: turned away, the body of it, lit (and the glint in each eye)
       'U': '664b95', 'u': '361f42'}                      # its belly, and the pores and shade of it
LETTER = {v: k for k, v in PAL.items()}
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# the idle: twelve frames played straight through, 162 ms each
RISE_ROWS = (30, 20)                                      # the rows of its back that are repeated to lift all that is above them: the first, then the second as well
SINK_ROWS = (14, 18, 27)                                  # the rows taken out to lower it: each is one the outline stays shut without
LEANS = {0: (), 1: ((18, 1),), 2: ((13, 2), (18, 1)),     # how far its hood is over -> (down to this row, this many columns), top first; + is back, away from its head.
         -1: ((18, -1),), -2: ((16, -2), (24, -1)), -3: ((16, -3), (23, -2), (30, -1))}   # Every row named is one it can bend at without opening its outline
EYES = ((15, 17, 50, 53), (22, 24, 48, 51))               # each eye: its columns, first to last, and its rows
HEAVE = (0, 1, 2, 1, 0, -1, -1, -2, -3, -3, -2, -1)       # its back and hood: up a pixel, two on frame 2; then sinking as it breathes out, lowest while it lies covered
LEAN  = (0, 1, 2, 1, 0, -1, -2, -3, -3, -3, -2, -1)       # and swaying: back as it rises, slumped toward its head as it sinks
COVER = (0, 0, 0, 0.15, 0.3, 0.45, 0.6, 0.8, 1, 1, 0.6, 0.3)   # breath out: how much of the belly the roll has come down over -- six frames to close, two to open
BLINK = (0, 0, 0, 0, 0, 1, 1, 2, 2, 1, 0, 0)              # its eyes: 1 the lids half down, 2 shut

def user():
    """The user's frame as they saved it: {pixel: letter}."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '60_rumptifusel_user_frame.png')).convert('RGBA'); assert im.size == (W, H), im.size
    return {(x, y): LETTER['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}

def heave(g, n):
    """Its back n pixels higher: for each of the first n RISE_ROWS, all above that row goes up one and the row is there twice.
    Or -n pixels lower: each of the first -n SINK_ROWS is taken out and all above it comes down one."""
    for r in RISE_ROWS[:max(n, 0)]: g = {**{(x, y - 1): c for (x, y), c in g.items() if y <= r}, **{p: c for p, c in g.items() if p[1] >= r}}
    for r in SINK_ROWS[:max(-n, 0)]: g = {(x, y + (y < r)): c for (x, y), c in g.items() if y != r}
    return g

def lean(g, level):
    """Its hood leaned: each row goes over by what LEANS gives it; the rows below the last one named stay."""
    over = lambda y: next((dx for row, dx in LEANS[level] if y <= row), 0)
    out = {(x + over(y), y): c for (x, y), c in g.items()}; assert len(out) == len(g)
    return out

def cover(g, share):
    """The roll come down over that share of the belly. In each column of the belly the roll's under edge, and the shade
    above it, slide toward the ground line by that share of the belly's height there, and the fur above is repeated to follow."""
    if not share: return g
    out = dict(g)
    for x in sorted({p[0] for p, c in g.items() if c in 'Uu'}):
        belly = sorted(y for (px, y), c in g.items() if px == x and c in 'Uu')
        edge, ground = belly[0] - 1, belly[-1] + 1        # the roll's under edge over the belly, and the line the belly rests on
        assert belly == list(range(belly[0], belly[-1] + 1)) and g[(x, edge)] == 'K' and g[(x, ground)] == 'K', x
        fur = next(y for y in range(edge - 1, 0, -1) if g[(x, y)] not in 'KD'); assert g[(x, fur)] in 'ML', (x, fur)
        d = int(share * (ground - edge) + 0.5)
        for y in range(fur, fur + d): out[(x, y)] = g[(x, fur)]
        for y in range(fur, edge + 1): out[(x, y + d)] = g[(x, y)]
    return out

def blink(g, shut):
    """Its eyes closing: the fur over each eye comes down over its top row (1, half shut), then over two and the glint goes dark,
    leaving its lower lid (2, shut)."""
    if not shut: return g
    out = dict(g)
    for x0, x1, y0, y1 in EYES:
        for x in range(x0, x1 + 1):
            for y in range(y0, y0 + shut):
                if g[(x, y)] in 'KL': out[(x, y)] = g[(x, y0 - 1)] if g[(x, y0 - 1)] != 'K' else 'M'
            for y in range(y0 + 2, y1 + 1):
                if shut == 2 and g[(x, y)] == 'L': out[(x, y)] = 'K'
    return out

def bare(g):
    """Colour with nothing beside it: where the outline is open."""
    return {p for p, c in g.items() if c != 'K' and any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}

def FRAMES():
    p = user()
    fs = [heave(lean(blink(cover(p, c), b), l), h) for h, l, c, b in zip(HEAVE, LEAN, COVER, BLINK)]
    assert fs[0] == p                                     # the user's frame is frame 0
    for i, f in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in f), i
        assert len(bare(f)) <= len(bare(p)), (i, sorted(bare(f) - bare(p)))     # no move opens the outline
        assert f != fs[i - 1], i                          # each frame moves
        assert (COVER[i] == 1) == (not any(c in 'Uu' for c in f.values())), i  # covered means no purple left, and only then
    return fs

def numbers(g):
    """What the bible measures, of one frame, and what is at the fight's point."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    belly = [p for p in g if g[p] in 'Uu']
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'edge that is black %': round(100 * (len(edge) - len(bare(g))) / len(edge), 1), 'open edge': sorted(bare(g)),
            'belly box': (min(p[0] for p in belly), min(p[1] for p in belly), max(p[0] for p in belly), max(p[1] for p in belly)) if belly else None,
            'at the frame middle': g.get((W // 2, H // 2), 'nothing'), 'frame middle': (W / 2, H / 2)}

if __name__ == '__main__':
    fr = FRAMES()
    for k, v in numbers(fr[0]).items(): print('%-22s %s' % (k, v))
    flat_parts.write('60_rumptifusel', fr, PAL, W, H, dirs='quarter', view=('DR', 'DL', 'L', 'UL'))   # as drawn in every direction: always facing left
