"""Fad Felen approved first frame: slow breathing, creeping lean, dripping saliva.
Draft animation only; game assets are unchanged.
"""
from pathlib import Path
import sys,json,importlib.util
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
meta=json.loads((HERE/'99_fad_felen_frame0_draft.json').read_text());PAL=meta['palette'];RGB={c:tuple(bytes.fromhex(h)) for c,h in PAL.items()};LETTER={v:k for k,v in RGB.items()}
W,H=76,52;STEP=180
BREATH=(0,0,-1,-1,-1,0,0,1,1,0)
LEAN=(0,0,0,0,1,1,1,1,0,0)
NOD=(0,0,0,1,1,1,0,0,0,0)
SALIVA=(3,4,5,6,7,8,8,6,4,3)

def pose_frames():
 im=Image.open(HERE/'99_fad_felen_idle_master.png').convert('RGBA')
 master={(x,y):LETTER[im.getpixel((x,y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x,y))[3]}
 frames=[];anchors=[]
 for i in range(10):
  g={}
  for y in range(H):
   for x in range(W):
    head=x>=48 and y<=35
    sx=x-LEAN[i] if head else x
    sy=y-(BREATH[i] if y<38 else 0)-(NOD[i] if head else 0)
    if (sx,sy) in master:g[x,y]=master[sx,sy]
  # Preserve a black outer outline at newly exposed pixels, without adding
  # outlines at shared roots or texture on the body.
  for x,y in list(g):
   if g[x,y]!='K':
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
     if (x+dx,y+dy) not in g:g[x+dx,y+dy]='K'
  x=60+LEAN[i];y=28+BREATH[i]+NOD[i]
  saliva={}
  for k in range(SALIVA[i]):saliva[x,y+k]='W' if k%3!=2 else 'M'
  saliva[x+1,y+SALIVA[i]-1]='W'
  # Saliva is laid over the lower lip/mane, with a black edge only where
  # it hangs against transparency. No new colours or shading texture.
  for xx,yy in saliva:
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    if (xx+dx,yy+dy) not in g:g[xx+dx,yy+dy]='K'
  g.update(saliva)
  if i in (6,7,8):
   drop_y={6:37,7:38,8:39}[i]
   g[x,drop_y]='W';g[x,drop_y+1]='M'
   for q in ((x-1,drop_y),(x+1,drop_y),(x,drop_y-1),(x,drop_y+2)):
    if q not in g:g[q]='K'
  assert all(0<x<W-1 and 0<y<H-1 for x,y in g)
  # Whole planted feet retain the user's pixels through every inhale/lean.
  for p,c in master.items():
   if p[1]>=41:assert g[p]==c,('foot moved',i,p)
  # The user's eye drawing moves intact with the head, never redraws/blinks.
  for yy in range(17,23):
   for xx in range(55,65):
    c=master.get((xx,yy));q=xx+LEAN[i],yy+BREATH[i]+NOD[i]
    assert g.get(q)==c,('eye changed',i,q)
  frames.append(g);anchors.append({'mouth':[60+LEAN[i],26+BREATH[i]+NOD[i]],'drool':[x,y]})
 return frames,anchors

def main():
 fs,anchors=pose_frames()
 spec=importlib.util.spec_from_file_location('author83',HERE/'83_beast_of_barrisdale_design.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
 d.W=W;d.H=H;d.STEP_MS=STEP;d.PAL=PAL
 strip=d.author(fs,'99_fad_felen_idle_draft')
 gif=[];board=Image.new('RGB',(W*5,(H+10)*2),(25,25,25));draw=ImageDraw.Draw(board)
 for i in range(10):
  frame=strip.crop((i*W,0,(i+1)*W,H));bg=Image.new('RGBA',(W,H),(25,25,25,255));bg.alpha_composite(frame)
  gif.append(bg.convert('RGB').resize((W*8,H*8),Image.Resampling.NEAREST))
  x=(i%5)*W;y=(i//5)*(H+10);board.paste(bg.convert('RGB'),(x,y+10));draw.text((x+2,y),str(i),fill='white')
 gif[0].save(HERE/'99_fad_felen_idle_preview.gif',save_all=True,append_images=gif[1:],duration=STEP,loop=0,disposal=2)
 board.resize((board.width*4,board.height*4),Image.Resampling.NEAREST).save(HERE/'99_fad_felen_idle_review.png')
 (HERE/'99_fad_felen_idle_draft.json').write_text(json.dumps({'width':W,'height':H,'frame_ms':STEP,'palette':PAL,'frames':[[''.join(g.get((x,y),'.') for x in range(W)) for y in range(H)] for g in fs],'anchors':anchors},indent=2)+'\n')
 print('10-frame 1.8s draft idle exported; eyes and planted feet verified unchanged.')
if __name__=='__main__':main()

