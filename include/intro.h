#ifndef INTRO_H
#define INTRO_H

#include <SDL2/SDL.h>

// The intro (docs/story.md): the foggy night the dog goes missing. While it
// runs, the whole frame is night-tinted. The boy is kept inside the area the
// user drew (assets/story/intro_area.png: one pixel a tile, its top-left 22
// tiles up and left of town 0's corner, which is the same in every world),
// and a dithered fog wall stands over everything outside it.
//
// Not saved yet: `game.exe --intro` starts it (skipping the title) until the
// whole sequence exists; then NEW GAME will, and it moves into the save.

struct Tilemap;
struct Camera;
struct Overworld;

enum { INTRO_NONE = 0, INTRO_NIGHT = 1 };

bool intro_init(SDL_Renderer* ren);   // loads the area; false if it is missing
void intro_free();
bool intro_active();
void intro_begin();
void intro_end();

// Is world tile (tx, ty) inside the drawn area.
bool intro_tile_open(const Tilemap* map, int tx, int ty);
// After the overworld moved the boy from (px, py): if his feet left the area,
// put him back, keeping whichever axis of the move stays inside (he slides
// along the fog). No-op while the intro is not running.
void intro_confine(const Tilemap* map, Overworld* ow, float px, float py);

// The fog wall, over the world and under the HUD. Overworld only.
void intro_draw_fog(SDL_Renderer* ren, const Camera* cam, const Tilemap* map);
// Night over the whole frame drawn so far (overworld or a room), w x h logical px.
void intro_draw_night(SDL_Renderer* ren, int w, int h);

// The dog (assets/story/dog.png, from art/story/intro/dog/dog_design.py). It
// walks the boy's own footsteps a little behind him, so it never cuts a
// corner through a wall. `space` is where he is: -1 the overworld, else the
// room's id; on a change the dog arrives with him. Feet are the bottom centre.
void intro_dog_update(int space, float boy_feet_x, float boy_feet_y, float dt);
bool intro_dog_feet(float* x, float* y);    // false while there is no dog to draw
void intro_dog_draw(SDL_Renderer* ren, const Camera* cam);

#endif
