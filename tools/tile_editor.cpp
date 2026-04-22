// Bare-bones SDL2 tile editor — Game Maker-style multi-tile stamp selection.
//
// Usage: ./tile_editor   (always opens town_0)
//
// Controls:
//   Sprite panel  LMB drag  — select a rectangle of tiles from the sheet
//   Canvas        LMB drag  — stamp the selection (tiles it as you drag)
//   Canvas        RMB drag  — pan
//   WASD / arrows           — pan
//   Scroll over canvas      — zoom
//   Scroll over panel       — scroll sprite rows
//   1-6                     — select a basic tile (blank/grass/path/hub/water/tree)
//   [  ]                    — change brush size (basic tiles only)
//   D                       — switch to depth layer (blue, marks tall/above-player tiles)
//   C                       — switch to collision layer (red, marks solid tiles)
//   T                       — switch back to tile layer
//   Shift+LMB               — erase in depth/collision layer
//   Ctrl-Z                  — undo (restores all layers)
//   Ctrl-S                  — save + build
//   Q / Escape              — quit

#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>
#include <algorithm>

// ---------------------------------------------------------------------------
// Area
// ---------------------------------------------------------------------------
static const char* AREA_NAME  = "town_0";
static const char* AREA_FILE  = "include/towns.h";
static const int   AREA_W     = 156;
static const int   AREA_H     = 156;
static const char* AREA_SHEET = "assets/town_0.png";

// ---------------------------------------------------------------------------
// Basic tile palette
// ---------------------------------------------------------------------------
// Canvas value encoding:
//   0        = blank (biome background shows through)
//   1        = grass
//   2        = path
//   3        = hub
//   4        = water
//   5        = tree (overlay)
//   val >= 6 = sprite tile: col=(val-6)%256  row=(val-6)/256
struct BasicTile { int val; const char* label; uint8_t r, g, b; };
static const BasicTile BASIC_TILES[] = {
    { 0, "Blank",  40,  40,  40 },
    { 1, "Grass",  34,  85,  34 },
    { 2, "Path",  120, 100,  60 },
    { 3, "Hub",    30,  90, 200 },
    { 4, "Water",  30,  90, 200 },
    { 5, "Tree",    0, 100,   0 },
};
static const int BASIC_COUNT = 6;

// ---------------------------------------------------------------------------
// Sprite sheet (tileset.png — 256 cols × 256 rows, 16×16 px each)
// ---------------------------------------------------------------------------
static const int SHEET_COLS = 256;
static const int SHEET_ROWS = 256;

// Decode a canvas sprite value (val >= 6) → sheet col/row.
static inline void canvas_to_sheet(int val, int* col, int* row) {
    int idx = val - 6;
    *col = idx % SHEET_COLS;
    *row = idx / SHEET_COLS;
}
// Encode sheet col/row → canvas sprite value.
static inline int sheet_to_canvas(int col, int row) {
    return col + row * SHEET_COLS + 6;
}

// ---------------------------------------------------------------------------
// Selection — either a basic tile (brush) or a sprite-sheet rectangle
// ---------------------------------------------------------------------------
enum SelKind { SEL_BASIC, SEL_SPRITE };

struct Selection {
    SelKind kind    = SEL_BASIC;
    int basic_val   = 1;    // canvas value 0-5 when kind == SEL_BASIC
    int brush       = 0;    // brush radius for basic tile
    // Sprite rectangle in sheet coords
    int col  = 0, row  = 0;
    int cols = 1, rows = 1;
};

static Selection g_sel;

// Canvas value for a cell within the current sprite selection.
static int sel_tile_at(int dx, int dy) {
    return sheet_to_canvas(g_sel.col + dx, g_sel.row + dy);
}

// ---------------------------------------------------------------------------
// 8×8 bitmap font
// ---------------------------------------------------------------------------
static const uint8_t FONT8[96][8] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // ' '
    {0x18,0x3C,0x3C,0x18,0x18,0x00,0x18,0x00}, // !
    {0x6C,0x6C,0x00,0x00,0x00,0x00,0x00,0x00}, // "
    {0x6C,0x6C,0xFE,0x6C,0xFE,0x6C,0x6C,0x00}, // #
    {0x30,0x7C,0x0C,0x38,0x60,0x7C,0x0C,0x38}, // $
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // %
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // &
    {0x18,0x18,0x18,0x00,0x00,0x00,0x00,0x00}, // '
    {0x30,0x18,0x0C,0x0C,0x0C,0x18,0x30,0x00}, // (
    {0x0C,0x18,0x30,0x30,0x30,0x18,0x0C,0x00}, // )
    {0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00}, // *
    {0x00,0x18,0x18,0x7E,0x18,0x18,0x00,0x00}, // +
    {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x0C}, // ,
    {0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00}, // -
    {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00}, // .
    {0x40,0x60,0x30,0x18,0x0C,0x06,0x02,0x00}, // /
    {0x3C,0x66,0x76,0x6E,0x66,0x66,0x3C,0x00}, // 0
    {0x18,0x1C,0x18,0x18,0x18,0x18,0x7E,0x00}, // 1
    {0x3C,0x66,0x60,0x38,0x0C,0x66,0x7E,0x00}, // 2
    {0x3C,0x66,0x60,0x38,0x60,0x66,0x3C,0x00}, // 3
    {0x60,0x68,0x6C,0x66,0x7E,0x60,0x60,0x00}, // 4
    {0x7E,0x06,0x3E,0x60,0x60,0x66,0x3C,0x00}, // 5
    {0x38,0x0C,0x06,0x3E,0x66,0x66,0x3C,0x00}, // 6
    {0x7E,0x66,0x60,0x30,0x18,0x18,0x18,0x00}, // 7
    {0x3C,0x66,0x66,0x3C,0x66,0x66,0x3C,0x00}, // 8
    {0x3C,0x66,0x66,0x7C,0x60,0x30,0x1C,0x00}, // 9
    {0x00,0x18,0x18,0x00,0x18,0x18,0x00,0x00}, // :
    {0x00,0x18,0x18,0x00,0x18,0x18,0x0C,0x00}, // ;
    {0x30,0x18,0x0C,0x06,0x0C,0x18,0x30,0x00}, // <
    {0x00,0x00,0x7E,0x00,0x7E,0x00,0x00,0x00}, // =
    {0x0C,0x18,0x30,0x60,0x30,0x18,0x0C,0x00}, // >
    {0x3C,0x66,0x60,0x30,0x18,0x00,0x18,0x00}, // ?
    {0x3C,0x66,0x6E,0x6A,0x6E,0x06,0x3C,0x00}, // @
    {0x18,0x3C,0x66,0x66,0x7E,0x66,0x66,0x00}, // A
    {0x3E,0x66,0x66,0x3E,0x66,0x66,0x3E,0x00}, // B
    {0x3C,0x66,0x06,0x06,0x06,0x66,0x3C,0x00}, // C
    {0x1E,0x36,0x66,0x66,0x66,0x36,0x1E,0x00}, // D
    {0x7E,0x06,0x06,0x3E,0x06,0x06,0x7E,0x00}, // E
    {0x7E,0x06,0x06,0x3E,0x06,0x06,0x06,0x00}, // F
    {0x3C,0x66,0x06,0x76,0x66,0x66,0x3C,0x00}, // G
    {0x66,0x66,0x66,0x7E,0x66,0x66,0x66,0x00}, // H
    {0x3C,0x18,0x18,0x18,0x18,0x18,0x3C,0x00}, // I
    {0x78,0x30,0x30,0x30,0x30,0x36,0x1C,0x00}, // J
    {0x66,0x36,0x1E,0x0E,0x1E,0x36,0x66,0x00}, // K
    {0x06,0x06,0x06,0x06,0x06,0x06,0x7E,0x00}, // L
    {0x63,0x77,0x7F,0x6B,0x63,0x63,0x63,0x00}, // M
    {0x66,0x6E,0x7E,0x76,0x66,0x66,0x66,0x00}, // N
    {0x3C,0x66,0x66,0x66,0x66,0x66,0x3C,0x00}, // O
    {0x3E,0x66,0x66,0x3E,0x06,0x06,0x06,0x00}, // P
    {0x3C,0x66,0x66,0x66,0x6A,0x3C,0x50,0x00}, // Q
    {0x3E,0x66,0x66,0x3E,0x1E,0x36,0x66,0x00}, // R
    {0x3C,0x66,0x06,0x3C,0x60,0x66,0x3C,0x00}, // S
    {0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x00}, // T
    {0x66,0x66,0x66,0x66,0x66,0x66,0x3C,0x00}, // U
    {0x66,0x66,0x66,0x66,0x66,0x3C,0x18,0x00}, // V
    {0x63,0x63,0x63,0x6B,0x7F,0x77,0x63,0x00}, // W
    {0x66,0x66,0x3C,0x18,0x3C,0x66,0x66,0x00}, // X
    {0x66,0x66,0x66,0x3C,0x18,0x18,0x18,0x00}, // Y
    {0x7E,0x60,0x30,0x18,0x0C,0x06,0x7E,0x00}, // Z
    {0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0x3C,0x00}, // [
    {0x02,0x06,0x0C,0x18,0x30,0x60,0x40,0x00}, /* \ */
    {0x3C,0x30,0x30,0x30,0x30,0x30,0x3C,0x00}, // ]
    {0x18,0x3C,0x66,0x00,0x00,0x00,0x00,0x00}, // ^
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF}, // _
    {0x0C,0x18,0x30,0x00,0x00,0x00,0x00,0x00}, // `
    {0x00,0x00,0x3C,0x60,0x7C,0x66,0x7C,0x00}, // a
    {0x06,0x06,0x3E,0x66,0x66,0x66,0x3E,0x00}, // b
    {0x00,0x00,0x3C,0x06,0x06,0x06,0x3C,0x00}, // c
    {0x60,0x60,0x7C,0x66,0x66,0x66,0x7C,0x00}, // d
    {0x00,0x00,0x3C,0x66,0x7E,0x06,0x3C,0x00}, // e
    {0x38,0x0C,0x0C,0x3E,0x0C,0x0C,0x0C,0x00}, // f
    {0x00,0x00,0x7C,0x66,0x66,0x7C,0x60,0x3C}, // g
    {0x06,0x06,0x3E,0x66,0x66,0x66,0x66,0x00}, // h
    {0x18,0x00,0x1C,0x18,0x18,0x18,0x3C,0x00}, // i
    {0x30,0x00,0x38,0x30,0x30,0x30,0x36,0x1C}, // j
    {0x06,0x06,0x66,0x36,0x1E,0x36,0x66,0x00}, // k
    {0x1C,0x18,0x18,0x18,0x18,0x18,0x3C,0x00}, // l
    {0x00,0x00,0x36,0x7F,0x6B,0x63,0x63,0x00}, // m
    {0x00,0x00,0x3E,0x66,0x66,0x66,0x66,0x00}, // n
    {0x00,0x00,0x3C,0x66,0x66,0x66,0x3C,0x00}, // o
    {0x00,0x00,0x3E,0x66,0x66,0x3E,0x06,0x06}, // p
    {0x00,0x00,0x7C,0x66,0x66,0x7C,0x60,0x60}, // q
    {0x00,0x00,0x36,0x6E,0x06,0x06,0x06,0x00}, // r
    {0x00,0x00,0x3C,0x06,0x3C,0x60,0x3C,0x00}, // s
    {0x0C,0x0C,0x3E,0x0C,0x0C,0x0C,0x38,0x00}, // t
    {0x00,0x00,0x66,0x66,0x66,0x66,0x7C,0x00}, // u
    {0x00,0x00,0x66,0x66,0x66,0x3C,0x18,0x00}, // v
    {0x00,0x00,0x63,0x6B,0x7F,0x36,0x36,0x00}, // w
    {0x00,0x00,0x66,0x3C,0x18,0x3C,0x66,0x00}, // x
    {0x00,0x00,0x66,0x66,0x7C,0x60,0x3C,0x00}, // y
    {0x00,0x00,0x7E,0x30,0x18,0x0C,0x7E,0x00}, // z
    {0x38,0x0C,0x0C,0x06,0x0C,0x0C,0x38,0x00}, // {
    {0x18,0x18,0x18,0x00,0x18,0x18,0x18,0x00}, // |
    {0x0E,0x18,0x18,0x30,0x18,0x18,0x0E,0x00}, // }
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // ~
    {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF}, // DEL
};

static void draw_char(SDL_Renderer* r, char c, int x, int y,
                      uint8_t fr, uint8_t fg, uint8_t fb) {
    int idx = (uint8_t)c - 0x20;
    if (idx < 0 || idx >= 96) return;
    SDL_SetRenderDrawColor(r, fr, fg, fb, 255);
    for (int row = 0; row < 8; row++) {
        uint8_t bits = FONT8[idx][row];
        for (int col = 0; col < 8; col++)
            if (bits & (1 << col))
                SDL_RenderDrawPoint(r, x + col, y + row);
    }
}
static void draw_text(SDL_Renderer* r, const char* s, int x, int y,
                      uint8_t fr, uint8_t fg, uint8_t fb) {
    for (; *s; s++, x += 9) draw_char(r, *s, x, y, fr, fg, fb);
}

// ---------------------------------------------------------------------------
// Canvas — stores tile values (see encoding at top of file)
// Depth layer: marks tiles that draw on top of player (Y-sort tall objects)
// Collision layer: marks tiles that are solid (precise collision footprint)
// ---------------------------------------------------------------------------
static const int MAX_W = 156, MAX_H = 156;
static int  g_canvas[MAX_H][MAX_W];
static bool g_depth[MAX_H][MAX_W];
static bool g_coll[MAX_H][MAX_W];
static int  g_bg[MAX_H][MAX_W];   // background display index into BASIC_TILES
static bool g_dirty = false;

enum LayerMode { LAYER_TILE, LAYER_DEPTH, LAYER_COLL };
static LayerMode g_layer = LAYER_TILE;

static const int MAX_UNDO = 32;
static int  g_undo_canvas[MAX_UNDO][MAX_H][MAX_W];
static bool g_undo_depth[MAX_UNDO][MAX_H][MAX_W];
static bool g_undo_coll[MAX_UNDO][MAX_H][MAX_W];
static int  g_undo_top = 0;

static void undo_push() {
    if (g_undo_top < MAX_UNDO) {
        memcpy(g_undo_canvas[g_undo_top], g_canvas, sizeof(g_canvas));
        memcpy(g_undo_depth[g_undo_top],  g_depth,  sizeof(g_depth));
        memcpy(g_undo_coll[g_undo_top],   g_coll,   sizeof(g_coll));
        g_undo_top++;
    } else {
        memmove(g_undo_canvas[0], g_undo_canvas[1], sizeof(g_canvas) * (MAX_UNDO - 1));
        memmove(g_undo_depth[0],  g_undo_depth[1],  sizeof(g_depth)  * (MAX_UNDO - 1));
        memmove(g_undo_coll[0],   g_undo_coll[1],   sizeof(g_coll)   * (MAX_UNDO - 1));
        memcpy(g_undo_canvas[MAX_UNDO - 1], g_canvas, sizeof(g_canvas));
        memcpy(g_undo_depth[MAX_UNDO - 1],  g_depth,  sizeof(g_depth));
        memcpy(g_undo_coll[MAX_UNDO - 1],   g_coll,   sizeof(g_coll));
    }
}
static void undo_pop() {
    if (g_undo_top == 0) return;
    g_undo_top--;
    memcpy(g_canvas, g_undo_canvas[g_undo_top], sizeof(g_canvas));
    memcpy(g_depth,  g_undo_depth[g_undo_top],  sizeof(g_depth));
    memcpy(g_coll,   g_undo_coll[g_undo_top],   sizeof(g_coll));
    g_dirty = true;
}

static void compute_background(const char* name, int w, int h) {
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
            g_bg[y][x] = 1; // grass
    if (strcmp(name, "town_0") == 0) {
        const int cx = w / 2, cy = h / 2;
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
            int dx = x-cx, dy = y-cy, d2 = dx*dx+dy*dy;
            if (d2 >= 78*78 && d2 <= 102*102) g_bg[y][x] = 4; // water
        }
    }
}

// ---------------------------------------------------------------------------
// Load / Save — tile layer
// ---------------------------------------------------------------------------
// Migrate a legacy char value to the new int canvas encoding.
static int legacy_char_to_canvas(char c) {
    switch (c) {
        case ' ': return 0;
        case '.': return 1;  // grass
        case ',': return 2;  // path
        case 'H': return 3;  // hub
        case 'W': return 4;  // water
        case 'T': return 5;  // tree
        default:  return 0;  // old sprite chars — cleared (sheet is different now)
    }
}

static bool load_area(const char* file, const char* name, int w, int h) {
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
            g_canvas[y][x] = 0;
    FILE* f = fopen(file, "r");
    if (!f) { fprintf(stderr, "Cannot open %s\n", file); return false; }

    // Detect format: look for "const int <name>[" (new) or "const char* <name>[" (legacy)
    char new_tag[128], legacy_tag[128];
    snprintf(new_tag,    sizeof(new_tag),    "int %s[", name);
    snprintf(legacy_tag, sizeof(legacy_tag), "char* %s[]", name);

    char line[8192];
    bool in_area = false; bool is_legacy = false; int row = 0;
    while (fgets(line, sizeof(line), f) && row < h) {
        if (!in_area) {
            if (strstr(line, new_tag))    { in_area = true; is_legacy = false; continue; }
            if (strstr(line, legacy_tag)) { in_area = true; is_legacy = true;  continue; }
            continue;
        }
        if (is_legacy) {
            char* p = strchr(line, '"');
            if (!p) { if (strstr(line, "nullptr")) break; continue; }
            p++;
            for (int col = 0; col < w && *p && *p != '"'; col++, p++)
                g_canvas[row][col] = legacy_char_to_canvas(*p);
        } else {
            char* p = strchr(line, '{');
            if (!p) { if (strchr(line, '}')) break; continue; }
            p++;
            for (int col = 0; col < w; col++) {
                while (*p == ' ' || *p == '\t') p++;
                if (*p == '}' || *p == '\0') break;
                g_canvas[row][col] = (int)strtol(p, &p, 10);
                while (*p == ',' || *p == ' ') p++;
            }
        }
        row++;
    }
    fclose(f);
    return true;
}

static bool save_area(const char* file, const char* name, int w, int h) {
    FILE* f = fopen(file, "r");
    if (!f) { fprintf(stderr, "Cannot open %s\n", file); return false; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); rewind(f);
    std::vector<char> buf(sz + 1);
    (void)fread(buf.data(), 1, sz, f); buf[sz] = '\0'; fclose(f);
    std::string src(buf.data());

    // Find either new "int <name>[" or legacy "char* <name>[]" declaration.
    char new_tag[128], legacy_tag[128];
    snprintf(new_tag,    sizeof(new_tag),    "int %s[", name);
    snprintf(legacy_tag, sizeof(legacy_tag), "char* %s[]", name);

    size_t pos = src.find(new_tag);
    bool is_legacy = false;
    if (pos == std::string::npos) { pos = src.find(legacy_tag); is_legacy = true; }
    if (pos == std::string::npos) { fprintf(stderr, "SAVE: array '%s' not found\n", name); return false; }

    // Find the declaration start (back up to "static")
    size_t decl = src.rfind("static", pos);
    if (decl == std::string::npos) decl = pos;

    // Find the end of the block
    size_t block_start = src.find('{', pos);
    if (block_start == std::string::npos) { fprintf(stderr, "SAVE: parse error\n"); return false; }
    size_t block_end;
    if (is_legacy) {
        size_t np = src.find("nullptr", block_start);
        if (np == std::string::npos) { fprintf(stderr, "SAVE: parse error (nullptr)\n"); return false; }
        block_end = src.find("};", np);
    } else {
        // New format: find the matching closing };
        block_end = src.find("};", block_start);
    }
    if (block_end == std::string::npos) { fprintf(stderr, "SAVE: parse error (end)\n"); return false; }

    // Build new declaration
    std::string body;
    body += "static const int ";
    body += name;
    body += "[";
    body += std::to_string(h);
    body += "][";
    body += std::to_string(w);
    body += "] = {\n";
    for (int r = 0; r < h; r++) {
        body += "    {";
        for (int c = 0; c < w; c++) {
            body += std::to_string(g_canvas[r][c]);
            if (c < w - 1) body += ",";
        }
        body += "},\n";
    }
    body += "};";

    src.replace(decl, block_end + 2 - decl, body);
    f = fopen(file, "w");
    if (!f) { fprintf(stderr, "SAVE: cannot write\n"); return false; }
    size_t written = fwrite(src.data(), 1, src.size(), f);
    fclose(f);
    printf("SAVE: wrote %zu bytes to %s\n", written, file);
    return written == src.size();
}

// ---------------------------------------------------------------------------
// Load / Save — meta layers (depth, collision)
// Array name: "<name>_depth" and "<name>_coll"
// Format: '#' = marked, '.' = clear
// If the array doesn't exist in the file yet, it is appended before #endif.
// ---------------------------------------------------------------------------
static void load_meta_layer(const char* file, const char* name, const char* suffix,
                             bool grid[MAX_H][MAX_W], int w, int h) {
    memset(grid, 0, sizeof(bool) * MAX_H * MAX_W);
    FILE* f = fopen(file, "r");
    if (!f) return;
    char tag[128]; snprintf(tag, sizeof(tag), "%s_%s[]", name, suffix);
    char line[4096];
    bool in_area = false; int row = 0;
    while (fgets(line, sizeof(line), f) && row < h) {
        if (!in_area) { if (strstr(line, tag)) in_area = true; continue; }
        char* p = strchr(line, '"');
        if (!p) { if (strstr(line, "nullptr")) break; continue; }
        p++;
        for (int col = 0; col < w && *p && *p != '"'; col++, p++)
            grid[row][col] = (*p == '#');
        row++;
    }
    fclose(f);
}

static bool save_meta_layer(const char* file, const char* name, const char* suffix,
                              bool grid[MAX_H][MAX_W], int w, int h) {
    FILE* f = fopen(file, "r");
    if (!f) { fprintf(stderr, "META SAVE: cannot open %s\n", file); return false; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); rewind(f);
    std::vector<char> buf(sz + 1);
    (void)fread(buf.data(), 1, sz, f); buf[sz] = '\0'; fclose(f);
    std::string src(buf.data());

    char arr_name[128]; snprintf(arr_name, sizeof(arr_name), "%s_%s", name, suffix);
    char tag[128];      snprintf(tag, sizeof(tag), "%s[]", arr_name);

    // Build the replacement/insertion body
    std::string body;
    body += "static const char* ";
    body += arr_name;
    body += "[] = {\n";
    for (int r = 0; r < h; r++) {
        body += "    \"";
        for (int c = 0; c < w; c++)
            body += grid[r][c] ? '#' : '.';
        body += "\",\n";
    }
    body += "    nullptr\n};";

    size_t pos = src.find(tag);
    if (pos != std::string::npos) {
        // Find the start of the declaration line
        size_t decl = src.rfind("static const char*", pos);
        if (decl == std::string::npos) decl = pos;
        size_t end_brace = src.find("};", pos);
        if (end_brace == std::string::npos) { fprintf(stderr, "META SAVE: parse error\n"); return false; }
        src.replace(decl, end_brace + 2 - decl, body);
    } else {
        // Append before #endif (or at end of file)
        size_t endif_pos = src.rfind("#endif");
        std::string insert = "\n" + body + "\n";
        if (endif_pos != std::string::npos)
            src.insert(endif_pos, insert);
        else
            src += insert;
    }

    f = fopen(file, "w");
    if (!f) { fprintf(stderr, "META SAVE: cannot write\n"); return false; }
    size_t written = fwrite(src.data(), 1, src.size(), f);
    fclose(f);
    return written == src.size();
}


// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------
static const int PALETTE_W  = 320;
static const int STATUS_H   = 20;
static const int WIN_W      = 1200;
static const int WIN_H      = 800;
static const int SPRITE_PX  = 16;  // px per tile in the sprite-sheet preview (18*16=288 fits in PALETTE_W)

static const char* PICKER_SHEET = "assets/tileset.png";

// ---------------------------------------------------------------------------
// Render helpers
// ---------------------------------------------------------------------------
static void draw_tile_at(SDL_Renderer* ren, SDL_Texture* sheet,
                         int val, int px, int py, int size) {
    if (val >= 6 && sheet) {
        int sc, sr; canvas_to_sheet(val, &sc, &sr);
        SDL_Rect src = { sc * 16, sr * 16, 16, 16 };
        SDL_Rect dst = { px, py, size, size };
        SDL_RenderCopy(ren, sheet, &src, &dst);
    } else {
        // Basic tile (0-5) — draw as a solid colour
        uint8_t r = 40, g = 40, b = 40;
        if (val >= 0 && val < BASIC_COUNT)
            { r = BASIC_TILES[val].r; g = BASIC_TILES[val].g; b = BASIC_TILES[val].b; }
        SDL_SetRenderDrawColor(ren, r, g, b, 255);
        SDL_Rect dst = { px, py, size, size };
        SDL_RenderFillRect(ren, &dst);
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
int main(int /*argc*/, char** /*argv*/) {
    load_area(AREA_FILE, AREA_NAME, AREA_W, AREA_H);
    load_meta_layer(AREA_FILE, AREA_NAME, "depth", g_depth, AREA_W, AREA_H);
    load_meta_layer(AREA_FILE, AREA_NAME, "coll",  g_coll,  AREA_W, AREA_H);
    compute_background(AREA_NAME, AREA_W, AREA_H);
    g_dirty = false;

    if (SDL_Init(SDL_INIT_VIDEO) < 0) { fprintf(stderr, "SDL: %s\n", SDL_GetError()); return 1; }
    if (IMG_Init(IMG_INIT_PNG) == 0)  { fprintf(stderr, "IMG: %s\n", IMG_GetError()); }

    char title[128];
    snprintf(title, sizeof(title), "Tile Editor — %s (%dx%d)", AREA_NAME, AREA_W, AREA_H);
    SDL_Window*   win = SDL_CreateWindow(title, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                         WIN_W, WIN_H, SDL_WINDOW_RESIZABLE);
    SDL_Renderer* ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);

    // Sprite picker — separate window
    static const int SPRITE_WIN_PX     = 32;
    static const int SPRITE_WIN_W      = SHEET_COLS * SPRITE_WIN_PX;
    static const int SPRITE_WIN_H      = SHEET_ROWS * SPRITE_WIN_PX;
    static const int SPRITE_WIN_INIT_W = 800;
    static const int SPRITE_WIN_INIT_H = 600;
    SDL_Window*   sprite_win = SDL_CreateWindow("Sprite Picker",
        SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
        SPRITE_WIN_INIT_W, SPRITE_WIN_INIT_H, SDL_WINDOW_RESIZABLE);
    SDL_Renderer* sprite_ren = SDL_CreateRenderer(sprite_win, -1, SDL_RENDERER_ACCELERATED);
    SDL_SetRenderDrawBlendMode(sprite_ren, SDL_BLENDMODE_BLEND);
    SDL_Texture*  sprite_win_tex = IMG_LoadTexture(sprite_ren, PICKER_SHEET);
    Uint32 sprite_win_id = SDL_GetWindowID(sprite_win);
    Uint32 main_win_id   = SDL_GetWindowID(win);

    SDL_Texture* sheet_tex = IMG_LoadTexture(ren, PICKER_SHEET);
    if (!sheet_tex) printf("%s not found: %s\n", PICKER_SHEET, SDL_GetError());

    // View state
    int   zoom   = 5;
    float cam_x  = 0.0f, cam_y = 0.0f;

    // Sprite picker view state
    float sprite_zoom  = 1.0f;
    float sprite_cam_x = 0.0f, sprite_cam_y = 0.0f;

    // Input state
    bool panning   = false;
    int  pan_ox = 0, pan_oy = 0;
    float pan_cx = 0.0f, pan_cy = 0.0f;
    bool painting  = false;
    bool sprite_panning = false;
    int  sprite_pan_ox = 0, sprite_pan_oy = 0;
    float sprite_pan_cx = 0.0f, sprite_pan_cy = 0.0f;

    // Sprite sheet drag selection state
    bool sheet_selecting  = false;
    int  sheet_drag_c0 = 0, sheet_drag_r0 = 0;
    int  sheet_drag_c1 = 0, sheet_drag_r1 = 0;


    // Helpers
    auto canvas_rect = [&](int ww, int wh) -> SDL_Rect {
        return { PALETTE_W, 0, ww - PALETTE_W, wh - STATUS_H };
    };
    auto tile_at_screen = [&](int sx, int sy, int ww, int wh, int* tx, int* ty) -> bool {
        SDL_Rect cv = canvas_rect(ww, wh);
        if (sx < cv.x || sy < cv.y || sx >= cv.x+cv.w || sy >= cv.y+cv.h) return false;
        *tx = (int)((sx - cv.x + cam_x) / zoom);
        *ty = (int)((sy - cv.y + cam_y) / zoom);
        return *tx >= 0 && *ty >= 0 && *tx < AREA_W && *ty < AREA_H;
    };
    // Kept in sync with the render loop — both must use the same integer tile size.
    int sprite_tile_px = SPRITE_WIN_PX;

    // Converts sprite-window local coords → sheet cell (accounts for zoom + pan)
    auto screen_to_sheet = [&](int sx, int sy, int* sc, int* sr) -> bool {
        if (sx < 0 || sy < 0 || sprite_tile_px < 1) return false;
        *sc = (int)((sx + sprite_cam_x) / sprite_tile_px);
        *sr = (int)((sy + sprite_cam_y) / sprite_tile_px);
        return *sc >= 0 && *sc < SHEET_COLS && *sr >= 0 && *sr < SHEET_ROWS;
    };
    auto commit_sheet_drag = [&]() {
        int c0 = std::min(sheet_drag_c0, sheet_drag_c1);
        int c1 = std::max(sheet_drag_c0, sheet_drag_c1);
        int r0 = std::min(sheet_drag_r0, sheet_drag_r1);
        int r1 = std::max(sheet_drag_r0, sheet_drag_r1);
        g_sel.kind = SEL_SPRITE;
        g_sel.col  = c0; g_sel.cols = c1 - c0 + 1;
        g_sel.row  = r0; g_sel.rows = r1 - r0 + 1;
    };
    auto set_title = [&](bool unsaved) {
        const char* layer_str = (g_layer == LAYER_DEPTH) ? " [DEPTH]"
                              : (g_layer == LAYER_COLL)  ? " [COLL]" : "";
        char t[160];
        snprintf(t, sizeof(t), "Tile Editor — %s (%dx%d)%s%s",
                 AREA_NAME, AREA_W, AREA_H, layer_str, unsaved ? "  [unsaved]" : "");
        SDL_SetWindowTitle(win, t);
    };

    // Paint onto canvas — tile layer
    auto do_paint_tile = [&](int tx, int ty) {
        if (g_sel.kind == SEL_BASIC) {
            int paint_val = g_sel.basic_val;
            bool changed = false;
            for (int dy = -g_sel.brush; dy <= g_sel.brush; dy++)
                for (int dx = -g_sel.brush; dx <= g_sel.brush; dx++) {
                    int bx = tx+dx, by = ty+dy;
                    if (bx < 0 || by < 0 || bx >= AREA_W || by >= AREA_H) continue;
                    if (g_canvas[by][bx] != paint_val) {
                        g_canvas[by][bx] = paint_val;
                        changed = true;
                    }
                }
            if (changed) g_dirty = true;
        } else {
            bool changed = false;
            for (int dy = 0; dy < g_sel.rows; dy++) {
                for (int dx = 0; dx < g_sel.cols; dx++) {
                    int bx = tx+dx, by = ty+dy;
                    if (bx < 0 || by < 0 || bx >= AREA_W || by >= AREA_H) continue;
                    int v = sel_tile_at(dx, dy);
                    if (g_canvas[by][bx] != v) {
                        g_canvas[by][bx] = v;
                        changed = true;
                    }
                }
            }
            if (changed) g_dirty = true;
        }
    };

    // Paint onto a meta layer (depth or coll) — erase=true clears instead of sets
    auto do_paint_meta = [&](int tx, int ty, bool (*layer)[MAX_W], bool erase) {
        int radius = (g_sel.kind == SEL_BASIC) ? g_sel.brush : 0;
        int sw     = (g_sel.kind == SEL_SPRITE) ? g_sel.cols : 1;
        int sh     = (g_sel.kind == SEL_SPRITE) ? g_sel.rows : 1;
        bool changed = false;
        for (int dy = -radius; dy < sh + radius; dy++) {
            for (int dx = -radius; dx < sw + radius; dx++) {
                int bx = tx+dx, by = ty+dy;
                if (bx < 0 || by < 0 || bx >= AREA_W || by >= AREA_H) continue;
                bool val = !erase;
                if (layer[by][bx] != val) { layer[by][bx] = val; changed = true; }
            }
        }
        if (changed) g_dirty = true;
    };

    auto do_paint = [&](int tx, int ty, bool erase) {
        if (g_layer == LAYER_TILE)  do_paint_tile(tx, ty);
        else if (g_layer == LAYER_DEPTH) do_paint_meta(tx, ty, g_depth, erase);
        else                             do_paint_meta(tx, ty, g_coll,  erase);
    };

    int last_stamp_tx = -9999, last_stamp_ty = -9999;

    bool running = true;
    Uint64 last_tick = SDL_GetPerformanceCounter();

    while (running) {
        Uint64 now = SDL_GetPerformanceCounter();
        float dt = (float)(now - last_tick) / (float)SDL_GetPerformanceFrequency();
        last_tick = now;

        int ww, wh; SDL_GetWindowSize(win, &ww, &wh);
        sprite_tile_px = std::max(1, (int)(SPRITE_WIN_PX * sprite_zoom));

        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            switch (ev.type) {
            case SDL_QUIT: running = false; break;
            case SDL_WINDOWEVENT:
                if (ev.window.event == SDL_WINDOWEVENT_CLOSE) {
                    if (ev.window.windowID == main_win_id)   running = false;
                    else if (ev.window.windowID == sprite_win_id) SDL_HideWindow(sprite_win);
                }
                break;

            case SDL_KEYDOWN:
                switch (ev.key.keysym.sym) {
                case SDLK_ESCAPE: case SDLK_q: running = false; break;
                case SDLK_s:
                    if (ev.key.keysym.mod & KMOD_CTRL) {
                        bool ok = save_area(AREA_FILE, AREA_NAME, AREA_W, AREA_H);
                        ok &= save_meta_layer(AREA_FILE, AREA_NAME, "depth", g_depth, AREA_W, AREA_H);
                        ok &= save_meta_layer(AREA_FILE, AREA_NAME, "coll",  g_coll,  AREA_W, AREA_H);
                        if (ok) {
                            g_dirty = false; set_title(false);
                            int rc = system("make 2>&1");
                            printf(rc == 0 ? "Build OK.\n" : "Build FAILED.\n");
                        }
                    }
                    break;
                // Layer switching
                case SDLK_d: g_layer = LAYER_DEPTH; set_title(g_dirty); break;
                case SDLK_c: g_layer = LAYER_COLL;  set_title(g_dirty); break;
                case SDLK_t: g_layer = LAYER_TILE;  set_title(g_dirty); break;
                // Basic tile hotkeys — also revert to tile layer
                case SDLK_1: g_sel.kind = SEL_BASIC; g_sel.basic_val = 0; g_layer = LAYER_TILE; set_title(g_dirty); break;
                case SDLK_2: g_sel.kind = SEL_BASIC; g_sel.basic_val = 1; g_layer = LAYER_TILE; set_title(g_dirty); break;
                case SDLK_3: g_sel.kind = SEL_BASIC; g_sel.basic_val = 2; g_layer = LAYER_TILE; set_title(g_dirty); break;
                case SDLK_4: g_sel.kind = SEL_BASIC; g_sel.basic_val = 3; g_layer = LAYER_TILE; set_title(g_dirty); break;
                case SDLK_5: g_sel.kind = SEL_BASIC; g_sel.basic_val = 4; g_layer = LAYER_TILE; set_title(g_dirty); break;
                case SDLK_6: g_sel.kind = SEL_BASIC; g_sel.basic_val = 5; g_layer = LAYER_TILE; set_title(g_dirty); break;
                case SDLK_EQUALS: case SDLK_PLUS:  zoom = std::min(zoom + 1, 48); break;
                case SDLK_MINUS:                    zoom = std::max(zoom - 1, 2);  break;
                case SDLK_RIGHTBRACKET: if (g_sel.kind==SEL_BASIC) g_sel.brush = std::min(g_sel.brush+1, 10); break;
                case SDLK_LEFTBRACKET:  if (g_sel.kind==SEL_BASIC) g_sel.brush = std::max(g_sel.brush-1, 0);  break;
                case SDLK_z: if (ev.key.keysym.mod & KMOD_CTRL) undo_pop(); break;
                }
                break;

            case SDL_MOUSEWHEEL: {
                if (ev.wheel.windowID == sprite_win_id) {
                    int old_tile_px = sprite_tile_px;
                    float factor = (ev.wheel.y > 0) ? 1.2f : 1.0f / 1.2f;
                    sprite_zoom = std::max(0.25f, std::min(8.0f, sprite_zoom * factor));
                    int new_tile_px = std::max(1, (int)(SPRITE_WIN_PX * sprite_zoom));
                    // zoom towards mouse cursor
                    int gx, gy, wx, wy;
                    SDL_GetGlobalMouseState(&gx, &gy);
                    SDL_GetWindowPosition(sprite_win, &wx, &wy);
                    float mx = (float)(gx - wx), my = (float)(gy - wy);
                    sprite_cam_x = (sprite_cam_x + mx) * new_tile_px / old_tile_px - mx;
                    sprite_cam_y = (sprite_cam_y + my) * new_tile_px / old_tile_px - my;
                    sprite_cam_x = std::max(0.0f, sprite_cam_x);
                    sprite_cam_y = std::max(0.0f, sprite_cam_y);
                    sprite_tile_px = new_tile_px;
                    break;
                }
                int old = zoom;
                zoom = std::max(2, std::min(48, zoom + ev.wheel.y));
                {
                    SDL_Rect cv = canvas_rect(ww, wh);
                    cam_x = (cam_x + cv.w * 0.5f) * zoom / old - cv.w * 0.5f;
                    cam_y = (cam_y + cv.h * 0.5f) * zoom / old - cv.h * 0.5f;
                    cam_x = std::max(0.0f, cam_x); cam_y = std::max(0.0f, cam_y);
                }
                break;
            }

            case SDL_MOUSEBUTTONDOWN: {
                int mx = ev.button.x, my = ev.button.y;
                // Events from the sprite picker window
                if (ev.button.windowID == sprite_win_id) {
                    if (ev.button.button == SDL_BUTTON_LEFT) {
                        int sc, sr;
                        if (screen_to_sheet(mx, my, &sc, &sr)) {
                            sheet_selecting = true;
                            sheet_drag_c0 = sheet_drag_c1 = sc;
                            sheet_drag_r0 = sheet_drag_r1 = sr;
                            commit_sheet_drag();
                        }
                    } else if (ev.button.button == SDL_BUTTON_RIGHT) {
                        sprite_panning = true;
                        sprite_pan_ox = mx; sprite_pan_oy = my;
                        sprite_pan_cx = sprite_cam_x; sprite_pan_cy = sprite_cam_y;
                    }
                    break;
                }
                // RMB: erase in depth/coll mode, pan in tile mode
                if (ev.button.button == SDL_BUTTON_RIGHT) {
                    if (g_layer != LAYER_TILE && mx >= PALETTE_W) {
                        painting = true;
                        undo_push();
                        last_stamp_tx = -9999; last_stamp_ty = -9999;
                        int tx, ty;
                        if (tile_at_screen(mx, my, ww, wh, &tx, &ty)) {
                            do_paint(tx, ty, true);
                            last_stamp_tx = tx; last_stamp_ty = ty;
                        }
                    } else {
                        panning = true; pan_ox = mx; pan_oy = my; pan_cx = cam_x; pan_cy = cam_y;
                    }
                }
                if (ev.button.button == SDL_BUTTON_LEFT) {
                    if (mx < PALETTE_W) {
                        int basic_item = (my - 40) / 34;
                        if (basic_item >= 0 && basic_item < BASIC_COUNT) {
                            g_sel.kind = SEL_BASIC;
                            g_sel.basic_val = BASIC_TILES[basic_item].val;
                            if (g_layer != LAYER_TILE) { g_layer = LAYER_TILE; set_title(g_dirty); }
                        }
                    } else {
                        painting = true;
                        undo_push();
                        last_stamp_tx = -9999; last_stamp_ty = -9999;
                        int tx, ty;
                        if (tile_at_screen(mx, my, ww, wh, &tx, &ty)) {
                            do_paint(tx, ty, false);
                            last_stamp_tx = tx; last_stamp_ty = ty;
                        }
                    }
                }
                break;
            }
            case SDL_MOUSEBUTTONUP:
                if (ev.button.button == SDL_BUTTON_RIGHT) {
                    if (ev.button.windowID == sprite_win_id) sprite_panning = false;
                    else { panning = false; painting = false; }
                }
                if (ev.button.button == SDL_BUTTON_LEFT) {
                    if (sheet_selecting) { commit_sheet_drag(); sheet_selecting = false; }
                    if (ev.button.windowID != sprite_win_id) painting = false;
                }
                break;

            case SDL_MOUSEMOTION: {
                int mx = ev.motion.x, my = ev.motion.y;
                // Sprite picker window — pan and sheet drag
                if (ev.motion.windowID == sprite_win_id) {
                    if (sprite_panning) {
                        sprite_cam_x = std::max(0.0f, sprite_pan_cx - (mx - sprite_pan_ox));
                        sprite_cam_y = std::max(0.0f, sprite_pan_cy - (my - sprite_pan_oy));
                    }
                    if (sheet_selecting) {
                        int sc, sr;
                        if (screen_to_sheet(mx, my, &sc, &sr)) {
                            sheet_drag_c1 = sc; sheet_drag_r1 = sr;
                            commit_sheet_drag();
                        }
                    }
                    break;
                }
                if (panning) {
                    cam_x = std::max(0.0f, pan_cx - (mx - pan_ox));
                    cam_y = std::max(0.0f, pan_cy - (my - pan_oy));
                }
                if (painting && mx >= PALETTE_W) {
                    int tx, ty;
                    // RMB erases in meta modes, LMB paints
                    bool erase = (ev.motion.state & SDL_BUTTON_RMASK) != 0;
                    if (tile_at_screen(mx, my, ww, wh, &tx, &ty)) {
                        if (g_layer != LAYER_TILE) {
                            // Meta layers: paint every cell individually (no grid-snap)
                            do_paint(tx, ty, erase);
                        } else if (g_sel.kind == SEL_BASIC) {
                            do_paint(tx, ty, erase);
                        } else {
                            int step_x = g_sel.cols, step_y = g_sel.rows;
                            int snapped_x = (last_stamp_tx == -9999) ? tx
                                : last_stamp_tx + ((tx - last_stamp_tx) / step_x) * step_x;
                            int snapped_y = (last_stamp_ty == -9999) ? ty
                                : last_stamp_ty + ((ty - last_stamp_ty) / step_y) * step_y;
                            if (snapped_x != last_stamp_tx || snapped_y != last_stamp_ty) {
                                do_paint(snapped_x, snapped_y, erase);
                                last_stamp_tx = snapped_x; last_stamp_ty = snapped_y;
                            }
                        }
                    }
                }
                break;
            }
            }
        }

        if (g_dirty) set_title(true);

        // WASD pan
        {
            const Uint8* ks = SDL_GetKeyboardState(nullptr);
            float speed = zoom * 20.0f;
            if (ks[SDL_SCANCODE_LEFT]  || ks[SDL_SCANCODE_A]) cam_x -= speed * dt;
            if (ks[SDL_SCANCODE_RIGHT] || ks[SDL_SCANCODE_D]) cam_x += speed * dt;
            if (ks[SDL_SCANCODE_UP]    || ks[SDL_SCANCODE_W]) cam_y -= speed * dt;
            if (ks[SDL_SCANCODE_DOWN]  || ks[SDL_SCANCODE_S]) cam_y += speed * dt;
            cam_x = std::max(0.0f, cam_x); cam_y = std::max(0.0f, cam_y);
        }

        // ---- Draw ----
        SDL_SetRenderDrawColor(ren, 18, 18, 18, 255);
        SDL_RenderClear(ren);

        SDL_Rect cv = canvas_rect(ww, wh);
        SDL_RenderSetClipRect(ren, &cv);

        // Tiles
        for (int ty = 0; ty < AREA_H; ty++) {
            int py = cv.y + (int)(ty * zoom - cam_y);
            if (py + zoom < cv.y || py >= cv.y + cv.h) continue;
            for (int tx = 0; tx < AREA_W; tx++) {
                int px = cv.x + (int)(tx * zoom - cam_x);
                if (px + zoom < cv.x || px >= cv.x + cv.w) continue;
                int val = g_canvas[ty][tx];
                if (val == 0) {
                    const BasicTile& bg = BASIC_TILES[g_bg[ty][tx]];
                    SDL_SetRenderDrawColor(ren, bg.r/2, bg.g/2, bg.b/2, 255);
                    SDL_Rect cell = { px, py, zoom, zoom };
                    SDL_RenderFillRect(ren, &cell);
                } else {
                    draw_tile_at(ren, sheet_tex, val, px, py, zoom);
                }
                if (zoom >= 5) {
                    SDL_SetRenderDrawColor(ren, 0, 0, 0, 50);
                    SDL_Rect cell = { px, py, zoom, zoom };
                    SDL_RenderDrawRect(ren, &cell);
                }
            }
        }

        // Depth overlay — blue
        for (int ty = 0; ty < AREA_H; ty++) {
            int py = cv.y + (int)(ty * zoom - cam_y);
            if (py + zoom < cv.y || py >= cv.y + cv.h) continue;
            for (int tx = 0; tx < AREA_W; tx++) {
                if (!g_depth[ty][tx]) continue;
                int px = cv.x + (int)(tx * zoom - cam_x);
                if (px + zoom < cv.x || px >= cv.x + cv.w) continue;
                uint8_t alpha = (g_layer == LAYER_DEPTH) ? 160 : 80;
                SDL_SetRenderDrawColor(ren, 40, 80, 255, alpha);
                SDL_Rect cell = { px, py, zoom, zoom };
                SDL_RenderFillRect(ren, &cell);
            }
        }

        // Collision overlay — red
        for (int ty = 0; ty < AREA_H; ty++) {
            int py = cv.y + (int)(ty * zoom - cam_y);
            if (py + zoom < cv.y || py >= cv.y + cv.h) continue;
            for (int tx = 0; tx < AREA_W; tx++) {
                if (!g_coll[ty][tx]) continue;
                int px = cv.x + (int)(tx * zoom - cam_x);
                if (px + zoom < cv.x || px >= cv.x + cv.w) continue;
                uint8_t alpha = (g_layer == LAYER_COLL) ? 160 : 80;
                SDL_SetRenderDrawColor(ren, 255, 50, 50, alpha);
                SDL_Rect cell = { px, py, zoom, zoom };
                SDL_RenderFillRect(ren, &cell);
            }
        }

        // Cursor outline — only when mouse is actually over the main window
        {
            int mx, my; Uint32 mbstate = SDL_GetMouseState(&mx, &my);
            int tx, ty;
            if (SDL_GetMouseFocus() == win && tile_at_screen(mx, my, ww, wh, &tx, &ty)) {
                bool erase = (mbstate & SDL_BUTTON_RMASK) != 0;
                if (g_layer == LAYER_DEPTH)
                    SDL_SetRenderDrawColor(ren, erase ? 255 : 80, erase ? 80 : 120, erase ? 80 : 255, 220);
                else if (g_layer == LAYER_COLL)
                    SDL_SetRenderDrawColor(ren, 255, erase ? 80 : 60, erase ? 80 : 60, 220);
                else
                    SDL_SetRenderDrawColor(ren, 255, 255, 255, 220);

                int fw = (g_sel.kind == SEL_SPRITE) ? g_sel.cols : (2*g_sel.brush+1);
                int fh = (g_sel.kind == SEL_SPRITE) ? g_sel.rows : (2*g_sel.brush+1);
                int ox = (g_sel.kind == SEL_BASIC)  ? -g_sel.brush : 0;
                int oy = (g_sel.kind == SEL_BASIC)  ? -g_sel.brush : 0;
                SDL_Rect outline = {
                    cv.x + (int)((tx + ox) * zoom - cam_x),
                    cv.y + (int)((ty + oy) * zoom - cam_y),
                    fw * zoom, fh * zoom
                };
                SDL_RenderDrawRect(ren, &outline);

                if (g_layer == LAYER_TILE && g_sel.kind == SEL_SPRITE && zoom >= 4 && sheet_tex) {
                    SDL_SetTextureAlphaMod(sheet_tex, 128);
                    for (int dy = 0; dy < g_sel.rows; dy++) {
                        for (int dx = 0; dx < g_sel.cols; dx++) {
                            int sc = g_sel.col + dx, sr = g_sel.row + dy;
                            int px = cv.x + (int)((tx+dx)*zoom - cam_x);
                            int py = cv.y + (int)((ty+dy)*zoom - cam_y);
                            SDL_Rect src = { sc*16, sr*16, 16, 16 };
                            SDL_Rect dst = { px, py, zoom, zoom };
                            SDL_RenderCopy(ren, sheet_tex, &src, &dst);
                        }
                    }
                    SDL_SetTextureAlphaMod(sheet_tex, 255);
                }
            }
        }

        SDL_RenderSetClipRect(ren, nullptr);

        // ---- Palette panel ----
        SDL_SetRenderDrawColor(ren, 28, 28, 28, 255);
        SDL_Rect palbg = { 0, 0, PALETTE_W, wh - STATUS_H };
        SDL_RenderFillRect(ren, &palbg);

        draw_text(ren, "TILES  (1-6)", 8, 10, 180, 180, 180);
        for (int i = 0; i < BASIC_COUNT; i++) {
            int iy = 36 + i * 34;
            const BasicTile& td = BASIC_TILES[i];
            bool sel = (g_layer == LAYER_TILE && g_sel.kind == SEL_BASIC && g_sel.basic_val == td.val);
            if (sel) {
                SDL_SetRenderDrawColor(ren, 255, 255, 100, 255);
                SDL_Rect hi = { 3, iy-3, PALETTE_W-6, 30 };
                SDL_RenderDrawRect(ren, &hi);
            }
            SDL_SetRenderDrawColor(ren, td.r, td.g, td.b, 255);
            SDL_Rect sw = { 8, iy+1, 20, 20 }; SDL_RenderFillRect(ren, &sw);
            char lbl[32];
            snprintf(lbl, sizeof(lbl), "%d %s", i+1, td.label);
            draw_text(ren, lbl, 34, iy+8, 210, 210, 210);
        }

        // Layer indicator strip
        int lay_y = 40 + BASIC_COUNT * 34 + 8;
        draw_text(ren, "LAYER (T/D/C):", 8, lay_y, 180, 180, 180);
        lay_y += 12;

        struct { const char* label; LayerMode mode; uint8_t r, g, b; } layers[] = {
            { "T TILES", LAYER_TILE,  200, 200, 200 },
            { "D DEPTH", LAYER_DEPTH,  80, 120, 255 },
            { "C COLL",  LAYER_COLL,  255,  80,  80 },
        };
        for (int i = 0; i < 3; i++) {
            bool active = (g_layer == layers[i].mode);
            if (active) {
                SDL_SetRenderDrawColor(ren, layers[i].r/3, layers[i].g/3, layers[i].b/3, 255);
                SDL_Rect hi = { 4, lay_y + i*14 - 1, PALETTE_W - 8, 12 };
                SDL_RenderFillRect(ren, &hi);
                SDL_SetRenderDrawColor(ren, layers[i].r, layers[i].g, layers[i].b, 255);
                SDL_RenderDrawRect(ren, &hi);
            }
            draw_text(ren, layers[i].label, 8, lay_y + i*14,
                      active ? layers[i].r : 140,
                      active ? layers[i].g : 140,
                      active ? layers[i].b : 140);
        }
        lay_y += 3 * 14 + 6;

        draw_text(ren, "RMB: erase",  8, lay_y, 140,140,140);
        lay_y += 12;

        draw_text(ren, "LMB drag: stamp", 8, lay_y,      140,140,140);
        draw_text(ren, "RMB/WASD: pan",   8, lay_y + 12, 140,140,140);
        draw_text(ren, "Wheel: zoom/scroll",8,lay_y + 24, 140,140,140);
        draw_text(ren, "[]: brush (basic)",8, lay_y + 36, 140,140,140);
        draw_text(ren, "C-z: undo",        8, lay_y + 48, 140,140,140);
        draw_text(ren, "C-s: save+build",  8, lay_y + 60, 140,140,140);

        SDL_SetRenderDrawColor(ren, 55, 55, 55, 255);
        SDL_RenderDrawLine(ren, PALETTE_W, 0, PALETTE_W, wh - STATUS_H);

        // Status bar
        SDL_SetRenderDrawColor(ren, 12, 12, 12, 255);
        SDL_Rect sb = { 0, wh-STATUS_H, ww, STATUS_H };
        SDL_RenderFillRect(ren, &sb);
        int mx, my; SDL_GetMouseState(&mx, &my);
        int tx, ty;
        bool main_has_mouse = (SDL_GetMouseFocus() == win);
        char sel_info[64];
        if (g_sel.kind == SEL_BASIC) {
            snprintf(sel_info, sizeof(sel_info), "basic=%s brush:%dx%d",
                     BASIC_TILES[g_sel.basic_val].label, 2*g_sel.brush+1, 2*g_sel.brush+1);
        } else {
            snprintf(sel_info, sizeof(sel_info), "sprite(%d,%d) %dx%d",
                     g_sel.col, g_sel.row, g_sel.cols, g_sel.rows);
        }
        const char* layer_name = (g_layer == LAYER_DEPTH) ? "DEPTH" :
                                  (g_layer == LAYER_COLL)  ? "COLL"  : "TILE";
        char status[220];
        if (main_has_mouse && tile_at_screen(mx, my, ww, wh, &tx, &ty))
            snprintf(status, sizeof(status), "%s | layer:%s | zoom:%d | (%d,%d) | %s | undo:%d",
                     AREA_NAME, layer_name, zoom, tx, ty, sel_info, g_undo_top);
        else
            snprintf(status, sizeof(status), "%s | layer:%s | zoom:%d | %s | undo:%d",
                     AREA_NAME, layer_name, zoom, sel_info, g_undo_top);
        draw_text(ren, status, 6, wh-STATUS_H+6, 160, 210, 160);

        SDL_RenderPresent(ren);

        // ---- Sprite picker window ----
        {
            int sww, swh; SDL_GetWindowSize(sprite_win, &sww, &swh);
            SDL_SetRenderDrawColor(sprite_ren, 18, 18, 18, 255);
            SDL_RenderClear(sprite_ren);
            for (int sr = 0; sr < SHEET_ROWS; sr++) {
                int py = sr * sprite_tile_px - (int)sprite_cam_y;
                if (py + sprite_tile_px < 0) continue;
                if (py >= swh) break;
                for (int sc = 0; sc < SHEET_COLS; sc++) {
                    int px = sc * sprite_tile_px - (int)sprite_cam_x;
                    if (px + sprite_tile_px < 0) continue;
                    if (px >= sww) break;
                    if (sprite_win_tex) {
                        SDL_Rect src = { sc*16, sr*16, 16, 16 };
                        SDL_Rect dst = { px, py, sprite_tile_px, sprite_tile_px };
                        SDL_RenderCopy(sprite_ren, sprite_win_tex, &src, &dst);
                    } else {
                        SDL_SetRenderDrawColor(sprite_ren, 60, 60, 80, 255);
                        SDL_Rect dst = { px, py, sprite_tile_px, sprite_tile_px };
                        SDL_RenderFillRect(sprite_ren, &dst);
                    }
                    if (sprite_tile_px >= 6) {
                        SDL_SetRenderDrawColor(sprite_ren, 0, 0, 0, 60);
                        SDL_Rect cell = { px, py, sprite_tile_px, sprite_tile_px };
                        SDL_RenderDrawRect(sprite_ren, &cell);
                    }
                }
            }
            auto sheet_rect = [&](int c0, int r0, int cols, int rows) -> SDL_Rect {
                return {
                    c0 * sprite_tile_px - (int)sprite_cam_x,
                    r0 * sprite_tile_px - (int)sprite_cam_y,
                    cols * sprite_tile_px, rows * sprite_tile_px
                };
            };
            if (g_sel.kind == SEL_SPRITE) {
                SDL_Rect hr = sheet_rect(g_sel.col, g_sel.row, g_sel.cols, g_sel.rows);
                SDL_SetRenderDrawColor(sprite_ren, 255, 255, 0, 255);
                SDL_RenderDrawRect(sprite_ren, &hr);
                SDL_Rect hr2 = { hr.x+1, hr.y+1, hr.w-2, hr.h-2 };
                SDL_RenderDrawRect(sprite_ren, &hr2);
            }
            if (sheet_selecting) {
                int c0 = std::min(sheet_drag_c0, sheet_drag_c1);
                int r0 = std::min(sheet_drag_r0, sheet_drag_r1);
                int cols = std::abs(sheet_drag_c1 - sheet_drag_c0) + 1;
                int rows = std::abs(sheet_drag_r1 - sheet_drag_r0) + 1;
                SDL_Rect hr = sheet_rect(c0, r0, cols, rows);
                SDL_SetRenderDrawColor(sprite_ren, 255, 180, 0, 255);
                SDL_RenderDrawRect(sprite_ren, &hr);
            }
            SDL_RenderPresent(sprite_ren);
        }

        SDL_Delay(14);
    }

    if (sheet_tex) SDL_DestroyTexture(sheet_tex);
    SDL_DestroyRenderer(ren); SDL_DestroyWindow(win);
    if (sprite_win_tex) SDL_DestroyTexture(sprite_win_tex);
    SDL_DestroyRenderer(sprite_ren); SDL_DestroyWindow(sprite_win);
    IMG_Quit(); SDL_Quit();
    return 0;
}
