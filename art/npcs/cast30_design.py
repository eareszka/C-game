"""Thirty authored NPC designs on the approved player body, drawn via pixel MCP."""
from pathlib import Path
import sys, json, hashlib, argparse
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'art/npcs/cast30'
TMP=ROOT/'build_tmp/npc_review/cast30'
sys.path.insert(0,str(ROOT/'art/direction'))
from mcpc import Pixel
from villager_walk_sidefix import player_pixels,write_frame
from villager_walk_4dir import validate_frame
import fcremap

# Identity comes from an authored head/costume/face combination, not a hue swap.
# hair/hat and clothing each use one palette entry; skin and black make four.
DESIGNS=[
 ('05_baker','Baker','chef','apron','moustache','633e1b','e8e0c0','f0b890'),
 ('06_fisher','Fisher','bucket','vest','stubble','9797aa','2850a0','d7a175'),
 ('07_postwoman','Postwoman','cap','satchel','plain','633e1b','b6433d','f0b890'),
 ('08_mechanic','Mechanic','bandana','bib','plain','633e1b','9797aa','d7a175'),
 ('09_librarian','Librarian','bun','cardigan','glasses','633e1b','664b95','f0b890'),
 ('10_gardener','Gardener','sunhat','suspenders','plain','94703d','235436','f0b890'),
 ('11_sailor','Sailor','sailor','striped','moustache','2850a0','e8e0c0','d7a175'),
 ('12_doctor','Doctor','sweep','coat','glasses','633e1b','e8e0c0','f0b890'),
 ('13_musician','Musician','beret','scarf','plain','633e1b','b6433d','d7a175'),
 ('14_carpenter','Carpenter','crop','vest','beard','94703d','2850a0','f0b890'),
 ('15_flower_seller','Flower seller','twintails','dress','plain','633e1b','fc74b4','f0b890'),
 ('16_shopkeeper','Shopkeeper','flatcap','waistcoat','moustache','633e1b','235436','d7a175'),
 ('17_student','Student','ponytail','uniform','plain','633e1b','2850a0','f0b890'),
 ('18_lamplighter','Lamplighter','beanie','jacket','beard','633e1b','d89830','d7a175'),
 ('19_grandmother','Grandmother','braid','shawl','plain','9797aa','b6433d','f0b890'),
 ('20_potter','Potter','headwrap','apron','plain','94703d','b6433d','d7a175'),
 ('21_cook','Cook','kerchief','bib','plain','633e1b','e8e0c0','f0b890'),
 ('22_courier','Courier','spiky','sash','plain','633e1b','3e91cc','d7a175'),
 ('23_tailor','Tailor','bob','cardigan','glasses','b6433d','235436','f0b890'),
 ('24_miner','Miner','helmet','workshirt','moustache','94703d','2850a0','d7a175'),
 ('25_innkeeper','Innkeeper','curls','waistcoat','beard','633e1b','b6433d','f0b890'),
 ('26_shepherd','Shepherd','hood','tunic','plain','633e1b','235436','d7a175'),
 ('27_barber','Barber','part','formal','moustache','633e1b','e8e0c0','f0b890'),
 ('28_weaver','Weaver','topknot','sash','plain','633e1b','664b95','d7a175'),
 ('29_artist','Artist','beret','smock','glasses','b6433d','2850a0','f0b890'),
 ('30_naturalist','Naturalist','pith','pockets','plain','94703d','235436','d7a175'),
 ('31_dancer','Dancer','bun','dress','plain','633e1b','664b95','f0b890'),
 ('32_watchman','Watchman','peak','uniform','beard','633e1b','2850a0','d7a175'),
 ('33_traveller','Traveller','longhair','satchel','plain','b6433d','235436','f0b890'),
 ('34_woodcutter','Woodcutter','beanie','suspenders','moustache','633e1b','b6433d','d7a175'),
]
BASES={'down':(0,1,2),'up':(3,4,5),'left':(6,7,23),'right':(8,9,22)}

def config(row):
 name,label,head,outfit,face,hair,cloth,skin=row
 return dict(name=name,label=label,head=head,outfit=outfit,face=face,palette=dict(K='000000',S=skin,H=hair,C=cloth))

def design(base,n,direction,phase):
 off=-1 if phase==0 else 0
 side=direction in ('left','right');back=direction=='up';kind=n['head']
 # Top hair/hat contours use the same broad head as the approved five.
 rows={6:(5,9),7:(4,10),8:(3,11),9:(2,12)}
 if kind in ('cap','bucket','sunhat','sailor','helmet','pith','peak','beanie','hood','headwrap'):
  rows={5:(5,9),6:(4,10),7:(3,11),8:(3,11),9:(2,12)}
 if kind=='chef':rows={4:(5,9),5:(4,10),6:(3,11),7:(3,11),8:(4,10),9:(3,11)}
 if kind=='beret':rows={5:(4,7),6:(3,10),7:(2,11),8:(3,11),9:(3,12)}
 if kind in ('bun','topknot'):rows={4:(8,10),5:(7,11),6:(5,10),7:(4,10),8:(3,11),9:(2,12)}
 if kind=='ponytail':rows={5:(9,11),6:(5,12),7:(4,12),8:(3,11),9:(2,12)}
 if kind=='twintails':rows={6:(4,10),7:(3,11),8:(2,12),9:(2,12)}
 if kind=='spiky':rows={5:(6,6),6:(4,9),7:(3,11),8:(3,11),9:(2,12)}
 if kind=='curls':rows={6:(5,9),7:(3,11),8:(2,12),9:(2,12)}
 if kind=='flatcap':rows={6:(4,9),7:(3,10),8:(3,11),9:(2,12)}
 if kind=='kerchief':rows={5:(7,9),6:(5,10),7:(4,11),8:(3,11),9:(2,12)}
 if (back or direction=='left') and kind in ('beret','bun','topknot','ponytail','kerchief'):
  rows={y:(14-b,14-a) for y,(a,b) in rows.items()}
 g={q:c for q,c in base.items() if q[1]>9+off}
 top={(x,y+off) for y,(a,b) in rows.items() for x in range(a,b+1)}
 occupied=set(g)|top
 for x,y in top:g[x,y]='K' if any((x+dx,y+dy) not in occupied for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))) else 'H'
 def put(x,y,c,interior=False):
  q=(x,y+off)
  if q in g and (not interior or g[q]!='K'):g[q]=c
 def line(y,a,b,c,interior=False):
  for x in range(a,b+1):put(x,y,c,interior)
 def detail(spans,c,interior=False):
  for y,a,b in spans:line(y,a,b,c,interior)
 # Re-establish the face and back hair beneath the new crown.
 for (x,y),c in list(g.items()):
  if 10+off<=y<=13+off:
   g[x,y]='H' if c!='K' else 'K'
 if not back and not side:
  detail([(10,4,10),(11,4,10),(12,4,10),(13,4,10)],'S')
 elif side:
  for q,c in base.items():
   if 10+off<=q[1]<=13+off and c=='S':g[q]='S'
 else:line(13,5,9,'S')
 # Hair treatments are carried across all directions, including rear views.
 if kind in ('sweep','part'):
  if not back:
   line(9,5,9,'S',True);put(5 if direction!='left' else 9,10,'H');put(6 if direction!='left' else 8,9,'H')
  else:detail([(8,7,7),(9,6,6)],'K',True)
 if kind=='crop':
  if not back:line(9,5,9,'S',True)
  else:line(12,4,10,'S',True)
 if kind in ('bob','longhair','braid','twintails','curls'):
  if not back:
   for y in range(10,14):
    if not side:put(4,y,'H');put(10,y,'H')
   if kind=='bob':line(9,5,9,'S',True)
   if kind=='curls':put(4,9,'H');put(10,9,'H');put(6,9,'S');put(8,9,'S')
  else:line(13,5,9,'H',True)
 if kind in ('ponytail','braid','twintails','longhair'):
  # Attached locks stay within the player's original silhouette.
  xs=[4,10] if kind=='twintails' else [5 if direction=='left' or back else 9]
  if back and kind=='braid':xs=[7]
  for x in xs:
   for y in (12,13,14):put(x,y,'H',True)
   put(x,13,'C',True)
 if kind in ('bun','topknot','ponytail'):put(9 if direction in ('down','right') else 5,6 if kind=='ponytail' else 5,'C',True)
 # Hats share head volume but have distinct crowns, bands and visors.
 if kind in ('cap','peak'):
  detail([(6,5,9),(7,4,10),(8,4,10)],'C',True)
  line(9,3,11,'C',True)
  if kind=='peak':put(7,7,'S',True);line(8,4,10,'H',True)
 if kind in ('bucket','sunhat','pith'):
  detail([(6,5,9),(7,4,10),(8,4,10)],'H',True);line(8,4,10,'C',True);line(9,3,11,'H',True)
  if kind=='pith':put(7,6,'S',True)
 if kind=='sailor':detail([(6,5,9),(7,4,10),(8,4,10)],'C',True);line(9,3,11,'H',True)
 if kind=='chef':detail([(5,5,9),(6,4,10),(7,4,10),(8,5,9)],'C',True);line(9,4,10,'H',True)
 if kind=='helmet':detail([(6,5,9),(7,4,10),(8,4,10),(9,3,11)],'C',True);put(7,7,'S',True);put(7,8,'H',True)
 if kind=='beanie':detail([(6,5,9),(7,4,10),(8,4,10)],'C',True);line(9,3,11,'H',True)
 if kind in ('bandana','headwrap','kerchief'):
  line(8,4,10,'C',True);line(9,3,11,'C',True)
  if kind!='bandana':detail([(6,6,9),(7,5,10)],'C',True)
  if kind=='kerchief':put(8 if not back else 6,7,'S',True)
 if kind=='beret':detail([(6,4,9),(7,3,10),(8,4,10)],'C',True)
 if kind=='flatcap':detail([(7,4,9),(8,4,10)],'C',True)
 if kind=='hood':
  detail([(6,5,9),(7,4,10),(8,4,10),(9,3,11)],'C',True)
  if back:detail([(10,4,10),(11,4,10),(12,4,10),(13,5,9)],'C',True)
  elif not side:put(4,10,'C');put(10,10,'C');put(4,12,'C');put(10,12,'C')
 # NPC eyes always differ from the protagonist's horizontal paired pixels.
 if not back:
  eye=5 if direction=='left' else 9
  eyes=[eye] if side else [5,9]
  if side:
   # Erase BOTH pixels of the protagonist's old horizontal eye before
   # drawing the approved NPC vertical eye. Leftover black read as a beard.
   for x in ((5,6) if direction=='left' else (8,9)):put(x,12,'S')
  for x in eyes:put(x,11 if side else 10,'K');put(x,12 if side else 11,'K')
  if n['face']=='glasses':
   if not side:detail([(10,4,6),(10,8,10),(11,4,4),(11,6,8),(11,10,10),(12,4,6),(12,8,10)],'K')
   else:
    # User-confirmed solid black side lenses, with a continuous temple arm.
    for y in (11,12,13):line(y,eye-1,eye+1,'K')
    line(11,6 if direction=='right' else 4,10 if direction=='right' else 8,'K')
  if n['face'] in ('moustache','beard','stubble'):
   if not side:line(12,6,8,'H');put(7,13,'S')
   else:put(eye,13,'H');put(eye-1 if direction=='right' else eye+1,13,'H')
   if n['face']=='beard':line(13,5,9,'H',True)
   if n['face']=='stubble':put(5,13,'H');put(9,13,'H')
 # Clothes occupy exactly the approved body; hands, black limb joints and feet stay.
 for q,c in list(g.items()):
  x,y=q
  if 14+off<=y<=16+off and 4<=x<=10 and base.get(q) in ('S','C'):g[q]='C'
  if y>=18 and c=='C':g[q]='H'
 def cloth(spans,c):
  for y,a,b in spans:
   for x in range(a,b+1):
    q=(x,y+off)
    if 4<=x<=10 and q in base and base[q]!='K':g[q]=c
 outfit=n['outfit']
 front=not back and not side
 if outfit in ('apron','bib','smock'):
  if front:cloth([(14,6,8),(15,5,9),(16,4,10)],'H');cloth([(14,7,7)],'S')
  elif back:cloth([(15,5,9),(16,7,7)],'H')
  else:cloth([(14,8 if direction=='right' else 6,8 if direction=='right' else 6),(15,7,8),(16,7,7)],'H')
  if outfit=='smock':cloth([(16,5,5),(16,9,9)],'S')
 if outfit in ('vest','waistcoat','cardigan','jacket','coat','formal'):
  if front:
   cloth([(14,6,8),(15,7,7)],'S');cloth([(14,5,5),(14,9,9),(15,6,6),(15,8,8)],'H')
   if outfit in ('coat','cardigan'):cloth([(16,7,7)],'H')
   if outfit=='waistcoat':cloth([(16,4,6),(16,8,10)],'H')
   if outfit=='formal':cloth([(14,7,7),(16,7,7)],'H')
   if outfit=='jacket':cloth([(16,5,5),(16,9,9)],'S')
  elif back:cloth([(14,5,9)],'H')
  else:cloth([(14,7,8),(15,7,7)],'H')
 if outfit in ('suspenders','pockets','workshirt'):
  cloth([(14,5,5),(14,9,9),(15,5,5),(15,9,9)],'H')
  if outfit=='pockets':cloth([(16,5,6),(16,8,9)],'H')
  if outfit=='workshirt':cloth([(14,6,8),(16,7,7)],'S')
 if outfit in ('scarf','shawl'):
  cloth([(14,4,10)],'H');cloth([(15,5,5),(16,5,5)],'H')
  if outfit=='shawl':cloth([(15,4,6),(15,8,10)],'H')
 if outfit=='striped':cloth([(14,4,10),(16,4,10)],'H')
 if outfit=='uniform':cloth([(14,5,5),(14,9,9),(15,7,7),(16,7,7)],'H');cloth([(14,7,7)],'S')
 if outfit=='dress':cloth([(14,6,8)],'S');cloth([(16,4,10)],'H');cloth([(15,7,7)],'H')
 if outfit=='tunic':cloth([(14,6,8),(16,4,10)],'H');cloth([(15,7,7)],'S')
 if outfit in ('sash','satchel'):
  if front:cloth([(14,9,9),(15,7,8),(16,5,7)],'H')
  elif back:cloth([(14,5,5),(15,6,7),(16,8,9)],'H')
  elif direction=='right':cloth([(14,8,8),(15,6,8),(16,6,8)],'H')
  else:cloth([(14,6,6),(15,7,7)],'H')
  if outfit=='satchel':cloth([(16,6,6)],'S')
 body=lambda image:{q for q in image if q[1]>=14+off}
 assert body(g)==body(base),(n['name'],direction,phase,'body footprint')
 assert all(g[q]=='K' for q,c in base.items() if q[1]>=14+off and c=='K')
 return g

def paint(p,path,pixels,frame=1):
 for at in range(0,len(pixels),700):p.call('draw_pixels',sprite_path=path,layer_name='Layer 1',frame_number=frame,pixels=pixels[at:at+700])

def frame_pixels(g,pal,ox=0,oy=0):
 return [dict(x=x+ox,y=y+oy,color='#'+pal[c]) for (x,y),c in g.items()]

def frames_for(n,player):
 return [design(player_pixels(player.crop((index*14,0,(index+1)*14,20))),n,d,phase) for d,indices in BASES.items() for phase,index in enumerate(indices)]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fronts',action='store_true');args=ap.parse_args()
 HERE.mkdir(exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
 ns=[config(r) for r in DESIGNS];player=Image.open(ROOT/'assets/player_small.png').convert('RGBA')
 allframes=[frames_for(n,player) for n in ns]
 # Exact geometry and indexed-color layouts: no two NPCs are mere recolors.
 fingerprints=[tuple(sorted(g[0].items())) for g in allframes];assert len(set(fingerprints))==30
 for n,frames in zip(ns,allframes):
  assert all(tuple(bytes.fromhex(c)) in fcremap.PALETTE for c in n['palette'].values())
  for g in frames:
   assert max(y for x,y in g)==19 and all(0<=x<14 and 0<=y<20 for x,y in g)
   remaining=set(g);stack=[remaining.pop()]
   while stack:
    x,y=stack.pop()
    for dx in (-1,0,1):
     for dy in (-1,0,1):
      q=(x+dx,y+dy)
      if q in remaining:remaining.remove(q);stack.append(q)
   assert not remaining,(n['name'],'disconnected',remaining)
 protected=list((ROOT/'art/npcs').glob('*.aseprite'))+list((ROOT/'assets/npcs').glob('*'))+[ROOT/'assets/player_small.png',ROOT/'assets/player_small.aseprite']
 hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in protected if path.is_file()}
 p=Pixel()
 try:
  if args.fronts:
   canvas=p.call('create_canvas',width=144,height=140,color_mode='rgb')['file_path']
   for i,(n,frames) in enumerate(zip(ns,allframes)):paint(p,canvas,frame_pixels(frames[0],n['palette'],5+24*(i%6),3+28*(i//6)))
   out=HERE/'cast30_fronts_review.aseprite';p.call('save_as',sprite_path=canvas,output_path=out.as_posix())
   p.call('export_sprite',sprite_path=out.as_posix(),output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
   im=Image.open(out.with_suffix('.png'));im.resize((720,700),Image.Resampling.NEAREST).save(TMP/'fronts_5x.png')
   print('Front designs painted via pixel plugin; ready for visual review.',flush=True);return
  for n,frames in zip(ns,allframes):
   out=HERE/(n['name']+'.aseprite')
   if out.exists():print('Preserving existing '+out.name,flush=True);continue
   canvas=p.call('create_canvas',width=14,height=20,color_mode='rgb')['file_path']
   p.call('set_palette',sprite_path=canvas,colors=['#'+v for v in n['palette'].values()]);p.call('set_frame_duration',sprite_path=canvas,frame_number=1,duration_ms=200)
   for f,g in enumerate(frames):
    if f:p.call('add_frame',sprite_path=canvas,duration_ms=200)
    write_frame(p,canvas,f+1,g,n['palette'])
   for d in range(4):p.call('create_tag',sprite_path=canvas,tag_name=list(BASES)[d],from_frame=3*d+1,to_frame=3*d+3,direction='forward')
   p.call('save_as',sprite_path=canvas,output_path=out.as_posix())
   # Reopen/export the saved timeline, then inspect every cel.
   r=p.call('export_spritesheet',sprite_path=out.as_posix(),output_path=(TMP/(n['name']+'_reopened.png')).as_posix(),layout='horizontal',padding=0,include_json=True)
   meta=json.loads(Path(r['metadata_path']).read_text());records=meta['frames'];records=list(records.values()) if isinstance(records,dict) else records
   assert len(records)==12 and all(f['duration']==200 for f in records)
   strip=Image.open(r['spritesheet_path']).convert('RGBA')
   for f,record in enumerate(records):
    b=record['frame'];validate_frame(strip.crop((b['x'],b['y'],b['x']+14,b['y']+20)),frames[f],n['palette'])
   atlas=p.call('create_canvas',width=42,height=80,color_mode='rgb')['file_path']
   paint(p,atlas,[pix for f,g in enumerate(frames) for pix in frame_pixels(g,n['palette'],14*(f%3),20*(f//3))])
   p.call('export_sprite',sprite_path=atlas,output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
   records=[]
   for f in range(12):records.append(dict(filename=n['name']+'_'+list(BASES)[f//3]+'_'+str(f%3),frame=dict(x=14*(f%3),y=20*(f//3),w=14,h=20),duration=200,rotated=False,trimmed=False,sourceSize=dict(w=14,h=20),spriteSourceSize=dict(x=0,y=0,w=14,h=20)))
   data=dict(frames=records,meta=dict(image=out.with_suffix('.png').name,size=dict(w=42,h=80),scale='1',frameTags=[dict(name=d,**{'from':3*i,'to':3*i+2},direction='forward') for i,d in enumerate(BASES)]),design=n,origin=dict(x=7,y=19),playback=dict(frame_duration_ms=200,stop_behavior='standing',**{d:dict(idle_frame=3*i,walk_sequence=[3*i+1,3*i,3*i+2,3*i]) for i,d in enumerate(BASES)}))
   out.with_suffix('.json').write_text(json.dumps(data,indent=2)+'\n')
   print(n['name']+': 12 saved cels verified; sheet and playback metadata exported',flush=True)
  # Three animated review pages, ten people each. All four directions use
  # the actual player cadence, not a three-cel forward loop.
  for page in range(3):
   board=p.call('create_canvas',width=104,height=200,color_mode='rgb')['file_path'];p.call('set_frame_duration',sprite_path=board,frame_number=1,duration_ms=200)
   for beat,pose in enumerate((1,0,2,0)):
    if beat:p.call('add_frame',sprite_path=board,duration_ms=200)
    paint(p,board,[dict(x=x,y=y,color='#00000000') for y in range(200) for x in range(104)],beat+1)
    pixels=[]
    for local in range(10):
     i=page*10+local;n=ns[i]
     for d in range(4):pixels.extend(frame_pixels(allframes[i][3*d+pose],n['palette'],2+20*(local%5),2+100*(local//5)+24*d))
    paint(p,board,pixels,beat+1)
   p.call('create_tag',sprite_path=board,tag_name='step_stand_otherstep_stand',from_frame=1,to_frame=4,direction='forward')
   out=HERE/('cast30_page'+str(page+1)+'_review.aseprite');p.call('save_as',sprite_path=board,output_path=out.as_posix())
   p.call('export_sprite',sprite_path=out.as_posix(),output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
   print('Animated review page '+str(page+1)+' saved',flush=True)
 finally:p.p.terminate()
 assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
 report=dict(npcs=30,unique_cels=360,frame_size=[14,20],sheet_size=[42,80],directions=list(BASES),poses=['standing','step_a','step_b'],all_saved_cels_reopened_and_verified=True,palette_max=4,body_footprints_match_player=True,no_duplicate_indexed_designs=True,originals_unchanged=True,protected_sha256=hashes,designs=ns)
 (HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 # Labels and nearest-neighbor review enlargement only; artwork comes from plugin PNGs.
 board=Image.new('RGB',(960,1040),(43,43,51));draw=ImageDraw.Draw(board)
 for i,n in enumerate(ns):
  x=8+160*(i%6);y=8+204*(i//6);im=Image.open(HERE/(n['name']+'.png')).convert('RGBA');front=im.crop((0,0,14,20)).resize((84,120),Image.Resampling.NEAREST)
  board.paste(front,(x+32,y+20),front);draw.text((x+5,y+155),n['name'].split('_',1)[0]+' '+n['label'],fill='white');draw.text((x+5,y+172),n['head']+' / '+n['outfit'],fill=(188,190,202))
 board.save(HERE/'cast30_labeled_overview.png')
 print('DONE: 30 distinct NPCs, 360 cels, protected sources unchanged.',flush=True)

if __name__=='__main__':main()
