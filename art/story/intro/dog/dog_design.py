"""The intro's dog: a small dark brown French bulldog, drawn by hand at game
size from the PixelLab pick (C_frenchie-c.png) in the boy's style: black
outline, flat colour, 3 colours plus black. python art/story/intro/dog/dog_design.py"""
from PIL import Image
import os

PAL = {'.': (0, 0, 0, 0), 'A': (0, 0, 0, 255),
       'B': (92, 56, 30, 255),     # coat, dark brown
       'C': (150, 104, 64, 255),    # muzzle, chest, inner ear
       'D': (182, 67, 61, 255)}    # tongue, the boy's red

# 4 views. West is east mirrored. Front and back 10 x 11, the side 12 x 11;
# the boy is 16 x 20 with 15 px drawn.
SOUTH = [
    ".A......A.",
    "ABA....ABA",
    "ACBAAAABCA",
    "ABBBBBBBBA",
    "ABABBBBABA",
    "ABBCCCCBBA",
    ".ACCAACCA.",
    ".AACDDCAA.",
    ".ABACCABA.",
    ".ABA..ABA.",
    ".AA....AA.",
]
NORTH = [
    ".A......A.",
    "ABA....ABA",
    "ABBAAAABBA",
    "ABBBBBBBBA",
    "ABBBBBBBBA",
    ".ABBBBBBA.",
    ".ABBBBBBA.",
    "ABBBBBBBBA",
    "ABBBAABBBA",
    ".ABA..ABA.",
    ".AA....AA.",
]
EAST = [
    ".......A....",
    "......ACA...",
    "......ACBA..",
    ".....ABBBBA.",
    "A...ABBABBBA",
    "AAAABBBBBCCA",
    "ABBBBBBBCDA.",
    "ABBBBBBBCA..",
    ".ABBBBBBBA..",
    ".ABA..ABA...",
    ".AA...AA....",
]

def img(rows):
    im = Image.new('RGBA', (len(rows[0]), len(rows)))
    for y, r in enumerate(rows):
        assert len(r) == len(rows[0]), (y, r)
        for x, ch in enumerate(r): im.putpixel((x, y), PAL[ch])
    return im

def west(rows): return [r[::-1] for r in rows]

def swap(rows, at, new):
    """rows with rows[at:] replaced by new (a pose differs only at the bottom or one line)."""
    out = list(rows); out[at:at + len(new)] = new
    return out

# The walk bounces like the boy's (player_small.png: on each stride he drops
# 1 px, up again between). The side walk is PixelLab's (pixellab/, one
# generation, 2026-11-08): low on a stride, up 1 px with the legs gathered in
# between. Its frames came back with a doubled ear and broken mouth once
# snapped to these 4 colours, so each is cleaned by hand to the confirmed head
# and body, keeping PixelLab's legs and timing. Front and back: the strides
# squash 1 px (the head's top row drops out), the passes stand full height.
WALK_MS, IDLE_MS = 200, 420

def squash(rows):
    return rows[:3] + rows[4:]

def up(rows, legs):
    """The side pose risen 1 px: body rows 0..8 kept, the legs gathered."""
    return rows[:9] + legs

SIDE_WALK = [
    swap(EAST, 9, ["ABA....ABA..", "AA......AA.."]),                          # stride, low
    up(EAST, [".ABBAABBA...", "..AA..ABA...", "......AA...."]),               # up, front leg reaching
    swap(EAST, 9, ["..ABAABA....", "..AA...AA..."]),                          # other stride, low
    up(EAST, [".ABBAABBA...", "..ABA..AA...", "..AA........"]),               # up, hind leg reaching
]
FRONT_A = swap(SOUTH, 9, [".ABA..AAA.", ".AA......."])
FRONT_B = swap(SOUTH, 9, [".AAA..ABA.", ".......AA."])
BACK_A  = swap(NORTH, 9, [".ABA..AAA.", ".AA......."])
BACK_B  = swap(NORTH, 9, [".AAA..ABA.", ".......AA."])
VIEWS = {   # stand, walk (4 steps, WALK_MS each), idle B (swaps with stand, IDLE_MS)
    'south': (SOUTH, [squash(FRONT_A), SOUTH, squash(FRONT_B), SOUTH], swap(SOUTH, 7, [".AACDDCAA.", ".ABADDABA."])),
    'north': (NORTH, [squash(BACK_A), NORTH, squash(BACK_B), NORTH],   swap(NORTH, 7, ["ABBBCCBBBA"])),
    'east':  (EAST,  SIDE_WALK,                                         swap(EAST, 6, ["ABBBBBBBCAD.", "ABBBBBBBCAD."])),
}
# East mirrored: the walk is a list of poses, stand and idle are one pose
# each (a list of rows), so tell them apart by what the list holds.
VIEWS['west'] = tuple([west(v) for v in x] if isinstance(x[0], list) else west(x) for x in VIEWS['east'])
ORDER = ['south', 'north', 'east', 'west']
CELL = 12          # sheet cell, each pose bottom-aligned so the feet stay put

# Asleep in its bed, the intro's opening: lying face on, head down between
# its paws, eyes shut (two short lines), ears still up. Breathing out, the
# head sinks a pixel. Sheet columns 6-7, the same in every row.
SLEEP_A = [
    "..A......A..",
    ".ABA....ABA.",
    ".ACBAAAABCA.",
    "AABBBBBBBBAA",
    "ABAABBBBAABA",
    "ABBBCCCCBBBA",
    "ABBCCAACCBBA",
    ".AAAAAAAAAA.",
]
SLEEP_B = ["............"] + SLEEP_A[:3] + SLEEP_A[4:]

def cell(rows):
    im, c = img(rows), Image.new('RGBA', (CELL, CELL))
    assert im.height <= CELL and im.width <= CELL
    c.alpha_composite(im, ((CELL - im.width) // 2, CELL - im.height))
    return c

def tint(im):      # the intro's night, for a second look
    out = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            out.putpixel((x, y), (min(255, r * 92 // 255 + 6), min(255, g * 112 // 255 + 10), min(255, b * 178 // 255 + 26), a))
    return out

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    # The sheet: a row per view (south, north, east, west), a column per pose.
    # Columns: stand, walk 1-4, idle B, asleep A, asleep B.
    sheet = Image.new('RGBA', (CELL * 8, CELL * 4))
    for j, v in enumerate(ORDER):
        stand, walk, idle = VIEWS[v]
        for i, rows in enumerate([stand] + walk + [idle, SLEEP_A, SLEEP_B]): sheet.alpha_composite(cell(rows), (CELL * i, CELL * j))
    sheet.save(os.path.join(here, 'dog_sheet.png'))
    sheet.save(os.path.join(here, '../../../../assets/story/dog.png'))   # what the game loads
    # Preview: walk then idle, each view, day above night, the boy for scale.
    boy = Image.open(os.path.join(here, '../../../../assets/player_small.png')).convert('RGBA').crop((0, 0, 16, 20))
    frames, durs = [], []
    seq = [(lambda v, k=k: VIEWS[v][1][k], WALK_MS) for k in range(4)] * 4         + [(lambda v: VIEWS[v][2], IDLE_MS), (lambda v: VIEWS[v][0], IDLE_MS)] * 3
    for pose, ms in seq:
        bd = Image.new('RGBA', (24 + 16 * 4, 24), (120, 140, 110, 255))
        bd.alpha_composite(boy, (4, 2))
        for j, v in enumerate(ORDER): bd.alpha_composite(cell(pose(v)), (26 + 16 * j, 10))
        f = Image.new('RGBA', (bd.width, 48)); f.paste(bd, (0, 0)); f.paste(tint(bd), (0, 24))
        frames.append(f.resize((f.width * 8, f.height * 8), Image.NEAREST).convert('P')); durs.append(ms)
    frames[0].save(os.path.join(here, 'dog_anim.gif'), save_all=True, append_images=frames[1:], duration=durs, loop=0)
