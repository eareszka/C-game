from pix import *

PAL = {
    'l': 'a4aaba',  # fur, lit
    'g': '848694',  # fur, mid
    'd': '595965',  # fur shade, iron lit
    'p': 'ec8476',  # ears, feet
    'r': 'b6433d',  # inner ear, nose
    't': 'e8e0c0',  # teeth
    'e': '34343e',  # iron shade
}


def over(im, part, x, y):
    """Paste a part, turning anything already drawn beside it into a black line."""
    px = im.load()
    src = part.load()
    for yy in range(part.height):
        for xx in range(part.width):
            if not src[xx, yy][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + xx + a, y + yy + b
                inside = 0 <= xx + a < part.width and 0 <= yy + b < part.height
                if inside and src[xx + a, yy + b][3]:
                    continue
                if 0 <= nx < im.width and 0 <= ny < im.height and px[nx, ny][3]:
                    px[nx, ny] = BLACK
    stamp(im, part, x, y)


EARS = [
    '.pp....pp.',
    'pppp..pppp',
    'pprrlgpprr',
    '.prlllgpr.',
    '.llllgggg.',
    '.lKllgKgg.',
    '.lKllgKgg.',
    '.llllgggd.',
]

BITE = grid(EARS + [
    '..llrrgd..',
    '...gttg...',
], PAL)

GAPE = grid(EARS + [
    '..llrrgd..',
    '..gttttd..',
    '...KKKK...',
    '...gttg...',
], PAL)

CHEW = grid(EARS + [
    '..llrrgd..',
    '...tttt...',
], PAL)

BODY = grid([
    '..gggddd..',
    '..gggddd..',
    '...ggdd...',
    '..ppp.pp..',
], PAL)

im = canvas(26, 22)

# Bodies stand behind the beam.
over(im, BODY, 8, 13)
over(im, BODY, 0, 15)
over(im, BODY, 16, 15)

# Middle mouse rears up off the beam.
over(im, GAPE, 8, 0)
rect(im, 11, 12, 5, 1, PAL['g'])

# The one shared iron beam.
BEAM_Y = 13
rect(im, 0, BEAM_Y, 26, 1, PAL['d'])
rect(im, 0, BEAM_Y + 1, 26, 2, PAL['e'])

# Side mice gnaw it, out of step with each other.
over(im, BITE, 0, 5)
over(im, CHEW, 16, 3)

# The reared mouse keeps its paws on the beam.
rect(im, 10, BEAM_Y, 2, 1, PAL['p'])
rect(im, 14, BEAM_Y, 2, 1, PAL['p'])

im = outline(im)
save(im)
