"""Design for the player's battle shots (art/battle/shots.aseprite).

    python art/battle/shots_design.py <out.json>
    python tools/draw_views.py <out.json> art/battle/shots     # through the pixel plugin
    python art/battle/gen_shots.py                             # -> assets/battle/player_shots.png

One 16x16 shot per weapon, WeaponType order, pointing right (the game turns it
the way it flies). The language of the enemy's bullets in the same arena:
flat, no outline, a white core -- NES shots -- but each the plain silhouette
of its weapon, so what is firing is never in doubt. The katana and scythe
fire slashes: the scythe's twice the katana's, the strongest weapon's mark.
B and L are the stone base and lit tones, which gen_shots.py swaps for each
ore's; W is the palette's white and stays white.
"""
import json, sys

PAL = {'B': '848694', 'L': 'bcbeca', 'W': 'fcfcfc'}
ORDER = ['knife', 'club', 'dagger', 'axe', 'halberd', 'katana', 'scythe']

E = '.' * 16
def cell(top, rows):
    g = [E] * top + [r.ljust(16, '.') for r in rows]
    return g + [E] * (16 - len(g))

VIEWS = {
 # a short blade: stub of a grip, a guard, a broad blade to a point
 'knife': cell(6, ['......L',
                   '..BBBBLLLLLLL',
                   '..BBBBLWWWWWWL',
                   '......L']),
 # a club: a grip into a big round head
 'club': cell(4, ['..........LLL',
                  '.........LWWWL',
                  '........LWWWWWL',
                  '.BBBBBBBLWWWWWL',
                  '.BBBBBBBLWWWWWL',
                  '........LWWWWWL',
                  '.........LWWWL',
                  '..........LLL']),
 # a dagger: long cross-guard, a thin blade
 'dagger': cell(5, ['.....L',
                    '.....L',
                    '.BBB.LWWWWWWWWL',
                    '.....L',
                    '.....L']),
 # an axe: a haft with a broad bit at its end
 'axe': cell(2, ['..........LLL',
                 '.........LWWWL',
                 '.........LWWWWL',
                 '..........LWWWL',
                 '...BBBBBBBBLWWL',
                 '...BBBBBBBBLWWL',
                 '..........LWWWL',
                 '.........LWWWWL',
                 '.........LWWWL',
                 '..........LLL']),
 # a halberd: a long pole, an axe blade on top, a spear point at its end
 'halberd': cell(3, ['.........LL',
                     '........LWWL',
                     '........LWWWL..L',
                     'BBBBBBBBBBBBLWWL',
                     '............LL']),
 # the katana's slash: a thin crescent, belly forward
 'katana': cell(2, ['.......BL',
                    '........BL',
                    '.........BL',
                    '.........BWL',
                    '..........BWL',
                    '..........BWL',
                    '..........BWL',
                    '..........BWL',
                    '.........BWL',
                    '.........BL',
                    '........BL',
                    '.......BL']),
 # the scythe's slash: the same crescent, twice as tall and thick, a white edge
 'scythe': cell(0, ['....BBL',
                    '.....BBLL',
                    '......BBLWL',
                    '.......BBLWL',
                    '........BBLWL',
                    '........BBLWWL',
                    '.........BBLWWL',
                    '.........BBLWWL',
                    '.........BBLWWL',
                    '.........BBLWWL',
                    '........BBLWWL',
                    '........BBLWL',
                    '.......BBLWL',
                    '......BBLWL',
                    '.....BBLL',
                    '....BBL']),
}

if __name__ == '__main__':
    json.dump({'pal': PAL, 'view_w': 16, 'order': ORDER, 'views': VIEWS}, open(sys.argv[1], 'w'))
