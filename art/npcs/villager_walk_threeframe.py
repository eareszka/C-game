"""Assemble approved standing and step cels through the pixel plugin; preserve sources."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; HERE=ROOT/'art/npcs'; TMP=ROOT/'build_tmp/npc_review'
sys.path.insert(0,str(ROOT/'art/direction'))
from mcpc import Pixel
from villager_walk_sidefix import write_frame
from villager_walk_4dir import validate_frame
npcs=json.loads((HERE/'villagers_standing_drafts.json').read_text())['npcs']
assert not any((HERE/(n['name']+'_walk_3frame.aseprite')).exists() for n in npcs),'Preserve existing outputs'
protected={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.aseprite')}
p=Pixel(); allframes=[]
def read(path):
 out=TMP/(path.stem+'_assembly.png')
 r=p.call('export_spritesheet',sprite_path=path.as_posix(),output_path=out.as_posix(),layout='horizontal',padding=0,include_json=True)
 meta=json.loads(Path(r['metadata_path']).read_text()); records=meta['frames'];records=list(records.values()) if isinstance(records,dict) else records
 strip=Image.open(out).convert('RGBA')
 return [strip.crop((f['frame']['x'],f['frame']['y'],f['frame']['x']+14,f['frame']['y']+20)) for f in records]
try:
 for n in npcs:
  name=n['name'];pal=n['palette'];inv={tuple(bytes.fromhex(c)):k for k,c in pal.items()}
  standing=read(HERE/(name+'_walk_4dir_matched.aseprite'));steps=read(HERE/(name+'_walk_4dir_fullstep.aseprite'))
  images=[standing[0],steps[0],steps[1],standing[2],steps[2],steps[3]]+steps[4:8]
  frames=[{(x,y):inv[im.getpixel((x,y))[:3]] for y in range(20) for x in range(14) if im.getpixel((x,y))[3]} for im in images];allframes.append(frames)
  work=p.call('create_canvas',width=14,height=20,color_mode='rgb')['file_path']
  p.call('set_palette',sprite_path=work,colors=['#'+v for v in pal.values()]);p.call('set_frame_duration',sprite_path=work,frame_number=1,duration_ms=200)
  for i,g in enumerate(frames):
   if i:p.call('add_frame',sprite_path=work,duration_ms=200)
   write_frame(p,work,i+1,g,pal)
  tags=[('down',0,2),('up',3,5),('left',6,7),('right',8,9)]
  for tag,a,b in tags:p.call('create_tag',sprite_path=work,tag_name=tag,from_frame=a+1,to_frame=b+1,direction='forward')
  out=HERE/(name+'_walk_3frame.aseprite');p.call('save_as',sprite_path=work,output_path=out.as_posix())
  reopened=read(out);assert len(reopened)==10
  for i,im in enumerate(reopened):validate_frame(im,frames[i],pal);assert im.tobytes()==images[i].tobytes()
  atlas=p.call('create_canvas',width=42,height=80,color_mode='rgb')['file_path']; records=[]
  for row,(tag,a,b) in enumerate(tags):
   for col,f in enumerate(range(a,b+1)):
    pixels=[dict(x=x+14*col,y=y+20*row,color='#'+pal[c]) for (x,y),c in frames[f].items()]
    p.call('draw_pixels',sprite_path=atlas,layer_name='Layer 1',frame_number=1,pixels=pixels)
    records.append(dict(filename=f'{name}_{tag}_{col}',frame=dict(x=14*col,y=20*row,w=14,h=20),duration=200,rotated=False,trimmed=False,sourceSize=dict(w=14,h=20),spriteSourceSize=dict(x=0,y=0,w=14,h=20)))
  p.call('export_sprite',sprite_path=atlas,output_path=out.with_suffix('.png').as_posix(),format='png',frame_number=1)
  out.with_suffix('.json').write_text(json.dumps(dict(frames=records,meta=dict(image=out.with_suffix('.png').name,size=dict(w=42,h=80),scale='1',frameTags=[dict(name=t,**{'from':a,'to':b},direction='forward') for t,a,b in tags]),poses=dict(down=['standing','left_step','right_step'],up=['standing','left_step','right_step'],left=['standing','step'],right=['standing','step']),origin=dict(x=7,y=19)),indent=2)+'\n')
  print(name+': 10 saved cels verified against approved source pixels',flush=True)
 board=p.call('create_canvas',width=84,height=100,color_mode='rgb')['file_path']
 p.call('set_frame_duration',sprite_path=board,frame_number=1,duration_ms=200)
 for phase in range(3):
  if phase:p.call('add_frame',sprite_path=board,duration_ms=200)
  for i,n in enumerate(npcs):
   for row,indices in enumerate(((0,1,2),(3,4,5),(6,7,6),(8,9,8))):
    g=allframes[i][indices[phase]];pixels=[dict(x=x+2+20*i,y=y+2+24*row,color='#'+n['palette'][c]) for (x,y),c in g.items()]
    p.call('draw_pixels',sprite_path=board,layer_name='Layer 1',frame_number=phase+1,pixels=pixels)
 p.call('create_tag',sprite_path=board,tag_name='standing_left_right',from_frame=1,to_frame=3,direction='forward')
 review=HERE/'villagers_walk_3frame_review.aseprite';p.call('save_as',sprite_path=board,output_path=review.as_posix())
 p.call('export_sprite',sprite_path=review.as_posix(),output_path=review.with_suffix('.png').as_posix(),format='png',frame_number=1)
finally:p.p.terminate()
assert all(hashlib.sha256(path.read_bytes()).hexdigest()==h for path,h in protected.items())
(HERE/'villagers_walk_3frame_validation.json').write_text(json.dumps(dict(canvas=[14,20],sheet=[42,80],frame_counts=dict(down=3,up=3,left=2,right=2),all_40_saved_cels_reopened_and_pixel_verified=True,source_files_unchanged=True,side_cels_unchanged=True),indent=2)+'\n')
