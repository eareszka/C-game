from pix import *

PAL = {
    'l': 'd7a175',  # hide light
    'm': '967448',  # hide mid
    'd': '583518',  # hide shade
    'h': '2b190e',  # hollow inside the hide
    's': '595965',  # muzzle
    't': '34343e',  # muzzle shade
    'w': 'e8e0c0',  # tusk
    'y': 'b29e5c',  # tusk shade
}

# Left half, right-aligned on the centre line. Written outer edge to centre.
# Extra letters pick a different tone on the right half, so light comes from the upper left:
#   o light both sides, n mid left / shade right, a tusk left / shade right, b shade left / tusk right
#   u muzzle left / muzzle shade right
ROWS = [
    "looo",
    "llooooo",
    "llllmmooo",
    "lllmmmmmmm",
    "llmmmmmmmmm",
    "lommmmmmmmmm",
    "lnooommmmmmm",
    "lnoKKommmmmmm",
    "lnmmmmmmmmmmm",
    "lnmmmKKKKKKmmm",
    "lnmmKssssssKmm",
    "lnmmKssssssssKm",
    "lnmmKsssssssssK",
    "lnmmKssssssssKss",
    "lnmmKsssssssKsss",
    "lnmmKsstsstssssuK",
    "lnmmKssstsstsssuK",
    "lnmmmKtsssssssstuK",
    "lnmmmmKttttttttttK",
    "lnmmmmmKKKKKawbKKKh",
    "lnmmmmdKdhhhawbhhhh",
    "lnmmmmmdKdhhhawbhhhh",
    "lnmmmKmdKdhhhawbhdhh",
    "lnmmmmKmdKdhhhawbhdhh",
    "lnmmmKmmdKdhhawbhhdhh",
    "lnmKmmKmmdKdhhawbhhdhh",
    "lnmmKmmKmmdKdhhawbhhhhh",
    "lnmmdKmKmmmdKhhhawbhhhhh",
    "lnmmdKmmKmmmdKhhhawbhhhhh",
    "lnmddKlmmKmmmdKhhhabhhhhhh",
    "lnmd...lnKmmmmdKhhhabhhhhhh",
    "lnmd...lnmKmmmmdKhhhabhhhhhh",
    "lnd....lnmmmmmmmdKhhhabhhhhhh",
    "nd....lnmmmmmmmmdKhhhahhhhhhh",
    "lnmmmmmmmmmmdKhhhahhhhhhh",
    "lnmdKmmmmmmmdKhhhahhhhhhh",
    "lnmdd.mmmmmmmdKhhhahhhhhhh",
    "lndd...dmmmmKmdKhhhdhhhhdhh",
    "nd.....ddmmddmdKhhhdhhhhdhh",
    "ddd..dddKhhh..hhh..h",
]

WIDTH = 29
RIGHT = {'l': 'm', 'n': 'd', 'o': 'l', 'a': 'y', 'b': 'w', 'u': 't'}
LEFT = {'o': 'l', 'n': 'm', 'a': 'w', 'b': 'y', 'u': 's'}

rows = []
for r in ROWS:
    half = r.rjust(WIDTH, '.')
    left = ''.join(LEFT.get(c, c) for c in half)
    right = ''.join(RIGHT.get(c, c) for c in half)
    rows.append(left + right[::-1])

im = grid(rows, PAL)
im = outline(im)
save(im)
