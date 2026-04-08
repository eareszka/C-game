#include <stdbool.h>
#include <stdio.h>
#include <SDL2/SDL_image.h>

#include "game_state.h"
#include "battle.h"
#include "platform.h"
#include "core.h"
#include "input.h"
#include "overworld.h"
#include "camera.h"
#include "tileset.h"
#include "tilemap.h"
#include "resource_node.h"

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    Platform plat;
    if (!platform_init(&plat, "Four Castle Chronicles", 640, 480)) {
        return 1;
    }

    //SDL_SetWindowFullscreen(plat.window, SDL_WINDOW_FULLSCREEN_DESKTOP);
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(plat.renderer, 640, 480);

    if (!(IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG)) {
        printf("SDL_image init failed: %s\n", IMG_GetError());
        platform_shutdown(&plat);
        return 1;
    }

    Tileset tileset;
    if (!tileset_load(&tileset, plat.renderer, "assets/tileset.png", 16, 16)) {
        IMG_Quit();
        platform_shutdown(&plat);
        return 1;
    }

    SDL_Texture* player_sprite = IMG_LoadTexture(plat.renderer, "assets/Sprite-0001.png");
    if (!player_sprite) {
        printf("Failed to load sprite: %s\n", IMG_GetError());
        tileset_unload(&tileset);
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

    Battle battle;

    Overworld ow;

    float start_x = 300.0f;
    float start_y = 150.0f;
    float player_spd = 150.0f;
    overworld_init(&ow, start_x, start_y, player_spd, 32, 48);

    Tilemap map;
    tilemap_build_starting_area(&map);

    //initializes resources
    ResourceNodeList resources;
    resource_nodes_init(&resources);

    resource_nodes_add(&resources, RESOURCE_TREE, 160, 160);
    resource_nodes_add(&resources, RESOURCE_ROCK, 256, 128);
    resource_nodes_add(&resources, RESOURCE_FLOWER, 320, 224);


    Input in = {0};

    Camera cam = {0};
    cam.screen_w = 640;
    cam.screen_h = 480;

    bool running = true;


    while (running) 
    {
        double dt_d = time_delta_seconds();
        float dt = (float)dt_d;

        input_begin_frame(&in);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            input_handle_event(&in, &e);
        }
        if (in.quit) running = false;
        if (input_down(&in, SDL_SCANCODE_ESCAPE)) running = false;

        if (input_pressed(&in, SDL_SCANCODE_B) && state != STATE_BATTLE) {
            // Placeholder encounter — replace with encounter data from overworld
            Enemy enc[2] = {0};
            enc[0].enemy_id        = 0;
            enc[0].stats.max_hp    = 30; enc[0].stats.hp    = 30;
            enc[0].stats.max_spd   = 8;  enc[0].stats.spd   = 8;
            enc[0].stats.max_attack= 10; enc[0].stats.attack= 10;
            enc[0].stats.max_iq    = 4;  enc[0].stats.iq    = 4;
            enc[0].stats.max_luck  = 10; enc[0].stats.luck  = 10;
            enc[1].enemy_id        = 1;
            enc[1].stats.max_hp    = 20; enc[1].stats.hp    = 20;
            enc[1].stats.max_spd   = 12; enc[1].stats.spd   = 12;
            enc[1].stats.max_attack= 7;  enc[1].stats.attack= 7;
            enc[1].stats.max_iq    = 2;  enc[1].stats.iq    = 2;
            enc[1].stats.max_luck  = 15; enc[1].stats.luck  = 15;
            battle_start(&battle, &player, enc, 2);
            state = STATE_BATTLE;
        }

        switch (state) {
            case STATE_TITLE:
                SDL_SetRenderDrawColor(plat.renderer, 0, 0, 0, 255);
                SDL_RenderClear(plat.renderer);
                break;

            case STATE_OVERWORLD: {
                overworld_update(&ow, &in, dt, &resources);

                float player_cx = ow.x + ow.width * 0.5f;
                float player_cy = ow.y + ow.height * 0.5f;
                camera_center_on(&cam, player_cx, player_cy);

                SDL_SetRenderDrawColor(plat.renderer, 10, 10, 20, 255);
                SDL_RenderClear(plat.renderer);
                

                //draw order
                tilemap_draw(&map, &tileset, &cam, plat.renderer); //tiles
                resource_nodes_draw(&resources, &cam, plat.renderer, tileset.texture); //resources
                overworld_draw(&ow, &cam, plat.renderer, player_sprite); //player
                break;
            }

            case STATE_BATTLE:
                battle_update(&battle, &in, dt);
                battle_draw(&battle, plat.renderer);
                if (battle.phase == BATTLE_PHASE_VICTORY || battle.phase == BATTLE_PHASE_DEFEAT) {
                    if (input_pressed(&in, SDL_SCANCODE_RETURN) || input_pressed(&in, SDL_SCANCODE_Z))
                        state = STATE_OVERWORLD;
                }
                break;
        }

        SDL_RenderPresent(plat.renderer);
    }

    //cleanups textures
    tileset_unload(&tileset);
    SDL_DestroyTexture(player_sprite);
    player_sprite = NULL;

    IMG_Quit();
    platform_shutdown(&plat);

    return 0;
}
