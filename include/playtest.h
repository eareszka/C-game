#ifndef PLAYTEST_H
#define PLAYTEST_H

#include <stddef.h>
#include "battle.h"   // TrialStats

// Difficulty trials (F4 in test mode): a human run through the finished
// enemies in the sheet's order, each a timed BattleScene trial, logged to
// playtest/trials.csv for tools/playtest_report.py to rank.

// The run's enemies in sheet order: playtest/order.txt (written by
// tools/playtest_order.py: finished sprites that are also ready), or, without
// it, every ready enemy by tier then id. Returns how many.
int  playtest_order(int* ids, int max);

// The check-only run: keeps, of the n ids, those listed in
// playtest/recheck.txt (the enemies needing work: written by
// tools/playtest_report.py from each one's latest trial), in their order.
// Returns how many are left.
int  playtest_recheck(int* ids, int n);

// The run's label: today's date and the direction, e.g. 2026-10-19-fwd, and
// -chk on a check-only run (so the day's full pass doesn't count as done).
// A run is resumed by its label, so a day's pass can be played in blocks.
void playtest_run_label(char* out, size_t n, bool reverse, bool check);

// The knife a trial of enemy id fights with: the ore, oil and level a player
// has by its tier (the table in src/playtest.cpp).
TrialGear playtest_gear(int id);

// Has this run already logged a (scored) trial of enemy id?
bool playtest_logged(const char* run, int id);

// Append a finished trial: a row to playtest/trials.csv, and its hits one a
// row to playtest/hits/<run>_<id>.csv. order_index is the enemy's place in
// the forward sheet order, -1 for a warm-up (not scored).
void playtest_log(const char* run, int order_index, int id, const char* name,
                  const TrialStats& s);

#endif
