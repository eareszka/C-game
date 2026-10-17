"""Patch only side-view faces; preserve the reviewed originals and other pixels."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'art/npcs/cast30';OUT=ROOT/'art/npcs/cast30_corrected';TMP=ROOT/'build_tmp/npc_review/cast30_corrected'
sys.path.insert(0,str(ROOT/'art/direction'))
from mcpc import Pixel
from cast30_design import design,BASES,frame_pixels,paint
from villager_walk_sidefix import player_pixels
from villager_walk_4dir import validate_frame

def main():
 OUT.mkdir(exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
 m=json.loads((SRC/'manifest.json').read_text());ns=m['designs'];player=Image.open(ROOT/'assets/player_small.png').convert('RGBA')
 hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.iterdir() if p.is_file()}
 allframes=[];report=[];p=Pixel()
 def reopen(path,label):
  r=p.call('export_spritesheet',sprite_path=path.as_posix(),output_path=(TMP/(path.stem+'_'+label+'.png')).as_posix(),layout='horizontal',padding=0,include_json=True)
  meta=json.loads(Path(r['metadata_path']).read_text());records=meta['frames'];records=list(records.values()) if isinstance(records,dict) else records
  strip=Image.open(r['spritesheet_path']).convert('RGBA');ims=[]
  for f in records:
   b=f['frame'];ims.append(strip.crop((b['x'],b['y'],b['x']+14,b['y']+20)))
  return meta,ims
 try:
  for n in ns:
   name=n['name'];pal=n['palette'];inv={tuple(bytes.fromhex(v)):k for k,v in pal.items()};source=SRC/(name+'.aseprite');out=OUT/source.name
   if out.exists() and out.with_suffix('.json').exists():raise RuntimeError('Preserve completed correction: '+str(out))
   meta,original=reopen(source,'source')
   frames=[{(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]} for im in original]
   p.call('save_as',sprite_path=source.as_posix(),output_path=out.as_posix());changes=0
   for d,direction in ((2,'left'),(3,'right')):
    for native,phase in enumerate((1,0,2)):
     f=3*d+native;off=-1 if phase==0 else 0;index=BASES[direction][phase];base=player_pixels(player.crop((14*index,0,14*(index+1),20)))
     corrected=design(base,n,direction,phase);pixels=[]
     # This face-only rectangle restores the misplaced eye pixels, the cheek,
     # and the opaque solid lens. Hair, costume, limbs and all other cels stay.
     for y in range(10+off,14+off):
      for x in range(3,12):
       q=(x,y)
       if frames[f].get(q)!=corrected.get(q):
        if q in corrected:frames[f][q]=corrected[q]
        else:frames[f].pop(q,None)
        pixels.append(dict(x=x,y=y,color='#'+pal[corrected[q]] if q in corrected else '#00000000'))
     paint(p,out.as_posix(),pixels,f+1);changes+=len(pixels)
     eye=5 if direction=='left' else 9
     if n['face']=='glasses':assert all(frames[f].get((x,y+off))=='K' for y in (11,12,13) for x in range(eye-1,eye+2))
     else:
      assert frames[f][eye,11+off]==frames[f][eye,12+off]=='K'
      assert frames[f][6 if direction=='left' else 8,12+off] in ('S','H')
   newmeta,saved=reopen(out,'corrected')
   assert len(saved)==12 and meta['meta']['frameTags']==newmeta['meta']['frameTags']
   for f,im in enumerate(saved):
    validate_frame(im,frames[f],pal)
    if f<6:assert im.tobytes()==original[f].tobytes()
    else:
     phase=(1,0,2)[f%3];off=-1 if phase==0 else 0
     for y in range(20):
      for x in range(14):
       if not (3<=x<12 and 10+off<=y<14+off):assert im.getpixel((x,y))==original[f].getpixel((x,y))
     assert im.getchannel('A').tobytes()==original[f].getchannel('A').tobytes(),'Transparency/outline footprint changed'
   # Convert native step/stand/step storage to standing-first atlas order.
   atlasframes=[frames[3*d+j] for d in range(4) for j in (1,0,2)];allframes.append(atlasframes)
   atlas=p.call('create_canvas',width=42,height=80,color_mode='rgb')['file_path'];paint(p,atlas,[pix for f,g in enumerate(atlasframes) for pix in frame_pixels(g,pal,14*(f%3),20*(f//3))])
   p.call('export_sprite',sprite_path=atlas,output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
   data=json.loads(source.with_suffix('.json').read_text());data['correction']='Side eyes cleared of player remnants; glasses lenses solid black, as requested.';out.with_suffix('.json').write_text(json.dumps(data,indent=2)+'\n')
   report.append(dict(name=name,changed_side_face_pixels=changes,front_back_unchanged=True,other_side_pixels_unchanged=True,alpha_unchanged=True,solid_lenses=n['face']=='glasses'))
   print(name+': side faces corrected and saved; other pixels verified unchanged',flush=True)
  for page in range(3):
   board=p.call('create_canvas',width=104,height=200,color_mode='rgb')['file_path'];p.call('set_frame_duration',sprite_path=board,frame_number=1,duration_ms=200)
   for beat,pose in enumerate((1,0,2,0)):
    if beat:p.call('add_frame',sprite_path=board,duration_ms=200)
    paint(p,board,[dict(x=x,y=y,color='#00000000') for y in range(200) for x in range(104)],beat+1)
    pixels=[]
    for local in range(10):
     i=10*page+local
     for d in range(4):pixels.extend(frame_pixels(allframes[i][3*d+pose],ns[i]['palette'],2+20*(local%5),2+100*(local//5)+24*d))
    paint(p,board,pixels,beat+1)
   p.call('create_tag',sprite_path=board,tag_name='step_stand_otherstep_stand',from_frame=1,to_frame=4,direction='forward')
   path=OUT/f'cast30_corrected_page{page+1}_review.aseprite';p.call('save_as',sprite_path=board,output_path=path.as_posix())
   p.call('export_sprite',sprite_path=path.as_posix(),output_path=path.with_suffix('.png').as_posix(),format='png',frame_number=1)
   # Independently reload the page and compare every placed sprite.
   r=p.call('export_spritesheet',sprite_path=path.as_posix(),output_path=(TMP/f'page{page+1}_verified.png').as_posix(),layout='horizontal',padding=0,include_json=True)
   strip=Image.open(r['spritesheet_path']).convert('RGBA')
   for beat,pose in enumerate((1,0,2,0)):
    for local in range(10):
     atlas=Image.open(OUT/(ns[10*page+local]['name']+'.png')).convert('RGBA')
     for d in range(4):
      x=104*beat+2+20*(local%5);y=2+100*(local//5)+24*d
      assert strip.crop((x,y,x+14,y+20)).tobytes()==atlas.crop((pose*14,d*20,(pose+1)*14,(d+1)*20)).tobytes()
   print(f'Corrected review page {page+1} verified',flush=True)
 finally:p.p.terminate()
 assert all(hashlib.sha256((SRC/name).read_bytes()).hexdigest()==h for name,h in hashes.items())
 (OUT/'validation.json').write_text(json.dumps(dict(npcs=30,original_pack_unchanged=True,frame_size=[14,20],frames_per_npc=12,source_sha256=hashes,corrections=report,all_saved_cels_reopened_and_verified=True,all_review_placements_verified=True),indent=2)+'\n')
 # Layout-only before/after comparison from actual exported files.
 names=['07_postwoman','09_librarian','12_doctor','14_carpenter','23_tailor','29_artist'];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
 board=Image.new('RGB',(900,750),(50,50,60));draw=ImageDraw.Draw(board)
 for i,name in enumerate(names):
  x=150*i;draw.text((x+4,8),name,fill='white',font=font)
  for row,(folder,d) in enumerate(((SRC,2),(OUT,2),(SRC,3),(OUT,3))):
   im=Image.open(folder/(name+'.png')).convert('RGBA').crop((0,20*d,14,20*(d+1))).resize((98,140),Image.Resampling.NEAREST);board.paste(im,(x+25,44+175*row),im)
 for row,label in enumerate(('Left before','Left corrected','Right before','Right corrected')):draw.text((3,29+175*row),label,fill=(168,240,188),font=font)
 board.save(OUT/'side_face_corrections.png')
 print('DONE: clean side eyes and solid black profile lenses; protected other pixels unchanged',flush=True)

if __name__=='__main__':main()
