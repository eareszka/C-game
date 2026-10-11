"""Lay an enemy frame out of parts, flat, the way the user finished the Nadubi (82).

A frame is a list of parts, back to front. A part is (pixels, kind, root):
    pixels  {(x, y): letter}
    kind    'flesh'  the body: limbs, trunk, neck. All flesh is ONE body -- its black edge is round
                     the outside only, never between two parts of it
            'solid'  a thing with its own edge all round: a barb, a claw, a head drawn apart
            'raw'    set down exactly as given
    root    for a limb, where it joins the body (see draw)

Used by art/enemies/NN_*_design.py; the small drawings (heads, hands) stay in those scripts."""
import math, io, json
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
add = lambda p, d: (p[0] + d[0], p[1] + d[1])
mid = lambda a, b, lift=0: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - lift)

def stroke(a, b, wa, wb):
    """The pixels of a length from a to b, wa px thick at a and wb at b."""
    (ax, ay), (bx, by) = a, b
    L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1.0
    r = max(wa, wb) / 2 + 1
    out = set()
    for y in range(int(min(ay, by) - r), int(max(ay, by) + r) + 1):
        for x in range(int(min(ax, bx) - r), int(max(ax, bx) + r) + 1):
            t = min(1.0, max(0.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
            if math.hypot(x - (ax + t * (bx - ax)), y - (ay + t * (by - ay))) <= (wa + (wb - wa) * t) / 2: out.add((x, y))
    return out

def run(*points_widths):
    """The pixels of a length through several points: (point, width), (point, width), ..."""
    px = set()
    for (a, wa), (b, wb) in zip(points_widths, points_widths[1:]): px |= stroke(a, b, wa, wb)
    return px

def grid(x0, y0, rows, kind='flesh', flip=False):
    """A small drawing (a letter a colour, '.' nothing) set down with its top left at (x0, y0)."""
    out = {}
    for y, r in enumerate(rows):
        r = r[::-1] if flip else r
        for x, c in enumerate(r):
            if c != '.': out[(round(x0) + x, round(y0) + y)] = c
    return (out, kind, None)

def draw(parts, w, h, darker, root_r=9):
    """One frame from its parts: {pixel: letter}. darker: a flesh tone -> the tone a step darker.

    - a solid part carries a black edge all round, flesh only on empty space or on a solid part
      behind it; either way only where it is thick enough to hold one -- thinner, it is colour only;
    - flesh in front of flesh of another tone gives way a pixel to it, with no line;
    - flesh in front of flesh of its own tone, further than root_r from its root, is a tone darker
      along that edge, so a limb crossing the body still reads."""
    owner, tone = {}, {}
    for i, (px, kind, root) in enumerate(parts):
        for p, c in px.items(): owner[p] = i; tone[p] = c
    flesh = lambda q: q in owner and parts[owner[q]][1] == 'flesh'
    out = {}
    for p, i in owner.items():
        px, kind, root = parts[i]; c = tone[p]
        nb = [add(p, d) for d in N4]
        if kind == 'raw' or c == 'K': out[p] = c
        elif kind == 'solid':
            inner = lambda q: q in px and all(add(q, d) in px for d in N4)
            out[p] = 'K' if any(q not in px for q in nb) and any(inner(q) for q in nb) else c
        elif any(q not in owner or (owner[q] < i and not flesh(q)) for q in nb):
            inner = lambda q: flesh(q) and all(add(q, d) in owner for d in N4)
            out[p] = 'K' if any(inner(q) for q in nb) else c
        else:
            behind = [tone[q] for q in nb if flesh(q) and owner[q] < i and q not in px]
            far = [t for t in behind if t != c and t in darker.values()]
            if far: out[p] = far[0]
            elif behind and root is not None and c in darker and math.dist(p, root) > root_r: out[p] = darker[c]
            else: out[p] = c
    off = sorted(p for p in out if not (0 <= p[0] < w and 1 <= p[1] < h))
    assert not off, f'drawn outside the frame (row 0 stays empty): {off[:6]}'
    return out

def rows(g, w, h):
    """The frame as the build reads it: rows 1..h-1 (it leaves the top row empty), then a blank one."""
    return [''.join(g.get((x, y + 1), '.') for x in range(w)) for y in range(h - 1)] + ['.' * w]

def write(name, frames, pal, w, h, body=40, dirs='down', view='D', pose='frames'):
    """NAME.json for tools/draw_views.py and NAME.txt for tools/build_enemy.py: one drawn view, its frames.
    view: which view the drawing is ('D' the front; 'DR' the 3/4, with dirs='quarter').
    pose: 'frames' when every frame is given; None for one still, which the build breathes about row `body`."""
    json.dump({'pal': pal, 'view_w': w, 'views': {str(i): rows(g, w, h) for i, g in enumerate(frames)}, 'order': [str(i) for i in range(len(frames))]}, open(name + '.json', 'w'))
    t = ['#PAL'] + [f'{k} {v}' for k, v in pal.items()] + ['#BODY', str(body)] + (['#POSE', pose] if pose else []) + ['#DIRS', dirs]
    for i, g in enumerate(frames): t += ['#' + view + (f'@{i}' if i else '')] + rows(g, w, h)[:-1]
    io.open(name + '.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(t) + '\n')

def image(g, pal, w, h, bg=None):
    from PIL import Image
    im = Image.new('RGBA', (w, h), bg or (0, 0, 0, 0))
    for (x, y), c in g.items(): im.putpixel((x, y), tuple(int(pal[c][i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    return im

def demo():
    """The rules above, on three bars."""
    limb = ({(x, y): 'L' for x in range(2, 9) for y in range(1, 6)}, 'flesh', (2, 3))
    far = ({(x, y): 'F' for x in range(6, 14) for y in range(3, 9)}, 'flesh', None)
    g = draw([far, limb], 20, 12, {'L': 'F', 'F': 'f'})
    assert g[(5, 1)] == 'K' and g[(5, 3)] == 'L'            # edge on empty space; inside
    assert g[(8, 4)] == 'F' and (7, 4) in g and g[(7, 4)] == 'L'   # over the other tone: gives way a pixel, no black
    assert 'K' not in {g[(8, y)] for y in (3, 4, 5)}
    thin = ({(x, 10): 'C' for x in range(2, 8)}, 'solid', None)
    assert set(draw([thin], 20, 12, {}).values()) == {'C'}  # too thin for an edge
    print('flat_parts ok')

if __name__ == '__main__':
    demo()
