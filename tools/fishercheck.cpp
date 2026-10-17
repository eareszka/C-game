#include "fisher.h"
#include "resident.h"
#include "tilemap.h"
#include "collision.h"
#include "interior.h"
#include "camera.h"
#include "save.h"
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cassert>
#include <algorithm>
#include <direct.h>
#include <cstring>

static Tilemap map;
static unsigned char explored[EXPLORE_H][EXPLORE_W];
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SDL_SetMainReady();assert(SDL_Init(SDL_INIT_VIDEO)==0);IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren=SDL_CreateSoftwareRenderer(surface);tilemap_init_tile_cache(ren);
    assert(story_people_init(ren));unsigned seed=argc>1?std::strtoul(argv[1],nullptr,10):387;
    tilemap_build_overworld_phase1(&map,seed);resident_reset();fisher_tick(&map,1.0f/48);
    FisherSave anchor=fisher_save();anchor.epoch=0;
    auto at=[&](double seconds) {
        auto clock=resident_save();clock.world_seconds=seconds;assert(resident_restore(clock));
        assert(fisher_restore(anchor));fisher_tick(&map,1.0f/48);return fisher_view();
    };
    auto start=at(0);assert(start.phase==FI_SLEEP&&start.location==2);
    assert(at(3599).phase==FI_SLEEP);assert(at(3600).phase==FI_TO_EXIT);
    auto plan=at(0);
    printf("Fishing begins at %.3f game hours; return departure %.3f; fishing duration %.3f hours\n",
        plan.fishing_start/3600,plan.return_departure/3600,(plan.return_departure-plan.fishing_start)/3600);
    auto fishing=at(plan.fishing_start+1);
    assert(fishing.phase==FI_FISH&&fishing.facing==FACE_RIGHT);
    assert(fishing.x==map.towns[0].x*TILE_SIZE+4763 && fishing.y==map.towns[0].y*TILE_SIZE+1399);
    assert(tilemap_pixel_water(&map,fishing.x+50,fishing.y+34));
    auto other_frame=at(plan.fishing_start+30);assert(other_frame.frame!=fishing.frame);
    assert(at(43200-.01).phase==FI_TO_BED);
    assert(at(43200).phase==FI_SLEEP && at(43200).location==2);
    assert(at(86400).phase==FI_SLEEP);
    unsigned phases=0;bool saved[10]={};
    int door=-1;for(int i=0;i<map.num_doors;i++)if(map.doors[i].interior_id==2){door=i;break;}assert(door>=0);
    _mkdir("build_tmp/npc_review/fisher_saves");
    for(int step=0;step<=36000;step++) {
        double seconds=step*2.4;auto s=at(seconds);phases|=1u<<s.phase;
        if(s.location<0)assert(can_occupy(&map,s.x,s.y,tilemap_pixel_solid));
        else {InteriorMap im;interior_load(&im,2);assert(interior_feet_fit(&im,s.x,s.y));}
        StoryWhere w={s.location<0?STATE_OVERWORLD:STATE_INTERIOR,&map,2,door,nullptr,false};StoryNpcPos p;
        assert(fisher_here(w,&p));
        if(s.phase==FI_FISH) {
            story_npc_face(p,-1,0);story_npc_face(p,0,-1);story_npc_face(p,0,1);
            auto spoken=fisher_view();
            assert(spoken.facing==FACE_RIGHT&&spoken.frame==s.frame);
            assert(spoken.return_departure==s.return_departure);
        }
        bool returning=s.phase==FI_TO_HOME||s.phase==FI_TO_BED;
        bool talkable=returning||s.phase==FI_SLEEP||s.phase==FI_TO_EXIT||s.phase==FI_TO_WATER||s.phase==FI_FISH;
        assert(story_npc_can_talk(p)==talkable);
        if(returning)assert(!std::strcmp(story_npc_line(p,w),"No bites again today, those damn beast across the river keep eating everything."));
        else if(s.phase==FI_SLEEP)assert(!std::strcmp(story_npc_line(p,w),"zzzz"));
        else if(s.phase==FI_TO_EXIT||s.phase==FI_TO_WATER)assert(!std::strcmp(story_npc_line(p,w),"Early start. The fish won't wait."));
        else if(s.phase==FI_FISH)assert(!std::strcmp(story_npc_line(p,w),"Keep your voice down. You'll scare them."));
        else assert(fisher_line()==nullptr);
        w.state=s.location<0?STATE_INTERIOR:STATE_OVERWORLD;assert(!fisher_here(w,&p));
        if(!saved[s.phase]) {
            saved[s.phase]=true;printf("phase %d at %.2f game hours: %.1f %.1f\n",s.phase,seconds/3600,s.x,s.y);
            char cwd[2048];assert(_getcwd(cwd,sizeof(cwd)));assert(_chdir("build_tmp/npc_review/fisher_saves")==0);
            Player player={};player.width=28;player.height=40;
            assert(save_write(seed,10,20,player,explored));resident_reset();
            unsigned restored;float x,y;assert(save_read(&restored,&x,&y,&player,explored));
            fisher_tick(&map,1.0f/48);auto loaded=fisher_view();
            assert(loaded.phase==s.phase && loaded.x==s.x && loaded.y==s.y && loaded.frame==s.frame);
            assert(fisher_save().epoch==anchor.epoch);assert(_chdir(cwd)==0);
            SDL_SetRenderDrawColor(ren,0,0,0,255);SDL_RenderClear(ren);Camera cam={};cam.zoom=1;cam.screen_w=640;cam.screen_h=480;
            if(s.location>=0) {
                InteriorMap im;interior_load(&im,2);interior_draw(&im,ren,tilemap_get_town_tex());
                fisher_draw(p,ren,&cam);interior_draw_over_player(&im,ren,s.x,s.y,28,40,s.y+40);
            } else {
                camera_place(&cam,s.x-300,s.y-200);
                tilemap_draw_base(&map,&cam,ren);
                fisher_draw(p,ren,&cam);tilemap_draw_depth(&map,&cam,ren);
            }
            char out[128];snprintf(out,sizeof(out),"build_tmp/npc_review/fisher_phase_%d.png",s.phase);assert(IMG_SavePNG(surface,out)==0);
        }
    }
    assert(phases==1023);
    resident_reset();for(int hour=0;hour<12;hour++)resident_advance_hour(&map);
    assert(resident_save().world_seconds==43200);assert(fisher_view().phase==FI_SLEEP);
    puts("PASS: two twelve-hour cycles, exact deadline, east-facing two-frame fishing, collision, every-phase save/load and T skips");
    story_people_free();tilemap_free_tile_cache();SDL_DestroyRenderer(ren);SDL_FreeSurface(surface);IMG_Quit();SDL_Quit();return 0;
}
