from pix import *

PAL = {
    'a': 'c6ccda', 'b': '9797aa', 'c': '595965',
    's': 'f0b890', 't': 'd7a175', 'u': '8d6b4f',
    'w': 'fcfcfc',
}

BODY = [
    "..aa",
    ".aaab",
    ".aabbb",
    "..abbb....aaaa....aaaa.........aaabbbc",
    "...bbc.." + "a" * 23 + "aaabbbc",
    "...Kc" + "a" * 26 + "aabbbbc",
    "...aaaaabaaaaabaaaaabaaaaaa" + "KKKK" + "a" + "abbbbcc",
    "..aaaaaKKKKabbbbbabbbbbbbb" + "K" + "aaab" + "K" + "abbbccc",
    "..aaabK" + "bbbb" + "Kbbbbbbb" + "aaaaaa" + "b" + "K" + "aabb" + "K" + "bbbbccc",
    "..aabK" + "bbbbbbKbbbbbb" + "b" + "KKKKKK" + "b" + "K" + "aabb" + "K" + "bbbcccc",
    "..aabK" + "bbbbbbbbbbbb" + "KKKwwKKK" + "K" + "abbb" + "K" + "bbccccc",
    "..abbK" + "bbbbbbbbbbbb" + "b" + "KKKKKK" + "b" + "K" + "abbc" + "K" + "bcccccc",
    "..abbK" + "bbbbbbbKbbKb" + "baaaaaab" + "K" + "abbc" + "K" + "cccccc",
    "..abbK" + "bbbbbbKbbKbb" + "bbbbbbbc" + "K" + "abbc" + "K" + "ccccc",
    "..abbbK" + "bbbbbKbbKbc" + "cbbccbcc" + "K" + "abbc" + "K" + "bccc",
    "..abbbKccccccKcccc" + "cKccccKc" + "K" + "abbc" + "K" + "bccc",
    "...abbbc...bbcc...cc..cc....abb.bccc",
    "...abbc....bbcc.............abb.bccc",
    "....abc....bcc..............KKK.KKKK",
    "....abc....bcc..............sst..stt",
    "...abc....bcc...............sst..stt",
    "...abc....bcc...............sst...stt",
    "..abc.....bcc..............sssst...sttu",
    "..abc.....bcc.............ssssst...sttuu",
    "..abc.....bcc.............sssstt...sttuu",
    "..abc.....bcc.............sssstt...tttuu",
    ".ccKc....ccKc............s.s.s.t...t.t.u",
    ".ccKc....ccKc............s.s.s.t...t.t.u",
]

HEAD = [
    ".a...............c.",
    ".ab.............bc.",
    "..ab...........bc..",
    "..ab...........bc..",
    "...ab.........bc...",
    "...abc.......bcc...",
    "....abc.aaa.bcc....",
    ".....abaaaaabc.....",
    ".....aaaaaaabb.....",
    "..abKsssssssstKbc..",
    ".aabKsKKsssKKtKbcc.",
    "..acKsssstssstKc...",
    "....KssstuusstK....",
    "....KsswKKKwstK....",
    "....KsssssssstK....",
    ".....KsssssstK.....",
    "......KtttuuK......",
    ".......aabbK.......",
    "........abK........",
    ".........a.........",
]

im = canvas(46, 42)
stamp(im, grid(BODY, PAL), 0, 12)
stamp(im, grid(HEAD, PAL), 25, 0)

im = outline(im)
save(im)
