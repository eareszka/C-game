"""58 Agropelter, big tier (the size of the sprite it replaces: its body 50 px
tall and 28 wide, arms spanning about 80), to art/direction/SPRITE_STYLE.md:
front view only, an 8-frame idle.

    python art/enemies/58_agropelter_design.py     # writes design.json, 58_agropelter.txt, draft.png

The user, 2026-10-10: "only front facing but longer animation and follow bible
exact"; 8 frames in the old 1.3 s loop (162 ms each), the old design kept.
  0 rest   1 right arm winds back   2 right arm at full reach (the lash)   3 it recoils, mouth opening
  4 both arms up, mouth widest (the scream)   5-7 the left arm's wind, reach (the lash) and recoil
Of the first draft (built from ellipses): "needs to be same size as original",
"arms need to be drawn on top of body", "looks like it uses too much shapes".
Then a reference picture, and "arms should both be wiggling constantly".
Then the user edited frame 0 in Aseprite (narrowed eyes, shorter side tufts,
three toes, no line where an arm lies on the chest, cut knuckles) and asked for
the arms to "move in an almost sine wave motion between frames".
So the body is drawn by hand, pixel by pixel, as one silhouette (BODY below, a
letter a colour, the left half; the right mirrors it) and the arms are drawn
over it, body and head both.

"The villainous face of an ape on a sinewy little body, with incredibly powerful
arms like organic whips": a bare ape's face in shaggy grey-brown fur (the user's reference picture), broad
shoulders, a narrow waist, folded haunches, bare feet, and two very long bare
arms, thick at the shoulder and whip-thin at the wrist.

Then drawn into the .aseprite through the pixel plugin by tools/draw_views.py."""
import json, io, math
PAL = {'K': '000000', 'D': '463422', 'M': '8d6b4f', 'L': 'b2966a', 'r': 'd7a175', 's': 'f0b890', 'W': 'fcfcfc'}
W, H = 98, 65
GROUND = 62
MIR = lambda p: (W - 1 - p[0], p[1])

BODY = """
.......K...K..
......KLK.KLKK
......KLLKLLLL
.....KMLLLLLLL
.....KMLLLLMMM
....KMMLMMKKKK
...KKMMMKKssss
..KMMMMKssssss
...KMMMKKKKsss
..KMMMKsKWWKss
.KMMMMKssKKsss
..KMMMKssssssK
.KMMMMKsssssss
..KMMMKrsKKKKK
..KKDMMKrsWsss
.KDDDDMMKrrrss
..KKKDDMMKKKKK
.....KDDDDDDDD
....KKKKDDDDDD
...KMMMKKKKDDD
..KMMMMMMMLLLL
.KMMMMMMLLLLLL
.KMMMMMLLLLLLL
KMMMMMMLLLLLLL
.KMMMMMLLLLLLL
.KMMMMMLLLLLLL
..KMMMMMLLLLLL
...KMMMMLLLLLL
..KMMMMMMLLLLL
...KMMMMMLLLLL
....KMMMMMLLLL
....KMMMMMMLLL
....KMMMMMMLLL
...KMMMMMMMMLL
....KMMMMMMMML
....KDMMMMMMMM
..KKKKKDMMMMMM
.KMMLLMKDDMMMM
KMMLLLMMKDDDDD
KMLLLLMMMKDDDD
KMMLLMMMMKDDDD
KMMMMMMMMKKDDD
KMMMMMMMDK.KKK
.KDMMMMDDK....
.KDDDDDDK.....
..KKsssssK....
.KssKssKssK...
.KsKssKsrrK...
..KKKKKKKK....
""".split()
X0, Y0 = (W - 28) // 2, GROUND - len(BODY) + 1
MOUTH_ROW = 13                                            # BODY's row of the shut mouth

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
def rim(shape): return {(x + dx, y + dy) for (x, y) in shape for dx, dy in N4} - shape

def arm(deg, length, swing, phase):
    """The right arm from its shoulder, in front of the chest: it sets out along `deg` (0 = straight out,
    negative = up) and its heading swings `swing` degrees either way down its length, so it hangs in big
    loose loops like rope; 6 px thick at the shoulder to 2 at the wrist, a long-fingered hand on the end.
    Returns (pixels, hand point)."""
    x, y = X0 + 22.0, Y0 + 22.0
    out = set(); n = int(length * 3)
    for i in range(n + 1):
        t = i / n
        h = math.radians(deg + swing * math.sin(phase + t * math.tau * 0.9) * min(1.0, t * 3))
        nx, ny = x + math.cos(h) / 3, y + math.sin(h) / 3
        if not (7 <= nx <= W - 8 and 6 <= ny <= GROUND - 5): break     # it stays in the frame: the loop is cut short there
        x, y = nx, ny
        r = 3.0 if t < 0.15 else 2.5 if t < 0.35 else 2.0 if t < 0.6 else 1.5 if t < 0.85 else 1.0
        k = int(r + 1)
        out |= {(round(x) + dx, round(y) + dy) for dx in range(-k, k + 1) for dy in range(-k, k + 1) if dx * dx + dy * dy <= r * r}
    hx, hy = round(x), round(y); ux, uy = math.cos(h), math.sin(h); vx, vy = -uy, ux
    out |= {(hx + dx, hy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}           # the hand
    out -= {(hx + round(ux + vx * k), hy + round(uy + vy * k)) for k in (-1, 1)}    # its knuckle corners cut (the user)
    out |= {(hx + round(ux * j + vx * k), hy + round(uy * j + vy * k)) for k in (-2, 0, 2) for j in (2, 3)}   # three long fingers
    return out, (hx, hy)

REST = (8, 44, 70, 0.0)
def front(right=REST, left=REST, mouth=0):
    """right / left: each arm's (deg, length, wave, phase); mouth 0 shut, 1 opening, 2 wide."""
    g = {}
    for y, r in enumerate(BODY):
        for x, c in enumerate(r + r[::-1]):
            if c != '.': g[(X0 + x, Y0 + y)] = c
    if mouth:                                             # the jaw dropped: black, teeth along the top (and the bottom, wide)
        mh = (0, 3, 5)[mouth]
        for y in range(Y0 + MOUTH_ROW, Y0 + MOUTH_ROW + mh):
            for x in range(X0 + 9, X0 + 19): g[(x, y)] = 'K'
        for x in range(X0 + 10, X0 + 18, 2): g[(x, Y0 + MOUTH_ROW + 1)] = 'W'
        if mouth == 2:
            for x in range(X0 + 11, X0 + 18, 2): g[(x, Y0 + MOUTH_ROW + mh - 2)] = 'W'
    hands = []
    for spec, flip in ((right, False), (left, True)):     # the arms last: over the body and the head
        a, hand = arm(*spec)
        if flip: a, hand = {MIR(p) for p in a}, MIR(hand)
        for p in rim(a):                                  # no line where it lies on the chest (the user): it grows out of it
            if not (p in g and g[p] != 'K' and p[1] >= Y0 + 19): g[p] = 'K'
        for p in a: g[p] = 's'
        for (x, y) in a:                                  # its underside, where it is thick enough to have one
            if (x, y + 1) not in a and (x, y - 1) in a and (x, y - 2) in a: g[(x, y)] = 'r'
        hands.append(hand)
    return g, hands

# Both arms move as a sine wave (the user): the wave runs down each arm one step a frame, so over the 8
# frames it travels a whole wavelength and loops; the two arms are half a wave apart. Riding on that,
# smoothly, each arm straightens and lifts toward its lash -- the right fullest on frame 2, the left on 6.
def one(f, peak, shift):
    e = 0.5 * (1 + math.cos(math.tau * (f - peak) / 8))                          # 1 at its lash frame, 0 opposite
    return (12 - 22 * e, 37, 75 - 45 * e, -math.tau * f / 8 + shift)             # (deg, length, swing, phase)
POSES = [dict(right=one(f, 2, 0.0), left=one(f, 6, math.pi), mouth={3: 1, 4: 2}.get(f, 0)) for f in range(8)]
FRAMES = [front(**p) for p in POSES]
rows = lambda g: [''.join(g.get((x, y), '.') for x in range(W)) for y in range(H)]

if __name__ == '__main__':
    from PIL import Image
    assert all(len(r) == 14 for r in BODY), [(i, len(r)) for i, r in enumerate(BODY) if len(r) != 14]
    gs = [g for g, h in FRAMES]
    json.dump({'pal': PAL, 'view_w': W, 'views': {str(i): rows(g) for i, g in enumerate(gs)}, 'order': [str(i) for i in range(len(gs))]}, open('design.json', 'w'))
    head = ['#BODY', '30', '#POSE', 'frames', '#DIRS', 'down', '#ROWS']
    t = ['#PAL'] + [f'{k} {v}' for k, v in PAL.items()] + head
    for i, g in enumerate(gs): t += ['#D' + (f'@{i}' if i else '')] + rows(g)[:-1]
    io.open('58_agropelter.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')
    im = Image.new('RGBA', (W * 4, H * 4), (0, 0, 0, 255)); im.paste((255, 170, 200, 255), (0, H * 2, W * 4, H * 4))
    for i, g in enumerate(gs):
        for (x, y), c in g.items():
            if 0 <= x < W and 0 <= y < H:
                for b in (0, 1): im.putpixel(((i % 4) * W + x, (b * 2 + i // 4) * H + y), tuple(int(PAL[c][j:j + 2], 16) for j in (0, 2, 4)) + (255,))
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save('draft.png')
    out = {(x, y) for g in gs for x, y in g if not (0 <= x < W and 0 <= y < H - 1)}
    assert not out, f'drawn outside the frame: {sorted(out)[:8]}'
    body = {(X0 + x, Y0 + y): c for y, r in enumerate(BODY) for x, c in enumerate(r + r[::-1]) if c != '.'}
    edge = {p for p in body if any((p[0] + dx, p[1] + dy) not in body for dx, dy in N4)}
    inner = sum(1 for p, c in body.items() if c == 'K' and p not in edge)
    print('body', len(BODY), 'tall | head share %.0f%%' % (100 * 19 / len(BODY)), '| interior black %.0f%%' % (100 * inner / len(body)),
          '| colours', len({c for gg in gs for c in gg.values()}) - 1, '+ K | hands', [h for gg, h in FRAMES])
