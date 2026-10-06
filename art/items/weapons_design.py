"""Design for the weapon icons (art/items/weapons.aseprite).

    python art/items/weapons_design.py <out.json>
    python tools/draw_views.py <out.json> art/items/weapons     # through the pixel plugin
    python art/items/gen_weapon_icons.py                        # -> assets/weapon_icons.png

One 16x16 drawing per weapon, in WeaponType order (include/entity.h), posed
corner to corner the way item icons are: grip low left, point high right. The
metal is in the four stone key tones (line, shade, base, lit), which
gen_weapon_icons.py swaps for each ore's ramp, so the menu shows a weapon in
what it is made of. The lowercase letters are wood and stay wood -- the brown
palette browns: w dark, v base, u lit; and k is the katana's dark grip wrap.
"""
import json, sys

PAL = {'K': '000000', 'S': '474751', 'B': '848694', 'L': 'bcbeca',
       'w': '3c2412', 'v': '785830', 'u': '94703d', 'k': '1e1e24'}
ORDER = ['knife', 'club', 'dagger', 'axe', 'halberd', 'katana', 'scythe']

def cell(rows):
    g = [r.ljust(16, '.') for r in rows]
    return g + ['.' * 16] * (16 - len(g))

VIEWS = {
    # a short, broad blade on a wooden handle
    'knife': cell(['',
                   '',
                   '',
                   '..........KKK',
                   '.........KLLBK',
                   '........KLLBSK',
                   '.......KLLBSK',
                   '......KLLBSK',
                   '.....KLBBSK',
                   '....KKBSSK',
                   '...KuKKKK',
                   '..KuvwK',
                   '.KuvwK',
                   '.KvwK',
                   '..KK']),
    # a studded iron head on a wooden haft
    'club': cell(['.........KKK',
                  '.......KKLLBKK',
                  '......KLLKBBSK',
                  '.....KLBBBBKSSK',
                  '.....KBKBBBBSK',
                  '.....KBBBBKSSK',
                  '......KSSBSSK',
                  '.....KuKSSKK',
                  '....KuvwKK',
                  '...KuvwK',
                  '..KuvwK',
                  '.KuvwK',
                  'KuvwK',
                  'KvwK',
                  '.KK']),
    # long and narrow, with a crossguard
    'dagger': cell(['..............KK',
                    '.............KLK',
                    '............KLBK',
                    '...........KLBK',
                    '..........KLBK',
                    '.........KLBK',
                    '........KLBK',
                    '.......KLBK',
                    '...KK.KLBK',
                    '...KLKLBK',
                    '....KSBK',
                    '...KvKSLK',
                    '..KvwK.KK',
                    '.KvwK',
                    '.KwK',
                    '..K']),
    # a broad blade on a long haft, its edge to the top left
    'axe': cell(['....KKKK',
                 '...KLLLBKK',
                 '..KLLBBBBSK',
                 '..KLBBBBBSSKK',
                 '...KLBBBSSKuvK',
                 '....KLBSSKuvwK',
                 '.....KKSKuvwK',
                 '.......KuvwK',
                 '......KuvwK',
                 '.....KuvwK',
                 '....KuvwK',
                 '...KuvwK',
                 '..KuvwK',
                 '.KuvwK',
                 '.KvwK',
                 '..KK']),
    # a spear point and an axe blade on a long haft
    'halberd': cell(['..............KK',
                     '.............KLK',
                     '............KLBK',
                     '.......KK..KLBK',
                     '......KLLKKLBK',
                     '......KLBBBBKK',
                     '.......KLBSKuK',
                     '........KKKuvK',
                     '.........KuvwK',
                     '........KuvwK',
                     '.......KuvwK',
                     '......KuvwK',
                     '.....KuvwK',
                     '....KuvwK',
                     '...KuvwK',
                     '..KvwK']),
    # a long, slightly curved blade, a small guard and a wrapped grip
    'katana': cell(['...............K',
                    '..............KK',
                    '.............KLK',
                    '............KLBK',
                    '...........KLBK',
                    '..........KLBK',
                    '.........KLBK',
                    '........KLBK',
                    '.......KLBK',
                    '.....KKLBK',
                    '.....KSKK',
                    '....KkSK',
                    '...KkwK',
                    '..KkwK',
                    '.KkwK',
                    '..KK']),
    # a long haft with the blade sweeping out from its head
    'scythe': cell(['....KKKKKK',
                    '..KKLLLLLBKK',
                    '.KLLBBBBBKuKK',
                    'KLBKKKKKKKuvK',
                    'KBK.....KuvwK',
                    '.K.....KuvwK',
                    '......KuvwK',
                    '......KuvwK',
                    '.....KuvwK',
                    '.....KuvwK',
                    '....KuvwK',
                    '....KuvwK',
                    '...KuvwK',
                    '...KuvwK',
                    '...KvwK',
                    '....KK']),
}

if __name__ == '__main__':
    json.dump({'pal': PAL, 'view_w': 16, 'order': ORDER, 'views': VIEWS}, open(sys.argv[1], 'w'))
