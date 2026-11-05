from pix import *

PAL = {
    'a': 'cebe82',  # tan light
    'b': 'b29e5c',  # tan mid
    'c': '785830',  # tan dark / rider lit
    'd': '583518',  # rider dark, hat bands
    'o': 'd89830',  # hat, bees
    'g': '4fa667',  # snake light
    'h': '2c6c44',  # snake dark
    'r': 'b6433d',  # rider eyes, scorpion spurs
}


def part(im, rows, x, y):
    """Stamp a part, with a black line wherever it touches what is already drawn."""
    g = grid(rows, PAL)
    src, dst = g.load(), im.load()
    for yy in range(g.height):
        for xx in range(g.width):
            if not src[xx, yy][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = xx + a, yy + b
                if 0 <= nx < g.width and 0 <= ny < g.height and src[nx, ny][3]:
                    continue
                px, py = x + nx, y + ny
                if 0 <= px < im.width and 0 <= py < im.height and dst[px, py][3]:
                    dst[px, py] = BLACK
    stamp(im, g, x, y)


im = canvas(44, 44)

# tail, far left, with its tuft
part(im, [
    '.aa...........',
    'aabb..........',
    '.bcccc........',
    '.....cccc.....',
    '.........ccccc',
], 1, 28)

# snake walking stick
part(im, [
    '.ggg....',
    'gggghh..',
    'gKgggh..',
    '.gghh...',
    '..gh....',
    '..gh....',
    '.gh.....',
    '.hh.....',
    '.gh.....',
    '.gh.....',
    '..gh....',
    '..hh....',
    '..gh....',
    '...gh...',
    '...gh...',
    '....hh..',
    '....gh..',
    '....gh..',
    '.....gh.',
    '.....hh.',
    '.....gh.',
    '......gh',
    '......gh',
    '.....ghh',
    '....ghh.',
    '...ghh..',
    '..gh....',
], 32, 7)

# hind feet
part(im, [
    '..aaab..',
    '.aaabbb.',
    'aaaabbbc',
], 8, 32)
part(im, [
    '..aabb..',
    '.aabbbc.',
    'aaabbbcc',
], 19, 32)

# body
part(im, [
    '....aaaaaab....',
    '...aaaaaaabb...',
    '..aaKaaaaaKbb..',
    '..aabKaaaKbbb..',
    '..aaaaaaaabbb..',
    '.aaKaaaaaaKbbb.',
    '.aKaaaaaaabKbb.',
    '.aKaaaaaabbKbc.',
    '.aaKKaaabKKbcc.',
    '..aaabbbbbbcc..',
], 10, 24)

# head
part(im, [
    '...aaaaaaaaaab...',
    '..aaaaaaaaaaabb..',
    '.aaaaaaaaaaaaabb.',
    'aaaaaaaaaaaaaabbb',
    'aaaaaaaaaaaaaabbb',
    'aaaaaKaaaaaKabbbb',
    'aaaaaKaaaaaKabbbb',
    'aaabaaaKcKaaabbbc',
    '.aaabbaaKaabbbbc.',
    '...bbbbbbbbbccc..',
], 9, 15)

# ears
part(im, [
    '.aab......',
    'aaabb.....',
    'aacbb.....',
    '.aaccb....',
    '.aaccb....',
    '..aaccb...',
    '..aaccb...',
    '...aaccb..',
    '...aaccb..',
    '....aaccb.',
    '....aaccb.',
], 6, 6)
part(im, [
    '......abb.',
    '.....aabbb',
    '.....accbb',
    '....accbb.',
    '....accbb.',
    '...accbb..',
    '...accbb..',
    '..accbb...',
    '..accbb...',
    '.accbb....',
    '.accbb....',
], 20, 6)

# rider
part(im, [
    '..cccccc..',
    '.cccccccd.',
    '.crrccrrd.',
    '.cccccccd.',
    '..cKKKcd..',
    '.ccccccdd.',
    'cdccccdddc',
    '..ccccdd..',
    '.cd....dd.',
    'rrr....rrr',
    'r........r',
], 13, 8)

# rider's arm out to the snake
part(im, [
    '.....ccccc',
    'cccccc.ddd',
    'ddd.......',
], 23, 12)

# beehive hat
part(im, [
    '...oo...',
    '..oooc..',
    '..dddd..',
    '.oooooc.',
    '.dddddd.',
    'oooooooc',
], 14, 3)

# bees
part(im, ['oa'], 9, 3)
part(im, ['oa'], 12, 0)
part(im, ['oa'], 24, 1)

im = outline(im)
save(im)
