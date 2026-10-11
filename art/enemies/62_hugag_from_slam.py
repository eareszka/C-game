"""The user redrew the face (and shaded the feet) on the stomp sheet's frame 1, which is the SUNK pose with dust.
Make the standing first frame from it: put the near front foot back (the dust was drawn over it: it gets the
near hind foot's pixels, which the user shaded the same way), then un-sink it (rows above LEG_ROW up one, a
leg row put back)."""
import sys
from PIL import Image
W, H, LEG_ROW = 98, 65, 50
T = (0, 0, 0, 0)
u = Image.open(sys.argv[1]).convert('RGBA')
foot = u.crop((20, 59, 30, 65))                    # the near hind foot
u.paste(T, (38, 59, 48, 65)); u.paste(foot, (38, 59))
u.paste(T, (48, 62, 49, 65))                       # a scrap of the dust's rim beside it
f0 = Image.new('RGBA', (W, H), T)
f0.paste(u.crop((0, 1, W, LEG_ROW + 1)), (0, 0))   # rows 1..LEG_ROW -> 0..LEG_ROW-1
f0.paste(u.crop((0, LEG_ROW + 1, W, LEG_ROW + 2)), (0, LEG_ROW))
f0.paste(u.crop((0, LEG_ROW + 1, W, H)), (0, LEG_ROW + 1))
f0.save(sys.argv[2])
low = Image.new('RGBA', (W, H), T); low.paste(f0.crop((0, 0, W, LEG_ROW)), (0, 1)); low.paste(f0.crop((0, LEG_ROW + 1, W, H)), (0, LEG_ROW + 1))
print('sinking the new first frame gives the user\'s frame back:', low.tobytes() == u.tobytes())
