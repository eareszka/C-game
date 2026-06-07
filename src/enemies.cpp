#include "enemy.h"
#include <math.h>

static const float PI  = 3.14159265f;
static const float TAU = 6.28318530f;

// ── RNG ───────────────────────────────────────────────────────────────────────

static unsigned int s_erng = 0xDEADBEEFu;

void seed_enemy_rng(unsigned int seed) { s_erng ^= seed; }

static float ernd() {
    s_erng = s_erng * 1664525u + 1013904223u;
    return (float)(s_erng >> 16) / 65536.0f;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

static BulletSpawn mk(float angle, float speed, float radius, float damage) {
    return { cosf(angle)*speed, sinf(angle)*speed, radius, damage, false };
}

// Bouncing bullet — blue, reflects off walls, deleted after 3rd bounce.
static BulletSpawn mkb(float angle, float speed, float radius, float damage) {
    return { cosf(angle)*speed, sinf(angle)*speed, radius, damage, true };
}

// Spawner orb — large bright-orange, slow, emits 8-way ring every spawn_interval seconds.
static BulletSpawn mksp(float angle, float speed, float spawn_interval) {
    return { cosf(angle)*speed, sinf(angle)*speed, 9.0f, 2.0f, false, true, spawn_interval };
}

static float aim_at(float ox, float oy, float tx, float ty) {
    return atan2f(ty - oy, tx - ox);
}

// Returns true when the enemy is in its enraged (low-HP) phase.
#define ENRAGED (hp < max_hp * 0.5f)

// ── Grassland enemies (IDs 0–6) ───────────────────────────────────────────────

class Skvader : public Enemy {
public:
    Skvader() : Enemy(320, 160, 10, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "SKVADER"; }
    float       fire_interval() const override { return ENRAGED ? 0.1f : 0.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 3; i++)
                out[i] = mk(a + (i-1)*0.2f, 240.0f, 2.5f, 0.5f);
            return 3;
        }
        out[0] = mk(a, 200.0f, 2.5f, 0.4f);
        return 1;
    }
};

class Wolpertinger : public Enemy {
public:
    Wolpertinger() : Enemy(320, 160, 14, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "WOLPERTINGER"; }
    float       fire_interval() const override { return ENRAGED ? 0.2f : 0.3f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.25f, 230.0f, 2.5f, 0.5f);
            out[1] = mk(a,         230.0f, 2.5f, 0.5f);
            out[2] = mk(a + 0.25f, 230.0f, 2.5f, 0.5f);
            out[3] = mk(a + PI,    180.0f, 2.5f, 0.4f);
            return 4;
        }
        out[0] = mk(a - 0.15f, 210.0f, 2.5f, 0.4f);
        out[1] = mk(a + 0.15f, 210.0f, 2.5f, 0.4f);
        return 2;
    }
};

class Treesqueak : public Enemy {
public:
    Treesqueak() : Enemy(320, 160, 18, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "TREESQUEAK"; }
    float       fire_interval() const override { return ENRAGED ? 0.25f : 0.4f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            float a = aim_at(x,y,px,py);
            out[0] = mk(a, 220.0f, 2.5f, 0.5f);
            for (int i = 1; i < 5; i++)
                out[i] = mk(ernd() * TAU, 200.0f, 2.5f, 0.4f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(ernd() * TAU, 180.0f, 2.5f, 0.4f);
        return 3;
    }
};

class Qique : public Enemy {
public:
    Qique() : Enemy(320, 160, 24, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QIQUE"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.28f, 190.0f, 3.5f, 0.9f);
            out[1] = mk(a,         190.0f, 3.5f, 1.0f);
            out[2] = mk(a + 0.28f, 190.0f, 3.5f, 0.9f);
            return 3;
        }
        out[0] = mk(a, 160.0f, 3.5f, 0.8f);
        return 1;
    }
};

class Lili : public Enemy {
public:
    Lili() : Enemy(320, 160, 30, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "LILI"; }
    float       fire_interval() const override { return ENRAGED ? 0.6f : 0.9f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.25f, 175.0f, 3.5f, 0.8f);
            out[1] = mk(a + 0.25f, 175.0f, 3.5f, 0.8f);
            out[2] = mk(a + PI/2.0f, 130.0f, 3.0f, 0.6f);
            out[3] = mk(a - PI/2.0f, 130.0f, 3.0f, 0.6f);
            return 4;
        }
        out[0] = mk(a - 0.2f, 155.0f, 3.5f, 0.7f);
        out[1] = mk(a + 0.2f, 155.0f, 3.5f, 0.7f);
        return 2;
    }
};

class CrowingCrestedCobra : public Enemy {
public:
    CrowingCrestedCobra() : Enemy(320, 160, 38, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "CROWING CRESTED COBRA"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.32f, 185.0f, 3.5f, 1.0f);
            return 5;
        }
        out[0] = mk(a,         160.0f, 3.5f, 0.9f);
        out[1] = mk(a - 0.35f, 140.0f, 3.5f, 0.8f);
        out[2] = mk(a + 0.35f, 140.0f, 3.5f, 0.8f);
        return 3;
    }
};

class WakmangganchiAragondi : public Enemy {
public:
    WakmangganchiAragondi() : Enemy(320, 160, 45, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "WAKMANGGANCHI ARAGONDI"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.25f, 190.0f, 4.0f, 1.1f);
            out[5] = mk(a + PI/2.0f, 150.0f, 3.5f, 0.9f);
            out[6] = mk(a - PI/2.0f, 150.0f, 3.5f, 0.9f);
            return 7;
        }
        out[0] = mk(a,        170.0f, 4.0f, 1.0f);
        out[1] = mk(a - 0.22f,150.0f, 3.5f, 0.9f);
        out[2] = mk(a + 0.22f,150.0f, 3.5f, 0.9f);
        return 3;
    }
};

// ── Forest enemies (IDs 7–13) ─────────────────────────────────────────────────

class Alber : public Enemy {
public:
    Alber() : Enemy(320, 160, 50, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "ALBER"; }
    float       fire_interval() const override { return ENRAGED ? 0.5f : 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.2f, 195.0f, 4.0f, 1.1f);
            out[1] = mk(a,        195.0f, 4.0f, 1.2f);
            out[2] = mk(a + 0.2f, 195.0f, 4.0f, 1.1f);
            return 3;
        }
        out[0] = mk(a, 170.0f, 4.0f, 1.0f);
        return 1;
    }
};

class Snawfus : public Enemy {
public:
    Snawfus() : Enemy(320, 160, 58, {1.0f,1.0f,1.0f,1.25f,1.25f,1.25f,1.25f}) {}
    const char* name()          const override { return "SNAWFUS"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.3f, 200.0f, 3.5f, 1.1f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.3f, 175.0f, 3.5f, 1.0f);
        return 3;
    }
};

class QuestingBeast : public Enemy {
public:
    QuestingBeast() : Enemy(320, 160, 68, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QUESTING BEAST"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.28f, 195.0f, 3.5f, 1.1f);
            out[5] = mk(a, 250.0f, 3.0f, 1.3f);
            return 6;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.28f, 165.0f, 3.5f, 0.9f);
        return 5;
    }
};

class GrandGoule : public Enemy {
public:
    GrandGoule() : Enemy(320, 160, 75, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "GRAND'GOULE"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.3f, 190.0f, 4.0f, 1.3f);
            out[5] = mk(a + PI/2.0f, 150.0f, 3.5f, 0.9f);
            out[6] = mk(a - PI/2.0f, 150.0f, 3.5f, 0.9f);
            return 7;
        }
        out[0] = mk(a,           175.0f, 4.0f, 1.2f);
        out[1] = mk(a + PI/2.0f, 130.0f, 3.5f, 0.8f);
        out[2] = mk(a - PI/2.0f, 130.0f, 3.5f, 0.8f);
        return 3;
    }
};

class Paoxiao : public Enemy {
public:
    Paoxiao() : Enemy(320, 160, 82, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "PAOXIAO"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.28f, 180.0f, 4.0f, 1.1f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.32f, 160.0f, 4.0f, 1.0f);
        return 5;
    }
};

class Ebigane : public Enemy {
public:
    Ebigane() : Enemy(320, 160, 90, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "EBIGANE"; }
    float       fire_interval() const override { return ENRAGED ? 1.8f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 4; i++)
                out[i] = mk(i * PI/2.0f, 90.0f, 7.0f, 2.2f);
            out[4] = mk(a,         140.0f, 5.5f, 2.8f);
            out[5] = mk(a + 0.4f,  110.0f, 4.5f, 2.0f);
            out[6] = mk(a - 0.4f,  110.0f, 4.5f, 2.0f);
            return 7;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(i * PI/2.0f, 80.0f, 7.0f, 2.0f);
        out[4] = mk(a, 120.0f, 5.0f, 2.5f);
        return 5;
    }
};

class BeastOfTheCharredForests : public Enemy {
public:
    BeastOfTheCharredForests() : Enemy(320, 160, 100, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "BEAST OF THE CHARRED FORESTS"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         145.0f, 6.5f, 3.2f);
            out[1] = mk(a + 0.45f, 120.0f, 5.5f, 2.3f);
            out[2] = mk(a - 0.45f, 120.0f, 5.5f, 2.3f);
            for (int i = 0; i < 6; i++)
                out[i+3] = mk(i * TAU/6.0f, 70.0f, 4.5f, 1.4f);
            return 9;
        }
        out[0] = mk(a,         130.0f, 6.0f, 2.8f);
        out[1] = mk(a + 0.45f, 110.0f, 5.0f, 2.0f);
        out[2] = mk(a - 0.45f, 110.0f, 5.0f, 2.0f);
        return 3;
    }
};

// ── Snow enemies (IDs 14–20) ──────────────────────────────────────────────────

class Lodsilungur : public Enemy {
public:
    Lodsilungur() : Enemy(320, 160, 80, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "LODSILUNGUR"; }
    float       fire_interval() const override { return ENRAGED ? 0.15f : 0.3f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.22f, 250.0f, 3.0f, 0.7f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.25f, 220.0f, 3.0f, 0.6f);
        return 3;
    }
};

class Ofuguggi : public Enemy {
public:
    Ofuguggi() : Enemy(320, 160, 90, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "OFUGUGGI"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,           190.0f, 4.0f, 1.3f);
            out[1] = mk(a + PI,      150.0f, 4.0f, 1.0f);
            out[2] = mk(a + PI/2.0f, 130.0f, 3.5f, 0.9f);
            out[3] = mk(a - PI/2.0f, 130.0f, 3.5f, 0.9f);
            return 4;
        }
        out[0] = mk(a,      170.0f, 4.0f, 1.1f);
        out[1] = mk(a + PI, 130.0f, 4.0f, 0.9f);
        return 2;
    }
};

class Kamaitachi : public Enemy {
    float sweep = 0.0f;
public:
    Kamaitachi() : Enemy(320, 160, 98, {1.25f,0.75f,1.25f,0.75f,1.0f,1.5f,1.5f}) {}
    const char* name()          const override { return "KAMAITACHI"; }
    float       fire_interval() const override { return ENRAGED ? 0.1f : 0.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            out[0] = mk(sweep,        300.0f, 2.5f, 0.6f);
            out[1] = mk(sweep + PI,   220.0f, 2.5f, 0.5f);
            sweep += PI / 4.0f;
            return 2;
        }
        out[0] = mk(sweep, 280.0f, 2.5f, 0.5f);
        sweep += PI / 5.0f;
        return 1;
    }
};

class Qiqirn : public Enemy {
public:
    Qiqirn() : Enemy(320, 160, 115, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QIQIRN"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.28f, 205.0f, 4.0f, 1.3f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.28f, 180.0f, 4.0f, 1.1f);
        return 3;
    }
};

class Vatnaormur : public Enemy {
public:
    Vatnaormur() : Enemy(320, 160, 128, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "VATNAORMUR"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.32f, 185.0f, 3.5f, 1.3f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.35f, 160.0f, 3.5f, 1.1f);
        return 5;
    }
};

class Skeljaskrimsli : public Enemy {
    int phase = 0;
public:
    Skeljaskrimsli() : Enemy(320, 160, 140, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "SKELJASKRIMSLI"; }
    float       fire_interval() const override { return ENRAGED ? 1.2f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            // shell burst + bouncing shards simultaneously
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 100.0f, 5.0f, 1.3f);
            for (int i = 0; i < 3; i++)
                out[i+8] = mkb(a + (i-1)*0.4f, 160.0f, 4.0f, 1.2f);
            return 11;
        }
        if (phase % 2 == 0) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 90.0f, 5.0f, 1.2f);
            phase++; return 8;
        } else {
            // bouncing shards
            for (int i = 0; i < 3; i++)
                out[i] = mkb(a + (i-1)*0.45f, 150.0f, 4.0f, 1.1f);
            phase++; return 3;
        }
    }
};

class Sermilik : public Enemy {
public:
    Sermilik() : Enemy(320, 160, 155, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SERMILIK"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 80.0f, 6.5f, 1.9f);
            out[8]  = mk(a,         145.0f, 6.0f, 2.8f);
            out[9]  = mk(a + 0.3f,  120.0f, 5.0f, 2.2f);
            out[10] = mk(a - 0.3f,  120.0f, 5.0f, 2.2f);
            out[11] = mksp(a, 55.0f, 0.45f);
            return 12;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(i * PI/2.0f, 75.0f, 7.0f, 2.0f);
        out[4] = mk(a, 130.0f, 5.5f, 2.5f);
        out[5] = mksp(a, 50.0f, 0.5f);
        return 6;
    }
};

// ── Desert enemies (IDs 21–27) ────────────────────────────────────────────────

class Asp : public Enemy {
public:
    Asp() : Enemy(320, 160, 145, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ASP"; }
    float       fire_interval() const override { return ENRAGED ? 0.5f : 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.18f, 265.0f, 3.5f, 1.4f);
            out[1] = mk(a,         265.0f, 3.5f, 1.5f);
            out[2] = mk(a + 0.18f, 265.0f, 3.5f, 1.4f);
            return 3;
        }
        out[0] = mk(a - 0.12f, 240.0f, 3.5f, 1.2f);
        out[1] = mk(a + 0.12f, 240.0f, 3.5f, 1.2f);
        return 2;
    }
};

class CactusCat : public Enemy {
public:
    CactusCat() : Enemy(320, 160, 155, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "CACTUS CAT"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a, 200.0f, 4.5f, 1.5f);
            for (int i = 0; i < 8; i++)
                out[i+1] = mk(i * TAU/8.0f, 120.0f, 3.0f, 0.9f);
            return 9;
        }
        out[0] = mk(a, 180.0f, 4.0f, 1.3f);
        for (int i = 0; i < 4; i++)
            out[i+1] = mk(a + (i+1) * PI/2.0f, 110.0f, 3.0f, 0.8f);
        return 5;
    }
};

class OlgoiKhorkhoi : public Enemy {
public:
    OlgoiKhorkhoi() : Enemy(320, 160, 165, {0.4f,1.0f,0.4f,0.75f,1.0f,1.0f,1.5f}) {}
    const char* name()          const override { return "OLGOI-KHORKHOI"; }
    float       fire_interval() const override { return ENRAGED ? 1.4f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            float off = ernd() * TAU;
            for (int i = 0; i < 16; i++)
                out[i] = mk(off + i * TAU/16.0f, 115.0f, 4.5f, 1.4f);
            return 16;
        }
        float off = ernd() * TAU;
        for (int i = 0; i < 10; i++)
            out[i] = mk(off + i * TAU/10.0f, 95.0f, 4.5f, 1.2f);
        return 10;
    }
};

class Zoureg : public Enemy {
public:
    Zoureg() : Enemy(320, 160, 175, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ZOUREG"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.35f, 195.0f, 3.5f, 1.3f);
            out[7] = mk(a, 280.0f, 3.5f, 1.6f);
            return 8;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.38f, 170.0f, 3.5f, 1.1f);
        return 5;
    }
};

class Myrmecoleon : public Enemy {
    float ring_rot = 0.0f;
public:
    Myrmecoleon() : Enemy(320, 160, 190, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "MYRMECOLEON"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         220.0f, 4.5f, 1.7f);
            out[1] = mk(a - 0.2f,  200.0f, 4.0f, 1.4f);
            out[2] = mk(a + 0.2f,  200.0f, 4.0f, 1.4f);
            for (int i = 0; i < 8; i++)
                out[i+3] = mk(ring_rot + i * TAU/8.0f, 100.0f, 3.5f, 1.0f);
            ring_rot += PI / 8.0f;
            return 11;
        }
        out[0] = mk(a, 200.0f, 4.0f, 1.4f);
        for (int i = 0; i < 6; i++)
            out[i+1] = mk(ring_rot + i * TAU/6.0f, 85.0f, 3.5f, 0.9f);
        ring_rot += PI / 6.0f;
        return 7;
    }
};

class Akhekh : public Enemy {
public:
    Akhekh() : Enemy(320, 160, 205, {0.5f,0.5f,0.75f,0.5f,1.5f,1.0f,1.5f}) {}
    const char* name()          const override { return "AKHEKH"; }
    float       fire_interval() const override { return ENRAGED ? 0.45f : 0.7f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,           275.0f, 3.5f, 1.5f);
            out[1] = mk(a - 0.3f,    250.0f, 3.0f, 1.2f);
            out[2] = mk(a + 0.3f,    250.0f, 3.0f, 1.2f);
            out[3] = mk(a + PI/2.0f, 200.0f, 3.0f, 1.0f);
            out[4] = mk(a - PI/2.0f, 200.0f, 3.0f, 1.0f);
            return 5;
        }
        out[0] = mk(a,         250.0f, 3.5f, 1.3f);
        out[1] = mk(a - 0.3f, 230.0f, 3.0f, 1.1f);
        out[2] = mk(a + 0.3f, 230.0f, 3.0f, 1.1f);
        return 3;
    }
};

class Grootslang : public Enemy {
public:
    Grootslang() : Enemy(320, 160, 220, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "GROOTSLANG"; }
    float       fire_interval() const override { return ENRAGED ? 1.6f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         125.0f, 8.5f, 4.0f);
            out[1] = mk(a + 0.5f,  100.0f, 6.5f, 2.8f);
            out[2] = mk(a - 0.5f,  100.0f, 6.5f, 2.8f);
            for (int i = 0; i < 4; i++)
                out[i+3] = mk(i * PI/2.0f, 75.0f, 5.5f, 1.8f);
            return 7;
        }
        out[0] = mk(a,         110.0f, 8.0f, 3.5f);
        out[1] = mk(a + 0.5f,  90.0f, 6.0f, 2.5f);
        out[2] = mk(a - 0.5f,  90.0f, 6.0f, 2.5f);
        return 3;
    }
};

// ── Wasteland enemies (IDs 28–34) ─────────────────────────────────────────────

class Opimachus : public Enemy {
public:
    Opimachus() : Enemy(320, 160, 210, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "OPIMACHUS"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.3f, 200.0f, 4.0f, 1.5f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.32f, 175.0f, 4.0f, 1.3f);
        return 5;
    }
};

class Karnabo : public Enemy {
    int phase = 0;
public:
    Karnabo() : Enemy(320, 160, 225, {1.25f,1.5f,2.0f,0.75f,0.75f,1.5f,1.0f}) {}
    const char* name()          const override { return "KARNABO"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            // curse ring + bouncing aimed bolts simultaneously
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 110.0f, 3.5f, 1.0f);
            for (int i = 0; i < 3; i++)
                out[i+12] = mkb(a + (i-1)*0.25f, 200.0f, 3.5f, 1.5f);
            return 15;
        }
        if (phase % 2 == 0) {
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 100.0f, 3.5f, 0.9f);
            phase++; return 12;
        } else {
            // bouncing curse bolts
            for (int i = 0; i < 3; i++)
                out[i] = mkb(a + (i-1)*0.25f, 190.0f, 3.5f, 1.3f);
            phase++; return 3;
        }
    }
};

class Dajna : public Enemy {
    float rot = 0.0f;
public:
    Dajna() : Enemy(320, 160, 238, {1.25f,1.5f,2.0f,0.75f,0.75f,1.5f,1.0f}) {}
    const char* name()          const override { return "DAJNA"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i]   = mk(rot       + i * TAU/8.0f, 105.0f, 3.5f, 1.0f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mk(rot + PI/8.0f + i * TAU/8.0f, 80.0f, 3.0f, 0.8f);
            out[16] = mk(a,         230.0f, 4.5f, 1.8f);
            out[17] = mk(a + 0.2f,  200.0f, 4.0f, 1.5f);
            rot += PI / 8.0f;
            return 18;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(rot + i * TAU/8.0f, 95.0f, 3.5f, 0.9f);
        out[8] = mk(a, 210.0f, 4.5f, 1.6f);
        rot += PI / 8.0f;
        return 9;
    }
};

class ManEatingBoulder : public Enemy {
public:
    ManEatingBoulder() : Enemy(320, 160, 258, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "MAN-EATING BOULDER"; }
    float       fire_interval() const override { return ENRAGED ? 1.6f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // rock fragments — inner ring bounces
            for (int i = 0; i < 8; i++)
                out[i]   = mk(i * TAU/8.0f,            80.0f, 7.0f, 2.5f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mkb(PI/8.0f + i * TAU/8.0f, 70.0f, 5.0f, 1.8f);
            return 16;
        }
        for (int i = 0; i < 4; i++)
            out[i]   = mk(i * PI/2.0f,            70.0f, 7.0f, 2.2f);
        for (int i = 0; i < 4; i++)
            out[i+4] = mkb(PI/4.0f + i * PI/2.0f, 60.0f, 5.0f, 1.6f);
        return 8;
    }
};

class Angont : public Enemy {
public:
    Angont() : Enemy(320, 160, 272, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ANGONT"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 9; i++)
                out[i] = mk(a + (i-4)*0.28f, 195.0f, 4.0f, 1.5f);
            out[9]  = mk(a,         270.0f, 4.5f, 2.0f);
            return 10;
        }
        for (int i = 0; i < 7; i++)
            out[i] = mk(a + (i-3)*0.3f, 170.0f, 4.0f, 1.3f);
        return 7;
    }
};

class TsenaGahi : public Enemy {
    float spin = 0.0f;
public:
    TsenaGahi() : Enemy(320, 160, 285, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "TSE'NAGAHI"; }
    float       fire_interval() const override { return ENRAGED ? 1.2f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // rolling stone — half the shots bounce
            for (int i = 0; i < 8; i++)
                out[i]   = mk(spin + i * TAU/8.0f,              105.0f, 6.0f, 2.2f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mkb(spin + PI/8.0f + i * TAU/8.0f,   90.0f, 5.0f, 1.8f);
            spin += PI / 16.0f;
            return 16;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(spin + i * TAU/8.0f, 90.0f, 6.0f, 2.0f);
        spin += PI / 8.0f;
        return 8;
    }
};

class Anaye : public Enemy {
public:
    Anaye() : Enemy(320, 160, 300, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "ANAYE"; }
    float       fire_interval() const override { return ENRAGED ? 2.0f : 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 95.0f, 6.0f, 2.0f);
            out[12] = mk(a,         165.0f, 7.5f, 3.5f);
            out[13] = mk(a + 0.35f, 135.0f, 6.0f, 2.5f);
            out[14] = mk(a - 0.35f, 135.0f, 6.0f, 2.5f);
            out[15] = mk(a + 0.7f,  110.0f, 5.0f, 2.0f);
            out[16] = mk(a - 0.7f,  110.0f, 5.0f, 2.0f);
            return 17;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(i * TAU/8.0f, 85.0f, 6.0f, 1.8f);
        out[8]  = mk(a,         150.0f, 7.0f, 3.0f);
        out[9]  = mk(a + 0.4f,  120.0f, 5.0f, 2.2f);
        out[10] = mk(a - 0.4f,  120.0f, 5.0f, 2.2f);
        out[11] = mksp(a + PI/4.0f, 45.0f, 0.5f);
        out[12] = mksp(a - PI/4.0f, 45.0f, 0.5f);
        return 13;
    }
};

// ── Mountains enemies (IDs 35–41) ─────────────────────────────────────────────

class Lomie : public Enemy {
public:
    Lomie() : Enemy(320, 160, 290, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "LOMIE"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.28f, 210.0f, 4.0f, 1.8f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.28f, 185.0f, 4.0f, 1.5f);
        return 3;
    }
};

class CuSith : public Enemy {
public:
    CuSith() : Enemy(320, 160, 310, {1.0f,1.0f,1.0f,1.25f,1.0f,1.5f,1.25f}) {}
    const char* name()          const override { return "CU SITH"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 6; i++)
                out[i] = mk(a + (i-2.5f)*0.28f, 215.0f, 4.0f, 1.8f);
            return 6;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(a + (i-1.5f)*0.25f, 190.0f, 4.0f, 1.5f);
        return 4;
    }
};

class CelestialStag : public Enemy {
public:
    CelestialStag() : Enemy(320, 160, 325, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "CELESTIAL STAG"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 4; i++)
                out[i] = mk(a + (i-1.5f)*0.3f, 205.0f, 4.0f, 1.7f);
            out[4] = mk(a + PI/2.0f, 160.0f, 3.5f, 1.2f);
            out[5] = mk(a - PI/2.0f, 160.0f, 3.5f, 1.2f);
            for (int i = 0; i < 6; i++)
                out[i+6] = mk(i * TAU/6.0f, 80.0f, 4.0f, 1.2f);
            return 12;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(a + (i-1.5f)*0.3f, 185.0f, 4.0f, 1.5f);
        out[4] = mk(a + PI/2.0f, 140.0f, 3.5f, 1.0f);
        out[5] = mk(a - PI/2.0f, 140.0f, 3.5f, 1.0f);
        return 6;
    }
};

class Igtuk : public Enemy {
    int phase = 0;
public:
    Igtuk() : Enemy(320, 160, 340, {0.5f,0.5f,0.5f,0.5f,0.75f,1.0f,0.75f}) {}
    const char* name()          const override { return "IGTUK"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // phase shot + bouncing ghost projectiles simultaneously
            out[0] = mk(aim_at(x,y,px,py), 220.0f, 4.5f, 2.0f);
            for (int i = 0; i < 6; i++)
                out[i+1] = mkb(ernd() * TAU, 140.0f, 3.5f, 1.1f);
            return 7;
        }
        if (phase % 2 == 0) {
            out[0] = mk(aim_at(x,y,px,py), 200.0f, 4.0f, 1.6f);
            phase++; return 1;
        } else {
            // ghost shots bounce around the arena
            for (int i = 0; i < 6; i++)
                out[i] = mkb(ernd() * TAU, 120.0f, 3.5f, 0.9f);
            phase++; return 6;
        }
    }
};

class Ajaju : public Enemy {
    float coil = 0.0f;
public:
    Ajaju() : Enemy(320, 160, 360, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "AJAJU"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         220.0f, 5.0f, 2.2f);
            out[1] = mk(a + 0.25f, 200.0f, 4.5f, 1.9f);
            out[2] = mk(a - 0.25f, 200.0f, 4.5f, 1.9f);
            for (int i = 0; i < 8; i++)
                out[i+3] = mk(coil + i * TAU/8.0f, 115.0f, 3.5f, 1.1f);
            coil += PI / 8.0f;
            return 11;
        }
        out[0] = mk(a, 200.0f, 4.5f, 1.8f);
        for (int i = 0; i < 5; i++)
            out[i+1] = mk(coil + i * TAU/5.0f, 100.0f, 3.5f, 1.0f);
        coil += PI / 5.0f;
        return 6;
    }
};

class SlideRockBolter : public Enemy {
public:
    SlideRockBolter() : Enemy(320, 160, 380, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SLIDE-ROCK BOLTER"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.35f, 165.0f, 6.5f, 3.0f);
            out[5] = mk(a + PI/2.0f, 130.0f, 5.0f, 2.0f);
            out[6] = mk(a - PI/2.0f, 130.0f, 5.0f, 2.0f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.35f, 140.0f, 6.0f, 2.5f);
        return 5;
    }
};

class Sasnalkahi : public Enemy {
public:
    Sasnalkahi() : Enemy(320, 160, 400, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SASNALKAHI"; }
    float       fire_interval() const override { return ENRAGED ? 1.1f : 1.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.28f, 200.0f, 5.5f, 2.6f);
            out[7] = mksp(a, 60.0f, 0.4f);
            return 8;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.3f, 175.0f, 5.5f, 2.2f);
        out[5] = mksp(a, 55.0f, 0.5f);
        return 6;
    }
};

// ── Ocean enemies (IDs 42–49) ─────────────────────────────────────────────────

class Nykur : public Enemy {
public:
    Nykur() : Enemy(320, 160, 380, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "NYKUR"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.3f, 215.0f, 4.5f, 2.1f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.3f, 190.0f, 4.5f, 1.8f);
        return 5;
    }
};

class SazaeOni : public Enemy {
    float spiral = 0.0f;
public:
    SazaeOni() : Enemy(320, 160, 415, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "SAZAE-ONI"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // shell shards — all bouncing
            for (int i = 0; i < 12; i++)
                out[i] = mkb(spiral + i * TAU/12.0f, 130.0f, 5.0f, 2.0f);
            spiral += PI / 12.0f;
            return 12;
        }
        // alternating: normal then bouncing spiral
        for (int i = 0; i < 3; i++)
            out[i]   = mk(spiral + i * TAU/3.0f,            100.0f, 6.0f, 2.0f);
        for (int i = 0; i < 3; i++)
            out[i+3] = mkb(spiral + PI/3.0f + i * TAU/3.0f, 90.0f, 5.0f, 1.6f);
        spiral += PI / 6.0f;
        return 6;
    }
};

class Itqiirpak : public Enemy {
    int phase = 0;
public:
    Itqiirpak() : Enemy(320, 160, 445, {1.25f,1.5f,2.0f,0.75f,0.75f,1.5f,1.0f}) {}
    const char* name()          const override { return "ITQIIRPAK"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 10; i++)
                out[i] = mk(i * TAU/10.0f, 120.0f, 4.0f, 1.5f);
            for (int i = 0; i < 5; i++)
                out[i+10] = mk(a + (i-2)*0.22f, 240.0f, 4.5f, 2.3f);
            return 15;
        }
        if (phase % 2 == 0) {
            for (int i = 0; i < 10; i++)
                out[i] = mk(i * TAU/10.0f, 110.0f, 4.0f, 1.3f);
            phase++; return 10;
        } else {
            for (int i = 0; i < 4; i++)
                out[i] = mk(a + (i-1.5f)*0.22f, 220.0f, 4.5f, 2.0f);
            phase++; return 4;
        }
    }
};

class KusaKap : public Enemy {
public:
    KusaKap() : Enemy(320, 160, 475, {0.75f,0.75f,1.0f,1.0f,1.5f,1.25f,1.25f}) {}
    const char* name()          const override { return "KUSA KAP"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(a + (i-3.5f)*0.3f, 190.0f, 4.5f, 2.2f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mk(i * TAU/8.0f, 85.0f, 4.0f, 1.4f);
            return 16;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(a + (i-3.5f)*0.3f, 165.0f, 4.5f, 1.9f);
        return 8;
    }
};

class Lusca : public Enemy {
    float tentrot = 0.0f;
public:
    Lusca() : Enemy(320, 160, 515, {0.75f,0.75f,1.0f,1.0f,1.5f,1.25f,1.25f}) {}
    const char* name()          const override { return "LUSCA"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         235.0f, 5.5f, 2.8f);
            out[1] = mk(a + 0.3f,  205.0f, 5.0f, 2.3f);
            out[2] = mk(a - 0.3f,  205.0f, 5.0f, 2.3f);
            out[3] = mk(a + 0.6f,  175.0f, 4.5f, 1.9f);
            out[4] = mk(a - 0.6f,  175.0f, 4.5f, 1.9f);
            for (int i = 0; i < 8; i++)
                out[i+5] = mk(tentrot + i * TAU/8.0f, 105.0f, 4.0f, 1.4f);
            tentrot += PI / 8.0f;
            return 13;
        }
        out[0] = mk(a,         210.0f, 5.0f, 2.2f);
        out[1] = mk(a + 0.35f, 180.0f, 4.5f, 1.8f);
        out[2] = mk(a - 0.35f, 180.0f, 4.5f, 1.8f);
        for (int i = 0; i < 5; i++)
            out[i+3] = mk(tentrot + i * TAU/5.0f, 90.0f, 4.0f, 1.2f);
        tentrot += PI / 5.0f;
        return 8;
    }
};

class MohaMoha : public Enemy {
public:
    MohaMoha() : Enemy(320, 160, 555, {0.5f,1.5f,0.5f,1.5f,1.5f,0.75f,1.0f}) {}
    const char* name()          const override { return "MOHA-MOHA"; }
    float       fire_interval() const override { return ENRAGED ? 2.0f : 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 90.0f, 7.5f, 2.8f);
            out[8]  = mk(a,         180.0f, 7.0f, 4.0f);
            out[9]  = mk(a + 0.4f,  150.0f, 6.0f, 3.2f);
            out[10] = mk(a - 0.4f,  150.0f, 6.0f, 3.2f);
            out[11] = mk(a + 0.8f,  120.0f, 5.0f, 2.5f);
            out[12] = mk(a - 0.8f,  120.0f, 5.0f, 2.5f);
            return 13;
        }
        for (int i = 0; i < 6; i++)
            out[i] = mk(i * TAU/6.0f, 80.0f, 7.5f, 2.5f);
        out[6] = mk(a,         160.0f, 6.5f, 3.5f);
        out[7] = mk(a + 0.5f,  130.0f, 5.5f, 2.8f);
        out[8] = mk(a - 0.5f,  130.0f, 5.5f, 2.8f);
        return 9;
    }
};

class Bjarndyrakongur : public Enemy {
public:
    Bjarndyrakongur() : Enemy(320, 160, 595, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "BJARNDYRAKONGUR"; }
    float       fire_interval() const override { return ENRAGED ? 2.0f : 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 12; i++) {
                float ang = i * TAU/12.0f;
                out[i]    = mk(ang,              110.0f, 5.5f, 2.3f);
                out[i+12] = mk(ang + PI/12.0f,    75.0f, 6.5f, 2.8f);
            }
            out[24] = mk(a,         200.0f, 7.5f, 4.5f);
            out[25] = mk(a + 0.25f, 170.0f, 6.5f, 3.5f);
            out[26] = mk(a - 0.25f, 170.0f, 6.5f, 3.5f);
            out[27] = mksp(a, 50.0f, 0.4f);
            return 28;
        }
        for (int i = 0; i < 12; i++) {
            float ang = i * TAU/12.0f;
            out[i]    = mk(ang,            95.0f, 5.5f, 2.0f);
            out[i+12] = mk(ang + PI/12.0f, 60.0f, 6.5f, 2.5f);
        }
        out[24] = mk(a, 180.0f, 7.0f, 4.0f);
        out[25] = mksp(a, 45.0f, 0.5f);
        return 26;
    }
};

class Physeter : public Enemy {
public:
    Physeter() : Enemy(320, 160, 650, {0.75f,0.75f,1.0f,1.0f,1.5f,1.25f,1.25f}) {}
    const char* name()          const override { return "PHYSETER"; }
    float       fire_interval() const override { return ENRAGED ? 1.7f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 16; i++)
                out[i] = mk(i * TAU/16.0f, 120.0f, 5.5f, 2.5f);
            for (int i = 0; i < 7; i++)
                out[i+16] = mk(a + (i-3)*0.28f, 220.0f, 5.0f, 3.0f);
            out[23] = mksp(a,           40.0f, 0.35f);
            out[24] = mksp(a + PI/2.0f, 35.0f, 0.4f);
            out[25] = mksp(a - PI/2.0f, 35.0f, 0.4f);
            return 26;
        }
        for (int i = 0; i < 16; i++)
            out[i] = mk(i * TAU/16.0f, 105.0f, 5.0f, 2.0f);
        for (int i = 0; i < 5; i++)
            out[i+16] = mk(a + (i-2)*0.3f, 200.0f, 5.0f, 2.5f);
        out[21] = mksp(a, 40.0f, 0.4f);
        return 22;
    }
};

// ── Factory ───────────────────────────────────────────────────────────────────

Enemy* enemy_create(int id) {
    switch (id) {
        case  0: return new Skvader();
        case  1: return new Wolpertinger();
        case  2: return new Treesqueak();
        case  3: return new Qique();
        case  4: return new Lili();
        case  5: return new CrowingCrestedCobra();
        case  6: return new WakmangganchiAragondi();
        case  7: return new Alber();
        case  8: return new Snawfus();
        case  9: return new QuestingBeast();
        case 10: return new GrandGoule();
        case 11: return new Paoxiao();
        case 12: return new Ebigane();
        case 13: return new BeastOfTheCharredForests();
        case 14: return new Lodsilungur();
        case 15: return new Ofuguggi();
        case 16: return new Kamaitachi();
        case 17: return new Qiqirn();
        case 18: return new Vatnaormur();
        case 19: return new Skeljaskrimsli();
        case 20: return new Sermilik();
        case 21: return new Asp();
        case 22: return new CactusCat();
        case 23: return new OlgoiKhorkhoi();
        case 24: return new Zoureg();
        case 25: return new Myrmecoleon();
        case 26: return new Akhekh();
        case 27: return new Grootslang();
        case 28: return new Opimachus();
        case 29: return new Karnabo();
        case 30: return new Dajna();
        case 31: return new ManEatingBoulder();
        case 32: return new Angont();
        case 33: return new TsenaGahi();
        case 34: return new Anaye();
        case 35: return new Lomie();
        case 36: return new CuSith();
        case 37: return new CelestialStag();
        case 38: return new Igtuk();
        case 39: return new Ajaju();
        case 40: return new SlideRockBolter();
        case 41: return new Sasnalkahi();
        case 42: return new Nykur();
        case 43: return new SazaeOni();
        case 44: return new Itqiirpak();
        case 45: return new KusaKap();
        case 46: return new Lusca();
        case 47: return new MohaMoha();
        case 48: return new Bjarndyrakongur();
        case 49: return new Physeter();
        default: return new Skvader();
    }
}
