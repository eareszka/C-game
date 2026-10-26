#include "../../../src/enemies.cpp"
#include <cassert>
#include <cstdio>
static float gap(float a,float b){return fabsf(a-b);}
int main() {
    int warned=0, charged=0, hot=0, ricochets=0, homing=0, slowing=0, embers=0;
    for(int scenario=0;scenario<5;++scenario) {
        Alber e;
        float lastx=e.x, beamage=0;
        bool previous=false;
        Enemy::TeleLine saved[3];
        for(int f=0;f<3600;++f) {
            if(f==1800) e.hp=e.max_hp*0.49f;
            float px=scenario==1?16:scenario==2?624:320;
            float py=scenario==3?140:scenario==4?44:400;
            e.update(1.0f/60,px,py);
            e.on_idle_frame((f/7)%6,px,py,nullptr,0);
            assert(gap(e.x,lastx)<2.5f); lastx=e.x;
            Enemy::TeleLine lines[4];
            int count=e.telegraphs(lines,4);
            assert(count==0 || count==3);
            for(int cap=0;cap<=3;++cap) {
                Enemy::TeleLine bounded[4]; bounded[cap].stage=-123;
                assert(e.telegraphs(bounded,cap)<=cap && bounded[cap].stage==-123);
            }
            if(count) {
                assert(f>1800);
                if(!previous) {beamage=0; for(int k=0;k<3;++k)saved[k]=lines[k];}
                else beamage+=1.0f/60;
                for(int k=0;k<3;++k) {
                    auto L=lines[k];
                    assert(std::isfinite(L.x0)&&std::isfinite(L.y0)&&std::isfinite(L.x1)&&std::isfinite(L.y1));
                    assert(L.x1>=0 && L.x1<=ARENA_W && L.y1>=0 && L.y1<=ARENA_H);
                    assert(hypotf(L.x1-L.x0,L.y1-L.y0)>0.1f);
                    assert(gap(L.x0,saved[k].x0)<0.001f && gap(L.y0,saved[k].y0)<0.001f);
                    assert(gap(L.x1,saved[k].x1)<0.001f && gap(L.y1,saved[k].y1)<0.001f);
                    if(k) {
                        assert(gap(L.x0,lines[k-1].x1)<0.001f && gap(L.y0,lines[k-1].y1)<0.001f);
                        float ax=lines[k-1].x1-lines[k-1].x0, ay=lines[k-1].y1-lines[k-1].y0;
                        float bx=L.x1-L.x0, by=L.y1-L.y0;
                        float al=hypotf(ax,ay), bl=hypotf(bx,by);
                        assert(gap(fabsf(ax/al),fabsf(bx/bl))<0.001f);
                        assert(gap(fabsf(ay/al),fabsf(by/bl))<0.001f);
                    }
                    if(L.stage==3){assert(L.hurt_w==0 && beamage<0.36f);++warned;}
                    if(L.stage==0){assert(L.hurt_w==0 && beamage>=0.34f);++charged;}
                    if(L.hurt_w>0){assert(beamage>=0.94f && L.stage==1);++hot;}
                }
            }
            previous=count>0;
            BulletSpawn out[8]; int n=e.fire(px,py,out,8);
            assert(n>=0 && n<=5);
            for(int k=0;k<n;++k) {
                auto b=out[k]; assert(b.from && b.damage==5.0f);
                assert(hypotf(px-b.ox,py-b.oy)>=64.0f);
                ricochets+=b.bouncing; homing+=b.homing; slowing+=b.min_speed>0;
                if(b.homing)assert(b.homing_timer>0 && b.homing_timer<=1.2f);
                if(b.shed_n){++embers;assert(f>1800 && b.shed_n==8 && b.shed_times==2);}
            }
        }
    }
    for(int cap=0;cap<6;++cap) {
        Alber bounded; bounded.hp=bounded.max_hp*0.49f;
        for(int f=0;f<600;++f){
            bounded.update(1.0f/60,320,400);
            BulletSpawn out[7];out[cap].damage=-123;
            assert(bounded.fire(320,400,out,cap)<=cap && out[cap].damage==-123);
        }
    }
    assert(warned && charged && hot && ricochets && homing && slowing && embers);
    printf("PASS: five aim scenarios, fixed two-bounce beam geometry, all segments warned before hot, bounded bullets/telegraphs, phase gate, smooth movement, 64px mouth clearance, finite homing, 5 damage.\n");
}
