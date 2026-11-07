from pix import *
# Kurrea, idle pose 1.
# Parts and where they attach:
# - coil: one round ring lying on the ground, white belly band along its bottom,
#   black fold line where the belly band meets the side,
#   hole in the middle showing the white inner wall of the far side
# - neck: rises out of the coil's front-right end, curves up and left, black line
#   on its left where it passes in front of the coil (coil top down to the hole)
# - belly stripe: plain white down the neck front, flowing into the coil's belly band
# - head: wedge facing right on top of the neck, jaw closed off by the mouth line
# - eye: 2 px yellow mark on the head
# - crystals (grow out of the coil's back, bases sit on the coil top, left side):
#   mint (tall, back), pink back (low, strong left lean), pink front (big),
#   sky blue (lean right), gold (small, leans right, in front)

V = '664b95'
VS = '3b2a58'
W = 'fcfcfc'
PAL = {'p': 'fc74b4', 'm': 'a8f0bc', 'b': '84a7e9', 'g': 'f0bc3c'}

im = canvas(80, 82)

# coil
oval(im, 2, 47, 67, 31, W)
oval(im, 2, 46, 67, 30, '000000')
oval(im, 2, 46, 67, 29, VS)
oval(im, 2, 45, 65, 27, V)
# hole with the white inner wall at its top
oval(im, 18, 55, 35, 11, W)
ImageDraw.Draw(im).ellipse((18, 57, 52, 66), fill=CLEAR)

# crystals, back to front
mint = [
    "....KK.....",
    "...KmmK....",
    "..KmmKmK...",
    ".KmmmKmmK..",
] + ["KmmmmKmmmK."] * 9 + [".KmmmmKmmmK"] * 17 + [".KKKKKKKKKK"]
stamp(im, grid(mint, PAL), 17, 17)

pink_back = [
    "...KK..........",
    "..KppK.........",
    ".KppKpK........",
    "KpppKppK.......",
    "KpppKppK.......",
    ".KpppKppK......",
    ".KpppKppK......",
    "..KpppKppK.....",
    "..KpppKppK.....",
    "...KpppKppK....",
    "...KpppKppK....",
    "....KpppKppK...",
    "....KpppKppK...",
    ".....KpppKppK..",
    ".....KpppKppK..",
    "......KpppKppK.",
    "......KpppKppK.",
    ".......KpppKppK",
    ".......KKKKKKKK",
]
stamp(im, grid(pink_back, PAL), 0, 33)

pink_front = [
    "....KK..........",
    "...KppK.........",
    "..KppKpK........",
    ".KpppKppK.......",
] + ["KppppKpppK......"] * 4 + [".KppppKpppK....."] * 3 + ["..KppppKpppK...."] * 3 \
  + ["...KppppKpppK..."] * 3 + ["....KppppKpppK.."] * 3 + [".....KppppKpppK."] * 3 \
  + [".....KKKKKKKKKK."]
stamp(im, grid(pink_front, PAL), 8, 26)

blue = [
    ".......KK...",
    "......KbbK..",
    ".....KbbKbK.",
] + ["....KbbbKbbK"] * 4 + ["...KbbbKbbK."] * 4 + ["..KbbbKbbK.."] * 4 \
  + [".KbbbKbbK..."] * 4 + [".KKKKKKKK..."]
stamp(im, grid(blue, PAL), 26, 29)

gold = [
    "......KK...",
    ".....KggK..",
    "....KgggKgK",
    "....KgggKgK",
    "...KgggKgK.",
    "...KgggKgK.",
    "..KgggKgK..",
    "..KgggKgK..",
    ".KgggKgK...",
    ".KgggKgK...",
    "KgggKgK....",
    "KKKKKKK....",
]
stamp(im, grid(gold, PAL), 33, 40)

# neck
poly(im, [(44, 10), (42, 22), (42, 30), (45, 38), (50, 45), (53, 52), (54, 60), (55, 66),
          (66, 66), (69, 60), (68, 52), (64, 44), (58, 37), (55, 30), (56, 22), (57, 13)], V)
poly(im, [(57, 13), (56, 22), (55, 30), (58, 37), (64, 44), (68, 52), (69, 60), (66, 66),
          (64, 66), (66, 60), (65, 52), (61, 45), (56, 38), (53, 30), (54, 22), (55, 13)], VS)
poly(im, [(47, 14), (46, 22), (47, 30), (50, 37), (54, 44), (57, 52), (58, 60), (57, 69),
          (62, 69), (63, 60), (62, 52), (59, 44), (55, 37), (52, 30), (51, 22), (53, 13)], W)
# line where the neck passes in front of the coil
rect(im, 50, 46, 1, 2, '000000')
rect(im, 51, 48, 1, 2, '000000')
rect(im, 52, 50, 1, 3, '000000')
rect(im, 53, 53, 1, 9, '000000')

# head
poly(im, [(45, 3), (48, 1), (62, 1), (67, 3), (72, 7), (72, 9), (68, 11), (58, 13),
          (52, 14), (45, 12), (43, 8)], V)
rect(im, 59, 12, 5, 1, VS)
rect(im, 62, 11, 7, 1, VS)
rect(im, 68, 10, 3, 1, VS)
# mouth line, closing off the jaw
rect(im, 58, 11, 4, 1, '000000')
rect(im, 62, 10, 6, 1, '000000')
rect(im, 68, 9, 5, 1, '000000')
rect(im, 58, 12, 1, 2, '000000')
# eye
rect(im, 60, 5, 2, 1, 'f0bc3c')

im = strip_outline(im)
im = outline(im)
save(im)
