#pragma once
#include "resident_path.h"
// Town 0's book shop (room 1): where the clerk and the shoppers stand, and
// the two questions every one of them asks before stepping up, so no two
// ever share a shelf or the desk. Sprite origins in room pixels.
constexpr int BOOKSHOP_ROOM = 1, BOOKSHOP_SHELVES = 4;
extern const ResidentPoint BOOKSHOP_SHELF[BOOKSHOP_SHELVES];
constexpr ResidentPoint BOOKSHOP_DESK = {293, 292};    // before the owner's counter
// Waiting for the desk: a step back from it and a sprite's width to the
// side (the floor ends a step behind the desk), in line behind whoever has it.
constexpr ResidentPoint BOOKSHOP_QUEUE = {325, 312};
enum BookshopWho { SHOP_CLERK, SHOP_GRANDMOTHER, SHOP_MOTHER };
// Someone other than `who` is at that shelf or on the way to it.
bool bookshop_shelf_taken(int shelf, int who);
// Someone other than `who` is at the desk or on the way to it.
bool bookshop_desk_taken(int who);
