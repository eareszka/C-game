"""70 Trollgadda, big tier: the troll pike with a tree wedged in its jaws, its one side view, from the user's frame.

    python art/enemies/70_trollgadda_design.py                 writes 70_trollgadda.txt and .json
    python art/enemies/70_trollgadda_design.py check           which columns and rows it can bend at without opening its outline

The user (2026-10-11): "please try not to use shapes. have it only have the sideways frames from the
orignal. its a green fish with a tree sticking out of its mouth similar to the orignal. follow the
bible exactly please". A first pose was typed by hand (70_trollgadda_pose_first.py); they redrew it --
a shorter head, the mouth gaping round a thick trunk, the canopy drawn in over the head -- and said
"i updated the first frame have all swimming frames match". Their drawing
(70_trollgadda_user_frame.png) is frame 0, pixel for pixel but for MEND; the other four frames move
its pixels and draw nothing (TAIL, LEAN, SINK, JAW).

In its fight it never moves: scales and bell rings leave from the middle of the frame, leaves from
a band 40 px either side of that and up to 10 px above it (class Trollgadda has no art coordinates).
Its bells ring on idle frame 2 (breath_frame), "jaws strained widest": the frame the jaw drops on."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import flat_parts
W, H = 98, 65                                             # the frame, as the old sheet's; row 0 stays empty
PAL = {'K': '000000', 'g': '2c6c44', 'G': '4fa667', 'B': 'e8e0c0',   # outline; the fish: its back, its flank, its belly
       'A': '00a800', 'a': '4edc4a',                      # the leaves, and where they are lit (their shade is the fish's back)
       'T': '583518', 't': '815423',                      # wood and fins: under and away, and the body of it
       'W': 'fcfcfc'}                                     # the eye's white
LETTER = {v: k for k, v in PAL.items()}
image = lambda g, bg=None: flat_parts.image(g, PAL, W, H, bg)

# Three pixels of the canopy's right edge were left behind at column 96 when the canopy was moved in
# the editor (rows 14-16, where that edge is open): they are put back on the edge.
MEND = {'from': 96, 'to': 85, 'rows': (14, 15, 16)}

# the idle: five frames played straight through, each a pixel from the last
TAIL_TO, TIPS_TO = 19, 15                                 # the tail fin is every column up to the first; the line at its root (column 20) takes up the step. Its tips, up to the second, go a pixel further on a full flick
CROWN_TO = 15                                             # the top of the canopy, down to this row, is what leans
JAW_COLS, JAW_ROW = (51, 71), 44                          # the lower jaw: these columns from this row down drop a pixel, the row doubled
TAIL = (0, -1, -2, 0, 1)                                  # the tail fin: up, flicked full up, back, down
LEAN = (0, 1, 0, -1, -1)                                  # the crown: toward its head, back, away, held
SINK = (0, 0, 1, 1, 0)                                    # the whole of it a pixel lower
JAW  = (0, 0, 1, 0, 0)                                    # frame 2: jaws strained widest

def user():
    """The user's frame as they saved it: {pixel: letter}."""
    from PIL import Image
    im = Image.open(os.path.join(HERE, '70_trollgadda_user_frame.png')).convert('RGBA'); assert im.size == (W, H), im.size
    return {(x, y): LETTER['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x, y))[3]}

def pose():
    """Their frame, the three stray pixels back on the canopy's edge."""
    g = user()
    for y in MEND['rows']:
        assert g.get((MEND['from'], y)) == 'K' and (MEND['to'], y) not in g and g.get((MEND['to'] - 1, y)) == 'A', y
        del g[(MEND['from'], y)]; g[(MEND['to'], y)] = 'K'
    assert all(0 <= x < W and 1 <= y < H for x, y in g)
    return g

def tail(g, dy):   return {(x, y + (dy > 0) - (dy < 0) if TIPS_TO < x <= TAIL_TO else y + dy * (x <= TIPS_TO)): c for (x, y), c in g.items()}
def lean(g, dx):   return {(x + dx * (y <= CROWN_TO), y): c for (x, y), c in g.items()}
def sink(g, dy):   return {(x, y + dy): c for (x, y), c in g.items()}
def jaw(g, open_):
    """The lower jaw a pixel lower: its columns from JAW_ROW down, that row left where it was as well."""
    if not open_: return g
    low = lambda p: JAW_COLS[0] <= p[0] <= JAW_COLS[1] and p[1] >= JAW_ROW
    return {**{p: c for p, c in g.items() if not low(p) or p[1] == JAW_ROW}, **{(x, y + 1): c for (x, y), c in g.items() if low((x, y))}}

def bare(g):
    """Colour with nothing beside it: where the outline is open."""
    return {p for p, c in g.items() if c != 'K' and any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}

def FRAMES():
    p = pose()
    fs = [sink(lean(tail(jaw(p, j), t), l), s) for t, l, s, j in zip(TAIL, LEAN, SINK, JAW)]
    assert fs[0] == p                                     # the user's frame is frame 0
    for i, f in enumerate(fs):
        assert all(0 <= x < W and 1 <= y < H for x, y in f), i
        assert len(f) >= len(p), i                        # nothing lands on anything else
        assert len(bare(f)) <= len(bare(p)), (i, sorted(bare(f)))     # no move opens the outline
        assert f != fs[i - 1], i                          # each frame moves
    return fs

def numbers(g):
    """What the bible measures, of one frame, and where the fight's points fall on it."""
    edge = {p for p in g if any(flat_parts.add(p, d) not in g for d in flat_parts.N4)}
    inner = sum(1 for p, c in g.items() if c == 'K' and p not in edge)
    xs = [p[0] for p in g]; ys = [p[1] for p in g]
    fish = [p for p in g if g[p] in 'GB']
    leaves = [p for p in g if g[p] in 'Aa']
    return {'box': (min(xs), min(ys), max(xs), max(ys)), 'size': (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1), 'colours': len(set(g.values()) - {'K'}),
            'black inside %': round(100 * inner / len(g), 1), 'edge that is black %': round(100 * (len(edge) - len(bare(g))) / len(edge), 1), 'open edge': sorted(bare(g)),
            'fish middle': (round(sum(p[0] for p in fish) / len(fish) + 0.5, 1), round(sum(p[1] for p in fish) / len(fish) + 0.5, 1)),
            'canopy box': (min(p[0] for p in leaves), min(p[1] for p in leaves), max(p[0] for p in leaves), max(p[1] for p in leaves)),
            'at the frame middle': g.get((W // 2, H // 2), 'nothing'), 'frame middle': (W / 2, H / 2)}

if __name__ == '__main__':
    p = pose()
    if sys.argv[1:2] == ['check']:
        base = len(bare(p))
        ok = lambda f: len(bare(f)) <= base and len(f) == len(p)
        print('open at rest', sorted(bare(p)))
        print('tail can hinge after column', [c for c in range(10, 21) if all(ok({(x, y + d * (x <= c)): k for (x, y), k in p.items()}) for d in (1, -1))])
        print('crown can hinge after row  ', [r for r in range(3, 27) if all(ok({(x + d * (y <= r), y): k for (x, y), k in p.items()}) for d in (1, -1))])
        print('jaw dropped opens', sorted(bare(jaw(p, 1)) - bare(p)))
    else:
        fr = FRAMES()
        for k, v in numbers(fr[0]).items(): print('%-22s %s' % (k, v))
        flat_parts.write('70_trollgadda', fr, PAL, W, H, dirs='profile', view='R')
