"""14 Lodsilungur's map mini: the pale hairy trout with its mouth hanging open and its red tongue out, flopping
along on land, at the player's scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its battle views (python tools/minis.py 14): from the front its face with
the eyes on its sides, the grey fin on top, the open mouth and tongue; from the back the fin and the tail
standing up; from the side the grey head, the fin, the spotted body, the tail. The second frame is the flop,
up in the air. 12 px tall: its battle frames stand 15. Three of its battle colours and black: its pale, its
grey (head, fins, the spots of its hair), its red (mouth, tongue). Its white and pink go.

Its chase: flop -- a fish on land: it flops at you, 2.4x the chase pace for 0.25 s and veering 0.7 rad off
the line, one way then the other, then lies there 0.3 s (closes at 0.83); in the air in the flop.
chase_speed(), chase_bend() and chase_frame() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/14_lodsilungur_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': 'c6ccda', 'G': '9797aa', 'R': 'b6433d'}
CHASE = 'flop'

# Front and back from row 16: the left half and the middle column, the right half its mirror.
FRONT = [
    '......' 'K',
    '.....K' 'G',
    '....KG' 'G',
    '...KGG' 'G',
    '..KPPP' 'P',
    '.KGKPP' 'P',
    '.KPPPP' 'P',
    'KPPPPP' 'P',
    'KPPKKK' 'K',
    '.KPKRR' 'R',
    '..KKKR' 'R',
    '....KK' 'K',
]
BACK = FRONT[:5] + [
    '.KGPPP' 'P',
    '.KPPPP' 'P',
    'KPPPPP' 'P',
    'KPPPPK' 'G',
    '.KKKKG' 'G',
    '....KG' 'G',
    '....KK' 'K',
]
SIDE = [
    '..........KK..........',
    '.........KGGK.........',
    '..KKKK..KGGGK.....KK..',
    '.KGGGGKKPPPPPKK..KGGK.',
    'KGKGGPPPPPPPPPPKKPGGK.',
    'KGGGPPPPGPPPPPPPPPGK..',
    'KPPPPPPPPPPPGPPPPPK...',
    'KKKKKPPPPPPPPPPPPPGK..',
    'KRRRKPPGPPPPPPPPKPPGK.',
    '.KRRKKKKKKKKKKKKKKPPGK',
    '..KRK.............KGGK',
    '...K..............KKK.',
]


def whole(halves):
    return [h + h[5::-1] for h in halves]


VIEWS = {
    'D': [(13, 16, whole(FRONT)), (13, 14, whole(FRONT))],
    'U': [(13, 16, whole(BACK)), (13, 14, whole(BACK))],
    'L': [(9, 16, SIDE), (9, 14, SIDE)],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(14, 'lodsilungur', FRAMES, PAL, cap=12)
    minis.chase_gif(14, CHASE, FRAMES, PAL)
