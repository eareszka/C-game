#include "core.h"
#include <SDL2/SDL.h>
#include <stdio.h>

// ---------------------------------------------------------------------------
// Bitmap font — 8x8, MSB = leftmost pixel
// ---------------------------------------------------------------------------
static const Uint8 bmp_font[][8] = {
    {0x3C,0x66,0x6E,0x76,0x66,0x66,0x3C,0x00}, // '0'
    {0x18,0x38,0x18,0x18,0x18,0x18,0x7E,0x00}, // '1'
    {0x3C,0x66,0x06,0x0C,0x18,0x30,0x7E,0x00}, // '2'
    {0x3C,0x66,0x06,0x1C,0x06,0x66,0x3C,0x00}, // '3'
    {0x0E,0x1E,0x36,0x66,0x7F,0x06,0x06,0x00}, // '4'
    {0x7E,0x60,0x7C,0x06,0x06,0x66,0x3C,0x00}, // '5'
    {0x1C,0x30,0x60,0x7C,0x66,0x66,0x3C,0x00}, // '6'
    {0x7E,0x66,0x0C,0x18,0x18,0x18,0x18,0x00}, // '7'
    {0x3C,0x66,0x66,0x3C,0x66,0x66,0x3C,0x00}, // '8'
    {0x3C,0x66,0x66,0x3E,0x06,0x0C,0x38,0x00}, // '9'
    {0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00}, // 'F' (index 10)
    {0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00}, // 'P' (index 11) — same shape, kept separate for clarity
    {0x3C,0x66,0x60,0x3C,0x06,0x66,0x3C,0x00}, // 'S' (index 12)
    {0x00,0x18,0x18,0x00,0x18,0x18,0x00,0x00}, // ':' (index 13)
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // ' ' (index 14)
};

// Lookup: ASCII char → index into bmp_font, or -1 if unsupported
static int font_index(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c == 'F') return 10;
    if (c == 'P') return 11;
    if (c == 'S') return 12;
    if (c == ':') return 13;
    if (c == ' ') return 14;
    return -1;
}

// Draw one character at (x, y); each bit pixel is SCALE×SCALE screen pixels
static void draw_char(SDL_Renderer* r, char c, int x, int y, int scale) {
    int idx = font_index(c);
    if (idx < 0) return;
    const Uint8* glyph = bmp_font[idx];
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (glyph[row] & (0x80u >> col)) {
                SDL_Rect px = { x + col * scale, y + row * scale, scale, scale };
                SDL_RenderFillRect(r, &px);
            }
        }
    }
}

void draw_fps(SDL_Renderer* renderer, float dt) {
    static float acc         = 0.0f;
    static int   frames      = 0;
    static int   display_fps = 0;

    acc += dt;
    frames++;
    if (acc >= 0.5f) {           // update display twice per second
        display_fps = (int)(frames / acc + 0.5f);
        frames = 0;
        acc    = 0.0f;
    }

    char buf[16];
    SDL_snprintf(buf, sizeof(buf), "FPS:%d", display_fps);

    const int SCALE = 2;           // 2×2 pixels per bit → 16px tall characters
    const int CHAR_W = 8 * SCALE;
    const int X = 4, Y = 4;

    // Dark shadow one pixel down-right for legibility over any background
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    for (int i = 0; buf[i]; i++)
        draw_char(renderer, buf[i], X + 1 + i * CHAR_W, Y + 1, SCALE);

    // Bright yellow text
    SDL_SetRenderDrawColor(renderer, 255, 220, 0, 255);
    for (int i = 0; buf[i]; i++)
        draw_char(renderer, buf[i], X + i * CHAR_W, Y, SCALE);
}

double time_delta_seconds(void) {
    static Uint64 prev = 0;

    if (prev == 0) {
        prev = SDL_GetPerformanceCounter();
        return 0.0;
    }

    Uint64 now = SDL_GetPerformanceCounter();
    double dt = (double)(now - prev) / (double)SDL_GetPerformanceFrequency();
    prev = now;
    return dt;
}
