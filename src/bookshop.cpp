#include "bookshop.h"
#include "resident.h"
#include "grandmother.h"
#include "mother.h"
#include <cmath>

const ResidentPoint BOOKSHOP_SHELF[BOOKSHOP_SHELVES] = {{235,196},{371,196},{434,308},{374,257}};

bool bookshop_shelf_taken(int shelf, int who) {
    if (who != SHOP_CLERK) {
        auto clerk = bookshop_clerk_save();
        if (clerk.stop == shelf ||
            std::hypot(clerk.x - BOOKSHOP_SHELF[shelf].x, clerk.y - BOOKSHOP_SHELF[shelf].y) < 32) return true;
    }
    if (who != SHOP_GRANDMOTHER && grandmother_reserved_shelf() == shelf) return true;
    if (who != SHOP_MOTHER && mother_reserved_shelf() == shelf) return true;
    return false;
}

bool bookshop_desk_taken(int who) {
    if (who != SHOP_GRANDMOTHER) {
        int phase = grandmother_save().phase;
        if (phase == GM_TO_DESK || phase == GM_DESK) return true;
    }
    if (who != SHOP_MOTHER && mother_at_desk()) return true;
    return false;
}
