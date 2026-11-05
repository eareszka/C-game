from pix import *

PAL = {
    'w': 'fcfcfc',  # hide, lit
    's': 'c6ccda',  # hide, mid
    'd': '848694',  # hide, shade
    'b': '94703d',  # antler, lit
    'B': '633e1b',  # antler, shade
    'p': 'fc74b4',  # blossom
    'h': '84a7e9',  # haze, deep
    'i': 'dcf0ff',  # haze, pale
}

im = canvas(32, 37)


def put(x, y, s):
    stamp(im, grid([s], PAL), x, y)


# blossoms on the main antler tips (mirrored about x = 18.5)
for cx in (13, 24):
    put(cx - 2, 0, '.p.p.')
    put(cx - 2, 1, 'ppppp')
    put(cx - 2, 2, '.pwp.')
    put(cx - 2, 3, 'ppppp')
    put(cx - 2, 4, '.pbp.')
# smaller blossoms on the side tines
for cx in (9, 28):
    put(cx, 6, 'p')
    put(cx - 1, 7, 'pwp')
    put(cx, 8, 'p')

# antlers
put(13, 5, 'b');  put(24, 5, 'b')
put(13, 6, 'b');  put(24, 6, 'b')
put(13, 7, 'bB'); put(23, 7, 'Bb')
put(10, 8, 'b');  put(14, 8, 'b');  put(23, 8, 'b');  put(27, 8, 'B')
put(11, 9, 'bbbbB');  put(22, 9, 'BbbbB')
put(15, 10, 'bB'); put(21, 10, 'Bb')
put(16, 11, 'bB'); put(20, 11, 'Bb')

# blue haze: two squiggles rising off the back
put(3, 3, '.iih')
put(2, 4, 'ih')
put(2, 5, 'hi')
put(3, 6, 'hih')
put(5, 7, 'ih')
put(4, 8, 'ih')
put(3, 9, 'hh')
put(7, 14, 'ih')
put(6, 15, 'ih')
put(6, 16, 'hi')
put(7, 17, 'hih')
put(9, 18, 'ih')
put(8, 19, 'ih')
put(7, 20, 'hh')

# neck, behind the head
put(14, 17, 'wK')
put(13, 18, 'wwsK')
put(13, 19, 'wwsK')
put(13, 20, 'wwwsK')
put(12, 21, 'wwwwss')

# body
put(5, 22, 'wwwwwwwwwwwwss')
put(4, 23, 'wwwwwKwwwwwKwwss')
put(4, 24, 'wwwwwwKwwwKwwwss')
put(4, 25, 'swwwwwKsssKwwsss')
put(5, 26, 'sssKKddddKKssd')
put(3, 21, 'w')
put(3, 22, 'ww')

# far legs
put(10, 27, 'ds'); put(12, 27, 'sd')
for y in range(28, 34):
    put(10, y, 'd'); put(13, y, 'd')
put(10, 34, 'bB'); put(12, 34, 'bB')

# near legs
put(5, 27, 'wws')
put(5, 28, 'ws')
put(5, 29, 'ws')
put(4, 30, 'ws')
put(4, 31, 'w')
put(4, 32, 'w')
put(4, 33, 'w')
put(3, 34, 'bB')
put(16, 27, 'ws')
for y in range(28, 34):
    put(17, y, 'w')
put(17, 30, 'ws')
put(17, 34, 'bB')

# ears
put(13, 13, 'ww');   put(23, 13, 'ss')
put(11, 14, 'wppw'); put(23, 14, 'sppd')
put(12, 15, 'ssK');  put(23, 15, 'Kds')

# head
put(16, 12, 'wwwwws')
put(15, 13, 'wwwwwwws')
put(15, 14, 'wwwwwwss')
put(15, 15, 'wwKwwKws')
put(15, 16, 'wwKwwKss')
put(16, 17, 'wwwwss')
put(17, 18, 'wwws')
put(17, 19, 'wKKs')
put(18, 20, 'ws')

im = outline(im)
save(im)
