from pix import *

PAL = {
    'a': 'e8e0c0',  # knob light
    'b': 'cebe82',  # knob mid
    'c': 'b29e5c',  # knob shade
    'y': 'f0bc3c',  # beak light
    'z': 'c18a39',  # beak shade
    'l': '848694',  # hide light, legs
    'm': '595965',  # hide
    'd': '34343e',  # hide shade
}

ROWS = [
    '..........aaab...........',
    '........aaaaabbb.........',
    '.......aaaKabbbbc........',
    '.......abbabbKbcc........',
    '........bbcbbccc.........',
    '.........KcccK...........',
    '.......mlllmmd...........',
    '.....yyKlmmmmd...........',
    '...yyyyyKmyymmd..........',
    '.yyyyyyyKlmmmdd..........',
    'yyyzzzzzKlmmmd...........',
    'yzKKKKKKmlmmdd...........',
    'zz.zzzzKmlmmd............',
    'z...zzz.mlmmd............',
    '........mlmKd............',
    '........mlmmd............',
    '.......mlKmmd............',
    '.......mllmKdd...........',
    '.......mllmmmdd..........',
    '.....mmlKmmmmKdd.........',
    '....mlllmmmmmmmddd.......',
    '...mllllmmKKKKmmmmdd.....',
    '..mllllmmKlllllKKmmdd....',
    '..mlllmmmKllmmmmmKKmdd...',
    '..mllmKKmKlmKKmmmmmKKdd..',
    '..mlmmmmKKlmmmKKmmmmmKdd.',
    '..mmmmmmmKlmmmmmKKmmmmdd.',
    '...mmKKmmKmKKmmmmmKKmmdd.',
    '....mmmmdKmmmKKmmmmmKddd.',
    '.....dddddKKmmmmmKKmddd..',
    '.........lm...dddd...ddd.',
    '.........lm.....lm....dd.',
    '.........lm.....lm.......',
    '.........lm.....lm.......',
    '.........lm.....lm.......',
    '........llmm...llmm......',
    '.........lm.....lm.......',
    '.........lm.....lm.......',
    '.........lm.....lm.......',
    '........llmm...llmm......',
    '......lll.mm.lll.mm......',
]

im = grid(ROWS, PAL)
im = outline(im)
save(im)
