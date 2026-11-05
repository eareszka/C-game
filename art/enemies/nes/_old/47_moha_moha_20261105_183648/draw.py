from pix import *
# Moha-Moha, side on, facing right. Large parts, back to front, and where each attaches:
#   tail       - comes out from behind the shell dome, runs down and left
#   top fin    - sits on the tail's top edge, swept back
#   tail fin   - forked, on the tail's tip, black line between
#   back leg   - from under the shell's rear, in front of the tail, foot to lower left
#   shell dome - the plain middle of the body
#   shell rim  - pale band under the dome, black line between
#   neck       - from behind the dome's right side, up to the head
#   front leg  - shoulder under the neck, in front of the shell, foot to lower left
#   upper jaw with head - on top of the neck, left of the open mouth
#   lower jaw  - hinged on the neck, right of the open mouth
# Extras: teeth on both jaws, claws on both feet, head spots, eye, three shadow marks
# on the tail and on each leg, each mark a different shape.

PAL = {
    'd': '595965', 'D': '474751',   # shell
    'g': '4fa667', 'G': '2c6c44',   # neck, head, legs
    't': '9797aa', 's': '595965',   # tail, rim
    'b': '8d6b4f', 'B': '463422',   # fins, head spots
    'w': 'e8e0c0',                  # teeth, claws
}

im = canvas(68, 40)

tail = grid([
    '..........................t',
    '........................tttt',
    '......................tttttt',
    '....................tttttttt',
    '..................tttttttttt',
    '................tttttssttttt',
    '..............tttttssttttttt',
    '...........tttsttttttttttttt',
    '........tttttssttttttttttttt',
    '.....ttttttttttttsssssssssss',
    '..ttttttttttttssss',
    'ttssttttttssss',
    'ttttttssss',
    'ssssss',
], PAL)
stamp(im, tail, 7, 22)

top_fin = grid([
    'bb',
    '.bbbb',
    '.bbbbBK',
    '.bbKKK',
    '.KK',
], PAL)
stamp(im, top_fin, 12, 27)

tail_fin = grid([
    '....bb',
    '..bbbb',
    'bbbbbbK',
    '.bbbbbK',
    '...bbBK',
    '...bbB',
    '..bbbB',
    '.bbbB',
    'bbbB',
], PAL)
stamp(im, tail_fin, 0, 31)

back_leg = grid([
    '.......KKK',
    '......KggG',
    '.....KgggG',
    '....KgGGgG',
    '...KgggGgG',
    '....gGgggG',
    '.....ggGGgG',
    '.....ggggggG',
    '..ggggggggGG',
    'wGGGGGGGGGG',
    '..ww..w',
], PAL)
stamp(im, back_leg, 22, 27)

dome = grid([
    '........dddddddddD',
    '......ddddddddddddDD',
    '....dddddddddddddddDDD',
    '...dddddddddddddddddDDD',
    '.KdddddddddddddddddddDDD',
    '.KdddddddddddddddddddDDD',
    'KdddddddddddddddddddddDDD',
    'KdddddddddddddddddddddDDD',
    'KdddddddddddddddDDDDDDDDD',
    'KdddddddddddddDDDDDDDDDDD',
    'KdddddddddDDDDDDDDDDDDDDD',
    'KddddDDDDDDDDDDDDDDDDDDDD',
    'KKKKKKKKKKKKKKKKKKKKKKKKK',
], PAL)
stamp(im, dome, 32, 19)

rim = grid([
    'tttttttttttttttttttttttt',
    '.tttttttttttttssssssssss',
    '...sssssssssss',
], PAL)
stamp(im, rim, 33, 32)

neck = grid([
    '....gggggGG',
    '....gggggGG',
    '....gggggGG',
    '....gggggGG',
    '...ggggggGG',
    '...ggggggGG',
    '..gggggggGG',
    '.ggggggggGG',
    '.gggggggGG',
    'ggggggggGG',
    'KggggggGG',
    'KggggggGG',
    '.KggggGG',
], PAL)
stamp(im, neck, 56, 13)

front_leg = grid([
    '........KKKKKKKKKKK',
    '.......KgggggggggGG',
    '......KgggggggggGG',
    '.....KgggGGggGggGG',
    '.....KggggGggGgGG',
    '.....KggggggggGG',
    '.....KgggggggGG',
    '.....KgggGggGG',
    '..KKKgggggGG',
    '..ggggggggGG',
    'wGGGGGGGGGGG',
    '...w.ww',
], PAL)
stamp(im, front_leg, 45, 26)

head = grid([
    '..ggg.......',
    '.ggggw....gG',
    'ggggg....wgG',
    'gKKggww...gG',
    'ggggg...wggG',
    'ggggggw..ggG',
    'gbgggg.wgggG',
    'ggbbggg.gggG',
    'gbggggg.gggG',
    '.ggbgggKgggG',
    '..ggggggKggG',
    '....GGGGGKgG',
    '....KKKKKKK',
], PAL)
stamp(im, head, 56, 0)

im = outline(im)
save(im)
