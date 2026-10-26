#include "playtest.h"
#include "ready.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#ifdef _WIN32
#include <direct.h>
#define make_dir(p) _mkdir(p)
#else
#define make_dir(p) mkdir(p, 0755)
#endif

static const char* const ORDER_PATH  = "playtest/order.txt";
static const char* const TRIALS_PATH = "playtest/trials.csv";
static const char* const TRIALS_OLD  = "playtest/trials_v1.csv";   // rows from before the knife (timed, shots did nothing)
static const char* const TRIALS_HEAD =
    "date,run,order_index,id,name,tier,secs,hits,bars,hits_p1,hits_p2,p2_at,"
    "hits_per_min,hpm_p1,hpm_p2,first_hit_t,grazes,shot,laser,part,body,rating,"
    "ore,oil,level,shots,shots_hit,accuracy\n";

// The knife by tier: what a player has in hand by the time they meet one.
// Climbs in difficulty order (the user): ... SEVERE, then the tier-1 bosses,
// then ELITE, and the tier-2 bosses hardest of all.
static const TrialGear TRIAL_GEAR[] = {
    { MAT_STONE,    0,  1 },   // T_UNSET (none now)
    { MAT_STONE,    0,  1 },   // T_STARTER
    { MAT_STONE,    1,  2 },   // T_LOW
    { MAT_BRONZE,   2,  4 },   // T_MEDIUM
    { MAT_EMERALD,  3,  6 },   // T_UPPER
    { MAT_VEYRITE,  4,  8 },   // T_HARD
    { MAT_VEYRITE,  5,  9 },   // T_SEVERE
    { MAT_DRAVIUM,  6, 11 },   // T_ELITE
    { MAT_DRAVIUM,  5, 10 },   // T_BOSS1: between SEVERE and ELITE
    { MAT_KHARVITE, 8, 14 },   // T_BOSS2: the hardest
    { MAT_KHARVITE, 8, 14 },   // T_BOSS3
};
static_assert(sizeof(TRIAL_GEAR) / sizeof(TRIAL_GEAR[0]) == T_BOSS3 + 1, "a gear row per EnemyTier");

TrialGear playtest_gear(int id) { return TRIAL_GEAR[enemy_tier(id)]; }

int playtest_order(int* ids, int max) {
    int n = 0;
    // One enemy a line, its id first; # starts a comment.
    if (FILE* f = fopen(ORDER_PATH, "r")) {
        char ln[160];
        while (n < max && fgets(ln, sizeof(ln), f)) {
            int id;
            if (ln[0] != '#' && sscanf(ln, "%d", &id) == 1 && id >= 0 && id < ENEMY_COUNT) ids[n++] = id;
        }
        fclose(f);
        if (n > 0) return n;
    }
    for (int t = T_UNSET; t <= T_BOSS3; t++)
        for (int e = 0; e < ENEMY_COUNT && n < max; e++)
            if (enemy_tier(e) == t && enemy_ready(e)) ids[n++] = e;
    return n;
}

void playtest_run_label(char* out, size_t n, bool reverse) {
    time_t now = time(nullptr);
    struct tm* lt = localtime(&now);
    snprintf(out, n, "%04d-%02d-%02d-%s", lt->tm_year + 1900, lt->tm_mon + 1, lt->tm_mday, reverse ? "rev" : "fwd");
}

bool playtest_logged(const char* run, int id) {
    FILE* f = fopen(TRIALS_PATH, "r");
    if (!f) return false;
    char ln[512], r[64];
    int order, eid;
    bool found = false;
    // date,run,order_index,id,...
    while (!found && fgets(ln, sizeof(ln), f))
        if (sscanf(ln, "%*[^,],%63[^,],%d,%d", r, &order, &eid) == 3)
            found = order >= 0 && eid == id && strcmp(r, run) == 0;
    fclose(f);
    return found;
}

void playtest_log(const char* run, int order_index, int id, const char* name,
                  const TrialStats& s) {
    make_dir("playtest");
    make_dir("playtest/hits");
    // A log with another header is from before this one: moved aside, so the
    // old rows never mix with these.
    if (FILE* old = fopen(TRIALS_PATH, "r")) {
        char head[512] = "";
        if (!fgets(head, sizeof(head), old)) head[0] = 0;
        fclose(old);
        if (head[0] && strcmp(head, TRIALS_HEAD) != 0) { remove(TRIALS_OLD); rename(TRIALS_PATH, TRIALS_OLD); }
    }
    struct stat st;
    bool fresh = stat(TRIALS_PATH, &st) != 0 || st.st_size == 0;
    FILE* f = fopen(TRIALS_PATH, "a");
    if (!f) return;
    if (fresh) fputs(TRIALS_HEAD, f);
    time_t now = time(nullptr);
    char date[32];
    strftime(date, sizeof(date), "%Y-%m-%d %H:%M", localtime(&now));
    // Hits a minute, overall and either side of the phase line.
    float secs = s.secs > 0.0f ? s.secs : 1.0f;
    float p1 = s.p2_at >= 0.0f ? s.p2_at : secs, p2 = secs - p1;
    fprintf(f, "%s,%s,%d,%d,\"%s\",%d,%.1f,%d,%d,%d,%d,%.1f,%.2f,%.2f,%.2f,%.1f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.1f\n",
            date, run, order_index, id, name, (int)enemy_tier(id), s.secs, s.hits, s.bars, s.hits_p1, s.hits_p2, s.p2_at,
            s.hits * 60.0f / secs, p1 > 0.5f ? s.hits_p1 * 60.0f / p1 : 0.0f, p2 > 0.5f ? s.hits_p2 * 60.0f / p2 : 0.0f,
            s.n_log ? s.log[0].t : -1.0f, s.grazes, s.by_src[0], s.by_src[1], s.by_src[2], s.by_src[3], s.rating,
            (int)s.gear.ore, s.gear.oil, s.gear.level, s.shots, s.shots_hit, s.shots ? s.shots_hit * 100.0f / s.shots : 0.0f);
    fclose(f);

    char path[160];
    snprintf(path, sizeof(path), "playtest/hits/%s_%02d%s.csv", run, id, order_index < 0 ? "_warmup" : "");
    if (FILE* h = fopen(path, "w")) {
        fprintf(h, "t,x,y,src,enraged\n");
        for (int i = 0; i < s.n_log; i++)
            fprintf(h, "%.2f,%.0f,%.0f,%c,%d\n", s.log[i].t, s.log[i].x, s.log[i].y, s.log[i].src, (int)s.log[i].enraged);
        fclose(h);
    }
}
