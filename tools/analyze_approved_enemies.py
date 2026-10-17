"""Read-only enemy style study and native-pixel reference boards for PixelLab."""
from pathlib import Path
import sys,json,re,hashlib,statistics
from collections import Counter
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
SPRITES=Path('C:/Users/emery/.herdr/worktrees/C-game/sprites')
OUT=ROOT/'art/direction/approved_enemy_study'
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'art/direction'));sys.path.append(str(SPRITES/'tools'))
import style_check as sc
sc.ROOT=str(ROOT)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def metrics(im):
 colors=Counter(c for c in im.getdata() if c[3])
 opaque=sum(colors.values());black=sum(n for c,n in colors.items() if c[:3]==(0,0,0));px=im.load();w,h=im.size
 edge=blackedge=soft=0
 for y in range(h):
  for x in range(w):
   c=px[x,y]
   if 0<c[3]<255:soft+=1
   if not c[3]:continue
   if any(not (0<=x+dx<w and 0<=y+dy<h) or not px[x+dx,y+dy][3] for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))):
    edge+=1;blackedge+=c[:3]==(0,0,0)
 return dict(canvas=[w,h],occupied_bounds=list(im.getbbox()) if im.getbbox() else None,opaque_pixels=opaque,colors=len(colors),soft_alpha_pixels=soft,black_fraction=round(black/max(1,opaque),4),black_edge_fraction=round(blackedge/max(1,edge),4),interior_black_fraction=round((black-blackedge)/max(1,opaque),4),palette=['#%02x%02x%02x'%c[:3] for c,n in colors.most_common()])

def pack(entries,path,max_width=1024):
 # Native pixels only: crop transparent padding, never scale a source.
 ordered=sorted(entries,key=lambda e:(-e['image'].height,-e['image'].width,e['id']))
 x=y=row_h=0;placements=[]
 for e in ordered:
  im=e['image']
  if x+im.width+8>max_width:x=0;y+=row_h+8;row_h=0
  placements.append((e,x+4,y+4));x+=im.width+8;row_h=max(row_h,im.height)
 height=y+row_h+8;board=Image.new('RGBA',(max_width,height));mapping=[]
 for e,x,y in placements:
  board.paste(e['image'],(x,y))
  mapping.append(dict(id=e['id'],name=e['name'],view=e['view'],rect=[x,y,e['image'].width,e['image'].height]))
 board.save(path)
 return dict(image=path.name,size=list(board.size),native_pixels=True,placements=mapping)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 status_path=ROOT/'art/enemies/redraw_status.json';status=json.loads(status_path.read_text());ids=sorted(set(status['done']+status['reference']+status['fine']['ids']))
 names=re.findall(r'"([^"]+)"',sc.ets.table('src/main.cpp','ENEMY_NAMES[] = {'))
 record=[];fronts=[];angles=[];protected={str(status_path.relative_to(ROOT)):sha(status_path)};palette=Counter();sheet_count=frame_count=0
 for i in ids:
  enemy=dict(id=i,name=names[i],approval='REF' if i in status['reference'] else 'DONE' if i in status['done'] else 'OK',tier=sc.tier_of(i),direction_class=sc.direction_class(i),sheets=[])
  definitions=sc.enemy_sheets(i);base_rows=definitions[0][2]
  for path,frames,rows,kind in definitions:
   # The old checker assumes a horizontal flap sheet. The actual renderer
   # uses es.rows for flap too (battle.cpp), so respect the current layout.
   if kind=='flap':rows=base_rows
   source=ROOT/path;protected[path]=sha(source);im=Image.open(source).convert('RGBA')
   assert im.width%(frames if rows else 8*frames)==0 and (not rows or im.height%8==0),(path,'layout')
   colors=im.getcolors(im.width*im.height);opaque=sum(n for n,c in colors if c[3]);soft=sum(n for n,c in colors if 0<c[3]<255)
   off=sum(n for n,c in colors if c[3] and c[:3] not in sc.PALETTE)
   palette.update({c[:3]:n for n,c in colors if c[3]})
   first=sc.frame(im,frames,rows,0,0)
   views=[]
   for d,label in enumerate(sc.ORDER):
    f0=sc.frame(im,frames,rows,d,0);views.append(dict(view=label,**metrics(f0)))
    if kind=='idle' and label in ('D','DR','R') and f0.getbbox():
     cropped=f0.crop(f0.getbbox());entry=dict(id=i,name=names[i],view=label,image=cropped)
     (fronts if label=='D' else angles).append(entry)
     f0.save(OUT/f'{i:02d}_{label}_frame0.png')
   enemy['sheets'].append(dict(path=path,kind=kind,layout='rows' if rows else 'horizontal',sheet_size=list(im.size),frames_per_direction=frames,stored_cels=8*frames,unique_stored_cels=len({sc.frame(im,frames,rows,d,f).tobytes() for d in range(8) for f in range(frames)}),opaque_pixels=opaque,soft_alpha_pixels=soft,off_palette_pixels=off,palette_count=sum(1 for n,c in colors if c[3]),views=views))
   sheet_count+=1;frame_count+=8*frames
  record.append(enemy)
 # Include directly attached renderer parts, bullets and marks in the census,
 # without pretending they share an eight-direction enemy-sheet layout.
 extras=[]
 rows=re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',sc.ets.table('src/battle.cpp','ENEMY_SHEETS[] = {'))
 for i in ids:
  a=sc.row_args(rows[i])+[None]*12
  for index,kind in ((6,'log'),(9,'marks'),(11,'parts')):
   if not a[index]:continue
   path=a[index];source=ROOT/path
   if not source.is_file():continue
   protected[path]=sha(source);im=Image.open(source).convert('RGBA');colors=im.getcolors(im.width*im.height)
   extras.append(dict(id=i,path=path,kind=kind,canvas=list(im.size),palette_count=sum(1 for n,c in colors if c[3]),soft_alpha_pixels=sum(n for n,c in colors if 0<c[3]<255),off_palette_pixels=sum(n for n,c in colors if c[3] and c[:3] not in sc.PALETTE)))
 boards=[pack(fronts,OUT/'approved_fronts_native.png'),pack(angles,OUT/'approved_angles_native.png')]
 # A labeled, enlarged overview for the human review, not for model input.
 cell_w,cell_h=252,250;cols=7;overview=Image.new('RGB',(cols*cell_w,6*cell_h),(43,43,51));draw=ImageDraw.Draw(overview);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
 for j,e in enumerate(sorted(fronts,key=lambda e:e['id'])):
  x=cell_w*(j%cols);y=cell_h*(j//cols);im=e['image'];factor=max(1,min(6,220//im.width,210//im.height))
  # The rare >220px-wide approved giant retains native pixels in its own
  # full-canvas export; this contact overview shrinks it for display only.
  size=(im.width*factor,im.height*factor)
  if size[0]>240 or size[1]>214:
   ratio=min(240/im.width,214/im.height);size=(int(im.width*ratio),int(im.height*ratio))
  zoom=im.resize(size,Image.Resampling.NEAREST);overview.paste(zoom,(x+(cell_w-zoom.width)//2,y+8+(212-zoom.height)//2),zoom)
  draw.text((x+8,y+226),f"{e['id']:02d} {e['name']}",font=font,fill=(168,240,188) if e['id'] in status['reference'] else 'white')
 overview.save(OUT/'approved_42_labeled_overview.png')
 assert all(sha(ROOT/path)==digest for path,digest in protected.items())
 study=dict(approval_source=str(status_path.relative_to(ROOT)),approved_count=len(ids),status_counts=dict(DONE=len(status['done']),REF=len(status['reference']),OK=len(status['fine']['ids'])),enemy_sheet_count=sheet_count,stored_cels_analyzed=frame_count,attached_assets=extras,bible_sources=['art/direction/ART_DIRECTION.md',str(SPRITES/'art/direction/SPRITE_STYLE.md')],ro_exception=dict(outline='red rather than black',skin='black with restrained charcoal form shading',appearance='demonic',canvas=[130,81]),boards=boards,enemy_records=record,global_used_colors=['#%02x%02x%02x'%c for c,n in palette.most_common()],source_sha256=protected,source_assets_unchanged=True,paid_generation_calls=0)
 (OUT/'analysis.json').write_text(json.dumps(study,indent=2)+'\n')
 print(json.dumps(dict(approved=len(ids),sheets=sheet_count,cels=frame_count,attached=len(extras),boards=[b['size'] for b in boards],soft_alpha_sheets=[s['path'] for e in record for s in e['sheets'] if s['soft_alpha_pixels']],off_palette_sheets=[s['path'] for e in record for s in e['sheets'] if s['off_palette_pixels']],sources_unchanged=True),indent=2),flush=True)

if __name__=='__main__':main()
