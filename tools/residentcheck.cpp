#include "resident.h"
#include "fisher.h"
#include "sailor_fisher.h"
#include "grandmother.h"
#include "woodcutter.h"
#include "mother.h"
#include "bookshop.h"
#include "tilemap.h"
#include "interior.h"
#include "collision.h"
#include "camera.h"
#include "save.h"
#include "battle.h"
#include "towns.h"
#include "core.h"
#include <SDL2/SDL_image.h>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <direct.h>
#include <vector>
#include <algorithm>
#include <cstddef>

static Tilemap map;
static unsigned char explored[EXPLORE_H][EXPLORE_W];
static void appearance_checks(SDL_Renderer* ren) {
    resident_reset();auto frozen=resident_save();
    frozen.phase=RES_LEAVE_HOME;frozen.x=80;frozen.y=80;
    frozen.facing=FACE_RIGHT;frozen.transition_frame=1;
    frozen.transfer_pending=1;frozen.flash=ACTOR_APPEAR_T;
    auto clear=[&](){SDL_SetRenderDrawColor(ren,0,0,0,255);SDL_RenderClear(ren);};
    auto pixels=[&](){std::vector<Uint32> p(640*480);assert(SDL_RenderReadPixels(ren,nullptr,SDL_PIXELFORMAT_RGBA32,p.data(),640*4)==0);return p;};
    clear();SDL_Texture* texture=IMG_LoadTexture(ren,"assets/npcs/girl.png");assert(texture);
    SDL_Rect src={14,60,14,20},dst={80,80,28,40};SDL_RenderCopy(ren,texture,&src,&dst);
    auto reference=pixels();SDL_DestroyTexture(texture);
    auto render=[&](float remaining,bool leaving){
        auto s=frozen;s.flash=remaining;s.transfer_pending=leaving;
        assert(resident_restore(s));clear();StoryNpcPos p={RESIDENT_STORY_ID,80,80,-1};
        Camera camera={0,0,640,480,1,0,0};
        assert(resident_draw(p,ren,&camera));
        return pixels();
    };
    assert(render(ACTOR_APPEAR_T,true)==reference);
    auto half=render(.3f,true);int visible=0,full=0;
    SDL_PixelFormat* fmt=SDL_AllocFormat(SDL_PIXELFORMAT_RGBA32);Uint32 black=SDL_MapRGBA(fmt,0,0,0,255);SDL_FreeFormat(fmt);
    for(size_t i=0;i<half.size();i++) {
        if(reference[i]!=black)full++;
        if(half[i]!=black){visible++;assert(half[i]==reference[i]);}
    }
    assert(visible>0 && visible<full);
    assert(render(.3f,false)==half);
    auto count=[&](const std::vector<Uint32>& p){int n=0;for(Uint32 pixel:p)if(pixel!=black)n++;return n;};
    assert(count(render(.5f,true))>count(render(.1f,true)));
    assert(count(render(.5f,false))<count(render(.1f,false)));
    clear();Camera cam={};cam.zoom=2;cam.screen_w=640;cam.screen_h=480;
    for(int leaving=0;leaving<2;leaving++)for(int i=0;i<5;i++) {
        auto s=frozen;s.flash=.6f-i*.149f;s.transfer_pending=leaving;
        assert(resident_restore(s));StoryNpcPos p={RESIDENT_STORY_ID,(float)(12+i*60),(float)(24+leaving*70),-1};
        resident_draw(p,ren,&cam);
    }
    SDL_Surface* shot=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
    assert(SDL_RenderReadPixels(ren,nullptr,SDL_PIXELFORMAT_RGBA32,shot->pixels,shot->pitch)==0);
    assert(IMG_SavePNG(shot,"build_tmp/npc_review/routine_transition.png")==0);SDL_FreeSurface(shot);
    resident_reset();puts("appearance: original colors, frozen walking pose, reverse dissolve and forward appearance checked");
}
static void bookshop_checks(SDL_Renderer* ren,unsigned seed) {
    resident_reset();
    InteriorMap shop;interior_load(&shop,1);
    assert(bookshop_clerk_valid(bookshop_clerk_save()));
    int door=-1;
    for(int i=0;i<map.num_doors;i++)if(map.doors[i].interior_id==1 &&
        map.doors[i].x>=map.towns[0].x && map.doors[i].x<map.towns[0].x+TOWN_W &&
        map.doors[i].y>=map.towns[0].y && map.doors[i].y<map.towns[0].y+TOWN_H)door=i;
    assert(door>=0);
    StoryWhere where={STATE_INTERIOR,&map,1,door,nullptr,false};
    StoryNpcPos clerk;
    assert(bookshop_clerk_here(where,&clerk));
    assert(story_npc_shop(clerk)==nullptr);
    const auto* conversation=story_npc_conversation(clerk);assert(conversation);
    assert(!strcmp(conversation->prompt,"Just restocking shelfs, need anything?"));
    assert(!strcmp(conversation->choices[0],"Why do I need books?"));
    assert(!strcmp(conversation->choices[1],"Where am I?"));
    assert(!strcmp(conversation->choices[2],"No"));
    assert(strstr(story_npc_answer(clerk,where,0),"purpose of life"));
    assert(strstr(story_npc_answer(clerk,where,1),"town of Bloom"));
    assert(strstr(story_npc_answer(clerk,where,1),"Vaalbara"));
    assert(story_npc_answer(clerk,where,2)==nullptr);
    auto elsewhere=where;elsewhere.door=-1;
    assert(!bookshop_clerk_here(elsewhere,&clerk));
    assert(strstr(story_where_am_i(clerk,elsewhere),"Bloom")==nullptr);
    auto outdoors=where;outdoors.state=STATE_OVERWORLD;
    StoryNpcPos world_clerk={BOOKSHOP_CLERK_ID,(float)((map.towns[0].x+70)*TILE_SIZE),(float)((map.towns[0].y+75)*TILE_SIZE),-1};
    assert(strstr(story_where_am_i(world_clerk,outdoors),"Bloom"));
    outdoors.state=STATE_DUNGEON;assert(!strstr(story_where_am_i(world_clerk,outdoors),"Bloom"));
    assert(!strcmp(story_world_name(),"Vaalbara") && !strcmp(story_town_name(0),"Bloom"));
    assert(story_town_name(1)==nullptr && story_town_name(9)==nullptr);
    StoryNpcPos people[32];int count=story_npcs_here(where,people,32),found=0,owners=0;
    for(int i=0;i<count;i++){found+=people[i].idx==BOOKSHOP_CLERK_ID;owners+=story_npc_shop(people[i])!=nullptr;}
    assert(found==1 && owners==1);
    unsigned stops=0;int cycles=0;bool moving_saved=false,browsing_saved=false;
    for(int frame=0;frame<5000 && cycles<3;frame++) {
        auto before=bookshop_clerk_save();double clock=resident_save().world_seconds;
        resident_tick(&map,.05f);auto after=bookshop_clerk_save();
        assert(std::fabs(resident_save().world_seconds-clock-2.4)<.001);
        assert(interior_feet_fit(&shop,after.x,after.y));
        assert(std::hypot(after.x-before.x,after.y-before.y)<=90*.05f+.02f);
        if(after.browsing) {
            assert(after.facing==FACE_UP && after.anim==0);
            if(!(stops&(1u<<after.stop))) {
                printf("bookshop shelf %d: (%.0f,%.0f), pause %.2f\n",after.stop,after.x,after.y,after.pause);
                SDL_SetRenderDrawColor(ren,0,0,0,255);SDL_RenderClear(ren);
                interior_draw(&shop,ren,tilemap_get_town_tex());
                Camera cam={0,0,640,480,1,0,0};
                // Draw all shop people, then the room's furniture occlusion.
                count=story_npcs_here(where,people,32);
                for(int i=0;i<count;i++) {
                    assert(story_npc_draw(people[i],ren,&cam));
                    interior_draw_over_player(&shop,ren,people[i].x,people[i].y,28,40,people[i].y+40);
                }
                SDL_Surface* shot=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
                assert(SDL_RenderReadPixels(ren,nullptr,SDL_PIXELFORMAT_RGBA32,shot->pixels,shot->pitch)==0);
                char filename[160];snprintf(filename,sizeof(filename),"build_tmp/npc_review/bookshop_clerk_stop_%d.png",after.stop);
                assert(IMG_SavePNG(shot,filename)==0);SDL_FreeSurface(shot);
                if(after.stop==0) {
                    SpeechState speech=SPEECH_TYPING;
                    SDL_Rect box=draw_speech(ren,conversation->prompt,0,1e9f,&speech);
                    assert(speech==SPEECH_END);
                    draw_speech_choices(ren,box,conversation->choices,3,0);
                    shot=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
                    assert(SDL_RenderReadPixels(ren,nullptr,SDL_PIXELFORMAT_RGBA32,shot->pixels,shot->pitch)==0);
                    assert(IMG_SavePNG(shot,"build_tmp/npc_review/bookshop_clerk_choices.png")==0);SDL_FreeSurface(shot);
                }
                stops|=1u<<after.stop;
            }
            if(!before.browsing && after.stop==0)cycles++;
        }
        if((after.browsing&&!browsing_saved)||(!after.browsing&&!moving_saved)) {
            // Save in an isolated directory, never over the player's save.
            char cwd[2048];assert(_getcwd(cwd,sizeof(cwd)));
            _mkdir("build_tmp/npc_review/clerk_save_test");assert(_chdir("build_tmp/npc_review/clerk_save_test")==0);
            Player player={};unsigned restored_seed;float x,y;
            assert(save_write(seed,10,20,player,explored));resident_reset();
            assert(save_read(&restored_seed,&x,&y,&player,explored));assert(restored_seed==seed);
            auto restored=bookshop_clerk_save();
            assert(!memcmp(&after,&restored,sizeof(after)));
            assert(_chdir(cwd)==0);
            bookshop_clerk_face(FACE_LEFT);
            resident_tick(&map,.05f);
            auto talking=bookshop_clerk_save();assert(!memcmp(&talking,&restored,sizeof(talking)));
            story_npc_resume(clerk);
            if(after.browsing)browsing_saved=true;else moving_saved=true;
        }
    }
    assert(stops==15 && cycles==3 && moving_saved && browsing_saved);
    // A conversation freezes just this worker and restores the interrupted facing.
    auto frozen=bookshop_clerk_save();
    bookshop_clerk_face(FACE_RIGHT);assert(bookshop_clerk_facing()==FACE_RIGHT);
    for(int i=0;i<30;i++)resident_tick(&map,.05f);
    auto held=bookshop_clerk_save();assert(!memcmp(&held,&frozen,sizeof(held)));
    assert(strstr(story_npc_answer(clerk,where,0),"books"));
    assert(strstr(story_npc_answer(clerk,where,1),"Bloom"));
    story_npc_resume(clerk);resident_tick(&map,.05f);
    assert(bookshop_clerk_save().pause<frozen.pause);
    // The hour-skip advances the same persistent routine, not just its clock.
    resident_reset();resident_advance_hour(&map);auto skipped=bookshop_clerk_save();
    resident_reset();for(int i=0;i<1500;i++)resident_tick(&map,.05f);
    auto simulated=bookshop_clerk_save();assert(!memcmp(&skipped,&simulated,sizeof(skipped)));
    auto invalid=simulated;invalid.x=-1;assert(!bookshop_clerk_restore(invalid));
    invalid=simulated;invalid.pause=5;assert(!bookshop_clerk_restore(invalid));
    resident_reset();
    puts("bookshop: three loops, shelves, dialogue topics, location resolution, offscreen tick, clock, hour skip and save/load checked");
}
static void grandmother_checks(SDL_Renderer* ren,unsigned seed) {
    resident_reset();assert(grandmother_valid(grandmother_save()));
    unsigned phases=0,saved=0;int cycles=0,last=-1;float couch_time=0,search_time=0,desk_time=0;
    bool reserved_clerk_wait=false;
    for(int frame=0;frame<10000&&cycles<2;frame++) {
        auto before=grandmother_save();
        if(before.phase==GM_COUCH)couch_time+=.05f;
        if(before.phase==GM_SEARCH)search_time+=.05f;
        if(before.phase==GM_DESK)desk_time+=.05f;
        double clock=resident_save().world_seconds;
        resident_tick(&map,.05f);auto s=grandmother_save();
        assert(std::fabs(resident_save().world_seconds-clock-2.4)<.001);
        assert(grandmother_valid(s));phases|=1u<<s.phase;
        if(s.phase!=last) {
            printf("grandmother phase %d room %d at %.0f %.0f\n",s.phase,s.location,s.x,s.y);last=s.phase;
        }
        if(s.location<0)assert(resident_on_trail(&map,s.x,s.y,true));
        else {InteriorMap im;interior_load(&im,s.location);assert(interior_feet_fit(&im,s.x,s.y));}
        if(s.location==before.location && s.flash==0)
            assert(std::hypot(s.x-before.x,s.y-before.y)<=90*.05f+.02f);
        if(before.phase==GM_COUCH&&s.phase==GM_LEAVE_HOME) {
            assert(couch_time>=37.49f&&couch_time<37.6f);couch_time=0;
        }
        if(before.phase==GM_SEARCH&&s.phase==GM_TO_DESK) {
            assert(search_time>=4.99f&&search_time<5.1f);search_time=0;
        }
        if(before.phase==GM_DESK&&s.phase==GM_LEAVE_SHOP) {
            assert(desk_time>=4.99f&&desk_time<5.1f);desk_time=0;
        }
        auto clerk=bookshop_clerk_save();int reserved=grandmother_reserved_shelf();
        if(reserved>=0) {
            assert(!(clerk.browsing&&clerk.stop==reserved));
            if(clerk.stop==reserved&&!clerk.browsing) {
                assert(clerk.anim==0);reserved_clerk_wait=true;
            }
        }
        StoryWhere w={s.location<0?STATE_OVERWORLD:STATE_INTERIOR,&map,s.location,-1,nullptr,false};
        if(s.location>=0)for(int i=0;i<map.num_doors;i++) {
            auto d=map.doors[i];
            if(d.interior_id==s.location&&d.x>=map.towns[0].x&&d.x<map.towns[0].x+TOWN_W&&
               d.y>=map.towns[0].y&&d.y<map.towns[0].y+TOWN_H){w.door=i;break;}
        }
        StoryNpcPos actor;assert(grandmother_here(w,&actor));
        const auto* conversation=story_npc_conversation(actor);assert(conversation);
        assert(!strcmp(conversation->prompt,"Good day deer, what do you need?"));
        assert(!strcmp(conversation->choices[0],"What's there to do in town?"));
        assert(strstr(story_npc_answer(actor,w,1),"Bloom"));
        if(!(saved&(1u<<s.phase))) {
            if(s.location>=0 && (s.phase==GM_COUCH||s.phase==GM_SEARCH||s.phase==GM_DESK)) {
                InteriorMap im;interior_load(&im,s.location);
                SDL_SetRenderDrawColor(ren,0,0,0,255);SDL_RenderClear(ren);
                interior_draw(&im,ren,tilemap_get_town_tex());
                StoryNpcPos people[32];int n=story_npcs_here(w,people,32);
                std::sort(people,people+n,[](auto a,auto b){return a.y<b.y;});
                Camera cam={0,0,640,480,1,0,0};
                for(int i=0;i<n;i++) {
                    assert(story_npc_draw(people[i],ren,&cam));
                    interior_draw_over_player(&im,ren,people[i].x,people[i].y,28,40,people[i].y+40);
                }
                SDL_Surface* shot=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
                assert(SDL_RenderReadPixels(ren,nullptr,SDL_PIXELFORMAT_RGBA32,shot->pixels,shot->pitch)==0);
                char filename[128];snprintf(filename,sizeof(filename),"build_tmp/npc_review/grandmother_phase_%d.png",s.phase);
                assert(IMG_SavePNG(shot,filename)==0);SDL_FreeSurface(shot);
            }
            char cwd[2048];assert(_getcwd(cwd,sizeof(cwd)));_mkdir("build_tmp/npc_review/grandma_save_test");
            auto girl=resident_save();auto worker=bookshop_clerk_save();
            assert(_chdir("build_tmp/npc_review/grandma_save_test")==0);
            Player player={};unsigned loaded_seed;float x,y;
            assert(save_write(seed,10,20,player,explored));resident_reset();
            assert(save_read(&loaded_seed,&x,&y,&player,explored));
            auto loaded=grandmother_save();assert(!memcmp(&s,&loaded,sizeof(s)));
            auto loaded_worker=bookshop_clerk_save();assert(!memcmp(&worker,&loaded_worker,sizeof(worker)));
            assert(resident_save().world_seconds==girl.world_seconds);
            assert(_chdir(cwd)==0);saved|=1u<<s.phase;
            if(s.flash==0) {
                grandmother_face(FACE_RIGHT);resident_tick(&map,.05f);
                auto held=grandmother_save();assert(!memcmp(&s,&held,sizeof(s)));
                story_npc_resume(actor);
            }
        }
        if(before.phase==GM_TO_COUCH&&s.phase==GM_COUCH)cycles++;
    }
    assert(cycles==2 && phases==(1u<<11)-1 && saved==phases);
    assert(reserved_clerk_wait);
    resident_reset();
    puts("grandmother: two complete couch/shop/couch loops; all outdoor feet on trail; reservations, 30-game-minute rest, 5-second activities, dialogue and every-phase save/load checked");
}

// The woodcutter: his first tree, a whole day (chop, home, bed, sleep, back
// out), his tree felled under him, every tree gone (sofa instead), save/load.
static void woodcutter_checks() {
    resident_reset();resident_tick(&map,.05f);
    auto w0=woodcutter_save();
    assert(w0.phase==WC_CHOP&&w0.location==-1&&w0.facing==FACE_RIGHT);
    assert(w0.x==48043&&w0.y==47607&&w0.tree_x==map.towns[0].x+80&&w0.tree_y==map.towns[0].y+66);
    assert(map.overlay[w0.tree_y][w0.tree_x]==TILE_TREE);
    assert(!strcmp(woodcutter_line(),"Chopping away at these trees is so relaxing, you know. You gotta try it sometime."));
    // One whole day: every phase but the tree-loss ones, chopping and sleep two game hours each.
    unsigned phases=0;float chop=0,sleep=0;int last=-1;bool day=false;
    for(int frame=0;frame<20000&&!day;frame++) {
        auto before=woodcutter_save();
        if(before.phase==WC_CHOP)chop+=.05f;
        if(before.phase==WC_SLEEP)sleep+=.05f;
        resident_tick(&map,.05f);auto s=woodcutter_save();
        assert(woodcutter_valid(s));phases|=1u<<s.phase;
        if(s.phase==WC_CHOP)assert(s.facing==FACE_LEFT||s.facing==FACE_RIGHT);   // the only swings drawn
        if(s.phase!=last){printf("woodcutter phase %d room %d at %.0f %.0f\n",s.phase,s.location,s.x,s.y);last=s.phase;}
        if(s.location<0&&!can_occupy(&map,s.x,s.y,tilemap_pixel_solid)){printf("woodcutter off ground at %.1f %.1f phase %d (from %.1f %.1f)\n",s.x,s.y,s.phase,before.x,before.y);assert(0);}
        if(s.location==before.location&&s.flash==0)assert(std::hypot(s.x-before.x,s.y-before.y)<=90*.05f+.02f);
        if(before.phase==WC_CHOP&&s.phase==WC_TO_HOME){assert(chop>=149.9f&&chop<150.2f);chop=0;}
        if(before.phase==WC_SLEEP&&s.phase==WC_LEAVE_HOME){assert(sleep>=149.9f&&sleep<150.2f);sleep=0;}
        if(before.phase==WC_TO_WORK&&s.phase==WC_CHOP){assert(s.x==w0.x&&s.y==w0.y);day=true;}
        if(s.phase!=before.phase){WoodcutterSave copy=s;assert(woodcutter_restore(copy));auto back=woodcutter_save();assert(!memcmp(&back,&s,sizeof(s)));}
    }
    assert(day);
    for(int ph:{WC_CHOP,WC_TO_HOME,WC_TO_BED,WC_SLEEP,WC_LEAVE_HOME,WC_TO_WORK})assert(phases&(1u<<ph));
    // His tree felled while he chops: straight on to the nearest standing tree, the chopping clock kept.
    for(int i=0;i<200;i++)resident_tick(&map,.05f);
    auto chopping=woodcutter_save();assert(chopping.phase==WC_CHOP&&chopping.elapsed>9);
    map.overlay[chopping.tree_y][chopping.tree_x]=0;
    Uint64 t0=SDL_GetPerformanceCounter();resident_tick(&map,.05f);
    double retarget_ms=(SDL_GetPerformanceCounter()-t0)*1000.0/SDL_GetPerformanceFrequency();
    auto moved=woodcutter_save();
    assert(moved.phase==WC_TO_TREE&&!strcmp(woodcutter_line(),"Stop targeting my trees."));
    assert(moved.tree_x!=chopping.tree_x||moved.tree_y!=chopping.tree_y);
    assert(map.overlay[moved.tree_y][moved.tree_x]==TILE_TREE&&std::fabs(moved.elapsed-chopping.elapsed)<.2f);
    float walked=0,px=moved.x,py=moved.y;
    for(int i=0;i<2000&&woodcutter_save().phase!=WC_CHOP;i++){resident_tick(&map,.05f);auto s=woodcutter_save();walked+=std::hypot(s.x-px,s.y-py);px=s.x;py=s.y;}
    auto arrived=woodcutter_save();assert(arrived.phase==WC_CHOP&&(arrived.facing==FACE_LEFT||arrived.facing==FACE_RIGHT));
    float straight=std::hypot(arrived.x-chopping.x,arrived.y-chopping.y);
    printf("woodcutter: tree felled at %d,%d -> next %d,%d, walked %.0f px for %.0f straight, retarget %.1f ms\n",
           chopping.tree_x,chopping.tree_y,moved.tree_x,moved.tree_y,walked,straight,retarget_ms);
    assert(walked<=straight*1.5f+8&&retarget_ms<50);   // straight there, not by the trail
    {   // Chopping from a tree's right side while its left (his first choice) is
        // free -- a neighbour felled after he arrived: he keeps facing the tree.
        auto s=woodcutter_save();s.phase=WC_CHOP;s.flash=0;s.transfer_pending=0;
        s.x=(s.tree_x+1)*32.0f-7;s.y=(s.tree_y+1)*32.0f-41;s.facing=FACE_LEFT;
        assert(can_occupy(&map,s.tree_x*32.0f-21,(s.tree_y+1)*32.0f-41,tilemap_pixel_solid));   // left side free
        assert(woodcutter_restore(s));
        for(int i=0;i<10;i++)resident_tick(&map,.05f);
        assert(woodcutter_save().phase==WC_CHOP&&woodcutter_save().facing==FACE_LEFT);
    }
    // Every tree on the island is his: with all but one far one felled, he walks to that one.
    static decltype(map.overlay) kept;memcpy(kept,map.overlay,sizeof(kept));
    auto here=woodcutter_save();int far_x=-1,far_y=-1;
    float far_d=0;
    {   // the island tree farthest from him that he can walk to
        std::vector<bool> seen((size_t)MAP_WIDTH*MAP_HEIGHT);std::vector<int> q={here.tree_y*MAP_WIDTH+here.tree_x};seen[q[0]]=true;
        for(size_t h=0;h<q.size();h++)for(int d=0;d<4;d++){
            int x=q[h]%MAP_WIDTH+(d==0)-(d==1),y=q[h]/MAP_WIDTH+(d==2)-(d==3);
            if(x<0||y<0||x>=MAP_WIDTH||y>=MAP_HEIGHT||seen[(size_t)y*MAP_WIDTH+x])continue;seen[(size_t)y*MAP_WIDTH+x]=true;
            if(map.overlay[y][x]==TILE_TREE){float dd=std::hypot(x-here.tree_x,y-here.tree_y);if(dd>far_d){far_d=dd;far_x=x;far_y=y;}}
            else if(tilemap_is_walkable(&map,x,y))q.push_back(y*MAP_WIDTH+x);
        }
    }
    assert(far_d>20);
    {
        for(int y=0;y<MAP_HEIGHT;y++)for(int x=0;x<MAP_WIDTH;x++)if(map.overlay[y][x]==TILE_TREE&&(x!=far_x||y!=far_y))map.overlay[y][x]=0;
        resident_tick(&map,.05f);auto s=woodcutter_save();
        assert(s.phase==WC_TO_TREE&&s.tree_x==far_x&&s.tree_y==far_y);
        printf("woodcutter: only tree left %d,%d (%.0f tiles off, the island's farthest) -> he heads for it\n",far_x,far_y,far_d);
    }
    // Every tree on the island gone: home to the sofa for chopping time, then bed.
    for(int y=0;y<MAP_HEIGHT;y++)for(int x=0;x<MAP_WIDTH;x++)if(map.overlay[y][x]==TILE_TREE)map.overlay[y][x]=0;
    for(int i=0;i<2&&woodcutter_save().phase!=WC_NO_TREES_HOME;i++)resident_tick(&map,.05f);
    assert(woodcutter_save().phase==WC_NO_TREES_HOME);
    assert(!strcmp(woodcutter_line(),"Well, look at that. You ruined all my fun. Now there's nothing left for me to chop away at. Get lost, kid."));
    unsigned seen=0;
    for(int i=0;i<40000;i++){resident_tick(&map,.05f);auto s=woodcutter_save();seen|=1u<<s.phase;if(s.phase==WC_SLEEP&&(seen&(1u<<WC_COUCH)))break;}
    assert(seen&(1u<<WC_TO_COUCH)&&seen&(1u<<WC_COUCH)&&seen&(1u<<WC_COUCH_TO_BED)&&woodcutter_save().phase==WC_SLEEP);
    for(int i=0;i<4000&&woodcutter_save().phase==WC_SLEEP;i++)resident_tick(&map,.05f);
    assert(woodcutter_save().phase==WC_TO_COUCH);   // woke with still no trees
    memcpy(map.overlay,kept,sizeof(kept));
    resident_reset();
    puts("woodcutter: first tree, a whole day at two-hour chop and sleep, tree felled -> straight to the nearest, any island tree is his, every island tree gone -> sofa then bed, save/load each phase");
}

// The girl's mother: kitchen an hour, a free shelf, the desk (in line behind
// the grandmother when she has it), home; two cycles, saved at every phase.
static void mother_checks() {
    resident_reset();resident_tick(&map,.05f);
    auto m0=mother_save();assert(m0.phase==MO_KITCHEN&&m0.location==3&&mother_valid(m0));
    unsigned phases=0;int cycles=0,last=-1;float kitchen=0,browse=0,buy=0;bool queued=false;
    for(int frame=0;frame<40000&&cycles<2;frame++) {
        auto before=mother_save();
        if(before.phase==MO_KITCHEN)kitchen+=.05f;
        if(before.phase==MO_BROWSE)browse+=.05f;
        if(before.phase==MO_BUY)buy+=.05f;
        resident_tick(&map,.05f);auto s=mother_save();
        assert(mother_valid(s));phases|=1u<<s.phase;
        if(s.phase!=last){printf("mother phase %d room %d at %.0f %.0f\n",s.phase,s.location,s.x,s.y);last=s.phase;}
        if(s.location<0)assert(can_occupy(&map,s.x,s.y,tilemap_pixel_solid));
        else {InteriorMap im;interior_load(&im,s.location);assert(interior_feet_fit(&im,s.x,s.y));}
        if(s.location==before.location&&s.flash==0)assert(std::hypot(s.x-before.x,s.y-before.y)<=90*.05f+.02f);
        if(before.phase==MO_KITCHEN&&s.phase==MO_LEAVE_HOME){assert(kitchen>=74.9f&&kitchen<75.2f);kitchen=0;}
        if(before.phase==MO_BROWSE&&s.phase!=MO_BROWSE){assert(browse>=4.99f&&browse<5.1f);browse=0;}
        if(before.phase==MO_BUY&&s.phase==MO_LEAVE_SHOP){assert(buy>=4.99f&&buy<5.1f);buy=0;}
        if(before.phase==MO_TO_KITCHEN&&s.phase==MO_KITCHEN)cycles++;
        // never two at one shelf, never two at the desk
        auto g=grandmother_save();auto c=bookshop_clerk_save();
        if(s.phase==MO_BROWSE){
            assert(!(g.phase==GM_SEARCH&&g.shelf==s.shelf));
            assert(!(c.browsing&&c.stop==s.shelf));
        }
        if(s.phase==MO_BUY)assert(g.phase!=GM_DESK);
        queued|=s.phase==MO_QUEUE;
        if(s.phase!=before.phase){MotherSave copy=s;assert(mother_restore(copy));auto back=mother_save();assert(!memcmp(&back,&s,sizeof(s)));}
    }
    assert(cycles==2);
    for(int ph=MO_KITCHEN;ph<=MO_TO_KITCHEN;ph++)if(ph!=MO_QUEUE)assert(phases&(1u<<ph));
    // In line: the grandmother at the desk as the mother finishes browsing.
    resident_reset();resident_tick(&map,.05f);
    for(int i=0;i<40000&&!(mother_save().phase==MO_BROWSE&&mother_save().elapsed>4.5f);i++)resident_tick(&map,.05f);
    assert(mother_save().phase==MO_BROWSE);   // half a second of browsing left
    {auto g=grandmother_save();g.phase=GM_DESK;g.location=1;g.x=BOOKSHOP_DESK.x;g.y=BOOKSHOP_DESK.y;g.elapsed=0;g.shelf=-1;g.flash=0;g.transfer_pending=0;assert(grandmother_restore(g));}
    for(int i=0;i<200&&mother_save().phase==MO_BROWSE;i++)resident_tick(&map,.05f);
    assert(mother_save().phase==MO_QUEUE&&!strcmp(mother_line(),"I'll wait my turn."));
    bool stepped_up=false;
    for(int i=0;i<400&&!stepped_up;i++){
        resident_tick(&map,.05f);auto s=mother_save();auto g=grandmother_save();
        if(s.phase==MO_TO_DESK||s.phase==MO_BUY){assert(g.phase!=GM_DESK&&g.phase!=GM_TO_DESK);stepped_up=true;}
        else assert(s.phase==MO_QUEUE);
    }
    assert(stepped_up);
    resident_reset();
    printf("mother: two cycles (75 s kitchen, 5 s browse/buy), shelves and desk never shared, queued behind the grandmother%s, save/load each phase\n",
           queued?" (also on her own)":"");
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);
    {   // The camera scrolls by screen pixels (no stutter); sprites snap to the art grid themselves.
        Camera c={};c.zoom=1;c.screen_w=640;c.screen_h=480;camera_place(&c,0,0);
        assert(cam_px(&c,101)-cam_px(&c,100)==1);
        assert(art_snap(101)==100&&art_snap(102)==102&&art_snap(103.9f)==102);
    }
    SDL_SetMainReady();assert(SDL_Init(SDL_INIT_VIDEO)==0);IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren=SDL_CreateSoftwareRenderer(surface);
    tilemap_init_tile_cache(ren);
    assert(story_people_init(ren));
    appearance_checks(ren);
    unsigned seed=argc>1?std::strtoul(argv[1],nullptr,10):387;
    tilemap_build_overworld_phase1(&map,seed);
    tilemap_build_overworld_phase2(&map,seed);
    grandmother_checks(ren,seed);
    woodcutter_checks();
    mother_checks();
    bookshop_checks(ren,seed);
    resident_reset();
    assert(!strcmp(resident_line(),"these new stoves scare me, i'm always afraid of a sudden gas leak"));
    resident_reset();
    // The whole kitchen loop must move, visit both work surfaces and take the
    // one-tile aisle below them without crossing furniture. Resume each leg.
    unsigned kitchen_legs=0;
    unsigned paused_surfaces=0;
    for(int frame=0;frame<300;frame++) {
        resident_tick(&map,.05f);auto s=resident_save();
        assert(s.phase==RES_WORK);
        assert(s.y<=248);
        if(s.kitchen_pause>0) {
            assert(s.facing==FACE_UP);
            paused_surfaces|=s.kitchen_leg==1?1:2;
            if(s.kitchen_pause==2) {
                // A full second remains still, including after save restoration.
                assert(resident_restore(s));
                for(int i=0;i<20;i++)resident_tick(&map,.05f);
                auto paused=resident_save();
                assert(paused.x==s.x && paused.y==s.y && paused.facing==FACE_UP);
                assert(std::fabs(paused.kitchen_pause-1)<.001);
                assert(resident_restore(s));
            }
        }
        InteriorMap im;interior_load(&im,4);assert(interior_feet_fit(&im,s.x,s.y));
        if(!(kitchen_legs&(1u<<s.kitchen_leg))) {
            kitchen_legs|=1u<<s.kitchen_leg;assert(resident_restore(s));
            assert(resident_save().kitchen_leg==s.kitchen_leg);
        }
    }
    assert(kitchen_legs==63 && paused_surfaces==3);
    resident_reset();
    for(int hour=1;hour<=7;hour++) {
        resident_advance_hour(&map);auto s=resident_save();
        assert(s.world_seconds==hour*3600);
        if(hour==1)assert(s.phase==RES_LEAVE_HOME);
        if(hour==2)assert(s.phase==RES_SLEEP && s.location==3);
        if(hour==3)assert(s.phase==RES_WORK && s.location==4);
    }
    puts("kitchen: all six walking legs collision-checked; hourly skips cross departure, sleep and return");
    resident_reset();
    int visited=0,cycles=0,old_phase=-1;bool saved[8]={};
    ResidentSave outdoor_sample={};
    int diagonal_run=0,longest_diagonal_run=0,diagonal_facing=-1;
    int indoor_diagonal_run=0,longest_indoor_diagonal_run=0,indoor_facing=-1;
    double entered=0;
    for(int frame=0;frame<40000 && cycles<2;frame++) {
        auto before=resident_save();resident_tick(&map,.05f);auto s=resident_save();
        if(before.flash>0 && s.flash>0) {
            assert(before.facing==s.facing && before.transition_frame==s.transition_frame);
            if(before.location==s.location)assert(before.x==s.x && before.y==s.y);
        }
        if(s.phase==RES_TO_PARENTS && outdoor_sample.magic==0)outdoor_sample=s;
        assert(std::fabs(s.world_seconds-before.world_seconds-2.4)<.001);
        if(s.phase!=old_phase) {
            printf("seed %u world %.1f phase %d room %d position %.1f %.1f\n",seed,s.world_seconds,s.phase,s.location,s.x,s.y);
            if(old_phase==RES_WORK||old_phase==RES_SLEEP)
                assert(std::fabs(s.world_seconds-entered-3600)<5);
            entered=s.world_seconds;old_phase=s.phase;visited|=1<<s.phase;
            if(s.phase==RES_WORK && visited==255)cycles++;
            if(s.phase==RES_WORK||s.phase==RES_SLEEP) {
                InteriorMap im;interior_load(&im,s.location);
                SDL_SetRenderDrawColor(ren,0,0,0,255);SDL_RenderClear(ren);
                interior_draw(&im,ren,tilemap_get_town_tex());
                Camera cam={};cam.zoom=1;cam.screen_w=640;cam.screen_h=480;
                StoryNpcPos p={RESIDENT_STORY_ID,s.x,s.y,-1};story_npc_draw(p,ren,&cam);
                interior_draw_over_player(&im,ren,s.x,s.y,28,40,s.y+40);
                char out[160];snprintf(out,sizeof(out),"build_tmp/npc_review/routine_%s.png",s.phase==RES_WORK?"kitchen":"sleep");
                assert(IMG_SavePNG(surface,out)==0);
            }
        }
        if(s.location<0) {
            assert(can_occupy(&map,s.x,s.y,tilemap_pixel_solid));
            assert(resident_on_trail(&map,s.x,s.y,true));
            float dx=s.x-before.x,dy=s.y-before.y;
            if(before.location<0 && s.flash==0 && std::fabs(dx)>1 && std::fabs(dy)>1) {
                assert(std::hypot(dx,dy)<=90*.05f+.02f);
                if(s.facing==diagonal_facing)diagonal_run++;
                else {diagonal_facing=s.facing;diagonal_run=1;}
                longest_diagonal_run=std::max(longest_diagonal_run,diagonal_run);
            } else diagonal_run=0;
        }
        else {
            InteriorMap im;interior_load(&im,s.location);assert(interior_feet_fit(&im,s.x,s.y));
            float dx=s.x-before.x,dy=s.y-before.y;
            if(before.location==s.location && s.flash==0 && std::fabs(dx)>.1f && std::fabs(dy)>.1f) {
                assert(std::hypot(dx,dy)<=90*.05f+.02f);
                if(s.facing==indoor_facing)indoor_diagonal_run++;
                else {indoor_facing=s.facing;indoor_diagonal_run=1;}
                longest_indoor_diagonal_run=std::max(longest_indoor_diagonal_run,indoor_diagonal_run);
            } else indoor_diagonal_run=0;
        }
        if(s.phase==RES_LEAVE_HOME||s.phase==RES_TO_PARENTS)assert(!strcmp(resident_line(),"heading over to my parents house right now, please leave me"));
        if(s.phase==RES_TO_BED)assert(!strcmp(resident_line(),"time for bed *yawnnnnn*"));
        if(s.phase==RES_SLEEP)assert(!strcmp(resident_line(),"zzzz"));
        if(s.phase==RES_LEAVE_PARENTS||s.phase==RES_TO_HOME||s.phase==RES_TO_WORK)assert(!strcmp(resident_line(),"Sorry i'm busy at the moment"));
        StoryNpcPos p;StoryWhere w={s.location<0?STATE_OVERWORLD:STATE_INTERIOR,&map,s.location,-1,nullptr,false};
        if(s.location>=0) {
            for(int i=0;i<map.num_doors;i++)if(map.doors[i].interior_id==s.location && map.doors[i].x>=map.towns[0].x && map.doors[i].x<map.towns[0].x+156 && map.doors[i].y>=map.towns[0].y && map.doors[i].y<map.towns[0].y+156){w.door=i;break;}
        }
        assert(resident_here(w,&p));
        StoryNpcPos people[32];int count=story_npcs_here(w,people,32),matches=0;
        for(int i=0;i<count;i++)if(people[i].idx==RESIDENT_STORY_ID)matches++;
        assert(matches==1);
        if(s.location>=0){int door=w.door;w.door=-1;assert(!resident_here(w,&p));w.door=door;}
        w.state=s.location<0?STATE_INTERIOR:STATE_OVERWORLD;assert(!resident_here(w,&p));
        // Exercise actual file persistence in an isolated folder, including
        // saving during every doorway departure flash. Never touch save.dat.
        if(!saved[s.phase] && (s.flash>0 || s.activity_seconds>100)) {
            char cwd[2048];assert(_getcwd(cwd,sizeof(cwd)));
            _mkdir("build_tmp/npc_review/save_test");assert(_chdir("build_tmp/npc_review/save_test")==0);
            Player player={};player.width=28;player.height=40;
            assert(save_write(seed,10,20,player,explored));
            resident_reset();unsigned loaded_seed=0;float x,y;
            assert(save_read(&loaded_seed,&x,&y,&player,explored));
            assert(loaded_seed==seed && x==10 && y==20);
            auto loaded=resident_save();assert(loaded.phase==s.phase && loaded.location==s.location && loaded.world_seconds==s.world_seconds && loaded.flash==s.flash && loaded.transfer_pending==s.transfer_pending && loaded.kitchen_leg==s.kitchen_leg && loaded.kitchen_pause==s.kitchen_pause && loaded.transition_frame==s.transition_frame);
            assert(_chdir(cwd)==0);saved[s.phase]=true;
        }
    }
    assert(cycles==2 && visited==255);
    assert(longest_diagonal_run>=30); // sustained diagonal movement, not a staircase
    assert(longest_indoor_diagonal_run>=10);
    // Loading an older position just off the trail must rejoin it rather
    // than strand the resident or permit grass shortcuts on the rest of the trip.
    bool rejoined=false;
    for(int dx=-24;dx<=24 && !rejoined;dx+=8) {
        auto old=outdoor_sample;old.x+=dx;old.flash=0;
        if(resident_on_trail(&map,old.x,old.y,true) || !can_occupy(&map,old.x,old.y,tilemap_pixel_solid))continue;
        assert(resident_restore(old));bool reached=false;
        for(int frame=0;frame<100;frame++) {
            resident_tick(&map,.05f);auto s=resident_save();
            bool on=resident_on_trail(&map,s.x,s.y,true);
            if(reached)assert(on);
            reached|=on;
        }
        assert(reached);rejoined=true;
    }
    assert(rejoined);
    // Version 5 has the same player/story record without the new footer.
    char cwd[2048];assert(_getcwd(cwd,sizeof(cwd)));
    assert(_chdir("build_tmp/npc_review/save_test")==0);
    FILE* file=fopen("save.dat","rb");assert(file);fseek(file,0,SEEK_END);long size=ftell(file);rewind(file);
    std::vector<unsigned char> bytes(size);assert(fread(bytes.data(),1,size,file)==size);fclose(file);
    const size_t base_size=size-sizeof(ResidentSave)-sizeof(BookshopClerkSave)-sizeof(GrandmotherSave)-sizeof(WoodcutterSave)-sizeof(FisherSave)-sizeof(SailorFisherSave)-sizeof(MotherSave);
    // V12 preserves all previous residents; the new fisher starts in bed.
    // V14 has every resident but the mother: she starts at her stove.
    auto version14=bytes;version14.resize(size-sizeof(MotherSave));
    unsigned v14=14;memcpy(version14.data()+4,&v14,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(version14.data(),1,version14.size(),file)==version14.size());fclose(file);
    {unsigned sd;float sx,sy;Player pl;assert(save_read(&sd,&sx,&sy,&pl,explored));}
    assert(mother_save().phase==MO_KITCHEN&&mother_save().location==3);
    auto version12=bytes;version12.resize(size-sizeof(FisherSave)-sizeof(SailorFisherSave)-sizeof(MotherSave));
    unsigned v12=12;memcpy(version12.data()+4,&v12,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(version12.data(),1,version12.size(),file)==version12.size());fclose(file);
    {unsigned sd;float sx,sy;Player pl;assert(save_read(&sd,&sx,&sy,&pl,explored));}
    assert(fisher_save().epoch==-1);
    // V11 has the grandmother but no woodcutter: he starts his day fresh.
    auto version11=bytes;version11.resize(size-sizeof(WoodcutterSave)-sizeof(FisherSave)-sizeof(SailorFisherSave)-sizeof(MotherSave));
    unsigned v11=11;memcpy(version11.data()+4,&v11,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(version11.data(),1,version11.size(),file)==version11.size());fclose(file);
    {unsigned sd;float sx,sy;Player pl;assert(save_read(&sd,&sx,&sy,&pl,explored));}
    assert(woodcutter_save().phase==WC_CHOP&&woodcutter_save().tree_x==-1);
    // V10 has both existing residents, but no grandmother footer.
    auto version10=bytes;version10.resize(size-sizeof(GrandmotherSave)-sizeof(WoodcutterSave)-sizeof(FisherSave)-sizeof(SailorFisherSave)-sizeof(MotherSave));
    unsigned v10=10;memcpy(version10.data()+4,&v10,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(version10.data(),1,version10.size(),file)==version10.size());fclose(file);
    unsigned v10seed;float v10x,v10y;Player v10player;
    assert(save_read(&v10seed,&v10x,&v10y,&v10player,explored));
    assert(grandmother_save().phase==GM_COUCH&&grandmother_save().elapsed==0);
    // V9 preserves the original resident footer and starts just the new clerk.
    ResidentSave v9_resident;memcpy(&v9_resident,bytes.data()+base_size,sizeof(v9_resident));
    bytes.resize(base_size+sizeof(ResidentSave));
    unsigned restored_seed;float x,y;Player player;
    unsigned version=9;memcpy(bytes.data()+4,&version,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(bytes.data(),1,bytes.size(),file)==bytes.size());fclose(file);
    assert(save_read(&restored_seed,&x,&y,&player,explored));
    assert(resident_save().world_seconds==v9_resident.world_seconds && resident_save().phase==v9_resident.phase);
    assert(bookshop_clerk_save().stop==0 && bookshop_clerk_save().pause==3);
    // V7/V8 used the 56-byte prefix before transition_frame.
    bytes.resize(base_size+offsetof(ResidentSave,transition_frame));
    float legacy_flash=ACTOR_FLASH_STEP;
    memcpy(bytes.data()+base_size+offsetof(ResidentSave,flash),&legacy_flash,sizeof(legacy_flash));
    version=8;memcpy(bytes.data()+4,&version,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(bytes.data(),1,bytes.size(),file)==bytes.size());fclose(file);
    assert(save_read(&restored_seed,&x,&y,&player,explored));
    assert(resident_save().transition_frame==0 && resident_save().flash==ACTOR_APPEAR_T);
    // V7 used the current pause field's bytes as padding. Ignore arbitrary
    // padding rather than rejecting an otherwise valid older save.
    version=7;memcpy(bytes.data()+4,&version,4);
    memset(bytes.data()+base_size+offsetof(ResidentSave,kitchen_pause),255,sizeof(float));
    file=fopen("save.dat","wb");assert(file);assert(fwrite(bytes.data(),1,bytes.size(),file)==bytes.size());fclose(file);
    assert(save_read(&restored_seed,&x,&y,&player,explored));
    assert(resident_save().kitchen_pause==0 && resident_save().world_seconds>0);
    bytes.resize(base_size+offsetof(ResidentSave,kitchen_leg));version=6;memcpy(bytes.data()+4,&version,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(bytes.data(),1,bytes.size(),file)==bytes.size());fclose(file);
    assert(save_read(&restored_seed,&x,&y,&player,explored));
    assert(resident_save().kitchen_leg==0 && resident_save().world_seconds>0);
    bytes.resize(base_size);version=5;memcpy(bytes.data()+4,&version,4);
    file=fopen("save.dat","wb");assert(file);assert(fwrite(bytes.data(),1,bytes.size(),file)==bytes.size());fclose(file);
    assert(save_read(&restored_seed,&x,&y,&player,explored));
    assert(resident_save().world_seconds==0 && resident_save().phase==RES_WORK);
    assert(_chdir(cwd)==0);
    printf("PASS: two cycles, collision, 30-minute clock, dialogue, location identity and save/load (seed %u)\n",seed);
    story_people_free();tilemap_free_tile_cache();SDL_DestroyRenderer(ren);SDL_FreeSurface(surface);IMG_Quit();SDL_Quit();
}
