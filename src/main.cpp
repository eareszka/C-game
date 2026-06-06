#include <stdio.h>
#include <thread>
#include <unordered_map>
#include <vector>
#include <SDL2/SDL_image.h>

#include "game_state.h"
#include "battle.h"
#include "dungeon.h"
#include "platform.h"
#include "core.h"
#include "input.h"
#include "overworld.h"
#include "camera.h"
#include "tilemap.h"
#include "resource_node.h"


int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    Platform plat;
    if (!platform_init(&plat, "Four Castle Chronicles", 640, 480)) {
        return 1;
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(plat.renderer, 640, 480);

    if (!(IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG)) 
    {
        printf("SDL_image init failed: %s\n", IMG_GetError());
        platform_shutdown(&plat);
        return 1;
    }

    tilemap_init_tile_cache(plat.renderer);

    SDL_Texture* player_sprite = IMG_LoadTexture(plat.renderer, "assets/Sprite-0001.png");
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
    GameState    state_after_battle = STATE_OVERWORLD;
    int          battle_queue[3]             = {};
    int          battle_queue_chaser_idx[3] = { -1, -1, -1 };
    int          battle_queue_count = 0;
    int          battle_queue_idx   = 0;
    struct FlashEntry { float x, y; };
    FlashEntry   flash_entries[3]   = {};
    int          flash_count        = 0;
    float        pre_battle_timer   = -1.0f;  // -1 = inactive

    // Floating +N resource text — one active at a time above the last hit node
    struct FloatText { float wx, wy, drift, life; char text[8]; Uint8 r, g, b; bool active; int count; };
    FloatText cur_float = {};
    auto spawn_float = [&](float wx, float wy, Uint8 r, Uint8 g, Uint8 b) {
        if (cur_float.active && fabsf(cur_float.wx - wx) < 2.0f && fabsf(cur_float.wy - wy) < 2.0f) {
            cur_float.count++;
            cur_float.life = 1.0f;
            cur_float.drift = 0.0f;
        } else {
            cur_float = {};
            cur_float.wx = wx; cur_float.wy = wy;
            cur_float.life = 1.0f; cur_float.active = true; cur_float.count = 1;
            cur_float.r = r; cur_float.g = g; cur_float.b = b;
        }
        SDL_snprintf(cur_float.text, sizeof(cur_float.text), "+%d", cur_float.count);
    };

    Overworld ow;

    float start_x = 47916.0f;
    float start_y = 46464.0f;
    overworld_init(&ow, &player, start_x, start_y);

    Tilemap* map = new Tilemap();
    unsigned int map_seed = (unsigned int)SDL_GetTicks();
    tilemap_build_overworld_phase1(map, map_seed);
    std::thread gen_thread(tilemap_build_overworld_phase2, map, map_seed);

    //initializes resources
    ResourceNodeList resources;
    resource_nodes_init(&resources);

    resource_nodes_add(&resources, RESOURCE_FLOWER, 320, 224);


    Input in = {0};

    // Zoom levels where TILE_SIZE(32) * zoom is always a whole number of pixels
    static const float zoom_levels[] = { 0.25f, 0.5f, 0.75f, 1.0f, 1.5f, 2.0f, 3.0f };
    static const int   zoom_count    = (int)(sizeof(zoom_levels) / sizeof(zoom_levels[0]));
    int zoom_idx = 3; // default: 1.0x

    Camera cam = {0};
    cam.screen_w = 640;
    cam.screen_h = 480;
    cam.zoom = zoom_levels[zoom_idx];

    bool running = true;

    // ── Debug menu ───────────────────────────────────────────────────────────
    static const char* DBG_TYPE_NAMES[] = {
        "CAVE", "RUINS", "GRAVEYARD", "GRAVEYARD LG",
        "OASIS", "PYRAMID", "STONEHENGE", "LARGE TREE"
    };
    static const int DBG_TYPE_COUNT = 8;

    bool dbg_open     = false;
    int  dbg_sel      = 0;   // 0=type, 1=enter, 2=regen, 3=noclip, 4=show all
    int  dbg_type     = 0;
    bool dbg_noclip   = false;
    bool dbg_show_all = false;
    bool crafting_open    = false;
    bool map_open         = false;
    bool battle_list_open = false;
    int  battle_list_sel  = 0;

    static const char* ENEMY_NAMES[50] = {
        "CAVE BAT", "CAVE SLIME", "CAVE SPIDER", "CAVE TROLL", "CAVE WORM", "CAVE MUSHROOM",
        "RUINS GUARD", "RUINS ARCHER", "RUINS GOLEM", "RUINS GHOST", "RUINS WISP", "RUINS COLOSSUS",
        "ZOMBIE", "WRAITH", "SKELETON", "GHOUL", "BANSHEE", "LICH",
        "GRAVE KNIGHT", "REVENANT", "DEMON", "NECROMANCER", "VAMPIRE", "GRAVE LORD",
        "SERPENT", "SCORPION", "MIRAGE", "SANDWORM", "DJINN", "CROCODILE",
        "MUMMY", "SCARAB", "ANUBIS", "BASTET", "SPHINX", "PHARAOH",
        "ANCIENT", "DRUID", "WARDEN", "OBSERVER", "ORACLE", "ELDER",
        "TREE SPRITE", "ENTWINE", "DRYAD", "WISP", "GUARDIAN", "TREE ANCIENT",
        "BANDIT", "DRAGON",
    };

    DungeonMap    dmap    = {};
    DungeonPlayer dplayer = {};

    struct DungeonChaser { float x, y; int enemy_id; bool active; bool chasing; float aggro_timer; };
    static const int MAX_CHASERS = 32;
    DungeonChaser chasers[MAX_CHASERS] = {};
    int num_chasers = 0;

    std::unordered_map<uint32_t, std::vector<uint8_t>> dungeon_explored_cache;
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

    while (running)
    {
        double dt_d = time_delta_seconds();
        if (dt_d > 0.05) dt_d = 0.05; // cap at 50 ms — prevents big jumps on stalled frames
        float dt = (float)dt_d;
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
            if (input_pressed(&in, SDL_SCANCODE_UP))
                dbg_sel = (dbg_sel + 4) % 5;
            if (input_pressed(&in, SDL_SCANCODE_DOWN))
                dbg_sel = (dbg_sel + 1) % 5;

            if (dbg_sel == 0) {
                if (input_pressed(&in, SDL_SCANCODE_LEFT))
                    dbg_type = (dbg_type + DBG_TYPE_COUNT - 1) % DBG_TYPE_COUNT;
                if (input_pressed(&in, SDL_SCANCODE_RIGHT))
                    dbg_type = (dbg_type + 1) % DBG_TYPE_COUNT;
            }

            bool dbg_confirm = input_pressed(&in, SDL_SCANCODE_RETURN) ||
                               input_pressed(&in, SDL_SCANCODE_Z);

            if (dbg_sel == 1 && dbg_confirm) {
                // Teleport to the nearest overworld entrance of the selected type
                for (int ei = 0; ei < map->num_dungeon_entrances; ei++) {
                    const DungeonEntrance* e = &map->dungeon_entrances[ei];
                    if ((int)e->type == dbg_type) {
                        ow.x = (float)(e->x * TILE_SIZE);
                        ow.y = (float)(e->y * TILE_SIZE);
                        state = STATE_OVERWORLD;
                        break;
                    }
                }
                dbg_open = false;
            }

            if (dbg_sel == 2 && dbg_confirm) {
                // Regenerate the entire overworld with a new seed
                tilemap_cancel_gen();
                gen_thread.join();
                tilemap_reset_gen_cancel();
                map_seed = (unsigned int)SDL_GetTicks();
                delete map;
                map = new Tilemap();
                tilemap_build_overworld_phase1(map, map_seed);
                gen_thread = std::thread(tilemap_build_overworld_phase2, map, map_seed);
                resource_nodes_init(&resources);
                ow.x = (MAP_WIDTH  / 2.0f) * TILE_SIZE;
                ow.y = (MAP_HEIGHT / 2.0f) * TILE_SIZE;
                state    = STATE_OVERWORLD;
                dbg_open = false;
            }

            if (dbg_sel == 3 && dbg_confirm)
                dbg_noclip = !dbg_noclip;

            if (dbg_sel == 4 && dbg_confirm)
                dbg_show_all = !dbg_show_all;

            if (input_pressed(&in, SDL_SCANCODE_ESCAPE))
                dbg_open = false;
        }

        // ── Battle test list (F3) ─────────────────────────────────────────────
        if (input_pressed(&in, SDL_SCANCODE_F3) && !dbg_open && state != STATE_BATTLE)
            battle_list_open = !battle_list_open;

        if (battle_list_open) {
            if (input_pressed(&in, SDL_SCANCODE_UP))
                battle_list_sel = (battle_list_sel + 49) % 50;
            if (input_pressed(&in, SDL_SCANCODE_DOWN))
                battle_list_sel = (battle_list_sel + 1) % 50;
            if (input_pressed(&in, SDL_SCANCODE_RETURN) ||
                input_pressed(&in, SDL_SCANCODE_Z)) {
                delete battle_scene;
                battle_scene = new BattleScene(&player, battle_list_sel, WEAPON_DAGGER);
                state = STATE_BATTLE;
                battle_list_open = false;
            }
            if (input_pressed(&in, SDL_SCANCODE_ESCAPE))
                battle_list_open = false;
        }

        // Blank input fed to game logic while menu is open so the player stands still.
        Input in_blank = {0};
        const Input* game_in = (dbg_open || crafting_open || map_open || battle_list_open)
                                ? &in_blank : &in;

        if (input_pressed(&in, SDL_SCANCODE_B) && !dbg_open && state != STATE_BATTLE) {
            delete battle_scene;
            battle_scene = new BattleScene(&player, 0, WEAPON_DAGGER);
            state = STATE_BATTLE;
        }

        // Mouse wheel steps through pixel-perfect zoom levels
        // scroll up (+y) = zoom in = higher index; scroll down = zoom out = lower index
        if (in.mouse_wheel != 0 && state != STATE_BATTLE) {
            zoom_idx += in.mouse_wheel;
            if (zoom_idx < 0)           zoom_idx = 0;
            if (zoom_idx >= zoom_count) zoom_idx = zoom_count - 1;
            cam.zoom = zoom_levels[zoom_idx];
        }

        switch (state) {
            case STATE_TITLE:
                SDL_SetRenderDrawColor(plat.renderer, 0, 0, 0, 255);
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
                        if (e->type != DUNGEON_ENT_GRAVEYARD_SM &&
                            e->type != DUNGEON_ENT_GRAVEYARD_LG) continue;
                        if (e->gravestones_spawned) continue;
                        float ex = (float)(e->x * TILE_SIZE + TILE_SIZE / 2);
                        float ey = (float)(e->y * TILE_SIZE + TILE_SIZE / 2);
                        float ddx = px - ex, ddy = py - ey;
                        if (ddx*ddx + ddy*ddy < SPAWN_RANGE * SPAWN_RANGE) {
                            if (e->type == DUNGEON_ENT_GRAVEYARD_SM)
                                tilemap_spawn_graveyard_nodes(map, &resources, i, map_seed);
                            else
                                tilemap_spawn_graveyard_lg_nodes(map, &resources, i, map_seed);
                        }
                    }
                }

                int resource_hit = -1;
                float hit_wx = 0, hit_wy = 0;
                overworld_update(&ow, &player, game_in, dt, &resources, map, dbg_noclip, &resource_hit, &hit_wx, &hit_wy);
                if (resource_hit >= 0) {
                    Uint8 fr = 180, fg = 120, fb = 60;
                    if      (resource_hit == (int)RESOURCE_ROCK) { fr = 160; fg = 160; fb = 160; }
                    else if (resource_hit == (int)RESOURCE_GOLD) { fr = 255; fg = 210; fb =  40; }
                    spawn_float(hit_wx, hit_wy, fr, fg, fb);
                }

                float player_cx = ow.x + player.width * 0.5f;
                float player_cy = ow.y + player.height * 0.5f;
                camera_center_on(&cam, player_cx, player_cy);

                SDL_SetRenderDrawColor(plat.renderer, 10, 10, 20, 255);
                SDL_RenderClear(plat.renderer);
                

                tilemap_draw_base(map, &cam, plat.renderer);
                resource_nodes_draw(&resources, &cam, plat.renderer, tilemap_get_town_tex());
                player_draw(&player, ow.x, ow.y, &cam, plat.renderer, player_sprite);
                tilemap_draw_depth(map, &cam, plat.renderer);

                // --- Weapon cooldown bar ---
                {
                    float max_cd = 1.0f / weapon_profile(player.equipped_weapon).fire_rate;
                    float ready  = 1.0f - (ow.tool_cd > 0.0f ? ow.tool_cd / max_cd : 0.0f);
                    const int BAR_W = 160, BAR_H = 5;
                    const int BAR_X = (640 - BAR_W) / 2, BAR_Y = 480 - 12;
                    SDL_SetRenderDrawColor(plat.renderer, 40, 40, 40, 200);
                    SDL_Rect track = { BAR_X, BAR_Y, BAR_W, BAR_H };
                    SDL_RenderFillRect(plat.renderer, &track);
                    SDL_SetRenderDrawColor(plat.renderer, 255, 220, 0, 255);
                    SDL_Rect fill = { BAR_X, BAR_Y, (int)(BAR_W * ready), BAR_H };
                    SDL_RenderFillRect(plat.renderer, &fill);
                }

                // --- Floating resource text ---
                if (cur_float.active) {
                    cur_float.drift += 60.0f * dt;
                    cur_float.life  -= dt;
                    if (cur_float.life <= 0.0f) {
                        cur_float.active = false;
                    } else {
                        int sx = (int)((cur_float.wx - cam.x) * cam.zoom);
                        int sy = (int)((cur_float.wy - cam.y) * cam.zoom) - (int)cur_float.drift;
                        sx -= text_width(cur_float.text, 1) / 2;
                        float a = cur_float.life;
                        draw_text(plat.renderer, cur_float.text, sx, sy, 1,
                                  (Uint8)(cur_float.r * a), (Uint8)(cur_float.g * a), (Uint8)(cur_float.b * a));
                    }
                }


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
                    };
                    int ci = (int)ow.dungeon_type;
                    if (ci < 0 || ci > 7) ci = 0;
                    const char* name = dungeon_names[ci];

                    draw_nes_panel(plat.renderer, 0, 448, 640, 32);

                    int nx = (640 - text_width(name, 2)) / 2;
                    draw_text(plat.renderer, name, nx, 456, 2, 255, 255, 255);

                    // difficulty bar inside inner border
                    SDL_SetRenderDrawColor(plat.renderer, 40, 40, 40, 255);
                    SDL_Rect diff_track = {NES_PAD + 2, 472, 640 - (NES_PAD+2)*2, 4};
                    SDL_RenderFillRect(plat.renderer, &diff_track);
                    SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
                    SDL_Rect diff_fill = {NES_PAD + 2, 472, (int)((640 - (NES_PAD+2)*2) * ow.dungeon_difficulty), 4};
                    SDL_RenderFillRect(plat.renderer, &diff_fill);

                    if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                        input_pressed(game_in, SDL_SCANCODE_Z)      ||
                        input_pressed(game_in, SDL_SCANCODE_SPACE)) {
                        int etx = (int)((ow.x + player.width  * 0.5f) / TILE_SIZE);
                        int ety = (int)((ow.y + player.height - 8.0f) / TILE_SIZE);

                        unsigned int dng_seed = map_seed
                            ^ ((unsigned int)etx * 73856093u)
                            ^ ((unsigned int)ety * 19349663u);

                        // Default: solo dungeon — both portals return to this entrance.
                        dng_entry_portal_x = etx; dng_entry_portal_y = ety;
                        dng_exit_portal_x  = etx; dng_exit_portal_y  = ety;
                        int from_exit = 0;
                        float connect_angle = NAN;

                        // Find the DungeonEntrance record we're standing on.
                        DungeonEntrance* cur_ent = nullptr;
                        for (int ci = 0; ci < map->num_dungeon_entrances; ci++) {
                            DungeonEntrance* ce = &map->dungeon_entrances[ci];
                            int stamp = (ce->size == 0) ? 1 : 2;
                            if (etx >= ce->x && etx < ce->x + stamp &&
                                ety >= ce->y && ety < ce->y + stamp) {
                                cur_ent = ce; break;
                            }
                        }

                        // For solo entrances, anchor the seed to the entrance's
                        // canonical top-left so any tile of a 2×2 stamp gives
                        // the same layout every visit.
                        if (cur_ent && cur_ent->partner_idx < 0) {
                            dng_seed = map_seed
                                ^ ((unsigned int)cur_ent->x * 73856093u)
                                ^ ((unsigned int)cur_ent->y * 19349663u);
                        }

                        // Fixed cave at tile (1498, 1572) — same layout every seed.
                        if (cur_ent && cur_ent->x == 1498 && cur_ent->y == 1572)
                            dng_seed = 0xCA4E5EEDu;

                        if (cur_ent && cur_ent->partner_idx >= 0) {
                            DungeonEntrance* partner = &map->dungeon_entrances[cur_ent->partner_idx];
                            int ax = cur_ent->x, ay = cur_ent->y;
                            int bx = partner->x, by = partner->y;

                            // Shared, order-independent seed.
                            int minx = ax < bx ? ax : bx, miny = ay < by ? ay : by;
                            int maxx = ax > bx ? ax : bx, maxy = ay > by ? ay : by;
                            dng_seed = map_seed
                                ^ ((unsigned int)minx * 73856093u)
                                ^ ((unsigned int)miny * 19349663u)
                                ^ ((unsigned int)maxx * 83492791u)
                                ^ ((unsigned int)maxy * 31729253u);

                            // Lexicographic order on stamp top-left: lower = DNG_ENTRY side.
                            bool we_are_primary = (ax < bx) || (ax == bx && ay < by);
                            if (we_are_primary) {
                                dng_entry_portal_x = ax;  dng_entry_portal_y = ay;
                                dng_exit_portal_x  = bx;  dng_exit_portal_y  = by;
                                from_exit     = 0;
                                connect_angle = atan2f((float)(by - ay), (float)(bx - ax));
                            } else {
                                dng_entry_portal_x = bx;  dng_entry_portal_y = by;
                                dng_exit_portal_x  = ax;  dng_exit_portal_y  = ay;
                                from_exit     = 1;
                                connect_angle = atan2f((float)(ay - by), (float)(ax - bx));
                            }
                        }

                        // SM connected to LG: generate at the larger scale.
                        DungeonEntranceType gen_type = ow.dungeon_type;
                        if (cur_ent && cur_ent->partner_idx >= 0) {
                            DungeonEntrance* partner2 = &map->dungeon_entrances[cur_ent->partner_idx];
                            if (gen_type == DUNGEON_ENT_GRAVEYARD_SM &&
                                partner2->type == DUNGEON_ENT_GRAVEYARD_LG)
                                gen_type = DUNGEON_ENT_GRAVEYARD_LG;
                        }
                        dungeon_generate(&dmap, gen_type,
                                         ow.dungeon_difficulty, dng_seed);
                        current_dng_seed = dng_seed;
                        {
                            auto exp_it = dungeon_explored_cache.find(current_dng_seed);
                            if (exp_it != dungeon_explored_cache.end())
                                SDL_memcpy(dmap.explored, exp_it->second.data(), DMAP_H * DMAP_W);
                        }

                        if (!isnan(connect_angle)) {
                            // Connected: orient portals so the underground direction
                            // matches the overworld direction between the two entrances.
                            dungeon_orient_portals(&dmap, connect_angle);
                        } else {
                            // Solo: remove the exit tile; the entry tile is the only way out.
                            dmap.tiles[dmap.exit_y][dmap.exit_x] = DNG_FLOOR;
                        }

                        dungeon_player_init(&dplayer, &player, &dmap, from_exit);
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
                    }
                }

                if (input_pressed(&in, SDL_SCANCODE_TAB) && !dbg_open)
                    crafting_open = !crafting_open;

                if (input_pressed(&in, SDL_SCANCODE_M) && !dbg_open)
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
                        if (input_pressed(game_in, SDL_SCANCODE_RETURN) ||
                            input_pressed(game_in, SDL_SCANCODE_Z)) {
                            bool victory = battle_scene->get_phase() == BATTLE_PHASE_VICTORY;
                            delete battle_scene;
                            battle_scene = nullptr;
                            if (victory && battle_queue_idx + 1 < battle_queue_count) {
                                battle_queue_idx++;
                                battle_scene = new BattleScene(&player, battle_queue[battle_queue_idx], WEAPON_DAGGER);
                            } else {
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
                if (pre_battle_timer < 0.0f)
                    dungeon_player_update(&dplayer, &player, game_in, dt, &dmap, dbg_noclip);

                float dpcx = dplayer.x + player.width  * 0.5f;
                float dpcy = dplayer.y + player.height * 0.5f;
                camera_center_on(&cam, dpcx, dpcy);

                // Pre-battle flash: each queued enemy flashes once in fight order,
                // then 0.5s pause before battle starts.
                static const float FLASH_STEP = 0.4f;  // total time per enemy
                static const float FLASH_ON   = 0.25f; // how long it's visible within that window
                if (pre_battle_timer >= 0.0f) {
                    pre_battle_timer += dt;
                    if (pre_battle_timer >= flash_count * FLASH_STEP + 0.5f) {
                        pre_battle_timer = -1.0f;
                        delete battle_scene;
                        battle_scene = new BattleScene(&player, battle_queue[0], WEAPON_DAGGER);
                        state_after_battle = STATE_DUNGEON;
                        state = STATE_BATTLE;
                    }
                } else {
                    // Update chasers — activate when seen, move toward player, queue on contact.
                    const float CHASER_SPEED  = 300.0f;
                    const float TRIGGER_DIST2 = 22.0f * 22.0f;
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

                            flash_count       = battle_queue_count;
                            pre_battle_timer  = 0.0f;
                            break;
                        }

                        float dist = sqrtf(dist2);
                        float nx = ch.x + (cdx / dist) * CHASER_SPEED * dt;
                        float ny = ch.y + (cdy / dist) * CHASER_SPEED * dt;
                        int ntx = (int)(nx / DMAP_TILE), nty = (int)(ny / DMAP_TILE);
                        if (ntx >= 0 && ntx < DMAP_W && nty >= 0 && nty < DMAP_H &&
                            dmap.tiles[nty][ntx] != DNG_WALL) {
                            ch.x = nx; ch.y = ny;
                        } else {
                            int ntx2 = (int)(nx / DMAP_TILE), nty2 = (int)(ch.y / DMAP_TILE);
                            if (ntx2 >= 0 && ntx2 < DMAP_W && nty2 >= 0 && nty2 < DMAP_H &&
                                dmap.tiles[nty2][ntx2] != DNG_WALL)
                                ch.x = nx;
                            int ntx3 = (int)(ch.x / DMAP_TILE), nty3 = (int)(ny / DMAP_TILE);
                            if (ntx3 >= 0 && ntx3 < DMAP_W && nty3 >= 0 && nty3 < DMAP_H &&
                                dmap.tiles[nty3][ntx3] != DNG_WALL)
                                ch.y = ny;
                        }
                    }
                }
                if (state == STATE_BATTLE) break;

                // Background matches wall colour so map edges blend in
                SDL_SetRenderDrawColor(plat.renderer, 5, 5, 8, 255);
                SDL_RenderClear(plat.renderer);

                dungeon_draw(&dmap, &dplayer, &cam, plat.renderer, dbg_show_all);
                player_draw(&player, dplayer.x, dplayer.y, &cam, plat.renderer, player_sprite);

                // Draw active chasers
                for (int ci = 0; ci < num_chasers; ci++) {
                    DungeonChaser& ch = chasers[ci];
                    if (!ch.active) continue;
                    int sz  = (int)(14 * cam.zoom);
                    int sx  = (int)((ch.x - cam.x) * cam.zoom) - sz / 2;
                    int sy  = (int)((ch.y - cam.y) * cam.zoom) - sz / 2;
                    SDL_Rect cr = { sx, sy, sz, sz };
                    SDL_SetRenderDrawColor(plat.renderer, 200, 30, 30, 255);
                    SDL_RenderFillRect(plat.renderer, &cr);
                    SDL_SetRenderDrawColor(plat.renderer, 255, 80, 80, 255);
                    SDL_RenderDrawRect(plat.renderer, &cr);
                }

                // Draw pre-battle flash: each enemy flashes once in fight order
                if (pre_battle_timer >= 0.0f) {
                    int cur_step = (int)(pre_battle_timer / FLASH_STEP);
                    float local_t = pre_battle_timer - cur_step * FLASH_STEP;
                    for (int fi = 0; fi < flash_count; fi++) {
                        int sz = (int)(14 * cam.zoom);
                        int sx = (int)((flash_entries[fi].x - cam.x) * cam.zoom) - sz / 2;
                        int sy = (int)((flash_entries[fi].y - cam.y) * cam.zoom) - sz / 2;
                        SDL_Rect cr = { sx, sy, sz, sz };
                        if (fi == cur_step && cur_step < flash_count && local_t < FLASH_ON) {
                            // Currently flashing — bright yellow
                            SDL_SetRenderDrawColor(plat.renderer, 255, 220, 50, 255);
                            SDL_RenderFillRect(plat.renderer, &cr);
                            SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
                            SDL_RenderDrawRect(plat.renderer, &cr);
                        } else if (fi > cur_step && cur_step < flash_count) {
                            // Not yet reached — shown dim
                            SDL_SetRenderDrawColor(plat.renderer, 80, 20, 20, 255);
                            SDL_RenderFillRect(plat.renderer, &cr);
                            SDL_SetRenderDrawColor(plat.renderer, 120, 40, 40, 255);
                            SDL_RenderDrawRect(plat.renderer, &cr);
                        }
                        // fi <= cur_step past FLASH_ON, or cur_step >= flash_count (pause): not drawn
                    }
                }

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
                        ow.x = (float)(dng_entry_portal_x * TILE_SIZE);
                        ow.y = (float)(dng_entry_portal_y * TILE_SIZE);
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
                        ow.x = (float)(dng_exit_portal_x * TILE_SIZE);
                        ow.y = (float)(dng_exit_portal_y * TILE_SIZE);
                        state = STATE_OVERWORLD;
                    }
                }

                if (input_pressed(&in, SDL_SCANCODE_TAB))
                    crafting_open = !crafting_open;

                if (input_pressed(&in, SDL_SCANCODE_M))
                    map_open = !map_open;

                if (map_open)
                    dungeon_minimap_draw(&dmap, &dplayer, plat.renderer, 640, 480, dbg_show_all);

                if (!dbg_open && input_pressed(&in, SDL_SCANCODE_ESCAPE)) {
                    dungeon_explored_cache[current_dng_seed].assign(
                        &dmap.explored[0][0], &dmap.explored[0][0] + DMAP_H * DMAP_W);
                    state = STATE_OVERWORLD;
                }
                break;
            }
        }

        // ── Resource bar (hidden during battle) ──────────────────────────────
        if (state != STATE_BATTLE) {
            static const int   res_idx[]    = { 0, 1, 3 };
            static const char* res_labels[] = { "WOOD", "STONE", "GOLD" };
            static const Uint8 res_r[] = {180, 160, 255};
            static const Uint8 res_g[] = {120, 160, 210};
            static const Uint8 res_b[] = { 60, 160,  40};

            SDL_SetRenderDrawColor(plat.renderer, 0, 0, 0, 255);
            SDL_Rect res_bg = {0, 0, 640, 28};
            SDL_RenderFillRect(plat.renderer, &res_bg);

            char buf[16];
            int cx = NES_PAD + 2;
            for (int ri = 0; ri < 3; ri++) {
                SDL_snprintf(buf, sizeof(buf), "%s:%d", res_labels[ri], player.inventory[res_idx[ri]]);
                draw_text(plat.renderer, buf, cx, 10, 1, res_r[ri], res_g[ri], res_b[ri]);
                cx += text_width(buf, 1) + 10;
            }

            SDL_snprintf(buf, sizeof(buf), "EXP:%d", player.stats.exp);
            int ew = text_width(buf, 1);
            draw_text(plat.renderer, buf, 640 - ew - NES_PAD - 2, 10, 1, 255, 255, 255);

            // Zoom slider — centered in bar
            {
                const int SL_W  = 120;
                const int SL_X  = (640 - SL_W) / 2;
                const int TRK_Y = 12;
                const int TRK_H = 3;

                SDL_SetRenderDrawColor(plat.renderer, 80, 80, 80, 255);
                SDL_Rect track = { SL_X, TRK_Y, SL_W, TRK_H };
                SDL_RenderFillRect(plat.renderer, &track);

                int hx = SL_X + zoom_idx * SL_W / (zoom_count - 1);
                SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
                SDL_Rect fill = { SL_X, TRK_Y, hx - SL_X, TRK_H };
                SDL_RenderFillRect(plat.renderer, &fill);

                for (int i = 0; i < zoom_count; i++) {
                    int tx = SL_X + i * SL_W / (zoom_count - 1);
                    SDL_SetRenderDrawColor(plat.renderer, 180, 180, 180, 255);
                    SDL_Rect tick = { tx - 1, TRK_Y - 2, 2, TRK_H + 4 };
                    SDL_RenderFillRect(plat.renderer, &tick);
                }

                SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
                SDL_Rect knob = { hx - 3, 5, 6, 18 };
                SDL_RenderFillRect(plat.renderer, &knob);
                SDL_SetRenderDrawColor(plat.renderer, 0, 0, 0, 255);
                SDL_Rect knob_inner = { hx - 1, 7, 2, 14 };
                SDL_RenderFillRect(plat.renderer, &knob_inner);
            }
        }

        // ── Crafting menu overlay ─────────────────────────────────────────────
        if (crafting_open && state != STATE_BATTLE) {
            const int PW = 460, PH = 180;
            const int PX = (640 - PW) / 2, PY = (480 - PH) / 2;

            draw_nes_panel(plat.renderer, PX, PY, PW, PH);

            draw_text(plat.renderer, "CRAFTING MENU",
                      PX + (PW - text_width("CRAFTING MENU", 2)) / 2, PY + NES_PAD + 4, 2, 255, 255, 255);

            SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
            SDL_Rect div1 = { PX + NES_PAD, PY + 36, PW - NES_PAD*2, 1 };
            SDL_RenderFillRect(plat.renderer, &div1);

            // ── Recipes row ───────────────────────────────────────────────────
            draw_text(plat.renderer, "RECIPES", PX + NES_PAD + 2, PY + 44, 1, 255, 255, 255);
            draw_text(plat.renderer, "COMING SOON...", PX + NES_PAD + 2, PY + 58, 1, 100, 100, 100);

            SDL_SetRenderDrawColor(plat.renderer, 255, 255, 255, 255);
            SDL_Rect div2 = { PX + NES_PAD, PY + 106, PW - NES_PAD*2, 1 };
            SDL_RenderFillRect(plat.renderer, &div2);

            // ── Collectibles row ──────────────────────────────────────────────
            draw_text(plat.renderer, "COLLECTIBLES", PX + NES_PAD + 2, PY + 114, 1, 255, 255, 255);
            {
                char buf[32];
                int rx = PX + NES_PAD + 2;
                SDL_snprintf(buf, sizeof(buf), "FLOWER: %d", player.inventory[2]);
                draw_text(plat.renderer, buf, rx, PY + 128, 1, 255, 180, 220);
                rx += text_width(buf, 1) + 16;
                SDL_snprintf(buf, sizeof(buf), "GRAVESTONE: %d", player.inventory[4]);
                draw_text(plat.renderer, buf, rx, PY + 128, 1, 160, 160, 180);
            }

            draw_text(plat.renderer, "[TAB] CLOSE",
                      PX + (PW - text_width("[TAB] CLOSE", 1)) / 2, PY + PH - 16, 1, 100, 100, 100);
        }

        // ── Debug menu overlay ───────────────────────────────────────────────
        if (dbg_open) {
            const int MX = 120, MY = 130, MW = 400, MH = 180;
            const int LH = 22;  // line height

            draw_nes_panel(plat.renderer, MX, MY, MW, MH);

            draw_text(plat.renderer, "DEBUG MENU", MX + NES_PAD + 2, MY + NES_PAD + 4, 2, 255, 255, 255);

            // Helper lambda: draw one menu row
            auto draw_row = [&](int row, const char* label, bool selected) {
                int ry = MY + 36 + row * LH;
                Uint8 r = selected ? 255 : 180;
                Uint8 g = selected ? 255 : 180;
                Uint8 b = selected ? 80  : 180;
                if (selected)
                    draw_text(plat.renderer, ">", MX + 8, ry, 2, r, g, b);
                draw_text(plat.renderer, label, MX + 24, ry, 2, r, g, b);
            };

            // Row 0: dungeon type selector
            {
                char buf[64];
                const char* dn = DBG_TYPE_NAMES[dbg_type];
                // build "< NAME >" string
                int blen = 0;
                buf[blen++] = '<'; buf[blen++] = ' ';
                for (int k = 0; dn[k]; k++) buf[blen++] = dn[k];
                buf[blen++] = ' '; buf[blen++] = '>'; buf[blen] = '\0';
                // prefix with "DUNGEON: "
                char full[80];
                int fi = 0;
                const char* pre = "DUNGEON: ";
                for (int k = 0; pre[k]; k++) full[fi++] = pre[k];
                for (int k = 0; buf[k]; k++) full[fi++] = buf[k];
                full[fi] = '\0';
                draw_row(0, full, dbg_sel == 0);
            }

            draw_row(1, "ENTER DUNGEON", dbg_sel == 1);
            draw_row(2, "REGEN MAP",     dbg_sel == 2);

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

            draw_text(plat.renderer, "UP/DN:NAV  LT/RT:CHANGE  Z:SELECT  F2:CLOSE",
                      MX + 6, MY + MH - 16, 1, 180, 180, 180);
        }

        // ── Battle test list overlay ──────────────────────────────────────────
        if (battle_list_open) {
            static const int VIEW = 10;
            const int PW = 360, PH = 34 + VIEW * 18 + 18;
            const int PX = (640 - PW) / 2, PY = (480 - PH) / 2;

            draw_nes_panel(plat.renderer, PX, PY, PW, PH);
            draw_text(plat.renderer, "BATTLE TEST",
                      PX + (PW - text_width("BATTLE TEST", 2)) / 2,
                      PY + NES_PAD + 4, 2, 255, 255, 255);

            int top = battle_list_sel - VIEW / 2;
            if (top < 0)       top = 0;
            if (top > 50-VIEW) top = 50 - VIEW;

            for (int i = 0; i < VIEW; i++) {
                int idx = top + i;
                if (idx >= 50) break;
                bool sel = (idx == battle_list_sel);
                int ry = PY + 34 + i * 18;
                Uint8 cr = sel ? 255 : 180, cg = sel ? 255 : 180, cb = sel ? 80 : 180;
                if (sel) draw_text(plat.renderer, ">", PX + 8, ry, 2, cr, cg, cb);
                char label[32];
                SDL_snprintf(label, sizeof(label), "%02d  %s", idx, ENEMY_NAMES[idx]);
                draw_text(plat.renderer, label, PX + 24, ry, 2, cr, cg, cb);
            }

            draw_text(plat.renderer, "UP/DN:SELECT  Z:FIGHT  F3:CLOSE",
                      PX + 6, PY + PH - 14, 1, 180, 180, 180);
        }

        float dbg_px = (state == STATE_DUNGEON) ? dplayer.x : ow.x;
        float dbg_py = (state == STATE_DUNGEON) ? dplayer.y : ow.y;
        draw_fps(plat.renderer, dt, dbg_px, dbg_py);

        if (esc_hold_time > 0.f) {
            const int BAR_W = 80;
            const int BAR_H = 6;
            const int BX = 4, BY = 34;
            draw_text(plat.renderer, "HOLD ESC TO QUIT", BX, BY - 12, 1, 255, 255, 80);
            SDL_SetRenderDrawColor(plat.renderer, 60, 60, 60, 255);
            SDL_Rect track = { BX, BY, BAR_W, BAR_H };
            SDL_RenderFillRect(plat.renderer, &track);
            int fill_w = (int)(esc_hold_time / 3.f * BAR_W);
            if (fill_w > BAR_W) fill_w = BAR_W;
            SDL_SetRenderDrawColor(plat.renderer, 255, 80, 80, 255);
            SDL_Rect fill = { BX, BY, fill_w, BAR_H };
            SDL_RenderFillRect(plat.renderer, &fill);
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
    gen_thread.join();
    delete battle_scene;
    delete map;

    //cleanups textures
    SDL_DestroyTexture(player_sprite);
    player_sprite = NULL;

    tilemap_free_tile_cache();
    IMG_Quit();
    platform_shutdown(&plat);

    return 0;
}
