#ifndef FC_PALETTE_H
#define FC_PALETTE_H

// The game's palette: FC World's 64 colours, and nothing else on screen.
//
// The art is put on it offline (tools/palette_pass.py). These are the same
// rules for the colours the code makes up at run time -- a UI panel, a
// minimap dot, a flat fallback tile -- so that a colour typed into the source
// cannot bring back the 16-bit look the art was taken off. fc_snap() sends any
// colour where the art's own table sends it: the table is generated from
// art/direction/fcremap.py into src/fc_palette_lut.inc, so there is one
// mapping, not a C++ copy of it.
//
// Effects that would blend (a wash, a dim) are dithers instead: fc_bayer()
// picks which pixels of an area take a palette colour, so every pixel is still
// exactly one of the 64.

#include <SDL2/SDL.h>
#include <stdint.h>

SDL_Color fc_snap(uint8_t r, uint8_t g, uint8_t b);

// SDL_SetRenderDrawColor, on the palette. Alpha passes through.
int fc_draw_color(SDL_Renderer* ren, uint8_t r, uint8_t g, uint8_t b, uint8_t a);

// 4x4 ordered-dither rank of a pixel, 0..15. A dither at k/16 covers the
// pixels whose rank is below k; two dithers over disjoint rank ranges never
// cover the same pixel, which is how storeys of haze stack.
static inline int fc_bayer(int x, int y) {
    static const uint8_t M[4][4] = { { 0,  8,  2, 10 },
                                     { 12, 4, 14,  6 },
                                     { 3, 11,  1,  9 },
                                     { 15, 7, 13,  5 } };
    return M[y & 3][x & 3];
}

#endif
