#include "sailor_fisher.h"
#include "mother.h"
#include "resident.h"
#include "resident_path.h"
#include <vector>
#include <limits>
#include "tilemap.h"
#include "collision.h"
#include "interior.h"
#include "camera.h"
#include "save.h"
#include "fisher.h"
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
static void check_sailor_text(const StoryNpcPos& npc,StoryWhere where) {
    StoryFlags original=*story_flags();
    for(int stage=0;stage<STORY_STAGE_COUNT;stage++) {
        story_set_stage((StoryStage)stage);
        for(bool debug:{false,true}) {
            where.debug=debug;
            StoryFlags before=*story_flags();
            int phase=sailor_fisher_view().phase;
            bool doorway=phase==SF_DISSOLVE_HOME||phase==SF_APPEAR_OUT||phase==SF_DISSOLVE_OUT||phase==SF_APPEAR_HOME;
            assert(story_npc_can_talk(npc)==!doorway);
            const char* line=story_npc_line(npc,where);
            const auto* conversation=story_npc_conversation(npc);
            if(doorway)assert(line==nullptr&&conversation==nullptr);
            else if(phase==SF_SLEEP)assert(!std::strcmp(line,"Zzzz...")&&conversation==nullptr);
            else {
                assert(line&&conversation&&!std::strcmp(line,conversation->prompt));
                assert(!std::strcmp(conversation->choices[0],"What's there to do in town?"));
                assert(!std::strcmp(conversation->choices[1],"Where am I?"));
                assert(!std::strcmp(conversation->choices[2],"No"));
                assert(std::strstr(story_npc_answer(npc,where,0),"cave south of town"));
                assert(std::strstr(story_npc_answer(npc,where,1),"Bloom"));
            }
            assert(story_npc_shop(npc)==nullptr);
            for(int choice:{-1,2,3})assert(story_npc_answer(npc,where,choice)==nullptr);
            if(!conversation)for(int choice=0;choice<=1;choice++)assert(story_npc_answer(npc,where,choice)==nullptr);
            story_npc_resume(npc);
            assert(std::memcmp(&before,story_flags(),sizeof(before))==0);
        }
    }
    *story_flags()=original;
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SDL_SetMainReady();assert(SDL_Init(SDL_INIT_VIDEO)==0);IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren=SDL_CreateSoftwareRenderer(surface);tilemap_init_tile_cache(ren);
    assert(story_people_init(ren));unsigned seed=argc>1?std::strtoul(argv[1],nullptr,10):387;
    tilemap_build_overworld_phase1(&map,seed);resident_reset();sailor_fisher_tick(&map,1.0f/48);
    SailorFisherSave anchor=sailor_fisher_save();anchor.epoch=0;
    auto at=[&](double seconds) {
        auto clock=resident_save();clock.world_seconds=seconds;assert(resident_restore(clock));
        assert(sailor_fisher_restore(anchor));sailor_fisher_tick(&map,1.0f/48);return sailor_fisher_view();
    };
    auto start=at(0);assert(start.phase==SF_FISH&&start.location==-1);
    auto plan=at(0);
    printf("Initial fishing origin %.0f %.0f; return departure %.3f game hours\n",start.x,start.y,plan.return_departure/3600);
    assert(std::hypot(start.x-(map.towns[0].x*TILE_SIZE+2766),start.y-(map.towns[0].y*TILE_SIZE+2451))<=TILE_SIZE);
    assert(tilemap_pixel_water(&map,start.x-44,start.y+34));
    assert(at(1).frame!=at(30).frame);
    for(int cycle=0;cycle<3;cycle++) {
        double base=cycle*43200.0;
        assert(at(base+36000-.01).phase==SF_TO_BED);
        assert(at(base+36000).phase==SF_SLEEP);
        assert(at(base+43200-.01).phase==SF_SLEEP);
        assert(at(base+43200).phase==SF_TO_EXIT);
    }
    auto paused=at(100);auto frozen=resident_save();resident_tick(&map,0);
    assert(resident_save().world_seconds==frozen.world_seconds);
    assert(sailor_fisher_view().x==paused.x&&sailor_fisher_view().frame==paused.frame);
    SailorFisherSave invalid=anchor;invalid.epoch=std::numeric_limits<double>::quiet_NaN();assert(!sailor_fisher_restore(invalid));
    invalid.epoch=-2;assert(!sailor_fisher_restore(invalid));
    unsigned phases=0;bool saved[10]={};
    int door=resident_town_door(&map,3);assert(door>=0);
    _mkdir("build_tmp/npc_review/sailor_fisher_saves");
    auto prior=at(0);
    for(int step=0;step<=54000;step++) {
        double seconds=step*2.4;auto s=at(seconds);phases|=1u<<s.phase;
        if(step>0) {
            if(prior.location==s.location)assert(std::hypot(prior.x-s.x,prior.y-s.y)<=4.6);
            else {
                assert(prior.visibility<.1&&s.visibility<.1);
                assert(prior.facing==s.facing&&prior.frame==s.frame);
            }
        }
        prior=s;
        if(s.location<0)assert(can_occupy(&map,s.x,s.y,tilemap_pixel_solid));
        else {InteriorMap im;interior_load(&im,3);assert(interior_feet_fit(&im,s.x,s.y));}
        StoryWhere w={s.location<0?STATE_OVERWORLD:STATE_INTERIOR,&map,3,door,nullptr,false};StoryNpcPos p;
        assert(sailor_fisher_here(w,&p));
        if(s.phase==SF_FISH) {
            story_npc_face(p,-1,0);story_npc_face(p,0,-1);story_npc_face(p,0,1);
            auto spoken=sailor_fisher_view();
            assert(spoken.facing==FACE_LEFT&&spoken.frame==s.frame);
            assert(spoken.return_departure==s.return_departure);
        }
        bool doorway=s.phase==SF_DISSOLVE_HOME||s.phase==SF_APPEAR_OUT||s.phase==SF_DISSOLVE_OUT||s.phase==SF_APPEAR_HOME;
        assert(story_npc_can_talk(p)==!doorway);
        assert((story_npc_line(p,w)!=nullptr)==!doorway);
        w.state=s.location<0?STATE_INTERIOR:STATE_OVERWORLD;assert(!sailor_fisher_here(w,&p));
        if(!saved[s.phase]) {
            w.state=s.location<0?STATE_OVERWORLD:STATE_INTERIOR;
            check_sailor_text(p,w);
            saved[s.phase]=true;printf("phase %d at %.2f game hours: %.1f %.1f\n",s.phase,seconds/3600,s.x,s.y);
            char cwd[2048];assert(_getcwd(cwd,sizeof(cwd)));assert(_chdir("build_tmp/npc_review/sailor_fisher_saves")==0);
            Player player={};player.width=28;player.height=40;
            assert(save_write(seed,10,20,player,explored));resident_reset();
            unsigned restored;float x,y;assert(save_read(&restored,&x,&y,&player,explored));
            sailor_fisher_tick(&map,1.0f/48);auto loaded=sailor_fisher_view();
            check_sailor_text(p,w);
            assert(loaded.phase==s.phase && loaded.x==s.x && loaded.y==s.y && loaded.frame==s.frame);
            assert(sailor_fisher_save().epoch==anchor.epoch);assert(_chdir(cwd)==0);
            SDL_SetRenderDrawColor(ren,0,0,0,255);SDL_RenderClear(ren);Camera cam={};cam.zoom=1;cam.screen_w=640;cam.screen_h=480;
            if(s.location>=0) {
                InteriorMap im;interior_load(&im,3);interior_draw(&im,ren,tilemap_get_town_tex());
                sailor_fisher_draw(p,ren,&cam);interior_draw_over_player(&im,ren,s.x,s.y,28,40,s.y+40);
            } else {
                camera_place(&cam,s.x-300,s.y-200);
                tilemap_draw_base(&map,&cam,ren);
                sailor_fisher_draw(p,ren,&cam);tilemap_draw_depth(&map,&cam,ren);
            }
            char out[128];snprintf(out,sizeof(out),"build_tmp/npc_review/sailor_fisher_phase_%d.png",s.phase);assert(IMG_SavePNG(surface,out)==0);
        }
    }
    assert(phases==1023);
    // Convert a genuine v14 save to the exact v13 prefix; the sailor alone starts fresh.
    char previous[2048];assert(_getcwd(previous,sizeof(previous)));assert(_chdir("build_tmp/npc_review/sailor_fisher_saves")==0);
    at(90000);Player player={};player.width=28;player.height=40;
    assert(save_write(seed,10,20,player,explored));
    auto oldclock=resident_save();auto oldfisher=fisher_save();
    FILE* file=fopen("save.dat","rb");assert(file);fseek(file,0,SEEK_END);long bytes=ftell(file);rewind(file);
    std::vector<unsigned char> data(bytes);assert(fread(data.data(),data.size(),1,file)==1);fclose(file);
    unsigned version=13;memcpy(data.data()+4,&version,sizeof(version));data.resize(data.size()-sizeof(SailorFisherSave)-sizeof(MotherSave));   // v13 had neither
    file=fopen("save.dat","wb");assert(file);assert(fwrite(data.data(),data.size(),1,file)==1);fclose(file);
    resident_reset();unsigned restored;float x,y;assert(save_read(&restored,&x,&y,&player,explored));
    assert(resident_save().world_seconds==oldclock.world_seconds&&fisher_save().epoch==oldfisher.epoch);
    assert(sailor_fisher_save().epoch==-1);sailor_fisher_tick(&map,1.0f/48);
    assert(sailor_fisher_view().phase==SF_FISH);assert(_chdir(previous)==0);

    resident_reset();for(int hour=0;hour<12;hour++)resident_advance_hour(&map);
    assert(resident_save().world_seconds==43200);assert(sailor_fisher_view().phase==SF_TO_EXIT);
    puts("PASS: initial and two later cycles, exact sleep/wake, grandma-style topics, sleeping line, west-facing fishing, collision, every-phase save/load and T skips");
    story_people_free();tilemap_free_tile_cache();SDL_DestroyRenderer(ren);SDL_FreeSurface(surface);IMG_Quit();SDL_Quit();return 0;
}
