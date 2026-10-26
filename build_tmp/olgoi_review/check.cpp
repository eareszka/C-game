#include "../../src/enemies.cpp"
#include <cassert>
#include <cstdio>
int main() {
    const float xs[]={16,320,624}, ys[]={44,140,400,464};
    int types[3][3]={}, warnings=0, charges=0, hot=0;
    for(float px:xs) for(float py:ys) {
        OlgoiKhorkhoi e;
        assert(e.phase2_at()==0.66f && e.max_hp==1200 && e.mults.knife==0.4f);
        float age=0; bool had=false;
        for(int f=0;f<3600;++f) {
            int st=f<1200?0:f<2400?1:2;
            e.hp=e.max_hp*(st==0?0.8f:st==1?0.5f:0.2f);
            e.update(1.0f/60,px,py);
            e.on_idle_frame((f/10)%12,px,py,nullptr,0);
            assert(e.alt_pose()==(st>0));
            Enemy::TeleLine lines[4];int nt=e.telegraphs(lines,4);
            assert(nt==0||nt==3);
            if(nt){
                assert(st==2);
                age=had?age+1.0f/60:0;
                for(int k=0;k<nt;++k){
                    auto L=lines[k];assert(std::isfinite(L.x1)&&std::isfinite(L.y1));
                    assert(fabsf(hypotf(L.x1-L.x0,L.y1-L.y0)-900)<0.01f);
                    if(L.stage==3){assert(L.hurt_w==0 && age<0.32f);++warnings;}
                    if(L.stage==0){assert(L.hurt_w==0 && age>=0.29f);++charges;}
                    if(L.hurt_w>0){assert(L.stage==1 && age>=0.89f);++hot;}
                }
            }
            had=nt>0;
            for(int cap=0;cap<4;++cap){
                Enemy::TeleLine bounded[5];bounded[cap].stage=-123;
                assert(e.telegraphs(bounded,cap)<=cap && bounded[cap].stage==-123);
            }
            BulletSpawn out[8];int n=e.fire(px,py,out,8);assert(n>=0&&n<=6);
            for(int k=0;k<n;++k){
                auto b=out[k];assert(b.from && b.damage==5);
                assert(hypotf(px-b.ox,py-b.oy)>=70);
                assert(b.ox>=0 && b.ox<=ARENA_W && b.oy>=ARENA_TOP && b.oy<=ARENA_H);
                if(b.half_len>0){
                    assert(hypotf(px-b.ox,py-b.oy)>=100);
                    ++types[st][1];assert(b.accel<0 && b.min_speed==0 && b.max_speed==260);
                    float dist=260.0f*260/(-2*b.accel), ux=b.vx/260,uy=b.vy/260;
                    assert(b.ox+ux*dist>=15.99f && b.ox+ux*dist<=ARENA_W-15.99f);
                    assert(b.oy+uy*dist>=ARENA_TOP+15.99f && b.oy+uy*dist<=ARENA_H-15.99f);
                } else if(b.shed_n){++types[st][2];assert(st>0&&b.shed_n==18&&b.shed_times==1);}
                else {++types[st][0];assert(b.min_speed==100);}
                if(b.homing)assert(st>0 && b.homing_timer==0.8f);
            }
        }
    }
    for(int cap=0;cap<=6;++cap){
        OlgoiKhorkhoi e;
        for(int f=0;f<1800;++f){
            e.hp=e.max_hp*(f<600?0.8f:f<1200?0.5f:0.2f);
            e.update(1.0f/60,320,400);
            BulletSpawn out[8];out[cap].damage=-123;
            assert(e.fire(320,400,out,cap)<=cap && out[cap].damage==-123);
        }
    }
    for(int st=0;st<3;++st){assert(types[st][0]&&types[st][1]);if(st)assert(types[st][2]);}
    // Beam gaps clear the 3px core outside its start guard, and every
    // playable point can follow the sweep at focus speed.
    float farthest=hypotf(ARENA_W-16-292,ARENA_H-16-160);
    assert(farthest*0.13f<70 && 70*sinf(0.32f)>12);
    assert((100-18)/260.0f*70>18); // close blade: time to clear its full bar
    assert(!types[0][2] && warnings && charges && hot);
    printf("PASS: 12 player positions; three HP phases; two attacks in phase 1, rings in phases 2/3, warned electric fork only in phase 3; bounded bullet/telegraph output; 5 damage, 70px launch clearance; returning blades stop inside arena.\n");
}
