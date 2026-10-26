#ifndef READY_H
#define READY_H

// The ready gate: the enemies a player can meet. An enemy is ready once its
// art is final enough to show, its pattern is its own (not the Unfinished
// volley or an old prototype ring) and it has been fought. Dungeons pick only
// from these (dungeon_pick_enemy), a boss site only fights a ready boss, and
// tools/enemy_tier_sheet.py tags exactly these DONE. Add an id here, and
// nowhere else, when it passes the per-enemy loop.
//
// Left out for Beta 0.1: the placeholders 65 and 89-100, and the old
// prototype patterns 13 29 31 34-38 40 41 44-49 51 52.
static const int READY_ENEMIES[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9,
    10, 11, 12,     14, 15, 16, 17, 18, 19,
    20, 21, 22, 23, 24, 25, 26, 27, 28,
    30,     32, 33,                     39,
            42, 43,
    50,         53, 54, 55, 56, 57, 58, 59,
    60, 61, 62, 63, 64,     66, 67, 68, 69,
    70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
    80, 81, 82, 83, 84, 85, 86, 87, 88,
};

inline bool enemy_ready(int id) {
    for (int r : READY_ENEMIES) if (r == id) return true;
    return false;
}

#endif
