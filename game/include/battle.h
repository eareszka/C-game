#ifndef BATTLE_H
#define BATTLE_H

#include <SDL2/SDL.h>
#include <stdbool.h>
#include "input.h"
#include "entity.h"

// ── Phase state machine ───────────────────────────────────────────────────────

typedef enum {
    BATTLE_PHASE_START_ROUND,   // sort/advance turn order
    BATTLE_PHASE_PLAYER_MENU,   // player picking an action
    BATTLE_PHASE_PLAYER_TARGET, // player picking which enemy
    BATTLE_PHASE_ENEMY_THINK,   // AI picks action
    BATTLE_PHASE_RESOLVE,       // apply damage / effects, write log
    BATTLE_PHASE_CHECK_END,     // did someone win?
    BATTLE_PHASE_VICTORY,
    BATTLE_PHASE_DEFEAT,
} BattlePhase;

// ── Actions ───────────────────────────────────────────────────────────────────

typedef enum {
    ACTION_ATTACK,
    ACTION_MAGIC,
    ACTION_DEFEND,
    ACTION_RUN,
} BattleAction;

// ── Combatant ─────────────────────────────────────────────────────────────────

typedef struct {
    const char* name;
    Stats*      stats;      // points into Player.stats or Enemy.stats
    bool        is_player;
    bool        defending;  // set by ACTION_DEFEND, cleared each round
    bool        dead;
} Combatant;

// ── Message log ───────────────────────────────────────────────────────────────

#define BATTLE_LOG_LINES 2
#define BATTLE_LOG_LEN   80

typedef struct {
    char lines[BATTLE_LOG_LINES][BATTLE_LOG_LEN];
} BattleLog;

// ── Main Battle struct ────────────────────────────────────────────────────────

#define BATTLE_MAX_ENEMIES 6

typedef struct {
    BattlePhase  phase;

    // combatants
    Player*      player;
    Combatant    player_combatant;

    Enemy        enemies[BATTLE_MAX_ENEMIES];
    Combatant    enemy_combatants[BATTLE_MAX_ENEMIES];
    int          enemy_count;

    // turn order — player + enemies sorted by spd descending
    Combatant*   turn_order[BATTLE_MAX_ENEMIES + 1];
    int          turn_count;
    int          turn_index;   // whose turn it is right now

    // player menu
    int          menu_cursor;    // 0=Attack 1=Magic 2=Defend 3=Run
    int          target_cursor;  // which enemy is targeted
    BattleAction pending_action;

    // brief pause after resolving so the player can read the log
    float        resolve_timer;

    BattleLog    log;
} Battle;

// ── API ───────────────────────────────────────────────────────────────────────

// Call when entering battle. player must stay valid for the battle's duration.
void battle_start(Battle* b, Player* player, Enemy* enemies, int enemy_count);

void battle_update(Battle* b, const Input* in, float dt);
void battle_draw(const Battle* b, SDL_Renderer* ren);

#endif
