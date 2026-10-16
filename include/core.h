#ifndef CORE_H
#define CORE_H

#include <SDL2/SDL.h>
#include <functional>

double time_delta_seconds(void);

void draw_fps(SDL_Renderer* renderer, float dt, float player_x, float player_y);

// Draw a string at (x, y) in the game's font (Pixuf, src/font.inc): printable
// ASCII, proportional. scale=1 → 8px tall, scale=2 → 16px tall.
void draw_text(SDL_Renderer* ren, const char* text, int x, int y, int scale,
               Uint8 r, Uint8 g, Uint8 b);

// Returns the pixel width of the string at the given scale.
int text_width(const char* text, int scale);

// The game's own glyphs in the font (tools/gen_font.py): the menus' cursor
// and the "more" arrow, drawn as text so they share its size, colour and shadow.
#define GLYPH_CURSOR "\x7f"
#define GLYPH_MORE   "\x80"

// A window as the menu reference draws them: black inside, a 4px frame with
// stepped round corners (white unless coloured), and a 2px black edge round
// the outside of the rect. Content area starts at (x+4, y+4); NES_PAD (4).
void draw_nes_panel(SDL_Renderer* ren, int x, int y, int w, int h,
                    Uint8 r = 255, Uint8 g = 255, Uint8 b = 255);

// A meter: black, filled cur/max of the way in (r,g,b), white outline.
void draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
              float cur, float max, Uint8 r, Uint8 g, Uint8 b);
static const int NES_PAD = 4;

// The textbox: one line of text (the menus' 16px font) in a window just big enough for it,
// centred near the top of the screen -- or, with low, mirrored to the bottom
// (a battle does that to keep it off the player). extra_h is room under the
// text. Returns the window's rect.
// The speech box: what a person or a note says, low on the screen, three
// lines 480px wide in the menus' 16px font. It types out a letter at a time,
// breathing at commas and full stops, and steps up a line when the three are
// full -- but never past words not yet read: before a line would push off
// one the player has not seen whole, it stops at the last comma or full stop
// and waits for the press (the arrow blinks). part: how many presses it has
// had at its stops; t: seconds since this part began (huge shows the part
// whole); *state: still typing, stopped for the press, or at the end. strike
// shows the entire page immediately in an expanded box with red lines
// through it. Not modal itself: the caller blanks the world's input while it is up
// (main.cpp dlg_text), keeps part and t, and closes it at the end.
static const int DIALOGUE_W = 504;
static const int DIALOGUE_H = 96;
static const int DIALOGUE_BOTTOM = 40;

enum SpeechState { SPEECH_TYPING, SPEECH_WAIT, SPEECH_END };
// left_pad: empty strip on the left of the text for a caller-drawn icon.
// '\n' starts a new line, and the box may stop for the press there too (a
// chest's list). line_icon(line, x, y), once a line starts typing, draws
// that line's icon at its text's place and returns how far to push the text
// right (0: no icon).
SDL_Rect draw_speech(SDL_Renderer* ren, const char* text, int part, float t, SpeechState* state,
                     bool strike = false, int left_pad = 0,
                     const std::function<int(int, int, int)>& line_icon = nullptr);
SDL_Rect draw_textbox(SDL_Renderer* ren, const char* text, Uint8 r, Uint8 g, Uint8 b,
                      bool low = false, int extra_h = 0, int left_pad = 0);

// Half-period of the flashing player marker on both minimaps, in milliseconds.
// Shared so the overworld and dungeon maps blink in step.
static const Uint32 MINIMAP_FLASH_MS = 350;

#endif
