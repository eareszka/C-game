"""06 Wakmangganchi Aragondi: its bite, put together, for the user to draw the necks in Aseprite.

    python art/enemies/06_bite_pose.py make     # writes art/enemies/06_bite_pose.aseprite
    python art/enemies/06_bite_pose.py take     # reads the necks back out of it into the game

In the fight the two lowest heads are separate pieces and each neck is one drawing the game turns and
stretches from the body to the head (src/enemies.cpp, WakmangganchiAragondi::parts). `make` lays that out
as a picture -- both heads out sideways at full reach, level -- in layers:
    body         the beast without those two heads (frame 0)          look, don't edit
    neck left    the left neck, where the game draws it               EDIT
    neck right   the right neck                                       EDIT
    heads        the two heads biting                                 look, don't edit
(In the fight the heads are drawn half as big again, so they cover a little more of each neck's end.)

`take` cuts each neck layer back out (NECK_W x 53, from its root on the body to the middle of the head)
and saves them as 06_wakmangganchi_aragondi_necks.png, which 06_wakmangganchi_aragondi_follow.py puts under
the bite sheet's cells; then it writes them straight into assets/enemies/06_wakmangganchi_aragondi_bite.png
too, so the next fight shows them. A neck is stored with its body end on the left; the left neck, drawn
pointing left, is stored mirrored (the game mirrors it back)."""
import os, subprocess, sys, tempfile
from PIL import Image, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASEPRITE = r"C:\Program Files\Aseprite\Aseprite.exe"
NAME = '06_wakmangganchi_aragondi'
W, H, CW, CH, MARG = 302, 166, 42, 53, 24
HOME = ((76, 73), (182, 84))                 # the two heads' cells at rest (art px), from the follow script
ROOTS = ((104, 98), (172, 104))              # where each neck leaves the body (src/enemies.cpp RX, RY)
NECK_W = (82, 88)                            # a neck's length at full reach, art px (src/enemies.cpp NECK_W)
POSE = os.path.join(HERE, '06_bite_pose.aseprite')
NECKS = os.path.join(HERE, NAME + '_necks.png')
BITE = os.path.join(ROOT, 'assets', 'enemies', NAME + '_bite.png')
SHEET = os.path.join(ROOT, 'assets', 'enemies', NAME + '.png')

def neck_box(h):
    """Where neck h sits in the pose picture: (x0, y0, x1, y1)."""
    rx, ry = ROOTS[h]
    x0 = rx - NECK_W[h] if h == 0 else rx
    return (MARG + x0, ry - CH // 2, MARG + x0 + NECK_W[h], ry - CH // 2 + CH)

def stored_necks(bite):
    """The two necks as the game holds them (body end on the left), from under the bite sheet's cells."""
    return [bite.crop((0, 2 * CH + h * CH, NECK_W[h], 3 * CH + h * CH)) for h in (0, 1)]

def make():
    bite = Image.open(BITE).convert('RGBA')
    body = Image.new('RGBA', (W + 2 * MARG, H), (0, 0, 0, 0)); body.paste(Image.open(SHEET).convert('RGBA').crop((0, 0, W, H)), (MARG, 0))
    layers = [('body', body)]
    for h, name in ((0, 'neck left'), (1, 'neck right')):
        n = stored_necks(bite)[h]
        im = Image.new('RGBA', body.size, (0, 0, 0, 0)); im.paste(ImageOps.mirror(n) if h == 0 else n, neck_box(h)[:2]); layers.append((name, im))
    heads = Image.new('RGBA', body.size, (0, 0, 0, 0))
    for h in (0, 1):
        reach = NECK_W[h] - abs(ROOTS[h][0] - (HOME[h][0] + CW // 2))            # how far its middle is from home, at full reach
        cell = bite.crop((9 * CW, h * CH, 10 * CW, (h + 1) * CH))               # mouth shut: the bite
        heads.alpha_composite(cell, (MARG + HOME[h][0] + (-reach if h == 0 else reach), ROOTS[h][1] - CH // 2))
    layers.append(('heads', heads))
    with tempfile.TemporaryDirectory() as tmp:
        args = []
        for i, (name, im) in enumerate(layers):
            p = os.path.join(tmp, f'{i}.png'); im.save(p); args += ['--script-param', f'l{i}={p}', '--script-param', f'n{i}={name}']
        lua = os.path.join(tmp, 'pose.lua')
        open(lua, 'w').write('''
local spr = Sprite(%d, %d, ColorMode.RGB)
local i = 0
while app.params["l" .. i] do
  local layer = i == 0 and spr.layers[1] or spr:newLayer()
  layer.name = app.params["n" .. i]
  spr:newCel(layer, 1, Image{ fromFile = app.params["l" .. i] }, Point(0, 0))
  i = i + 1
end
spr:saveAs(app.params.out)
''' % body.size)
        subprocess.run([ASEPRITE, '-b'] + args + ['--script-param', 'out=' + POSE.replace('\\', '/'), '--script', lua], check=True)
    print(POSE)

def take():
    """The necks are everything in the file that is not on the body or heads layers -- whatever the layers
    are called now (the user merged the two neck layers and painted shading on a new one)."""
    bite = Image.open(BITE).convert('RGBA')
    out = Image.new('RGBA', (max(NECK_W), 2 * CH), (0, 0, 0, 0))
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'necks.png')
        subprocess.run([ASEPRITE, '-b', '--ignore-layer', 'body', '--ignore-layer', 'heads', POSE, '--save-as', p], check=True, stdout=subprocess.DEVNULL)
        im = Image.open(p).convert('RGBA')
    if im.size != (W + 2 * MARG, H): sys.exit(f'{POSE}: the canvas must stay {W + 2 * MARG}x{H}')
    spill = im.copy()
    for h in (0, 1):
        box = neck_box(h); n = im.crop(box); spill.paste((0, 0, 0, 0), box)
        out.paste(ImageOps.mirror(n) if h == 0 else n, (0, h * CH))
    if spill.getbbox(): print(f'  {sum(1 for q in spill.getdata() if q[3])} px drawn outside the two neck boxes are left out (around {spill.getbbox()})')
    out.save(NECKS)
    bite.paste((0, 0, 0, 0), (0, 2 * CH, bite.width, bite.height)); bite.paste(out, (0, 2 * CH)); bite.save(BITE)
    print(NECKS, 'and', BITE)

if __name__ == '__main__':
    {'make': make, 'take': take}[sys.argv[1]]()
