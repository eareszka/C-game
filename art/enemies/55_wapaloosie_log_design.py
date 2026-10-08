"""Design for the Wapaloosie's log bullet (assets/enemies/55_wapaloosie_log.aseprite).

    python art/enemies/55_wapaloosie_log_design.py <out.json>
    python tools/draw_views.py <out.json> assets/enemies/55_wapaloosie_log   # through the pixel plugin

In its second phase logs fall on the player from out of sight above the
arena, rolling as they come. Drawn as one of the battle's shots first and a
log second: like every enemy bullet, flat colour with a white core -- the
Wapaloosie's violet body, its bullet violet (palette L) outline, a white
streak along the middle -- and just enough log to read: the round cut end
with a ring and a white heart, a few bark dashes, a broken branch stub.

The sheet: three rows of FRAMES frames, W x H each. Row 0 lies flat; rows 1
and 2 are the same log tilted about TILT degrees left and right, each column
moved up or down whole, so the pixels stay on the grid (the battle steps
between the rows to rock it, never rotating). Along each row it rolls about
its long axis: the bark rides over the top and wraps round, a notch on the
cut end's rim turns, the stub stands up off the top, faces you, drops under,
and the loop closes seamless.
"""
import json, math, sys

PAL = {'L': 'b69cee', 'F': '664b95', 'f': '3b2a58', 'W': 'fcfcfc'}
W, H, FRAMES, TILT = 46, 18, 8, 10
LOG_H = 10                           # the flat log's own height, centred in the frame
CY, R = 4.5, 4.0                     # in the log's own rows: its axis and radius, rows 1..8
X0, X1 = 2, 38                       # the side, from its left end to the cut end
EX, ERX = 39.5, 3.4                  # the cut end: an oval as tall as the log

GRAIN = [(6, 5, 0.1), (16, 6, 0.36), (27, 5, 0.62), (11, 4, 0.85), (31, 4, 0.2)]   # (x, length, turn), 0 facing you
STUB = (21, 0.5)

def in_end(x, y, rx, ry):
    return ((x + 0.5 - EX) / rx) ** 2 + ((y + 0.5 - (CY + 0.5)) / ry) ** 2 <= 1

def flat(k):
    """The log lying flat, rolled k frames: LOG_H rows."""
    roll = k / FRAMES
    g = [['.'] * W for _ in range(LOG_H)]
    for y in range(LOG_H):
        for x in range(X0, X1 + 1):
            d = abs(y + 0.5 - (CY + 0.5))
            if d <= R and not (x == X0 and d > R - 1.2): g[y][x] = 'F'
    sx, st = STUB                                        # the stub, standing off the round over the top or under
    a = 2 * math.pi * (st + roll)
    c, s = math.cos(a), math.sin(a)
    if abs(s) > 0.7 and c < 0.5:
        g[0 if s < 0 else LOG_H - 1][sx] = g[0 if s < 0 else LOG_H - 1][sx + 1] = 'F'
    for y in range(LOG_H):                               # the outline: any wood with open air beside it
        for x in range(W):
            if g[y][x] == 'F' and any(not (0 <= x + dx < W and 0 <= y + dy < LOG_H) or g[y + dy][x + dx] == '.'
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'L'
    core = round(CY)                                     # the white core along the middle, as every shot has
    for x in range(X0 + 3, X1 - 2): g[core][x] = g[core + 1][x] = 'W'
    if c >= 0.5:                                         # the stub facing you: a light cut end, off the core
        y = round(CY + R * s * 0.8)
        if y not in (core, core + 1): g[y][sx] = g[y][sx + 1] = 'L'
    for gx, n, t in GRAIN:                               # bark dashes riding round with the roll, off the core
        a2 = 2 * math.pi * (t + roll)
        y = round(CY + R * math.sin(a2) * 0.85)
        if math.cos(a2) > 0.25 and 1 < y < LOG_H - 2 and y not in (core, core + 1):
            for x in range(gx, gx + n):
                if g[y][x] == 'F': g[y][x] = 'f'
    for y in range(LOG_H):                               # the cut end: rim, one ring, a white heart
        for x in range(W):
            if in_end(x, y, ERX, R + 0.1):
                rim = not in_end(x, y, ERX - 1, R - 0.6) or y in (1, LOG_H - 2)
                ring = in_end(x, y, ERX - 1.6, R - 1.8) and not in_end(x, y, ERX - 2.3, R - 2.6)
                g[y][x] = 'L' if rim or ring else 'W' if in_end(x, y, ERX - 2.4, R - 2.7) else 'F'
    a = 2 * math.pi * roll                               # a notch on the rim, turning with the log
    nx = math.floor(EX + math.cos(a) * (ERX - 0.6)); ny = math.floor(CY + 0.5 + math.sin(a) * (R - 0.5))
    if in_end(nx, ny, ERX, R + 0.1): g[ny][nx] = 'f'
    return g

def framed(g, tilt):
    """Into an H-row frame, centred, each column moved whole by its tilt."""
    out = [['.'] * W for _ in range(H)]
    top = (H - LOG_H) // 2
    t = math.tan(math.radians(tilt))
    for x in range(W):
        dy = round((x + 0.5 - W / 2) * t)
        for y in range(LOG_H):
            if g[y][x] != '.': out[top + y + dy][x] = g[y][x]
    if tilt:
        # Moving columns breaks the outline at every step: re-draw it on the
        # moved shape -- wood against air is outline, an old outline pixel now
        # inside is wood (the cut end's rings, on its own columns, stay).
        air = lambda x, y: not (0 <= x < W and 0 <= y < H) or out[y][x] == '.'
        edge = lambda x, y: any(air(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        was = [r[:] for r in out]
        for y in range(H):
            for x in range(W):
                if was[y][x] == '.': continue
                if edge(x, y): out[y][x] = 'L'
                elif was[y][x] == 'L' and x < EX - ERX - 1: out[y][x] = 'F'
    return [''.join(r) for r in out]

if __name__ == '__main__':
    views, extras = {}, []
    for k in range(FRAMES):
        views[f'F{k}'] = framed(flat(k), 0)
    for row, tilt in ((1, -TILT), (2, TILT)):              # tilt left: its left end up; right: its right end up
        for k in range(FRAMES):
            extras.append([k * W, row * H, framed(flat(k), tilt)])
    json.dump({'pal': PAL, 'view_w': W, 'order': list(views), 'views': views, 'extras': extras}, open(sys.argv[1], 'w'))
    for v in (views['F0'], extras[0][2], extras[FRAMES][2]):
        print('\n'.join(v)); print()
