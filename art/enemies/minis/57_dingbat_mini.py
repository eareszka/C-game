"""57 Dingbat's map mini: the owl-thing of Rice Lake, a short feathered body, short antlers, great wings, always in
the air, swooping at you, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has one view, its front. Through PixelLab (art/enemies/pixellab/57_dingbat/mini, pixellab-out/
57-mini, five generations): eight rotations of its battle front, then its front, back and left side each given a
flight -- a slow strong wingbeat, then a glide, wings spread. The left side came back with its wings folded, not
flying; its three-quarter view (south-west) flew, and is its side. At 15 px their shrinks lost its face and
antlers and gave its wings another span in each view, so each frame is drawn by hand after them: one body a view
between two wings, the same two wingbeats on every view (raised in a V, then spread in the glide), one black
outline round it all. Its back is its front's body from behind. The right view is the left mirrored.
It flies: on the map it hovers above its shadow (mini_hover() in src/main.cpp), bobbing with its wingbeat.
15 px tall: its battle height (42 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
owl tan (body, wings), its dark brown (the wings' undersides and shadowed feathers), its cream (belly, face,
antlers; its grey feet go to it).

Its chase: the swoop (as the Alber's, chase_speed(), src/main.cpp) -- a glide, then wingbeats.

    python art/enemies/minis/57_dingbat_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '967448', 'D': '633e1b', 'L': 'e8e0c0'}
CHASE = 'swoop'
HEIGHT = 15
HOVER = 7                                        # its shadow's half width, art px (mini_hover() in src/main.cpp)
# Drawn by hand, fill only (one outline round it all at the end): at 15 px the shrinks of PixelLab's flights lost
# its face and antlers, and its wings came out a different span in every view. One body a view, between two wings,
# the same two wingbeats on every view: raised in a V, then spread in the glide. M tan, D dark brown, L cream, K eyes.
FRONT = [                                        # antlers, its crown, its face's disc, two great eyes, its eerie
    'L.L..L.L',                                  # grin (the user: "have a errie mouth in mini as well"), its belly
    '.LL..LL.',
    '..MMMM..',
    '.MMMMMM.',
    'MLLMMLLM',
    'MLKLLKLM',
    'MLKKKKLM',
    '.MKLKLM.',
    'MMLLLLMM',
    'MMLLLLMM',
    '.MLLLLM.',
    '..MMMM..',
    '..L..L..',
]
BACK = [                                         # its front's body from behind: all tan, its tail feathers low
    'L.L..L.L',
    '.LL..LL.',
    '..MMMM..',
    '.MMMMMM.',
    'MMMMMMMM',
    'MMMMMMMM',
    'MMMMMMMM',
    '.MMMMMM.',
    'MMMMMMMM',
    'MMMMMMMM',
    '.MMDDMM.',
    '..MDDM..',
    '..L..L..',
]
SIDE = [                                         # three quarters, its face turned to the left
    '.L.L.L..',
    '..LLL...',
    '.MMMMM..',
    'MMMMMMM.',
    'LLMLLMM.',
    'LKLLKMMM',
    'LKKKLMMM',
    '.KLKLMMM',
    '.LLLMMMM',
    '.MLLMMMD',
    '..LLMMD.',
    '..MMMD..',
    '...L.L..',
]
WING_UP = {1: 'MM........', 2: 'DMMM......', 3: '.DMMMM....', 4: '..DMMMMM..',      # the left wing, raised: rows of
           5: '...DDMMMMM', 6: '....DDMMMM', 7: '.....DDMMM', 8: '.......DDM'}     # the body, its root by the body
WING_GLIDE = {5: '..MMMMMMMM', 6: 'MMMMMMMMMM', 7: 'DDMMMMMMMM', 8: '.DDDDDMMMM', 9: '.....DDDDM'}


def bird(body, wing, far=0):
    """Its body between its wings, centred, its feet's row on the cell's last but one; the right wing the left
    mirrored. far: columns cut off the left wing's tip, the far wing in three quarters."""
    g = {(10 + x, y): c for y, r in enumerate(body) for x, c in enumerate(r) if c != '.'}
    for y, r in wing.items():
        for x, c in enumerate(r):
            if c == '.': continue
            if x >= far: g[x, y] = c
            g[27 - x, y] = c
    x0, y0 = minis.W // 2 - 14, minis.H - 1 - len(body)
    return ff.outline({(x + x0, y + y0): c for (x, y), c in g.items()})


FRAMES = {v: [bird(b, WING_UP, far), bird(b, WING_GLIDE, far)] for v, b, far in (('D', FRONT, 0), ('U', BACK, 0), ('L', SIDE, 3))}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(57, 'dingbat', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(57, CHASE, FRAMES, PAL, hover=HOVER)
