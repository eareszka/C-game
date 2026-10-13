from pathlib import Path
import sys,json,shutil,datetime
from PIL import Image
r=Path.cwd();sys.path.insert(0,str(r/'art/direction'));from mcpc import Pixel
base=r/'art/enemies/99_fad_felen_frame0_draft';im=Image.open(r/'art/_work/99_readability_source.png').convert('RGBA');meta=json.loads(base.with_suffix('.json').read_text());pal=meta['palette'];rgb={c:tuple(bytes.fromhex(h)) for c,h in pal.items()};inv={v:k for k,v in rgb.items()};W,H=im.size
g={(x,y):inv[im.getpixel((x,y))[:3]] for y in range(H) for x in range(W) if im.getpixel((x,y))[3]};before=dict(g)
backup=r/'art/_backup'/('99_before_readability_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir();shutil.copy2(base.with_suffix('.aseprite'),backup/base.with_suffix('.aseprite').name)
def line(c,points):
 for (x0,y0),(x1,y1) in zip(points,points[1:]):
  n=max(abs(x1-x0),abs(y1-y0))
  for i in range(n+1):
   p=round(x0+(x1-x0)*i/max(1,n)),round(y0+(y1-y0)*i/max(1,n))
   if p in g:g[p]=c
def fill(c,spans,only='DML'):
 for y,x,n in spans:
  for xx in range(x,x+n):
   if g.get((xx,y)) in only:g[xx,y]=c
# Stronger near/far contrast: near planted arm and palm are lighter than
# the tucked far hind leg. Shading follows their tapered surfaces.
fill('M',[(32,49,3),(33,49,3),(34,50,3),(35,50,4),(36,51,3),(37,51,4),(38,52,4),(39,52,4),(40,53,4),(41,53,4),(42,54,5),(43,53,9),(44,53,14),(45,53,15),(46,56,12)])
fill('L',[(33,49,1),(34,50,1),(35,50,2),(36,51,1),(37,52,1),(38,52,2),(39,53,1),(40,54,1),(41,54,2),(42,55,2),(43,56,3),(44,56,5)])
# A broad near thigh/knee plane, rather than a narrow stripe.
fill('L',[(30,27,3),(31,28,4),(32,29,3),(33,30,2),(34,30,2),(35,29,3),(36,29,2),(40,30,2),(41,30,2),(42,30,2),(43,31,3),(44,32,4),(45,33,4)])
# Hanging claw gets a readable light palm against the belly.
fill('M',[(33,38,3),(34,38,4),(35,39,3),(36,39,3),(37,39,2),(38,39,2)])
fill('L',[(33,38,1),(34,39,1),(35,39,1)])
# Shared structural outlines mark the part boundaries, not extra texture.
line('K',[(22,28),(23,29),(24,29)])  # tail into haunch
line('K',[(26,28),(28,29),(30,30),(32,32),(32,34),(30,36)])
line('K',[(29,36),(28,39),(28,42),(29,44)]) # near shin against far leg
line('K',[(34,26),(34,29),(36,31),(38,33),(39,34)]) # hanging forearm
line('K',[(38,35),(38,37)])
line('K',[(40,31),(42,32),(44,32)]) # belly against planted arm
line('K',[(34,20),(36,22),(39,23),(40,25),(43,26),(45,27)]) # mane/body
line('K',[(51,17),(51,21),(52,23),(53,24)]) # mane/face border
line('K',[(59,44),(60,45),(61,46)])
line('K',[(64,44),(65,45),(66,46)])
line('K',[(34,45),(35,46),(36,47)])
# Preserve the full edited eye area byte-for-byte.
for y in range(17,23):
 for x in range(55,65):assert g.get((x,y))==before.get((x,y))
assert set(g)==set(before)
px=Pixel()
try:
 source=px.call('create_canvas',width=W,height=H,color_mode='rgb')['file_path'];px.call('set_palette',sprite_path=source,colors=['#'+h for h in pal.values()])
 pixels=[{'x':x,'y':y,'color':'#'+pal[c]} for (x,y),c in g.items()]
 for at in range(0,len(pixels),800):px.call('draw_pixels',sprite_path=source,layer_name='Layer 1',frame_number=1,pixels=pixels[at:at+800])
 px.call('save_as',sprite_path=source,output_path=str(base.with_suffix('.aseprite')).replace('\\','/'))
 px.call('export_sprite',sprite_path=str(base.with_suffix('.aseprite')).replace('\\','/'),output_path=str(base.with_suffix('.png')).replace('\\','/'),format='png',frame_number=1)
finally:px.p.terminate()
final=Image.open(base.with_suffix('.png')).convert('RGBA');assert all(final.getpixel(p)==(*rgb[c],255) for p,c in g.items())
for y in range(17,23):
 for x in range(55,65):assert final.getpixel((x,y))==im.getpixel((x,y))
meta['frame0']=[''.join(g.get((x,y),'.') for x in range(W)) for y in range(H)];base.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print('Readability pass:',sum(g[p]!=before[p] for p in g),'pixels; eyes and silhouette preserved.')
