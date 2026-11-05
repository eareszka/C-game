from pix import *

PAL = {
    'W': 'fcfcfc',  # white-hot blade
    'Y': 'fae488',  # blade shade / hot belly
    'A': 'f0bc3c',  # blade deep shade
    'O': 'fc9838',  # body light
    'R': 'b70000',  # body mid
    'D': '7c0a1b',  # body shade
}


def at(x, s):
    return ' ' * x + s


def c(s):
    return at(17 - len(s) // 2, s)


rows = [
    # blade
    c('W'),
    c('W'),
    c('WWY'),
    c('WWY'),
    c('WWWYY'),
    c('WWWYA'),
    c('YWWWYAA'),
    c('YWWWYAA'),
    # hood
    c('OKYWWYAKR'),
    c('OOOKYWYAKRR'),
    c('OYOOOKYKOORRD'),
    c('OYYOOOOOOOORRDD'),
    c('OYOKKOOOOOKKORD'),
    c('ROOOOOOOOOOOORD'),
    c('RROOOOKOOORRD'),
    c('RRROOKOORRD'),
    c('DRROKORRD'),
    c('RKKKKKD'),
    # neck with belly plates
    c('ROYYORD'),
    c('ROYYORD'),
    c('ROKKKRD'),
    c('ROYYORD'),
    c('ROYYORD'),
    c('ROKKKRD'),
    c('ROYYORD'),
    c('ROYYORD'),
    c('RROYYORRD'),
    # top coil
    at(11, 'OOOROKKKKORRD'),
    at(10, 'OYYOOKOOOORKRRD'),
    at(10, 'ORRDKRRRRDKRDDD'),
    at(11, 'D' + 'K' * 11 + 'D'),
    # middle coil
    at(6, 'OOYYOOOORKOOOOORRKORRRD'),
    at(5, 'OYOOORRRRKOOORRRRKOORRRDD'),
    at(5, 'ORRRRRRRKOORRRRRKOORRRDDD'),
    at(5, 'RRRDDDDKRRDDDDDKRRDDDDDDD'),
    at(6, 'D' + 'K' * 21 + 'D') + at(8, 'Y'),
    # base coil and tail
    at(2, 'OYYYOOORKOOOOORRKOOOOORRKORRRRD') + at(3, 'OY'),
    at(1, 'OYOORRRRKOOORRRRKOOORRRRKOORRRDDD') + at(1, 'RO'),
    at(1, 'ORRRRRRKOORRRRRKOORRRRRKOORRRDDDD') + 'RR',
    at(1, 'OYYYYYYKOYYYYYKOYYYYOOKOOOORRRDDD'),
    at(2, 'RRRRRRDDDDDDDDDDDDDDDDDDDDDDDDD'),
]

im = grid(rows, PAL)
im = outline(im)
save(im)
