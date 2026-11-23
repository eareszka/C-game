"""Review files for the old-path restyle: D's 8 frames before/after, the D GIF at 260 ms (read back with seek+load),
the 8 views at frame 0 before/after, and a board of the restyled 64 among installed enemies at the game's 2x on
the battle's black. Run: python -B art/enemies/anim/64_dungavenhooter/oldpath/review.py"""
import os, re, sys
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import enemy_sheet as es
RV = os.path.join(HERE, 'review'); os.makedirs(RV, exist_ok=True)
BG, ARENA = (24, 24, 32, 255), (0, 0, 0, 255)
before = es.cells_of(Image.open(os.path.join(ROOT, 'assets/enemies/64_dungavenhooter.png')).convert('RGBA'), 8, False)
after = es.cells_of(Image.open(os.path.join(HERE, '64_dungavenhooter_nes.png')).convert('RGBA'), 8, False)
W, H = 98, 65

def grid(rows, s, bg=BG, g=3):
    out = Image.new('RGBA', (g + max(len(r) for r in rows) * (W + g), g + len(rows) * (H + g)), bg)
    for j, r in enumerate(rows):
        for i, f in enumerate(r): out.alpha_composite(f, (g + i * (W + g), g + j * (H + g)))
    return out.resize((out.width * s, out.height * s), Image.NEAREST)

def gif(fs, path, s=4):
    g = [Image.alpha_composite(Image.new('RGBA', f.size, BG), f).convert('RGB').resize((W * s, H * s), Image.NEAREST) for f in fs]
    g[0].save(path, save_all=True, append_images=g[1:], duration=260, loop=0, disposal=1, optimize=False)
    n = Image.open(path).n_frames; back = []
    for i in range(n):
        r = Image.open(path); r.seek(i); r.load(); back.append(r.convert('RGB'))
    assert n == len(g) and all(ImageChops.difference(back[i - 1], back[i]).getbbox() for i in range(1, n)), (path, n)
    return n

def sheet_d0(i):
    """Enemy i's frame 0 facing D, from its ENEMY_SHEETS row in battle.cpp."""
    src = open(os.path.join(ROOT, 'src/battle.cpp'), encoding='utf-8').read()
    rows = re.findall(r'^\s*\{ "(assets/enemies/[^"]+)",\s*\{[^}]*\},\s*(\d+)(?:,\s*(true|false))?', src, re.M)
    path, n, r = next(x for x in rows if re.search(r'/%02d_' % i, x[0]))
    return es.cells_of(Image.open(os.path.join(ROOT, path)).convert('RGBA'), int(n), r == 'true')['D'][0]

if __name__ == '__main__':
    grid([before['D'], after['D']], 4).save(os.path.join(RV, 'D_before_after.png'))
    print('D gif frames', gif(after['D'], os.path.join(RV, 'D_260.gif')))
    grid([[before[d][0] for d in es.ORDER], [after[d][0] for d in es.ORDER]], 3).save(os.path.join(RV, 'views_f0.png'))
    names = {61: 'Roperite', 62: 'Hugag', 63: 'Hidebehind', 67: 'Lagopus', 72: 'Mahwot', 73: 'Liderc', 74: 'Bes rap', 75: 'Makalala', 76: 'Loch Oich'}
    tiles = [('64 NEW (restyled)', after['D'][0]), ('64 before', before['D'][0])] + [('%d %s' % (i, n), sheet_d0(i)) for i, n in names.items()]
    tiles = [(t, f.crop(f.getbbox())) for t, f in tiles]
    cols, pad, lab = 4, 16, 16
    cw = max(f.width for _, f in tiles) * 2 + pad; ch = max(f.height for _, f in tiles) * 2 + pad + lab
    board = Image.new('RGBA', (cols * cw + pad, ((len(tiles) + cols - 1) // cols) * ch + pad), ARENA); d = ImageDraw.Draw(board)
    for k, (t, f) in enumerate(tiles):
        x, y = pad + (k % cols) * cw, pad + (k // cols) * ch
        d.text((x, y), t, fill=(255, 255, 0, 255) if t.startswith('64 NEW') else (200, 200, 200, 255))
        big = f.resize((f.width * 2, f.height * 2), Image.NEAREST)
        board.alpha_composite(big, (x, y + lab + (ch - pad - lab - big.height)))
    board.save(os.path.join(RV, 'board_2x.png')); print('board', os.path.join(RV, 'board_2x.png'), board.size)
