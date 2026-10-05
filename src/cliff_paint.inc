// The cliff walls, painted. Included by src/tilemap.cpp after cliff_cell_at().
//
// The island sprites on the sheet (row ISLAND_ROW0) stay the shape: what they
// leave keyed out is ground, and the black they draw against that ground is
// the outline. Everything else a wall sprite draws -- its flat brown and the
// streaks through it -- is repainted here from one tileable rock texture
// (art/cliffs/cliff_texture.aseprite -> cliff_texture.inc) read in world
// pixels, so a face runs on across tile seams with no repeat at the tile, in
// the four tones of the mountain's ore (ore_tones.inc, row 0 for a mountain
// with no cave). Scree and the beaded line keep their own pixels, recoloured.
//
// Painted a chunk of CP_CHUNK x CP_CHUNK tiles at a time, on the main thread,
// when first drawn; the chunks are thrown away whenever the islands or their
// ores change (cliff_paint_invalidate, which world generation calls from its
// thread, so it only bumps a counter).
#include "cliff_texture.inc"
#include "ore_tones.inc"

enum { CP_CHUNK = 16, CP_CACHE = 64 };

// Each island sprite's pixels as read off the sheet: 0 key, 1 brown, 2 black.
static unsigned char s_cliff_px[ISLAND_SPRITES][16][16];
static bool s_cliff_px_ready = false;
static std::atomic<int> s_cliff_paint_version{0};

static struct CliffChunk {
    SDL_Texture* tex;
    int cx, cy, version;
    unsigned last_used;
} s_cliff_chunks[CP_CACHE];
static unsigned s_cliff_chunk_clock = 0;
static const Tilemap* s_cliff_paint_map = nullptr;   // the map being drawn, for its cave mouths

static void cliff_paint_invalidate(void) { s_cliff_paint_version++; }

static void cliff_paint_load(SDL_Surface* rgba) {
    s_cliff_px_ready = false;
    for (int i = 1; i < ISLAND_SPRITES; i++) {
        int y0 = (ISLAND_ROW0 + i / TOWN0_SHEET_COLS) * 16, x0 = (i % TOWN0_SHEET_COLS) * 16;
        if (y0 + 16 > rgba->h || x0 + 16 > rgba->w) return;
        for (int py = 0; py < 16; py++)
            for (int px = 0; px < 16; px++) {
                const unsigned char* p = (const unsigned char*)rgba->pixels
                                       + (size_t)(y0 + py) * rgba->pitch + (size_t)(x0 + px) * 4;
                s_cliff_px[i][py][px] = (p[0] == 255 && p[1] == 0 && p[2] == 0) ? 0
                                      : (p[0] | p[1] | p[2]) ? 1 : 2;
            }
    }
    s_cliff_px_ready = true;
}

// Whether the world pixel (wx, wy) is wall rock: what a rock sprite closes
// (s_cliff_ink -- its drawing with the pinholes and slots filled, the same
// mask the feet are stopped by), and any pixel left with rock on all four
// sides across a tile seam. Scree and the line are not rock: they lie on the
// ground in front of or behind it. Nor is the wall's foot a cave mouth lifts
// (cave_foot_lifted), which is drawn and walked as ground: the wall's outline
// runs round it rather than being cut by it.
static bool cliff_paint_ink(int wx, int wy) {
    int tx = (wx >= 0 ? wx : wx - 15) / 16, ty = (wy >= 0 ? wy : wy - 15) / 16;
    int ax = wx - tx * 16, ay = wy - ty * 16;
    int c = cliff_cell_at(tx, ty);
    if (!c || ISLAND_KIND[c] != 1 || !((s_cliff_ink[c][ay] >> ax) & 1)) return false;
    return !(s_cliff_paint_map && cave_foot_lifted(s_cliff_paint_map, tx, ty, ax, ay));
}
static bool cliff_paint_rock(int wx, int wy) {
    return cliff_paint_ink(wx, wy) ||
           (cliff_paint_ink(wx - 1, wy) && cliff_paint_ink(wx + 1, wy) &&
            cliff_paint_ink(wx, wy - 1) && cliff_paint_ink(wx, wy + 1));
}

static unsigned cliff_paint_hash(unsigned v) {
    v ^= v >> 16; v *= 0x7FEB352Du; v ^= v >> 15; v *= 0x846CA68Bu; v ^= v >> 16;
    return v;
}

// The texture's tone at a world pixel of mountain id: each mountain reads
// the texture from its own offset, so neighbours do not share a pattern.
static int cliff_paint_tone(int id, int wx, int wy) {
    unsigned h = cliff_paint_hash((unsigned)id * 2654435761u + 1u);
    int ox = (int)(h & 127u), oy = (int)((h >> 8) & 127u);
    return CLIFF_TEX[(wy + oy) & (CLIFF_TEX_N - 1)][(wx + ox) & (CLIFF_TEX_N - 1)] - '0';
}

static uint32_t cliff_paint_rgba(const unsigned char* c) {   // ABGR8888 in memory: R, G, B, A
    return (uint32_t)c[0] | ((uint32_t)c[1] << 8) | ((uint32_t)c[2] << 16) | 0xFF000000u;
}

static void cliff_paint_chunk(SDL_Texture* tex, int cx, int cy) {
    static uint32_t buf[CP_CHUNK * 16 * CP_CHUNK * 16];
    const int W = CP_CHUNK * 16;
    memset(buf, 0, sizeof buf);
    for (int ty = 0; ty < CP_CHUNK; ty++)
        for (int tx = 0; tx < CP_CHUNK; tx++) {
            int x = cx * CP_CHUNK + tx, y = cy * CP_CHUNK + ty;
            if (x >= MAP_WIDTH || y >= MAP_HEIGHT) continue;
            int c = s_island_cell[y][x];
            if (!c) continue;
            int id = s_island_id[y][x];
            int mat = id ? s_island_mat[id] : -1;
            const unsigned char (*ramp)[3] = ORE_TONES[mat >= 0 ? 1 + mat : 0];
            for (int py = 0; py < 16; py++)
                for (int px = 0; px < 16; px++) {
                    int v = s_cliff_px[c][py][px];
                    int wx = x * 16 + px, wy = y * 16 + py;
                    const unsigned char* col;
                    if (ISLAND_KIND[c] != 1) {
                        if (!v) continue;
                        col = ramp[v == 1 ? 2 : 0];          // scree, line: base and ink
                    } else {
                        if (!cliff_paint_rock(wx, wy)) continue;
                        // The outline is the rock's own rim: every rock pixel
                        // against anything that is not rock, whatever the
                        // sprite drew there -- so it is one pixel, unbroken,
                        // and on the edge the feet are stopped at.
                        bool edge = false;
                        for (int dy = -1; dy <= 1 && !edge; dy++)
                                for (int dx = -1; dx <= 1 && !edge; dx++)
                                    if ((dx || dy) && !cliff_paint_rock(wx + dx, wy + dy)) edge = true;
                        col = ramp[edge ? 0 : cliff_paint_tone(id, wx, wy)];
                    }
                    buf[(ty * 16 + py) * W + tx * 16 + px] = cliff_paint_rgba(col);
                }
        }
    SDL_UpdateTexture(tex, NULL, buf, W * 4);
}

// The cache slot holding (kx, ky) at this version, painted by paint() into a
// w x h texture when it is not there yet; null if a texture cannot be made.
// ponytail: linear scan; a map from key to slot if a cache grows past ~100.
template <typename Paint>
static CliffChunk* cliff_cache_get(SDL_Renderer* renderer, CliffChunk* cache, int n,
                                   int kx, int ky, int w, int h, Paint paint) {
    int ver = s_cliff_paint_version;
    CliffChunk* slot = nullptr;
    for (int i = 0; i < n && !slot; i++)
        if (cache[i].tex && cache[i].cx == kx && cache[i].cy == ky && cache[i].version == ver) slot = &cache[i];
    if (!slot) {
        slot = &cache[0];
        for (int i = 1; i < n; i++) {
            CliffChunk& k = cache[i];
            if (!k.tex || k.version != ver) { slot = &k; break; }
            if (k.last_used < slot->last_used) slot = &k;
        }
        if (!slot->tex) {
            slot->tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STATIC, w, h);
            if (!slot->tex) return nullptr;
            SDL_SetTextureBlendMode(slot->tex, SDL_BLENDMODE_BLEND);
        }
        paint(slot->tex);
        slot->cx = kx; slot->cy = ky; slot->version = ver;
    }
    slot->last_used = ++s_cliff_chunk_clock;
    return slot;
}

// Draw the painted cliff over tile (x, y); false when there is nothing to
// paint with, and the caller blits the sheet cell as before.
static bool cliff_paint_draw(SDL_Renderer* renderer, const Tilemap* map, int x, int y, int sx, int sy, int size) {
    if (!s_cliff_px_ready || !s_island_cell[y][x]) return false;
    s_cliff_paint_map = map;
    int cx = x / CP_CHUNK, cy = y / CP_CHUNK;
    CliffChunk* slot = cliff_cache_get(renderer, s_cliff_chunks, CP_CACHE, cx, cy, CP_CHUNK * 16, CP_CHUNK * 16,
                                       [&](SDL_Texture* t) { cliff_paint_chunk(t, cx, cy); });
    if (!slot) return false;
    SDL_Rect src = { (x - cx * CP_CHUNK) * 16, (y - cy * CP_CHUNK) * 16, 16, 16 };
    SDL_Rect dst = { sx, sy, size, size };
    SDL_RenderCopy(renderer, slot->tex, &src, &dst);
    return true;
}
