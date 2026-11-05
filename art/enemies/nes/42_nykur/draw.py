from pix import *

PAL = {
    'a': 'bcbeca',  # lit hide
    'b': '848694',  # hide
    'c': '474751',  # shaded hide
    'g': '2c6c44',  # lit mane
    'h': '235436',  # mane
    'j': '163623',  # deep mane
    'd': '785830',  # hoof
    'e': 'b29e5c',  # hoof edge
}

ROWS = [
    #0         1         2         3
    #0123456789012345678901234567890123456789
    '                      a      a',
    '                     ab     ab',
    '                     acb    acb',
    '                     acb    acc',
    '                     abbg   bbc',
    '                    gabbbgghbbbc',
    '                   gghaabgghhbbbc',
    '                  gghjaaagghjbbbc',
    '                  ghjjKaaaghjabbc',
    '                 gghjKaaaaahabbbc',
    '                 ghjjKaKKaaaabKKc',
    '                 ghjjKaaaaaaabbbc',
    '                 ghhjjKaaaaabbbc',
    '                gghhjjKaaaabbbbc',
    '               gghhjjKaaaaabbbc',
    '               g ghjjKaaaaabbbc',
    '                gghKbKaaaabbbbc',
    '               ghhKabKaaaabbbc',
    '               ghjKaaKaaabbbbc',
    '              gghKaabKabbbbcc',
    '             gghhKaabKbbbbbcc',
    '             g ghKaabKcKccKcc',
    '              ghjKabbKccccccc',
    '             gghKaaabbKccccc',
    '             ghhKaabaabKKKKb',
    '             ghKaabbaabbbbbc',
    '       aaaa  ghKaaaaaabbbbbbc',
    '     aaaaaaaKhKaabaaabbbbbbbc',
    '    aaabbaaaaKgKaabbaaabbbbbbc',
    '  gaaaabbaaabaKhKaaaaabbabbbbc',
    ' gjaaaaaaaabbaaKgKaaabaaabbbbcc',
    ' ghaabaaaaabbaaaKKaabbaaaabbbbcc',
    ' gKaabbaaaaaaabaaKaaaaaabaabbbbc',
    'ghKaaaaaabaaabbaabKaabaaabbabbbc',
    'gKhaaabaabbaaaKaaabKaaaaaabbabbc',
    'gjKaabbaaaaaabKaabbKaabbaaabbbcc',
    'ghKaaaaaaaaabbaKaabbKaaaaaabbbcc',
    'gKjbaaabaaaaaaaKaabbKaaaaabbbbcK',
    'gjKbbabbaaaabaaKabbcKbbaabbbbcKc',
    ' jhbbbbbbbbbbbbKbbcccKbbbbbbcKcc',
    ' gjbbbcccccccccKcccccKKbbbbcKccb',
    ' gKbbbKccKKKKKKKKKKKcbbKccKbbcbbc',
    ' g bbbbKbcc   ccb    abbcKbabbbbc',
    ' g abbbbKcc   cbc    abbc  abbbbc',
    ' j  abbbcc    cbc    abbc   abbc',
    '    abbcc     cbc    abbc   abbc',
    '    abbc      abc    abbc   abbc',
    '    abc       abc     abc    abc',
    '    abc       abc     abc    abc',
    '    aKKc      aKKc    aKKc   aKKc',
    '    abbc      abbc    abbc   abbc',
    '    abc       abc     abc    abc',
    '    abc       abc     abc    abc',
    '    abc       abc     abc    abc',
    '    abc       abc     abc    abc',
    '    abc       abc     abc    abc',
    '   eKKK      eKKK    eKKK   eKKK',
    '  edddd     edddd   edddd  edddd',
    ' dddddd    dddddd  dddddd dddddd',
]

src = grid(ROWS, PAL)
im = canvas(src.width + 2, src.height + 2)
stamp(im, src, 1, 1)
im = outline(im)
save(im)
