#include "courier.h"
#include "gardener.h"
#include "resident.h"
#include "tilemap.h"
#include "collision.h"
#include "camera.h"
#include "save.h"
#include "battle.h"
#include <SDL2/SDL_image.h>
#include <cassert>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <vector>
#include <direct.h>
static Tilemap map;
static unsigned char explored[EXPLORE_H][EXPLORE_W];
static int cols[]={54,56,58,60,62,64,66,68,70,75,77,79,81,83,85,91,93,95,97};
static void trees(unsigned mask){for(int i=0;i<19;i++)map.overlay[map.towns[0].y+88][map.towns[0].x+cols[i]]=(mask&(1u<<i))?TILE_TREE:0;}
static void sweep(unsigned mask){
 trees(mask);gardener_reset();assert(gardener_validate_route(&map));gardener_tick(&map,.001f);
 int visits[19]={},turns=0,lastdir=1;double duration=0;int active=-1;
 for(int n=0;n<80000&&turns<4;n++){
  auto before=gardener_save();gardener_tick(&map,.01f);auto after=gardener_save();
  assert(can_occupy(&map,after.x,after.y,tilemap_pixel_solid));if(std::fabs(after.y-((map.towns[0].y+90)*32-34))<.001f)assert(resident_on_trail(&map,after.x,after.y));
  if(before.watering){assert(mask&(1u<<before.target));if(active<0){active=before.target;duration=3-before.remaining;}duration+=after.watering&&after.target==before.target?before.remaining-after.remaining:before.remaining;
   if(!after.watering||after.target!=before.target){assert(std::fabs(duration-3)<.002);visits[active]++;active=-1;duration=0;}}
  if(after.direction!=lastdir){turns++;lastdir=after.direction;assert(std::fabs(after.x-((map.towns[0].x+cols[after.direction<0?18:0])*32+2))<1);}
 }
 assert(turns==4);
 for(int i=0;i<19;i++){if(mask&(1u<<i))assert(visits[i]>=2);else assert(visits[i]==0);}
}
int main(){setvbuf(stdout,nullptr,_IONBF,0);SDL_SetMainReady();assert(SDL_Init(SDL_INIT_VIDEO)==0);IMG_Init(IMG_INIT_PNG);auto surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);auto r=SDL_CreateSoftwareRenderer(surface);tilemap_init_tile_cache(r);tilemap_build_overworld_phase1(&map,387);tilemap_build_overworld_phase2(&map,387);
 for(int i=0;i<19;i++)assert(map.overlay[map.towns[0].y+88][map.towns[0].x+cols[i]]==TILE_TREE);
 const unsigned all=(1u<<19)-1;
 sweep(all);puts("PASS four sweeps: three seconds per watering visit, no duplicate endpoint watering");
 sweep(0x55555);sweep(all&~(0x3fu<<5));for(int i=0;i<19;i++)sweep(1u<<i);sweep(0);puts("PASS alternating removals, consecutive gaps, every lone survivor, no plants: continuous clear street");
 trees(all);gardener_reset();gardener_tick(&map,1+24.0f/90);auto water=gardener_save();assert(water.watering);assert(std::fabs(water.remaining-2)<.001);
 gardener_face(0);gardener_tick(&map,20);auto frozen=gardener_save();assert(!memcmp(&water,&frozen,sizeof(water)));gardener_resume();gardener_tick(&map,.5f);assert(std::fabs(gardener_save().remaining-1.5f)<.001);
 assert(gardener_restore(water));gardener_tick(&map,.5f);assert(std::fabs(gardener_save().remaining-1.5f)<.001);
 trees(all&~1u);gardener_tick(&map,.01f);assert(gardener_save().initialized==2&&!gardener_save().watering);
 gardener_tick(&map,24.0f/90);
 auto approach=gardener_save();assert(gardener_restore(approach));trees(all&~3u);gardener_tick(&map,.01f);assert(gardener_save().target==2);
 trees(0);gardener_tick(&map,.01f);auto empty=gardener_save();assert(empty.target==18&&!empty.watering);assert(gardener_restore(empty));trees(all);gardener_tick(&map,.01f);assert(gardener_save().target==18);puts("PASS interruption, save-state restore, removal during watering/approach, plants returning on next pass");
 // The same routine receives the resident hour skip, wherever the player is.
 trees(all);resident_reset();resident_tick(&map,.01f);resident_advance_hour(&map);auto hour=gardener_save();assert(hour.x!=water.x);gardener_reset();gardener_tick(&map,.01f);for(int i=0;i<1500;i++)gardener_tick(&map,.05f);auto manual=gardener_save();assert(!memcmp(&hour,&manual,sizeof(hour)));puts("PASS offscreen shared clock and hour skip");
 // Inject an unexpected street obstruction after validation; keep the same target.
 trees(all);gardener_reset();gardener_tick(&map,3.1f+48.0f/90);auto blocked=gardener_save();assert(!blocked.watering);
 int bx=int(blocked.x+14)/32,by=int(blocked.y+34)/32;int original=map.tiles[by][bx];map.tiles[by][bx]=TILE_WATER;
 gardener_tick(&map,.1f);auto failed=gardener_save();assert(!memcmp(&blocked,&failed,sizeof(blocked)));
 map.tiles[by][bx]=original;gardener_tick(&map,.5f);assert(gardener_save().x==blocked.x);gardener_tick(&map,.6f);assert(gardener_save().x>blocked.x&&gardener_save().target==blocked.target);puts("PASS unexpected path failure retains target and retries after one second");
 assert(story_people_init(r));gardener_reset();gardener_tick(&map,.4f+24.0f/90);auto pose=gardener_save();Camera c={};c.zoom=2;c.screen_w=640;c.screen_h=480;camera_place(&c,pose.x-140,pose.y-160);tilemap_draw_base(&map,&c,r);tilemap_draw_depth(&map,&c,r);StoryNpcPos npc={GARDENER_ID,pose.x,pose.y,-1};gardener_draw(npc,r,&c);SDL_RenderReadPixels(r,nullptr,SDL_PIXELFORMAT_RGBA32,surface->pixels,surface->pitch);IMG_SavePNG(surface,"build_tmp/npc_review/gardener_water.png");
 assert(!strcmp(story_npc_conversation(npc)->choices[0],"Why water them?"));assert(story_npc_answer(npc,{STATE_OVERWORLD,&map,-1,-1,nullptr,false},0));
 // Isolated save directory; construct v15 by removing only the new footer.
 _mkdir("build_tmp/gardener_saves");assert(_chdir("build_tmp/gardener_saves")==0);Player player={};player.equipped=(WeaponType)0;unsigned seed;float x,y;
 for(auto saved : {approach,empty,pose}){assert(gardener_restore(saved));assert(save_write(387,10,20,player,explored));gardener_reset();assert(save_read(&seed,&x,&y,&player,explored));auto back=gardener_save();assert(!memcmp(&saved,&back,sizeof(saved)));}
 FILE* f=fopen("save.dat","rb");assert(f);fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);std::vector<unsigned char> bytes(size);assert(fread(bytes.data(),1,size,f)==size);fclose(f);bytes.resize(size-sizeof(GardenerSave)-sizeof(CourierSave));unsigned v=15;memcpy(bytes.data()+4,&v,4);f=fopen("save.dat","wb");assert(fwrite(bytes.data(),1,bytes.size(),f)==bytes.size());fclose(f);assert(save_read(&seed,&x,&y,&player,explored));assert(!gardener_save().initialized);puts("PASS v16 save roundtrip and v15 migration");
 puts("PASS gardener checks");return 0;}
