"""Where the outline meets the band, do they join, or does one run past the other?

The two are drawn from different fields — the outline follows the height's own
edge, the band follows the mask of face tiles below it — so there is nothing
making them agree pixel for pixel, and two failures are possible:

  orphan   a stretch of outline lying alongside the rock rather than being
           covered by it: a doubled edge, a hairline above the cliff.
  gap      grass between the outline and the rock where they should touch: the
           band standing off the lip instead of tucked under it.

Both are counted against the length of outline that is near rock at all, since
outline far from any rock (a plain north edge) is not in question.

Usage: python tools/join_check.py <render.png> [half]
"""
import sys
import numpy as np
from PIL import Image

im = np.array(Image.open(sys.argv[1]).convert('RGB'))
if len(sys.argv) > 2 and sys.argv[2] == 'half':
    im = im[::2, ::2]
BROWN, INK = (136, 112, 0), (0, 0, 0)
brown = np.all(im == BROWN, axis=2)
ink = np.all(im == INK, axis=2)


def grow(mask, r):
    out = np.zeros_like(mask)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


# The rock mass: brown, plus the ink that belongs to it (ink touching brown).
mass = brown | (ink & grow(brown, 2))
# The outline: ink that is not part of the mass.
line = ink & ~mass
near = grow(mass, 6)

near_line = (line & near).sum()
total_line = line.sum()

# Orphans: outline running alongside the mass, two pixels clear of it. A pixel
# of outline that terminates against the rock is fine and is not counted — it
# has mass within one pixel.
touching = line & grow(mass, 1)
orphan = line & near & ~grow(mass, 1)

# Gaps: grass pixels with mass on one side and outline on the other, close up.
grass = ~mass & ~line
gap = grass & grow(mass, 1) & grow(line, 1)

print('outline px total          %6d' % total_line)
print('  of which near the rock  %6d' % near_line)
print('  terminating on it       %6d' % touching.sum())
print('  orphaned alongside it   %6d   (%.1f%% of near)' % (
    orphan.sum(), 100.0 * orphan.sum() / max(near_line, 1)))
print('grass wedged between      %6d' % gap.sum())
