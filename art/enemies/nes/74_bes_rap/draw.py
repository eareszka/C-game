from pix import *

PAL = {
    'a': 'f0b890',  # lit skin
    'b': 'ec8476',  # main pink-red
    'c': 'b6433d',  # shade
    'd': '792727',  # deep shade
    'p': 'fc74b4',  # snout
    't': 'e8e0c0',  # teeth and claws
    's': '9797aa',  # shoulder spike
    'g': '595965',  # spike shade
}

# Body: left half, centre column last. 'e' is an edge: lit on the left, shaded on the right.
HALF = [
    "...............ebb",
    "...s...........ebb",
    "...ss..........ebb",
    "....ss.........ebb",
    "....gss.....eebbbb",
    ".....gs..eeebbbbbb",
    ".....eeeeebbbbbbbb",
    "....eebbbbbbbbbbbb",
    "...eebc.ebbKKKbbbb",
    "...ebc..ebbbbbKKbc",
    "..ebc....ebcbbbbbc",
    "..ebc....ebbcbbbbc",
    "..ebc.....ebbcbbbK",
    "..ebc..eee.ebbbbbK",
    "..ebc.eabbb.ebbbbK",
    "..ebc.abbbbc.ebbcK",
    ".ebc.eabbbbbc.ebcd",
    ".ebc.ebbbbbbbc.cdd",
    ".ebc.ebbbbbbbbcKdd",
    ".ebc.ebbbbbbbbbcKd",
    ".ebc.Kcbbbbbbbbbc.",
    ".ebc.ccKbbbbbbcKK.",
    ".ebc.cccKKKKKKc...",
    ".ebc.cccccccccc...",
    "ebbc.cccdccccc....",
    "ebbc.ebbbKbbKbc...",
    "tKtK.tKtKtKtKt....",
]

left = {'e': 'a'}
right = {'e': 'c', 'a': 'b'}
body = []
for r in HALF:
    r = r.ljust(18, '.')
    l = ''.join(left.get(ch, ch) for ch in r)
    m = ''.join(right.get(ch, ch) for ch in r[-2::-1])
    body.append(l + m)

HEAD = [
    "...a.........a..........",
    "..ab........ab..........",
    "..adc......adc..........",
    ".abdc......abdc.........",
    ".abbbaaaaaabbbbc........",
    "abddbbbbbbbddbbbaaa.....",
    "abbbddbbbddbbbbbbbbpppp.",
    "abbKbbbbbbbKbbcbbbpppppp",
    "abbKbbbbbbbKbcbbbbpKppKp",
    "abbbbbbbbbbbbbbbbbpKppKp",
    "abbbbbbbbbbbbbbbbcpppppp",
    "bKKKKKKKKKKKKKKKcccpppp.",
    "bKttKttKttKttKtKcc......",
    "cKKttKttKttKttKKc.......",
    ".cKKKKKKKKKKKKKc........",
    "..ccccccccccccc.........",
]

im = canvas(35, 41)
stamp(im, grid(body, PAL), 0, 14)
stamp(im, grid(HEAD, PAL), 8, 0)
im = outline(im)
save(im)
