from pathlib import Path
import sys,json,shutil
r=Path.cwd();sys.path.insert(0,str(r/'art/direction'));from mcpc import Pixel
W,H=76,52
PAL={'K':'000000','D':'595965','M':'9797aa','L':'e8e0c0','d':'876a1f','Y':'c9a433','y':'f0e880','W':'fcfcfc'}
g={}
def poly(c,points):
 for yy in range(H):
  for xx in range(W):
   x,y=xx+0.5,yy+0.5;inside=False
   for a,b in zip(points,points[1:]+points[:1]):
    if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
   if inside:g[xx,yy]=c
def line(c,pts):
 for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
  n=max(abs(x1-x0),abs(y1-y0))
  for i in range(n+1):g[round(x0+(x1-x0)*i/max(1,n)),round(y0+(y1-y0)*i/max(1,n))]=c
# Compose one flat silhouette; overlapping roots share a fill and no seams.
poly('D',[(29,25),(39,28),(35,34),(30,40),(29,44),(36,45),(37,47),(25,47),(24,44),(25,36)])
poly('D',[(45,23),(52,27),(53,33),(57,41),(63,43),(68,44),(70,47),(65,47),(61,45),(61,48),(58,47),(56,45),(53,47),(50,46),(52,42),(49,37),(44,31)])
poly('M',[(24,23),(23,28),(17,33),(11,33),(7,31),(5,27),(5,22),(7,27),(9,29),(13,30),(18,28),(23,24)])
poly('M',[(20,27),(22,21),(25,13),(28,9),(32,8),(37,12),(41,17),(50,21),(51,29),(47,33),(39,36),(32,36),(25,33)])
poly('D',[(29,26),(34,24),(42,28),(48,27),(47,32),(39,36),(31,33)])
poly('L',[(23,24),(27,15),(30,11),(32,11),(34,14),(30,20),(29,26),(26,30),(23,29)])
poly('M',[(25,29),(31,28),(37,32),(36,36),(32,41),(33,44),(40,45),(43,47),(38,48),(35,46),(33,49),(31,47),(28,47),(28,42),(30,36),(25,33)])
poly('L',[(26,29),(29,29),(33,32),(33,35),(29,37),(30,34),(26,32)])
poly('L',[(31,39),(33,38),(31,43),(32,45),(38,46),(32,46),(30,45)])
poly('M',[(34,22),(38,23),(38,29),(42,34),(42,37),(40,40),(38,39),(38,36),(36,39),(35,37),(36,34),(34,29)])
poly('L',[(35,23),(37,25),(36,29),(40,34),(40,36),(38,34),(35,30)])
# Mane is three broad shapes, with just three silhouette tufts.
poly('Y',[(31,10),(37,14),(43,17),(48,16),(50,11),(53,9),(54,7),(56,9),(60,8),(63,6),(63,10),(66,9),(68,13),(69,17),(68,26),(65,32),(62,33),(58,32),(54,34),(49,31),(46,29),(44,26),(40,27),(39,24),(37,25),(35,21),(33,19)])
poly('d',[(33,13),(37,17),(44,21),(48,18),(49,25),(52,29),(51,32),(48,30),(45,26),(42,26),(39,22),(36,22)])
poly('y',[(51,14),(53,12),(58,11),(63,11),(66,14),(65,18),(62,16),(60,14),(57,15),(53,18),(51,24),(50,20)])
# Broad mask-like hag face, no skull cracks, eye sockets or individual bones.
poly('M',[(54,17),(57,15),(61,16),(65,19),(65,25),(62,29),(59,31),(55,28),(53,24)])
poly('L',[(57,17),(60,17),(63,19),(64,23),(62,27),(59,28),(56,25),(56,21)])
# Outline only once around the completed body, then sparse shared part lines.
for x,y in list(g):
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  if (x+dx,y+dy) not in g:g[x+dx,y+dy]='K'
line('K',[(27,29),(30,30),(32,32),(32,34)])
line('K',[(35,24),(34,27),(35,30),(37,32)])
line('K',[(46,27),(48,29),(49,32)])
line('K',[(53,19),(53,23),(55,26),(57,29),(60,30),(63,28),(65,25)])
line('K',[(55,25),(57,26),(62,26),(64,24)])
for x in (56,61):
 g[x,20]='W';g[x+1,20]='K';g[x,21]='W';g[x+1,21]='W'
g[59,23]='K'
for x in range(57,63):g[x,27]='y'
g[59,27]='K';g[62,27]='K'
# Keep toes simple: three short silhouette notches, no knuckle texture.
line('K',[(36,46),(37,47)])
line('K',[(60,45),(61,46)])
base=r/'art/enemies/99_fad_felen_frame0_draft'
backup=r/'art/_backup/99_detailed_first';backup.mkdir(exist_ok=True)
for suffix in ('.aseprite','.png','.json'):
 p=base.with_suffix(suffix)
 if p.exists() and not (backup/p.name).exists():shutil.copy2(p,backup/p.name)
px=Pixel()
try:
 source=px.call('create_canvas',width=W,height=H,color_mode='rgb')['file_path'];px.call('set_palette',sprite_path=source,colors=['#'+c for c in PAL.values()])
 pixels=[{'x':x,'y':y,'color':'#'+PAL[c]} for (x,y),c in g.items()]
 for at in range(0,len(pixels),800):px.call('draw_pixels',sprite_path=source,layer_name='Layer 1',frame_number=1,pixels=pixels[at:at+800])
 px.call('save_as',sprite_path=source,output_path=str(base.with_suffix('.aseprite')).replace('\\','/'))
 px.call('export_sprite',sprite_path=str(base.with_suffix('.aseprite')).replace('\\','/'),output_path=str(base.with_suffix('.png')).replace('\\','/'),format='png',frame_number=1)
finally:px.p.terminate()
base.with_suffix('.json').write_text(json.dumps({'palette':PAL,'width':W,'height':H,'frame0':[''.join(g.get((x,y),'.') for x in range(W)) for y in range(H)]},indent=2)+'\n')
print('Simplified native redraw saved:',len(g),'pixels',len(set(g.values())),'colors')
