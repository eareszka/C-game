"""The town's signpost (sheet cell 0,0; town_0's value 6): a small wooden
board on a post, in the oblique view the houses are drawn in -- its front
square on, its top and right edge receding up and to the right -- the face
the houses' cream trim, framed in the doors' wood, two strokes of writing.

    python art/structures/town/sign_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/town/sign
"""
import json, sys

PAL = {'K': '000000', 'W': '94703d', 'M': 'e8e0c0', 'D': '633e1b'}   # line, wood, face, its writing and shade
X0, X1, Y0, Y1 = 1, 12, 3, 10          # the board's front face
PX0, PX1 = 5, 8                         # the post, outline to outline


def design():
    g = [['.'] * 16 for _ in range(16)]
    for x in range(X0 + 1, X1 + 2):    # the top, one row back
        g[Y0 - 1][x] = 'W'
    for x in range(X0 + 1, X1 + 3):
        g[Y0 - 2][x] = 'K'
    g[Y0 - 1][X0] = 'K'                # the top's near corner
    for y in range(Y0 - 1, Y1):        # the right edge, one column back, in shade
        g[y][X1 + 1] = 'D'
        g[y][X1 + 2] = 'K'
    g[Y1][X1 + 1] = 'K'                # its foot
    for y in range(Y0, Y1 + 1):        # the front: black round, a frame of wood, the face
        for x in range(X0, X1 + 1):
            if x in (X0, X1) or y in (Y0, Y1):
                c = 'K'
            elif x in (X0 + 1, X1 - 1) or y in (Y0 + 1, Y1 - 1):
                c = 'W'
            else:
                c = 'M'
            g[y][x] = c
    for x in (4, 5, 7, 8, 9):          # the writing
        g[6][x] = 'D'
    for x in (4, 5, 6, 7):
        g[8][x] = 'D'
    for y in range(Y1 + 1, 16):        # the post
        for x in range(PX0, PX1 + 1):
            g[y][x] = 'K' if x in (PX0, PX1) or y == 15 else 'W' if x == PX0 + 1 else 'D'
    rows = [''.join(r) for r in g]
    return {'pal': PAL, 'view_w': 16, 'order': ['sign'], 'views': {'sign': rows}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
