#include "gardener.h"
#include "resident.h"
#include "resident_path.h"
#include "collision.h"
#include "tilemap.h"
#include "camera.h"
#include "npc_sleep.h"
#include <SDL2/SDL_image.h>
#include <cmath>
#include <algorithm>
namespace {
constexpr unsigned MAGIC=0x47415231;
constexpr int cols[]={54,56,58,60,62,64,66,68,70,75,77,79,81,83,85,91,93,95,97};
GardenerSave g={MAGIC,0,0,0,0,0,1,0,FACE_UP,0};
bool talking=false,ready=false,moving=false;
float retry=0;
int count=19;
SDL_Texture *art=nullptr,*pour=nullptr;
ResidentPoint stops[19],plants[19];
bool standing(const Tilemap* m,int i){return m->overlay[m->towns[0].y+88][m->towns[0].x+cols[i]]==TILE_TREE;}
bool fits(const Tilemap* m,ResidentPoint p){return resident_on_trail(m,p.x,p.y)&&can_occupy(m,p.x,p.y,tilemap_pixel_solid);}
bool segment(const Tilemap* m,ResidentPoint a,ResidentPoint b){return resident_way_fits(a,b,[&](ResidentPoint p){return fits(m,p);});}
void next_target(){g.watering=0;g.remaining=0;if(g.target==18&&g.direction==1)g.direction=-1;else if(g.target==0&&g.direction==-1)g.direction=1;g.target+=g.direction;}
void onward(){g.watering=0;g.remaining=0;g.initialized=2;}
}
void gardener_reset(){g={MAGIC,0,0,0,0,0,1,0,FACE_UP,0};talking=ready=moving=false;retry=0;count=19;}
GardenerSave gardener_save(){return g;}
bool gardener_valid(const GardenerSave& s) {
    return s.magic==MAGIC && std::isfinite(s.x) && std::isfinite(s.y) &&
        s.x>=0 && s.y>=0 && s.x<MAP_WIDTH*TILE_SIZE && s.y<MAP_HEIGHT*TILE_SIZE &&
        std::isfinite(s.remaining) && s.remaining>=0 && s.remaining<=3 &&
        std::isfinite(s.anim) && s.anim>=0 && s.anim<.8f &&
        s.target>=0 && s.target<19 && (s.direction==1||s.direction==-1) &&
        (s.watering==0||s.watering==1) && (s.initialized>=0&&s.initialized<=2) &&
        (!s.watering || (s.initialized && s.remaining>0)) &&
        (s.facing==FACE_DOWN||s.facing==FACE_UP||s.facing==FACE_LEFT||s.facing==FACE_RIGHT);
}
bool gardener_restore(const GardenerSave& s){if(!gardener_valid(s))return false;gardener_reset();g=s;return true;}
bool gardener_validate_route(const Tilemap* m){
    if(!m)return false;
    ready=false;
    // Authored street line: sprite feet centred two tiles below the planted row.
    for(int i=0;i<19;i++)stops[i]={(m->towns[0].x+cols[i])*32.0f+2,(m->towns[0].y+90)*32.0f-34};
    for(int i=0;i<19;i++)if(!fits(m,stops[i])||(i&& !segment(m,stops[i-1],stops[i]))){SDL_Log("Gardener: invalid street approach %d (%g,%g)",i,stops[i].x,stops[i].y);return false;}
    // Step off the street to the soil immediately below each planter.
    for(int i=0;i<19;i++) {
        plants[i]={stops[i].x,stops[i].y-24};
        if(!resident_way_fits(stops[i],plants[i],[&](ResidentPoint p){return can_occupy(m,p.x,p.y,tilemap_pixel_solid);})) {
            SDL_Log("Gardener: invalid plant approach %d",i);return false;
        }
    }
    // Move existing saves from the previous street line without resetting the routine.
    if(g.initialized && std::fabs(g.y-(stops[0].y+16))<.01f)g.y=stops[0].y;
    if(g.watering && std::fabs(g.y-stops[0].y)<.01f)g.y=plants[g.target].y;
    ready=true;return true;
}
void gardener_tick(const Tilemap* m,float dt) {
    if(!m||dt<=0)return;
    if(!ready) {
        retry-=dt;
        if(retry>0)return;
        if(!gardener_validate_route(m)){retry=1;return;}
    }
    count=0;
    for(int i=0;i<19;i++)count+=standing(m,i);
    if(!g.initialized) {
        g.target=0;
        while(g.target<18&&!standing(m,g.target))g.target++;
        if(!count)g.target=0;
        g.x=stops[g.target].x;g.y=stops[g.target].y;g.initialized=1;
    }
    if(talking)return;
    moving=false;
    // Consume time at phase boundaries: movement and watering share the same
    // unpaused seconds, even when a caller advances several seconds at once.
    while(dt>0) {
        bool exists=standing(m,g.target);
        if(g.watering&&!exists){onward();continue;}
        if(g.watering) {
            float used=std::min(dt,g.remaining);
            g.remaining-=used;dt-=used;
            g.anim=std::fmod(g.anim+used,.8f);
            if(g.remaining<=0)onward();
            continue;
        }
        // Missing interior stops are crossed; endpoints are always visited.
        if(g.initialized!=2&&!exists&&g.target>0&&g.target<18){
            if(std::fabs(g.y-stops[0].y)>.001f)onward();else next_target();
            continue;
        }
        bool returning=g.initialized==2;
        auto p=stops[g.target];
        if(returning)p={g.x,stops[0].y};
        else if(exists && std::fabs(g.x-p.x)<.001f)p=plants[g.target];
        float distance=std::hypot(p.x-g.x,p.y-g.y);
        if(distance>.001f) {
            retry-=dt;
            if(retry>0)return;
            float used=std::min(dt,distance/90);
            float f=std::min(1.0f,90*used/distance);
            ResidentPoint step={g.x+(p.x-g.x)*f,g.y+(p.y-g.y)*f};
            bool street=std::fabs(g.y-stops[0].y)<.001f && std::fabs(step.y-g.y)<.001f;
            bool clear=street?segment(m,{g.x,g.y},step):
                resident_way_fits({g.x,g.y},step,[&](ResidentPoint at){return can_occupy(m,at.x,at.y,tilemap_pixel_solid);});
            if(!clear) {
                SDL_Log("Gardener: runtime route failure at target %d; preserving progress, retrying in one second",g.target);
                retry=1;
                return;
            }
            g.facing=std::fabs(p.y-g.y)>.001f?(p.y>g.y?FACE_DOWN:FACE_UP):(p.x>g.x?FACE_RIGHT:FACE_LEFT);
            g.x=step.x;g.y=step.y;
            dt-=used;moving=true;
            g.anim=std::fmod(g.anim+used,.8f);
            if(f<1)return;
        }
        if(returning){g.initialized=1;next_target();continue;}
        if(exists && std::fabs(g.y-plants[g.target].y)>.001f)continue;
        if(exists){g.watering=1;g.remaining=3;g.facing=FACE_UP;g.anim=0;}
        else next_target();
    }
}
bool gardener_here(const StoryWhere& w,StoryNpcPos* p){if(!g.initialized||w.state!=STATE_OVERWORLD)return false;*p={GARDENER_ID,g.x,g.y,-1};return true;}
const char* gardener_line(){if(!count)return "Nothing left to water. I still take my walk. Habit, I suppose. Need anything?";if(count==1)return "Well, you're still here. Let's keep you that way. Need anything?";if(count<19)return "Less to water today. Can't say I'm pleased about why. Need anything?";return g.watering?"A little water, a little patience. These ones mostly need patience. Need anything?":"Nineteen plants, two feet, and somehow I'm the one doing all the work. Need anything?";}
void gardener_face(int){talking=true;}
int gardener_facing(){return g.facing;}
void gardener_resume(){talking=false;}
bool gardener_art_init(SDL_Renderer* r){gardener_art_free();art=IMG_LoadTexture(r,"assets/npcs/gardener.png");pour=IMG_LoadTexture(r,"assets/npcs/gardener_water.png");if(art)SDL_SetTextureScaleMode(art,SDL_ScaleModeNearest);if(pour)SDL_SetTextureScaleMode(pour,SDL_ScaleModeNearest);return art&&pour;}
void gardener_art_free(){if(art)SDL_DestroyTexture(art);if(pour)SDL_DestroyTexture(pour);art=pour=nullptr;}
bool gardener_draw(const StoryNpcPos& p,SDL_Renderer* r,const Camera* c) {
    if(p.idx!=GARDENER_ID)return false;
    if(!art||!pour)return true;
    int col=moving&&!talking?npc_walk_col(g.facing,int(g.anim/.2f)):0;
    SDL_Rect src={col*14,npc_sheet_row(g.facing)*20,14,20};
    SDL_Rect dst={cam_screen_x(c,p.x),cam_screen_y(c,p.y),int(28*c->zoom),int(40*c->zoom)};
    if(!g.watering) {SDL_RenderCopy(r,art,&src,&dst);return true;}
    src={0,0,14,20};SDL_RenderCopy(r,pour,&src,&dst);
    // The north-facing spout leads to the soil below the plant. Animation is
    // driven only by the routine timer, so conversation freezes every droplet.
    SDL_SetRenderDrawColor(r,99,175,218,255);
    for(int i=0;i<8;i++) {
        float t=std::fmod(g.anim+i*.1f,.8f)/.8f;
        float x=p.x+16*t,y=p.y+20-16*t-8*std::sin(t*3.14159265f);
        SDL_Rect d={cam_screen_x(c,art_snap(x)),cam_screen_y(c,art_snap(y)),
                    std::max(1,int(2*c->zoom)),std::max(1,int(2*c->zoom))};
        SDL_RenderFillRect(r,&d);
    }
    return true;
}
