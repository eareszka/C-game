#include "battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// ── Helpers ───────────────────────────────────────────────────────────────────

static void log_write(BattleLog* log, const char* msg) {
    // shift lines up, write new one at bottom
    for (int i = 0; i < BATTLE_LOG_LINES - 1; i++)
        strncpy(log->lines[i], log->lines[i + 1], BATTLE_LOG_LEN);
    strncpy(log->lines[BATTLE_LOG_LINES - 1], msg, BATTLE_LOG_LEN - 1);
    log->lines[BATTLE_LOG_LINES - 1][BATTLE_LOG_LEN - 1] = '\0';
}

// ±15% variance seeded from luck
static int apply_variance(int base, int luck) {
    float variance = 0.15f * ((float)(luck % 100) / 100.0f) - 0.075f;
    int result = (int)(base * (1.0f + variance));
    return result < 1 ? 1 : result;
}

static int calc_physical(const Stats* atk, const Stats* def) {
    int raw = atk->attack - def->iq / 2;
    if (raw < 1) raw = 1;
    return apply_variance(raw, atk->luck);
}

static int calc_magic(const Stats* atk, const Stats* def) {
    int raw = atk->mag - def->iq;
    if (raw < 1) raw = 1;
    return apply_variance(raw, atk->luck);
}

static void apply_damage(Combatant* target, int dmg) {
    if (target->defending) dmg /= 2;
    if (dmg < 1) dmg = 1;
    target->stats->hp -= dmg;
    if (target->stats->hp <= 0) {
        target->stats->hp = 0;
        target->dead = true;
    }
}

// ── Turn order ────────────────────────────────────────────────────────────────

static int cmp_spd(const void* a, const void* b) {
    const Combatant* ca = *(const Combatant**)a;
    const Combatant* cb = *(const Combatant**)b;
    return cb->stats->spd - ca->stats->spd; // descending
}

static void build_turn_order(Battle* b) {
    b->turn_count = 0;
    b->turn_order[b->turn_count++] = &b->player_combatant;
    for (int i = 0; i < b->enemy_count; i++)
        b->turn_order[b->turn_count++] = &b->enemy_combatants[i];
    qsort(b->turn_order, b->turn_count, sizeof(Combatant*), cmp_spd);
    b->turn_index = 0;
}

static Combatant* current_actor(Battle* b) {
    return b->turn_order[b->turn_index];
}

// Advance to the next living actor, wrapping to a new round when needed.
static void next_actor(Battle* b) {
    do {
        b->turn_index++;
        if (b->turn_index >= b->turn_count) {
            b->turn_index = 0;
            // clear defending flags at round boundary
            b->player_combatant.defending = false;
            for (int i = 0; i < b->enemy_count; i++)
                b->enemy_combatants[i].defending = false;
        }
    } while (b->turn_order[b->turn_index]->dead);
}

// ── AI ────────────────────────────────────────────────────────────────────────

static void enemy_think(Battle* b) {
    // always attack the player
    b->pending_action = ACTION_ATTACK;
}

// ── Resolve ───────────────────────────────────────────────────────────────────

static void resolve_action(Battle* b) {
    Combatant* actor = current_actor(b);
    char msg[BATTLE_LOG_LEN];

    if (actor->is_player) {
        switch (b->pending_action) {
            case ACTION_ATTACK: {
                Combatant* target = &b->enemy_combatants[b->target_cursor];
                int dmg = calc_physical(actor->stats, target->stats);
                apply_damage(target, dmg);
                snprintf(msg, sizeof(msg), "%s attacks %s for %d damage!",
                         actor->name, target->name, dmg);
                break;
            }
            case ACTION_MAGIC: {
                Combatant* target = &b->enemy_combatants[b->target_cursor];
                int dmg = calc_magic(actor->stats, target->stats);
                apply_damage(target, dmg);
                snprintf(msg, sizeof(msg), "%s casts on %s for %d damage!",
                         actor->name, target->name, dmg);
                break;
            }
            case ACTION_DEFEND:
                actor->defending = true;
                snprintf(msg, sizeof(msg), "%s takes a defensive stance.", actor->name);
                break;
            case ACTION_RUN: {
                int roll = (int)(SDL_GetTicks() % 100);
                int chance = actor->stats->max_luck > 0
                    ? actor->stats->luck * 100 / actor->stats->max_luck
                    : 0;
                if (roll < chance) {
                    log_write(&b->log, "Escaped from battle!");
                    b->phase = BATTLE_PHASE_DEFEAT; // caller treats this as "exit"
                    return;
                }
                snprintf(msg, sizeof(msg), "%s tried to run but failed!", actor->name);
                break;
            }
        }
    } else {
        int dmg = calc_physical(actor->stats, b->player_combatant.stats);
        apply_damage(&b->player_combatant, dmg);
        snprintf(msg, sizeof(msg), "%s attacks %s for %d damage!",
                 actor->name, b->player_combatant.name, dmg);
    }

    log_write(&b->log, msg);
    b->resolve_timer = 1.2f;
    b->phase = BATTLE_PHASE_RESOLVE;
}

// ── Public API ────────────────────────────────────────────────────────────────

void battle_start(Battle* b, Player* player, Enemy* enemies, int enemy_count) {
    memset(b, 0, sizeof(*b));

    b->player = player;
    b->player_combatant.name      = "Hero";
    b->player_combatant.stats     = &player->stats;
    b->player_combatant.is_player = true;

    if (enemy_count > BATTLE_MAX_ENEMIES) enemy_count = BATTLE_MAX_ENEMIES;
    b->enemy_count = enemy_count;

    static const char* enemy_names[] = {"Goblin","Slime","Bat","Wolf","Shade","Golem"};
    for (int i = 0; i < enemy_count; i++) 
    {
        b->enemies[i] = enemies[i];
        b->enemy_combatants[i].name = enemy_names[i % 6];
        b->enemy_combatants[i].stats = &b->enemies[i].stats;
        b->enemy_combatants[i].is_player = false;
    }

    build_turn_order(b);
    log_write(&b->log, "Battle start!");
    b->phase = BATTLE_PHASE_START_ROUND;
}

void battle_update(Battle* b, const Input* in, float dt) 
{
    switch (b->phase) 
    {

        case BATTLE_PHASE_START_ROUND: 
        {
            Combatant* actor = current_actor(b);
            b->phase = actor->is_player ? BATTLE_PHASE_PLAYER_MENU : BATTLE_PHASE_ENEMY_THINK;
            break;
        }

        case BATTLE_PHASE_PLAYER_MENU: 
        {
            if (input_pressed(in, SDL_SCANCODE_UP))
                b->menu_cursor = (b->menu_cursor + 3) % 4;
            if (input_pressed(in, SDL_SCANCODE_DOWN))
                b->menu_cursor = (b->menu_cursor + 1) % 4;

            if (input_pressed(in, SDL_SCANCODE_RETURN) || input_pressed(in, SDL_SCANCODE_Z)) 
            {
                b->pending_action = (BattleAction)b->menu_cursor;
                if (b->pending_action == ACTION_DEFEND || b->pending_action == ACTION_RUN) 
                {
                    resolve_action(b);
                } 
                else 
                {
                    // pick first living enemy as default target
                    b->target_cursor = 0;
                    while (b->target_cursor < b->enemy_count &&
                           b->enemy_combatants[b->target_cursor].dead)
                        b->target_cursor++;
                    b->phase = BATTLE_PHASE_PLAYER_TARGET;
                }
            }
            break;
        }

        case BATTLE_PHASE_PLAYER_TARGET: 
        {
            if (input_pressed(in, SDL_SCANCODE_LEFT)) 
            {
                do 
                {
                    b->target_cursor = (b->target_cursor + b->enemy_count - 1) % b->enemy_count;
                } 
                while (b->enemy_combatants[b->target_cursor].dead);
            }
            if (input_pressed(in, SDL_SCANCODE_RIGHT)) {
                do {
                    b->target_cursor = (b->target_cursor + 1) % b->enemy_count;
                } while (b->enemy_combatants[b->target_cursor].dead);
            }
            if (input_pressed(in, SDL_SCANCODE_ESCAPE) || input_pressed(in, SDL_SCANCODE_X))
                b->phase = BATTLE_PHASE_PLAYER_MENU;
            if (input_pressed(in, SDL_SCANCODE_RETURN) || input_pressed(in, SDL_SCANCODE_Z))
                resolve_action(b);
            break;
        }

        case BATTLE_PHASE_ENEMY_THINK:
            enemy_think(b);
            resolve_action(b);
            break;

        case BATTLE_PHASE_RESOLVE:
            b->resolve_timer -= dt;
            if (b->resolve_timer <= 0.0f)
                b->phase = BATTLE_PHASE_CHECK_END;
            break;

        case BATTLE_PHASE_CHECK_END: {
            if (b->player_combatant.dead) {
                log_write(&b->log, "You were defeated...");
                b->phase = BATTLE_PHASE_DEFEAT;
                break;
            }
            bool all_dead = true;
            for (int i = 0; i < b->enemy_count; i++)
                if (!b->enemy_combatants[i].dead) { all_dead = false; break; }
            if (all_dead) 
            {
                log_write(&b->log, "Victory!");
                b->phase = BATTLE_PHASE_VICTORY;
                break;
            }
            next_actor(b);
            b->phase = BATTLE_PHASE_START_ROUND;
            break;
        }

        case BATTLE_PHASE_VICTORY:
        case BATTLE_PHASE_DEFEAT:
            // main.c polls b->phase and transitions back to overworld
            break;
    }
}

// ── Drawing ───────────────────────────────────────────────────────────────────

static void fill_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                      Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    SDL_SetRenderDrawColor(ren, r, g, b, a);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(ren, &rect);
}

static void draw_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                      Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    SDL_SetRenderDrawColor(ren, r, g, b, a);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderDrawRect(ren, &rect);
}

static void draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
                     int cur, int max, Uint8 fr, Uint8 fg, Uint8 fb) {
    fill_rect(ren, x, y, w, h, 40, 40, 40, 255);
    if (max > 0 && cur > 0) {
        int filled = w * cur / max;
        fill_rect(ren, x, y, filled, h, fr, fg, fb, 255);
    }
    draw_rect(ren, x, y, w, h, 180, 180, 180, 255);
}

void battle_draw(const Battle* b, SDL_Renderer* ren) {
    // background
    SDL_SetRenderDrawColor(ren, 0, 0, 0, 255);
    SDL_RenderClear(ren);

    // ── Enemy area (y 0..263) ─────────────────────────────────────────────────
    int slot_w = b->enemy_count > 0 ? 640 / b->enemy_count : 640;

    for (int i = 0; i < b->enemy_count; i++) {
        const Combatant* c = &b->enemy_combatants[i];
        int cx = slot_w * i + slot_w / 2;
        int cy = 110;
        bool targeted = (b->phase == BATTLE_PHASE_PLAYER_TARGET && i == b->target_cursor);

        if (c->dead) {
            draw_rect(ren, cx - 32, cy - 40, 64, 80, 60, 60, 60, 255);
        } else {
            Uint8 hi = targeted ? 255 : 160;
            fill_rect(ren, cx - 32, cy - 40, 64, 80, 60, hi, 60, 255);
            draw_rect(ren, cx - 32, cy - 40, 64, 80, 200, 255, 200, 255);
            if (targeted)
                draw_rect(ren, cx - 34, cy - 42, 68, 84, 255, 255, 80, 255);
            // HP bar
            draw_bar(ren, cx - 32, cy + 46, 64, 8,
                     c->stats->hp, c->stats->max_hp, 80, 220, 80);
        }
    }

    // ── Log strip (y 264..311) ────────────────────────────────────────────────
    fill_rect(ren, 0, 264, 640, 48, 10, 10, 28, 255);
    draw_rect(ren, 0, 264, 640, 48, 70, 70, 110, 255);
    // TODO: render b->log.lines[0] and [1] with SDL_ttf once wired up

    // ── Bottom panel (y 312..479) ─────────────────────────────────────────────
    fill_rect(ren, 0, 312, 640, 168, 20, 20, 50, 255);

    // action menu box (left)
    draw_rect(ren, 4, 316, 236, 160, 100, 100, 160, 255);

    static const char* action_labels[] = {"Attack", "Magic", "Defend", "Run"};
    (void)action_labels; // used once SDL_ttf is wired up
    for (int i = 0; i < 4; i++) {
        int ay = 330 + i * 36;
        bool sel = (b->menu_cursor == i && b->phase == BATTLE_PHASE_PLAYER_MENU);
        if (sel) fill_rect(ren, 8, ay - 4, 228, 28, 50, 50, 110, 255);
        // cursor arrow placeholder
        if (sel) {
            fill_rect(ren, 14, ay + 4, 8, 8, 255, 255, 80, 255);
        }
        // label box placeholder (replace with text)
        draw_rect(ren, 28, ay, 100, 18, sel ? 255 : 160, sel ? 255 : 160, sel ? 255 : 160, 255);
    }

    // player status box (right)
    draw_rect(ren, 248, 316, 388, 160, 100, 100, 160, 255);
    {
        const Stats* s = &b->player->stats;
        // HP bar
        draw_bar(ren, 260, 360, 360, 18, s->hp, s->max_hp, 80, 220, 80);
        // player name / HP label placeholder box
        draw_rect(ren, 260, 330, 200, 18, 200, 200, 200, 255);
    }

    // ── Victory / Defeat overlay ──────────────────────────────────────────────
    if (b->phase == BATTLE_PHASE_VICTORY) {
        fill_rect(ren, 160, 170, 320, 80, 10, 60, 10, 230);
        draw_rect(ren, 160, 170, 320, 80, 80, 255, 80, 255);
    } else if (b->phase == BATTLE_PHASE_DEFEAT) {
        fill_rect(ren, 160, 170, 320, 80, 70, 5, 5, 230);
        draw_rect(ren, 160, 170, 320, 80, 255, 50, 50, 255);
    }
}
