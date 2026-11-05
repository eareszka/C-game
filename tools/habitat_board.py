"""Habitat review board: which enemies spawn where, one panel per habitat.

Edit HABITATS and re-run; it writes art/enemies/habitat_board_N.png, pages
small enough for an image viewer. Review only:
the game does not read this yet (see the plan for include/habitat.h).
Tiers and the ready gate are read from include/enemy.h and include/ready.h,
names from src/main.cpp, and each sprite is the front view's first frame of its
sheet in ENEMY_SHEETS (src/battle.cpp), cut as the battle cuts it.
"""
import re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "enemies" / "habitat_board.png"

# name, where, kin, ids[, reachable tiers]. Wild habitats never take elites
# (wilds.cpp), so elites are listed only under dungeons. Raised ground is no
# biome of its own: the wilds there use whatever biome it is.
#
# A cave is one of seven ore kinds, and its ore is set by its difficulty
# (MATERIALS in src/dungeon.cpp), so each kind only ever reaches a few tiers:
# its band against TIER_CUTS, plus the tier below that every pool mixes in,
# plus elites from difficulty 0.51 (veyrite and deeper).
CAVE_STONE   = ["LOW", "MEDIUM", "UPPER"]               # .00-.372
CAVE_BRONZE  = ["MEDIUM", "UPPER", "HARD"]              # .372-.452
CAVE_EMERALD = ["UPPER", "HARD", "SEVERE"]              # .452-.494
CAVE_DEEP    = ["HARD", "SEVERE", "ELITE"]              # .494 and on
# The hardest places in the world, by the user's ranking: reality shard caves
# and catacombs at the top (no tier below mixed in), the ocean next.
HARDEST      = ["SEVERE", "ELITE"]
OCEAN_TIERS  = ["HARD", "SEVERE", "ELITE"]
HABITATS = [
    ("GRASSLAND", "wilds: grass, flat or raised", "FOREST", [0, 1, 3, 4, 5, 56, 68, 75]),
    ("FOREST", "wilds: trees, flat or raised", "GRASSLAND", [50, 54, 55, 69, 8, 9, 11, 57, 60, 73, 63, 61, 92]),
    ("SNOW", "wilds: snow", "RIVERS", [17, 71, 62, 67, 16, 19, 20, 84, 95]),
    ("DESERT", "wilds: sand", "PYRAMID", [65, 66, 59, 21, 22, 24, 78, 86, 25]),
    ("WASTELAND", "wilds: wasteland", "RUINS (WASTELAND)", [28, 64, 82, 33, 87, 91]),
    ("RIVERS", "wilds: by rivers and lakes", "GRASSLAND", [14, 15, 70, 72, 76, 77, 79, 18, 42, 89, 90, 93]),
    ("OCEAN", "sea: coast and open water", "RIVERS", [43, 88, 45, 46, 47, 94, 51, 96], OCEAN_TIERS),
    ("STONE CAVE", "cave: commonest, nearest", "GRASSLAND", [53, 66, 4, 60, 71, 61], CAVE_STONE),
    ("BRONZE CAVE", "cave", "STONE CAVE", [60, 71, 61, 81, 83, 39], CAVE_BRONZE),
    ("EMERALD CAVE", "cave: green", "BRONZE CAVE", [81, 39, 85, 83, 38], CAVE_EMERALD),
    ("VEYRITE CAVE", "cave: indigo", "EMERALD CAVE", [83, 85, 38, 40, 41, 48], CAVE_DEEP),
    ("DRAVIUM CAVE", "cave: dark red", "VEYRITE CAVE", [27, 35, 40, 7], CAVE_DEEP),
    ("KHARVITE CAVE", "cave: dark gold", "DRAVIUM CAVE", [27, 37, 35, 41], CAVE_DEEP),
    ("REALITY SHARD CAVE", "cave: black, rarest, hardest", "KHARVITE CAVE", [37, 38, 97, 7], HARDEST),
    ("OASIS", "dungeon: flooded, swimmers only", "RIVERS", [72, 77, 14, 15, 85, 46, 89, 91, 93]),
    ("LARGE TREE", "dungeon", "FOREST", [2, 55, 69, 58, 57, 74, 63, 80, 12, 13]),
    ("GRAVEYARD", "dungeon: small + large", "GRASSLAND / FOREST", [73, 11, 63, 86, 87, 29]),
    ("PYRAMID", "dungeon", "DESERT", [21, 24, 26, 27, 25]),
    ("RUINS (WASTELAND)", "dungeon: much harder", "WASTELAND", [33, 87, 91, 32, 31, 99], ["HARD", "SEVERE", "ELITE"]),
    ("RUINS (SNOW)", "dungeon: easier", "SNOW", [17, 62, 67, 79, 16, 19, 20, 84], ["MEDIUM", "UPPER", "HARD"]),
    ("STONEHENGE", "dungeon: British / Arthurian", "FOREST", [8, 9, 73, 76, 83, 36, 13]),
    ("CATACOMBS", "dungeon: hardest", "REALITY SHARD CAVE", [36, 92, 10, 29, 99], HARDEST),
]

TIERS = ["UNSET", "STARTER", "LOW", "MEDIUM", "UPPER", "HARD", "SEVERE", "ELITE", "BOSS1", "BOSS2", "BOSS3"]
ROWS = ["STARTER", "LOW", "MEDIUM", "UPPER", "HARD", "SEVERE", "ELITE"]


def read_tiers():
    src = (ROOT / "include" / "enemy.h").read_text(encoding="utf-8")
    body = src[src.index("ENEMY_TIERS[] = {"):]
    body = re.sub(r"//[^\n]*", "", body[:body.index("};")])
    return [TIERS.index(t) for t in re.findall(r"T_([A-Z0-9]+)", body)]


def read_ready():
    src = (ROOT / "include" / "ready.h").read_text(encoding="utf-8")
    body = src[src.index("READY_ENEMIES[] = {"):]
    return {int(n) for n in re.findall(r"\d+", body[body.index("{"):body.index("}")])}


def read_names():
    src = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
    body = src[src.index("ENEMY_NAMES[] = {"):]
    body = re.sub(r"//[^\n]*", "", body[:body.index("};")])
    return re.findall(r'"([^"]*)"', body)


SHEET_RE = re.compile(r'\{\s*(?:nullptr\s*\}|"(assets/enemies/[^"]+\.png)",\s*\{[^}]*\}(?:\s*,\s*(\d+))?(?:\s*,\s*(true|false))?)')


def read_sheets():
    """ENEMY_SHEETS in src/battle.cpp, in id order: (png, frames, rows)."""
    src = (ROOT / "src" / "battle.cpp").read_text(encoding="utf-8")
    body = src[src.index("ENEMY_SHEETS[] = {"):]
    body = re.sub(r"//[^\n]*", "", body[:body.index("\n};")])
    return [(m[1], int(m[2] or 3), m[3] == "true") for m in SHEET_RE.finditer(body)]


def frame0(sheet):
    """The front view's first frame, cut the way battle.cpp cuts it, trimmed."""
    path, frames, rows = sheet
    if path is None:   # { nullptr }: no sprite yet
        return None
    im = Image.open(ROOT / path).convert("RGBA")
    fw = im.width // frames if rows else im.width // (8 * frames)
    fh = im.height // 8 if rows else im.height
    im = im.crop((0, 0, fw, fh))
    box = im.getbbox()
    return im.crop(box) if box else None


CELL_W, CELL_H, SPR = 112, 118, 84
LABEL_W, HEAD_H, COLS = 74, 34, 8
K = 3   # drawn this many times over, so the board zooms sharp: text native, sprites whole pixels
BG, PANEL, INK, DIM = (24, 24, 30), (38, 38, 48), (232, 232, 236), (130, 130, 140)


def font(size, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size * K)
        except OSError:
            pass
    return ImageFont.load_default()


class Scaled:
    """ImageDraw in layout units: every coordinate times K."""
    def __init__(self, d):
        self.d = d
    def text(self, xy, *a, **k):
        self.d.text((xy[0] * K, xy[1] * K), *a, **k)
    def rectangle(self, box, **k):
        self.d.rectangle(tuple(v * K for v in box), **k)
    def line(self, box, **k):
        self.d.line(tuple(v * K for v in box), width=K, **k)


EMPTY_H = 30
PAGE_H = 1700   # layout units a column holds before the next starts


def row_height(ids):
    return CELL_H * -(-len(ids) // COLS) if ids else EMPTY_H


def rows_height(rows):
    return sum(row_height(r) for _, r in rows)


def main():
    tiers, ready, names, sheets = read_tiers(), read_ready(), read_names(), read_sheets()
    f_head, f_sub, f_lab, f_tag = font(17, True), font(12), font(11), font(10, True)
    by_name = {h[0]: h for h in HABITATS}
    sprites = {}

    def cell(d, img, x, y, eid):
        if eid not in sprites:
            sprites[eid] = frame0(sheets[eid]) if eid < len(sheets) else None
        spr, live = sprites[eid], eid in ready
        if spr is not None:
            s = min(SPR / spr.width, SPR / spr.height)
            s = int(s * K) if s >= 1 else s * K   # whole pixels where the sprite grows
            spr2 = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))),
                              Image.Resampling.NEAREST if s >= 1 else Image.Resampling.LANCZOS)
            if not live:   # unready: greyed and faded
                a = spr2.getchannel("A").point(lambda v: v * 35 // 100)
                spr2 = spr2.convert("LA").convert("RGBA")
                spr2.putalpha(a)
            img.alpha_composite(spr2, ((x * 2 + CELL_W) * K // 2 - spr2.width // 2,
                                       (y + 4) * K + (SPR * K - spr2.height) // 2))
        else:
            d.text((x + CELL_W // 2, y + SPR // 2), "no art", fill=DIM, font=f_lab, anchor="mm")
        name = names[eid] if eid < len(names) else "?"
        d.text((x + CELL_W // 2, y + SPR + 10), f"{eid} {name}"[:19], fill=INK if live else DIM, font=f_lab, anchor="mm")
        if not live:
            d.text((x + CELL_W // 2, y + SPR + 24), "UNREADY", fill=(200, 150, 60), font=f_tag, anchor="mm")

    def kin_has(kin, tier):
        return any(TIERS[tiers[e]] == tier and e in ready
                   for k in kin.split(" / ") if k in by_name for e in by_name[k][3])

    panels = []
    for name, where, kin, ids, *reach in HABITATS:
        dungeon = not where.startswith("wilds")
        shown = reach[0] if reach else [t for t in ROWS if dungeon or t != "ELITE"]
        rows = [(t, [e for e in ids if TIERS[tiers[e]] == t]) for t in ROWS if t in shown]
        stray = [e for e in ids if TIERS[tiers[e]] not in shown]
        assert not stray, f"{name}: {stray} sit in tiers it never reaches"
        rows = [(t, r) for t, r in rows if r or t != "STARTER"]
        panels.append((name, where, kin, rows, HEAD_H + rows_height(rows) + 8))

    placed = {e for h in HABITATS for e in h[3]}
    common = lambda e: tiers[e] < TIERS.index("BOSS1")
    orphans_ready = [e for e in sorted(ready) if e not in placed and common(e)]
    orphans_unready = [e for e in range(len(tiers)) if e not in ready and e not in placed and common(e)]
    orph = [("READY", orphans_ready), ("UNREADY", orphans_unready)]
    panels.append(("NEVER SPAWNS", "in no habitat (bosses left out)", "-", orph, HEAD_H + rows_height(orph) + 8))

    pw = LABEL_W + COLS * CELL_W + 8
    # Pages a common image viewer will open: panels in list order, two columns
    # a page, a column closed once it passes PAGE_H.
    pages, page, col, y_col = [], [[], []], 0, 0
    for p in panels:
        if y_col and y_col + p[4] > PAGE_H:
            col, y_col = col + 1, 0
            if col == 2:
                pages.append(page)
                page, col = [[], []], 0
        page[col].append((y_col, p))
        y_col += p[4] + 12
    pages.append(page)

    for old in OUT.parent.glob(OUT.stem + "*.png"):   # last run's pages, and the one-sheet board
        old.unlink()
    for n, cols in enumerate(pages, 1):
        W = 2 * pw + 36
        H = max(y + p[4] for c in cols for y, p in c) + 64
        img = Image.new("RGBA", (W * K, H * K), BG + (255,))
        d = Scaled(ImageDraw.Draw(img))
        d.text((12, 12), f"ENEMY HABITATS - review board  {n}/{len(pages)}", fill=INK, font=font(22, True))
        d.text((W - 12, 18), "dim = unready    amber EMPTY = falls back to kin    red EMPTY = kin empty too",
               fill=DIM, font=f_sub, anchor="ra")
        for c, col in enumerate(cols):
            x0 = 12 + c * (pw + 12)
            for y_off, (name, where, kin, rows, h) in col:
                y = 52 + y_off
                d.rectangle((x0, y, x0 + pw, y + h), fill=PANEL)
                d.text((x0 + 10, y + 8), name, fill=INK, font=f_head)
                d.text((x0 + pw - 10, y + 11), f"{where}    kin: {kin}", fill=DIM, font=f_sub, anchor="ra")
                y += HEAD_H
                for t, ids in rows:
                    d.line((x0 + 6, y, x0 + pw - 6, y), fill=(60, 60, 74))
                    d.text((x0 + 10, y + 10), t, fill=INK, font=f_tag)
                    if name != "NEVER SPAWNS" and not any(e in ready for e in ids):
                        ok = kin_has(kin, t)
                        d.text((x0 + 10, y + 24) if ids else (x0 + LABEL_W + 8, y + 10), f"EMPTY -> {kin}" if ok else "EMPTY, kin too",
                               fill=(215, 160, 60) if ok else (220, 70, 70), font=f_tag)
                    for i, e in enumerate(ids):
                        cell(d, img, x0 + LABEL_W + (i % COLS) * CELL_W, y + 4 + (i // COLS) * CELL_H, e)
                    y += row_height(ids)
        out = OUT.with_name(f"{OUT.stem}_{n}.png")
        img.convert("RGB").save(out)
        print(f"wrote {out.relative_to(ROOT)}  {img.width}x{img.height}")
    print("ready but placed nowhere:", orphans_ready or "none")
    print("unready, placed nowhere:", orphans_unready or "none")


if __name__ == "__main__":
    sys.exit(main())
