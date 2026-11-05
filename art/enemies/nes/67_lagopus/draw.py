from pix import *

PAL = {
    'w': 'fcfcfc',
    'l': 'c6ccda',
    'm': '9797aa',
    'd': '595965',
    'r': 'b6433d',
    'R': '7c0a1b',
}


def over(im, part, x, y):
    """Stamp a part, with a black line only where it crosses what is already drawn."""
    src, dst = part.load(), im.load()
    for yy in range(part.height):
        for xx in range(part.width):
            if not src[xx, yy][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = xx + a, yy + b
                inside = 0 <= nx < part.width and 0 <= ny < part.height
                if inside and src[nx, ny][3]:
                    continue
                if 0 <= x + nx < im.width and 0 <= y + ny < im.height and dst[x + nx, y + ny][3]:
                    dst[x + nx, y + ny] = BLACK
    stamp(im, part, x, y)


WING = [
    '......wwww.......',
    '....wwwwwwww.....',
    '...wwwwwwwwwww...',
    '..wwwllwlllwwwww.',
    '.wwlllKllKlllwwww',
    '.wlKKKmmKKKllllww',
    'wwlKlmmmmmmKKllww',
    'wlKlmmKlmmmmmKKll',
    'wlKlmKlmmmmmmmmKl',
    'llKlmKlmmKlmmmmmK',
    'mmKlmKlmmKlmmmmmm',
    'dmKlmmKlmmKlmmmmm',
    'ddKlmmKlmmKlmmmmm',
    '.ddKlmKlmmmKlmmmm',
    '..d.dKlmmmmKlmmmm',
    '.....ddKlmmKlmmmm',
    '......d.ddKlmmmm.',
    '.........d.dKlmm.',
    '...........d.dm..',
]

BODY = [
    '.....wwwwwwl....',
    '...wwwwwwwwwll..',
    '..wwwwwwwwwwwll.',
    '.wwwwwwwwwwwwwll',
    '.wlwwwlwlwwwlwll',
    'wwwlllwwwlllwwlm',
    'wwwwwwwwwwwwwwlm',
    'wwwwlwwwlwwwwwlm',
    'wwwwwlllwwwwwllm',
    'wwwwwwwwwwwwwllm',
    'wlwwwlwlwwwlwlmm',
    'wwlllwwwlllwwlmm',
    '.wwwwwwwwwwwllm.',
    '.lwwwwwwwwwlllm.',
    '..llwwwwwwlllm..',
    '...lllllllmmm...',
    '.....mmmmmm.....',
]

HEAD = [
    '....r.rr....',
    '....rrrrR...',
    '...wwRRRwwl.',
    '..wwwwwwwwll',
    '.wrrwwwwrrRl',
    '.wwKwwwwKwwl',
    '.wwKwddwKwll',
    '.wwwwwdwwwll',
    '..wwwwwwwll.',
    '...wwwwwll..',
]

LEG = [
    '..wlm..',
    '..llm..',
    '..mmd..',
    '.mmmdd.',
    'mmdmddd',
    'd.d.d.d',
]

TAIL = [
    '.....mmm',
    '...mmdmm',
    '.mmddmmm',
    'dddd....',
]

im = canvas(40, 32)
wing = grid(WING, PAL)
stamp(im, wing, 0, 2)

# The right wing is the shaded side: its outer white goes one tone down.
right = wing.transpose(Image.FLIP_LEFT_RIGHT)
px = right.load()
for y in range(right.height):
    for x in range(9, right.width):
        if px[x, y] == rgba(PAL['w']):
            px[x, y] = rgba(PAL['l'])
stamp(im, right, 23, 2)

over(im, grid(TAIL, PAL), 5, 22)
leg = grid(LEG, PAL)
stamp(im, leg, 13, 24)
stamp(im, leg, 20, 24)
over(im, grid(BODY, PAL), 12, 9)
over(im, grid(HEAD, PAL), 14, 0)

im = outline(im)
save(im)
