from pix import *

PAL = {
    'r': 'b70000',  # flame edge, comb, wattle
    'o': 'fc9838',  # flame
    'y': 'fae488',  # flame core, beak, eyes
    'l': '848694',  # plucked hide, lit rim, shins
    'm': '474751',  # plucked hide
    'd': '292931',  # plucked hide, shade
}

ROWS = [
    ".....|.r...|.....|.|.....|.....|.....",
    "..o..|.rr..|.....|.|.....|...r.|.....",
    ".....|rrr..|..y..|.|..o..|..rr.|.....",
    ".....|rorr.|.....|.|.....|..rrr|.....",
    ".r...|roorr|.....|.|.....|.rror|...r.",
    ".rr..|.roor|.....|.|.....|rroor|..rr.",
    ".rrr.|.royo|r..r.|r|.r...|roor.|.rrr.",
    ".roor|.royy|or.rr|r|rr..r|oyor.|roor.",
    ".royo|r.ryy|orKll|l|mmKro|yyor.|royor",
    ".royo|r.roy|yKlmm|m|mmmKy|yor.r|oyor.",
    "..roo|orroy|Klmmm|m|mmmdK|yorro|oor..",
    "..roy|ooroy|Klmym|m|mymdK|yoroo|yor..",
    "...ro|oyooy|Klmym|y|mymdK|yooyo|or...",
    "....r|oyyoy|Klmmy|y|ymmdK|yoyyo|r....",
    "....r|oyyoy|Kmmmm|o|mmddK|yoyyo|r....",
    "...ro|oyyoy|yKmmm|r|mddKy|yoyyo|or...",
    "..rro|oyyyo|KmKKK|r|KKKdK|oyyyo|orr..",
    ".rroy|oyyyK|llmmm|m|mmmdd|Kyyyo|yorr.",
    "rrooy|yyoKl|lmmmm|m|mmmmd|dKoyy|yoorr",
    ".rroy|yyoKl|mKmmm|m|mmmKd|dKoyy|yorr.",
    "..roy|yyoKl|lmKmm|m|mmKmm|dKoyy|yor..",
    "...ro|yyoKl|lmKmm|m|mmKmd|dKoyy|or...",
    "....r|oooKm|mKmmm|m|mmmKd|dKooo|r....",
    ".....|rooKm|Kmmmm|m|mmddK|dKoor|.....",
    "..y..|.rr..|mmmmm|m|mmddd|..rr.|.....",
    ".....|.....|mKKmm|m|mmddd|.....|o....",
    ".....|.....|.mmmm|m|dddd.|.....|.....",
    ".....|.....|..mmd|d|ddd..|.....|.....",
    ".....|.....|...dd|d|dd...|.....|.....",
    ".....|.....|...md|.|md...|.....|.....",
    ".....|.....|...md|.|md...|.....|.....",
    ".....|.....|..lm.|.|.lm..|.....|.....",
    ".....|.....|..l..|.|..l..|.....|.....",
    ".....|.....|..l..|.|..l..|.....|.....",
    ".....|.....|..l..|.|..l..|.....|.....",
    ".....|.....|..l..|.|..l..|.....|.....",
    ".....|.....|..l..|.|..l..|.....|.....",
    ".....|.....|.lll.|.|.lll.|.....|.....",
    ".....|.....|l.l.l|.|l.l.l|.....|.....",
]

rows = [r.replace('|', '') for r in ROWS]
assert all(len(r) == 31 for r in rows), [i for i, r in enumerate(rows) if len(r) != 31]

im = grid(rows, PAL)
im = outline(im)
save(im)
