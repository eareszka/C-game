"""The player swimming (the oasis): three frames of a doggy-paddle facing
right, the same mirrored facing left -- each 14 x 20, the player's own head
from assets/player_small.png (frame 9) over a small body made for the water
(user: redone to fit the sprite's small size): it leans into the stroke, the
pants trail back, the shoes flutter behind, and it bobs a pixel as it pulls.

    python art/player/swim_design.py <design.json>
    python tools/draw_views.py <design.json> art/player/swim

    0  reach    the hand out in front, the shoes level behind
    1  pull     the hand drawn in, a kick, the whole body lifted a pixel
    2  recover  the hand back up by the chin, the shoes low
"""
import json, sys

PAL = {'K': '000000', 'a': '633e1b', 'b': 'f0b890', 'c': 'b6433d'}   # player_small.png's

HEAD = [".....KK.KK....",     # frame 9's head, as it is
        "....KaaKaaK...",
        "...KaaaaaaaK..",
        "..KaaaaaaaaaK.",
        "..KaaaaaaabaK.",
        "..KaaaaabbbK..",
        "...KaabbKKbK..",
        "....KabbbbK..."]
# Each frame: how far down the head sits (the body bobs with the stroke), and
# the body under it -- leaning forward, a doggy-paddle arm under the chin, the
# pants trailing back and a flutter of the shoes behind. Small and chunky, as
# the walking frames are (user: fit the sprite's small size).
FRAMES = [
    (6, ["...KKKcbcKKK..",     # reach: the hand out in front, the shoes level behind
         "..KcbcbcbcbbK.",
         "..KbcbcbKKKK..",
         ".KKKKKKK......",
         "KccKK.........",
         "KKK..........."]),
    (5, ["....KKcbcK....",     # pull: the hand drawn in under, a kick -- the body lifts
         "...KcbcbcbK...",
         "..KbcbcKbbK...",
         ".KKKKKKKKK....",
         "KccKccK.......",
         "KKKKKKK......."]),
    (6, ["...KKKcbcKbbK.",     # recover: the hand back up by the chin, the shoes low
         "..KcbcbcbcKK..",
         "..KbcbcbcK....",
         ".KKKKKKK......",
         ".KKccK........",
         "..KKKK........"]),
]


def design():
    right = []
    for top, body in FRAMES:
        f = ['.' * 14] * top + HEAD + body
        right.append((f + ['.' * 14] * 20)[:20])
    left = [[r[::-1] for r in f] for f in right]
    frames = right + left
    for f in frames:
        assert len(f) == 20 and all(len(r) == 14 for r in f)
    return {'pal': PAL, 'view_w': 14, 'order': ['r0', 'r1', 'r2', 'l0', 'l1', 'l2'],
            'views': dict(zip(['r0', 'r1', 'r2', 'l0', 'l1', 'l2'], frames))}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
