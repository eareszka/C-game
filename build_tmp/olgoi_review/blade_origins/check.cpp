#include "../../../src/enemies.cpp"
#include <cassert>
#include <cstdio>
int main(){
    FILE* csv=fopen("build_tmp/olgoi_review/blade_origins/origins.csv","w");
    assert(csv);fprintf(csv,"spin,frame,side,x,y\n");
    for(int spin=0;spin<2;++spin)for(int frame=0;frame<12;++frame){
        OlgoiKhorkhoi e;e.hp=e.max_hp*(spin?0.5f:0.8f);
        e.update(spin?1.0f/60:1.21f,320,400);
        BulletSpawn out[8];e.fire(320,400,out,8);
        int n=e.on_idle_frame(frame,320,400,out,8);assert(n==2);
        for(int k=0;k<n;++k){
            auto b=out[k];assert(b.from&&b.half_len==12&&b.damage==5&&b.accel<0);
            fprintf(csv,"%d,%d,%d,%.0f,%.0f\n",spin,frame,k,(b.ox-e.x)/2+76,(b.oy-e.y)/2+62);
        }
        assert(e.on_idle_frame(frame,320,400,out,8)==0);
    }
    fclose(csv);
    for(int cap=0;cap<=2;++cap){
        OlgoiKhorkhoi e;e.hp=e.max_hp*0.5f;e.update(1.0f/60,320,400);
        BulletSpawn out[8];e.fire(320,400,out,8);out[cap].damage=-123;
        assert(e.on_idle_frame(5,320,400,out,cap)==cap&&out[cap].damage==-123);
    }
    puts("PASS: 48 origins captured on displayed frames; bounded callback writes; blade behavior preserved.");
}
