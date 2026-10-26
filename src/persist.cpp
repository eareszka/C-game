#include "persist.h"
#include <mutex>
#include <unordered_map>
#include <unordered_set>
#include <vector>

static std::mutex s_lock;
static std::unordered_set<uint32_t> s_tiles;
static uint64_t s_oilblooms = 0;
static std::unordered_map<uint32_t, DungeonDeadRecord> s_dungeons;

void persist_clear(void) {
    std::lock_guard<std::mutex> g(s_lock);
    s_tiles.clear();
    s_oilblooms = 0;
    s_dungeons.clear();
}

void persist_tile_add(uint32_t key) {
    std::lock_guard<std::mutex> g(s_lock);
    s_tiles.insert(key);
}
bool persist_tile_has(uint32_t key) {
    std::lock_guard<std::mutex> g(s_lock);
    return s_tiles.count(key) != 0;
}
void persist_tiles_each(void (*fn)(uint32_t key, void* ctx), void* ctx) {
    std::lock_guard<std::mutex> g(s_lock);
    for (uint32_t k : s_tiles) fn(k, ctx);
}

void persist_oilbloom_add(int site) {
    if (site < 0 || site >= 64) return;
    std::lock_guard<std::mutex> g(s_lock);
    s_oilblooms |= 1ull << site;
}
bool persist_oilbloom_has(int site) {
    if (site < 0 || site >= 64) return false;
    std::lock_guard<std::mutex> g(s_lock);
    return (s_oilblooms >> site) & 1;
}

static DungeonDeadRecord& record(uint32_t seed) {
    DungeonDeadRecord& r = s_dungeons[seed];
    r.seed = seed;
    return r;
}
void persist_spawner_beaten(uint32_t dungeon_seed, int spawner) {
    if (spawner < 0 || spawner >= 64) return;
    std::lock_guard<std::mutex> g(s_lock);
    record(dungeon_seed).spawners |= 1ull << spawner;
}
void persist_node_broken(uint32_t dungeon_seed, int node) {
    if (node < 0 || node >= 64) return;
    std::lock_guard<std::mutex> g(s_lock);
    record(dungeon_seed).nodes |= 1ull << node;
}
DungeonDeadRecord persist_dungeon(uint32_t dungeon_seed) {
    std::lock_guard<std::mutex> g(s_lock);
    auto it = s_dungeons.find(dungeon_seed);
    return it == s_dungeons.end() ? DungeonDeadRecord{ dungeon_seed, 0, 0, 0 } : it->second;
}

bool persist_write(FILE* f) {
    std::lock_guard<std::mutex> g(s_lock);
    std::vector<uint32_t> tiles(s_tiles.begin(), s_tiles.end());
    std::vector<DungeonDeadRecord> dungeons;
    for (const auto& kv : s_dungeons) dungeons.push_back(kv.second);
    uint32_t nt = (uint32_t)tiles.size(), nd = (uint32_t)dungeons.size();
    bool ok = fwrite(&nt, sizeof(nt), 1, f) == 1;
    if (nt) ok = fwrite(tiles.data(), sizeof(uint32_t), nt, f) == nt && ok;
    ok = fwrite(&s_oilblooms, sizeof(s_oilblooms), 1, f) == 1 && ok;
    ok = fwrite(&nd, sizeof(nd), 1, f) == 1 && ok;
    if (nd) ok = fwrite(dungeons.data(), sizeof(DungeonDeadRecord), nd, f) == nd && ok;
    return ok;
}

bool persist_read(FILE* f) {
    // Bounds well past anything a world can hold: a bad count is a bad file.
    const uint32_t MAX_TILES = 3000u * 3000u, MAX_DUNGEONS = 1u << 20;
    uint32_t nt = 0, nd = 0;
    uint64_t oil = 0;
    if (fread(&nt, sizeof(nt), 1, f) != 1 || nt > MAX_TILES) return false;
    std::vector<uint32_t> tiles(nt);
    if (nt && fread(tiles.data(), sizeof(uint32_t), nt, f) != nt) return false;
    if (fread(&oil, sizeof(oil), 1, f) != 1) return false;
    if (fread(&nd, sizeof(nd), 1, f) != 1 || nd > MAX_DUNGEONS) return false;
    std::vector<DungeonDeadRecord> dungeons(nd);
    if (nd && fread(dungeons.data(), sizeof(DungeonDeadRecord), nd, f) != nd) return false;
    std::lock_guard<std::mutex> g(s_lock);
    s_tiles = std::unordered_set<uint32_t>(tiles.begin(), tiles.end());
    s_oilblooms = oil;
    s_dungeons.clear();
    for (const DungeonDeadRecord& r : dungeons) s_dungeons[r.seed] = r;
    return true;
}
