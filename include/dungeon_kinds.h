#ifndef DUNGEON_KINDS_H
#define DUNGEON_KINDS_H

#include "tilemap.h"   // DungeonEntranceType, DungeonEntrance
#include "entity.h"    // Material

// Every kind of dungeon a player can find, in ONE order from commonest to
// rarest, with how many of each a world aims to hold.
//
// A "kind" is finer than a DungeonEntranceType: a cave is one type but seven
// materials, and a player meets a stone cave and a reality-shard cave as two
// different dungeons. Rarity used to be decided in two places that could not
// see each other -- per-biome weights for the eight non-cave types in
// build_entrance_pool() (src/tilemap.cpp) and a share table for the seven
// materials in tools/oreprof.cpp -- so "a small graveyard sits between bronze
// and emerald caves" was not something either could say. This table says it,
// and both mechanisms read from it:
//
//   * ordinary placement draws a site's type with weight proportional to how
//     far each biome-native type still is from its target, so the counts
//     chase this table as far as biome area allows;
//   * cave materials are quantile bands of cave difficulty, and the band
//     widths are these targets normalised over the cave rows
//     (dungeon_cave_share, read by tools/oreprof.cpp to calibrate the cut
//     points in src/dungeon.cpp's MATERIALS);
//   * the guarantee pass at the end of placement and tools/dngcensus.cpp both
//     count kinds, not types, so "at least one of everything" and "is the
//     order right" are asked about the same fifteen things.
//
// Targets are per world. Cave rows sum to roughly the number of cave systems a
// world grows (330-380, decided by its mountains, not by this table), so a
// cave target is really a share; the non-cave rows are absolute and must sum
// below the placement loop's TARGET. Change numbers here, then run
// `make dngcensus && ./dngcensus.exe` -- it prints target against measured
// and flags any adjacent pair that came out in the wrong order.
struct DungeonKindDef {
    const char*         name;      // "stone", "grv_sm", ...; caves print as cave:<name>
    DungeonEntranceType type;
    int                 material;  // Material index for a cave row, -1 otherwise
    int                 target;    // per-world count aimed for
};

// Eight non-cave types plus seven materials.
enum { DUNGEON_KIND_COUNT = (DUNGEON_ENT_COUNT - 1) + MAT_COUNT };

extern const DungeonKindDef DUNGEON_KINDS[DUNGEON_KIND_COUNT];

// Which row an entrance record is. A cave's material is not stored on the
// record; it is derived from difficulty the same way dungeon_generate() does.
int dungeon_kind_of(const DungeonEntrance* e);
// Row for a non-cave type, or -1 for DUNGEON_ENT_CAVE (which is seven rows).
int dungeon_kind_for_type(DungeonEntranceType t);
int dungeon_kind_for_material(Material m);
// This material's target as a fraction of all cave targets: the width of its
// difficulty band.
float dungeon_cave_share(Material m);
// "cave:stone", "grv_sm", ... into buf; returns buf.
const char* dungeon_kind_label(int kind, char* buf, int n);

#endif // DUNGEON_KINDS_H
