"""24 Zoureg's map mini: the red-hot knife of a snake, coiled and aiming, then uncoiled and thrown straight at you,
at the player's scale, four views, two frames (tools/minis.py).

Drawn through PixelLab (art/enemies/pixellab/24_zoureg/mini, pixellab-out/24-mini): its battle idle (coiled, head
up) and dash (uncoiled, thrown like a knife) in the front, back and left views, each edited into a chunkier map
sprite, snapped to its colours and shrunk at the coil's scale, 12 px (minis.snap, minis.shrink, minis.clean); then
by hand: the white-hot tip on the coiled front, and the side dash drawn long (shrunk, it came out a stub). Three
of its battle colours and black: its orange, its dark red, its white-hot blade tip. Its pale yellow and maroon go.

Its chase: it coils and draws back, still, then thrusts straight at you and stops (the lore: through rocks, trees,
walls and bodies like a hot knife through butter) -- the coil frame while it waits, the dash frame while it flies
(chase_speed() and chase_frame(), src/main.cpp).

    python art/enemies/minis/24_zoureg_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'A': 'fc9838', 'R': 'b70000', 'W': 'fcfcfc'}
CHASE = 'thrust'

COIL_D = (15, 16, [
    '.....K.....',
    '....KWK....',
    '...KAWAK...',
    '..KAAAAAK..',
    '..KRAAAK...',
    '...KRRK....',
    '...KARK....',
    '..KKARRKK..',
    '.KRRARRRRK.',
    'KARAAARRRRK',
    'KRRAAAARRK.',
    '.KKKKKKKK..',
])
COIL_U = (16, 16, [
    '....K.....',
    '...KWK....',
    '..KAAAK...',
    '.KAAAAAK..',
    '.KAAAAK...',
    '..KRRK....',
    '..KRAK....',
    '.KKRARKK..',
    'KARRAAAAK.',
    'KAAAAAAAAK',
    'KRAAAAAAAK',
    '.KKKKKKKK.',
])
COIL_L = (13, 18, [                              # its head to the left, the blade out in front
    '....KK.........',
    '.KKKAAKKK......',
    'KWWAAARAAK.....',
    '.KKKKKKKRAK....',
    '.......KRARK...',
    '......KKRARKK..',
    '.....KRRRARRRK.',
    '....KRRRAAAAAAK',
    '....KRRRAAAAAK.',
    '.....KKKKKKKK..',
])
DASH_D = (17, 16, [                              # thrown at you, the white-hot tip first
    '...K...',
    '..KAK..',
    '.KAAK..',
    '.KAAK..',
    '.KAARK.',
    '.KAARK.',
    '.KAARK.',
    '.KAAAK.',
    'KAAAAAK',
    '.KWWWK.',
    '..KWK..',
    '...K...',
])
DASH_U = (17, 16, [
    '...K...',
    '..KWK..',
    '.KWWWK.',
    'KAAAAAK',
    'KAAAAAK',
    '.KAARK.',
    '.KAARK.',
    '..KARK.',
    '.KARK..',
    '.KARK..',
    '..KRK..',
    '...K...',
])
DASH_L = (12, 23, [                              # thrown straight, its body a long blade behind the tip
    '.......KKK....KK.',
    '.KKKKKKAAAK..KAAK',
    'KWWWWAAARRAKKARK.',
    '.KKKKKKKKKRAAAK..',
    '.........KKKKK...',
])

VIEWS = {'D': [COIL_D, DASH_D], 'U': [COIL_U, DASH_U], 'L': [COIL_L, DASH_L]}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(24, 'zoureg', FRAMES, PAL)
    minis.chase_gif(24, CHASE, FRAMES, PAL)
