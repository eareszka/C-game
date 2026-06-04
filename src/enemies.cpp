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
    return { cosf(angle)*speed, sinf(angle)*speed, radius, damage };
}

static float aim_at(float ox, float oy, float tx, float ty) {
    return atan2f(ty - oy, tx - ox);
}

// ── Cave enemies (IDs 0–5) ────────────────────────────────────────────────────

class CaveBat : public Enemy {
public:
    CaveBat() : Enemy(320, 160, 25) {}
    const char* name()          const override { return "CAVE BAT"; }
    float       fire_interval() const override { return 0.3f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 180.0f, 3.0f, 0.5f);
        return 1;
    }
};

class CaveSlime : public Enemy {
public:
    CaveSlime() : Enemy(320, 160, 30) {}
    const char* name()          const override { return "CAVE SLIME"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 4; i++)
            out[i] = mk(i * PI/2.0f, 100.0f, 4.0f, 0.8f);
        return 4;
    }
};

class CaveSpider : public Enemy {
public:
    CaveSpider() : Enemy(320, 160, 35) {}
    const char* name()          const override { return "CAVE SPIDER"; }
    float       fire_interval() const override { return 2.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 8; i++)
            out[i] = mk(i * TAU/8.0f, 70.0f, 4.0f, 0.8f);
        return 8;
    }
};

class CaveTroll : public Enemy {
public:
    CaveTroll() : Enemy(320, 160, 40) {}
    const char* name()          const override { return "CAVE TROLL"; }
    float       fire_interval() const override { return 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 60.0f, 8.0f, 3.0f);
        return 1;
    }
};

class CaveWorm : public Enemy {
    bool side = false;
public:
    CaveWorm() : Enemy(320, 160, 30) {}
    const char* name()          const override { return "CAVE WORM"; }
    float       fire_interval() const override { return 0.6f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py) + (side ? 0.4f : -0.4f);
        out[0] = mk(a, 140.0f, 3.5f, 0.7f);
        side = !side;
        return 1;
    }
};

class CaveMushroom : public Enemy {
public:
    CaveMushroom() : Enemy(320, 160, 28) {}
    const char* name()          const override { return "CAVE MUSHROOM"; }
    float       fire_interval() const override { return 1.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 6; i++)
            out[i] = mk(ernd() * TAU, 90.0f, 3.0f, 0.7f);
        return 6;
    }
};

// ── Ruins enemies (IDs 6–11) ──────────────────────────────────────────────────

class RuinsGuard : public Enemy {
public:
    RuinsGuard() : Enemy(320, 160, 40) {}
    const char* name()          const override { return "RUINS GUARD"; }
    float       fire_interval() const override { return 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a - 0.28f, 150.0f, 4.0f, 1.0f);
        out[1] = mk(a,         150.0f, 4.0f, 1.0f);
        out[2] = mk(a + 0.28f, 150.0f, 4.0f, 1.0f);
        return 3;
    }
};

class RuinsArcher : public Enemy {
public:
    RuinsArcher() : Enemy(320, 160, 35) {}
    const char* name()          const override { return "RUINS ARCHER"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a,           240.0f, 3.0f, 1.2f);
        out[1] = mk(a + PI/4.0f, 160.0f, 3.5f, 0.8f);
        out[2] = mk(a - PI/4.0f, 160.0f, 3.5f, 0.8f);
        return 3;
    }
};

class RuinsGolem : public Enemy {
public:
    RuinsGolem() : Enemy(320, 160, 60) {}
    const char* name()          const override { return "RUINS GOLEM"; }
    float       fire_interval() const override { return 2.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 8; i++)
            out[i] = mk(i * TAU/8.0f, 80.0f, 7.0f, 2.0f);
        return 8;
    }
};

class RuinsGhost : public Enemy {
    bool flip = false;
public:
    RuinsGhost() : Enemy(320, 160, 38) {}
    const char* name()          const override { return "RUINS GHOST"; }
    float       fire_interval() const override { return 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py) + (flip ? PI : 0.0f);
        out[0] = mk(a, 160.0f, 4.0f, 1.0f);
        flip = !flip;
        return 1;
    }
};

class RuinsWisp : public Enemy {
    float rot = 0.0f;
public:
    RuinsWisp() : Enemy(320, 160, 32) {}
    const char* name()          const override { return "RUINS WISP"; }
    float       fire_interval() const override { return 0.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 3; i++)
            out[i] = mk(rot + i * TAU/3.0f, 110.0f, 3.5f, 0.9f);
        rot += PI/4.0f;
        return 3;
    }
};

class RuinsColossus : public Enemy {
public:
    RuinsColossus() : Enemy(320, 160, 80) {}
    const char* name()          const override { return "RUINS COLOSSUS"; }
    float       fire_interval() const override { return 3.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 8; i++)
            out[i] = mk(i * PI/4.0f, 120.0f, 5.0f, 1.5f);
        return 8;
    }
};

// ── Graveyard SM enemies (IDs 12–17) ─────────────────────────────────────────

class GraveZombie : public Enemy {
public:
    GraveZombie() : Enemy(320, 160, 35) {}
    const char* name()          const override { return "ZOMBIE"; }
    float       fire_interval() const override { return 0.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 80.0f, 4.0f, 0.8f);
        return 1;
    }
};

class GraveWraith : public Enemy {
    float rot = 0.0f;
public:
    GraveWraith() : Enemy(320, 160, 42) {}
    const char* name()          const override { return "WRAITH"; }
    float       fire_interval() const override { return 0.8f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 6; i++)
            out[i] = mk(rot + i * TAU/6.0f, 100.0f, 3.5f, 0.9f);
        rot += PI/6.0f;
        return 6;
    }
};

class GraveSkeleton : public Enemy {
public:
    GraveSkeleton() : Enemy(320, 160, 38) {}
    const char* name()          const override { return "SKELETON"; }
    float       fire_interval() const override { return 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a,           130.0f, 4.0f, 1.0f);
        out[1] = mk(a + PI/4.0f, 110.0f, 3.5f, 0.8f);
        out[2] = mk(a - PI/4.0f, 110.0f, 3.5f, 0.8f);
        return 3;
    }
};

class GraveGhoul : public Enemy {
public:
    GraveGhoul() : Enemy(320, 160, 45) {}
    const char* name()          const override { return "GHOUL"; }
    float       fire_interval() const override { return 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        for (int i = 0; i < 5; i++)
            out[i] = mk(a - PI/3.0f + i * PI/6.0f, 120.0f, 4.0f, 1.0f);
        return 5;
    }
};

class GraveBanshee : public Enemy {
    int phase = 0;
public:
    GraveBanshee() : Enemy(320, 160, 50) {}
    const char* name()          const override { return "BANSHEE"; }
    float       fire_interval() const override { return 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (phase % 2 == 0) {
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 90.0f, 3.0f, 0.7f);
            phase++; return 12;
        } else {
            float a = aim_at(x, y, px, py);
            out[0] = mk(a - 0.2f, 160.0f, 4.0f, 1.1f);
            out[1] = mk(a,        160.0f, 4.0f, 1.1f);
            out[2] = mk(a + 0.2f, 160.0f, 4.0f, 1.1f);
            phase++; return 3;
        }
    }
};

class GraveLich : public Enemy {
public:
    GraveLich() : Enemy(320, 160, 60) {}
    const char* name()          const override { return "LICH"; }
    float       fire_interval() const override { return 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        for (int i = 0; i < 12; i++)
            out[i] = mk(i * TAU/12.0f, 80.0f, 3.0f, 0.7f);
        out[12] = mk(aim_at(x, y, px, py), 220.0f, 4.5f, 1.5f);
        return 13;
    }
};

// ── Graveyard LG enemies (IDs 18–23) ─────────────────────────────────────────

class LgGraveKnight : public Enemy {
public:
    LgGraveKnight() : Enemy(320, 160, 70) {}
    const char* name()          const override { return "GRAVE KNIGHT"; }
    float       fire_interval() const override { return 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.22f, 140.0f, 4.0f, 1.0f);
        out[5] = mk(a + PI/2.0f, 120.0f, 3.5f, 0.8f);
        out[6] = mk(a - PI/2.0f, 120.0f, 3.5f, 0.8f);
        return 7;
    }
};

class LgGraveRevenant : public Enemy {
public:
    LgGraveRevenant() : Enemy(320, 160, 65) {}
    const char* name()          const override { return "REVENANT"; }
    float       fire_interval() const override { return 0.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 200.0f, 3.0f, 0.6f);
        return 1;
    }
};

class LgGraveDemon : public Enemy {
    float sweep = 0.0f;
public:
    LgGraveDemon() : Enemy(320, 160, 75) {}
    const char* name()          const override { return "DEMON"; }
    float       fire_interval() const override { return 0.8f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 8; i++)
            out[i] = mk(sweep + i * TAU/8.0f, 110.0f, 4.0f, 1.0f);
        sweep += 10.0f * PI/180.0f;
        return 8;
    }
};

class LgGraveNecromancer : public Enemy {
public:
    LgGraveNecromancer() : Enemy(320, 160, 85) {}
    const char* name()          const override { return "NECROMANCER"; }
    float       fire_interval() const override { return 3.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 16; i++)
            out[i] = mk(i * TAU/16.0f, 95.0f, 3.5f, 0.8f);
        return 16;
    }
};

class LgGraveVampire : public Enemy {
    float rot = 0.0f;
public:
    LgGraveVampire() : Enemy(320, 160, 72) {}
    const char* name()          const override { return "VAMPIRE"; }
    float       fire_interval() const override { return 0.6f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 3; i++)
            out[i] = mk(rot + i * TAU/3.0f, 130.0f, 4.0f, 1.0f);
        rot += PI/6.0f;
        return 3;
    }
};

class LgGraveLord : public Enemy {
public:
    LgGraveLord() : Enemy(320, 160, 100) {}
    const char* name()          const override { return "GRAVE LORD"; }
    float       fire_interval() const override { return 2.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 8; i++) {
            float a = i * TAU/8.0f;
            out[i]   = mk(a,          130.0f, 4.0f, 1.0f);
            out[i+8] = mk(a + PI/8.0f, 70.0f, 5.0f, 1.2f);
        }
        return 16;
    }
};

// ── Oasis enemies (IDs 24–29) ─────────────────────────────────────────────────

class OasisSerpent : public Enemy {
public:
    OasisSerpent() : Enemy(320, 160, 45) {}
    const char* name()          const override { return "SERPENT"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        float offsets[5] = { 0.0f, 0.3f, -0.3f, 0.6f, -0.6f };
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + offsets[i], 130.0f, 3.5f, 0.9f);
        return 5;
    }
};

class OasisScorpion : public Enemy {
public:
    OasisScorpion() : Enemy(320, 160, 48) {}
    const char* name()          const override { return "SCORPION"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a,            150.0f, 4.0f, 1.1f);
        out[1] = mk(a + PI/2.0f,  120.0f, 3.5f, 0.8f);
        out[2] = mk(a - PI/2.0f,  120.0f, 3.5f, 0.8f);
        return 3;
    }
};

class OasisMirage : public Enemy {
public:
    OasisMirage() : Enemy(320, 160, 42) {}
    const char* name()          const override { return "MIRAGE"; }
    float       fire_interval() const override { return 1.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 4; i++)
            out[i] = mk(PI/4.0f + i * PI/2.0f, 120.0f, 4.0f, 1.0f);
        return 4;
    }
};

class OasisSandworm : public Enemy {
public:
    OasisSandworm() : Enemy(320, 160, 55) {}
    const char* name()          const override { return "SANDWORM"; }
    float       fire_interval() const override { return 2.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 10; i++)
            out[i] = mk(i * TAU/10.0f, 75.0f, 5.0f, 1.0f);
        return 10;
    }
};

class OasisDjinn : public Enemy {
    float ring_rot = 0.0f;
public:
    OasisDjinn() : Enemy(320, 160, 52) {}
    const char* name()          const override { return "DJINN"; }
    float       fire_interval() const override { return 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 220.0f, 3.5f, 1.3f);
        for (int i = 0; i < 5; i++)
            out[i+1] = mk(ring_rot + i * TAU/5.0f, 90.0f, 3.5f, 0.8f);
        ring_rot += PI/5.0f;
        return 6;
    }
};

class OasisCrocodile : public Enemy {
    bool toward = true;
public:
    OasisCrocodile() : Enemy(320, 160, 58) {}
    const char* name()          const override { return "CROCODILE"; }
    float       fire_interval() const override { return 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py) + (toward ? 0.0f : PI);
        out[0] = mk(a, 150.0f, 5.0f, 1.2f);
        toward = !toward;
        return 1;
    }
};

// ── Pyramid enemies (IDs 30–35) ───────────────────────────────────────────────

class PyramidMummy : public Enemy {
public:
    PyramidMummy() : Enemy(320, 160, 50) {}
    const char* name()          const override { return "MUMMY"; }
    float       fire_interval() const override { return 2.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 4; i++)
            out[i] = mk(i * PI/2.0f, 40.0f, 6.0f, 1.5f);
        return 4;
    }
};

class PyramidScarab : public Enemy {
public:
    PyramidScarab() : Enemy(320, 160, 30) {}
    const char* name()          const override { return "SCARAB"; }
    float       fire_interval() const override { return 0.25f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 280.0f, 2.0f, 0.4f);
        return 1;
    }
};

class PyramidAnubis : public Enemy {
public:
    PyramidAnubis() : Enemy(320, 160, 75) {}
    const char* name()          const override { return "ANUBIS"; }
    float       fire_interval() const override { return 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        for (int i = 0; i < 10; i++)
            out[i] = mk(i * TAU/10.0f, 90.0f, 4.0f, 0.9f);
        float a = aim_at(x, y, px, py);
        out[10] = mk(a,      200.0f, 4.5f, 1.5f);
        out[11] = mk(a + PI, 130.0f, 4.5f, 1.0f);
        return 12;
    }
};

class PyramidBastet : public Enemy {
public:
    PyramidBastet() : Enemy(320, 160, 65) {}
    const char* name()          const override { return "BASTET"; }
    float       fire_interval() const override { return 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.1f, 100.0f + i*25.0f, 3.5f, 1.0f);
        return 5;
    }
};

class PyramidSphinx : public Enemy {
public:
    PyramidSphinx() : Enemy(320, 160, 80) {}
    const char* name()          const override { return "SPHINX"; }
    float       fire_interval() const override { return 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.08f, 130.0f, 4.0f, 1.2f);
        return 5;
    }
};

class PyramidPharaoh : public Enemy {
public:
    PyramidPharaoh() : Enemy(320, 160, 100) {}
    const char* name()          const override { return "PHARAOH"; }
    float       fire_interval() const override { return 3.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 8; i++) {
            float a = i * TAU/8.0f;
            out[i]   = mk(a,          100.0f, 4.0f, 1.0f);
            out[i+8] = mk(a + PI/8.0f, 60.0f, 5.5f, 1.3f);
        }
        return 16;
    }
};

// ── Stonehenge enemies (IDs 36–41) ────────────────────────────────────────────

class StonehengeAncient : public Enemy {
    float cw = 0.0f;
public:
    StonehengeAncient() : Enemy(320, 160, 65) {}
    const char* name()          const override { return "ANCIENT"; }
    float       fire_interval() const override { return 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 160.0f, 4.0f, 1.2f);
        for (int i = 0; i < 3; i++)
            out[i+1] = mk(cw - i * PI/4.0f, 100.0f, 3.5f, 0.9f);
        cw -= PI/6.0f;
        return 4;
    }
};

class StonehengeDruid : public Enemy {
public:
    StonehengeDruid() : Enemy(320, 160, 60) {}
    const char* name()          const override { return "DRUID"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a,         150.0f, 4.0f, 1.0f);
        out[1] = mk(a + 0.35f, 130.0f, 4.0f, 1.0f);
        out[2] = mk(a - 0.35f, 130.0f, 4.0f, 1.0f);
        out[3] = mk(a + 0.70f, 110.0f, 4.0f, 0.9f);
        out[4] = mk(a - 0.70f, 110.0f, 4.0f, 0.9f);
        return 5;
    }
};

class StonehengeWarden : public Enemy {
public:
    StonehengeWarden() : Enemy(320, 160, 70) {}
    const char* name()          const override { return "WARDEN"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 4; i++)
            out[i] = mk(PI/4.0f + i * PI/2.0f, 130.0f, 4.0f, 1.1f);
        return 4;
    }
};

class StonehengeObserver : public Enemy {
public:
    StonehengeObserver() : Enemy(320, 160, 55) {}
    const char* name()          const override { return "OBSERVER"; }
    float       fire_interval() const override { return 0.4f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        out[0] = mk(aim_at(x, y, px, py), 350.0f, 3.0f, 1.3f);
        return 1;
    }
};

class StonehengeOracle : public Enemy {
    int phase = 0;
public:
    StonehengeOracle() : Enemy(320, 160, 72) {}
    const char* name()          const override { return "ORACLE"; }
    float       fire_interval() const override { return 1.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        float offset = (phase % 2 == 0) ? 0.0f : TAU/10.0f;
        for (int i = 0; i < 5; i++)
            out[i] = mk(offset + i * TAU/5.0f, 110.0f, 4.0f, 1.0f);
        phase++;
        return 5;
    }
};

class StonehengeElder : public Enemy {
    int phase = 0;
public:
    StonehengeElder() : Enemy(320, 160, 90) {}
    const char* name()          const override { return "ELDER"; }
    float       fire_interval() const override { return 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (phase % 2 == 0) {
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 90.0f, 3.5f, 0.8f);
            phase++; return 12;
        } else {
            float a = aim_at(x, y, px, py);
            for (int i = 0; i < 4; i++)
                out[i] = mk(a + (i-1.5f)*0.2f, 170.0f, 4.0f, 1.2f);
            phase++; return 4;
        }
    }
};

// ── Large Tree enemies (IDs 42–47) ────────────────────────────────────────────

class TreeSprite : public Enemy {
public:
    TreeSprite() : Enemy(320, 160, 40) {}
    const char* name()          const override { return "TREE SPRITE"; }
    float       fire_interval() const override { return 0.3f; }
    int fire(float, float, BulletSpawn out[], int) override {
        out[0] = mk(ernd() * TAU, 150.0f, 3.0f, 0.7f);
        return 1;
    }
};

class TreeEntwine : public Enemy {
public:
    TreeEntwine() : Enemy(320, 160, 55) {}
    const char* name()          const override { return "ENTWINE"; }
    float       fire_interval() const override { return 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a,             140.0f, 4.0f, 1.0f);
        out[1] = mk(a + PI/2.0f,   120.0f, 3.5f, 0.9f);
        out[2] = mk(a + PI + 0.3f, 100.0f, 3.5f, 0.8f);
        return 3;
    }
};

class TreeDryad : public Enemy {
public:
    TreeDryad() : Enemy(320, 160, 80) {}
    const char* name()          const override { return "DRYAD"; }
    float       fire_interval() const override { return 3.0f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 20; i++)
            out[i] = mk(i * TAU/20.0f, 60.0f, 3.5f, 0.8f);
        return 20;
    }
};

class TreeWisp : public Enemy {
public:
    TreeWisp() : Enemy(320, 160, 50) {}
    const char* name()          const override { return "WISP"; }
    float       fire_interval() const override { return 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a - 0.08f, 240.0f, 3.0f, 1.1f);
        out[1] = mk(a,          240.0f, 3.0f, 1.1f);
        out[2] = mk(a + 0.08f, 240.0f, 3.0f, 1.1f);
        return 3;
    }
};

class TreeGuardian : public Enemy {
    float aim_angle = 0.0f;
public:
    TreeGuardian() : Enemy(320, 160, 90) {}
    const char* name()          const override { return "GUARDIAN"; }
    float       fire_interval() const override { return 0.7f; }
    void update(float dt, float px, float py) override {
        float target = aim_at(x, y, px, py);
        float diff = target - aim_angle;
        // wrap to [-PI, PI]
        while (diff >  PI) diff -= TAU;
        while (diff < -PI) diff += TAU;
        float max_turn = 1.57f * dt;
        if (diff >  max_turn) diff =  max_turn;
        if (diff < -max_turn) diff = -max_turn;
        aim_angle += diff;
    }
    int fire(float, float, BulletSpawn out[], int) override {
        out[0] = mk(aim_angle, 170.0f, 4.5f, 1.3f);
        return 1;
    }
};

class TreeAncient : public Enemy {
    float cw_rot  = 0.0f;
    float ccw_rot = 0.0f;
public:
    TreeAncient() : Enemy(320, 160, 120) {}
    const char* name()          const override { return "TREE ANCIENT"; }
    float       fire_interval() const override { return 0.5f; }
    int fire(float, float, BulletSpawn out[], int) override {
        for (int i = 0; i < 3; i++)
            out[i]   = mk(cw_rot  + i * TAU/3.0f, 110.0f, 3.5f, 1.0f);
        for (int i = 0; i < 3; i++)
            out[i+3] = mk(ccw_rot - i * TAU/3.0f, 110.0f, 3.5f, 1.0f);
        cw_rot  += PI/8.0f;
        ccw_rot -= PI/8.0f;
        return 6;
    }
};

// ── Overworld enemies (IDs 48–49) ─────────────────────────────────────────────

class OverworldBandit : public Enemy {
public:
    OverworldBandit() : Enemy(320, 160, 30) {}
    const char* name()          const override { return "BANDIT"; }
    float       fire_interval() const override { return 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        out[0] = mk(a,        160.0f, 3.5f, 1.0f);
        out[1] = mk(a + 0.3f, 140.0f, 3.5f, 0.8f);
        return 2;
    }
};

class OverworldDragon : public Enemy {
public:
    OverworldDragon() : Enemy(320, 160, 150) {}
    const char* name()          const override { return "DRAGON"; }
    float       fire_interval() const override { return 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        for (int i = 0; i < 12; i++)
            out[i] = mk(i * TAU/12.0f, 90.0f, 5.0f, 1.0f);
        float a = aim_at(x, y, px, py);
        for (int i = 0; i < 3; i++)
            out[i+12] = mk(a + (i-1)*0.25f, 250.0f, 4.5f, 1.8f);
        return 15;
    }
};

// ── Factory ───────────────────────────────────────────────────────────────────

Enemy* enemy_create(int id) {
    switch (id) {
        // Cave
        case  0: return new CaveBat();
        case  1: return new CaveSlime();
        case  2: return new CaveSpider();
        case  3: return new CaveTroll();
        case  4: return new CaveWorm();
        case  5: return new CaveMushroom();
        // Ruins
        case  6: return new RuinsGuard();
        case  7: return new RuinsArcher();
        case  8: return new RuinsGolem();
        case  9: return new RuinsGhost();
        case 10: return new RuinsWisp();
        case 11: return new RuinsColossus();
        // Graveyard SM
        case 12: return new GraveZombie();
        case 13: return new GraveWraith();
        case 14: return new GraveSkeleton();
        case 15: return new GraveGhoul();
        case 16: return new GraveBanshee();
        case 17: return new GraveLich();
        // Graveyard LG
        case 18: return new LgGraveKnight();
        case 19: return new LgGraveRevenant();
        case 20: return new LgGraveDemon();
        case 21: return new LgGraveNecromancer();
        case 22: return new LgGraveVampire();
        case 23: return new LgGraveLord();
        // Oasis
        case 24: return new OasisSerpent();
        case 25: return new OasisScorpion();
        case 26: return new OasisMirage();
        case 27: return new OasisSandworm();
        case 28: return new OasisDjinn();
        case 29: return new OasisCrocodile();
        // Pyramid
        case 30: return new PyramidMummy();
        case 31: return new PyramidScarab();
        case 32: return new PyramidAnubis();
        case 33: return new PyramidBastet();
        case 34: return new PyramidSphinx();
        case 35: return new PyramidPharaoh();
        // Stonehenge
        case 36: return new StonehengeAncient();
        case 37: return new StonehengeDruid();
        case 38: return new StonehengeWarden();
        case 39: return new StonehengeObserver();
        case 40: return new StonehengeOracle();
        case 41: return new StonehengeElder();
        // Large Tree
        case 42: return new TreeSprite();
        case 43: return new TreeEntwine();
        case 44: return new TreeDryad();
        case 45: return new TreeWisp();
        case 46: return new TreeGuardian();
        case 47: return new TreeAncient();
        // Overworld
        case 48: return new OverworldBandit();
        case 49: return new OverworldDragon();
        default: return new CaveBat();
    }
}
