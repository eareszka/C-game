"""04 Lili's new mini, its sources for PixelLab: each view drawn by hand at mini size after its battle view (a block shrink mushed the face and clipped the feet), fill
only, one outline, padded so PixelLab has room. Ears, pale band with the eyes, hot-pink snout, bristles, four legs (the user, 2026-10-10: "only 4 legs"); its battle sheet's
dark underside goes for the three-colour cap, as the old mini's did. Writes src_D/U/L.png and a board.

    python art/enemies/pixellab/04_lili/mini/source.py
"""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff
from PIL import Image
PAL = {'K': '000000', 'M': 'ec8476', 'L': 'f0b890', 'P': 'fc74b4'}
LEGS = ['.MM.MM.MM.MM.', '.M..MM.MM..M.', '.M...M.M...M.']
VIEWS = {
    'D': ['.M.........M.', '.MM.......MM.', '.MMMMMMMMMMM.', 'MMLLLLLLLLLMM', 'MMLKLLLLLKLMM', 'MMMMLLLLLMMMM', 'MMMPPPPPPPMMM', 'MMPPPPPPPPPMM', 'MMMPPPPPPPMMM', '.MMMMMMMMMMM.'] + LEGS,
    'U': ['.M.........M.', '.MM.......MM.', '.MMMMMMMMMMM.', 'MMMMMLLLMMMMM', 'MMMLLLKLLLMMM', 'MMLLLLLLLLLMM', 'MMLLLLKLLLLMM', 'MMLLLLLLLLLMM', 'MMMLLLKLLLMMM', '.MMMMMMMMMMM.'] + LEGS,
    'L': ['.........M.........', '.......MMMM.M..M...', '.....MMMMMMMMMMMMM.', '...MMLLLLMMMLLLLMMM', '..MMLKLLLMMLLLLLMMM', 'PPPMMLLLMMMMMLLMMMM',
          'PPPMMMMMMMMMMMMMMMM', 'PPPMMMMMMMMMMMMMMM.', '..MMMMMMMMMMMMMMM..', '....MM.MM....MM.MM.', '....M..MM....M..MM.', '....M...M....M...M.'],
}
CANVAS = {'D': (24, (-8, -6)), 'U': (24, (-8, -6)), 'L': (32, (-4, 2))}   # canvas side, where the cell's corner lands: PixelLab wants the subject at 55-70% of it
board = Image.new('RGBA', (minis.W * 3 * 8, minis.H * 8), minis.GRASS)
for n, (v, rows) in enumerate(VIEWS.items()):
    assert len({len(r) for r in rows}) == 1, v
    x0, y0 = minis.W // 2 - len(rows[0]) // 2, minis.H - 1 - len(rows)
    g = ff.outline({(x0 + x, y0 + y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'})
    size, off = CANVAS[v]; pad = Image.new('RGBA', (size, size)); pad.paste(ff.image(g, PAL, minis.W, minis.H), off); pad.save(HERE / f'src_{v}.png')
    board.alpha_composite(ff.image(g, PAL, minis.W, minis.H, bg=minis.GRASS).resize((minis.W * 8, minis.H * 8), 0), (n * minis.W * 8, 0))
board.save(HERE / 'src_board.png')
