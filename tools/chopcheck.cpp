#include "resident.h"
#include "woodcutter.h"
#include "tilemap.h"
#include "camera.h"
#include <SDL2/SDL_image.h>
#include <cassert>
#include <cstdio>
#include <vector>
#include <set>
#include <cstdint>
#include <cstring>

static Tilemap map;
int main() {
    SDL_SetMainReady();assert(SDL_Init(SDL_INIT_VIDEO)==0);IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren=SDL_CreateSoftwareRenderer(surface);tilemap_init_tile_cache(ren);assert(story_people_init(ren));
    tilemap_build_overworld_phase1(&map,387);resident_reset();resident_tick(&map,.01f);
    auto chopping=woodcutter_save();assert(chopping.phase==WC_CHOP);
    SDL_Surface* source=IMG_Load("assets/npcs/woodcutter.png");assert(source);
    SDL_Surface* rgba=SDL_ConvertSurfaceFormat(source,SDL_PIXELFORMAT_RGBA32,0);SDL_FreeSurface(source);
    const int faces[]={FACE_DOWN,FACE_UP,FACE_LEFT,FACE_RIGHT};
    Camera cam={};cam.screen_w=640;cam.screen_h=480;cam.zoom=1;
    for(int row=0;row<4;row++) {
        std::set<uint64_t> hashes;
        for(int frame=0;frame<4;frame++) {
            auto state=chopping;state.x=100;state.y=100;state.facing=faces[row];state.anim=frame*.2f+.01f;
            assert(woodcutter_restore(state));SDL_SetRenderDrawColor(ren,0,0,0,0);SDL_RenderClear(ren);
            StoryNpcPos p={WOODCUTTER_ID,state.x,state.y,-1};assert(woodcutter_draw(p,ren,&cam));
            for(int face:faces) {
                story_npc_face(p,face==FACE_LEFT?-1.0f:face==FACE_RIGHT?1.0f:0.0f,
                               face==FACE_UP?-1.0f:face==FACE_DOWN?1.0f:0.0f);
                auto spoken=woodcutter_save();
                assert(spoken.facing==state.facing&&spoken.anim==state.anim);
            }
            std::vector<Uint32> pixels(640*480);assert(SDL_RenderReadPixels(ren,nullptr,SDL_PIXELFORMAT_RGBA32,pixels.data(),640*4)==0);
            uint64_t hash=1469598103934665603ull;for(auto pixel:pixels){hash^=pixel;hash*=1099511628211ull;}hashes.insert(hash);
            // Every visible foot pixel keeps the approved source color/location.
            for(int y=16;y<20;y++)for(int x=0;x<14;x++) {
                Uint32 src=*(Uint32*)((Uint8*)rgba->pixels+(row*20+y)*rgba->pitch+x*4);
                Uint8 r,g,b,a;SDL_GetRGBA(src,rgba->format,&r,&g,&b,&a);if(!a)continue;
                for(int oy=0;oy<2;oy++)for(int ox=0;ox<2;ox++)
                    assert(pixels[(100+y*2+oy)*640+100+x*2+ox]==src);
            }
            if(row==3) {
                state.x=chopping.x;state.y=chopping.y;assert(woodcutter_restore(state));
                cam.zoom=2;camera_place(&cam,chopping.x-120,chopping.y-100);
                tilemap_draw_base(&map,&cam,ren);p.x=state.x;p.y=state.y;woodcutter_draw(p,ren,&cam);
                tilemap_draw_over_player(&map,&cam,ren,p.x,p.y,28,40,p.y+40);tilemap_draw_depth(&map,&cam,ren);
                char out[120];snprintf(out,sizeof(out),"build_tmp/npc_review/woodcutter_chop_world_%d.png",frame);assert(IMG_SavePNG(surface,out)==0);
                cam.zoom=1;camera_place(&cam,0,0);
            }
        }
        assert(hashes.size()==4);
    }
    assert(woodcutter_restore(chopping));
    for(int i=0;i<80;i++){woodcutter_tick(&map,.01f);auto s=woodcutter_save();assert(s.x==chopping.x&&s.y==chopping.y&&s.phase==WC_CHOP);}
    puts("PASS: four unique chop cels in all four directions, planted source feet, runtime tree captures, stationary swing loop");
    SDL_FreeSurface(rgba);story_people_free();tilemap_free_tile_cache();SDL_DestroyRenderer(ren);SDL_FreeSurface(surface);IMG_Quit();SDL_Quit();
}
