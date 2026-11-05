#include "chase_path.h"
#include <math.h>

static const int CHASE_STEP = 16;    // the lattice the way is searched on
static const int HALF       = CHASE_STEP / 2;   // where a step is asked: midway
static const float LINE_ASK = 6.0f;  // a straight walk asked this often; the feet are 12 across

bool chase_straight(float sx, float sy, float px, float py, const std::function<bool(float, float)>& fits) {
    float dx = px - sx, dy = py - sy, d = sqrtf(dx * dx + dy * dy);
    int n = (int)ceilf(d / LINE_ASK);
    for (int i = 1; i <= n; i++)
        if (!fits(sx + dx * i / n, sy + dy * i / n)) return false;
    return true;
}

// The ground at a point of the half-step lattice (x, y in multiples of HALF),
// asked once and kept. *budget: asks left; at none, nothing new is asked and
// the point reads as shut (the search is UNSURE then, and says so).
static bool lattice_fits(ChaseCache* c, int hx, int hy, const std::function<bool(float, float)>& fits, int* budget) {
    uint64_t key = (uint64_t)(uint32_t)hx << 32 | (uint32_t)hy;
    auto it = c->fit.find(key);
    if (it != c->fit.end()) return it->second;
    if (*budget <= 0) return false;
    --*budget;
    bool f = fits((float)(hx * HALF), (float)(hy * HALF));
    if (c->fit.size() > 400000) c->fit.clear();   // a long walk across the world: start the notes again
    c->fit[key] = f;
    return f;
}

ChaseWay chase_route(ChaseCache* cache, float sx, float sy, float px, float py, float half_w, float half_h,
                     const std::function<bool(float, float)>& fits, std::vector<ResidentPoint>& route, int budget) {
    route.clear();
    if (fabsf(sx - px) > half_w || fabsf(sy - py) > half_h) return CHASE_NONE;   // out of range already

    // The box's nodes: lattice points (gx * STEP + HALF, ...), node (i, j) of
    // the box at gx = gx0 + i.
    int gx0 = (int)floorf((px - half_w - HALF) / CHASE_STEP), gx1 = (int)floorf((px + half_w - HALF) / CHASE_STEP);
    int gy0 = (int)floorf((py - half_h - HALF) / CHASE_STEP), gy1 = (int)floorf((py + half_h - HALF) / CHASE_STEP);
    int w = gx1 - gx0 + 1, h = gy1 - gy0 + 1;
    auto wx = [&](int i) { return (float)((gx0 + i) * CHASE_STEP + HALF); };
    auto wy = [&](int j) { return (float)((gy0 + j) * CHASE_STEP + HALF); };
    // On the half lattice a node is (2g + 1), a midpoint between two the even one.
    auto node_ok = [&](int i, int j) { return lattice_fits(cache, 2 * (gx0 + i) + 1, 2 * (gy0 + j) + 1, fits, &budget); };
    auto mid_ok  = [&](int i, int j, int di, int dj) {   // the step from (i, j) to (i + di, j + dj), one of them 0
        return lattice_fits(cache, 2 * (gx0 + i) + 1 + di, 2 * (gy0 + j) + 1 + dj, fits, &budget);
    };

    // 0 none, 1 reached from the chaser's side, 2 from the player's.
    std::vector<uint8_t> side(w * h, 0);
    std::vector<int> parent(w * h, -1);
    std::vector<int> fa, fb;   // the two frontiers
    // A side's way on: the nodes round its end that its end walks straight to.
    auto seed = [&](float x, float y, uint8_t s, std::vector<int>& front) {
        int ci = (int)floorf((x - HALF) / CHASE_STEP) - gx0, cj = (int)floorf((y - HALF) / CHASE_STEP) - gy0;
        for (int j = cj - 1; j <= cj + 2; j++)
            for (int i = ci - 1; i <= ci + 2; i++) {
                if (i < 0 || j < 0 || i >= w || j >= h || side[j * w + i]) continue;
                if (!node_ok(i, j) || !chase_straight(x, y, wx(i), wy(j), fits)) continue;
                side[j * w + i] = s;
                front.push_back(j * w + i);
            }
    };
    seed(sx, sy, 1, fa);
    seed(px, py, 2, fb);
    if (fa.empty() || fb.empty()) return budget > 0 ? CHASE_NONE : CHASE_UNSURE;

    static const int DI[8] = { 1, -1, 0, 0, 1, 1, -1, -1 }, DJ[8] = { 0, 0, 1, -1, 1, -1, 1, -1 };
    int meet_a = -1, meet_b = -1;
    // Did a node seed on both sides at once? Then they meet where they stand.
    for (int u : fa) for (int v : fb) if (u == v && meet_a < 0) { meet_a = meet_b = u; }
    // One layer of the smaller frontier at a time: where one side is shut in
    // (a plateau's top, an island), the search ends as soon as it has filled it.
    while (meet_a < 0 && !fa.empty() && !fb.empty()) {
        bool from_a = fa.size() <= fb.size();
        std::vector<int>& front = from_a ? fa : fb;
        uint8_t me = from_a ? 1 : 2;
        std::vector<int> next;
        for (size_t k = 0; k < front.size() && meet_a < 0; k++) {
            int u = front[k], ui = u % w, uj = u / w;
            for (int d = 0; d < 8 && meet_a < 0; d++) {
                int vi = ui + DI[d], vj = uj + DJ[d];
                if (vi < 0 || vj < 0 || vi >= w || vj >= h) continue;
                int v = vj * w + vi;
                if (side[v] == me) continue;
                if (!node_ok(vi, vj)) continue;
                bool ok;
                if (d < 4) ok = mid_ok(ui, uj, DI[d], DJ[d]);
                else       // a diagonal: both ways round its corner walk, so no corner is cut
                    ok = node_ok(vi, uj) && node_ok(ui, vj)
                      && mid_ok(ui, uj, DI[d], 0) && mid_ok(vi, uj, 0, DJ[d])
                      && mid_ok(ui, uj, 0, DJ[d]) && mid_ok(ui, vj, DI[d], 0);
                if (!ok) continue;
                if (side[v]) {   // the other side's: they meet
                    meet_a = from_a ? u : v;
                    meet_b = from_a ? v : u;
                    break;
                }
                side[v] = me;
                parent[v] = u;
                next.push_back(v);
            }
        }
        front.swap(next);
    }
    if (meet_a < 0) return budget > 0 ? CHASE_NONE : CHASE_UNSURE;   // shut in, or out of asks before it knew

    // The chain: the chaser's side back from its meeting node, then the
    // player's side on from its own.
    std::vector<int> chain;
    for (int n = meet_a; n >= 0; n = parent[n]) chain.push_back(n);
    std::vector<int> rev(chain.rbegin(), chain.rend());
    if (meet_b != meet_a) for (int n = meet_b; n >= 0; n = parent[n]) rev.push_back(n);
    std::vector<ResidentPoint> pts;
    for (int n : rev) pts.push_back({ wx(n % w), wy(n / w) });
    pts.push_back({ px, py });

    // Straight runs: from each corner, the farthest of the next few points it
    // walks straight to.
    ResidentPoint at = { sx, sy };
    size_t i = 0;
    while (i < pts.size()) {
        size_t far = i;
        for (size_t j = pts.size() - 1 < i + 8 ? pts.size() - 1 : i + 8; j > i; j--)
            if (chase_straight(at.x, at.y, pts[j].x, pts[j].y, fits)) { far = j; break; }
        route.push_back(pts[far]);
        at = pts[far];
        i = far + 1;
    }
    return CHASE_WAY;
}
