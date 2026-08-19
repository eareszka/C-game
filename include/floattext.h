#ifndef FLOATTEXT_H
#define FLOATTEXT_H

#include <SDL2/SDL.h>
#include "camera.h"
#include "resource_node.h"   // HarvestResult

// One floating "+N" popup, shown above the last resource harvested -- stacks
// (+1 -> +2 -> ...) rather than spawning a new one when the same spot is hit
// again while still visible. Shared by the overworld and every dungeon, so a
// pickaxe swing reads the same wherever it happens.
struct FloatText {
    float wx = 0.0f, wy = 0.0f;
    float drift = 0.0f, life = 0.0f;
    char  text[8] = {};
    Uint8 r = 0, g = 0, b = 0;
    bool  active = false;
    int   count = 0;
};

void floattext_spawn(FloatText* ft, float wx, float wy, Uint8 r, Uint8 g, Uint8 b);

// Feeds every resource hit in a HarvestResult through floattext_spawn(),
// picking the popup colour by ResourceType -- the one place both the
// overworld and every dungeon decide what a harvested resource looks like.
void floattext_spawn_from_harvest(FloatText* ft, const HarvestResult* h);

// Advance and draw, in world space. Call once per frame regardless of game
// state -- it no-ops when nothing is active.
void floattext_update_draw(FloatText* ft, float dt, const Camera* cam, SDL_Renderer* ren);

#endif
