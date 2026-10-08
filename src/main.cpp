#include <stdio.h>
#include <stdlib.h>   // strtoul, for the seed argument
#include <thread>
#include <unordered_map>
#include <vector>
#include <SDL2/SDL_image.h>

#include "fc_palette.h"
#include "game_state.h"
#include "battle.h"
#include "dungeon.h"
#include "dungeon_kinds.h"
#include "platform.h"
#include "core.h"
#include "input.h"
#include "overworld.h"
#include "interior.h"
#include "collision.h"
#include "camera.h"
#include "tilemap.h"
#include "resource_node.h"
#include "floattext.h"
#include "crafting.h"
#include "game_menu.h"


// How many whole pixels of frame there are to a logical pixel: as many as the
// window has room for. One is the floor, so a window smaller than the logical
// screen still gets a frame, just a downscaled one.
static int frame_scale_for(SDL_Renderer* renderer, int lw, int lh) {
    int ow = lw, oh = lh;
    SDL_GetRendererOutputSize(renderer, &ow, &oh);
    int s = ow / lw;
    if (oh / lh < s) s = oh / lh;
    return s < 1 ? 1 : s;
}

// Snap 0..1 to `levels` hard steps (rounding down; 1 stays 1), the way the
// NES fades and moves: a few distinct states, nothing in between.
static float nes_steps(float a, int levels) {
    if (a <= 0.0f) return 0.0f;
    if (a >= 1.0f) return 1.0f;
    return (float)(int)(a * levels) / levels;
}

int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    // One logical screen, drawn at one pixel to the pixel and scaled to the
    // window exactly once, at present time.
    static const int LOGICAL_W = 640, LOGICAL_H = 480;

    Platform plat;
    if (!platform_init(&plat, "Four Castle Chronicles", LOGICAL_W, LOGICAL_H)) {
        return 1;
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(plat.renderer, LOGICAL_W, LOGICAL_H);

    // Everything the game draws goes here first, and this one finished picture
    // goes to the window.
    //
    // Drawing straight at the window sent every tile quad through the
    // logical-size scale -- 2.25 in a 1920x1080 window -- so a tile edge could
    // land on a half pixel. The outermost row of such a quad has its centre
    // exactly on the boundary of the source cell, and nearest rounding takes it
    // one texel into the neighbouring cell: tileset.png is packed sixteen to
    // the cell with no gutter, and what sits above the grass block is the tree
    // row, keyed background with two black pixels along the foot of a trunk.
    // That came out as a one-pixel dark dash along the top of the tile, walking
    // over the ground as the camera moved it in and out of the half-pixel
    // phase.
    //
    // Compositing first makes every quad edge whole, so no sample can reach a
    // cell boundary. That is a property of the frame rather than of any sheet,
    // tile or draw site, so it holds at every zoom and every window size, and
    // nothing downstream has to know about it.
    // The frame is a whole multiple of the logical screen rather than the
    // logical screen itself. At one to one a source texel gets
    // (int)(32*zoom)/16 pixels to live in, which is half a pixel at 0.25x and
    // one and a half at 0.75x: the first throws every other texel away and the
    // second lands them alternately one and two wide, and the window then
    // magnifies whichever it got. Drawing at the largest whole multiple the
    // window has room for gives those zooms their pixels back, and keeps the
    // scale inside the frame a whole number, which is the part that closes the
    // seam.
    SDL_Texture* frame_tex   = NULL;
    int          frame_scale = 0;
    const bool   can_target  = (SDL_RenderTargetSupported(plat.renderer) == SDL_TRUE);
    if (!can_target) printf("No render target: drawing straight at the window, seams and all.\n");

    if (!(IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG)) 
    {
        printf("SDL_image init failed: %s\n", IMG_GetError());
        platform_shutdown(&plat);
        return 1;
    }

    tilemap_init_tile_cache(plat.renderer);

    // The player, on the maps and in battle: 14x20 art pixels a frame
    // (assets/player_small.aseprite), drawn at 2x.
    SDL_Texture* player_sprite = IMG_LoadTexture(plat.renderer, "assets/player_small.png");
    if (!player_sprite) {
        printf("Failed to load sprite: %s\n", IMG_GetError());
        tilemap_free_tile_cache();
        IMG_Quit();
        platform_shutdown(&plat);
        return 1;
    }

    GameState state = STATE_OVERWORLD;

    // Placeholder player stats — wire up to a real save/character system later
    Player player = {0};
    player.level             = 1;
    player.stats.max_hp      = 60;  player.stats.hp      = 60;
    player.stats.max_spd     = 10;  player.stats.spd     = 10;
    player.stats.max_attack  = 18;  player.stats.attack  = 18;
    player.stats.max_mag     = 12;  player.stats.mag     = 12;
    player.stats.max_luck    = 30;  player.stats.luck    = 30;
    player.stats.max_iq      = 8;   player.stats.iq      = 8;

    BattleScene* battle_scene = nullptr;
    // The oasis's air: 1 full, 0 gone. It runs out over 16 s under water and
    // fills again at a surface; once gone, the swimmer drowns a bar of HP
    // every 2 s, never below 1 HP. A fight stops the clock (user).
    float oxygen = 1.0f, oxy_hurt_t = 0.0f;
    float drown_t = 9.0f;      // seconds since drowning last hurt: the fight's shake and red flash
    GameState    state_after_battle = STATE_OVERWORLD;
    int          battle_queue[3]             = {};
    int          battle_queue_chaser_idx[3] = { -1, -1, -1 };
    int          battle_queue_count = 0;
    int          battle_queue_idx   = 0;
    struct FlashEntry { float x, y; };
    FlashEntry   flash_entries[3]   = {};
    int          flash_count        = 0;
    float        pre_battle_timer   = -1.0f;  // -1 = inactive
    float        post_battle_t      = 0.0f;   // back on the map: fade-in, chasers hold
    // Test enemies in the spawn house: the enemy being tuned (swap in each new
    // one as its patterns are done; more entries fight as a pack). Armed
    // again once the player steps off them.
    struct TestEnemy { int id; float x, y; };
    // The practice dummies stand on the starting house's floor (interior 0,
    // whose walkable floor starts at row 7), across the room from where the
    // player wakes, so they can be walked into but are not touched at once.
    TestEnemy    test_enemies[]     = {
        { 57, 10.0f * IMAP_TILE, 8.5f * IMAP_TILE },  // 57 Dingbat
    };
    const int    TEST_N             = (int)(sizeof(test_enemies) / sizeof(test_enemies[0]));
    bool         test_armed         = true;

    // Floating +N resource text — one active at a time above the last hit node.
    // Shared by the overworld and every dungeon (include/floattext.h).
    FloatText cur_float;

    Overworld ow;

    Tilemap* map = new Tilemap();
    // Print the seed, and take one on the command line. Worlds were seeded from
    // the clock and never recorded, so a world you noticed something wrong in
    // was gone the moment you closed the game and there was no way to get back
    // to it. Pass the number back in to regenerate that exact world.
    unsigned int map_seed = (argc > 1) ? (unsigned int)strtoul(argv[1], nullptr, 10)
                                       : (unsigned int)SDL_GetTicks();
    printf("World seed: %u   (re-run with: game.exe %u)\n", map_seed, map_seed);
    fflush(stdout);
    tilemap_build_overworld_phase1(map, map_seed);

    // Spawn directly in front of the spawn house's front door. Phase 1 only
    // stamps town 0, and the stamp scans top-to-bottom, so the first
    // interior-0 door registered is the spawn house. Must be read before the
    // phase-2 thread starts appending doors from the other towns.
    float start_x = 47916.0f;
    float start_y = 46528.0f;   // fallback if the door lookup fails
    for (int i = 0; i < map->num_doors; i++) {
        const InteriorDoor& d = map->doors[i];
        if (d.interior_id != 0) continue;
        // Feet centred under the door, one tile row below it; the -8 mirrors
        // the door-detection bias in overworld_update.
        start_x = (d.x + d.w * 0.5f) * TILE_SIZE - 8.0f - (HB_X1 + HB_X2) * 0.5f;
        start_y = (d.y + 1) * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
        break;
    }
    overworld_init(&ow, &player, start_x, start_y);

    std::thread gen_thread(tilemap_build_overworld_phase2, map, map_seed);

    //initializes resources
    ResourceNodeList resources;
    resource_nodes_init(&resources);

    resource_nodes_add(&resources, RESOURCE_FLOWER, 320, 224);
    bool oilbloom_done[OILBLOOM_SITES] = {};   // which of the world's sites are placed


    Input in = {0};

    // Zoom levels where TILE_SIZE(32) * zoom is always a whole number of pixels
    static const float zoom_levels[] = { 0.25f, 0.5f, 0.75f, 1.0f, 1.5f, 2.0f, 3.0f };
    static const int   zoom_count    = (int)(sizeof(zoom_levels) / sizeof(zoom_levels[0]));
    int zoom_idx = 3; // default: 1.0x

    Camera cam = {0};
    cam.screen_w = LOGICAL_W;
    cam.screen_h = LOGICAL_H;
    cam.zoom = zoom_levels[zoom_idx];

    bool running = true;

    // ── Debug menu ───────────────────────────────────────────────────────────
    static const char* DBG_TYPE_NAMES[] = {
        "CAVE", "RUINS", "GRAVEYARD", "GRAVEYARD LG",
        "OASIS", "PYRAMID", "STONEHENGE", "LARGE TREE", "CATACOMBS"
    };
    static const int DBG_TYPE_COUNT = DUNGEON_ENT_COUNT;

    // The warp list is "any cave" and then every kind of dungeon, commonest
    // first, straight from DUNGEON_KINDS (include/dungeon_kinds.h) -- the one
    // table the spawn rates come from, so the menu reads in the order the
    // world is populated in. A cave is one type but seven entries there: which
    // of MATERIALS (src/dungeon.cpp) a cave holds is picked from its
    // DungeonEntrance difficulty, and that material is the whole of the
    // difference, so it is what the menu has to name to warp you to a
    // particular kind of cave.
    //
    // Index layout: 0 = any cave, 1.. = DUNGEON_KINDS[index - 1].
    static const int DBG_TARGET_COUNT = 1 + DUNGEON_KIND_COUNT;
    auto dbg_target_type = [&](int i) -> DungeonEntranceType {
        return i == 0 ? DUNGEON_ENT_CAVE : DUNGEON_KINDS[i - 1].type;
    };
    // Which material this target insists on, or -1 for "whatever it holds".
    auto dbg_target_ore = [&](int i) {
        return i == 0 ? -1 : DUNGEON_KINDS[i - 1].material;
    };
    // Does this overworld entrance answer to the selected target?
    auto dbg_target_matches = [&](int i, const DungeonEntrance* e) {
        if (e->type != dbg_target_type(i)) return false;
        int ore = dbg_target_ore(i);
        return ore < 0 || (int)material_for_difficulty(e->difficulty) == ore;
    };
    // "CAVE", "CAVE: DRAVIUM", "RUINS", ... Material names come from
    // dungeon.cpp's table and are upper-cased here, because core.cpp's bitmap
    // font only carries ASCII 32-90 and draws lowercase as blanks.
    auto dbg_target_name = [&](int i, char* out, size_t n) {
        int ore = dbg_target_ore(i);
        if (ore < 0) {
            SDL_snprintf(out, n, "%s", DBG_TYPE_NAMES[dbg_target_type(i)]);
            return;
        }
        SDL_snprintf(out, n, "CAVE: %s", material_name((Material)ore));
        for (char* c = out; *c; c++)
            if (*c >= 'a' && *c <= 'z') *c = (char)(*c - 'a' + 'A');
    };
    // Every separate place the target could warp you to, as indices into
    // dungeon_entrances[], in array order. Every mouth of one mountain opens
    // the same cave and they all share its anchor, so a system contributes its
    // first mouth and no more -- otherwise a four-mouthed mountain is three
    // wasted steps of the tour and reads as four caves in the count.
    //
    // The row's count and the tour both walk this one list, so "12 FOUND" and
    // twelve presses of ENTER land on twelve different caves by construction.
    auto dbg_target_list = [&](int i, int* out, int max_out) {
        int n = 0;
        for (int a = 0; a < map->num_dungeon_entrances && n < max_out; a++) {
            const DungeonEntrance* e = &map->dungeon_entrances[a];
            if (!dbg_target_matches(i, e)) continue;
            bool listed = false;
            if (e->cave_anchor_x >= 0)
                for (int b = 0; b < a && !listed; b++)
                    listed = map->dungeon_entrances[b].cave_anchor_x == e->cave_anchor_x &&
                             map->dungeon_entrances[b].cave_anchor_y == e->cave_anchor_y;
            if (!listed) out[n++] = a;
        }
        return n;
    };
    // Scratch for the above, sized to the entrance array so no target can
    // overflow it. static rather than a local: 8KB is more than a stack frame
    // wants, and it is rebuilt from scratch on every call anyway.
    static int dbg_list[MAX_DUNGEON_ENTRANCES];
    // Where the tour has got to: index into dbg_list of the one you were last
    // put outside, or -1 before the first press.
    int  dbg_tour     = -1;

    bool dbg_open     = false;
    float ow_swap_t   = 99.0f;   // seconds since Q / E swapped weapons outside battle, for the weapon box
    bool dbg_readout  = false;   // F1: the FPS and position readout, off in normal play
    // 0=target, 1=enter, 2=regen, 3=noclip, 4=show all, 5=weapon, 6=grid, 7=seam
    static const int DBG_ROW_COUNT = 11;
    // The rows in two columns: the world (0-4, 6, 7) on the left, the player
    // (5, 8-10) on the right. dbg_sel is a row's id; UP/DOWN step through this
    // order, down the left column and on into the right.
    static const int DBG_ORDER[DBG_ROW_COUNT] = { 0, 1, 2, 3, 4, 6, 7,   5, 8, 9, 10 };
    static const int DBG_PLAYER_AT = 7;   // where the player column starts in DBG_ORDER
    auto dbg_pos = [&](int id) { int i = 0; while (DBG_ORDER[i] != id) i++; return i; };
    int  dbg_sel      = 0;
    int  dbg_target   = 0;
    bool dbg_noclip   = false;
    bool dbg_show_all = false;
    bool dbg_grid     = false;
    GameMenu menu;            // the TAB menu: crafting and items
    // A line at the foot of the screen that answers a pickup ("GOT RAFT
    // BOOK"), and how long it stays.
    int  item_last[ITEM_COUNT] = {};   // last frame's item counts, for items_note_gains
    bool items_primed = false;
    const char* pickup_note   = nullptr;
    float       pickup_note_t = 0.0f;
    bool map_open         = false;
    bool battle_list_open = false;
    int  battle_list_sel  = 0;        // position in the filtered list
    char battle_query[24] = "";       // typed search: part of a name, or an id

    static const char* ENEMY_NAMES[] = {
        // Grassland 0–6
        "SKVADER", "WOLPERTINGER", "TREESQUEAK", "QIQUE", "LILI",
        "CROWING CRESTED COBRA", "WAKMANGGANCHI ARAGONDI",
        // Forest 7–13
        "ALBER", "SNAWFUS", "QUESTING BEAST", "GRAND'GOULE", "PAOXIAO",
        "EBIGANE", "BEAST OF THE CHARRED FORESTS",
        // Snow 14–20
        "LODSILUNGUR", "OFUGUGGI", "KAMAITACHI", "QIQIRN", "VATNAORMUR",
        "SKELJASKRIMSLI", "SERMILIK",
        // Desert 21–27
        "ASP", "CACTUS CAT", "OLGOI-KHORKHOI", "ZOUREG", "MYRMECOLEON",
        "AKHEKH", "GROOTSLANG",
        // Wasteland 28–34
        "OPIMACHUS", "KARNABO", "DAJNA", "MAN-EATING BOULDER", "ANGONT",
        "TSE'NAGAHI", "ANAYE",
        // Mountains 35–41
        "LOMIE", "CU SITH", "CELESTIAL STAG", "IGTUK", "AJAJU",
        "SLIDE-ROCK BOLTER", "SASNALKAHI",
        // Ocean 42–49
        "NYKUR", "SAZAE-ONI", "ITQIIRPAK", "KUSA KAP", "LUSCA",
        "MOHA-MOHA", "BJARNDYRAKONGUR", "PHYSETER",
        // Later cryptids, 50 on
        "TEAKETTLER", "ASPIDOCHELONE", "SANNAJA",
        "COME-AT-A-BODY", "BILLDAD", "WAPALOOSIE", "MOSKITTO", "DINGBAT", "AGROPELTER", "TRIPODERO", "RUMPTIFUSEL", "ROPERITE", "HUGAG", "HIDEBEHIND", "DUNGAVENHOOTER",
        // Folklore creatures, 65-99
        "MICE THAT EAT IRON", "AYOTOCHTLI", "LAGOPUS", "SHUYU", "BES CHEM",
        "TROLLGADDA", "NAMUNGUMI", "MAHWOT", "LIDERC", "BES RAP",
        "MAKALALA", "LOCH OICH MONSTER", "HOGA", "ZANKALLALA", "UGJUKNARPAK",
        "BES KOTAK", "IELTXU", "NADUBI", "BEAST OF BARRISDALE", "KIGUTILIK",
        "NANABOLELE", "LEUCROCOTTA", "COROCOTTA", "AMIXSAK", "CUERO",
        "CHIPEKWE", "KURREA", "SIEHNAM", "CHIPIQUE", "TROCHUS",
        "WITKES", "BREGDI", "RO", "BOIUNA", "FAD FELEN",
    };
    static_assert(sizeof(ENEMY_NAMES) / sizeof(ENEMY_NAMES[0]) == ENEMY_COUNT, "a name per enemy in the roster");

    // Static: the map is megabytes (its tiles, sight and the pyramid's art),
    // far past what main's stack holds.
    static DungeonMap dmap = {};
    DungeonPlayer dplayer = {};

    InteriorMap    imap    = {};
    InteriorPlayer iplayer = {};

    // Begin the game inside the spawn house, standing mid-room on the floor,
    // by the bed. Exiting the doormat drops the player onto the overworld at
    // start_x/start_y.
    interior_load(&imap, 0);
    interior_player_init(&iplayer, &player, &imap);
    iplayer.x = IMAP_W * IMAP_TILE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
    iplayer.y = 10 * IMAP_TILE + IMAP_TILE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
    player.facing = FACE_DOWN;  // toward the door
    state = STATE_INTERIOR;

    struct DungeonChaser { float x, y; int enemy_id; bool active; bool chasing; float aggro_timer; };
    static const int MAX_CHASERS = 32;
    DungeonChaser chasers[MAX_CHASERS] = {};
    int num_chasers = 0;

    std::unordered_map<uint32_t, std::vector<uint8_t>> dungeon_explored_cache;
    // Dungeons whose one treasure is taken, by seed (the same key as the
    // explored cache): a dungeon is laid out again each visit, and must not
    // put it back.
    std::unordered_map<uint32_t, bool> treasure_taken;
    char pickup_buf[48] = "";
    uint32_t current_dng_seed = 0;

    // Portal state: which overworld tiles DNG_ENTRY / DNG_EXIT map back to.
    // Set when entering a dungeon; both default to the entrance tile if there
    // is no connected partner dungeon.
    int dng_entry_portal_x = -1, dng_entry_portal_y = -1;
    int dng_exit_portal_x  = -1, dng_exit_portal_y  = -1;

    float esc_hold_time = 0.f;

    // Manual 60 fps frame cap — more consistent than SDL_RENDERER_PRESENTVSYNC on WSL2
    const Uint64 PERF_FREQ      = SDL_GetPerformanceFrequency();
    const Uint64 FRAME_TICKS    = PERF_FREQ / 60;
    Uint64       frame_deadline = SDL_GetPerformanceCounter() + FRAME_TICKS;

    // ── Battle entry, shared by every map that starts fights ─────────────────
    // Each queued enemy flashes once in fight order, the screen blinks white,
    // and black stripes wipe the map away; the battle then fades up with
    // everyone in place. c is the map's camera.
    static const float FLASH_STEP = 0.25f; // total time per enemy
    static const float FLASH_ON   = 0.16f; // how long it's visible within that window
    static const float HOLD       = 0.24f; // the screen flashes, after the enemy flashes
    static const float FADE       = 0.24f; // stripe wipe to black
    auto pre_battle_tick = [&](float step, GameState back) {
        pre_battle_timer += step;
        if (pre_battle_timer < flash_count * FLASH_STEP + HOLD + FADE) return;
        pre_battle_timer = -1.0f;
        delete battle_scene;
        battle_scene = new BattleScene(&player, battle_queue[0]);
        battle_scene->set_more_after(battle_queue_count > 1);
        state_after_battle = back;
        state = STATE_BATTLE;
    };
    // Black over the screen in the NES's four steps, not a smooth ramp: its
    // fades are palette swaps, a few brightness levels and nothing between.
    auto veil = [&](float a) {
        if (a <= 0.0f) return;
        a = a >= 1.0f ? 1.0f : (float)(int)(a * 4.0f + 0.999f) / 4.0f;  // round up: starts fully black
        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_BLEND);
        fc_draw_color(plat.renderer, 0, 0, 0, (Uint8)(255 * a));
        SDL_Rect r = { 0, 0, 640, 480 };
        SDL_RenderFillRect(plat.renderer, &r);
        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_NONE);
    };
    auto chaser_rect = [&](const Camera* c, float wx, float wy) {
        int sz = (int)(14 * c->zoom);
        return SDL_Rect{ cam_px(c, wx) - sz / 2, cam_py(c, wy) - sz / 2, sz, sz };
    };
    // Drawn over the map: the flashes and fade going in, the fade-in coming back.
    auto battle_veil_draw = [&](const Camera* c) {
        if (pre_battle_timer >= 0.0f) {
            int cur_step = (int)(pre_battle_timer / FLASH_STEP);
            float local_t = pre_battle_timer - cur_step * FLASH_STEP;
            for (int fi = 0; fi < flash_count; fi++) {
                SDL_Rect cr = chaser_rect(c, flash_entries[fi].x, flash_entries[fi].y);
                if (fi == cur_step && local_t < FLASH_ON) {
                    // Currently flashing — bright yellow
                    fc_draw_color(plat.renderer, 255, 220, 50, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 255, 255, 255, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                } else if (fi > cur_step) {
                    // Not yet reached — shown dim
                    fc_draw_color(plat.renderer, 80, 20, 20, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 120, 40, 40, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                } else {
                    // Flashed already: back to its own red, there until the wipe.
                    fc_draw_color(plat.renderer, 200, 30, 30, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 255, 80, 80, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                }
            }
            // After the flashes: the whole screen blinks white, the old
            // encounter flash, then black stripes slide in from alternate
            // sides a tile at a time until nothing is left.
            float flash_end = flash_count * FLASH_STEP;
            if (pre_battle_timer >= flash_end) {
                float t = pre_battle_timer - flash_end;
                if (t < HOLD) {
                    if ((int)(t / 0.04f) % 2 == 0) {
                        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_BLEND);
                        fc_draw_color(plat.renderer, 255, 255, 255, 170);
                        SDL_Rect r = { 0, 0, 640, 480 };
                        SDL_RenderFillRect(plat.renderer, &r);
                        SDL_SetRenderDrawBlendMode(plat.renderer, SDL_BLENDMODE_NONE);
                    }
                } else {
                    float k = (t - HOLD) / FADE;
                    int cols = (int)(nes_steps(k > 1.0f ? 1.0f : k, 10) * 20.0f + 0.5f);  // of 20 32px tiles
                    fc_draw_color(plat.renderer, 0, 0, 0, 255);
                    for (int row = 0; row < 30; row++) {          // 16px stripes
                        int w = cols * 32;
                        SDL_Rect r = { row % 2 ? 640 - w : 0, row * 16, w, 16 };
                        SDL_RenderFillRect(plat.renderer, &r);
                    }
                }
            }
        }
        // Back from a fight: the map steps up out of black.
        if (post_battle_t > 0.6f) veil((post_battle_t - 0.6f) / 0.4f);
    };

    while (running)
    {
        double dt_d = time_delta_seconds();
        if (dt_d > 0.05) dt_d = 0.05; // cap at 50 ms — prevents big jumps on stalled frames
        float dt = (float)dt_d;
        if (post_battle_t > 0.0f) post_battle_t -= dt;
        drown_t += dt;
        if (state == STATE_DUNGEON && dmap.type == DUNGEON_ENT_OASIS) {
            if (dungeon_breathing(&dmap, &dplayer)) oxygen = SDL_min(1.0f, oxygen + dt * 1.5f);
            else oxygen = SDL_max(0.0f, oxygen - dt / 16.0f);
            if (oxygen > 0.0f) oxy_hurt_t = 0.0f;
            else if ((oxy_hurt_t += dt) >= 2.0f) {
                oxy_hurt_t -= 2.0f;
                player.stats.hp = SDL_max(1, player.stats.hp - HP_PER_BAR);
                drown_t = 0.0f;
            }
        }
        tilemap_update(dt);

        input_begin_frame(&in);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            input_handle_event(&in, &e);
        }
        if (in.quit) running = false;
        if (input_down(&in, SDL_SCANCODE_ESCAPE)) {
            esc_hold_time += dt;
            if (esc_hold_time >= 3.f) running = false;
        } else {
            esc_hold_time = 0.f;
        }

        // Bound before any state draws, so the RenderClear each of them opens
        // with clears the frame rather than the window. Sized here too, since
        // the window is resizable and F11 changes it out from under us.
        if (can_target) {
            int fs = frame_scale_for(plat.renderer, LOGICAL_W, LOGICAL_H);
            if (fs != frame_scale || !frame_tex) {
                if (frame_tex) SDL_DestroyTexture(frame_tex);
                frame_tex = SDL_CreateTexture(plat.renderer, SDL_PIXELFORMAT_RGBA8888,
                                              SDL_TEXTUREACCESS_TARGET,
                                              LOGICAL_W * fs, LOGICAL_H * fs);
                if (frame_tex) SDL_SetTextureBlendMode(frame_tex, SDL_BLENDMODE_NONE);
                frame_scale = fs;
            }
        }
        if (frame_tex) {
            SDL_SetRenderTarget(plat.renderer, frame_tex);
            // Explicit: binding a target resets the logical size, and this is
            // what makes the scale inside the frame exactly frame_scale.
            SDL_RenderSetLogicalSize(plat.renderer, LOGICAL_W, LOGICAL_H);
        }

        if (input_pressed(&in, SDL_SCANCODE_F1))
            dbg_readout = !dbg_readout;

        if (input_pressed(&in, SDL_SCANCODE_F11)) {
            Uint32 flags = SDL_GetWindowFlags(plat.window);
            SDL_SetWindowFullscreen(plat.window,
                (flags & SDL_WINDOW_FULLSCREEN_DESKTOP) ? 0 : SDL_WINDOW_FULLSCREEN_DESKTOP);
        }

        // ── Debug menu toggle / navigation ───────────────────────────────────
        if (input_pressed(&in, SDL_SCANCODE_F2)) {
            dbg_open = !dbg_open;
            dbg_sel  = 0;
        }
        if (dbg_open) {
            // W/S up and down a column, wrapping; A/D across to the other
            // column, on the same line or its last. Q/E step the selected
            // row's value back and on, or flip it if it is on/off.
            {
                int pos   = dbg_pos(dbg_sel);
                int right = pos >= DBG_PLAYER_AT;
                int first = right ? DBG_PLAYER_AT : 0;
                int len   = right ? DBG_ROW_COUNT - DBG_PLAYER_AT : DBG_PLAYER_AT;
                int line  = pos - first;
                if (input_pressed(&in, SDL_SCANCODE_W)) line = (line + len - 1) % len;
                if (input_pressed(&in, SDL_SCANCODE_S)) line = (line + 1) % len;
                if (input_pressed(&in, SDL_SCANCODE_A) || input_pressed(&in, SDL_SCANCODE_D)) {
                    right = !right;
                    first = right ? DBG_PLAYER_AT : 0;
                    len   = right ? DBG_ROW_COUNT - DBG_PLAYER_AT : DBG_PLAYER_AT;
                    if (line >= len) line = len - 1;
                }
                dbg_sel = DBG_ORDER[first + line];
            }
            int  dbg_step   = input_pressed(&in, SDL_SCANCODE_E) - input_pressed(&in, SDL_SCANCODE_Q);
            bool dbg_toggle = input_pressed(&in, SDL_SCANCODE_E) || input_pressed(&in, SDL_SCANCODE_Q);

            if (dbg_sel == 0) {
                int was = dbg_target;
                dbg_target = (dbg_target + dbg_step + DBG_TARGET_COUNT) % DBG_TARGET_COUNT;
                // A different target is a different tour. Carrying the position
                // over would start the Dravium caves at the third one purely
                // because that is where the Kharvite tour had got to.
                if (dbg_target != was) dbg_tour = -1;
            }

            // Weapon: applied straight to the player so the change is visible
            // immediately — it drives both battle damage and the overworld tool
            // cooldown, with no confirm step to forget.
            // Row 8 does the same for the ore it is made of.
            {
                int step = dbg_step;
                if (dbg_sel == 5 && step) {
                    // Debug hands over the weapon outright: owned from here on.
                    player.equipped = (WeaponType)(((int)player.equipped + step + WEAPON_COUNT) % WEAPON_COUNT);
                    player.owned[player.equipped] = true;
                }
                Weapon& eq = equipped_weapon(&player);
                if (dbg_sel == 8)
                    eq.material = (Material)(((int)eq.material + step + MAT_COUNT) % MAT_COUNT);
            }

            bool dbg_confirm = input_pressed(&in, SDL_SCANCODE_RETURN) ||
                               input_pressed(&in, SDL_SCANCODE_Z);
            bool dbg_flip    = dbg_confirm || dbg_toggle;   // the on/off rows take either

            if (dbg_sel == 1 && dbg_confirm) {
                // Step to the NEXT place answering the target, not the nearest:
                // pressing this repeatedly walks every one of them in turn,
                // which is how you find out where they all are. Array order, so
                // press number three always lands on the same cave.
                //
                // The menu deliberately stays open. Touring is the point, and
                // an F2 between every hop is three keys where one will do; the
                // world still draws around the panel, and the minimap (M) is
                // the thing you are reading anyway.
                int n = dbg_target_list(dbg_target, dbg_list, MAX_DUNGEON_ENTRANCES);
                if (n > 0) {
                    // Modulo, not ++: the gen thread is still appending
                    // entrances early on, so the list can grow or shrink under
                    // a tour already in progress.
                    dbg_tour = (dbg_tour + 1) % n;
                    // Feet in the middle of the entrance tile, the same way the
                    // spawn-door placement above does it. Landing the sprite
                    // origin on the tile instead puts the feet a tile south of
                    // the mouth, which is far enough off that the entrance
                    // prompt never appears and a key press mines the rock in
                    // front of you rather than taking you in.
                    const DungeonEntrance& e = map->dungeon_entrances[dbg_list[dbg_tour]];
                    ow.x  = e.x * TILE_SIZE + TILE_SIZE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
                    ow.y  = e.y * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
                    state = STATE_OVERWORLD;
                }
            }

            if (dbg_sel == 2 && dbg_confirm) {
                // Regenerate the entire overworld with a new seed
                tilemap_cancel_gen();
                gen_thread.join();
                tilemap_reset_gen_cancel();
                map_seed = (unsigned int)SDL_GetTicks();
                printf("World seed: %u   (re-run with: game.exe %u)\n", map_seed, map_seed);
                fflush(stdout);
                delete map;
                map = new Tilemap();
                tilemap_build_overworld_phase1(map, map_seed);
                gen_thread = std::thread(tilemap_build_overworld_phase2, map, map_seed);
                resource_nodes_init(&resources);
                for (bool& b : oilbloom_done) b = false;
                dbg_tour = -1;   // new world, new set of entrances to tour
                ow.x = (MAP_WIDTH  / 2.0f) * TILE_SIZE;
                ow.y = (MAP_HEIGHT / 2.0f) * TILE_SIZE;
                state    = STATE_OVERWORLD;
                dbg_open = false;
            }

            if (dbg_sel == 3 && dbg_flip)
                dbg_noclip = !dbg_noclip;

            if (dbg_sel == 4 && dbg_flip)
                dbg_show_all = !dbg_show_all;

            if (dbg_sel == 6 && dbg_flip)
                dbg_grid = !dbg_grid;

            // Row 7: stand three tiles short of the seam, on the nearest
            // walkable tile to the middle of it, so the crossing can be tried
            // in seconds. The seam is the far edge of the wrap axis.
            // Row 9: ten of every material, and every book and special part,
            // to try every recipe. Never the raft: making it is the opening.
            if (dbg_sel == 9 && dbg_confirm)
                for (int it = 0; it < ITEM_COUNT; it++) {
                    if (item_is_material((Item)it))      item_slot(&player, (Item)it) += 10;
                    else if (it != ITEM_RAFT && item_count(&player, (Item)it) == 0)
                        item_slot(&player, (Item)it) = 1;
                }

            // Row 10: every weapon held, as good as it gets -- the best ore,
            // FASTER and MORE SHOTS at their tops.
            if (dbg_sel == 10 && dbg_confirm)
                for (int w = 0; w < WEAPON_COUNT; w++) {
                    if (!player.owned[w]) continue;
                    player.arsenal[w].material = (Material)(MAT_COUNT - 1);
                    player.arsenal[w].oil      = WEAPON_OIL_MAX;
                    player.arsenal[w].echo     = WEAPON_ECHO_MAX;
                }

            if (dbg_sel == 7 && dbg_confirm && state == STATE_OVERWORLD) {
                int sx = MAP_WIDTH / 2, sy = MAP_HEIGHT / 2;
                if (map->wrap_axis == WRAP_X) sx = MAP_WIDTH  - 4;
                else                          sy = MAP_HEIGHT - 4;
                for (int d = 0; d < MAP_WIDTH / 2; d++) {
                    int ax = sx, ay = sy;
                    if (map->wrap_axis == WRAP_X) ay = MAP_HEIGHT / 2 + ((d & 1) ? d / 2 : -(d / 2));
                    else                          ax = MAP_WIDTH  / 2 + ((d & 1) ? d / 2 : -(d / 2));
                    if (!tilemap_is_walkable(map, ax, ay)) continue;
                    ow.x = ax * TILE_SIZE + TILE_SIZE * 0.5f - (HB_X1 + HB_X2) * 0.5f;
                    ow.y = ay * TILE_SIZE + TILE_SIZE * 0.5f - (HB_Y1 + HB_Y2) * 0.5f;
                    break;
                }
                dbg_open = false;
            }

            if (input_pressed(&in, SDL_SCANCODE_ESCAPE))
                dbg_open = false;
        }

        // Whatever was gained since last frame now counts as found; the first
        // frame only takes stock, so what the game started with is not.
        items_note_gains(&player, item_last, !items_primed);
        items_primed = true;

        // ── The TAB menu (src/game_menu.cpp) ──────────────────────────────────
        // Opens anywhere but a battle (which has its own TAB panel) and the
        // title. Handled before anything else reads a key, so while it is open
        // the world sees none: game_in below is blank, and each raw key that
        // reaches into the world (zoom, map, leaving a room or dungeon, the
        // battle list) checks menu.open itself.
        {
            bool menu_ok  = state != STATE_BATTLE && state != STATE_TITLE;
            bool was_open = menu.open;
            if (input_pressed(&in, SDL_SCANCODE_TAB) && !dbg_open && menu_ok) game_menu_toggle(&menu);
            else if (menu.open && menu_ok) game_menu_update(&menu, &player, &in, dt);
            // The key that closed it (Z on CLOSE) is still held next frame;
            // without this it would swing at whatever stands in front.
            if (was_open && !menu.open) {
                input_consume(&in, SDL_SCANCODE_RETURN);
                input_consume(&in, SDL_SCANCODE_Z);
                input_consume(&in, SDL_SCANCODE_SPACE);
            }
        }

        // ── Battle test list (F3) ─────────────────────────────────────────────
        if (input_pressed(&in, SDL_SCANCODE_F3) && !dbg_open && !menu.open && state != STATE_BATTLE)
            battle_list_open = !battle_list_open;

        // The list, filtered by what's typed: letters match anywhere in the
        // name, a number matches the id (its digits from the start).
        int battle_hits[ENEMY_COUNT], battle_n = 0;
        for (int e = 0; e < ENEMY_COUNT; e++) {
            char id[8];
            SDL_snprintf(id, sizeof(id), "%02d", e);
            bool digits = battle_query[0] >= '0' && battle_query[0] <= '9';
            bool hit = digits ? (SDL_strncmp(id, battle_query, SDL_strlen(battle_query)) == 0 ||
                                 SDL_atoi(battle_query) == e)
                              : SDL_strstr(ENEMY_NAMES[e], battle_query) != nullptr;
            if (hit) battle_hits[battle_n++] = e;
        }
        if (battle_list_sel >= battle_n) battle_list_sel = battle_n > 0 ? battle_n - 1 : 0;

        if (battle_list_open) {
            // Typing: A-Z, 0-9, space, - and ' (names like COME-AT-A-BODY,
            // GRAND'GOULE); backspace takes one off. Enter fights.
            size_t ql = SDL_strlen(battle_query);
            auto type = [&](char c) {
                if (ql + 1 < sizeof(battle_query)) { battle_query[ql++] = c; battle_query[ql] = 0; battle_list_sel = 0; }
            };
            for (int k = 0; k < 26; k++)
                if (input_pressed(&in, (SDL_Scancode)(SDL_SCANCODE_A + k))) type((char)('A' + k));
            for (int k = 0; k < 10; k++)   // SDL lists 1..9 then 0
                if (input_pressed(&in, (SDL_Scancode)(SDL_SCANCODE_1 + k))) type((char)(k == 9 ? '0' : '1' + k));
            if (input_pressed(&in, SDL_SCANCODE_SPACE))      type(' ');
            if (input_pressed(&in, SDL_SCANCODE_MINUS))      type('-');
            if (input_pressed(&in, SDL_SCANCODE_APOSTROPHE)) type('\'');
            if (input_pressed(&in, SDL_SCANCODE_BACKSPACE) && ql > 0) { battle_query[--ql] = 0; battle_list_sel = 0; }

            if (battle_n > 0) {
                if (input_pressed(&in, SDL_SCANCODE_UP))
                    battle_list_sel = (battle_list_sel + battle_n - 1) % battle_n;
                if (input_pressed(&in, SDL_SCANCODE_DOWN))
                    battle_list_sel = (battle_list_sel + 1) % battle_n;
                if (input_pressed(&in, SDL_SCANCODE_RETURN)) {
                    delete battle_scene;
                    battle_scene = new BattleScene(&player, battle_hits[battle_list_sel]);
                    state = STATE_BATTLE;
                    battle_list_open = false;
                }
            }
            if (input_pressed(&in, SDL_SCANCODE_ESCAPE)) {
                if (ql > 0) { battle_query[0] = 0; battle_list_sel = 0; }   // first clears the search
                else battle_list_open = false;
            }
        }

        // Blank input fed to game logic while menu is open so the player stands still.
        Input in_blank = {0};
        const Input* game_in = (dbg_open || menu.open || map_open || battle_list_open)
                                ? &in_blank : &in;


        if (input_pressed(&in, SDL_SCANCODE_B) && !dbg_open && !menu.open && state != STATE_BATTLE) {
            delete battle_scene;
            battle_scene = new BattleScene(&player, 0);
            state = STATE_BATTLE;
        }

        // Mouse wheel steps through pixel-perfect zoom levels
        // scroll up (+y) = zoom in = higher index; scroll down = zoom out = lower index
        if (in.mouse_wheel != 0 && state != STATE_BATTLE && !menu.open) {
            zoom_idx += in.mouse_wheel;
            if (zoom_idx < 0)           zoom_idx = 0;
            if (zoom_idx >= zoom_count) zoom_idx = zoom_count - 1;
            cam.zoom = zoom_levels[zoom_idx];
        }

        // Q / E swap weapons on the map and in dungeons too (battle does its
        // own, in BattleScene::_cycle).
        ow_swap_t += dt;
        if ((state == STATE_OVERWORLD || state == STATE_DUNGEON) && !menu.open && !dbg_open)
            for (int dir : { -1, 1 })
                if (input_pressed(&in, dir < 0 ? SDL_SCANCODE_Q : SDL_SCANCODE_E)) {
                    player.equipped = owned_neighbour(&player, dir);
                    ow_swap_t = 0.0f;   // the box shows even with only one weapon
                }

        GameState state_before = state;

        switch (state) {
            case STATE_TITLE:
                fc_draw_color(plat.renderer, 0, 0, 0, 255);
                SDL_RenderClear(plat.renderer);
                break;

            case STATE_OVERWORLD: {
                // Lazy-spawn graveyard resource nodes when player gets within range.
                // Done here (main thread) so resource nodes are never touched by gen thread.
                {
                    const float SPAWN_RANGE = 1000.0f; // pixels
                    float px = ow.x + player.width  * 0.5f;
                    float py = ow.y + player.height * 0.5f;
                    for (int i = 0; i < map->num_dungeon_entrances; i++) {
                        DungeonEntrance* e = &map->dungeon_entrances[i];
                        if (!dungeon_is_graveyard(e->type)) continue;
                        if (e->gravestones_spawned) continue;
                        float ex = (float)(e->x * TILE_SIZE + TILE_SIZE / 2);
                        float ey = (float)(e->y * TILE_SIZE + TILE_SIZE / 2);
                        float ddx = wrap_dpx(px - ex), ddy = wrap_dpy(py - ey);
                        if (ddx*ddx + ddy*ddy < SPAWN_RANGE * SPAWN_RANGE) {
                            // SM hides its entrance under one of a scattered
                            // handful; the two larger scales lay theirs out in
                            // rows across a visible yard.
                            if (e->type == DUNGEON_ENT_GRAVEYARD_SM)
                                tilemap_spawn_graveyard_nodes(map, &resources, i, map_seed);
                            else
                                tilemap_spawn_graveyard_lg_nodes(map, &resources, i, map_seed);
                        }
                    }
                }

                // Oilblooms, on the same lazy rule as the graveyards.
                for (int s = 0; s < OILBLOOM_SITES; s++)
                    if (!oilbloom_done[s])
                        oilbloom_done[s] = tilemap_spawn_oilbloom(map, &resources, map_seed, s,
                            ow.x + player.width * 0.5f, ow.y + player.height * 0.5f);

                HarvestResult harvest = {};
                overworld_update(&ow, &player, game_in, dt, &resources, map, &cam, dbg_noclip, &harvest);
                floattext_spawn_from_harvest(&cur_float, &harvest);

                camera_follow(&cam, ow.x, ow.y, (float)player.width, (float)player.height);

                fc_draw_color(plat.renderer, 10, 10, 20, 255);
                SDL_RenderClear(plat.renderer);
                

                tilemap_draw_base(map, &cam, plat.renderer);
                resource_nodes_draw(&resources, &cam, plat.renderer, tilemap_get_town_tex());
                // Afloat: the raft under the player's feet, the menu's own
                // picture of it at 2x, while their feet are on water.
                {
                    float fx = ow.x + (HB_X1 + HB_X2) * 0.5f, fy = ow.y + (HB_Y1 + HB_Y2) * 0.5f;
                    if (player.raft > 0 && tilemap_pixel_water(map, fx, fy)) {
                        int size = (int)(32 * cam.zoom);
                        game_menu_draw_item(&menu, plat.renderer, ITEM_RAFT,
                                            cam_screen_x(&cam, fx) - size / 2,
                                            cam_screen_y(&cam, fy) - size / 2, size);
                    }
                }
                player_draw(&player, ow.x, ow.y, &cam, plat.renderer, player_sprite);
                overworld_draw_swing(&ow, &cam, plat.renderer);
                tilemap_draw_over_player(map, &cam, plat.renderer, ow.x, ow.y,
                                         (float)player.width, (float)player.height, ow.y + HB_Y2);
                resource_nodes_draw_over_player(&resources, &cam, plat.renderer, ow.x, ow.y,
                                                (float)player.width, (float)player.height, ow.y + HB_Y2);
                tilemap_draw_depth(map, &cam, plat.renderer);
                if (dbg_grid) tilemap_draw_debug_grid(map, &cam, plat.renderer);

                // --- Weapon cooldown bar ---
                {
                    // Same source the swing uses, so the bar always spans the
                    // cooldown this weapon actually sets rather than its raw
                    // fire rate — which several weapons no longer go by.
                    float max_cd = weapon_cooldown_seconds(equipped_weapon(&player));
                    float ready  = (max_cd > 0.0f && ow.swing.tool_cd > 0.0f)
                                 ? 1.0f - ow.swing.tool_cd / max_cd : 1.0f;
                    if (ready < 0.0f) ready = 0.0f;
                    if (ready > 1.0f) ready = 1.0f;
                    const int BAR_W = 160, BAR_H = 5;
                    const int BAR_X = (640 - BAR_W) / 2, BAR_Y = 480 - 12;
                    fc_draw_color(plat.renderer, 40, 40, 40, 200);
                    SDL_Rect track = { BAR_X, BAR_Y, BAR_W, BAR_H };
                    SDL_RenderFillRect(plat.renderer, &track);
                    fc_draw_color(plat.renderer, 255, 220, 0, 255);
                    SDL_Rect fill = { BAR_X, BAR_Y, (int)(BAR_W * ready), BAR_H };
                    SDL_RenderFillRect(plat.renderer, &fill);
                }

                // --- Floating resource text ---
                floattext_update_draw(&cur_float, dt, &cam, plat.renderer);


                // Dungeon entry — show name prompt when standing on an entrance.
                if (ow.at_dungeon_entrance) {
                    static const char* dungeon_names[] = {
                        "CAVE",
                        "RUINS",
                        "GRAVEYARD",
                        "GRAVEYARD",
                        "OASIS",
                        "PYRAMID",
                        "STONEHENGE",
                        "LARGE TREE",
                        "CATACOMBS",
                    };
                    int ci = (int)ow.dungeon_type;
                    if (ci < 0 || ci >= DUNGEON_ENT_COUNT) ci = 0;
                    const char* name = dungeon_names[ci];

                    draw_nes_panel(plat.renderer, 0, 448, 640, 32);

                    int nx = (640 - text_width(name, 2)) / 2;
                    draw_text(plat.renderer, name, nx, 456, 2, 255, 255, 255);

                    // difficulty bar inside inner border
                    fc_draw_color(plat.renderer, 40, 40, 40, 255);
                    SDL_Rect diff_track = {NES_PAD + 2, 472, 640 - (NES_PAD+2)*2, 4};
                    SDL_RenderFillRect(plat.renderer, &diff_track);
                    fc_draw_color(plat.renderer, 255, 255, 255, 255);
                    SDL_Rect diff_fill = {NES_PAD + 2, 472, (int)((640 - (NES_PAD+2)*2) * ow.dungeon_difficulty), 4};
                    SDL_RenderFillRect(plat.renderer, &diff_fill);

                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        int etx = wrap_x((int)((ow.x + player.width  * 0.5f) / TILE_SIZE));
                        int ety = wrap_y((int)((ow.y + player.height - 8.0f) / TILE_SIZE));

                        // Find the DungeonEntrance record we're standing on.
                        int cur_ent_idx = -1;
                        for (int ci = 0; ci < map->num_dungeon_entrances; ci++) {
                            DungeonEntrance* ce = &map->dungeon_entrances[ci];
                            int stamp = (ce->size == 0) ? 1 : 2;
                            if (etx >= ce->x && etx < ce->x + stamp &&
                                ety >= ce->y && ety < ce->y + stamp) {
                                cur_ent_idx = ci; break;
                            }
                        }

                        // Which dungeon this is, how hard, and where its stairs
                        // come out. One answer with its precedence written down,
                        // in dungeon.cpp where a tool can reach it -- as four
                        // last-writer-wins blocks out here, the partner rule
                        // silently beat the cave-system rule and a mountain
                        // could hide two different caves.
                        DungeonWiring w = dungeon_wiring_for(map, map_seed, cur_ent_idx);

                        dng_entry_portal_x = w.entry_ow_x; dng_entry_portal_y = w.entry_ow_y;
                        dng_exit_portal_x  = w.exit_ow_x;  dng_exit_portal_y  = w.exit_ow_y;
                        int   from_exit     = w.from_exit;
                        float connect_angle = w.connect_angle;
                        int   n_cave_mouth  = w.n_mouths;
                        int   my_mouth      = w.my_mouth;

                        dmap.want_portals = (n_cave_mouth >= 2) ? n_cave_mouth : 2;
                        dmap.starter      = w.starter;
                        dmap.step_pyramid = w.step_pyramid;
                        for (int m = 0; m < n_cave_mouth; m++) {
                            dmap.want_ox[m] = w.want_ox[m];
                            dmap.want_oy[m] = w.want_oy[m];
                        }

                        dungeon_generate(&dmap, w.type, w.difficulty, w.seed);
                        current_dng_seed = w.seed;
                        if (treasure_taken.count(current_dng_seed))
                            for (int li = 0; li < dmap.num_loot; li++)
                                if (dmap.loot[li].item >= 0) dmap.loot[li].collected = true;
                        {
                            auto exp_it = dungeon_explored_cache.find(current_dng_seed);
                            if (exp_it != dungeon_explored_cache.end())
                                SDL_memcpy(dmap.explored, exp_it->second.data(), DMAP_H * DMAP_W);
                        }

                        // Where the stairs let out. The three cases and the
                        // invariant they keep live in dungeon.cpp, next to the
                        // code that carved the stairs — out here they were
                        // somewhere tools/dngportals.cpp could not check them.
                        if (n_cave_mouth >= 2) {
                            dungeon_bind_cave_mouths(&dmap, w.mouth_ow_x, w.mouth_ow_y,
                                                     n_cave_mouth);
                        } else if (!isnan(connect_angle)) {
                            dungeon_bind_pair(&dmap, connect_angle,
                                              dng_entry_portal_x, dng_entry_portal_y, w.entry_type,
                                              dng_exit_portal_x,  dng_exit_portal_y,  w.exit_type);
                        } else {
                            dungeon_bind_solo(&dmap, dng_entry_portal_x, dng_entry_portal_y);
                        }

                        dungeon_player_init(&dplayer, &player, &dmap, from_exit);
                        // Come in by the mouth you actually used. Otherwise every
                        // way into a mountain drops you at the same chamber and
                        // the cave stops being a route through it.
                        if (n_cave_mouth >= 2 && my_mouth >= 0 &&
                            my_mouth < dmap.num_portals) {
                            dplayer.x = (float)(dmap.portals[my_mouth].tx * DMAP_TILE);
                            dplayer.y = (float)(dmap.portals[my_mouth].ty * DMAP_TILE
                                                + DMAP_TILE / 2 - 24);
                        }
                        num_chasers = 0;
                        for (int si = 0; si < dmap.num_spawners && num_chasers < MAX_CHASERS; si++) {
                            DungeonSpawner& sp = dmap.spawners[si];
                            chasers[num_chasers++] = {
                                sp.tx * DMAP_TILE + DMAP_TILE * 0.5f,
                                sp.ty * DMAP_TILE + DMAP_TILE * 0.5f,
                                sp.enemy_id, true, false
                            };
                        }
                        state = STATE_DUNGEON;
                        oxygen = 1.0f; oxy_hurt_t = 0.0f;          // a breath at the top of the shaft
                        dplayer.vx = dplayer.vy = 0.0f;
                    }
                }
                // Building door — prompt and enter the interior.
                else if (ow.at_interior_door) {
                    draw_nes_panel(plat.renderer, 0, 457, 640, 23);
                    const char* lbl = "ENTER";
                    draw_text(plat.renderer, lbl,
                              (640 - text_width(lbl, 2)) / 2, 461, 2, 255, 255, 255);

                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        const InteriorDoor& d = map->doors[ow.interior_door_idx];
                        interior_load(&imap, d.interior_id);
                        interior_player_init(&iplayer, &player, &imap);
                        state = STATE_INTERIOR;
                    }
                }


                if (input_pressed(&in, SDL_SCANCODE_M) && !dbg_open && !menu.open)
                    map_open = !map_open;

                if (map_open) {
                    minimap_draw(map, plat.renderer, 640, 480, ow.x, ow.y);

                    if (in.mouse_left_pressed) {
                        float wx, wy;
                        if (minimap_click_to_world(640, 480, in.mouse_x, in.mouse_y, &wx, &wy)) {
                            ow.x = wx;
                            ow.y = wy;
                            map_open = false;
                        }
                    }
                }
                break;
            }

            case STATE_BATTLE:
                if (battle_scene) {
                    battle_scene->update(game_in, dt);
                    battle_scene->draw(plat.renderer, player_sprite);
                    if (battle_scene->is_done()) {
                        {
                            bool victory = battle_scene->get_phase() == BATTLE_PHASE_VICTORY;
                            float last_x = battle_scene->player_x(), last_y = battle_scene->player_y();
                            delete battle_scene;
                            battle_scene = nullptr;
                            if (victory && battle_queue_idx + 1 < battle_queue_count) {
                                battle_queue_idx++;
                                battle_scene = new BattleScene(&player, battle_queue[battle_queue_idx],
                                                               true, last_x, last_y);
                                battle_scene->set_more_after(battle_queue_idx + 1 < battle_queue_count);
                            } else {
                                post_battle_t = 1.0f;
                                // Re-activate any queued enemies that were never fought.
                                for (int qi = battle_queue_idx + 1; qi < battle_queue_count; qi++) {
                                    int cidx = battle_queue_chaser_idx[qi];
                                    if (cidx >= 0 && cidx < num_chasers)
                                        chasers[cidx].active = true;
                                }
                                battle_queue_count = 0;
                                battle_queue_idx   = 0;
                                state = state_after_battle;
                                state_after_battle = STATE_OVERWORLD;
                            }
                        }
                    }
                }
                break;

            case STATE_DUNGEON: {
                if (pre_battle_timer < 0.0f) {
                    HarvestResult dng_harvest = {};
                    dungeon_player_update(&dplayer, &player, game_in, dt, &dmap, &cam, dbg_noclip, &dng_harvest);
                    floattext_spawn_from_harvest(&cur_float, &dng_harvest);
                    if (dplayer.picked_item >= 0) {
                        treasure_taken[current_dng_seed] = true;
                        SDL_snprintf(pickup_buf, sizeof(pickup_buf), "GOT %s", item_name((Item)dplayer.picked_item));
                        pickup_note   = pickup_buf;
                        pickup_note_t = 2.5f;
                    }
                }

                float dpcx = dplayer.x + player.width  * 0.5f;
                float dpcy = dplayer.y + player.height * 0.5f;
                cam.zoom = dmap.type == DUNGEON_ENT_OASIS ? 1.0f : zoom_levels[zoom_idx];   // the oasis is one screen tall
                camera_follow(&cam, dplayer.x, dplayer.y, (float)player.width, (float)player.height);
                dungeon_frame_camera(&dmap, &cam);

                if (pre_battle_timer >= 0.0f) {
                    pre_battle_tick(dt, STATE_DUNGEON);
                } else if (post_battle_t > 0.0f) {
                    // Just back from a fight: everyone holds a beat, so the
                    // next battle can't start before the player can move.
                } else {
                    // Update chasers — activate when seen, move toward player, queue on contact.
                    // As fast as the player runs: outrunning them takes a lead.
                    const float CHASER_SPEED  = PLAYER_RUN_SPEED;
                    const float TRIGGER_DIST2 = 22.0f * 22.0f;
                    // Chasers are drawn 14px wide; keep their centres this far
                    // apart so a pack never stacks into a single square.
                    const float CHASER_SEP    = 16.0f;

                    auto dng_walkable = [&](float wx, float wy) {
                        int tx = (int)(wx / DMAP_TILE), ty = (int)(wy / DMAP_TILE);
                        return tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H &&
                               dmap.tiles[ty][tx] != DNG_WALL;
                    };

                    for (int ci = 0; ci < num_chasers; ci++) {
                        DungeonChaser& ch = chasers[ci];
                        if (!ch.active) continue;

                        // Drop aggro if the chaser has moved outside the player's FOV.
                        if (ch.chasing) {
                            int ctx = (int)(ch.x / DMAP_TILE), cty = (int)(ch.y / DMAP_TILE);
                            if (ctx < 0 || ctx >= DMAP_W || cty < 0 || cty >= DMAP_H ||
                                !dmap.visible[cty][ctx]) {
                                ch.chasing = false;
                            }
                        }

                        // Start aggro timer once the player's FOV reaches the chaser's tile.
                        if (!ch.chasing) {
                            int ctx = (int)(ch.x / DMAP_TILE), cty = (int)(ch.y / DMAP_TILE);
                            if (ctx >= 0 && ctx < DMAP_W && cty >= 0 && cty < DMAP_H &&
                                dmap.visible[cty][ctx]) {
                                ch.chasing = true;
                                ch.aggro_timer = 1.0f;
                            } else {
                                continue;
                            }
                        }

                        if (ch.aggro_timer > 0.0f) {
                            ch.aggro_timer -= dt;
                            continue;
                        }

                        float cdx = dpcx - ch.x, cdy = dpcy - ch.y;
                        float dist2 = cdx*cdx + cdy*cdy;

                        if (dist2 < TRIGGER_DIST2) {
                            ch.active = false;

                            // Snapshot queue: touching enemy first, then up to 2 nearest
                            // other chasers that are currently in the player's FOV.
                            battle_queue_count = 0;
                            battle_queue_idx   = 0;
                            battle_queue_chaser_idx[0] = battle_queue_chaser_idx[1] = battle_queue_chaser_idx[2] = -1;
                            battle_queue[battle_queue_count++] = ch.enemy_id;
                            flash_entries[0] = { ch.x, ch.y };

                            struct { float d2; int enemy_id; int idx; } cands[MAX_CHASERS];
                            int nc = 0;
                            for (int cj = 0; cj < num_chasers; cj++) {
                                if (cj == ci) continue;
                                DungeonChaser& o = chasers[cj];
                                if (!o.active || !o.chasing) continue;
                                int otx = (int)(o.x / DMAP_TILE), oty = (int)(o.y / DMAP_TILE);
                                if (otx < 0 || otx >= DMAP_W || oty < 0 || oty >= DMAP_H) continue;
                                if (!dmap.visible[oty][otx]) continue;
                                float odx = dpcx - o.x, ody = dpcy - o.y;
                                cands[nc++] = { odx*odx + ody*ody, o.enemy_id, cj };
                            }
                            for (int a = 1; a < nc; a++) {
                                auto tmp = cands[a];
                                int b = a - 1;
                                while (b >= 0 && cands[b].d2 > tmp.d2) { cands[b+1] = cands[b]; b--; }
                                cands[b+1] = tmp;
                            }
                            for (int k = 0; k < nc && battle_queue_count < 3; k++) {
                                flash_entries[battle_queue_count] = { chasers[cands[k].idx].x, chasers[cands[k].idx].y };
                                battle_queue_chaser_idx[battle_queue_count] = cands[k].idx;
                                battle_queue[battle_queue_count++] = cands[k].enemy_id;
                                chasers[cands[k].idx].active = false;
                            }

                            // Clear every other active chaser currently visible in the
                            // player's FOV — not just the ones joining this fight — so
                            // finishing this encounter doesn't immediately chain into
                            // another one with whoever else was standing nearby.
                            for (int cj = 0; cj < num_chasers; cj++) {
                                if (cj == ci) continue;
                                DungeonChaser& o = chasers[cj];
                                if (!o.active) continue;
                                int otx = (int)(o.x / DMAP_TILE), oty = (int)(o.y / DMAP_TILE);
                                if (otx < 0 || otx >= DMAP_W || oty < 0 || oty >= DMAP_H) continue;
                                if (!dmap.visible[oty][otx]) continue;
                                o.active = false;
                            }

                            flash_count       = battle_queue_count;
                            pre_battle_timer  = 0.0f;
                            break;
                        }

                        // Steer toward the player, blended with a short-range push
                        // away from any other chaser we're crowding, so they flow
                        // around each other instead of merging.
                        float dist = sqrtf(dist2);
                        float mvx = cdx / dist, mvy = cdy / dist;
                        for (int cj = 0; cj < num_chasers; cj++) {
                            if (cj == ci) continue;
                            const DungeonChaser& o = chasers[cj];
                            if (!o.active) continue;
                            float sx = ch.x - o.x, sy = ch.y - o.y;
                            float sd2 = sx*sx + sy*sy;
                            if (sd2 >= CHASER_SEP * CHASER_SEP) continue;
                            if (sd2 < 0.0001f) { sx = 1.0f; sy = 0.0f; sd2 = 1.0f; }
                            float sd = sqrtf(sd2);
                            float w  = (CHASER_SEP - sd) / CHASER_SEP;  // 1 when coincident
                            mvx += (sx / sd) * w * 1.5f;
                            mvy += (sy / sd) * w * 1.5f;
                        }
                        float mvl = sqrtf(mvx*mvx + mvy*mvy);
                        if (mvl > 0.0001f) { mvx /= mvl; mvy /= mvl; }

                        float nx = ch.x + mvx * CHASER_SPEED * dt;
                        float ny = ch.y + mvy * CHASER_SPEED * dt;
                        if (dng_walkable(nx, ny)) {
                            ch.x = nx; ch.y = ny;
                        } else {
                            if (dng_walkable(nx, ch.y)) ch.x = nx;
                            if (dng_walkable(ch.x, ny)) ch.y = ny;
                        }
                    }

                    // Hard separation: push overlapping pairs apart until nothing
                    // overlaps, so what gets drawn this frame never shows two
                    // chasers merged. This is a relaxation, and one sweep only
                    // propagates a correction one link along a chain -- a pack
                    // crammed into a corridor needs many sweeps to spread out, so
                    // the cap is high and the loop exits as soon as it is clean.
                    // In the common case (nothing touching) that costs one sweep.
                    if (pre_battle_timer < 0.0f) {
                        // Slide per-axis, so a corridor wall blocking one
                        // component doesn't discard the whole correction.
                        auto shove = [&](DungeonChaser& C, float dx, float dy) {
                            if (dng_walkable(C.x + dx, C.y + dy)) {
                                C.x += dx; C.y += dy; return true;
                            }
                            bool moved = false;
                            if (dx != 0.0f && dng_walkable(C.x + dx, C.y)) { C.x += dx; moved = true; }
                            if (dy != 0.0f && dng_walkable(C.x, C.y + dy)) { C.y += dy; moved = true; }
                            return moved;
                        };

                        for (int pass = 0; pass < 32; pass++) {
                            bool overlapped = false;
                            for (int a = 0; a < num_chasers; a++) {
                                if (!chasers[a].active) continue;
                                for (int b = a + 1; b < num_chasers; b++) {
                                    if (!chasers[b].active) continue;
                                    DungeonChaser& A = chasers[a];
                                    DungeonChaser& B = chasers[b];
                                    float sx = B.x - A.x, sy = B.y - A.y;
                                    float d2 = sx*sx + sy*sy;
                                    if (d2 >= CHASER_SEP * CHASER_SEP) continue;
                                    overlapped = true;
                                    float d = sqrtf(d2);
                                    if (d < 0.0001f) {
                                        // Coincident: vary the direction by index so
                                        // a whole stack doesn't unfold along one axis.
                                        float ang = (float)((a * 7 + b) % 16) / 16.0f * 6.28318f;
                                        sx = cosf(ang); sy = sinf(ang); d = 1.0f;
                                    }
                                    float ux = sx / d, uy = sy / d;
                                    float half = (CHASER_SEP - d) * 0.5f;
                                    bool a_moved = shove(A, -ux * half, -uy * half);
                                    bool b_moved = shove(B,  ux * half,  uy * half);
                                    // Whatever one side couldn't take, give to the other.
                                    if (!a_moved) shove(B,  ux * half,  uy * half);
                                    if (!b_moved) shove(A, -ux * half, -uy * half);
                                }
                            }
                            if (!overlapped) break;
                        }
                    }
                }
                if (state == STATE_BATTLE) break;

                // Background matches wall colour so map edges blend in
                fc_draw_color(plat.renderer, 5, 5, 8, 255);
                SDL_RenderClear(plat.renderer);

                SDL_Rect drown_vp;
                hurt_shake_begin(plat.renderer, drown_t, &drown_vp);     // drowning: hurt as a fight shows it
                dungeon_draw(&dmap, &dplayer, &cam, plat.renderer, dbg_show_all);
                if (dbg_grid) dungeon_draw_debug_grid(&dmap, &cam, plat.renderer);
                if (!dungeon_draw_swimmer(&dmap, &dplayer, &player, &cam, plat.renderer))
                    player_draw(&player, dplayer.x, dplayer.y, &cam, plat.renderer, player_sprite);
                dungeon_draw_front(&dmap, &dplayer, &cam, plat.renderer);
                dungeon_draw_swing(&dplayer, &cam, plat.renderer);

                // --- Floating resource text ---
                floattext_update_draw(&cur_float, dt, &cam, plat.renderer);

                // Draw active chasers
                for (int ci = 0; ci < num_chasers; ci++) {
                    DungeonChaser& ch = chasers[ci];
                    if (!ch.active) continue;
                    int sz  = (int)(14 * cam.zoom);
                    int sx  = cam_px(&cam, ch.x) - sz / 2;
                    int sy  = cam_py(&cam, ch.y) - sz / 2;
                    SDL_Rect cr = { sx, sy, sz, sz };
                    fc_draw_color(plat.renderer, 200, 30, 30, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 255, 80, 80, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                }
                hurt_shake_end(plat.renderer, &drown_vp);
                hurt_flash(plat.renderer, drown_t, 640, 480);

                battle_veil_draw(&cam);

                // DNG_ENTRY tile — exit back to the overworld entrance we came from.
                if (dplayer.at_entry) {
                    draw_nes_panel(plat.renderer, 0, 457, 640, 23);
                    const char* lbl = "EXIT";
                    draw_text(plat.renderer, lbl,
                              (640 - text_width(lbl, 2)) / 2, 461, 2, 255, 255, 255);

                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        dungeon_explored_cache[current_dng_seed].assign(
                            &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                        // Leave by the portal you are standing on. A cave has one
                        // per mouth, so which one you are on is the whole question,
                        // and the old pair of destinations could only answer it for
                        // two. Falls back to the pair when a portal carries no
                        // destination of its own.
                        int land_x = dng_entry_portal_x, land_y = dng_entry_portal_y;
                        {
                            float pcx = dplayer.x + (HB_X1 + HB_X2) * 0.5f;
                            float pcy = dplayer.y + (HB_Y1 + HB_Y2) * 0.5f;
                            int ptx = (int)(pcx / DMAP_TILE), pty = (int)(pcy / DMAP_TILE);
                            for (int pi = 0; pi < dmap.num_portals; pi++)
                                if (dmap.portals[pi].tx == ptx && dmap.portals[pi].ty == pty &&
                                    dmap.portals[pi].ow_x >= 0) {
                                    land_x = dmap.portals[pi].ow_x;
                                    land_y = dmap.portals[pi].ow_y;
                                }
                        }
                        ow.x = (float)(land_x * TILE_SIZE);
                        ow.y = (float)(land_y * TILE_SIZE);
                        state = STATE_OVERWORLD;
                    }
                }

                // DNG_EXIT tile — exit to the connected overworld entrance (or back if none).
                if (dplayer.at_exit) {
                    draw_nes_panel(plat.renderer, 0, 457, 640, 23);
                    const char* lbl2 = "ENTER";
                    draw_text(plat.renderer, lbl2,
                              (640 - text_width(lbl2, 2)) / 2, 461, 2, 255, 255, 255);

                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        dungeon_explored_cache[current_dng_seed].assign(
                            &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                        // Leave by the portal you are standing on. A cave has one
                        // per mouth, so which one you are on is the whole question,
                        // and the old pair of destinations could only answer it for
                        // two. Falls back to the pair when a portal carries no
                        // destination of its own.
                        int land_x = dng_exit_portal_x, land_y = dng_exit_portal_y;
                        {
                            float pcx = dplayer.x + (HB_X1 + HB_X2) * 0.5f;
                            float pcy = dplayer.y + (HB_Y1 + HB_Y2) * 0.5f;
                            int ptx = (int)(pcx / DMAP_TILE), pty = (int)(pcy / DMAP_TILE);
                            for (int pi = 0; pi < dmap.num_portals; pi++)
                                if (dmap.portals[pi].tx == ptx && dmap.portals[pi].ty == pty &&
                                    dmap.portals[pi].ow_x >= 0) {
                                    land_x = dmap.portals[pi].ow_x;
                                    land_y = dmap.portals[pi].ow_y;
                                }
                        }
                        ow.x = (float)(land_x * TILE_SIZE);
                        ow.y = (float)(land_y * TILE_SIZE);
                        state = STATE_OVERWORLD;
                    }
                }


                if (input_pressed(&in, SDL_SCANCODE_M) && !menu.open)
                    map_open = !map_open;

                if (map_open) {
                    dungeon_minimap_draw(&dmap, &dplayer, plat.renderer, 640, 480, dbg_show_all);

                    if (in.mouse_left_pressed) {
                        float wx, wy;
                        if (dungeon_minimap_click_to_world(&dmap, 640, 480, in.mouse_x, in.mouse_y,
                                                           dbg_show_all, &wx, &wy)) {
                            dplayer.x = wx;
                            dplayer.y = wy;
                            map_open = false;
                        }
                    }
                }

                if (!dbg_open && !menu.open && input_pressed(&in, SDL_SCANCODE_ESCAPE)) {
                    dungeon_explored_cache[current_dng_seed].assign(
                        &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                    state = STATE_OVERWORLD;
                }
                break;
            }

            case STATE_INTERIOR: {
                // Interior fills the screen 1:1 — identity camera.
                Camera icam = {};
                icam.zoom = 1.0f;
                icam.screen_w = LOGICAL_W;
                icam.screen_h = LOGICAL_H;

                if (pre_battle_timer >= 0.0f) {
                    pre_battle_tick(dt, STATE_INTERIOR);
                    if (state == STATE_BATTLE) break;
                } else {
                    interior_player_update(&iplayer, &player, game_in, dt, &imap);
                    // Test dummies: walk into one and they all fight, as a
                    // dungeon pack does -- the one touched first, then by
                    // distance, each flashing in that order. Armed again once
                    // the player is off all of them.
                    float pcx = iplayer.x + player.width  * 0.5f;
                    float pcy = iplayer.y + player.height * 0.5f;
                    auto d2 = [&](const TestEnemy& te) {
                        return (pcx - te.x) * (pcx - te.x) + (pcy - te.y) * (pcy - te.y);
                    };
                    int hit = -1;
                    for (int i = 0; i < TEST_N && imap.id == 0; i++)   // the starting house only
                        if (d2(test_enemies[i]) < 22.0f * 22.0f) hit = i;
                    if (hit < 0) {
                        test_armed = true;
                    } else if (test_armed && post_battle_t <= 0.0f) {
                        test_armed = false;
                        int order[3] = { 0, 1, 2 };       // a pack is at most 3
                        int n = TEST_N < 3 ? TEST_N : 3;
                        for (int a = 0; a < n; a++)       // nearest first: the touched one leads
                            for (int b = a + 1; b < n; b++)
                                if (d2(test_enemies[order[b]]) < d2(test_enemies[order[a]]))
                                    { int t = order[a]; order[a] = order[b]; order[b] = t; }
                        for (int q = 0; q < n; q++) {
                            const TestEnemy& te = test_enemies[order[q]];
                            battle_queue[q]            = te.id;
                            battle_queue_chaser_idx[q] = -1;
                            flash_entries[q]           = { te.x, te.y };
                        }
                        battle_queue_count = flash_count = n;
                        battle_queue_idx   = 0;
                        pre_battle_timer   = 0.0f;
                    }
                }

                fc_draw_color(plat.renderer, 5, 5, 8, 255);
                SDL_RenderClear(plat.renderer);

                interior_draw(&imap, plat.renderer, tilemap_get_town_tex());

                // The raft book, until it is taken.
                int btx = 0, bty = 0;
                bool book_here = player.raft_book == 0 && interior_book_spot(imap.id, &btx, &bty);
                if (book_here)
                    game_menu_draw_item(&menu, plat.renderer, ITEM_RAFT_BOOK,
                                        btx * IMAP_TILE, bty * IMAP_TILE, IMAP_TILE);
                for (const TestEnemy& te : test_enemies) {
                    if (pre_battle_timer >= 0.0f || imap.id != 0) break;   // the flashes draw them; the starting house only
                    SDL_Rect cr = chaser_rect(&icam, te.x, te.y);
                    fc_draw_color(plat.renderer, 200, 30, 30, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    fc_draw_color(plat.renderer, 255, 80, 80, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                }
                player_draw(&player, iplayer.x, iplayer.y, &icam, plat.renderer, player_sprite);
                interior_draw_over_player(&imap, plat.renderer, iplayer.x, iplayer.y,
                                          (float)player.width, (float)player.height, iplayer.y + HB_Y2);
                battle_veil_draw(&icam);

                // Doormat — exit back to the overworld; ow.x/ow.y were never
                // touched, so the player reappears where they entered.
                if (iplayer.at_exit) {
                    draw_nes_panel(plat.renderer, 0, 457, 640, 23);
                    const char* lbl = "EXIT";
                    draw_text(plat.renderer, lbl,
                              (640 - text_width(lbl, 2)) / 2, 461, 2, 255, 255, 255);

                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        state = STATE_OVERWORLD;
                    }
                }

                // Standing by the book: take it. It teaches the raft, and
                // stays in ITEMS as what the raft needs.
                float fcx = iplayer.x + (HB_X1 + HB_X2) * 0.5f;
                float fcy = iplayer.y + (HB_Y1 + HB_Y2) * 0.5f;
                float bdx = fcx - (btx + 0.5f) * IMAP_TILE, bdy = fcy - (bty + 0.5f) * IMAP_TILE;
                if (book_here && !iplayer.at_exit && bdx * bdx + bdy * bdy < 40.0f * 40.0f) {
                    draw_nes_panel(plat.renderer, 0, 457, 640, 23);
                    const char* lbl = "TAKE BOOK";
                    draw_text(plat.renderer, lbl,
                              (640 - text_width(lbl, 2)) / 2, 461, 2, 255, 255, 255);
                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        player.raft_book = 1;
                        pickup_note   = "GOT RAFT BOOK";
                        pickup_note_t = 2.0f;
                        input_consume(&in, SDL_SCANCODE_Z);
                        input_consume(&in, SDL_SCANCODE_RETURN);
                        input_consume(&in, SDL_SCANCODE_SPACE);
                    }
                }

                if (!dbg_open && !menu.open && input_pressed(&in, SDL_SCANCODE_ESCAPE))
                    state = STATE_OVERWORLD;
                break;
            }
        }

        // The answer to a pickup, at the foot of the screen, a moment.
        if (pickup_note_t > 0.0f) {
            pickup_note_t -= dt;
            draw_nes_panel(plat.renderer, 0, 457, 640, 23);
            draw_text(plat.renderer, pickup_note,
                      (640 - text_width(pickup_note, 2)) / 2, 461, 2, 255, 255, 80);
        }

        // A scene change consumes the key that caused it. The prompts confirm on
        // input_pressed, but the overworld tool swings on input_down, so without
        // this the key is still held on the next frame and the press that walked
        // you out of a dungeon or closed a battle also swings at whatever
        // resource happens to be standing next to the door.
        if (state != state_before) {
            input_consume(&in, SDL_SCANCODE_RETURN);
            input_consume(&in, SDL_SCANCODE_Z);
            input_consume(&in, SDL_SCANCODE_SPACE);
        }

        // ── Top HUD bar, every state ──────────────────────────────────────────
        // Left: health, the stamina meter (the weapon refilling after an
        // attack) and EXP. Right: the enemy's name and health in battle, the
        // zoom slider everywhere else. Drawn last, so it stays up through the
        // battle transitions too.
        {
            float hp = (float)player.stats.hp, max_hp = (float)player.stats.max_hp;
            float stamina = 1.0f;
            const Enemy* foe = nullptr;
            const WeaponSwingState* sw = state == STATE_OVERWORLD ? &ow.swing
                                       : state == STATE_DUNGEON   ? &dplayer.swing : nullptr;
            if (state == STATE_BATTLE && battle_scene) {
                hp      = battle_scene->hud_hp();
                max_hp  = battle_scene->hud_max_hp();
                stamina = battle_scene->hud_stamina();
                foe     = battle_scene->hud_enemy();
            } else if (sw) {
                float cd = weapon_cooldown_seconds(equipped_weapon(&player));
                stamina = cd > 0.0f ? 1.0f - sw->tool_cd / cd : 1.0f;
            }
            if (stamina < 0.0f) stamina = 0.0f;
            if (stamina > 1.0f) stamina = 1.0f;

            fc_draw_color(plat.renderer, 0, 0, 0, 255);
            SDL_Rect hud_bg = {0, 0, 640, ARENA_TOP};
            SDL_RenderFillRect(plat.renderer, &hud_bg);

            draw_text(plat.renderer, "HP", NES_PAD + 2, 7, 1, 255, 255, 255);
            // Health in segments, Zelda II style: one per HP_PER_BAR, green
            // while held, black once lost, in a white box.
            {
                int bars = (int)max_hp / HP_PER_BAR;
                int full = (int)ceilf(hp / HP_PER_BAR);
                fc_draw_color(plat.renderer, 255, 255, 255, 255);
                SDL_Rect box = { 27, 5, bars * 9 + 3, 10 };
                SDL_RenderDrawRect(plat.renderer, &box);
                for (int b = 0; b < bars; b++) {
                    if (b < full) fc_draw_color(plat.renderer, 78, 220, 74, 255);
                    else          fc_draw_color(plat.renderer, 0, 0, 0, 255);
                    SDL_Rect seg = { 29 + b * 9, 7, 8, 6 };
                    SDL_RenderFillRect(plat.renderer, &seg);
                }
            }
            draw_bar(plat.renderer, 28, 17, 110, 5, stamina, 1.0f, 255, 220, 0);
            char buf[24];
            // Level and EXP, just right of the HP box (it grows a bar a level).
            // In battle the score climbs live with this fight's hits and
            // grazes; levels are only applied when the fight is won.
            int exp_shown = player.stats.exp + ((state == STATE_BATTLE && battle_scene) ? battle_scene->hud_exp() : 0);
            SDL_snprintf(buf, sizeof(buf), "LV%d EXP:%d", player.level, exp_shown);
            draw_text(plat.renderer, buf, 27 + ((int)max_hp / HP_PER_BAR) * 9 + 12, 10, 1, 255, 255, 255);

            // The weapon in hand, in the item menu's own box and pictures: a
            // textbox hanging from the bar, the icon at 2x with ore and name
            // beside it as the menu writes them, and -- with more than one
            // owned -- the previous and next, dimmed, with the keys that reach
            // them in the menu's grey hint style. The outline blinks the menu's
            // selection yellow for a moment after a swap. Shown only then:
            // up for WEAPON_BOX_T after a swap (Q / E), then gone.
            const float WEAPON_BOX_T = 1.5f;
            float swap_t = (state == STATE_BATTLE && battle_scene) ? battle_scene->hud_swap_t() : ow_swap_t;
            if (swap_t < WEAPON_BOX_T) {
                const int WX = 245, WY = 2, WW = 150, WH = 40;
                const Weapon& eq = equipped_weapon(&player);
                draw_nes_panel(plat.renderer, WX, WY, WW, WH);
                if (swap_t < 0.3f && (int)(swap_t * 20.0f) % 2 == 0) {
                    fc_draw_color(plat.renderer, 255, 255, 80, 255);
                    for (int t = 0; t < 4; t++) {
                        SDL_Rect r = { WX + t, WY + t, WW - 2 * t, WH - 2 * t };
                        SDL_RenderDrawRect(plat.renderer, &r);
                    }
                }
                game_menu_draw_weapon(&menu, plat.renderer, eq.type, eq.material, WX + 6, WY + 4, 32);
                draw_text(plat.renderer, weapon_name(eq.type), WX + 44, WY + 10, 1, 252, 252, 252);
                draw_text(plat.renderer, game_menu_ore_name(eq.material), WX + 44, WY + 22, 1, 120, 120, 120);

                int owned_n = 0;
                for (int w = 0; w < WEAPON_COUNT; w++) owned_n += player.owned[w];
                if (owned_n > 1) {
                    int pw = owned_neighbour(&player, -1), nw = owned_neighbour(&player, 1);
                    game_menu_draw_weapon(&menu, plat.renderer, (WeaponType)pw, player.arsenal[pw].material,
                                          WX - 20, WY + 6, 16, 110);
                    game_menu_draw_weapon(&menu, plat.renderer, (WeaponType)nw, player.arsenal[nw].material,
                                          WX + WW + 4, WY + 6, 16, 110);
                    draw_text(plat.renderer, "Q", WX - 16, WY + 26, 1, 120, 120, 120);
                    draw_text(plat.renderer, "E", WX + WW + 8, WY + 26, 1, 120, 120, 120);
                }
            }

            if (state == STATE_BATTLE) {
                if (foe) {
                    const char* nm = foe->name();
                    draw_text(plat.renderer, nm, 600 - text_width(nm, 1), 3, 1, 220, 220, 220);
                    draw_bar(plat.renderer, 420, 14, 180, 8, foe->hp, foe->max_hp, 220, 60, 60);
                }
            } else if (state == STATE_DUNGEON && dmap.type == DUNGEON_ENT_OASIS) {
                // In the oasis the zoom is held, and its air goes where the slider was
                dungeon_draw_oxygen(plat.renderer, oxygen, 452, 6);
            } else {
                // Zoom slider
                const int SL_W  = 120;
                const int SL_X  = 480 - SL_W / 2 + 40;
                const int TRK_Y = 12;
                const int TRK_H = 3;

                fc_draw_color(plat.renderer, 80, 80, 80, 255);
                SDL_Rect track = { SL_X, TRK_Y, SL_W, TRK_H };
                SDL_RenderFillRect(plat.renderer, &track);

                int hx = SL_X + zoom_idx * SL_W / (zoom_count - 1);
                fc_draw_color(plat.renderer, 255, 255, 255, 255);
                SDL_Rect fill = { SL_X, TRK_Y, hx - SL_X, TRK_H };
                SDL_RenderFillRect(plat.renderer, &fill);

                for (int i = 0; i < zoom_count; i++) {
                    int tx = SL_X + i * SL_W / (zoom_count - 1);
                    fc_draw_color(plat.renderer, 180, 180, 180, 255);
                    SDL_Rect tick = { tx - 1, TRK_Y - 2, 2, TRK_H + 4 };
                    SDL_RenderFillRect(plat.renderer, &tick);
                }

                fc_draw_color(plat.renderer, 255, 255, 255, 255);
                SDL_Rect knob = { hx - 3, 5, 6, 18 };
                SDL_RenderFillRect(plat.renderer, &knob);
                fc_draw_color(plat.renderer, 0, 0, 0, 255);
                SDL_Rect knob_inner = { hx - 1, 7, 2, 14 };
                SDL_RenderFillRect(plat.renderer, &knob_inner);
            }
        }

        // ── Crafting menu overlay ─────────────────────────────────────────────
        // ── The TAB menu (src/game_menu.cpp) ─────────────────────────────────
        if (state != STATE_BATTLE) game_menu_draw(&menu, &player, plat.renderer);

        // ── Debug menu overlay ───────────────────────────────────────────────
        if (dbg_open) {
            // Two columns, world and player, each under its heading. The rows
            // are in the small font (8px a character): the longest, the seam
            // row, is 32 characters, 256px, inside a 270px column.
            const int MX = 50, MY = 110, MW = 540, MH = 230;
            const int LH = 20;  // line height
            const int COL_W = 270;

            draw_nes_panel(plat.renderer, MX, MY, MW, MH);

            draw_text(plat.renderer, "DEBUG MENU", MX + NES_PAD + 2, MY + NES_PAD + 4, 2, 255, 255, 255);

            // A column's heading, then its rows; a row goes where DBG_ORDER puts it.
            draw_text(plat.renderer, "WORLD",  MX + 8,         MY + 36, 2, 120, 120, 120);
            draw_text(plat.renderer, "PLAYER", MX + 8 + COL_W, MY + 36, 2, 120, 120, 120);
            auto draw_row = [&](int row, const char* label, bool selected) {
                int pos = dbg_pos(row), right = pos >= DBG_PLAYER_AT;
                int rx  = MX + right * COL_W;
                int ry  = MY + 36 + LH + 6 + (pos - right * DBG_PLAYER_AT) * LH;
                Uint8 r = selected ? 255 : 180;
                Uint8 g = selected ? 255 : 180;
                Uint8 b = selected ? 80  : 180;
                if (selected)
                    draw_text(plat.renderer, ">", rx + 10, ry, 1, r, g, b);
                draw_text(plat.renderer, label, rx + 20, ry, 1, r, g, b);
            };

            // Row 0: warp target selector
            {
                char name[48], full[80];
                dbg_target_name(dbg_target, name, sizeof(name));
                SDL_snprintf(full, sizeof(full), "WARP: < %s >", name);
                draw_row(0, full, dbg_sel == 0);
            }

            // Row 1: the tour. Before the first press it reads how many of the
            // target this world holds -- a target as narrow as one ore band can
            // legitimately have none, and without that an empty result is
            // indistinguishable from a dead key. Once touring it reads which of
            // them you are standing outside, so you know when you have been
            // round them all.
            {
                char buf[48];
                int  n = dbg_target_list(dbg_target, dbg_list, MAX_DUNGEON_ENTRANCES);
                if (n <= 0)
                    SDL_snprintf(buf, sizeof(buf), "ENTER DUNGEON: NONE FOUND");
                else if (dbg_tour < 0)
                    SDL_snprintf(buf, sizeof(buf), "ENTER DUNGEON: %d FOUND", n);
                else
                    SDL_snprintf(buf, sizeof(buf), "ENTER DUNGEON: %d OF %d",
                                 (dbg_tour % n) + 1, n);
                draw_row(1, buf, dbg_sel == 1);
            }

            draw_row(2, "REGEN MAP", dbg_sel == 2);

            // Row 3: noclip toggle
            {
                const char* nc = dbg_noclip ? "NOCLIP: ON " : "NOCLIP: OFF";
                draw_row(3, nc, dbg_sel == 3);
            }

            // Row 4: show all tiles toggle
            {
                const char* sa = dbg_show_all ? "SHOW ALL: ON " : "SHOW ALL: OFF";
                draw_row(4, sa, dbg_sel == 4);
            }

            // Row 5: equipped weapon selector
            {
                char wbuf[64];
                SDL_snprintf(wbuf, sizeof(wbuf), "WEAPON: < %s >",
                             weapon_name(equipped_weapon(&player).type));
                draw_row(5, wbuf, dbg_sel == 5);
            }

            // Row 6: tile-grid overlay toggle
            {
                const char* gr = dbg_grid ? "GRID: ON " : "GRID: OFF";
                draw_row(6, gr, dbg_sel == 6);
            }

            // Row 7: warp to the seam, and which way the world wraps
            {
                static const char* SIDE[4] = { "W", "E", "N", "S" };
                char sb[64];
                SDL_snprintf(sb, sizeof(sb), "WARP TO SEAM (OCEAN %s, WRAP %s)",
                             SIDE[map->ocean_side & 3],
                             map->wrap_axis == WRAP_X ? "E-W" : "N-S");
                draw_row(7, sb, dbg_sel == 7);
            }

            // Row 8: what the equipped weapon is made of
            {
                char obuf[64];
                SDL_snprintf(obuf, sizeof(obuf), "ORE: < %s >",
                             material_name(equipped_weapon(&player).material));
                SDL_strupr(obuf);   // the menu font has capitals only
                draw_row(8, obuf, dbg_sel == 8);
            }

            // Row 9: give all
            draw_row(9, "GIVE ALL", dbg_sel == 9);
            draw_row(10, "MAX OUT WEAPONS", dbg_sel == 10);

            draw_text(plat.renderer, "WASD:MOVE  Q/E:CHANGE  Z:SELECT  F2:CLOSE",
                      MX + 6, MY + MH - 16, 1, 180, 180, 180);
        }

        // ── Battle test list overlay ──────────────────────────────────────────
        if (battle_list_open) {
            static const int VIEW = 10;
            const int PW = 360, PH = 46 + VIEW * 18 + 18;
            const int PX = (640 - PW) / 2, PY = (480 - PH) / 2;

            draw_nes_panel(plat.renderer, PX, PY, PW, PH);
            draw_text(plat.renderer, "BATTLE TEST",
                      PX + (PW - text_width("BATTLE TEST", 2)) / 2,
                      PY + NES_PAD + 4, 2, 255, 255, 255);

            // The search line, then the filtered list -- all ENEMY_COUNT of
            // them with nothing typed.
            char qline[40];
            SDL_snprintf(qline, sizeof(qline), "FIND:%s_", battle_query);
            draw_text(plat.renderer, qline, PX + 8, PY + 32, 1, 255, 255, 80);

            int top = battle_list_sel - VIEW / 2;
            if (top > battle_n - VIEW) top = battle_n - VIEW;
            if (top < 0)               top = 0;

            for (int i = 0; i < VIEW; i++) {
                int li = top + i;
                if (li >= battle_n) break;
                int idx = battle_hits[li];
                bool sel = (li == battle_list_sel);
                int ry = PY + 46 + i * 18;
                Uint8 cr = sel ? 255 : 180, cg = sel ? 255 : 180, cb = sel ? 80 : 180;
                if (sel) draw_text(plat.renderer, ">", PX + 8, ry, 2, cr, cg, cb);
                char label[40];
                SDL_snprintf(label, sizeof(label), "%02d  %s", idx, ENEMY_NAMES[idx]);
                draw_text(plat.renderer, label, PX + 24, ry, 2, cr, cg, cb);
            }
            if (battle_n == 0)
                draw_text(plat.renderer, "NO MATCH", PX + 24, PY + 46, 2, 180, 180, 180);

            draw_text(plat.renderer, "TYPE:FIND  UP/DN:SELECT  ENTER:FIGHT  ESC:CLEAR  F3:CLOSE",
                      PX + 6, PY + PH - 14, 1, 180, 180, 180);
        }

        if (dbg_readout) {
            float dbg_px = (state == STATE_DUNGEON) ? dplayer.x : ow.x;
            float dbg_py = (state == STATE_DUNGEON) ? dplayer.y : ow.y;
            draw_fps(plat.renderer, dt, dbg_px, dbg_py);
        }

        if (esc_hold_time > 0.f) {
            const int BAR_W = 80;
            const int BAR_H = 6;
            const int BX = 4, BY = 34;
            draw_text(plat.renderer, "HOLD ESC TO QUIT", BX, BY - 12, 1, 255, 255, 80);
            fc_draw_color(plat.renderer, 60, 60, 60, 255);
            SDL_Rect track = { BX, BY, BAR_W, BAR_H };
            SDL_RenderFillRect(plat.renderer, &track);
            int fill_w = (int)(esc_hold_time / 3.f * BAR_W);
            if (fill_w > BAR_W) fill_w = BAR_W;
            fc_draw_color(plat.renderer, 255, 80, 80, 255);
            SDL_Rect fill = { BX, BY, fill_w, BAR_H };
            SDL_RenderFillRect(plat.renderer, &fill);
        }

        // The one place the window scale is applied. RenderClear ignores the
        // viewport, so this paints the letterbox bars as well.
        if (frame_tex) {
            SDL_SetRenderTarget(plat.renderer, NULL);
            SDL_RenderSetLogicalSize(plat.renderer, LOGICAL_W, LOGICAL_H);
            fc_draw_color(plat.renderer, 10, 10, 20, 255);
            SDL_RenderClear(plat.renderer);
            SDL_RenderCopy(plat.renderer, frame_tex, NULL, NULL);
        }
        SDL_RenderPresent(plat.renderer);

        // Precise frame cap: sleep most of the wait, spin the last ~1 ms
        {
            Uint64 now = SDL_GetPerformanceCounter();
            if (now < frame_deadline) {
                Uint32 sleep_ms = (Uint32)((frame_deadline - now) * 1000 / PERF_FREQ);
                if (sleep_ms > 1) SDL_Delay(sleep_ms - 1);
                while (SDL_GetPerformanceCounter() < frame_deadline) {}
            }
            frame_deadline += FRAME_TICKS; // next frame target (self-correcting)
        }
    }

    tilemap_cancel_gen();
    game_menu_free(&menu);
    gen_thread.join();
    delete battle_scene;
    delete map;

    //cleanups textures
    SDL_DestroyTexture(player_sprite);
    player_sprite = NULL;

    if (frame_tex) SDL_DestroyTexture(frame_tex);
    frame_tex = NULL;

    tilemap_free_tile_cache();
    IMG_Quit();
    platform_shutdown(&plat);

    return 0;
}
