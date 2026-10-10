#include "game_menu.h"
#include "crafting.h"
#include "battle.h"          // weapon_name
#include "dungeon.h"         // material_name
#include "core.h"            // draw_text, text_width, draw_nes_panel
#include "fc_palette.h"      // fc_draw_color
#include <SDL2/SDL_image.h>

// Icon sheets: 16px cells. Items one per Item in Item order, then the oil
// flask; weapons a row per ore, a column per weapon (art/items/).
static const char* ITEMS_SHEET   = "assets/items.png";
static const int   ICON          = 16;

enum { CMD_ITEMS, CMD_MAKE, CMD_CLOSE, CMD_COUNT };
static const char* CMD_NAMES[CMD_COUNT] = { "ITEMS", "MAKE", "CLOSE" };

// ── Layout (logical 640x480) ─────────────────────────────────────────────────
// The three windows' rects are in game_menu.h, shared with the debug menus.
static const int COL_W = 212, ROW_H = 40,  ROWS_SHOWN = 4;
static const int PANEL_Y = LST_Y + 12 + ROWS_SHOWN * ROW_H + 6;   // the divider under the list
static const int ACT_H   = 34;

static const SDL_Color WHITE  = { 252, 252, 252, 255 };
static const SDL_Color GREY   = { 120, 120, 120, 255 };
static const SDL_Color YELLOW = { 255, 255,  80, 255 };

static void text(SDL_Renderer* ren, const char* s, int x, int y, int scale, SDL_Color c) {
    draw_text(ren, s, x, y, scale, c.r, c.g, c.b);
}

// An ore's name short enough for a line: REALITY SHARD is SHARD.
static const char* ore_short(Material m) {
    return m == MAT_REALITY_SHARD ? "SHARD" : item_name(ore_item(m));
}

// ── The two lists ────────────────────────────────────────────────────────────
// MAKE is the whole recipe table, in its own order: everything there is to
// make, greyed where nothing can be done with it yet. ITEMS is what the
// player has: the weapons owned, then every item held.
struct Entry { bool weapon; int id; };
static int items_list(const Player* p, Entry out[]) {
    int n = 0;
    for (int w = 0; w < WEAPON_COUNT; w++)
        if (p->owned[w]) out[n++] = { true, w };
    for (int it = 0; it < ITEM_COUNT; it++)
        if (item_count(p, (Item)it) > 0) out[n++] = { false, it };
    return n;
}

enum { MAX_ENTRIES = 64 };

static int entry_count(const GameMenu* m, const Player* p) {
    Entry es[MAX_ENTRIES];
    return m->cmd == CMD_MAKE ? craft_count() : m->cmd == CMD_ITEMS ? items_list(p, es) : 0;
}

// ── What can be done with the selected thing ─────────────────────────────────
// Built fresh whenever needed, so the lines drawn and the line Z acts on are
// always the same list. MAKE: make it (a weapon in the best ore it can have)
// and, for a weapon owned, its two upgrades. ITEMS: take a weapon in hand.
// A line that cannot be done is still listed, greyed, with why.
enum ActKind { ACT_MAKE, ACT_EQUIP, ACT_FASTER, ACT_SHOTS, ACT_SLEEP };
struct Action {
    ActKind     kind;
    char        label[24];
    bool        can;
    const char* why;    // the answer to Z when it cannot
    int         ore;    // ACT_MAKE on a weapon: the ore it makes it in; -1 for none
};

static int make_actions(const Player* p, const Craft& c, Action out[3]) {
    int n = 0;
    Action& mk = out[n++];
    mk = { ACT_MAKE, "", craft_ready(p, c), "NEED MORE", -1 };
    if (c.is_weapon) {
        const Weapon& wp = p->arsenal[c.weapon];
        bool owned = p->owned[c.weapon];
        int  best  = craft_best_ore(p, c);
        // The ore it would be made in; with none affordable, the next one
        // worth having -- stone, or one better than it is now.
        mk.ore = best >= 0 ? best : owned ? (int)wp.material + 1 : MAT_STONE;
        if (mk.ore >= MAT_COUNT) { mk.ore = -1; SDL_snprintf(mk.label, sizeof(mk.label), "BEST ORE"); mk.why = "ALREADY BEST"; }
        else SDL_snprintf(mk.label, sizeof(mk.label), "MAKE IN %s", ore_short((Material)mk.ore));
        // Missing its book or its special part: Z says where that comes
        // from. (What is missing is listed by name under the actions.)
        Item miss = craft_missing(p, c);
        if (miss != ITEM_COUNT) mk.why = item_source(miss);
        if (owned) {
            bool fmax = wp.oil >= WEAPON_OIL_MAX, smax = wp.echo >= WEAPON_ECHO_MAX;
            Action& f = out[n++];
            f = { ACT_FASTER, "", !fmax && can_afford(p, oil_recipe(wp)), fmax ? "ALREADY MAX" : "NEED MORE", -1 };
            SDL_snprintf(f.label, sizeof(f.label), fmax ? "FASTER  MAX" : "FASTER %d/%d", wp.oil, (int)WEAPON_OIL_MAX);
            Action& s = out[n++];
            s = { ACT_SHOTS, "", !smax && can_afford(p, echo_recipe(wp)), smax ? "ALREADY MAX" : "NEED MORE", -1 };
            SDL_snprintf(s.label, sizeof(s.label), smax ? "MORE SHOTS  MAX" : "MORE SHOTS %d/%d", wp.echo, (int)WEAPON_ECHO_MAX);
        }
    } else if (craft_at_max(p, c)) {
        SDL_snprintf(mk.label, sizeof(mk.label), "ALREADY HAVE");
        mk.why = "ALREADY HAVE";
    } else if (c.needs != ITEM_COUNT && item_count(p, c.needs) <= 0) {
        SDL_snprintf(mk.label, sizeof(mk.label), "MAKE");
        mk.why = item_source(c.needs);
    } else {
        SDL_snprintf(mk.label, sizeof(mk.label), "MAKE");
    }
    return n;
}

static int item_actions(const GameMenu* m, const Player* p, const Entry& e, Action out[1]) {
    if (!e.weapon && e.id == ITEM_SLEEPING_BAG) {
        bool full = p->stats.hp >= p->stats.max_hp;
        out[0] = { ACT_SLEEP, "SLEEP", !m->chased && !full,
                   m->chased ? "NOT WHILE CHASED" : "HP ALREADY FULL", -1 };
        return 1;
    }
    if (!e.weapon || p->equipped == e.id) return 0;
    out[0] = { ACT_EQUIP, "EQUIP", true, "", -1 };
    return 1;
}

// The selected entry's actions, whichever page.
static int entry_actions(const GameMenu* m, const Player* p, int sel, Action out[3]) {
    if (m->cmd == CMD_MAKE) return make_actions(p, craft_at(sel), out);
    Entry es[MAX_ENTRIES];
    items_list(p, es);
    return item_actions(m, p, es[sel], out);
}

static void say(GameMenu* m, const char* note) { m->note = note; m->note_t = 1.5f; }

// ── Keys ─────────────────────────────────────────────────────────────────────
void game_menu_toggle(GameMenu* m) {
    m->open = !m->open;
    m->focus = FOCUS_COMMANDS;
    m->note_t = 0.0f;
}

void game_menu_update(GameMenu* m, Player* p, const Input* in, float dt) {
    if (!m->open) return;
    if (m->note_t > 0.0f) m->note_t -= dt;

    bool up    = input_pressed(in, SDL_SCANCODE_UP),   down  = input_pressed(in, SDL_SCANCODE_DOWN);
    bool left  = input_pressed(in, SDL_SCANCODE_LEFT), right = input_pressed(in, SDL_SCANCODE_RIGHT);
    bool ok    = input_pressed(in, SDL_SCANCODE_Z) || input_pressed(in, SDL_SCANCODE_RETURN);
    bool back  = input_pressed(in, SDL_SCANCODE_X);

    // A message answers the last press; moving on clears it.
    if (up || down || left || right || back) m->note_t = 0.0f;

    switch (m->focus) {
    case FOCUS_COMMANDS:
        if (up)   m->cmd = (m->cmd + CMD_COUNT - 1) % CMD_COUNT;
        if (down) m->cmd = (m->cmd + 1) % CMD_COUNT;
        if (back || (ok && m->cmd == CMD_CLOSE)) { m->open = false; return; }
        if (ok) { m->focus = FOCUS_LIST; m->sel = 0; }
        return;

    case FOCUS_LIST: {
        if (back) { m->focus = FOCUS_COMMANDS; return; }
        int n = entry_count(m, p);
        if (n == 0) return;
        if (left  && m->sel % 2 == 1)                   m->sel--;
        if (right && m->sel % 2 == 0 && m->sel + 1 < n) m->sel++;
        if (up    && m->sel - 2 >= 0)                   m->sel -= 2;
        if (down) {
            if (m->sel + 2 < n)                 m->sel += 2;
            else if ((m->sel / 2 + 1) * 2 < n)  m->sel = n - 1;   // a short last row: its only entry
        }
        if (m->sel >= n) m->sel = n - 1;
        Action acts[3];
        if (ok && entry_actions(m, p, m->sel, acts) > 0) { m->focus = FOCUS_ACTIONS; m->act = 0; }
        return;
    }

    case FOCUS_ACTIONS: {
        if (back) { m->focus = FOCUS_LIST; return; }
        Action acts[3];
        int n = entry_actions(m, p, m->sel, acts);
        if (n == 0) { m->focus = FOCUS_LIST; return; }
        if (m->act >= n) m->act = n - 1;
        if (up   && m->act > 0)     m->act--;
        if (down && m->act + 1 < n) m->act++;
        if (!ok) return;
        const Action& a = acts[m->act];
        bool done = false;
        if (a.can) {
            if (m->cmd == CMD_ITEMS) {
                Entry es[MAX_ENTRIES];
                items_list(p, es);
                done = a.kind == ACT_SLEEP ? craft_sleep(p) : craft_equip(p, (WeaponType)es[m->sel].id);
            } else {
                const Craft& c = craft_at(m->sel);
                done = a.kind == ACT_MAKE   ? craft_make(p, c)
                     : a.kind == ACT_FASTER ? craft_oil(p, c.weapon)
                     :                        craft_echo(p, c.weapon);
            }
        }
        static const char* DONE[] = { "MADE!", "EQUIPPED", "FASTER!", "MORE SHOTS!", "RESTED! HP FULL" };
        say(m, done ? (a.kind == ACT_SLEEP && p->sleeping_bag == 0 ? "RESTED! THE BAG WORE OUT" : DONE[a.kind]) : a.why);
        // The list may have changed shape (EQUIP gone once in hand).
        int now = entry_actions(m, p, m->sel, acts);
        if (now == 0) m->focus = FOCUS_LIST;
        else if (m->act >= now) m->act = now - 1;
        return;
    }
    }
}

// ── Drawing ──────────────────────────────────────────────────────────────────
static void load_sheets(GameMenu* m, SDL_Renderer* ren) {
    if (m->tried) return;
    m->tried = true;
    m->items   = IMG_LoadTexture(ren, ITEMS_SHEET);
    m->weapons = IMG_LoadTexture(ren, WEAPON_ICON_SHEET);
    if (!m->items)   SDL_Log("menu icons %s: %s", ITEMS_SHEET, IMG_GetError());
    if (!m->weapons) SDL_Log("menu icons %s: %s", WEAPON_ICON_SHEET, IMG_GetError());
}

// An icon `size` pixels square. Nothing if its sheet is missing.
static void draw_item_icon(const GameMenu* m, SDL_Renderer* ren, int icon, int x, int y, int size) {
    if (!m->items) return;
    SDL_Rect src = { icon * ICON, 0, ICON, ICON }, dst = { x, y, size, size };
    SDL_RenderCopy(ren, m->items, &src, &dst);
}

static void draw_weapon_icon(const GameMenu* m, SDL_Renderer* ren, WeaponType w, Material ore,
                             int x, int y, int size) {
    if (!m->weapons) return;
    SDL_Rect src = { (int)w * ICON, (int)ore * ICON, ICON, ICON }, dst = { x, y, size, size };
    SDL_RenderCopy(ren, m->weapons, &src, &dst);
}

// One picture in the small box: an item, or a weapon in an ore, with an
// amount ("3", grey when the player has too few) or a tag ("1/3") under it.
struct Pic { bool weapon; int id; int ore; int amount; bool short_of; const char* tag; };

static void draw_pic(const GameMenu* m, SDL_Renderer* ren, const Pic& pc, int x, int y, int size) {
    if (pc.weapon) draw_weapon_icon(m, ren, (WeaponType)pc.id, (Material)pc.ore, x, y, size);
    else           draw_item_icon(m, ren, pc.id, x, y, size);
    char buf[12];
    if (pc.amount > 0) SDL_snprintf(buf, sizeof(buf), "%d", pc.amount);
    else if (pc.tag)   SDL_snprintf(buf, sizeof(buf), "%s", pc.tag);
    else return;
    text(ren, buf, x + size - text_width(buf, 1), y + size - 4, 1, pc.short_of ? GREY : WHITE);
}

// The small box as a conversion: what goes in, stacked down the left, an
// arrow, and what comes out -- so a make or an upgrade shows the thing it
// starts from and the thing it becomes.
static void draw_conversion(const GameMenu* m, SDL_Renderer* ren, const Pic in[], int n, const Pic& out) {
    const int top = PRE_Y + 10, h = PRE_H - 54;
    // 32px pictures 36 apart while they fit; a long recipe packs them closer.
    int step = n > 0 && h / n < 36 ? h / n : 36;
    int size = step - 4 < 32 ? step - 4 : 32;
    int total = n * step - 4;
    int y = top + (h - total) / 2;
    for (int i = 0; i < n; i++, y += step) draw_pic(m, ren, in[i], PRE_X + 12 + (32 - size) / 2, y, size);

    int cy = top + h / 2;
    fc_draw_color(ren, 252, 252, 252, 255);
    SDL_Rect shaft = { PRE_X + 54, cy - 1, 18, 3 };
    SDL_RenderFillRect(ren, &shaft);
    for (int k = 0; k < 4; k++) {   // the head, narrowing to its point
        SDL_Rect r = { PRE_X + 72 + k * 2, cy - 7 + k * 2, 2, 15 - k * 4 };
        SDL_RenderFillRect(ren, &r);
    }
    draw_pic(m, ren, out, PRE_X + 88, cy - 24, 48);
}

// A cost as pictures with their amounts, appended to out from index n.
static int cost_pics(const Player* p, const Recipe& r, Pic out[], int n) {
    for (int i = 0; i < r.n; i++)
        out[n++] = { false, r.c[i].item, 0, r.c[i].amount,
                     item_count(p, r.c[i].item) < r.c[i].amount, nullptr };
    return n;
}

// What an action turns into what, for the small box; 0 if it is not a
// conversion (EQUIP, a weapon already in the best ore). `was` and `will`
// hold the level tags.
static int action_pics(const Player* p, const Craft* c, WeaponType w, const Action& a,
                       Pic ins[], Pic* out, char was[8], char will[8]) {
    int n = 0;
    if (a.kind == ACT_MAKE && c) {
        if (c->is_weapon) {
            if (a.ore < 0) return 0;
            if (p->owned[c->weapon])    // the weapon it starts from
                ins[n++] = { true, c->weapon, (int)p->arsenal[c->weapon].material, 0, false, nullptr };
            n = cost_pics(p, craft_recipe(p, *c, a.ore), ins, n);
            if (c->needs != ITEM_COUNT)   // its book: shown, but kept
                ins[n++] = { false, c->needs, 0, 0, item_count(p, c->needs) <= 0, "KEEP" };
            *out = { true, c->weapon, a.ore, 0, false, nullptr };
        } else {
            if (craft_at_max(p, *c)) return 0;   // nothing more to make
            n = cost_pics(p, craft_recipe(p, *c, -1), ins, n);
            if (c->needs != ITEM_COUNT)   // the book: shown, but kept
                ins[n++] = { false, c->needs, 0, 0, item_count(p, c->needs) <= 0, "KEEP" };
            *out = { false, c->item, 0, 0, false, nullptr };
        }
        return n;
    }
    if (a.kind == ACT_FASTER || a.kind == ACT_SHOTS) {
        const Weapon& wp = p->arsenal[w];
        bool faster = a.kind == ACT_FASTER;
        int lvl = faster ? wp.oil : wp.echo, max = faster ? WEAPON_OIL_MAX : WEAPON_ECHO_MAX;
        if (lvl >= max) return 0;
        SDL_snprintf(was,  8, "%d/%d", lvl, max);
        SDL_snprintf(will, 8, "%d/%d", lvl + 1, max);
        ins[n++] = { true, w, wp.material, 0, false, was };
        n = cost_pics(p, faster ? oil_recipe(wp) : echo_recipe(wp), ins, n);
        *out = { true, w, wp.material, 0, false, will };
    }
    return n;
}

// Words laid out across lines of the panel, wrapping between them.
static void draw_wrapped(SDL_Renderer* ren, const char* words[], int n, int x, int y, int width, SDL_Color c) {
    int cx = x;
    for (int i = 0; i < n; i++) {
        char buf[32];
        SDL_snprintf(buf, sizeof(buf), i + 1 < n ? "%s," : "%s", words[i]);
        int w = text_width(buf, 2);
        if (cx > x && cx + w > x + width) { cx = x; y += 24; }
        text(ren, buf, cx, y, 2, c);
        cx += w + 16;
    }
}

void game_menu_draw(GameMenu* m, const Player* p, SDL_Renderer* ren) {
    if (!m->open) return;
    load_sheets(m, ren);

    // Command window.
    draw_nes_panel(ren, CMD_X, CMD_Y, CMD_W, CMD_H);
    for (int i = 0; i < CMD_COUNT; i++) {
        int y = CMD_Y + 12 + i * 24;
        bool on = m->cmd == i, here = on && m->focus == FOCUS_COMMANDS;
        if (on) text(ren, ">", CMD_X + 10, y, 2, here ? YELLOW : GREY);
        text(ren, CMD_NAMES[i], CMD_X + 28, y, 2, here ? YELLOW : WHITE);
    }

    Entry items[MAX_ENTRIES];
    int n_items = items_list(p, items);
    int n = m->cmd == CMD_MAKE ? craft_count() : m->cmd == CMD_ITEMS ? n_items : 0;
    int sel = m->sel < n ? m->sel : n - 1;
    bool in_list = m->focus != FOCUS_COMMANDS;
    const Weapon& eq = equipped_weapon(p);

    Action acts[3];
    int na = (in_list && sel >= 0) ? entry_actions(m, p, sel, acts) : 0;

    if (m->cmd != CMD_CLOSE) {
        draw_nes_panel(ren, LST_X, LST_Y, LST_W, LST_H);
        int top = in_list ? (sel / 2) - (ROWS_SHOWN - 1) : 0;   // first row shown, keeping sel in view
        if (top < 0) top = 0;
        if (n == 0) text(ren, "NOTHING YET", LST_X + 20, LST_Y + 20, 2, GREY);
        for (int e = top * 2; e < n && e < (top + ROWS_SHOWN) * 2; e++) {
            int cx = LST_X + 12 + (e % 2) * COL_W;
            int ry = LST_Y + 12 + (e / 2 - top) * ROW_H;
            bool on = in_list && e == sel;
            if (on) text(ren, ">", cx, ry + 8, 2, m->focus == FOCUS_LIST ? YELLOW : GREY);
            char name[24];
            SDL_Color c = WHITE;
            if (m->cmd == CMD_MAKE) {
                const Craft& cr = craft_at(e);
                SDL_snprintf(name, sizeof(name), "%s", craft_name(cr));
                // Grey when nothing on it can be done now.
                Action ea[3];
                int ne = make_actions(p, cr, ea);
                bool any = false;
                for (int i = 0; i < ne; i++) any = any || ea[i].can;
                if (!any) c = GREY;
            } else if (items[e].weapon) {
                WeaponType w = (WeaponType)items[e].id;
                SDL_snprintf(name, sizeof(name), "%s", weapon_name(w));
                if (p->equipped == w) text(ren, "E", cx + COL_W - 8 - text_width("E", 2), ry + 8, 2, YELLOW);
            } else {
                Item it = (Item)items[e].id;
                // Short names fit the column; under the list is the full one.
                SDL_snprintf(name, sizeof(name), "%s", it == ITEM_GRAVESTONE    ? "GRAVE"
                                                     : it == ITEM_REALITY_SHARD ? "SHARD"
                                                     : it == ITEM_OLD_SPEARHEAD ? "SPEARHEAD"
                                                     : it == ITEM_REAPERS_EDGE  ? "REAPER EDGE"
                                                     : it == ITEM_WHITE_FUR     ? "FUR"
                                                     : it == ITEM_SLEEPING_BAG  ? "SLEEP BAG" : item_name(it));
                // How many, for a material, or the uses left in the bag; a
                // book or a part is just had.
                if (item_is_material(it) || it == ITEM_SLEEPING_BAG) {
                    char cnt[8];
                    SDL_snprintf(cnt, sizeof(cnt), "%d", item_count(p, it));
                    text(ren, cnt, cx + COL_W - 8 - text_width(cnt, 2), ry + 8, 2, WHITE);
                }
            }
            text(ren, name, cx + 20, ry + 8, 2, on && m->focus == FOCUS_LIST ? YELLOW : c);
        }

        // Under the list: what the selected thing is, and what can be done.
        fc_draw_color(ren, 252, 252, 252, 255);
        SDL_Rect div = { LST_X + 8, PANEL_Y, LST_W - 16, 2 };
        SDL_RenderFillRect(ren, &div);
        char line[48];
        int ty = PANEL_Y + 10, ly = ty + 26;
        bool item_material = false;
        if (sel >= 0 && m->cmd == CMD_MAKE) {
            const Craft& cr = craft_at(sel);
            if (cr.is_weapon && p->owned[cr.weapon])
                SDL_snprintf(line, sizeof(line), "%s %s%s", ore_short(p->arsenal[cr.weapon].material),
                             weapon_name(cr.weapon), p->equipped == cr.weapon ? "  IN HAND" : "");
            else
                SDL_snprintf(line, sizeof(line), "%s", craft_name(cr));
            text(ren, line, LST_X + 16, ty, 2, WHITE);
        } else if (sel >= 0 && m->cmd == CMD_ITEMS && items[sel].weapon) {
            WeaponType w = (WeaponType)items[sel].id;
            SDL_snprintf(line, sizeof(line), "%s %s%s", ore_short(p->arsenal[w].material),
                         weapon_name(w), p->equipped == w ? "  IN HAND" : "");
            text(ren, line, LST_X + 16, ty, 2, WHITE);
        } else if (sel >= 0 && m->cmd == CMD_ITEMS && items[sel].id == ITEM_SLEEPING_BAG) {
            // The bag: its uses left, and SLEEP under it like a weapon's EQUIP.
            SDL_snprintf(line, sizeof(line), "SLEEPING BAG  %d/%d LEFT", p->sleeping_bag, (int)SLEEPING_BAG_USES);
            text(ren, line, LST_X + 16, ty, 2, WHITE);
        } else if (sel >= 0 && m->cmd == CMD_ITEMS) {
            Item it = (Item)items[sel].id;
            SDL_snprintf(line, sizeof(line), "%s  X%d", item_name(it), item_count(p, it));
            text(ren, line, LST_X + 16, ty, 2, WHITE);
            const char* uses[8];
            int nu = item_uses(it, uses, 8);
            text(ren, "USED FOR:", LST_X + 16, ly + 8, 2, GREY);
            if (nu == 0) { const char* none[] = { "NOTHING YET" }; draw_wrapped(ren, none, 1, LST_X + 16, ly + 34, LST_W - 32, GREY); }
            else         draw_wrapped(ren, uses, nu, LST_X + 16, ly + 34, LST_W - 32, WHITE);
            if (const char* src = item_source(it))
                text(ren, src, LST_X + 16, LST_Y + LST_H - 56, 2, GREY);
            item_material = true;
        }
        if (!item_material) {
            // The list's selected entry's actions; until Z moves into them,
            // still shown so the player can see what is on offer.
            if (sel >= 0 && !in_list) na = entry_actions(m, p, sel, acts);
            for (int i = 0; i < na; i++) {
                int ay = ly + i * ACT_H;
                bool on = m->focus == FOCUS_ACTIONS && m->act == i;
                if (on) text(ren, ">", LST_X + 12, ay + 8, 2, YELLOW);
                text(ren, acts[i].label, LST_X + 30, ay + 8, 2, on ? YELLOW : acts[i].can ? WHITE : GREY);
            }
            // What the highlighted line still lacks, by name, in the order its
            // pictures stand in the small box -- so each sprite there has a
            // name. Gives way to the answer to Z.
            if (m->cmd == CMD_MAKE && na > 0 && sel >= 0 && !(m->note_t > 0.0f && m->note)) {
                const Craft& cr = craft_at(sel);
                int ai = m->focus == FOCUS_ACTIONS ? m->act : 0;
                Pic pics[6], o;
                char a1[8], a2[8];
                int np = action_pics(p, &cr, cr.weapon, acts[ai], pics, &o, a1, a2);
                const char* miss[6];
                int nm = 0;
                for (int i = 0; i < np; i++)
                    if (pics[i].short_of) miss[nm++] = pics[i].weapon ? weapon_name((WeaponType)pics[i].id)
                                                                      : item_name((Item)pics[i].id);
                if (nm > 0) {
                    int ny = ly + na * ACT_H + 6, nx = LST_X + 16 + text_width("NEEDS: ", 2);
                    text(ren, "NEEDS:", LST_X + 16, ny, 2, GREY);
                    draw_wrapped(ren, miss, nm, nx, ny, LST_X + LST_W - 16 - nx, WHITE);
                }
            }
        }
        // The answer to the last Z, at the foot of the window.
        if (m->note_t > 0.0f && m->note)
            text(ren, m->note, LST_X + 16, LST_Y + LST_H - 28, 2, YELLOW);
    }

    // The small box: the selected thing, large -- or, for a make or an
    // upgrade, what goes in, an arrow, and what comes out (the highlighted
    // action's, or the first one on offer). The weapon in hand while the
    // commands have focus. And the two keys there are.
    draw_nes_panel(ren, PRE_X, PRE_Y, PRE_W, PRE_H);
    Pic big = { true, eq.type, eq.material, 0, false, nullptr };
    Pic ins[6];
    int nin = 0;
    Pic out = {};
    char was[8], will[8];
    if (in_list && n > 0) {
        const Craft* cr = nullptr;
        WeaponType w = eq.type;
        if (m->cmd == CMD_MAKE) {
            cr = &craft_at(sel);
            w = cr->weapon;
            int ore = cr->is_weapon ? (p->owned[w] ? (int)p->arsenal[w].material : MAT_STONE) : 0;
            big = cr->is_weapon ? Pic{ true, w, ore, 0, false, nullptr } : Pic{ false, cr->item, 0, 0, false, nullptr };
        } else if (items[sel].weapon) {
            w = (WeaponType)items[sel].id;
            big = { true, w, p->arsenal[w].material, 0, false, nullptr };
        } else {
            big = { false, items[sel].id, 0, 0, false, nullptr };
        }
        int ai = m->focus == FOCUS_ACTIONS ? m->act : 0;
        if (na > 0 && ai < na) nin = action_pics(p, cr, w, acts[ai], ins, &out, was, will);
    }
    if (nin > 0) draw_conversion(m, ren, ins, nin, out);
    else         draw_pic(m, ren, big, PRE_X + (PRE_W - 64) / 2, PRE_Y + 10 + (PRE_H - 54 - 64) / 2, 64);
    text(ren, "Z: CHOOSE", PRE_X + 14, PRE_Y + PRE_H - 36, 1, GREY);
    text(ren, "X: BACK",   PRE_X + 14, PRE_Y + PRE_H - 22, 1, GREY);
}

void game_menu_draw_item(GameMenu* m, SDL_Renderer* ren, int item, int x, int y, int size) {
    load_sheets(m, ren);
    draw_item_icon(m, ren, item, x, y, size);
}

void game_menu_draw_weapon(GameMenu* m, SDL_Renderer* ren, WeaponType w, Material ore,
                           int x, int y, int size, Uint8 shade) {
    load_sheets(m, ren);
    if (!m->weapons) return;
    SDL_SetTextureColorMod(m->weapons, shade, shade, shade);
    draw_weapon_icon(m, ren, w, ore, x, y, size);
    SDL_SetTextureColorMod(m->weapons, 255, 255, 255);
}

const char* game_menu_ore_name(Material m) { return ore_short(m); }

void game_menu_free(GameMenu* m) {
    if (m->items)   SDL_DestroyTexture(m->items);
    if (m->weapons) SDL_DestroyTexture(m->weapons);
    m->items = m->weapons = nullptr;
    m->tried = false;
}
