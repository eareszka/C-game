#pragma once

constexpr int HB_X1 = 10;  // left edge
constexpr int HB_X2 = 26;  // right edge
constexpr int HB_Y1 = 32;  // top of feet
constexpr int HB_Y2 = 48;  // bottom of feet

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
// at the back of a height is one pixel across, and the feet are a box tested
// only at its four corners, so a line that thin stops you only where a corner
// lands on it. A slide is a licence to go looking for somewhere a corner does
// not, and how far it may look is exactly how thin a wall it can defeat: with
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
// and everything the cliff draws is longer than the sixteen pixels this is
// wide.
bool can_occupy(const void* map, float x, float y, TileSolidFn tile_solid);

// Move the feet by (dx, dy), each axis on its own so that a wall is slid along
// rather than stopped at, and small things in the way are stepped around.
// Returns whether they moved at all.
bool move_feet(const void* map, float* x, float* y, float dx, float dy,
               TileSolidFn tile_solid);

// If the feet are somewhere they cannot be, put them on the nearest ground they
// can. Returns whether anything moved.
bool unwedge_feet(const void* map, float* x, float* y, TileSolidFn tile_solid);
