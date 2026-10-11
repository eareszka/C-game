#pragma once

// The feet: the boots of the sprite, twelve world pixels square at the bottom
// of the 28x40 frame, which the ground is asked about at every art pixel along
// the edge -- seven samples a side (HB_SAMPLE below).
//
// Twelve, not the sixteen it was, because the cliffs draw ground narrower than
// that and mean it to be walked. Mother 1's landforms put two flanks half a
// tile apart with the back line dipping between them, and hang a flank's foot
// or a notch's line straight over the teeth of a front: a strip of open ground
// eight art pixels across in the one case and eight to twelve tall in the
// other, drawn inside the wall sprites, plainly ground, and walled off by feet
// that took nine. The narrowest strip the drawings make is that half-tile
// slot, eight of the art's pixels; the boots are six and pass it with a pixel
// to spare. Every landform in the library is measured against this box by
// tools/gen_islands.py (FEET), and the two must agree.
constexpr int HB_X1 = 8;   // left edge   (the feet: bottom centre of the 28x40 frame)
constexpr int HB_X2 = 20;  // right edge
constexpr int HB_Y1 = 28;  // top of feet
constexpr int HB_Y2 = 40;  // bottom of feet

// How far across the way the feet will be slid to get past something small in
// front of them. Two world pixels, which is exactly one of the art's, and that
// exactness is the whole of why it is two.
//
// Read off one measurement alone this wants to be as wide as it will go.
// Pressed against a face and walking along it, on a window of seed 99, the
// share of steps refused runs 29-37% with no slide at all, 11-15% at one pixel
// of the art, 5-8% at two and 3.5-5.7% at three.
//
// The other measurement says one pixel and not a fraction more. The beaded line
// at the back of a height is one pixel across, and when the feet were a box
// tested only at its four corners a line that thin stopped you only where a
// corner landed on it. A slide is a licence to go looking for somewhere a
// corner does not, and how far it may look is exactly how thin a wall it can
// defeat: with
// the plateau top reachable from open country 0.1% of the time at a slide of
// one pixel and 94% at two, walking a pixel a frame. There is no curve there to
// trade along — the line is a wall or it is not.
//
// Three world pixels is not a compromise between the two, because the ground is
// asked in art pixels and floors what it is given: a three-pixel offset lands
// on one art pixel or on two depending on where in the tile it starts, so it
// buys half the smoothness of two and leaks half the time. Two is the largest
// that cannot.
constexpr int HB_SLIP = 2;

// How finely the feet are felt out, and how far they are allowed to travel
// between one test and the next. Two world pixels, which is one of the art's —
// the finest the ground is drawn at, and so the finest there is anything to
// find.
constexpr float HB_SAMPLE = 2.0f;

using TileSolidFn = bool (*)(const void* map, float px, float py);

// Whether the feet fit here: nothing solid anywhere around the box.
//
// Around, rather than at its four corners, which is what this was. Four corners
// is enough for as long as everything solid is a tile thick, and the cliff
// stopped being that: the drop at the back of a height is a beaded line one art
// pixel across, and a line that thin lies between two corners far more often
// than it lies on one. Walked at, it was not there at all about a fifth of the
// time, and sprinted at, three fifths.
//
// The box only — an obstacle that crosses it has to cross the edge to get in,
// and everything the cliff draws is longer than the twelve pixels this is
// wide.
bool can_occupy(const void* map, float x, float y, TileSolidFn tile_solid);

// Move the feet by (dx, dy), each axis on its own so that a wall is slid along
// rather than stopped at, and small things in the way are stepped around.
// Returns whether they moved at all.
bool move_feet(const void* map, float* x, float* y, float dx, float dy,
               TileSolidFn tile_solid);

// A door, ladder or cave mouth is taken by walking into it, not by standing
// near it: the feet's centre (cx, cy) inside its opening -- WAY_INSET in from
// each side of its tile, clear of the frame -- and the feet pressed against
// what it stands on, solid within WAY_REACH pixels of their (dx, dy) side.
// WAY_REACH is more than a sprinting frame's step, which is how far short of
// a wall a blocked move can leave the feet.
constexpr float WAY_INSET = 6.0f, WAY_REACH = 6.0f;
inline bool way_opening(float local) { return local >= WAY_INSET && local <= 32.0f - WAY_INSET; }
inline bool feet_walked_into(const void* map, float cx, float cy, int dx, int dy,
                             TileSolidFn tile_solid) {
    // That side's middle and both its corners: a wall on the slant (a room's
    // side walls) meets a corner first, and is never nearer the middle.
    float h = (HB_X2 - HB_X1) * 0.5f, r = h + WAY_REACH;
    for (int s = -1; s <= 1; s++)
        if (tile_solid(map, cx + dx * r + dy * s * h, cy + dy * r + dx * s * h)) return true;
    return false;
}

// Where to stand on arriving through a way: from (cx, cy) on it, the first
// place straight out of it along (dx, dy) -- else down the screen, to either
// side, up -- where the feet fit and no longer take it: before the door, a
// pixel clear of it. taken and fits are asked of a feet centre. False, and
// nothing moved, if there is none within a tile and a half.
template <class Taken, class Fits>
bool stand_clear(float* cx, float* cy, int dx, int dy, Taken taken, Fits fits) {
    const int dirs[5][2] = { { dx, dy }, { 0, 1 }, { -1, 0 }, { 1, 0 }, { 0, -1 } };
    for (const auto& d : dirs)
        for (int n = 1; n <= 48; n++) {
            float x = *cx + d[0] * n, y = *cy + d[1] * n;
            if (!fits(x, y) || taken(x, y)) continue;
            *cx = x; *cy = y;
            return true;
        }
    return false;
}

// If the feet are somewhere they cannot be, put them on the nearest ground they
// can. Returns whether anything moved.
bool unwedge_feet(const void* map, float* x, float* y, TileSolidFn tile_solid);
