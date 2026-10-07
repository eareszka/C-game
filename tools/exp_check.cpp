// The EXP curve and level-ups: python-free check, run after changing them.
//   g++ -Iinclude tools/exp_check.cpp src/entity.cpp src/input.cpp $(sdl2-config --cflags --libs) -o exp_check && ./exp_check
#include "entity.h"
#include <assert.h>
#include <stdio.h>

int main(int, char**) {
    for (int l = 2; l < 30; l++) assert(exp_for_level(l + 1) > exp_for_level(l));
    assert(exp_for_level(2) == 100 && exp_for_level(3) == 303);
    Player p = {};
    p.level = 1; p.stats.max_hp = 60; p.stats.hp = 20;
    int up = player_gain_exp(&p, 350);          // past L2 (100) and L3 (303)
    assert(up == 2 && p.level == 3 && p.stats.max_hp == 70 && p.stats.hp == 70);
    assert(player_gain_exp(&p, 1) == 0 && p.level == 3);
    printf("exp curve ok: L2 %d L3 %d L5 %d L10 %d\n", exp_for_level(2), exp_for_level(3), exp_for_level(5), exp_for_level(10));
    return 0;
}
