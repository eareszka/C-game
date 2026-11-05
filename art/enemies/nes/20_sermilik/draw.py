from pix import *

PAL = {
    'W': 'fcfcfc',  # ice, lit
    'I': 'dcf0ff',  # ice, mid
    'B': '84a7e9',  # ice, shade
    'L': 'c6ccda',  # fur, lit
    'M': '9797aa',  # fur, mid
    'D': '595965',  # fur, shade
}
N = 31


def p(s, fill='M'):
    return s.ljust(N, fill)


BODY = [
    p('....................W.......W', '.'),
    p('...................WIB.....WIB', '.'),
    p('..............W....WWIB...WWIIB', '.'),
    p('.............WIB.WWWWWWWWWWWWWW', 'W'),
    '.........W..WWIIBWWWWWWWWWWWWWW',
    '........WIBWWWWIIBWWWIIIIIIIIII',
    p('.......WWWWWIIIBB', 'B'),
    p('......IWKKWWIIBB', 'B'),
    p('.....IWWIIKWIIBB', 'B'),
    p('....IWWWWWWIIIBB', 'B'),
    p('....WWWWWWIIIBBB', 'B'),
    p('...IWWWWIIIBBBBB', 'B'),
    p('...IWWIIIIBBKKKK'),
    p('..IWIIIBBBBKKLLL'),
    p('..WIIIBBBKKLLLLL'),
    p('..IIBBKKKLLLLLLL'),
    p('..IBKKLLLLLLLLLL'),
    p('.IIBKLLLLLLLLLLL'),
    p('.IBBKLLLLLLLLLLM'),
    p('..BKLLLLLKKLLLMM'),
    p('.LKLLLLLLLLKLMMM'),
    p('.LLLLLLLLLLLMMMM'),
    p('LLLLLKKLLLLLMMMM'),
    p('LLLLLLLKLLLLMMMM'),
    p('.LLLLLLLLLLLMMMM'),
    p('LLLIWWWIILLKKMMM'),
    p('LLLIWIIIBBLLMMMK'),
    p('.LLLIIBBLLLLMMKM'),
    p('MLLLLBLLLLLLMKMM'),
    p('MLLLLLLLLLLMMMKM'),
    'MLKKLLLLLLMMMMMK' + 'MMMMDDDDDDDDDDD',
    'MLLLKLLLLKMMMMMK' + 'MMMMMMDDDDMMMDD',
    '.LLLLLLLKKMMMMMK' + 'DMMMMMMMMMMMMMM',
    'MLLLLLLLLMMMMMMK' + 'DMMMMMMDMMMMDMM',
    'MMLLLLLLMMMMMMDK' + 'DDMMMMDDDMMDDDM',
    '.MMLLLKLLMMMMDDK' + 'DDDMDDDDDDDDDDD',
    '.MMLLLKLLMMMMDDK' + 'DDDDDDDDDDDDDDD',
    '.MMLLLKLMMMMMDDKKKKKKKKKKDDDDDD',
    '...LLLKLMMMMMDDD.LLMMMMMD.DD.DD',
    '...LLLLKLMMMMDDD.LLMMMMMD......',
    '...LLLLKLMMMMDDD.LLMMMMMD......',
    '..LLLLLKLMMMDDDD.LMMMMMMD......',
    '.IIIMLLLLMMIWIDD.LMMKKMDD......',
    'IWWWIILLMIIWWIIB.LMMMKMDD......',
    'WWWIWWIIIIWWIIBB.LMMMMMDD......',
    'IWIIWWWIIWWIIBBB.LMMMMMDD......',
    'IIIIBIIIIIIBBBBB.MMMMMDDD......',
    'IIIBIIIBIIIBIIIB.IIIIIBBD......',
    'IKIIKIIKIIKIIKIB.IKIIKIBB......',
    '.W.W..W..W..W.....W..W.W.......',
]
assert all(len(r) == N for r in BODY)

HEAD = [
    '...KKK...........',
    '..KWLLK..........',
    '..KLDLK....KKKKKK',
    '..KLDLKKKKKWWWWWW',
    '..KLLLWWWWWWWWWWW',
    '...KLWWWWWWWWWWWW',
    '...KWWWWWWWWWWWWW',
    '...KWWWWIIIWWWWWW',
    '...KWWIIIBIIWWIII',
    '..KLIIBLLIBLLLIBW',
    '..KLLLLLLLLLLLLLL',
    '..KLLLLLMMMLLLLLL',
    '.KLLLLLLLDDDLLLLL',
    '.KLLLLLLLLKKLLLLL',
    '.KLLLLLLLLLLLLIII',
    'KLLLLLLLLLLLIIIII',
    'KMLLLLLLLLLIIIKKK',
    '.KMLLLLLLLLIIIKKK',
    'KMMLLLLLLLLIIIIKK',
    '.KMMLLLLLLLIIIIIK',
    '..KMMLLLLLIIIIIIK',
    '...KMMLLLLIIKKKKK',
    '....KMMLLLIKIIIII',
    '.....KMMMMIIBIBBB',
    '......KKMMMBBBBBB',
    '........KKKKKKKKK',
]
assert all(len(r) == 17 for r in HEAD)

SHADE = {PAL['W']: PAL['I'], PAL['L']: PAL['M'], PAL['M']: PAL['D']}


def shade(part, x0):
    """Light from the upper left: the part's right side drops one tone."""
    px = part.load()
    for y in range(part.height):
        for x in range(x0, part.width):
            c = px[x, y]
            if not c[3]:
                continue
            h = '%02x%02x%02x' % c[:3]
            if h in SHADE:
                px[x, y] = rgba(SHADE[h])


body = grid(mirror(BODY), PAL)
shade(body, 50)
head = grid(mirror(HEAD), PAL)
shade(head, 26)

im = canvas(61, 50)
stamp(im, body, 0, 0)
stamp(im, head, 14, 4)

im = outline(im)
save(im)
