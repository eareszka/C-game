"""Draw the lumberjack's four-direction axe swing through the local pixel plugin."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'art/direction'))
from first_frame import draw_frames
from mcpc import Pixel

source=ROOT/'assets/npcs/woodcutter.png'
before=hashlib.sha256(source.read_bytes()).hexdigest()
sheet=Image.open(source).convert('RGBA')
palette={'K':'000000','W':'633e1b','R':'b6433d','S':'d7a175'}
inverse={tuple(bytes.fromhex(v)):k for k,v in palette.items()}
W=H=40

def line(g,a,b,c,radius=0):
    steps=max(abs(b[0]-a[0]),abs(b[1]-a[1]))
    for i in range(steps+1):
        t=i/max(1,steps);x=round(a[0]+(b[0]-a[0])*t);y=round(a[1]+(b[1]-a[1])*t)
        for oy in range(-radius,radius+1):
            for ox in range(-radius,radius+1):
                if 0<=x+ox<W and 0<=y+oy<H:g[x+ox,y+oy]=c

# Bronze-colored blade and dark wooden handle use the character's four colors.
HEAD=['.....KK.','....KSSK','...KWSSK','KKKWSSSK','KWKWSSSK',
      'KKKWSSSK','...KWSSK','....KSSK','.....KK.']
poses_right=[((23,25),(28,17)),((22,22),(20,6)),((24,26),(32,24)),((23,26),(28,21))]
poses_down=[((21,26),(27,20)),((20,22),(20,6)),((20,28),(20,34)),((21,27),(25,26))]
poses_up=[((20,23),(27,18)),((20,20),(20,5)),((20,20),(20,12)),((21,23),(26,16))]
frames=[]
for row,direction in enumerate(('down','up','left','right')):
    base=sheet.crop((0,row*20,14,row*20+20))
    planted={(x+12,y+12):inverse[base.getpixel((x,y))[:3]]
             for y in range(20) for x in range(14) if base.getpixel((x,y))[3]}
    for phase in range(4):
        g=dict(planted)
        if phase==2:
            # Lean into contact while keeping the lower body planted.
            dx=1 if direction=='right' else -1 if direction=='left' else 0
            dy=1 if direction=='down' else -1 if direction=='up' else 0
            g={(x,y):c for (x,y),c in planted.items() if y>=28}
            g.update({(x+dx,y+dy):c for (x,y),c in planted.items() if y<28})
        grip,head=(poses_right if direction in ('left','right') else poses_up if direction=='up' else poses_down)[phase]
        shoulder=(21,25) if direction in ('left','right') else (19,25)
        if direction=='left':
            grip=(38-grip[0],grip[1]);head=(38-head[0],head[1]);shoulder=(38-shoulder[0],shoulder[1])
        # Clear the old dangling sleeve before drawing bent, two-handed arms.
        arm_x=range(21,24) if direction=='right' else range(14,17) if direction=='left' else range(17,22)
        for y in range(25,28):
            for x in arm_x:g.pop((x,y),None)
        for origin in (shoulder,(shoulder[0]-1,shoulder[1]+2)):
            line(g,origin,grip,'K',1)
            line(g,origin,grip,'R')
        line(g,(grip[0],grip[1]+2),head,'K',1)
        line(g,(grip[0],grip[1]+2),head,'W')
        for y,r in enumerate(HEAD):
            for x,c in enumerate(r):
                if c!='.':g[head[0]+(2-x if direction=='left' else x-2),head[1]+y-4]=c
        for x,y in (grip,(grip[0]-1,grip[1]+1)):g[x,y]='S'
        assert all(0<=x<W and 0<=y<H for x,y in g)
        # Feet never stride or slide while swinging.
        for (x,y),c in planted.items():
            if y>=28:g[x,y]=c
        frames.append(g)

out=ROOT/'art/npcs/woodcutter_chop_v2'
if not out.with_suffix('.aseprite').exists():
    draw_frames(frames,palette,W,H,out,200,{f'chop_{d}':(i*4+1,i*4+4) for i,d in enumerate(('down','up','left','right'))})
px=Pixel()
try:
    px.call('export_spritesheet',sprite_path=out.with_suffix('.aseprite').as_posix(),
        output_path=(ROOT/'assets/npcs/woodcutter_chop.png').as_posix(),layout='horizontal',padding=0,include_json=True)
finally:px.p.terminate()
atlas=Image.open(ROOT/'assets/npcs/woodcutter_chop.png').convert('RGBA')
assert atlas.size==(640,40)
for i,g in enumerate(frames):
    for y in range(H):
        for x in range(W):
            pixel=atlas.getpixel((i*W+x,y))
            assert (inverse[pixel[:3]] if pixel[3] else None)==g.get((x,y))
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(ROOT/'assets/npcs/woodcutter_chop.json').write_text(json.dumps({
    'frame_width':40,'frame_height':40,'frames_per_direction':4,'directions':['down','up','left','right'],
    'duration_ms':200,'impact_frame':2,'sprite_offset':{'x':-12,'y':-12},'palette':palette,
    'source':out.relative_to(ROOT).with_suffix('.aseprite').as_posix(),'plugin_pixel_verified':True},indent=2)+'\n')
board=Image.new('RGBA',(160,160))
for i in range(16):board.paste(atlas.crop((i*40,0,i*40+40,40)),((i%4)*40,(i//4)*40))
board.resize((640,640),Image.Resampling.NEAREST).save(ROOT/'build_tmp/npc_review/woodcutter_chop_preview.png')
print('16 chopping cels: plugin export verified, four colors, walking source unchanged.')
