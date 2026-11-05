#pragma once
#include <SDL2/SDL.h>
#include "camera.h"
#include "resource_node.h"
#include "tilemap.h"

// The desert's tumbleweeds (the user, 2026-10-28: "it rolls across the screen
// like in movies with a shadow beneath and all to show how its going airborn
// and back to the ground"). Not laid on the map: while the player is on sand
// one blows in now and then from off screen on the windward side, bounces
// across -- hopping the props, glancing off cliffs and water -- and out the
// far side. Every one goes with the one wind, which drifts round over the day
// and gusts. A weapon breaks one for a wood; the feet pass through. Nothing
// of them is saved.

// The wind at this world time (seconds, the resident clock): a unit direction
// and a strength, 0.7 to 1.3.
void tumble_wind(double world_seconds, float* dx, float* dy, float* strength);

// One step: blow in a new one if it is time, move and bounce the rest, put
// away the ones gone past the screen. (px, py): the middle of the player.
void tumble_tick(const Tilemap* map, const Camera* cam, float px, float py, double world_seconds, float dt);
// For the overworld's sprites, sorted by their feet (main.cpp): whether
// tumbleweed i is out, and if so where its ground line is and the box it is
// drawn in, at its image nearest the player (px, py), world pixels.
bool tumble_sprite(int i, float px, float py, float* feet, float* x, float* y, float* w, float* h);
// Tumbleweed i over its shadow, at its image nearest the camera.
void tumble_draw_one(SDL_Renderer* ren, const Camera* cam, SDL_Texture* sheet, int i);
// The twigs of any just broken, flying.
void tumble_draw_bursts(SDL_Renderer* ren, const Camera* cam);
// None left (another world, off the overworld).
void tumble_clear(void);

// A weapon's strikes, as the props' (combat.cpp): each breaks the tumbleweed
// it meets for one WOOD in out. The same shapes as resource_nodes_*.
int tumble_try_hit(float px, float py, int range, HarvestResult* out);
int tumble_sweep(float px, float py, float radius, float start_ang, float rel0, float rel1, HarvestResult* out);
int tumble_thrust(float px, float py, float angle, float half_width, float from, float to, HarvestResult* out);
int tumble_strike_point(float x, float y, float radius, HarvestResult* out);

// For tools/tumblecheck.cpp: let one loose at a ground point, and look at them.
struct Tumbleweed {
    bool  live;
    float x, y, z;          // the ground point under it, world pixels; z its height off it
    float vx, vy, vz;
    float speed;            // its own pace in the wind, px/s at strength 1
    float rolled;           // ground covered: its turn
    float age, rest;        // seconds alive; seconds left rolling along the ground before the next hop
    int   face;             // +1 rolling right, -1 left: which way the frames turn
    int   hops, big_hops, deflects;
};
enum { TUMBLE_MAX = 4 };
Tumbleweed* tumble_spawn_at(float x, float y);
const Tumbleweed* tumble_list(void);
int tumble_frame(const Tumbleweed& t);   // its frame of the eight
// One weed's step in the wind at this world time, as tumble_tick moves each.
void tumble_step(Tumbleweed* t, const Tilemap* map, double world_seconds, float dt);
