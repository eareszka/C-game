#ifndef STORY_H
#define STORY_H

#include <stdint.h>
#include <SDL2/SDL.h>
#include "game_state.h"
#include "entity.h"   // Player: what the people ask of the boy and hand him
#include "crafting.h" // Item: what a shop sells

// The story (src/story.cpp): a civilization above writes this world's script
// and feeds it through the swarm at the planet's centre; the boy, outside the
// script, hunts the bosses it wrote in. Everyone else is scripted: what they
// say and where the bosses stand follow the stage, and the stage follows what
// has been beaten. Nothing here is saved but the flags block.

struct Tilemap;
struct Camera;
struct DungeonMap;

// Saved whole, appended to the save file after the chests. All zero = a
// fresh story. beaten: bit i = STORY_BOSSES[i] beaten. notes: bit i = note i
// taken. first_village_plus1: the village the boy first spoke in, + 1 (0 =
// none yet).
struct StoryFlags {
    uint32_t beaten;
    uint32_t notes;
    uint8_t  first_village_plus1;
    uint8_t  quest;          // STORY_Q_* bits: the lighthouse keeper's errands
    uint8_t  pad[2];
};
enum { STORY_Q_BOAT_WOOD = 1, STORY_Q_SAIL_TOLD = 2 };   // the wood delivered; the bat named (its tree holds it)
StoryFlags* story_flags();

// The bosses in story order. Tier 1 (06 23 49 30) stand in the world from the
// start; tier 2 (52 44 98) are sent after the turn; Anaye guards the cave's
// mouth once they fall; the swarm waits below. The index is the flag bit and
// the row of the boss sites laid by worldgen (Tilemap::boss_sites).
static const int STORY_BOSSES[] = { 6, 23, 49, 30, 52, 44, 98, 34, 100 };
enum { STORY_BOSS_COUNT = 9, STORY_TIER1 = 4, STORY_TIER2 = 3, STORY_ANAYE = 7, STORY_SWARM = 8 };

// What has happened, read off the beaten bits, never stored.
enum StoryStage { STORY_ARC1, STORY_TURN, STORY_DESCENT, STORY_OPEN, STORY_AMNESIA, STORY_STAGE_COUNT };
static const char* const STORY_STAGE_NAMES[STORY_STAGE_COUNT] = { "ARC1", "TURN", "DESCENT", "OPEN", "AMNESIA" };

int        story_boss_index(int enemy_id);      // -1 for an enemy that is not a story boss
bool       story_beaten(int enemy_id);
void       story_mark_beaten(int enemy_id);     // a no-op for any other enemy
StoryStage story_stage();
void       story_set_stage(StoryStage s);       // debug: beaten as if exactly that far
int        story_tier2_kills();

// Boss sites on the overworld. A site stands while its boss is unbeaten and
// the stage has sent it; the swarm never stands (it is in the cave).
bool story_site_active(const Tilemap* map, int i);
// The site the player's frame middle is touching, or -1.
int  story_site_touch(const Tilemap* map, float pcx, float pcy);
// Where the pre-battle flash goes for site i (world pixels, its middle).
void story_site_flash_at(const Tilemap* map, int i, float* x, float* y);
// Every standing site in view, as the boss's own idle frame (until the map
// minis exist). Before the player, so the boy can walk in front.
void story_sites_draw(SDL_Renderer* ren, const Camera* cam, const Tilemap* map);

// The people who speak. Where the player is: the state, the room (interiors)
// and the door walked in by (map->doors index, -1 if none) -- a village's
// house shares its room with every other village, so the room cannot say
// which town the player is in, the door can.
// debug: test mode (--debug), which lets the debug people stand.
struct StoryWhere { GameState state; const Tilemap* map; int room; int door; Player* player; bool debug; };
// x, y: the top left of a player-sized frame, in that map's pixels; village:
// which village's (map->villages index) for a villager, -1 otherwise.
struct StoryNpcPos { int idx; float x, y; int village; };
// Where a village's speaker stands: on the street beside the well.
void        story_village_npc_tile(const Tilemap* map, int village, int* tx, int* ty);
int         story_npcs_here(const StoryWhere& w, StoryNpcPos out[], int max);
// Their sheet in assets/npcs: 0 elder, 1 farmer, 2 glasses;
// -1 a legacy speaker (the player's sprite, tinted).
int         story_npc_sprite(const StoryNpcPos& p);
// What a shopkeeper sells and says when asked to TALK; the books in stock.
struct Shop { const char* chat; const Item* stock; int n; };
const Shop* story_npc_shop(const StoryNpcPos& p);   // nullptr: not a shopkeeper
struct StoryNpcConversation { const char* prompt; const char* choices[3]; };
const StoryNpcConversation* story_npc_conversation(const StoryNpcPos& p);
const char* story_npc_answer(const StoryNpcPos& p, const StoryWhere& where, int choice);
void story_npc_resume(const StoryNpcPos& p);
bool story_npc_can_talk(const StoryNpcPos& p);
// Location-aware topic shared by NPCs, including interiors identified by entrance.
const char* story_world_name();
const char* story_town_name(int town);
const char* story_where_am_i(const StoryNpcPos& p, const StoryWhere& where);
// Where they are spoken to from: their feet's bottom middle -- a
// shopkeeper's a tile further down, across the counter.
void        story_npc_talk_point(const StoryNpcPos& p, float* x, float* y);
bool        story_people_init(SDL_Renderer* renderer);
void        story_people_free();
// Draw a resident with its own artwork; false for a legacy speaker.
bool        story_npc_draw(const StoryNpcPos& p, SDL_Renderer* renderer, const Camera* cam);
// Spoken to: turn toward (dx, dy) from it, the nearest of the four ways; it
// stays that way (the walking resident turns again as she walks on).
void        story_npc_face(const StoryNpcPos& p, float dx, float dy);
int         story_npc_facing(const StoryNpcPos& p);   // FACE_*, FACE_DOWN until spoken to
// Called while nothing is open (no speech, choices or shop): shopkeepers turn forward.
void        story_npcs_idle();
// The row of a 42x80 NPC sheet (assets/npcs) for a facing: down, up, left, right.
inline int  npc_sheet_row(int facing) { return facing == FACE_UP ? 1 : facing == FACE_LEFT ? 2 : facing == FACE_RIGHT ? 3 : 0; }
// Its column on walking beat `beat`, as player_frame steps: down and up go
// step A, standing, step B, standing; the sides have their two drawings.
inline int  npc_walk_col(int facing, int beat) {
    static const int BEATS[4] = { 1, 0, 2, 0 };
    return facing == FACE_UP || facing == FACE_DOWN ? BEATS[beat % 4] : beat % 2 ? 0 : 1;
}
// What this person says now, for the stage; a lead's direction is measured
// from the door the player came in by, or from the villager's village. Asked
// only when spoken to: a villager's first talk marks the first village. A
// static buffer, good until the next call. nullptr for the debug speaker:
// open the dialogue list (story_dialogue) instead.
const char* story_npc_line(const StoryNpcPos& p, const StoryWhere& w);
// Debug: every line the people and the notes can say, i < count, as it reads
// in play (leads appended), with the flags and w.player forced to the case
// that brings it on and put back after. label: the list's name for it.
// Static buffers, good until the next call.
int         story_dialogue_count();
const char* story_dialogue(int i, const StoryWhere& w, const char** label, bool* strike);
// The notes: pages of the writers' own that fell into the world. Each lies at
// a fixed spot and shows once the stage (and the tier-2 kills) allow, until
// taken (StoryFlags::notes, bit = row). x, y: its middle in that map's pixels.
struct StoryNotePos { int idx; float x, y; bool strike; };
int         story_notes_here(const StoryWhere& w, const DungeonMap* dmap, StoryNotePos out[], int max);
// Takes note idx and gives its text (a lead note ends with its direction,
// measured from where it lay). A static buffer, good until the next call.
const char* story_note_take(int idx, const StoryWhere& w);
int         story_note_count();
// For the checks: the world tile of an outdoor note (false for one indoors or in the cave).
bool        story_note_world_tile(const Tilemap* map, int idx, int* tx, int* ty);

// The hole: from the turn on, the ground round the starter cave's mouth is
// wasteland (a disc of HOLE_R tiles, the water and the mouth itself left as
// they are), and the mouth refuses the boy while the pages pour in -- until
// Anaye falls there. Apply every overworld frame: it writes only what is not
// yet wasteland, so it is cheap, and heals whatever worldgen lays over it.
enum { STORY_HOLE_R = 6 };
void        story_hole_apply(Tilemap* map);
bool        story_hole_blocked();              // TURN or DESCENT: the pages push back
bool        story_hole_tile(int tx, int ty);  // is this the starter cave's mouth
// The hole's art (art/structures/hole/), from the turn on. air=false: the
// cracked ring over the mouth, on the ground, before the player; air=true:
// the portal five tiles up and the pages pouring from it into the ring,
// while story_hole_blocked(), after the depth pass. Nothing is kept between
// frames: the phases come off SDL_GetTicks().
void        story_hole_draw(SDL_Renderer* ren, const Camera* cam, const Tilemap* map, bool air);

// "NORTH-EAST, FAR, IN THE SAND." from a tile to a boss's site; "nobody knows"
// for a boss with no site.
void        story_lead(const Tilemap* map, int from_tx, int from_ty, int boss, char* buf, int n);

// The lighthouse keeper's errand: the great bat (12 Ebigane) roosts in the
// large tree nearest the coastal town -- that entrance's index, or -1 -- and
// a dungeon grown from its wiring seed gets it as its first spawner while the
// errand is open (told of, and no sail made yet).
int         story_quest_tree(const Tilemap* map);
// The boat: moored one tile off the wharf's tip, toward the sea. False with
// no wharf. Ready to sail once the keeper's wood is paid and the sail made.
bool        story_boat_spot(const Tilemap* map, int* tx, int* ty);
bool        story_boat_ready(const Player* player);
bool        story_quest_pin(const Tilemap* map, unsigned map_seed, unsigned dungeon_seed, const Player* player);

#endif
