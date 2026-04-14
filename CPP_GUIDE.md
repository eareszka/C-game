# Four Castle Chronicles — Developer Guide

---

## 1. Project Map

```
game/
├── makefile               build system
├── assets/                sprite sheets, tilesets (PNG)
├── include/               all headers (.h) — one per system
│   ├── game_state.h       GameState enum (4 states)
│   ├── entity.h           Player, Enemy, Stats structs
│   ├── tilemap.h          Tilemap, DungeonEntrance, all tile IDs (71 tiles)
│   ├── dungeon.h          DungeonMap, DungeonPlayer, dungeon tile types
│   ├── overworld.h        Overworld struct + function declarations
│   ├── battle.h           Battle, BattlePlayer, BattleEnemy, Bullet pools
│   ├── input.h            Input struct, key state enum
│   ├── camera.h           Camera struct
│   ├── resource_node.h    ResourceNode, ResourceNodeList
│   ├── core.h             draw_text, text_width, draw_fps, time_delta_seconds
│   ├── platform.h         Platform (SDL2 window + renderer wrapper)
│   ├── towns.h            Town/village blueprint data (currently all nullptr)
│   └── castles.h          Castle blueprint data (currently all nullptr)
└── src/                   all implementations (.cpp)
    ├── main.cpp           game loop, state machine, all state transitions
    ├── tilemap.cpp        world generation (~2700 lines, phase1 + phase2)
    ├── dungeon.cpp        dungeon generation, decoration, movement (~1000 lines)
    ├── overworld.cpp      player movement, entrance detection, resource interaction
    ├── battle.cpp         bullet-hell combat, enemy AI, weapon profiles
    ├── resource_node.cpp  resource node pool, hit detection, rendering
    ├── core.cpp           bitmap font, FPS display, delta time
    ├── camera.cpp         camera centering + pixel-quantization
    ├── input.cpp          SDL event → key state machine
    ├── platform.cpp       SDL2 init/shutdown
    ├── tileset.cpp        tileset texture loader (unused — game renders ASCII)
    └── enemy.cpp          empty (placeholder for future enemy logic)
```

**Rule of thumb:** if you're adding a new _system_, create `include/system.h` and `src/system.cpp`. If you're extending an existing system, find its file pair and add there.

---

## 2. Navigation

### Finding things fast

| What you want | Where it is |
|---|---|
| Add a new game state | `game_state.h` enum + new `case` in `main.cpp` switch |
| Change player speed | `overworld.cpp` ~line 60, `dungeon.cpp` `dungeon_player_init` |
| Add a new tile type | `tilemap.h` enum + style entry in `tilemap.cpp` `tile_styles[]` |
| Add a new dungeon type | `tilemap.h` `DungeonEntranceType` + 5 places in `tilemap.cpp` + `dungeon.cpp` |
| Change battle weapon | `battle.h` `WeaponType` enum + `battle.cpp` `weapon_profile()` |
| Add a new resource | `resource_node.h` `ResourceType` enum + cases in `resource_node.cpp` |
| Change dungeon room shapes | `dungeon.cpp` carve/decorate functions for that type |
| Change dungeon colors | `dungeon.cpp` `PALETTES[]` array, indexed by `DungeonEntranceType` |
| Change overworld biome colors | `tilemap.cpp` `tile_styles[]` array |
| Change how dungeons connect | `tilemap.cpp` `link_dungeons` block at end of `tilemap_build_overworld_phase2` |
| Change portal placement logic | `dungeon.cpp` `dungeon_orient_portals` |
| Change frame rate | `main.cpp` `FRAME_TICKS = PERF_FREQ / 60` |

### Coordinate systems

There are three coordinate spaces in this game. Always know which one you're in:

```
Tile coords:   (tx, ty)  integer,  range [0, 3000)  ← tilemap grid
World coords:  (wx, wy)  float,    pixels            ← wx = tx * TILE_SIZE (32)
Screen coords: (sx, sy)  integer   pixels            ← sx = (wx - cam.x) * cam.zoom
```

Player **position** is world coords top-left. Player **feet** for tile detection are:
```cpp
float feet_x = ow.x + player.width  * 0.5f;
float feet_y = ow.y + player.height - 8.0f;
int   tile_x = (int)(feet_x / TILE_SIZE);
int   tile_y = (int)(feet_y / TILE_SIZE);
```

Dungeon uses a separate 80×80 grid (`DMAP_W/H`) with `DMAP_TILE = 32`. World pixel position inside a dungeon = `tile * DMAP_TILE`.

### RNG pattern

Every procedural system uses the same LCG:
```cpp
seed = seed * 1664525u + 1013904223u;
int value = (int)((seed >> 16) % range);   // integer in [0, range)
float f   = (float)(seed >> 16) / 65536.0f; // float in [0, 1)
```

Always pass `uint32_t* rng` or `unsigned int seed` (value-copy for stateless, pointer for stateful). XOR the world seed with position or type to get unique sub-seeds:
```cpp
uint32_t dungeon_seed = world_seed ^ ((uint32_t)type * 0xBEEF1234u);
uint32_t entrance_seed = world_seed ^ (x * 73856093u) ^ (y * 19349663u);
```

---

## 3. How to Add New Things

### Adding a new dungeon type

This touches 5 files. Use STONEHENGE as the reference — it's the most complex existing type.

**Step 1 — `tilemap.h`: add the enum value**
```cpp
typedef enum {
    // ... existing types ...
    DUNGEON_ENT_LARGE_TREE   = 7,
    DUNGEON_ENT_SWAMP        = 8,  // ← new
} DungeonEntranceType;
```

**Step 2 — `tilemap.h`: add a tile ID** (for the overworld entrance tile)
```cpp
// at the end of the tile type list
#define TILE_DUNGEON_SWAMP  (TILE_DUNGEON_LARGE_TREE + 1)
```

**Step 3 — `tilemap.cpp`: add a tile style** (color + ASCII glyph for the overworld tile)
```cpp
// in tile_styles[] array, matching the tile ID:
[TILE_DUNGEON_SWAMP] = { 30, 60, 40,   // bg: dark green
                         80, 180, 90,   // fg: bright green
                         { /* 8-byte glyph bitmap */ } },
```

**Step 4 — `tilemap.cpp`: wire it into biome selection and tile ID lookup**

Find `pick_entrance_type()` — add your type to the biome condition that makes sense (e.g. SWAMP appears in wetland/river-adjacent tiles). Find `entrance_tile_id()` — add a `case DUNGEON_ENT_SWAMP: return TILE_DUNGEON_SWAMP;`.

**Step 5 — `dungeon.cpp`: add a palette and layout function**
```cpp
// in PALETTES[]:
// SWAMP  (index 8 — expand array to [9])
{{ 20, 40, 25,255},{ 35, 65, 38,255},{200,175, 40,255},{ 60,200, 80,255}},
```

Then write your layout function or add a branch in `dungeon_generate`:
```cpp
if (type == DUNGEON_ENT_SWAMP) {
    // use carve_room_layout, carve_hybrid_layout, or write a custom carver
    carve_room_layout(dmap, type, rng);
    // add decoration
    clear_portal_surroundings(dmap);
    return;
}
```

**Step 6 — `main.cpp`: add the name string** in the `dungeon_names[]` array.

---

### Adding a new game state

**Step 1 — `game_state.h`**
```cpp
typedef enum GameState {
    STATE_TITLE     = 0,
    STATE_OVERWORLD = 1,
    STATE_BATTLE    = 2,
    STATE_DUNGEON   = 3,
    STATE_MENU      = 4,  // ← new
} GameState;
```

**Step 2 — `main.cpp`** — add the case to the switch. Follow the existing pattern: update first, then draw, then check for exit condition.
```cpp
case STATE_MENU: {
    menu_update(&menu, &in, dt);

    SDL_SetRenderDrawColor(plat.renderer, 0, 0, 0, 255);
    SDL_RenderClear(plat.renderer);
    menu_draw(&menu, plat.renderer);

    if (menu.selected_start)
        state = STATE_OVERWORLD;
    break;
}
```

**Step 3** — declare `menu_update` and `menu_draw` in `include/menu.h`, implement in `src/menu.cpp`. The makefile picks up all `src/*.cpp` automatically — no makefile changes needed.

---

### Adding a new tile type

1. Add a `#define TILE_FOO N` in `tilemap.h` with a unique number
2. Add a `TileStyle` entry at index `N` in `tilemap.cpp`'s `tile_styles[]` — this is the color and ASCII glyph rendered in the tile cache
3. Stamp it wherever you want in `tilemap_build_overworld_phase2`
4. If it needs special collision or interaction, add a case in `overworld.cpp` where tile types are checked

The tile cache (`tilemap_init_tile_cache`) iterates up to `NUM_TILE_STYLES` so bump that constant if you add beyond the current max.

---

### Adding a new weapon to battle

Everything lives in `battle.h`/`battle.cpp`.

**Step 1 — `battle.h`:** add to the enum
```cpp
enum WeaponType {
    WEAPON_DAGGER, WEAPON_LONGSWORD, WEAPON_SPEAR, WEAPON_AXE,
    WEAPON_BOW,   // ← new
};
```

**Step 2 — `battle.cpp`:** add a case in `weapon_profile()`
```cpp
case WEAPON_BOW:
    return { 600.f, 6.f, 3.f, 1, 0.f, 4.f };
    //        speed  dmg  rate cnt spread radius
```

**Step 3 — `main.cpp`:** pass the new weapon to `battle_start()` when you want it used.

---

### Adding a new resource node type

1. Add to `ResourceType` enum in `resource_node.h`
2. Add rendering logic in `resource_nodes_draw()` in `resource_node.cpp` — pick a color and ASCII glyph
3. Set HP and hit radius in `resource_nodes_add()` or wherever you spawn them
4. Add collection behavior in `tilemap_try_hit()` if destroying it should change the tile underneath

---

### Adding an NPC or non-hostile entity

There is no entity system yet. The practical approach right now:

1. Add a struct in a new header, e.g. `include/npc.h` — copy the pattern from `Enemy`
2. Store a fixed-size array of them in the `Tilemap` struct (like `DungeonEntrance dungeon_entrances[300]`)
3. Spawn them in phase2 alongside dungeon entrance placement
4. Update and draw them in the `STATE_OVERWORLD` case in `main.cpp`
5. Add proximity detection in `overworld_update` following the same pattern as `at_dungeon_entrance`

---

## 4. Using C++ Effectively in This Project

This codebase mixes C-style structs with C++ features. Here's the project's existing style and where to go next.

### What the project already uses — keep using it

**Lambdas for local algorithms** — `tilemap.cpp` uses ~20 lambdas for procedural logic that only makes sense in context. This is correct. Don't extract these into named functions.
```cpp
auto door_ok = [&](int ex, int ey, int sz) -> bool { ... };
auto lnext   = [&]() -> uint32_t { lrng = lrng*1664525u+1013904223u; return (lrng>>16)&0x7FFF; };
```

**`std::vector` for dynamic arrays** — used in tilemap.cpp for shuffle buffers and coordinate lists. Always prefer this over a raw array + count variable.

**`std::unordered_map` for sparse data** — `s_tile_hp` maps `(x,y)` → HP for destructible tiles. The pattern is right; avoid it for data you iterate over frequently since cache locality suffers.

**`nullptr` over `NULL`** — already consistent throughout.

**`bool` over `int` for flags** — `battle.cpp` and `dungeon.cpp` use `bool`. Follow this.

### The most valuable C++ additions right now

**References instead of always-non-null pointers**

When a pointer parameter is never null at any call site, make it a reference. This removes an entire category of bug (null dereference) at no cost:
```cpp
// current:
void overworld_update(Overworld* ow, Player* player, const Input* in, ...);

// better:
void overworld_update(Overworld& ow, Player& player, const Input& in, ...);
```
Use `const T&` for inputs you don't modify, `T&` for outputs you do. Keep raw `T*` only when null is genuinely valid (optional parameters, nullable handles).

**Constructors on Stats and Player to kill uninitialized-field warnings**

Every `Player player = {0};` in the codebase is suppressing potential bugs. Add a constructor:
```cpp
struct Stats {
    int max_hp = 0, hp = 0;
    int max_spd = 0, spd = 0;
    int max_mag = 0, mag = 0;
    int max_attack = 0, attack = 0;
    int max_luck = 0, luck = 0;
    int max_iq = 0, iq = 0;
    int exp = 0;
};
```
In-class default member initializers (the `= 0` syntax) zero-initialize without needing a constructor body. This also fixes all the `-Wmissing-field-initializers` warnings in `main.cpp`.

**`enum class` for new enums**

New enums should use `enum class` — it prevents silent integer comparisons and name collisions:
```cpp
// old (values leak into enclosing scope — FIGHTING could clash with anything)
enum BattlePhase { BATTLE_PHASE_FIGHTING, ... };

// new (scoped — must write BattlePhase::Fighting)
enum class BattlePhase { Fighting, Victory, Defeat };
```
Don't convert existing enums unless you're touching that file anyway — the rename is noisy.

**`constexpr` for compile-time constants**

Replace scattered `#define` magic numbers with `constexpr`:
```cpp
// instead of:
#define CONNECT_RANGE 100

// write:
static constexpr int CONNECT_RANGE = 100;  // typed, scoped, debuggable
```
`constexpr` variables show up in the debugger with their names. `#define` substitutions don't.

**`[[nodiscard]]` on functions whose return value matters**

```cpp
[[nodiscard]] bool tilemap_is_walkable(const Tilemap& map, int tx, int ty);
```
The compiler will warn if you call it and ignore the result — catches bugs where you check the wrong condition.

### What to avoid

**Don't use `new`/`delete` for new code.** `Tilemap* map = new Tilemap()` is a leak waiting to happen. Use stack allocation or `std::unique_ptr`:
```cpp
auto map = std::make_unique<Tilemap>();
// automatically deleted when it goes out of scope
```

**Don't use `std::shared_ptr` for game objects.** Shared ownership with reference counting is expensive and rarely correct for game state. Everything in this game has a clear single owner.

**Don't use exceptions** — SDL2 doesn't use them, and the game loop can't meaningfully recover from most errors. Return error codes or booleans for fallible operations.

**Don't add virtual functions to hot-path structs.** `Player`, `Enemy`, `Bullet` — these are iterated every frame. A vtable pointer adds indirection and breaks data layout. Use free functions with switch-on-type instead.

**Don't use `std::string` for fixed names.** Dungeon names, item names — these are compile-time constants. Use `const char*` or `std::string_view`. Reserve `std::string` for user-generated or concatenated text.

---

## 5. Things to Work On

These are listed from most foundational (blocking other work) to most cosmetic.

---

### Critical — unblocks content

**Town/village/castle blueprints** (`towns.h`, `castles.h`)
All blueprint arrays are `nullptr`. The world generates placement positions but stamps magenta/orange checkerboards instead of actual content. This is the single biggest gap between what exists and a playable game. Options:
- Design hand-crafted town layouts as 2D `int` tile arrays in `towns.h`
- Or write a procedural town generator (simpler: grid of buildings with paths between them)
- See `stamp_town()` in `tilemap.cpp` for the stamping API

**Save and load**
Player stats are hardcoded in `main.cpp` every run. Add a simple binary or JSON save:
- Serialize: world seed, player stats, dungeon completion flags
- Load on startup if save file exists, otherwise generate fresh
- The world seed alone is enough to reproduce the full map deterministically — you only need to save the seed + player state

---

### High value — gameplay systems

**Multiple enemy encounter types**
`Battle` only supports a single enemy. The enemy's stats drive its fire pattern, but every battle uses the same AI. Add variety by:
- Giving each `DungeonEntranceType` its own enemy roster with distinct stat ranges
- Writing 2-3 additional fire patterns in `battle.cpp`'s enemy update logic
- The difficulty float already stored in `DungeonEntrance` should scale enemy HP/speed

**Dungeon rewards**
Completing a dungeon (stepping on `DNG_EXIT` of a connected dungeon, or clearing a solo dungeon) gives nothing. Add:
- A chest tile type (`DNG_CHEST`) that triggers a reward screen
- Item pickup that writes to `Player.stats`
- This requires a new game state (`STATE_REWARD`) or an in-dungeon UI layer

**Experience and leveling**
`Stats.exp` exists but nothing writes to it. Wire up: enemy defeat → add exp → check level threshold → apply stat gains. A simple formula: `exp_to_next = 10 * level * level`.

**Dialogue / interaction system**
NPCs, signs, and town buildings have nowhere to put text. Add a minimal dialogue state:
- `STATE_DIALOGUE` with a `DialogueBox` struct holding the speaker name and message lines
- Enter from overworld on pressing Z near an NPC tile
- Exit by pressing Z again

---

### Medium — polish and correctness

**Thread safety for dungeon entrance data**
`tilemap_build_overworld_phase2` runs on a background thread and writes to `map->dungeon_entrances[]`. The main thread reads this array in `main.cpp` when the player steps on an entrance. Add a simple flag:
```cpp
// in Tilemap:
std::atomic<bool> generation_complete{false};

// end of phase2:
generation_complete.store(true, std::memory_order_release);

// main.cpp before entrance lookup:
if (!map->generation_complete.load(std::memory_order_acquire)) { /* skip */ }
```

**Memory cleanup**
`Tilemap* map = new Tilemap()` is never deleted. `gen_thread` is never joined before exit. Fix both before the game loop ends:
```cpp
gen_thread.join();
delete map;
```

**Title screen**
`STATE_TITLE` clears to black and does nothing. Minimum viable: draw the game name and "Press Z to start", transition to `STATE_OVERWORLD` on Z.

**Minimap improvements**
The TAB minimap shows terrain but not the player's current position, dungeon locations, or towns. Add a dot for the player and icons for discovered points of interest.

---

### Low — nice to have

**Sound effects and music**
SDL2 includes `SDL_mixer` support. Add `platform_init_audio()`, load WAV files for footsteps/hits/dungeon entry, and play them from the relevant update functions.

**Pause menu**
Add `STATE_PAUSED`. On ESC (currently quits), push to paused, draw a translucent overlay with "Resume / Save / Quit". This is also where you surface the save system.

**Animated tiles**
Water, lava, and rivers could animate. The jitter system (`s_tile_jitter` in `tilemap.cpp`) is a start — extend it to cycle through 2-3 frames for liquid tiles using `tilemap_update(dt)`.

**Inventory**
A simple item array on `Player`: `ItemType items[8]` + `int item_count`. Draw it as a horizontal bar in dungeon/overworld UI. Wire to dungeon reward drops and shop NPCs.

**Enemy sprites**
`battle_draw` falls back to a colored rectangle when no enemy texture is provided. Add enemy sprite sheets per `DungeonEntranceType` — each dungeon type has a boss sprite.

---

## 6. Build Reference

```sh
make          # build game binary
make run      # build and run
make clean    # delete .o files and binary
```

**Debug build with AddressSanitizer** (catches memory errors):
```sh
g++ -Wall -Wextra -std=c++17 -Iinclude -g -fsanitize=address,undefined \
    src/*.cpp -o game_asan $(pkg-config --cflags --libs sdl2 SDL2_image) -lm -lpthread
./game_asan
```

**Debug build with symbols** (for gdb/valgrind):
```sh
g++ -Wall -Wextra -std=c++17 -Iinclude -g -O0 \
    src/*.cpp -o game_dbg $(pkg-config --cflags --libs sdl2 SDL2_image) -lm -lpthread
```

The makefile does not yet have these as targets — add them when you need them.

**The `-MMD -MP` flags** in the makefile auto-generate `.d` dependency files so that changing a header causes all files that include it to recompile. You never need to `make clean` after editing a header.

---

## 7. Quick Reference — Key Constants

| Constant | Value | File | Meaning |
|---|---|---|---|
| `MAP_WIDTH/HEIGHT` | 3000 | `tilemap.h` | Overworld tile dimensions |
| `TILE_SIZE` | 32 | `tilemap.h` | Pixels per overworld tile |
| `DMAP_W/H` | 80 | `dungeon.h` | Dungeon tile grid dimensions |
| `DMAP_TILE` | 32 | `dungeon.h` | Pixels per dungeon tile |
| `ARENA_W/H` | 640 / 480 | `battle.h` | Battle arena pixel size |
| `MAX_PLAYER_BULLETS` | 64 | `battle.h` | Bullet pool size |
| `MAX_ENEMY_BULLETS` | 256 | `battle.h` | Enemy bullet pool size |
| `PLAYER_R` | 12 | `battle.h` | Player hitbox radius (battle) |
| `ENEMY_R` | 24 | `battle.h` | Enemy hitbox radius (battle) |
| `MAX_BSP_NODES` | 127 | `dungeon.cpp` | BSP tree node limit |
| `CONNECT_RANGE` | 100 | `main.cpp` | Max tiles between linked dungeons |
