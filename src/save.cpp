#include "save.h"
#include <stdio.h>
#include <string.h>

static const char* SAVE_PATH = "save.dat";
static const char* SAVE_TMP  = "save.tmp";
enum { SAVE_VERSION = 2 };

struct SaveFile {
    char     magic[4];     // "FCC1"
    unsigned version;
    unsigned player_size;  // sizeof(Player): a changed Player is another version
    unsigned seed;
    float    x, y;
    Player   player;
    uint8_t  explored[EXPLORE_H][EXPLORE_W];
};

bool save_write(unsigned seed, float x, float y, const Player& p,
                const uint8_t explored[EXPLORE_H][EXPLORE_W]) {
    static SaveFile s;
    memset(&s, 0, sizeof(s));
    memcpy(s.magic, "FCC1", 4);
    s.version = SAVE_VERSION;
    s.player_size = (unsigned)sizeof(Player);
    s.seed = seed;
    s.x = x;
    s.y = y;
    s.player = p;
    memcpy(s.explored, explored, sizeof(s.explored));
    // To one side first, then over the old save: a crash mid-write leaves
    // the old one whole.
    FILE* f = fopen(SAVE_TMP, "wb");
    if (!f) return false;
    bool ok = fwrite(&s, sizeof(s), 1, f) == 1;
    ok = fclose(f) == 0 && ok;
    if (!ok) { remove(SAVE_TMP); return false; }
    remove(SAVE_PATH);   // rename does not replace on Windows
    return rename(SAVE_TMP, SAVE_PATH) == 0;
}

bool save_read(unsigned* seed, float* x, float* y, Player* p,
               uint8_t explored[EXPLORE_H][EXPLORE_W]) {
    FILE* f = fopen(SAVE_PATH, "rb");
    if (!f) return false;
    static SaveFile s;
    bool ok = fread(&s, sizeof(s), 1, f) == 1 && fgetc(f) == EOF;
    fclose(f);
    if (!ok || memcmp(s.magic, "FCC1", 4) != 0 || s.version != SAVE_VERSION ||
        s.player_size != sizeof(Player))
        return false;
    // Whatever else, never an equipped weapon outside the arsenal.
    if ((int)s.player.equipped < 0 || (int)s.player.equipped >= WEAPON_COUNT) return false;
    *seed = s.seed;
    *x = s.x;
    *y = s.y;
    *p = s.player;
    memcpy(explored, s.explored, sizeof(s.explored));
    return true;
}
