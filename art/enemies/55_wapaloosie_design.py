"""55 Wapaloosie, medium tier, to art/direction/SPRITE_STYLE.md: front and
front 3/4 only.

    python art/enemies/55_wapaloosie_design.py   # writes the .json and .txt of both sheets, draft.png

The user, 2026-10-10: "only front and front 3/4s"; then, of the first draft,
"front is too wide" and a reference picture (A Book of Creatures' wapaloosie).
Two sheets, each drawn from the front (D) and 3/4 front-right (DR; DL mirrors):
  55_wapaloosie     on all fours: arched / the full inchworm hump (frame 1, the spikes) / low
  55_wapaloosie_up  phase 2, reared up on its back legs: stand / chest up (frame 1, the spores) / low

After the reference: rust fur with a white belly, the body one tall inchworm
arch, a small head low at the front with dark tufted ears and a white muzzle,
grey bird's feet, bracket fungus (yellow) down its back, a thin dark tail.
From the front it is narrow: the head, and the arch rising straight up behind it,
as wide as the arch is thick in the 3/4 view (the user: the thickness must agree
between views).

At this size it is drawn by hand (the grids below, a letter a colour). Then
drawn into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io
PAL = {'K': '000000', 't': '421618', 'D': '792727', 'M': 'b6433d', 'L': 'ec8476', 'W': 'e8e0c0', 'G': '848694', 'Y': 'f0e880'}
W, H = 26, 26
GROUND = H - 3

def sym(half): return [r + r[::-1] for r in half.split()]
def cut(grid, *rows): return [r for i, r in enumerate(grid) if i not in rows]      # rows shorter: a lower pose
def tall(grid, row): return grid[:row] + [grid[row]] + grid[row:]                  # a row taller: chest up

D_HUMP = sym("""
...KK
..KMM
.YKML
..KML
.YKML
..KMM
.tKMM
.tKDD
.KMMM
.KMKM
.KMWW
.KWWW
..KWK
.KMKK
.KGK.
KGGK.
KKKK.
""")                                                      # the arch end on, behind the head; fungus out each side
Q_HUMP = [r.ljust(26, '.') for r in """
.........KKKKKK
......Y.KMMMMMMK.Y
.......KMMLLLLMMK
.....YKMMLLLLLLMMKY
......KMMMMKKKWMMMK
....Y.KMMMK...KWMMMKY
.....KMMMWK...KWWMMMK
.....KMMMWK....KWMMMK.t.t
.....KMMMWK....KWMMMKtKtK
.....KMMMWK....KWMMMMMMMMK
....KMMMMWK.....KMMMMMKMMK
tttKMMMMMK......KMMMMMWWWK
...KKMMMMK.......KKMWWWKK
....KGGGK........KGGGKK
...KGGGGK.......KGGGGK
...KKKKKK.......KKKKKK
""".split()]
D_UP = sym("""
.t...
.t...
.KKKK
.KMMM
.KMKM
.KMWW
.KWWW
..KWK
..KWW
.YKMW
.GKMW
.YKMW
..KMW
.YKMW
..KMW
..KMM
.KGKK
KGGK.
KKKK.
""")                                                      # reared up: the white belly to us, a claw out each side
Q_UP = """
....t.t.......
...KtKtK......
...KMMMMK.....
..KMMMMMMK....
..KMMMKMMK....
..KMMMMWWWK...
...KMMWWKK....
..YKMMWWK.....
...KMMWWKGK...
..YKMMWWKK....
...KMMWWK.....
..YKMMWWK.....
...KMMWWK.....
t..KMMMWK.....
.ttKMMMKK.....
..KGGKGGK.....
..KKKKKKK.....
""".split()

def stand(grid):
    """A grid standing on the ground, in the middle of the frame."""
    x0, y0 = (W - len(grid[0])) // 2, GROUND - len(grid) + 1
    return {(x0 + x, y0 + y): c for y, r in enumerate(grid) for x, c in enumerate(r) if c != '.'}

IDLE = {'D': [stand(cut(D_HUMP, 3, 4)), stand(D_HUMP), stand(cut(D_HUMP, 2, 3, 4, 5))],
        'DR': [stand(cut(Q_HUMP, 5, 6)), stand(Q_HUMP), stand(cut(Q_HUMP, 5, 6, 7))]}
UP = {'D': [stand(D_UP), stand(tall(D_UP, 12)), stand(cut(D_UP, 12))],
      'DR': [stand(Q_UP), stand(tall(Q_UP, 10)), stand(cut(Q_UP, 10))]}
SHEETS = {'55_wapaloosie': IDLE, '55_wapaloosie_up': UP}
rows = lambda g: [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]

if __name__ == '__main__':
    from PIL import Image
    for n, gr in (('D_HUMP', D_HUMP), ('Q_HUMP', Q_HUMP), ('D_UP', D_UP), ('Q_UP', Q_UP)):
        assert len({len(r) for r in gr}) == 1, (n, [len(r) for r in gr])
    for name, V in SHEETS.items():
        fl = [(f'{k}{i}', g) for k, fr in V.items() for i, g in enumerate(fr)]
        json.dump({'pal': PAL, 'view_w': W, 'views': {n: rows(g) for n, g in fl}, 'order': [n for n, g in fl]}, open(name + '.json', 'w'))
        t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + ['#BODY', '14', '#POSE', 'frames', '#DIRS', 'fore']
        for k, fr in V.items():
            for i, g in enumerate(fr): t += [f'#{k}' + (f'@{i}' if i else '')] + rows(g)[:-1]
        io.open(name + '.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    allg = [g for V in SHEETS.values() for fr in V.values() for g in fr]
    im = Image.new('RGBA', (W * 12, H * 2), (0, 0, 0, 255)); im.paste((255, 170, 200, 255), (W * 6, 0, W * 12, H * 2))
    for r, k in enumerate(('D', 'DR')):
        for i, g in enumerate(IDLE[k] + UP[k]):
            for (x, y), c in g.items():
                if 0 <= x < W and 0 <= y < H:
                    for b in (0, 1): im.putpixel((b * 6 * W + i * W + x, r * H + y), tuple(int(PAL[c][j:j + 2], 16) for j in (0, 2, 4)) + (255,))
    im.resize((im.width * 5, im.height * 5), Image.NEAREST).save('draft.png')
    out = {(x, y) for g in allg for x, y in g if not (0 <= x < W and 0 <= y < H - 1)}
    assert not out, f'drawn outside the frame: {sorted(out)[:8]}'
