from pathlib import Path
import sys,json,shutil,datetime
from PIL import Image
r=Path.cwd();sys.path.insert(0,str(r/'art/direction'));from mcpc import Pixel
base=r/'art/enemies/99_fad_felen_frame0_draft';backup=r/'art/_backup'/('99_user_eyes_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir()
shutil.copy2(base.with_suffix('.aseprite'),backup/base.with_suffix('.aseprite').name)
user=Image.open(r/'art/_work/99_user_eyes.png').convert('RGBA');user.save(r/'art/enemies/99_fad_felen_user_eyes.png')
meta=json.loads(base.with_suffix('.json').read_text());pal=meta['palette'];rgb={c:tuple(bytes.fromhex(h)) for c,h in pal.items()};inv={v:k for k,v in rgb.items()};W,H=user.size
g={(x,y):inv[user.getpixel((x,y))[:3]] for y in range(H) for x in range(W) if user.getpixel((x,y))[3]}
original=dict(g)
def stroke(c,points):
 for x,y in points:
  assert (x,y) in g,('outside silhouette',x,y)
  g[x,y]=c
# One broad gold highlight follows the mane's sweep; no strands or hatching.
stroke('y',[(34,15),(35,16),(35,17),(36,17),(36,18),(37,18),(38,19),(39,19),(40,20),(41,20),(42,20),(43,20),(44,20),(45,19)])
# A single shadow at the lower near edge of the mane.
stroke('d',[(66,23),(66,24),(65,25),(65,26),(64,27),(64,28),(63,29),(62,30),(61,31)])
# Small cheek and jaw planes, without skull cracks or realistic bone detail.
stroke('M',[(54,24),(54,25),(55,26),(56,28)])
stroke('L',[(58,28),(59,28),(60,28),(61,28),(59,29),(60,29)])
# Two restrained structural bends under the shoulder and at the near hip.
stroke('K',[(31,22),(32,22),(33,23),(34,24)])
stroke('D',[(28,27),(29,27),(30,28),(31,28)])
# Form-based forearm highlight tapers toward the wrist.
stroke('M',[(49,33),(50,33),(50,34),(51,34),(50,35),(51,35),(51,36),(52,36),(52,37),(52,38),(53,38),(53,39),(54,40),(54,41),(55,42),(56,42),(57,43)])
stroke('M',[(26,36),(26,37),(26,38),(25,39),(25,40),(25,41),(25,42)])
# A shared finger division makes the dangling hand readable, with no knuckles.
stroke('K',[(38,35),(38,36),(38,37)])
for y in range(17,23):
 for x in range(55,65):assert g.get((x,y))==original.get((x,y)),('user eye altered',x,y)
assert set(g)==set(original),'Silhouette changed'
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
 for x in range(55,65):assert final.getpixel((x,y))==user.getpixel((x,y))
meta['frame0']=[''.join(g.get((x,y),'.') for x in range(W)) for y in range(H)];base.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
print(sum(g[p]!=original[p] for p in g),'pixels refined; edited eyes and complete silhouette preserved.')
