"""Pull a tail in by deletion only, as short_key.py does for the impact's straight shaft: where a line of the tail
repeats the one before it (straight, or slid 1-2 px along a slant), the repeat is dropped and everything beyond it
(the rest of the tail and the ball) moves in one px. Each tail segment gets shorter; no px drawn or recoloured.
  up(f, n, top, ball_bottom): an upright tail -- rows between the ball and the body's top (`top`), part above moves down.
  out(f, n, left, ball_left): a tail out behind -- columns between `left` and the ball, part right moves left."""
from PIL import Image
CLEAR = (0, 0, 0, 0)

def _slid(r, s): return (r[s:] + (None,) * s) if s > 0 else ((None,) * -s + r[:len(r) + s]) if s < 0 else r

def _repeats(f, lo, hi, k=1):
    """Rows y in (lo, hi), lowest first, whose band y..y+k-1 repeats band y+k.. slid by s: [(y, s)]."""
    p = f.load(); W, _ = f.size
    row = lambda y: tuple(p[x, y] if p[x, y][3] else None for x in range(W))
    out = []
    for y in range(hi - k, lo, -1):
        a, b = [row(y + i) for i in range(k)], [row(y + k + i) for i in range(k)]
        for s in (0, 1, -1, 2, -2, 3, -3):
            if all(sum(v is not None for v in r) >= 3 for r in a) and a == [_slid(r, s) for r in b]: out.append((y, s)); break
    return out

def _drop(f, n, lo, hi, k=1):
    """Drop n px of repeats (k rows at a time): the band y..y+k-1 goes, everything above moves down k and back by s."""
    W, _ = f.size; done = 0
    while done < n:
        r = _repeats(f, lo + done, hi, k)
        if not r: break
        y, s = r[0]; part = f.crop((0, 0, W, y))
        out = f.copy(); out.paste(CLEAR, (0, 0, W, y + k)); out.alpha_composite(part, (-s, k)); f = out; done += k
    return f, done

def up(f, n, top, ball_bottom, k=1): return _drop(f, n, ball_bottom, top, k)

def out(f, n, left, ball_left, k=1):
    W, _ = f.size                                         # columns -> rows: x becomes W-1-y (right = up)
    g, done = _drop(f.transpose(Image.ROTATE_90), n, W - 1 - ball_left, W - 1 - left, k)
    return g.transpose(Image.ROTATE_270), done
