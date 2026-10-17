#include "save.h"
#include "legacy_player_v2.h"
#include "legacy_player_v3.h"
#include "legacy_player_v4.h"
#include "crafting.h"
#include "dungeon.h"   // the dungeons' chests (dungeon_chest_records)
#include "story.h"     // the story's flags (story_flags)
#include "resident.h"
#include "grandmother.h"
#include "fisher.h"
#include "woodcutter.h"
#include "battle.h"     // migrate the old white-flash timer to appearance timing
#include <stddef.h>
#include <stdio.h>
#include <string.h>

static const char* SAVE_PATH = "save.dat";
static const char* SAVE_TMP  = "save.tmp";
enum { SAVE_VERSION = 13 };

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
using InventorySaveFile = SaveRecord<LegacyPlayerV3>;
using PoisonSaveFile = SaveRecord<LegacyPlayerV4>;
static_assert(offsetof(Player, footwear) == sizeof(LegacyPlayerV4), "V4 player prefix must stay intact");
static_assert(offsetof(Player, poisoned) == sizeof(LegacyPlayerV3), "V3 player prefix must stay intact");
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
    ResidentSave resident = resident_save();
    ok = fwrite(&resident, sizeof(resident), 1, f) == 1 && ok;
    BookshopClerkSave clerk=bookshop_clerk_save();
    ok = fwrite(&clerk,sizeof(clerk),1,f)==1 && ok;
    GrandmotherSave grandmother=grandmother_save();
    ok = fwrite(&grandmother,sizeof(grandmother),1,f)==1 && ok;
    WoodcutterSave woodcutter=woodcutter_save();
    ok = fwrite(&woodcutter,sizeof(woodcutter),1,f)==1 && ok;
    FisherSave fisher=fisher_save();
    ok = fwrite(&fisher,sizeof(fisher),1,f)==1 && ok;
    ok = fclose(f) == 0 && ok;
    if (!ok) { remove(SAVE_TMP); return false; }
    remove(SAVE_PATH);   // rename does not replace on Windows
    return rename(SAVE_TMP, SAVE_PATH) == 0;
}

template<class P> static bool read_record(FILE* f, SaveRecord<P>& s, bool legacy, bool extended = false) {
    using R = SaveRecord<P>;
    memset(&s,0,sizeof(s));
    size_t got = fread(&s,1,sizeof(s),f);
    const size_t first=(offsetof(R,landmarks)+3)&~(size_t)3;
    const size_t landmarks=(offsetof(R,landmarks)+MAX_LANDMARKS/8+3)&~(size_t)3;
    const size_t chests=offsetof(R,story);
    if ((!extended && fgetc(f)!=EOF) || !(got==sizeof(s) || (legacy && (got==first || got==landmarks || got==chests)))) return false;
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
    ResidentSave resident = {};
    BookshopClerkSave clerk = {};
    GrandmotherSave grandmother = {};
    WoodcutterSave woodcutter = {};
    FisherSave fisher = {};
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
    } else if (valid && header.version==3 && header.player_size==sizeof(LegacyPlayerV3)) {
        static InventorySaveFile old;
        valid=read_record(f,old,false);
        if (valid) {
            memcpy(&s.player,&old.player,sizeof(old.player));
            s.seed=old.seed; s.x=old.x; s.y=old.y;
            memcpy(s.explored,old.explored,sizeof(s.explored));
            memcpy(s.landmarks,old.landmarks,sizeof(s.landmarks));
            memcpy(s.dungeon_chests,old.dungeon_chests,sizeof(s.dungeon_chests));
            s.story=old.story;
        }
    } else if (valid && header.version==4 && header.player_size==sizeof(LegacyPlayerV4)) {
        static PoisonSaveFile old;
        valid=read_record(f,old,false);
        if (valid) {
            memcpy(&s.player,&old.player,sizeof(old.player));
            s.player.footwear = item_count(&s.player,ITEM_SWIFT_BOOTS)>0;
            s.seed=old.seed; s.x=old.x; s.y=old.y;
            memcpy(s.explored,old.explored,sizeof(s.explored));
            memcpy(s.landmarks,old.landmarks,sizeof(s.landmarks));
            memcpy(s.dungeon_chests,old.dungeon_chests,sizeof(s.dungeon_chests));
            s.story=old.story;
        }
    } else if (valid && header.version==5 && header.player_size==sizeof(Player)) {
        valid=read_record(f,s,false);
    } else if (valid && header.version>=6 && header.version<=SAVE_VERSION && header.player_size==sizeof(Player)) {
        // Version 6's footer ends immediately before the kitchen waypoint.
        const size_t size = header.version==6 ? offsetof(ResidentSave,kitchen_leg) :
                            header.version<9 ? offsetof(ResidentSave,transition_frame) : sizeof(resident);
        valid=read_record(f,s,false,true) && fread(&resident,size,1,f)==1;
        if(valid && header.version>=10)valid=fread(&clerk,sizeof(clerk),1,f)==1;
        if(valid && header.version>=11)valid=fread(&grandmother,sizeof(grandmother),1,f)==1;
        if(valid && header.version>=12)valid=fread(&woodcutter,sizeof(woodcutter),1,f)==1;
        if(valid && header.version>=13)valid=fread(&fisher,sizeof(fisher),1,f)==1;
        valid=valid && fgetc(f)==EOF;
        // V7's final four bytes were padding, not a saved pause timer.
        if(header.version<8) resident.kitchen_pause=0;
        if(header.version<9) resident.flash=resident.flash / ACTOR_FLASH_STEP * ACTOR_APPEAR_T;
    } else valid=false;
    fclose(f);
    if (!valid || s.player.equipped < 0 || s.player.equipped >= WEAPON_COUNT) return false;
    if(header.version>=10 && !bookshop_clerk_valid(clerk))return false;
    if(header.version>=11 && !grandmother_valid(grandmother))return false;
    if(header.version>=12 && !woodcutter_valid(woodcutter))return false;
    if(header.version>=13 && (!fisher_valid(fisher)||fisher.epoch>resident.world_seconds))return false;
    if (header.version>=6) {
        if (!resident_restore(resident)) return false;
    } else resident_reset();
    if(header.version>=10)bookshop_clerk_restore(clerk);
    if(header.version>=11)grandmother_restore(grandmother);
    if(header.version>=12)woodcutter_restore(woodcutter);
    if(header.version>=13)fisher_restore(fisher);
    *seed=s.seed; *x=s.x; *y=s.y; *p=s.player;
    int snapshot[ITEM_COUNT]={}; items_note_gains(p,snapshot,true);
    if (!item_footwear_equipped(p,ITEM_SWIFT_BOOTS) && !item_footwear_equipped(p,ITEM_DIVING_FINS)) p->footwear=FOOTWEAR_NONE;
    memcpy(explored,s.explored,sizeof(s.explored));
    memcpy(tilemap_landmarks_opened(),s.landmarks,sizeof(s.landmarks));
    memcpy(dungeon_chest_records(),s.dungeon_chests,sizeof(s.dungeon_chests));
    *story_flags()=s.story;
    return true;
}
