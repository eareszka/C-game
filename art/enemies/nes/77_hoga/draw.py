from pix import *

PAL = {
    'a': 'e8e0c0',  # horn
    'b': 'b2966a',  # horn and muzzle shade
    's': 'd7a175',  # muzzle
    'm': '94703d',  # hide
    'd': '633e1b',  # hide shade
    'L': '84a7e9',  # fish light
    'B': '3e91cc',  # fish
    'D': '2850a0',  # fish shade
}

HALF = [
    "..a............",
    ".aa............",
    ".aa............",
    ".aab...........",
    ".aab...........",
    ".aaab..........",
    "..aab..........",
    "..aaab.........",
    "...aaab........",
    "....aaab..ddddd",
    ".....aabKddmddm",
    "......aabKmmdmm",
    ".......aaKmmmmm",
    "..mmmm..aKmmmmm",
    ".mmbbddKmmmmmmm",
    ".mbbbddKmmmmmmm",
    "..mddddKmbbbbmm",
    "......dmmmKKmmm",
    "......dmmmmmmmm",
    ".......dmmmmmmm",
    ".......dmmmmmmm",
    "......mKKKKKKKK",
    ".....ssssssssss",
    "....sssssssssss",
    "....sssssssbbss",
    "....sssssssssss",
    "....sssssssssss",
    "....bssssssssss",
    ".....bssssKKKKK",
    ".....bsssssssss",
    "......bbsssssss",
    ".......bbbbbbbb",
]
assert all(len(r) == 15 for r in HALF)


def shade_right(row):
    """Light is upper left: horns get their shade outside, and the right rim goes dark."""
    left, right = list(row[:15]), list(row[15:])
    i = 0
    while i < len(right):
        if right[i] in 'ab':
            j = i
            while j < len(right) and right[j] in 'ab':
                j += 1
            right[i:j] = sorted(right[i:j])
            i = j
        else:
            i += 1
    done = 0
    for i in range(len(right) - 1, -1, -1):
        if right[i] == '.':
            continue
        if done < 2:
            right[i] = {'m': 'd', 's': 'b'}.get(right[i], right[i])
        done += 1
    return ''.join(left + right)


head = grid([shade_right(r) for r in mirror(HALF)], PAL)

BODY = [
    "...........D................",
    "...........DD...............",
    "...........BDD..............",
    "............BDD.............",
    "............BBDD............",
    "D............BBDD...........",
    "DD...........BKBDD..........",
    ".BD..........BKBBDD.........",
    ".BBD..........BKBBDD........",
    "..BBD.........KKKKKKKKK.....",
    "..BBDD.....LLLLLLLLLLLLLLL..",
    "...BBD...LLLLBBBBBBBBBBBBBBB",
    "...BBDD.LLBBBBBBBBBBBBBBBBBB",
    "....BBDDLBBBBDBBBBDBBBBDBBBB",
    "....BBDKBBBBDBBBBDBBBBDBBBBB",
    ".....BDKBBBBDBBBBDBBBBDBBBBB",
    ".....DDKBBBBBDBBBBDBBBBDBBBB",
    "......DKBBBBDDDDDDDDDDDDDDDD",
    ".....DDKDDDKLLLLLLLKLLLLKLLL",
    ".....BDKLLLLLLLLLLLKLLLLKLLL",
    "....BBD.DDDDDDDDDDDDDDDDDDDD",
    "....BDD..DDDKDDDDKDDDDKDDDDD",
    "...BBD....DDKDDDDKDDDDKDDDDD",
    "...BD......DDDDDDDDDDDDDDDDD",
    "..BBD.......DDDDDDDDDDDDDDD.",
    "..BD..........DDDDDDDDDDDD..",
    ".BD...........KKKKKKKK......",
    ".D............BBBDDD........",
    "D............BBDD...........",
    ".............BDD............",
    "............BD..............",
    "............D...............",
]

im = canvas(49, 37)
stamp(im, grid(BODY, PAL), 0, 3)

HX, HY = 20, 1
ring = outline(head)
cover = im.copy().load()
rp = ring.load()
for y in range(ring.height):
    for x in range(ring.width):
        px, py = HX - 1 + x, HY - 1 + y
        if 0 <= px < im.width and 0 <= py < im.height and rp[x, y][3] and cover[px, py][3]:
            dot(im, px, py, '000000')
stamp(im, head, HX, HY)

im = strip_outline(im)
im = outline(im)
save(im)
