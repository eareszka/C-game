from pathlib import Path
import sys,json,importlib.util
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'tools'));import enemy_sheet
meta=json.loads((HERE/'99_fad_felen_frame0_draft.json').read_text());PAL=meta['palette'];RGB={c:tuple(bytes.fromhex(h)) for c,h in PAL.items()};INV={v:k for k,v in RGB.items()}
W,H,STEP=76,74,180

def standing():
 im=enemy_sheet.read(str(HERE/'99_fad_felen_frame0_draft.aseprite'));master={(x,y):INV[im.getpixel((x,y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]}
 g={}
 def poly(c,p):
  for yy in range(H):
   for xx in range(W):
    x,y=xx+.5,yy+.5;inside=False
    for a,b in zip(p,p[1:]+p[:1]):
     if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    if inside:g[xx,yy]=c
 def line(c,p):
  for a,b in zip(p,p[1:]):
   n=max(abs(a[0]-b[0]),abs(a[1]-b[1]))
   for i in range(n+1):g[round(a[0]+(b[0]-a[0])*i/max(1,n)),round(a[1]+(b[1]-a[1])*i/max(1,n))]=c
 # Far bent hind leg, weight carried on a short planted foot.
 poly('D',[(31,42),(37,46),(33,51),(30,54),(31,59),(29,66),(34,68),(35,70),(24,70),(21,69),(24,67),(26,64),(27,59),(25,53),(26,48)])
 # Thin tail sweeps away behind the upright pelvis.
 poly('M',[(31,44),(29,48),(23,51),(18,52),(13,51),(10,48),(9,43),(11,47),(14,49),(19,50),(25,47),(29,43)])
 # Upright but hunched back and chest, with broad flat form-based fills.
 poly('M',[(27,34),(27,24),(29,18),(32,15),(35,17),(37,24),(43,28),(47,34),(46,41),(42,47),(37,50),(31,48),(27,42)])
 poly('L',[(28,34),(29,24),(31,19),(33,18),(34,21),(32,27),(32,34),(30,38),(28,37)])
 poly('D',[(34,29),(41,29),(45,33),(44,40),(41,46),(35,48),(31,43),(32,37)])
 # Far arm has an outward elbow and a slack, curled hand.
 poly('D',[(31,28),(35,31),(32,37),(28,41),(28,48),(30,51),(30,54),(28,55),(27,52),(26,55),(24,54),(25,50),(24,45),(24,40),(28,34)])
 # Near hind leg bends inward at the knee; both feet remain on the ground.
 poly('M',[(35,43),(41,44),(45,50),(43,55),(39,58),(40,64),(41,66),(47,67),(51,70),(46,70),(43,68),(41,71),(38,69),(36,69),(36,64),(36,59),(38,54),(36,50),(32,47)])
 poly('L',[(36,45),(39,45),(41,50),(41,53),(38,56),(37,55),(38,51),(36,49),(34,47)])
 poly('L',[(38,59),(39,58),(38,63),(39,66),(43,68),(39,68),(37,66)])
 # Near elbow is raised, while the forearm and three short claws hang loosely.
 poly('M',[(42,28),(46,30),(49,36),(48,41),(45,44),(46,49),(49,53),(49,56),(47,55),(46,52),(46,56),(44,57),(43,54),(42,56),(41,54),(42,50),(42,44),(44,39),(44,35),(40,32)])
 poly('L',[(43,31),(45,32),(47,36),(46,40),(44,43),(43,42),(45,38),(44,35)])
 poly('L',[(44,46),(45,46),(44,49),(46,52),(44,53),(43,50)])
 # One outline surrounds the complete composed drawing, no stamped roots.
 for x,y in list(g):
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   if (x+dx,y+dy) not in g:g[x+dx,y+dy]='K'
 line('K',[(30,31),(29,35),(26,40),(26,44)])
 line('K',[(31,43),(34,46),(37,49),(39,51),(39,53)])
 line('K',[(36,57),(35,61),(35,65)])
 line('K',[(41,34),(42,37),(41,41),(41,45)])
 line('K',[(27,50),(27,53)])
 line('K',[(44,52),(44,55)])
 line('K',[(42,68),(43,69)])
 # Preserve the user's complete mane, face and eyes, translated as one drawing.
 for (x,y),c in master.items():
  if x>=48 and y<=33:g[x-9,y]=c
 for yy in range(17,23):
  for xx in range(55,65):assert g.get((xx-9,yy))==master.get((xx,yy))
 return g

def frames():
 master=standing();out=[];breath=(0,0,-1,-1,-1,0,0,1,1,0);lean=(0,0,0,0,1,1,1,1,0,0);nod=(0,0,0,1,1,1,0,0,0,0);length=(3,4,5,6,7,8,8,6,4,3)
 for i in range(10):
  g={}
  for y in range(H):
   for x in range(W):
    head=x>=39 and y<=34;sx=x-lean[i] if head else x;sy=y-(breath[i] if y<58 else 0)-(nod[i] if head else 0)
    if (sx,sy) in master:g[x,y]=master[sx,sy]
  for x,y in list(g):
   if g[x,y]!='K':
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
     if (x+dx,y+dy) not in g:g[x+dx,y+dy]='K'
  x=51+lean[i];y=28+breath[i]+nod[i]
  for k in range(length[i]):
   q=x,y+k
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    if (q[0]+dx,q[1]+dy) not in g:g[q[0]+dx,q[1]+dy]='K'
   g[q]='M' if k==length[i]-1 else 'W'
  if i in (6,7,8):
   yy={6:37,7:40,8:43}[i];g[x,yy]='W';g[x,yy+1]='M'
   for q in ((x-1,yy),(x+1,yy),(x,yy-1),(x,yy+2)):
    if q not in g:g[q]='K'
  for p,c in master.items():
   if p[1]>=60:assert g[p]==c,('foot moved',i,p)
  assert all(0<x<W-1 and 0<y<H-1 for x,y in g)
  out.append(g)
 return out

def main():
 fs=frames();sp=importlib.util.spec_from_file_location('author83',HERE/'83_beast_of_barrisdale_design.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);d.W=W;d.H=H;d.PAL=PAL;d.STEP_MS=STEP
 strip=d.author(fs,'99_fad_felen_standing_draft');gif=[]
 for i in range(10):
  bg=Image.new('RGBA',(W,H),(25,25,25,255));bg.alpha_composite(strip.crop((i*W,0,(i+1)*W,H)));gif.append(bg.convert('RGB').resize((W*7,H*7),Image.Resampling.NEAREST))
 gif[0].save(HERE/'99_fad_felen_standing_preview.gif',save_all=True,append_images=gif[1:],duration=STEP,loop=0,disposal=2)
 (HERE/'99_fad_felen_standing_draft.json').write_text(json.dumps({'width':W,'height':H,'frame_ms':STEP,'palette':PAL,'frames':[[''.join(g.get((x,y),'.') for x in range(W)) for y in range(H)] for g in fs]},indent=2)+'\n')
 print('Standing second sheet: 10 frames, 1.8s loop, fixed hind feet, original eyes.')
if __name__=='__main__':main()
