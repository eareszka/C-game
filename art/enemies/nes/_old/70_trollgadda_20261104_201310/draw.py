from pix import *

PAL = {
    'a': '4fa667',  # scale light
    'b': '2c6c44',  # scale shade, leaf shade
    's': '4edc4a',  # leaf light
    'm': '05c43a',  # leaf mid
    't': '815423',  # wood and fin
    'u': '633e1b',  # wood shade
    'c': 'e8e0c0',  # belly, teeth
}

rows = [
    #012345678901234567890123456789012
    "...............ssss...ssss.......",
    ".............ssssssmm.sssssmm....",
    ".........sss.ssssmmmmKssssmmmmm..",
    "........sssmKsssmmmmbKsssmmmmmss.",
    "........ssmmKbsmmmmbbKbmmmmbbsssm",
    "........smmmbKKbmmbbKsKKbmbbKKsmm",
    "........mmbbmmmKKbbKssmmKKbKmmmbb",
    ".........bbbmmmmmKKmmmmbbttbbbbb.",
    ".........m.m.bbmmb.bbb.ttu.tt..m.",
    ".........m....m.m..m...ttu.tt..m.",
    ".tt....................ttuttu....",
    ".ttt.....ttt.............ttttuu..",
    "..ttuu..ttttu....aaaKaaaaaKtttuu.",
    ".tttuu..aaaaaaaaaaaaKaaaaaKtttuu.",
    "..tttuK" + "aaabaaabaaaba" + "K" + "aKaaaK" + "tttuu",
    "...ttub" + "baabbaabbaabb" + "K" + "aKaaaaK" + "ttuu",
    "...ttua" + "aabaaabaaabaa" + "K" + "aaaaaaaKuu" + "aa",
    "..tttuK" + "abbaabbaabbaa" + "K" + "aaaaaaaaaaaa",
    "..ttuu." + "bbKbbbKbbbKbb" + "K" + "KKKKKKcKcKcK",
    "..tuu.." + "bKcbKcbKcbKcb" + "K" + "cccbbbbbbbb.",
    ".ttt...." + "cccccccccccccccccc",
    ".tt.......ttu.....ttu",
    "..........tu.......tu",
]

im = grid(rows, PAL)
im = outline(im)
save(im)
