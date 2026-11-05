"""85 Nanabolele's map mini: the Sotho river dragon of the flooded caves at the player's scale, four views, two
frames (tools/minis.py) -- swimming SUBMERGED (the user, 2026-10-29: "mini would be swimming submerged").

Drawn by hand after its redesigned battle sheet (art/enemies/pixellab/85_nanabolele), fill only, one black outline
round it. Under the water all but what breaks the surface, as a sea serpent's humps do: its horned head up on its neck
with its glowing eyes and dark jaws, one hump of its back with its glowing scale lights, the glowing tip of
its tail, the pale water between and round them. Head on, the wake round its neck; from behind, the lights
down its spine; from the side, head, hump and tail tip in a line. The two frames swim: it sinks a row and the
hump rolls back along it. The right view is the left mirrored. Three colours and
black: its dark green hide, the glow green of its lights and eyes (its scales shine in the dark water: the eyes
take the lights' colour here, the one accent), the pale mint of the wake.

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide.

    python art/enemies/minis/85_nanabolele_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'D': '235436', 'G': '4edc4a', 'M': 'a8f0bc'}
CHASE = 'surf'
HEIGHT = 15

FRONT = ([               # head on, raised out of the water: thin horns, glowing eyes under angled brows, the snout narrowing to its dark jaws, the wake round its neck
    '.D...........D.',
    '..D.........D..',
    '..DD.......DD..',
    '...DDDDDDDDD...',
    '..DDGDDDDDGDD..',
    '..DDDGDDDGDDD..',
    '...DDDDDDDDD...',
    '....DDDDDDD....',
    '....DKKKKKD....',
    '....DDDDDDD....',
    '.M..DDDDDDD..M.',
    'MMMMMDDDDDMMMMM',
    '.MMMMMMMMMMMMM.',
], [                     # it rolls: sunk a row, the wake further out
    '...............',
    '.D...........D.',
    '..D.........D..',
    '..DD.......DD..',
    '...DDDDDDDDD...',
    '..DDGDDDDDGDD..',
    '..DDDGDDDGDDD..',
    '...DDDDDDDDD...',
    '....DKKKKKD....',
    'M...DDDDDDD...M',
    'MM.MMDDDDDMM.MM',
    '.MMMMMMMMMMMMM.',
    '..M.........M..',
])
BACK = ([                # from behind: its neck going away, the lights down its spine, the horns, the wake
    '..D.........D..',
    '..DD.......DD..',
    '...DD.....DD...',
    '...DDDDDDDDD...',
    '...DDDDDDDDD...',
    '....DDDGDDD....',
    '.....DDGDD.....',
    '.....DGGGD.....',
    '.....DDGDD.....',
    '.M...DGGGD...M.',
    'MMMMMDDGDDMMMMM',
    '.MMMMMMMMMMMMM.',
], [
    '...............',
    '..D.........D..',
    '..DD.......DD..',
    '...DD.....DD...',
    '...DDDDDDDDD...',
    '....DDDGDDD....',
    '.....DDGDD.....',
    '.....DGGGD.....',
    'M....DDGDD....M',
    'MM..MDGGGDM..MM',
    '.MMMMMDGDMMMMM.',
    '..M.MMMMMMM.M..',
])
SIDE = ([                # its head to the left, up on its neck out of the water, a hump of its back with its lights,
    '..D.D.........................',   # the tail tip glowing up behind, water between
    '...DDD.....................G..',
    '..DDDDD...................GGG.',
    '.DGDDDDD.........G..G......G..',
    'DDDDDDDD........GDGGDG.....DD.',
    'DKKKKDDD.......DDDDDDDD....DD.',
    '.DDDDDDD......DDDDDDDDDD..DD..',
    '..DDDDDD.....DDDDDDDDDDDD.DD..',
    'MM.DDDDDMMMMMDDDDDDDDDDDDMDDMM',
    '.MMMMMMMM.MMMMMMMMMMMMMMMMMMM.',
], [                     # the wave rolls back along it: the hump further back, the tail lower
    '..D.D.........................',
    '...DDD........................',
    '..DDDDD.....................G.',
    '.DGDDDDD...........G..G....GGG',
    'DDDDDDDD..........GDGGDG....G.',
    'DKKKKDDD.........DDDDDDDD...DD',
    '.DDDDDDD........DDDDDDDDDD..DD',
    '..DDDDDD.......DDDDDDDDDDDDDD.',
    'MM.DDDDDMMMMMMMDDDDDDDDDDDDDMM',
    '.MMMMMMMMMMM.MMMMMMMMMMMMMMMM.',
])
for rows in BACK + FRONT + SIDE:
    assert len({len(r) for r in rows}) == 1, rows


def place(rows):
    """Fill rows to a frame: centred, the bottom row on the cell's last but one (the outline under it)."""
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    return ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})


FRAMES = {'D': [place(r) for r in FRONT], 'U': [place(r) for r in BACK], 'L': [place(r) for r in SIDE]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(85, 'nanabolele', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(85, CHASE, FRAMES, PAL)
