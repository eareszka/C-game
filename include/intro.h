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

// The night's steps (docs/story.md): ASLEEP, the boy in bed while the dog
// wakes, panics and runs out; AWAKE, he's up and the dog is barking at the
// water; PAGE_FALLING, he came in sight of it and the page floats down;
// PAGE_DOWN, it lies there to read; READ, read, a breath; EMERGE, the hand
// (44 Itqiirpak, black) rises out of the sea north of the dog; FIGHT, the
// forced loss (main.cpp starts it from intro_take_fight); TAKEN, after it:
// he lies out cold by the water while the hand takes the dog north, then
// black, "THE NEXT MORNING"; MORNING, he wakes in bed, lights on, the
// everyday room 0; DAWN, his first step outside: he stands still while the
// night lifts to day and the fog goes, and the intro is over.
enum { INTRO_NONE = 0, INTRO_ASLEEP, INTRO_AWAKE, INTRO_PAGE_FALLING, INTRO_PAGE_DOWN, INTRO_READ,
       INTRO_EMERGE, INTRO_FIGHT, INTRO_TAKEN, INTRO_MORNING, INTRO_DAWN };

bool intro_init(SDL_Renderer* ren);   // loads the area; false if it is missing
void intro_free();
bool intro_active();
bool intro_night();          // the night itself, up to the black: room 0 is the dog's
int  intro_stage();
void intro_begin();
void intro_end();
void intro_skip_opening();   // testing: start with the boy up and the dog already out
void intro_test_read();      // testing: and the page already read (the hand comes)
void intro_test_taken();     // testing: straight to after the fight
// The fight over, however it went: TAKEN. He lies out cold where he stood
// (intro_draw_fallen draws him, feet's middle fx, fy; false otherwise) while
// the hand reaches down, takes the dog and carries it off north. Then the
// screen goes black: intro_blackout gives how black (0..1) and the card to
// write on it, or null. intro_take_morning, once, when the morning comes:
// the caller puts him home in room 0 (he's drawn asleep in bed and gets up).
void intro_taken_begin();
bool intro_draw_fallen(SDL_Renderer* ren, const Camera* cam, float fx, float fy);
float intro_blackout(const char** card);
bool intro_take_morning();

// The boy asleep, then waking, and while the hand rises: he can't move. In bed the room draws him with
// intro_draw_sleeper (true when it drew him); climbing out, intro_boy_scripted
// gives where his feet are, how far up to draw him and which frame.
bool intro_holds_player();
bool intro_draw_sleeper(SDL_Renderer* ren, const Camera* cam);
bool intro_boy_scripted(float* feet_x, float* feet_y, float* lift, int* frame);   // lift: drawn this far up
// Once, as he wakes: where his feet stand, beside his bed (room 0 pixels).
bool intro_take_wake(float* feet_x, float* feet_y);

// Is world tile (tx, ty) inside the drawn area.
bool intro_tile_open(const Tilemap* map, int tx, int ty);
// After the overworld moved the boy from (px, py): if his feet left the area,
// put him back, keeping whichever axis of the move stays inside (he slides
// along the fog). No-op while the intro is not running.
void intro_confine(const Tilemap* map, Overworld* ow, float px, float py);

// The fog wall, over the world and under the HUD. Overworld only.
void intro_draw_fog(SDL_Renderer* ren, const Camera* cam, const Tilemap* map);
// Night over the whole frame drawn so far (overworld or a room), w x h logical
// px. Indoors only while he sleeps: once he's up the house's lights are on.
void intro_draw_night(SDL_Renderer* ren, int w, int h, bool indoors);

// The page by the water: on the open ground's north shore. It falls once the
// boy comes in sight of the barking dog (drawn by intro_draw_note), and can
// be read once it lies there: its middle in world pixels, else false.
bool        intro_note_spot(const Tilemap* map, float* x, float* y);
bool        intro_page_land(const Tilemap* map, float* x, float* y);   // where it lands, whatever the stage
// Once, when the hand has risen: the fight begins (stage FIGHT); x, y its
// middle in world pixels, for the fight's flash.
bool        intro_take_fight(const Tilemap* map, float* x, float* y);
const char* intro_note_take();   // reads it: the stage moves on; its text
void        intro_draw_note(SDL_Renderer* ren, const Camera* cam, const Tilemap* map);

// The dog (assets/story/dog.png, from art/story/intro/dog/dog_design.py). It
// sleeps in its bed in room 0, wakes with a start, looks about, runs out and
// fades at the door; outdoors it fades in by the door, sprints north and
// barks at the water until the page is read. Otherwise it walks the boy's
// own footsteps a little behind him. It also runs the night's clock, so call
// it every frame the boy is in a room or outdoors. `space` is where he is:
// -1 the overworld, else the room's id. Feet are the bottom centre.
void intro_dog_update(const Tilemap* map, int space, float boy_feet_x, float boy_feet_y, float dt);
bool intro_dog_feet(float* x, float* y);    // false while there is no dog to draw
void intro_dog_draw(SDL_Renderer* ren, const Camera* cam);

#endif
