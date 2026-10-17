#include "resident_path.h"
#include "entity.h"
#include "interior.h"
#include "overworld.h"
#include "towns.h"
#include "resident.h"
#include "collision.h"
#include <unordered_map>
#include <cstdint>
#include <SDL2/SDL.h>
#include <algorithm>
#include <cmath>
#include <queue>

bool resident_find_route(ResidentPoint start, ResidentPoint target, int step, int ox, int oy, int w, int h,
                bool rejoin, const std::function<bool(ResidentPoint)>& fits,
                const std::function<bool(ResidentPoint,ResidentPoint,bool)>& segment,
                std::vector<ResidentPoint>& route, ResidentPoint& route_start, size_t& next_point,
                const std::function<float(ResidentPoint)>& weight) {
    auto point=[&](int i)->ResidentPoint {return {(float)(ox+i%w*step),(float)(oy+i/w*step)};};
    auto nearest=[&](ResidentPoint p,bool rejoin=false)->int {
        int cx=(int)std::round((p.x-ox)/step),cy=(int)std::round((p.y-oy)/step);
        float best=1e20f; int found=-1;
        for(int y=cy-6;y<=cy+6;y++) for(int x=cx-6;x<=cx+6;x++) {
            if(x<0||y<0||x>=w||y>=h) continue;
            int i=y*w+x; ResidentPoint q=point(i);
            float d=std::hypot(q.x-p.x,q.y-p.y);
            if(d<best && fits(q) && segment(p,q,!rejoin)) {best=d;found=i;}
        }
        return found;
    };
    int a=nearest(start,rejoin),b=nearest(target);
    if(a<0||b<0) {SDL_Log("Resident: inaccessible endpoint (%.0f %.0f -> %.0f %.0f)",start.x,start.y,target.x,target.y);return false;}
    struct Open {float score;int i;bool operator<(const Open& p)const{return score>p.score;}};
    std::priority_queue<Open> open;
    std::vector<float> cost(w*h,1e20f);
    std::vector<int> parent(w*h,-1);
    std::vector<unsigned char> closed(w*h,0);
    cost[a]=0;open.push({0,a});
    while(!open.empty()) {
        int i=open.top().i;open.pop();if(closed[i])continue;closed[i]=1;
        if(i==b)break;
        ResidentPoint p=point(i);
        const int dx[8]={1,-1,0,0,1,1,-1,-1};
        const int dy[8]={0,0,1,-1,1,-1,1,-1};
        for(int d=0;d<8;d++) {
            int x=i%w+dx[d],y=i/w+dy[d];
            if(x<0||y<0||x>=w||y>=h)continue;
            int j=y*w+x;if(closed[j])continue;ResidentPoint q=point(j);
            if(!segment(p,q,true))continue;
            float nc=cost[i]+step*(d<4?1.0f:1.41421356237f)*(weight?weight(q):1.0f);
            if(nc>=cost[j])continue;
            cost[j]=nc;parent[j]=i;ResidentPoint end=point(b);
            open.push({nc+std::hypot(q.x-end.x,q.y-end.y),j});
        }
    }
    if(!closed[b]){SDL_Log("Resident: no route to %.0f %.0f",target.x,target.y);return false;}
    route.clear();route.push_back(target);
    for(int i=b;i!=a;i=parent[i])route.push_back(point(i));
    route.push_back(point(a));std::reverse(route.begin(),route.end());next_point=0;
    {
        // Join visible waypoints into straight runs. The entire feet box is
        // sampled along every proposed line in every area, so bends cannot
        // cut across grass, walls or furniture.
        std::vector<ResidentPoint> smooth;
        ResidentPoint anchor=start;size_t first=0;
        if(rejoin){smooth.push_back(route[0]);anchor=route[0];first=1;}
        while(first<route.size()) {
            size_t last=first;
            for(size_t j=first;j<route.size();j++) {
                if(!segment(anchor,route[j],true))break;
                last=j;
            }
            smooth.push_back(route[last]);anchor=route[last];first=last+1;
        }
        route.swap(smooth);
    }
    route_start=start;
    return true;
}

bool resident_follow_route(const std::vector<ResidentPoint>& route, size_t& next_point, ResidentPoint route_start,
                           float& x, float& y, int& facing, float budget) {
    bool moved=false;
    while(next_point<route.size() && budget>0) {
        ResidentPoint p=route[next_point];float dx=p.x-x,dy=p.y-y,d=std::hypot(dx,dy);
        if(d<.01f){next_point++;continue;}
        // Face along the whole leg, so an exact 45-degree one cannot flicker.
        ResidentPoint from=next_point?route[next_point-1]:route_start;
        float hx=p.x-from.x,hy=p.y-from.y;
        facing=std::fabs(hx)>std::fabs(hy)?(hx<0?FACE_LEFT:FACE_RIGHT):(hy<0?FACE_UP:FACE_DOWN);
        float step=std::min(d,budget);
        x+=dx/d*step;y+=dy/d*step;budget-=step;moved=true;
        if(step==d)next_point++;
    }
    return moved;
}

static bool town_door(const Tilemap* map, int i, int interior) {
    const auto& t=map->towns[0];
    const auto& d=map->doors[i];
    return d.interior_id==interior&&d.x>=t.x&&d.x<t.x+TOWN_W&&d.y>=t.y&&d.y<t.y+TOWN_H;
}
int resident_town_door(const Tilemap* map, int interior) {
    if(!map)return -1;
    // Asked thousands of times a search (resident_on_trail). Town 0 has one
    // door per room, so a remembered index that still fits is the answer --
    // checked rather than trusted, so a rebuilt world finds its own.
    static int known[16]={-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1};
    int* cached=interior>=0&&interior<16?&known[interior]:nullptr;
    if(cached&&*cached>=0&&*cached<map->num_doors&&town_door(map,*cached,interior))return *cached;
    for(int i=0;i<map->num_doors;i++)
        if(town_door(map,i,interior)){if(cached)*cached=i;return i;}
    return -1;
}
ResidentPoint resident_outside(const Tilemap* map, int door) {
    Overworld ow={};Player player={};player.width=28;player.height=40;
    overworld_stand_before_door_idx(&ow,&player,map,door);
    return {ow.x,ow.y};
}
ResidentPoint resident_entry(int interior) {
    InteriorMap im;interior_load(&im,interior);
    InteriorPlayer ip={};Player player={};interior_player_init(&ip,&player,&im);
    return {ip.x,ip.y};
}

namespace {
bool walkable(const Tilemap* map,ResidentPoint p){return can_occupy(map,p.x,p.y,tilemap_pixel_solid);}
bool trail_at(const Tilemap* map,ResidentPoint p){return resident_on_trail(map,p.x,p.y,false);}
// What the feet at a whole pixel stand on, remembered for one search: the
// grid's edges share their pixels, each asked by up to sixteen. Walkable and
// on-the-trail are asked apart: the first at every pixel of a way, the
// second (49 samples) only every fourth.
enum { WALK_KNOWN=1, WALKABLE=2, TRAIL_KNOWN=4, TRAIL=8 };
std::unordered_map<uint64_t,uint8_t> memo;
uint8_t& memo_at(ResidentPoint p) {
    // Floored: the feet are asked at whole-pixel offsets from p, so p and
    // its floor give the same answer.
    int x=(int)std::floor(p.x),y=(int)std::floor(p.y);
    return memo[(uint64_t)(uint32_t)x<<32|(uint32_t)y];
}
bool walk_here(const Tilemap* map,ResidentPoint p) {
    uint8_t& g=memo_at(p);
    if(!(g&WALK_KNOWN))g|=WALK_KNOWN|(walkable(map,{std::floor(p.x),std::floor(p.y)})?WALKABLE:0);
    return g&WALKABLE;
}
bool trail_here(const Tilemap* map,ResidentPoint p) {
    if(!walk_here(map,p))return false;
    uint8_t& g=memo_at(p);
    if(!(g&TRAIL_KNOWN))g|=TRAIL_KNOWN|(trail_at(map,{std::floor(p.x),std::floor(p.y)})?TRAIL:0);
    return g&TRAIL;
}
// Every whole-pixel cell a straight walk from a to b passes through, in
// order (a grid walk, Amanatides-Woo): the feet are asked at whole-pixel
// offsets, so a position fits exactly when its floored pixel does, and
// asking these cells asks every position the walker will stand at --
// sampling along the line skips the corner cells of a diagonal. At an exact
// corner both cells beside it are asked.
template<class Fits> bool every_cell(ResidentPoint a,ResidentPoint b,Fits fits) {
    int x=(int)std::floor(a.x),y=(int)std::floor(a.y);
    const int ex=(int)std::floor(b.x),ey=(int)std::floor(b.y);
    const float dx=b.x-a.x,dy=b.y-a.y,inf=1e30f;
    const int sx=dx>0?1:-1,sy=dy>0?1:-1;
    const float step_x=dx!=0?std::fabs(1/dx):inf,step_y=dy!=0?std::fabs(1/dy):inf;
    float next_x=dx!=0?(sx>0?x+1-a.x:a.x-x)*step_x:inf,next_y=dy!=0?(sy>0?y+1-a.y:a.y-y)*step_y:inf;
    if(!fits(x,y))return false;
    for(int guard=std::abs(ex-x)+std::abs(ey-y)+2;(x!=ex||y!=ey)&&guard>0;guard--) {
        if(next_x<next_y){x+=sx;next_x+=step_x;}
        else if(next_y<next_x){y+=sy;next_y+=step_y;}
        else {
            if(!fits(x+sx,y)||!fits(x,y+sy))return false;
            x+=sx;y+=sy;next_x+=step_x;next_y+=step_y;
        }
        if(!fits(x,y))return false;
    }
    return true;
}
// The way fits, and when `trail` keeps to the trail too (asked every fourth
// pixel: a trail has nothing one pixel wide). A search asks walkability
// every other pixel, which is quick and nearly always right; the route it
// finds is then checked cell by cell (route_exact), and only if that fails is
// the search run again with every cell asked (exact_ways).
bool exact_ways=false;
bool clear_way(const Tilemap* map,ResidentPoint a,ResidentPoint b,bool trail) {
    if(exact_ways) {
        if(!every_cell(a,b,[&](int x,int y){return walk_here(map,{(float)x,(float)y});}))return false;
    } else {
        int n=std::max(1,(int)std::ceil(std::hypot(a.x-b.x,a.y-b.y)/2));
        for(int i=0;i<=n;i++)if(!walk_here(map,{a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n}))return false;
    }
    if(!trail)return true;
    int n=std::max(1,(int)std::ceil(std::hypot(a.x-b.x,a.y-b.y)/4));
    for(int i=0;i<=n;i++)if(!trail_here(map,{a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n}))return false;
    return true;
}
// The route as walked, every position checked: a leg that cuts a corner
// cell is replaced by a small exact search round just that leg -- cheaper
// than searching the whole way exactly. False if a leg cannot be mended.
bool mend_route(const Tilemap* map,ResidentPoint start,std::vector<ResidentPoint>& route) {
    auto fits=[&](int x,int y){return walk_here(map,{(float)x,(float)y});};
    std::vector<ResidentPoint> mended;
    ResidentPoint from=start;
    for(ResidentPoint to:route) {
        if(!every_cell(from,to,fits)) {
            const int step=4,margin=2*TILE_SIZE;
            int ox=(int)std::min(from.x,to.x)-margin,oy=(int)std::min(from.y,to.y)-margin;
            int w=((int)std::max(from.x,to.x)+margin-ox)/step,h=((int)std::max(from.y,to.y)+margin-oy)/step;
            std::vector<ResidentPoint> leg;ResidentPoint origin;size_t next;
            exact_ways=true;
            bool ok=resident_find_route(from,to,step,ox,oy,w,h,false,
                [&](ResidentPoint p){return walk_here(map,p);},
                [&](ResidentPoint a,ResidentPoint b,bool){return clear_way(map,a,b,false);},leg,origin,next);
            exact_ways=false;
            if(!ok)return false;
            mended.insert(mended.end(),leg.begin(),leg.end());
        } else mended.push_back(to);
        from=to;
    }
    route.swap(mended);
    return true;
}
// A search run quick, its route mended where it cuts a corner; exact
// throughout only if that fails.
template<class Search> bool checked(const Tilemap* map,ResidentPoint start,std::vector<ResidentPoint>& out,Search search) {
    memo.clear();
    exact_ways=false;
    bool found=search(out)&&mend_route(map,start,out);
    if(!found){exact_ways=true;out.clear();found=search(out);exact_ways=false;}
    memo.clear();
    return found;
}
// clear_way over grass, outside a search (nothing remembered).
bool clear_way_now(const Tilemap* map,ResidentPoint a,ResidentPoint b) {
    return every_cell(a,b,[&](int x,int y){return walkable(map,{(float)x,(float)y});});
}
// The trail point nearest p reachable straight across the grass: offsets
// tried nearest first, so the first that works is the answer.
constexpr int GRASS_REACH=16*TILE_SIZE,GRASS_STEP=8;
bool trail_access(const Tilemap* map,ResidentPoint p,ResidentPoint* out) {
    if(trail_at(map,p)){*out=p;return true;}
    static std::vector<ResidentPoint> offsets;
    if(offsets.empty()) {
        for(int dy=-GRASS_REACH;dy<=GRASS_REACH;dy+=GRASS_STEP)
            for(int dx=-GRASS_REACH;dx<=GRASS_REACH;dx+=GRASS_STEP)
                if(dx*dx+dy*dy<=GRASS_REACH*GRASS_REACH)offsets.push_back({(float)dx,(float)dy});
        std::sort(offsets.begin(),offsets.end(),[](ResidentPoint a,ResidentPoint b){return a.x*a.x+a.y*a.y<b.x*b.x+b.y*b.y;});
    }
    for(ResidentPoint o:offsets) {
        ResidentPoint q={p.x+o.x,p.y+o.y};
        if(trail_at(map,q)&&clear_way_now(map,p,q)){*out=q;return true;}
    }
    return false;
}
// The trail point nearest p over any ground, for an end too far from the
// trail for a straight walk to it; and a search over the grass between two
// points, its own route appended to out. Unweighted, so it heads straight
// for its end and opens little.
bool nearest_trail(const Tilemap* map,ResidentPoint p,ResidentPoint* out) {
    // Nearest on foot, not in a straight line: a flood over the walkable
    // tiles from p, so a trail across water or behind woods is never picked
    // over one he can walk to.
    int sx=(int)(p.x+(HB_X1+HB_X2)*0.5f)/TILE_SIZE,sy=(int)(p.y+(HB_Y1+HB_Y2)*0.5f)/TILE_SIZE;
    if(sx<0||sy<0||sx>=MAP_WIDTH||sy>=MAP_HEIGHT)return false;
    std::vector<bool> seen((size_t)MAP_WIDTH*MAP_HEIGHT,false);
    std::vector<int> queue={sy*MAP_WIDTH+sx};
    seen[queue[0]]=true;
    for(size_t head=0;head<queue.size();head++) {
        int x=queue[head]%MAP_WIDTH,y=queue[head]/MAP_WIDTH;
        // the feet in the middle of this tile
        ResidentPoint q={x*TILE_SIZE+TILE_SIZE*0.5f-(HB_X1+HB_X2)*0.5f,y*TILE_SIZE+TILE_SIZE*0.5f-(HB_Y1+HB_Y2)*0.5f};
        if(trail_here(map,q)){*out=q;return true;}
        const int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};
        for(int d=0;d<4;d++) {
            int nx=x+dx[d],ny=y+dy[d];
            if(nx<0||ny<0||nx>=MAP_WIDTH||ny>=MAP_HEIGHT||seen[(size_t)ny*MAP_WIDTH+nx])continue;
            seen[(size_t)ny*MAP_WIDTH+nx]=true;
            if(tilemap_is_walkable(map,nx,ny))queue.push_back(ny*MAP_WIDTH+nx);
        }
    }
    return false;
}
bool grass_leg(const Tilemap* map,ResidentPoint a,ResidentPoint b,std::vector<ResidentPoint>& out) {
    // A coarse grid first (a quarter of the cells); the fine one only where
    // the woods leave gaps too narrow for it.
    // Searched round both ends a dozen tiles out, then -- for a walk that must
    // go round a lake or a wood -- forty.
    for(int reach:{12,40})for(int step:{16,8}) {
        const int margin=reach*TILE_SIZE;
        int ox=(int)std::min(a.x,b.x)-margin,oy=(int)std::min(a.y,b.y)-margin;
        int w=((int)std::max(a.x,b.x)+margin-ox)/step,h=((int)std::max(a.y,b.y)+margin-oy)/step;
        std::vector<ResidentPoint> leg;ResidentPoint origin;size_t next;
        if(!resident_find_route(a,b,step,ox,oy,w,h,false,
            [&](ResidentPoint p){return walk_here(map,p);},
            [&](ResidentPoint p,ResidentPoint q,bool){return clear_way(map,p,q,false);},leg,origin,next))continue;
        out.insert(out.end(),leg.begin(),leg.end());
        return true;
    }
    return false;
}
bool trail_route(const Tilemap* map,ResidentPoint start,ResidentPoint target,std::vector<ResidentPoint>& out) {
    ResidentPoint on,off;
    bool straight_on=trail_access(map,start,&on),straight_off=trail_access(map,target,&off);
    if((!straight_on&&!nearest_trail(map,start,&on))||(!straight_off&&!nearest_trail(map,target,&off)))return false;
    out.clear();
    if(on.x!=start.x||on.y!=start.y) {
        if(straight_on)out.push_back(on);
        else if(!grass_leg(map,start,on,out))return false;
    }
    // Trails wind, so the box round both ends is wide; only trail cells are
    // ever opened, so its size costs little.
    const int step=16,margin=40*TILE_SIZE;
    int ox=(int)std::min(on.x,off.x)-margin,oy=(int)std::min(on.y,off.y)-margin;
    int w=((int)std::max(on.x,off.x)+margin-ox)/step,h=((int)std::max(on.y,off.y)+margin-oy)/step;
    std::vector<ResidentPoint> trail;ResidentPoint origin;size_t next;
    if(!resident_find_route(on,off,step,ox,oy,w,h,false,
        [&](ResidentPoint p){return trail_here(map,p);},
        [&](ResidentPoint a,ResidentPoint b,bool){return clear_way(map,a,b,true);},trail,origin,next))return false;
    out.insert(out.end(),trail.begin(),trail.end());
    if(off.x!=target.x||off.y!=target.y) {
        if(straight_off)out.push_back(target);
        else if(!grass_leg(map,off,target,out))return false;
    }
    return true;
}
}
bool resident_trail_route(const Tilemap* map, ResidentPoint start, ResidentPoint target,
                          std::vector<ResidentPoint>& route, ResidentPoint& route_start, size_t& next_point) {
    std::vector<ResidentPoint> out;
    if(!checked(map,start,out,[&](std::vector<ResidentPoint>& o){return trail_route(map,start,target,o);}))return false;
    route.swap(out);route_start=start;next_point=0;
    return true;
}
bool resident_grass_route(const Tilemap* map, ResidentPoint start, ResidentPoint target,
                          std::vector<ResidentPoint>& route, ResidentPoint& route_start, size_t& next_point) {
    std::vector<ResidentPoint> out;
    if(!checked(map,start,out,[&](std::vector<ResidentPoint>& o){return grass_leg(map,start,target,o);}))return false;
    route.swap(out);route_start=start;next_point=0;
    return true;
}

bool resident_way_fits(ResidentPoint a, ResidentPoint b, const std::function<bool(ResidentPoint)>& fits) {
    return every_cell(a,b,[&](int x,int y){return fits({(float)x,(float)y});});
}
