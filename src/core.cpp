#include "fc_palette.h"
#include "core.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>

// The game's font: Pixuf (art/fonts/Pixuf.ttf), baked by tools/gen_font.py --
// printable ASCII, 8 rows a glyph, proportional. Anything else draws nothing.
#include "font.inc"

static int char_adv(char c) {
    int i = (int)(unsigned char)c - FONT_FIRST;
    return i < 0 || i > FONT_LAST - FONT_FIRST ? 0 : FONT_ADV[i];
}

static void draw_char(SDL_Renderer* r, char c, int x, int y, int scale) {
    int idx = (int)(unsigned char)c - FONT_FIRST;
    if (idx < 0 || idx > FONT_LAST - FONT_FIRST) return;
    const Uint8* glyph = FONT_ROWS[idx];
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (glyph[row] & (0x80u >> col)) {
                SDL_Rect px = { x + col * scale, y + row * scale, scale, scale };
                SDL_RenderFillRect(r, &px);
            }
        }
    }
}

// Draw a string, each letter its own width. scale=1 → 8px tall, scale=2 → 16px tall.
void draw_text(SDL_Renderer* ren, const char* text, int x, int y, int scale,
               Uint8 r, Uint8 g, Uint8 b) {
    // Shadow one of its own pixels down-right: whole pixels, as the art's
    fc_draw_color(ren, 0, 0, 0, 255);
    for (int i = 0, cx = x; text[i]; cx += char_adv(text[i++]) * scale)
        draw_char(ren, text[i], cx + scale, y + scale, scale);
    // Main colour
    fc_draw_color(ren, r, g, b, 255);
    for (int i = 0, cx = x; text[i]; cx += char_adv(text[i++]) * scale)
        draw_char(ren, text[i], cx, y, scale);
}

// Returns the pixel width of a string at the given scale.
int text_width(const char* text, int scale) {
    int w = 0;
    for (; *text; text++) w += char_adv(*text);
    return w * scale;
}

// A rect with its corners stepped in by two 2px stairs, the reference's
// round corner at the game's 2x pixel.
static void fill_rounded(SDL_Renderer* ren, int x, int y, int w, int h) {
    SDL_Rect band[5] = {
        { x + 4, y,         w - 8, 2     },
        { x + 2, y + 2,     w - 4, 2     },
        { x,     y + 4,     w,     h - 8 },
        { x + 2, y + h - 4, w - 4, 2     },
        { x + 4, y + h - 2, w - 8, 2     },
    };
    SDL_RenderFillRects(ren, band, 5);
}

void draw_nes_panel(SDL_Renderer* ren, int x, int y, int w, int h, Uint8 r, Uint8 g, Uint8 b) {
    fc_draw_color(ren, 0, 0, 0, 255);
    fill_rounded(ren, x - 2, y - 2, w + 4, h + 4);     // the black edge
    fc_draw_color(ren, r, g, b, 255);
    fill_rounded(ren, x, y, w, h);
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect inner = {x + 4, y + 4, w - 8, h - 8};
    SDL_RenderFillRect(ren, &inner);
    // The frame rounds on the inside too: two stairs into each inner corner.
    fc_draw_color(ren, r, g, b, 255);
    int L = x + 4, R = x + w - 4, T = y + 4, B = y + h - 4;
    SDL_Rect fill[8] = {
        { L,     T,     4, 2 }, { L,     T + 2, 2, 2 },
        { R - 4, T,     4, 2 }, { R - 2, T + 2, 2, 2 },
        { L,     B - 2, 4, 2 }, { L,     B - 4, 2, 2 },
        { R - 4, B - 2, 4, 2 }, { R - 2, B - 4, 2, 2 },
    };
    SDL_RenderFillRects(ren, fill, 8);
}

// Wrapped at words into lines max_px wide at scale; a word wider than that
// is cut, and '\n' always breaks (hard[i], if given, marks the lines that
// ended on one). out is max_lines rows of stride bytes; the count is returned.
static int wrap_lines(const char* text, int max_px, int scale, int stride, char* out, int max_lines,
                      bool* hard = nullptr) {
    int n = 0;
    for (const char* s = text; *s && n < max_lines; ) {
        while (*s == ' ') s++;
        // as much as fits; short of the end, back to the last whole word
        int len = 0, word_end = 0, w = 0;
        while (s[len] && s[len] != '\n' && len < stride - 1) {
            int a = char_adv(s[len]) * scale;
            if (w + a > max_px) break;
            w += a;
            len++;
            if (s[len] == ' ' || s[len] == '\n' || s[len] == 0) word_end = len;
        }
        if (s[len] && s[len] != '\n' && word_end > 0) len = word_end;
        if (len == 0 && *s != '\n') break;
        memcpy(out + n * stride, s, len);
        out[n * stride + len] = 0;
        if (hard) hard[n] = s[len] == '\n';
        n++;
        s += len;
        if (*s == '\n') s++;
    }
    return n;
}

// The "more" arrow (the font's own glyph), blinking, bottom right inside the
// box's 12px text padding: its ink 12-18px above the bottom.
static void draw_more_arrow(SDL_Renderer* ren, const SDL_Rect& box, int up_from_bottom) {
    if ((SDL_GetTicks() / 300) % 2) return;
    draw_text(ren, GLYPH_MORE, box.x + box.w - 12 - text_width(GLYPH_MORE, 2),
              box.y + box.h - 24 - up_from_bottom, 2, 252, 252, 252);
}

// How fast a person talks: letters a second; the slide up a line once the
// three are full, made in SPEECH_SCROLL_STEPS jumps (stepped, not smooth);
// and the breaths after a comma and after a sentence's end.
static const float SPEECH_CPS          = 40.0f;
static const float SPEECH_SCROLL_T     = 0.15f;
static const int   SPEECH_SCROLL_STEPS = 3;
static const float SPEECH_COMMA_T      = 0.15f;
static const float SPEECH_STOP_T       = 0.35f;

// The breath after letter c, with next the one after it (' ' across a line
// break, 0 at the very end): only where a word ends, so "..." breathes once
// and the end waits on the arrow, not a pause. Where it breathes, the box
// may also stop for the press.
static float speech_pause(char c, char next) {
    if (next != ' ') return 0.0f;
    if (c == ',') return SPEECH_COMMA_T;
    if (c == '.' || c == '!' || c == '?') return SPEECH_STOP_T;
    return 0.0f;
}

SDL_Rect draw_speech(SDL_Renderer* ren, const char* text, int part, float t, SpeechState* state,
                     bool strike, int left_pad, const std::function<int(int, int, int)>& line_icon) {
    const int LINE = 24, PAD = 12, MAX_LINES = 48, STRIDE = 96;
    // ponytail: wraps at the full width, not minus a line's icon; fine while
    // the iconed lines are short (a chest's "VINE x3").
    const int TEXT_W = DIALOGUE_W - PAD * 2 - left_pad;
    char lines[MAX_LINES][STRIDE];
    bool hard[MAX_LINES] = {};
    int  n = wrap_lines(text, TEXT_W, 2, STRIDE, &lines[0][0], MAX_LINES, hard);
    // Every dialogue shares the same frame; long pages scroll within it.
    const int LINES = (DIALOGUE_H - PAD * 2) / LINE;
    if (strike) t = 1e9f;
    // The letters as one run across the lines: line i holds [off[i], off[i + 1]).
    int off[MAX_LINES + 1] = { 0 };
    for (int i = 0; i < n; i++) off[i + 1] = off[i] + (int)strlen(lines[i]);
    auto line_of = [&](int k) { int i = 0; while (i + 1 < n && off[i + 1] <= k) i++; return i; };
    auto at      = [&](int k) { int i = line_of(k); return lines[i][k - off[i]]; };
    auto next    = [&](int k) {   // what follows letter k: its line's next, ' ' across a break, 0 at the end
        int i = line_of(k), c = k - off[i] + 1;
        return lines[i][c] ? lines[i][c] : i + 1 < n ? ' ' : '\0';
    };

    // Where it stops for the press. A line only scrolls off once all of it
    // has been up at a stop, so the box never pushes away words the player
    // has not had the chance to read: each part ends before the line three
    // under the first line not yet read through, at the last comma,
    // sentence's end or '\n' before it -- or at that line's start, if there is none.
    int stops[MAX_LINES * 2], ns = 0, read = 0;
    while (ns < MAX_LINES * 2) {
        int f = 0;
        while (f < n && off[f + 1] <= read) f++;
        if (f + LINES >= n) { stops[ns++] = off[n]; break; }
        int limit = off[f + LINES], p = limit;
        for (int k = limit - 1; k >= read; k--) {
            int i = line_of(k);
            if (speech_pause(at(k), next(k)) > 0.0f || (hard[i] && k + 1 == off[i + 1])) { p = k + 1; break; }
        }
        stops[ns++] = read = p;
    }
    if (part >= ns) part = ns - 1;
    int a = part > 0 ? stops[part - 1] : 0, b = stops[part];

    // This part's timeline, from t: each letter, the breath after it, and a
    // slide before any letter that falls under the box.
    int   top   = a > 0 ? SDL_max(0, line_of(a - 1) - (LINES - 1)) : 0;
    int   shown = a;
    float acc   = 0.0f, slide = -1.0f;   // slide: how far into one under way
    for (int k = a; k < b; k++) {
        if (line_of(k) - (LINES - 1) > top) {
            if (t < acc) break;
            if (t < acc + SPEECH_SCROLL_T) { slide = t - acc; break; }
            acc += SPEECH_SCROLL_T;
            top++;
        }
        acc += 1.0f / SPEECH_CPS;
        if (t < acc) break;
        shown = k + 1;
        if (k + 1 < b) acc += speech_pause(at(k), next(k));
    }
    if (state) *state = shown < b ? SPEECH_TYPING : b == off[n] ? SPEECH_END : SPEECH_WAIT;
    // Stepped: a beat, then a third of a line a jump.
    int lift = slide < 0.0f ? 0 : (int)(slide / SPEECH_SCROLL_T * SPEECH_SCROLL_STEPS) * LINE / SPEECH_SCROLL_STEPS;

    int w = DIALOGUE_W, h = DIALOGUE_H;
    SDL_Rect box = { (640 - w) / 2, 480 - DIALOGUE_BOTTOM - h, w, h };
    draw_nes_panel(ren, box.x, box.y, box.w, box.h);
    SDL_Rect inside = { box.x + NES_PAD, box.y + NES_PAD, box.w - NES_PAD * 2, box.h - NES_PAD * 2 };
    SDL_RenderSetClipRect(ren, &inside);
    int text_x = box.x + left_pad + PAD;
    for (int k = top; k <= top + LINES && k < n; k++) {
        int len = off[k + 1] - off[k], out = SDL_min(SDL_max(shown - off[k], 0), len);
        if (out <= 0) continue;
        char part_text[STRIDE];
        SDL_strlcpy(part_text, lines[k], (size_t)out + 1);
        int ty = box.y + PAD + (k - top) * LINE - lift;
        int tx = text_x + (line_icon ? line_icon(k, text_x, ty) : 0);
        draw_text(ren, part_text, tx, ty, 2, 252, 252, 252);
        if (strike) {
            fc_draw_color(ren, 220, 40, 40, 255);
            SDL_Rect bar = { tx, ty + 6, text_width(part_text, 2), 4 };
            SDL_RenderFillRect(ren, &bar);
        }
    }
    SDL_RenderSetClipRect(ren, nullptr);
    if (shown >= b) draw_more_arrow(ren, box, 0);
    return box;
}

SDL_Rect draw_textbox(SDL_Renderer* ren, const char* text, Uint8 r, Uint8 g, Uint8 b,
                      bool low, int extra_h, int left_pad) {
    const int TOP  = 48;    // under the HUD bar and the weapon box
    const int TEXT_W = 160; // as wide as the old font's "STONEHENGE"
    const int LINE = 24, PAD = 12, MAX_LINES = 16;   // the menus' font: 16px a character

    char lines[MAX_LINES][64];
    int  n = wrap_lines(text, TEXT_W, 2, 64, &lines[0][0], MAX_LINES);
    if (n > 2) n = wrap_lines(text, TEXT_W - 16, 2, 64, &lines[0][0], MAX_LINES);   // paging: clear of the arrow

    // One line high; two for anything longer, and past two it turns its
    // pages itself, a blinking arrow in the corner saying there is more.
    // ponytail: pages turn on the global clock (the prompts own the confirm
    // key), so a long text can open mid-way; give it a start time if any
    // text ever runs past two lines.
    int shown = n > 1 ? 2 : 1, pages = (n + 1) / 2;
    int page  = pages > 1 ? (int)(SDL_GetTicks() / 1800) % pages : 0;
    int w = TEXT_W + PAD * 2 + left_pad, h = 32 + (shown - 1) * LINE + extra_h;
    SDL_Rect box = { (640 - w) / 2, low ? 480 - TOP - h : TOP, w, h };
    draw_nes_panel(ren, box.x, box.y, box.w, box.h);
    for (int i = 0; i < shown && page * 2 + i < n; i++) {
        const char* ln = lines[page * 2 + i];
        // One line sits centred in the text strip; wrapped text reads from the left.
        int text_x = box.x + left_pad;
        int tx = n == 1 ? text_x + (TEXT_W + PAD * 2 - text_width(ln, 2)) / 2 : text_x + PAD;
        draw_text(ren, ln, tx, box.y + 8 + i * LINE, 2, r, g, b);
    }
    if (pages > 1) draw_more_arrow(ren, box, extra_h);
    return box;
}

void draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
              float cur, float max, Uint8 r, Uint8 g, Uint8 b) {
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect bg = {x, y, w, h};
    SDL_RenderFillRect(ren, &bg);
    if (max > 0.0f && cur > 0.0f) {
        int filled = (int)(w * cur / max);
        if (filled > w) filled = w;
        fc_draw_color(ren, r, g, b, 255);
        SDL_Rect fill = {x, y, filled, h};
        SDL_RenderFillRect(ren, &fill);
    }
    fc_draw_color(ren, 255, 255, 255, 255);
    SDL_RenderDrawRect(ren, &bg);
}

void draw_fps(SDL_Renderer* renderer, float dt, float player_x, float player_y) {
    static float acc         = 0.0f;
    static int   frames      = 0;
    static int   display_fps = 0;

    acc += dt;
    frames++;
    if (acc >= 0.5f) {
        display_fps = (int)(frames / acc + 0.5f);
        frames = 0;
        acc    = 0.0f;
    }

    char buf[32];
    SDL_snprintf(buf, sizeof(buf), "FPS:%d", display_fps);
    draw_text(renderer, buf, 4, 4, 2, 255, 220, 0);

    SDL_snprintf(buf, sizeof(buf), "X:%d Y:%d", (int)player_x, (int)player_y);
    draw_text(renderer, buf, 4, 22, 2, 255, 220, 0);
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
