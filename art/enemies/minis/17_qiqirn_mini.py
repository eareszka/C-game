"""17 Qiqirn's map mini: the huge hairless dog, hair only at its mouth, feet and ear and tail tips, galloping,
at the player's scale, four views of two frames (tools/minis.py).

Placed by hand over the shrink of its run sheet (assets/enemies/17_qiqirn_run.png, python tools/minis.py 17):
the long ears with their tufts, the narrow head, the ribs showing down its bare flank, the thin legs with
their white feet, the tail streaming out behind with its white tip. Its two frames are its sprint: from the
side all four legs stretched out, then gathered under it; from the front and back a diagonal pair up, then
the other. 16 px tall, as the Snawfus: its battle frames stand 31. Three of its battle colours
and black: its bare skin, its darker skin (the ribs, the hind legs, the shade), its white (the tufts). Its
pale grey goes to white, its brown ear tips to the darker skin.

Its chase: flee -- it is terrified of people and runs from you (the user, 2026-10-14: "this enemy is unique
it runs away from player"): once it has seen you, its heading turned straight away from you, at 1.1x the
chase pace, 198 px a second -- run and you catch it (you run 240), walk and it gets away; past the edge of
sight it forgets you and ambles again. chase_speed() and chase_bend() in src/main.cpp and tools/minis.py.

    python art/enemies/minis/17_qiqirn_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'S': 'f0b890', 'D': 'd7a175', 'W': 'fcfcfc'}
CHASE = 'flee'

FRONT = [                                        # from row 12
    '..K...K..',
    '.KWK.KWK.',
    '.KSSKSSK.',
    '.KSSSSSK.',
    '.KSKSKSK.',
    '..KSSSK..',
    '..KSWSK..',
    '..KSSSK..',
    '.KSSSSSK.',
    '.KSDSDSK.',
    '.KDSKSDK.',
]
# All four legs sprinting (the user, 2026-10-14: "all legs should be spriting"): the front pair outside, the
# hind pair between, a diagonal pair up, then the other.
FRONT_LEGS = ['KSKDKDKSK', 'KWKDKKKSK', '.KKDK.KSK', '..KWK.KWK', '...K...K.']
BACK = FRONT[:4] + [
    '.KSSSSSK.',
    '..KSSSK..',
    '..KSSSK..',
    '..KSSSK..',
    '.KSSSSSK.',
    '.KSSSSSK.',
    '.KDSWSDK.',
]
BACK_LEGS = ['KDKSKSKDK', 'KWKSKKKDK', '.KKSK.KDK', '..KWK.KWK', '...K...K.']
SIDE = [                                         # from row 12, its head to the left, its tail streaming out
    '....K..............',
    '...KWK.............',
    '..KSSK.............',
    '.KSSSSK............',
    'KSKSSSK..KKKK......',
    'KWSSSSKKKSSSSKK....',
    '.KKSSSSSSSSSSSSKKKK',
    '...KSSSDSDSSSSSSSWK',
    '...KSSDSDSSSSSSKKK.',
    '...KSSKKKKKKSSSK...',
]
# The gallop from the side, all four legs: stretched out, front pair forward and hind pair back; then
# gathered, crossing under its belly.
SIDE_LEGS = (['...KSDK.....KSDK...', '..KSDK.......KSDK..', '.KSDK.........KSDK.', 'KSDK...........KSDK',
              'KWWK...........KWWK', '.KK.............KK.'],
             ['...KSDK.....KSDK...', '....KSDK...KSDK....', '.....KSDK.KSDK.....', '......KSDKKSDK.....',
              '......KWWKKWWK.....', '.......KK..KK......'])

VIEWS = {
    'D': [(15, 12, FRONT + FRONT_LEGS), (15, 12, FRONT + [r[::-1] for r in FRONT_LEGS])],
    'U': [(15, 12, BACK + BACK_LEGS), (15, 12, BACK + [r[::-1] for r in BACK_LEGS])],
    'L': [(10, 12, SIDE + legs) for legs in SIDE_LEGS],
}
VIEWS['R'] = [(40 - x0 - len(rows[0]), top, [r[::-1] for r in rows]) for x0, top, rows in VIEWS['L']]
FRAMES = {v: [ff.grid([(top + y, x0, r) for y, r in enumerate(rows)], PAL) for x0, top, rows in fs]
          for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(17, 'qiqirn', FRAMES, PAL, cap=16)
    minis.chase_gif(17, CHASE, FRAMES, PAL)
