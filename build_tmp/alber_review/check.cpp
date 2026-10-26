#include "../../src/enemies.cpp"
#include <cassert>
#include <cstdio>
int main() {
    Alber e;
    float lastx=e.x;
    int embers=0, shots1=0, shots2=0;
    for(int f=0;f<3600;++f) {
        if(f==1800) e.hp=e.max_hp*0.5f;
        e.update(1.0f/60,320,400);
        assert(fabsf(e.x-lastx)<2.5f); lastx=e.x;
        BulletSpawn out[8];
        int n=e.fire(320,400,out,8);
        assert(n>=0 && n<=5);
        (f<1800?shots1:shots2)+=n;
        for(int k=0;k<n;++k) {
            assert(out[k].from && out[k].damage==5.0f);
            if(out[k].shed_n) {
                ++embers;
                assert(f>1800 && out[k].shed_n==8 && out[k].shed_times==2);
                assert(out[k].shed_first==0.8f && out[k].shed_every==0.8f);
            }
        }
    }
    for(int cap=0;cap<5;++cap) {
        Alber bounded;
        for(int f=0;f<360;++f) {
            bounded.update(1.0f/60,320,400);
            BulletSpawn out[6]; out[cap].damage=-123;
            int n=bounded.fire(320,400,out,cap);
            assert(n<=cap && out[cap].damage==-123);
        }
    }
    assert(embers>0 && shots2>shots1);
    printf("PASS: bounded writes, smooth transition at exactly half HP, mouth origins, 5 damage, two-ring embers. Shots by half: %d / %d; embers %d\n",shots1,shots2,embers);
}
