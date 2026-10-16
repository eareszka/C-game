#include "save.h"
#include "legacy_player_v2.h"
#include "crafting.h"
#include "dungeon.h"   // the dungeons' chests (dungeon_chest_records)
#include "story.h"     // the story's flags (story_flags)
#include <stddef.h>
#include <stdio.h>
#include <string.h>

static const char* SAVE_PATH = "save.dat";
static const char* SAVE_TMP  = "save.tmp";
enum { SAVE_VERSION = 3 };

template<class P> struct SaveRecord {
    char     magic[4];     // "FCC1"
    unsigned version;
    unsigned player_size;  // sizeof(Player): a changed Player is another version
    unsigned seed;
    float    x, y;
    P        player;
    uint8_t  explored[EXPLORE_H][EXPLORE_W];
    // Added after the first saves were written, and so last: the landmarks
    // whose cache has been opened (tilemap_landmarks_opened). A save that ends
    // before it is one from before there were landmarks, and is read as none
    // opened -- never refused.
    uint8_t  landmarks[MAX_LANDMARKS / 8];
    // And after them, the same way: which chests of which dungeons have been
    // opened (dungeon_chest_records). Before it, read as none.
    DungeonChestRecord dungeon_chests[MAX_DUNGEON_CHEST_RECORDS];
    // And after them: the story's flags (story_flags). Before it, a fresh story.
    StoryFlags story;
};
using SaveFile = SaveRecord<Player>;
using LegacySaveFile = SaveRecord<LegacyPlayerV2>;
static_assert(offsetof(Player, extra_items) == sizeof(LegacyPlayerV2), "V2 player prefix must stay intact");

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
    memcpy(s.landmarks, tilemap_landmarks_opened(), sizeof(s.landmarks));
    memcpy(s.dungeon_chests, dungeon_chest_records(), sizeof(s.dungeon_chests));
    s.story = *story_flags();
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

template<class P> static bool read_record(FILE* f, SaveRecord<P>& s, bool legacy) {
    using R = SaveRecord<P>;
    memset(&s,0,sizeof(s));
    size_t got = fread(&s,1,sizeof(s),f);
    const size_t first=(offsetof(R,landmarks)+3)&~(size_t)3;
    const size_t landmarks=(offsetof(R,landmarks)+MAX_LANDMARKS/8+3)&~(size_t)3;
    const size_t chests=offsetof(R,story);
    if (fgetc(f)!=EOF || !(got==sizeof(s) || (legacy && (got==first || got==landmarks || got==chests)))) return false;
    if (got < landmarks) memset(s.landmarks,0,sizeof(s.landmarks));
    if (got < chests) memset(s.dungeon_chests,0,sizeof(s.dungeon_chests));
    if (got != sizeof(s)) memset(&s.story,0,sizeof(s.story));
    return true;
}
bool save_read(unsigned* seed, float* x, float* y, Player* p,
               uint8_t explored[EXPLORE_H][EXPLORE_W]) {
    FILE* f=fopen(SAVE_PATH,"rb");
    if (!f) return false;
    struct Header { char magic[4]; unsigned version, player_size; } header;
    bool valid=fread(&header,sizeof(header),1,f)==1 && memcmp(header.magic,"FCC1",4)==0;
    rewind(f);
    static SaveFile s;
    memset(&s,0,sizeof(s));
    if (valid && header.version==2 && header.player_size==sizeof(LegacyPlayerV2)) {
        static LegacySaveFile old;
        valid=read_record(f,old,true);
        if (valid) {
            memcpy(&s.player,&old.player,sizeof(old.player));
            s.seed=old.seed; s.x=old.x; s.y=old.y;
            memcpy(s.explored,old.explored,sizeof(s.explored));
            memcpy(s.landmarks,old.landmarks,sizeof(s.landmarks));
            memcpy(s.dungeon_chests,old.dungeon_chests,sizeof(s.dungeon_chests));
            s.story=old.story;
        }
    } else if (valid && header.version==SAVE_VERSION && header.player_size==sizeof(Player)) {
        valid=read_record(f,s,false);
    } else valid=false;
    fclose(f);
    if (!valid || s.player.equipped < 0 || s.player.equipped >= WEAPON_COUNT) return false;
    *seed=s.seed; *x=s.x; *y=s.y; *p=s.player;
    int snapshot[ITEM_COUNT]={}; items_note_gains(p,snapshot,true);
    memcpy(explored,s.explored,sizeof(s.explored));
    memcpy(tilemap_landmarks_opened(),s.landmarks,sizeof(s.landmarks));
    memcpy(dungeon_chest_records(),s.dungeon_chests,sizeof(s.dungeon_chests));
    *story_flags()=s.story;
    return true;
}
