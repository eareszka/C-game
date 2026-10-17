from pathlib import Path
import sys,json
from PIL import Image
root=Path.cwd();folder=root/'art/npcs';sys.path.insert(0,str(root/'art/direction'))
from mcpc import Pixel
npcs=json.loads((folder/'villagers_standing_drafts.json').read_text())['npcs'];p=Pixel()
try:
 out=folder/'villagers_player_cadence_review.aseprite'
 for phase,pose in enumerate([1,0,2,0]):
  clear=[dict(x=x,y=y,color='#00000000') for y in range(48) for x in range(84)]
  for at in range(0,len(clear),600):p.call('draw_pixels',sprite_path=out.as_posix(),layer_name='Layer 1',frame_number=phase+1,pixels=clear[at:at+600])
  for i,n in enumerate(npcs):
   im=Image.open(folder/(n['name']+'_walk_3frame.png')).convert('RGBA')
   for row in range(2):
    pixels=[dict(x=x+2+20*i,y=y+2+24*row,color='#%02x%02x%02x'%im.getpixel((x+14*pose,y+20*row))[:3]) for y in range(20) for x in range(14) if im.getpixel((x+14*pose,y+20*row))[3]]
    p.call('draw_pixels',sprite_path=out.as_posix(),layer_name='Layer 1',frame_number=phase+1,pixels=pixels)
 r=p.call('export_spritesheet',sprite_path=out.as_posix(),output_path=(root/'build_tmp/npc_review/player_cadence_verified.png').as_posix(),layout='horizontal',padding=0,include_json=True)
 data=json.loads(Path(r['metadata_path']).read_text());records=list(data['frames'].values());strip=Image.open(r['spritesheet_path']).convert('RGBA');cells=[strip.crop((i*84,0,(i+1)*84,48)) for i in range(4)]
 assert len(records)==4 and all(f['duration']==200 for f in records)
 assert cells[1].tobytes()==cells[3].tobytes() and cells[0].tobytes()!=cells[2].tobytes()
 for n in npcs:
  path=folder/(n['name']+'_walk_3frame.json');data=json.loads(path.read_text());data['playback']={'frame_duration_ms':200,'down':{'idle_frame':0,'walk_sequence':[1,0,2,0]},'up':{'idle_frame':3,'walk_sequence':[4,3,5,3]},'stop_behavior':'standing','source':'src/entity.cpp player_frame'};path.write_text(json.dumps(data,indent=2)+'\n')
 print('Four-beat cadence verified and metadata saved')
finally:p.p.terminate()
