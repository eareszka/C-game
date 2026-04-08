# C++ Guide for Four Castle Chronicles

The key insight for games: **C++ OOP is most useful at system boundaries, not everywhere**.

---

## The core pattern: structs with methods

Right now you have this C pattern:
```c
void battle_update(Battle* b, const Input* in, float dt);
```

In C++ you move the function inside the struct:
```cpp
struct Battle {
    // ... data ...
    void update(const Input& in, float dt);
    void draw(SDL_Renderer* ren) const;
};

// call site becomes:
battle.update(in, dt);
```

Same thing happening, better to read and reason about.

---

## What to convert first (high value)

**1. Entity stats — add a constructor so you never have uninitialized data**
```cpp
struct Stats {
    int max_hp, hp;
    int max_spd, spd;
    // ...

    Stats() : max_hp(0), hp(0), max_spd(0), spd(0) {} // zero by default
    Stats(int hp, int spd, int attack, int mag, int luck, int iq);
};
```
This kills the `= {0}` pattern and the `-Wmissing-field-initializers` warnings.

**2. ResourceNodeList — replace fixed array with `std::vector`**
```cpp
#include <vector>

struct ResourceNodeList {
    std::vector<ResourceNode> nodes;  // was: ResourceNode nodes[128]; int count;

    void add(ResourceType type, float x, float y);
    void draw(const Camera& cam, SDL_Renderer* ren, SDL_Texture* atlas) const;
    int try_hit(float player_x, float player_y, int range);
};
```
No more `MAX_RESOURCE_NODES` cap. No more `list->count` bookkeeping.

**3. BattleLog — `std::string` + `std::deque`**
```cpp
#include <string>
#include <deque>

struct BattleLog {
    std::deque<std::string> lines;
    static constexpr int MAX_LINES = 2;

    void write(const std::string& msg) {
        lines.push_back(msg);
        if (lines.size() > MAX_LINES) lines.pop_front();
    }
};
```
No more `strncpy`, no more fixed buffer, no more off-by-one risk.

---

## What NOT to convert

- **Enums** — `BattlePhase`, `GameState`, `Direction` are fine as-is. Optionally use `enum class` for stronger typing.
- **Camera, Tileset, Platform** — tiny POD structs, leave them alone.
- **`qsort` for turn order** — replace with `std::sort` (cleaner), but low priority.
- **`SDL_Renderer*`, `SDL_Texture*`** — don't wrap SDL handles in RAII unless you want the practice; the manual cleanup in `main` is fine.

---

## The one C++ feature that pays immediately: references

Replace pointer parameters with references where the pointer is never null:
```cpp
// C style — caller has to wonder: can this be null?
void overworld_update(Overworld* ow, const Input* in, float dt, ResourceNodeList* resources);

// C++ style — clear contract, no null checks needed
void update(const Input& in, float dt, ResourceNodeList& resources);
```

Use `const T&` for read-only params, `T&` for params you modify, raw `T*` only when null is genuinely possible.

---

## Suggested migration order

1. Add constructors to `Stats`, `Player`, `Enemy` — fixes warnings, establishes the habit
2. Move `battle_*` functions into `Battle` as methods
3. Convert `ResourceNodeList` to use `std::vector`
4. Move `overworld_*` into `Overworld` as methods
5. Replace `BattleLog` char arrays with `std::string`/`std::deque`

Each step is self-contained and the game stays buildable throughout.
