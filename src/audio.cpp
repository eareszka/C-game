// Sound: the mixer, and the recipes every clip is synthesized from. See audio.h.
#include "audio.h"
#include <SDL2/SDL.h>
#include <atomic>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>

static const int   RATE   = 44100;
static const int   VOICES = 16;
static const float PI_F   = 3.14159265f;
static const float TAU_F  = 6.28318530f;

// ── The synth ────────────────────────────────────────────────────────────────
//
// A clip is a few layers summed, then a post stage. A layer is one oscillator
// sliding from f0 to f1 Hz over its length (exponentially, so sweeps sound
// musical), shaped by an attack / decay-to-sustain / release envelope, through
// its own low-pass. Noise is white through the same low-pass. The post stage
// is another low-pass, a soft drive and a feedback echo: the echo is most of
// what moves these from NES bleeps toward SNES samples. Every clip is then
// normalised to a fixed peak, so the loudness table below is the whole mix.

enum Wave { SINE, TRI, SQUARE, PULSE, SAW, NOISE };

struct Layer {
    Wave  wave;
    float f0, f1;       // Hz at start and end (ignored by NOISE)
    float start, dur;   // seconds: when it begins, how long it sounds
    float gain;
    float lp;           // low-pass cutoff Hz, 0 = none
    float a, d, s, r;   // envelope: attack, decay, sustain level, release (seconds, level)
    float vib_hz, vib;  // vibrato: rate and depth (fraction of pitch)
};

struct Post {
    float lp;           // Hz, 0 = none
    float drive;        // 1 = clean, more = saturates
    float echo_ms;      // 0 = no echo
    float echo_fb;      // feedback 0..1
    float echo_mix;     // how much of the echo is heard
};

struct Recipe {
    std::vector<Layer> layers;
    Post post;
};

// A layer with sensible defaults; the recipes override the few that matter.
static Layer L(Wave w, float f0, float f1, float start, float dur, float gain = 1.0f, float lp = 0.0f) {
    Layer l;
    l.wave = w; l.f0 = f0; l.f1 = f1; l.start = start; l.dur = dur; l.gain = gain; l.lp = lp;
    l.a = 0.003f; l.d = dur * 0.45f; l.s = 0.0f; l.r = dur * 0.25f;
    l.vib_hz = 0.0f; l.vib = 0.0f;
    return l;
}
static Layer env(Layer l, float a, float d, float s, float r) { l.a = a; l.d = d; l.s = s; l.r = r; return l; }
static Layer vib(Layer l, float hz, float depth) { l.vib_hz = hz; l.vib = depth; return l; }
static Post  P(float lp = 0.0f, float drive = 1.0f, float echo_ms = 0.0f, float fb = 0.0f, float mix = 0.0f) {
    return Post{ lp, drive, echo_ms, fb, mix };
}

// A note: a triangle lead with a quiet sine an octave under it, for the
// jingles. Sustained a little so it rings rather than plucks.
static void note(Recipe& r, float hz, float start, float dur, float gain = 1.0f, Wave w = TRI) {
    r.layers.push_back(env(L(w,    hz,        hz,        start, dur, gain,        5000.0f), 0.004f, dur * 0.5f, 0.55f, dur * 0.35f));
    r.layers.push_back(env(L(SINE, hz * 0.5f, hz * 0.5f, start, dur, gain * 0.4f, 0.0f),    0.004f, dur * 0.5f, 0.55f, dur * 0.35f));
}

static Recipe recipe(Sfx s) {
    Recipe r;
    switch (s) {
    case SFX_SHOT:
        r.layers = { L(TRI, 1100, 480, 0, 0.085f, 1.0f, 6500),
                     L(NOISE, 0, 0, 0, 0.025f, 0.3f, 4500) };
        r.post = P(7500, 1.1f);
        break;
    case SFX_ENEMY_HIT:
        r.layers = { L(SQUARE, 240, 75, 0, 0.10f, 0.8f, 1900),
                     L(SINE,   130, 55, 0, 0.13f, 0.9f),
                     L(NOISE, 0, 0, 0, 0.05f, 0.55f, 2600) };
        r.post = P(4000, 1.6f);
        break;
    case SFX_GRAZE:
        r.layers = { env(L(SINE, 1900, 1900, 0, 0.04f), 0.001f, 0.03f, 0, 0.01f),
                     env(L(SINE, 3800, 3800, 0, 0.02f, 0.3f), 0.001f, 0.015f, 0, 0.005f) };
        r.post = P(0, 1.0f, 60, 0.3f, 0.35f);
        break;
    case SFX_HURT:
        r.layers = { L(SAW,   520, 50, 0, 0.30f, 1.0f, 2600),
                     L(SQUARE, 260, 40, 0, 0.30f, 0.5f, 1500),
                     L(NOISE, 0, 0, 0, 0.09f, 0.45f, 3000) };
        r.post = P(3200, 2.2f, 90, 0.25f, 0.3f);
        break;
    case SFX_ENRAGE:
        r.layers = { env(L(SQUARE, 170, 780, 0, 0.45f, 0.9f, 3200), 0.02f, 0.2f, 0.7f, 0.12f),
                     env(L(SINE,    85, 390, 0, 0.45f, 0.6f),        0.02f, 0.2f, 0.7f, 0.12f) };
        r.post = P(4000, 1.4f, 120, 0.4f, 0.4f);
        break;
    case SFX_SWAP:
        r.layers = { L(TRI, 620, 620, 0,     0.05f, 1.0f, 6000),
                     L(TRI, 930, 930, 0.05f, 0.08f, 1.0f, 6000) };
        r.post = P(0, 1.0f, 50, 0.2f, 0.2f);
        break;
    case SFX_VICTORY:
        note(r, 523.25f, 0.00f, 0.16f);
        note(r, 659.25f, 0.11f, 0.16f);
        note(r, 783.99f, 0.22f, 0.16f);
        note(r, 1046.5f, 0.33f, 0.42f);
        r.layers.back() = vib(r.layers.back(), 6.0f, 0.01f);
        r.post = P(0, 1.0f, 150, 0.35f, 0.35f);
        break;
    case SFX_PICKUP:
        r.layers = { env(L(SINE, 1300, 1750, 0, 0.07f), 0.002f, 0.05f, 0, 0.02f),
                     env(L(TRI, 2600, 3500, 0, 0.045f, 0.3f, 7000), 0.002f, 0.03f, 0, 0.01f) };
        r.post = P(0, 1.0f, 50, 0.2f, 0.25f);
        break;
    case SFX_DEFEAT:
        note(r, 440.0f, 0.00f, 0.30f);
        note(r, 349.23f, 0.28f, 0.34f);
        note(r, 311.13f, 0.60f, 0.70f, 0.9f);
        r.layers.back() = vib(r.layers.back(), 5.0f, 0.012f);
        r.post = P(2800, 1.0f, 180, 0.4f, 0.4f);
        break;
    case SFX_BATTLE_START:
        r.layers = { L(SAW,    170, 38, 0, 0.32f, 0.8f, 2200),
                     L(SQUARE,  85, 40, 0, 0.32f, 0.5f, 1200),
                     env(L(NOISE, 0, 0, 0, 0.28f, 0.6f, 1600), 0.01f, 0.2f, 0.1f, 0.08f) };
        r.post = P(2600, 2.0f, 100, 0.3f, 0.3f);
        break;
    case SFX_CURSOR:
        r.layers = { env(L(PULSE, 1250, 1250, 0, 0.035f, 1.0f, 5500), 0.001f, 0.03f, 0, 0.008f),
                     env(L(SINE,  2500, 2500, 0, 0.03f,  0.3f),        0.001f, 0.025f, 0, 0.005f) };
        r.post = P();
        break;
    case SFX_CONFIRM:
        r.layers = { L(TRI,  880, 880,  0,     0.06f, 1.0f, 6000),
                     L(TRI, 1320, 1320, 0.06f, 0.11f, 1.0f, 6000) };
        r.post = P(0, 1.0f, 70, 0.25f, 0.3f);
        break;
    case SFX_BACK:
        r.layers = { L(TRI, 1100, 1100, 0,     0.06f, 1.0f, 6000),
                     L(TRI,  740,  740, 0.06f, 0.10f, 1.0f, 6000) };
        r.post = P(0, 1.0f, 60, 0.2f, 0.25f);
        break;
    case SFX_DENY:
        r.layers = { env(L(SQUARE, 220, 215, 0,     0.09f, 1.0f, 2000), 0.002f, 0.08f, 0.3f, 0.02f),
                     env(L(SQUARE, 200, 195, 0.11f, 0.13f, 1.0f, 2000), 0.002f, 0.1f,  0.3f, 0.03f) };
        r.post = P(2500, 1.3f);
        break;
    case SFX_DONE:
        note(r, 783.99f, 0.00f, 0.10f);
        note(r, 987.77f, 0.08f, 0.10f);
        note(r, 1174.7f, 0.16f, 0.28f);
        r.post = P(0, 1.0f, 100, 0.3f, 0.3f);
        break;
    case SFX_TEXT_BLIP:
        r.layers = { env(L(SINE, 1200, 1200, 0, 0.04f), 0.002f, 0.03f, 0, 0.008f) };
        r.post = P();
        break;
    case SFX_SWING:
        r.layers = { env(L(NOISE, 0, 0, 0, 0.10f, 1.0f, 1800), 0.02f, 0.05f, 0.2f, 0.03f),
                     L(SINE, 300, 110, 0, 0.08f, 0.35f) };
        r.post = P(2400, 1.0f);
        break;
    case SFX_NODE_HIT:
        r.layers = { L(SINE,   190, 85,  0, 0.07f, 1.0f),
                     L(NOISE, 0, 0, 0, 0.035f, 0.7f, 3500),
                     L(SQUARE, 620, 300, 0, 0.03f, 0.3f, 3000) };
        r.post = P(4500, 1.4f);
        break;
    case SFX_NODE_BREAK:
        r.layers = { L(SINE,   160, 48,  0, 0.20f, 1.0f),
                     L(NOISE, 0, 0, 0, 0.04f, 0.8f, 3500),
                     env(L(NOISE, 0, 0, 0.02f, 0.26f, 0.6f, 2200), 0.005f, 0.15f, 0.0f, 0.08f),
                     L(SQUARE, 520, 180, 0, 0.05f, 0.3f, 2500) };
        r.post = P(3800, 1.5f, 60, 0.2f, 0.2f);
        break;
    case SFX_CHEST:
        r.layers = { L(TRI, 660, 660, 0,     0.08f, 1.0f, 6000),
                     L(TRI, 990, 990, 0.08f, 0.12f, 1.0f, 6000),
                     vib(env(L(SINE, 1980, 1980, 0.18f, 0.30f, 0.5f), 0.004f, 0.15f, 0.4f, 0.1f), 7.0f, 0.01f) };
        r.post = P(0, 1.0f, 120, 0.3f, 0.35f);
        break;
    case SFX_LEVEL_UP:
        note(r, 523.25f, 0.00f, 0.13f);
        note(r, 659.25f, 0.09f, 0.13f);
        note(r, 783.99f, 0.18f, 0.13f);
        note(r, 1046.5f, 0.27f, 0.13f);
        note(r, 1318.5f, 0.36f, 0.55f);
        r.layers.back() = vib(r.layers.back(), 6.0f, 0.012f);
        r.post = P(0, 1.0f, 160, 0.35f, 0.4f);
        break;
    case SFX_STAIRS:   // the WAV (stairs.wav) replaces this at start-up
        r.layers = { L(TRI, 500, 500, 0.0f, 0.09f, 1.0f, 5000),
                     L(TRI, 420, 420, 0.1f, 0.09f, 1.0f, 5000),
                     L(TRI, 350, 350, 0.2f, 0.12f, 1.0f, 5000) };
        r.post = P(0, 1.0f, 80, 0.25f, 0.3f);
        break;
    default:
        break;
    }
    return r;
}

// How loud each clip plays (after normalising), the least time between two
// plays of it, and how much its pitch wanders play to play so a run of them
// doesn't sound like one sample on repeat.
struct Mix { float gain; int gap_ms; float jitter; };
static const Mix MIX[SFX_COUNT] = {
    /* SHOT         */ { 0.40f, 45, 0.04f },
    /* ENEMY_HIT    */ { 0.55f, 60, 0.05f },
    /* GRAZE        */ { 0.35f, 40, 0.03f },
    /* HURT         */ { 0.90f,  0, 0.00f },
    /* ENRAGE       */ { 0.80f,  0, 0.00f },
    /* SWAP         */ { 0.55f,  0, 0.00f },
    /* VICTORY      */ { 0.80f,  0, 0.00f },
    /* PICKUP       */ { 0.45f, 25, 0.00f },
    /* DEFEAT       */ { 0.80f,  0, 0.00f },
    /* BATTLE_START */ { 0.85f,  0, 0.00f },
    /* CURSOR       */ { 0.45f,  0, 0.00f },
    /* CONFIRM      */ { 0.55f,  0, 0.00f },
    /* BACK         */ { 0.50f,  0, 0.00f },
    /* DENY         */ { 0.60f,  0, 0.00f },
    /* DONE         */ { 0.70f,  0, 0.00f },
    /* TEXT_BLIP    */ { 0.16f, 30, 0.02f },
    /* SWING        */ { 0.40f, 50, 0.05f },
    /* NODE_HIT     */ { 0.60f, 40, 0.06f },
    /* NODE_BREAK   */ { 0.70f,  0, 0.04f },
    /* CHEST        */ { 0.70f,  0, 0.00f },
    /* LEVEL_UP     */ { 0.80f,  0, 0.00f },
    /* STAIRS       */ { 0.80f,  0, 0.00f },
};

static const char* NAMES[SFX_COUNT] = {
    "shot", "enemy_hit", "graze", "hurt", "enrage", "swap", "victory", "pickup", "defeat", "battle_start",
    "cursor", "confirm", "back", "deny", "done", "text_blip",
    "swing", "node_hit", "node_break", "chest", "level_up", "stairs",
};

const char* sfx_name(Sfx s) { return s >= 0 && s < SFX_COUNT ? NAMES[s] : "?"; }
int audio_rate() { return RATE; }

// The envelope at t seconds into a layer of length dur.
static float envelope(const Layer& l, float t) {
    if (t < 0.0f || t >= l.dur) return 0.0f;
    float e = t < l.a ? t / l.a : l.s + (1.0f - l.s) * expf(-(t - l.a) / fmaxf(l.d, 1e-4f));
    float left = l.dur - t;
    if (left < l.r) e *= left / fmaxf(l.r, 1e-4f);
    return e;
}

static float lp_alpha(float hz) {
    return hz <= 0.0f ? 1.0f : 1.0f - expf(-TAU_F * hz / RATE);
}

// Render one recipe to samples at RATE, normalised to peak 0.9.
static std::vector<float> render(const Recipe& r) {
    float end = 0.0f;
    for (const Layer& l : r.layers) end = fmaxf(end, l.start + l.dur);
    // The echo's tail: until it has died to 1%.
    float tail = 0.0f;
    if (r.post.echo_ms > 0.0f && r.post.echo_fb > 0.0f && r.post.echo_mix > 0.0f) {
        int bounces = (int)ceilf(logf(0.01f) / logf(fmaxf(r.post.echo_fb, 0.02f)));
        tail = fminf(bounces * r.post.echo_ms * 0.001f, 0.7f);
    }
    int n = (int)((end + tail) * RATE) + 1;
    std::vector<float> out(n, 0.0f);

    unsigned rng = 0x9E3779B9u;
    for (const Layer& l : r.layers) {
        float phase = 0.0f, y = 0.0f, alpha = lp_alpha(l.lp);
        int s0 = (int)(l.start * RATE), s1 = (int)((l.start + l.dur) * RATE);
        if (s1 > n) s1 = n;
        for (int i = s0; i < s1; i++) {
            float t = (i - s0) / (float)RATE;
            float x;
            if (l.wave == NOISE) {
                rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
                x = (rng >> 8) * (1.0f / 8388608.0f) - 1.0f;
            } else {
                float u = l.dur > 0.0f ? t / l.dur : 0.0f;
                float f = l.f0 > 0.0f && l.f1 > 0.0f ? l.f0 * powf(l.f1 / l.f0, u) : l.f0 + (l.f1 - l.f0) * u;
                if (l.vib > 0.0f) f *= 1.0f + l.vib * sinf(TAU_F * l.vib_hz * t);
                phase += f / RATE;
                if (phase >= 1.0f) phase -= 1.0f;
                switch (l.wave) {
                    case SINE:   x = sinf(TAU_F * phase); break;
                    case TRI:    x = 4.0f * fabsf(phase - 0.5f) - 1.0f; break;
                    case SQUARE: x = phase < 0.5f ? 1.0f : -1.0f; break;
                    case PULSE:  x = phase < 0.25f ? 1.0f : -1.0f; break;
                    case SAW:    x = 2.0f * phase - 1.0f; break;
                    default:     x = 0.0f; break;
                }
            }
            y += alpha * (x - y);
            out[i] += y * l.gain * envelope(l, t);
        }
    }

    // Post: low-pass, drive, echo.
    if (r.post.lp > 0.0f) {
        float y = 0.0f, alpha = lp_alpha(r.post.lp);
        for (float& v : out) { y += alpha * (v - y); v = y; }
    }
    if (r.post.drive > 1.0f) {
        float peak = 0.0f;
        for (float v : out) peak = fmaxf(peak, fabsf(v));
        if (peak > 0.0f)
            for (float& v : out) v = tanhf(v / peak * r.post.drive) / tanhf(r.post.drive) * peak;
    }
    if (r.post.echo_ms > 0.0f && r.post.echo_mix > 0.0f) {
        int d = (int)(r.post.echo_ms * 0.001f * RATE);
        if (d > 0 && d < n) {
            std::vector<float> line(d, 0.0f);
            int w = 0;
            for (int i = 0; i < n; i++) {
                float delayed = line[w];
                float x = out[i];
                line[w] = x + delayed * r.post.echo_fb;
                out[i] = x + delayed * r.post.echo_mix;
                if (++w >= d) w = 0;
            }
        }
    }

    float peak = 0.0f;
    for (float v : out) peak = fmaxf(peak, fabsf(v));
    if (peak > 0.0f) for (float& v : out) v *= 0.9f / peak;
    return out;
}

int audio_render_clip(Sfx s, float** out) {
    std::vector<float> v = render(recipe(s));
    *out = (float*)SDL_malloc(v.size() * sizeof(float) + 4);
    memcpy(*out, v.data(), v.size() * sizeof(float));
    return (int)v.size();
}

bool audio_write_wav(const char* path, const float* samples, int n, int rate) {
    SDL_RWops* f = SDL_RWFromFile(path, "wb");
    if (!f) return false;
    Uint32 data_bytes = (Uint32)n * 2;
    SDL_RWwrite(f, "RIFF", 1, 4); SDL_WriteLE32(f, 36 + data_bytes); SDL_RWwrite(f, "WAVE", 1, 4);
    SDL_RWwrite(f, "fmt ", 1, 4); SDL_WriteLE32(f, 16); SDL_WriteLE16(f, 1); SDL_WriteLE16(f, 1);
    SDL_WriteLE32(f, (Uint32)rate); SDL_WriteLE32(f, (Uint32)rate * 2); SDL_WriteLE16(f, 2); SDL_WriteLE16(f, 16);
    SDL_RWwrite(f, "data", 1, 4); SDL_WriteLE32(f, data_bytes);
    for (int i = 0; i < n; i++) {
        float v = samples[i] < -1.0f ? -1.0f : samples[i] > 1.0f ? 1.0f : samples[i];
        SDL_WriteLE16(f, (Uint16)(Sint16)(v * 32767.0f));
    }
    SDL_RWclose(f);
    return true;
}

// ── The mixer ────────────────────────────────────────────────────────────────

struct Clip { std::vector<float> s; };

struct Voice {
    const Clip* clip;
    double      pos;      // sample position; negative while a delayed play waits
    float       step;     // samples advanced per output frame (pitch)
    float       gain;
    bool        active;
};

static Clip               s_clips[SFX_COUNT];
static Voice              s_voices[VOICES];
static SDL_AudioDeviceID  s_dev = 0;
static bool               s_ready = false;
static std::atomic<float> s_master{0.7f};
static std::atomic<float> s_sfx{1.0f};
static int                s_master_i = 7, s_sfx_i = 10;
static Uint32             s_last_play[SFX_COUNT];
static unsigned           s_jitter_rng = 12345u;

static void mix_callback(void*, Uint8* stream, int len) {
    float* out = (float*)stream;
    int frames = len / (int)(sizeof(float) * 2);
    memset(stream, 0, len);
    float vol = s_master.load() * s_sfx.load();
    for (Voice& v : s_voices) {
        if (!v.active) continue;
        const std::vector<float>& s = v.clip->s;
        int n = (int)s.size();
        for (int i = 0; i < frames; i++) {
            if (v.pos < 0.0) { v.pos += 1.0; continue; }
            int k = (int)v.pos;
            if (k + 1 >= n) { v.active = false; break; }
            float frac = (float)(v.pos - k);
            float x = (s[k] + (s[k + 1] - s[k]) * frac) * v.gain * vol;
            out[i * 2]     += x;
            out[i * 2 + 1] += x;
            v.pos += v.step;
        }
    }
    // Soft clip: a few loud things at once round off instead of cracking.
    for (int i = 0; i < frames * 2; i++) {
        float x = out[i];
        out[i] = x / (1.0f + fabsf(x) * 0.5f);
    }
}

// A WAV in assets/sound overrides the synthesized clip: loaded and converted
// to the mixer's format, float mono at RATE.
static bool load_override(Sfx s) {
    std::string path = std::string("assets/sound/") + NAMES[s] + ".wav";
    SDL_AudioSpec spec; Uint8* buf = nullptr; Uint32 len = 0;
    if (!SDL_LoadWAV(path.c_str(), &spec, &buf, &len)) return false;
    SDL_AudioCVT cvt;
    int need = SDL_BuildAudioCVT(&cvt, spec.format, spec.channels, spec.freq, AUDIO_F32SYS, 1, RATE);
    if (need < 0) { SDL_FreeWAV(buf); return false; }
    std::vector<Uint8> work;
    const float* samples; int n;
    if (need == 0) {
        samples = (const float*)buf; n = (int)(len / sizeof(float));
    } else {
        cvt.len = (int)len;
        work.resize((size_t)cvt.len * cvt.len_mult);
        memcpy(work.data(), buf, len);
        cvt.buf = work.data();
        if (SDL_ConvertAudio(&cvt) != 0) { SDL_FreeWAV(buf); return false; }
        samples = (const float*)work.data(); n = cvt.len_cvt / (int)sizeof(float);
    }
    s_clips[s].s.assign(samples, samples + n);
    SDL_FreeWAV(buf);
    return true;
}

bool audio_init() {
    for (int i = 0; i < SFX_COUNT; i++) {
        s_clips[i].s = render(recipe((Sfx)i));
        load_override((Sfx)i);
    }
    memset(s_voices, 0, sizeof(s_voices));
    memset(s_last_play, 0, sizeof(s_last_play));
    if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) { printf("No audio: %s\n", SDL_GetError()); return false; }
    SDL_AudioSpec want = {}, have = {};
    want.freq = RATE; want.format = AUDIO_F32SYS; want.channels = 2; want.samples = 512;
    want.callback = mix_callback;
    s_dev = SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);
    if (!s_dev) { printf("No audio device: %s\n", SDL_GetError()); return false; }
    SDL_PauseAudioDevice(s_dev, 0);
    s_ready = true;
    return true;
}

void audio_shutdown() {
    if (s_dev) { SDL_CloseAudioDevice(s_dev); s_dev = 0; }
    s_ready = false;
}

bool audio_ready() { return s_ready; }

void audio_play_after(Sfx s, float delay_secs, float gain, float pitch) {
    if (!s_ready || s < 0 || s >= SFX_COUNT || s_clips[s].s.size() < 2) return;
    const Mix& m = MIX[s];
    Uint32 now = SDL_GetTicks();
    if (m.gap_ms > 0 && s_last_play[s] && now - s_last_play[s] < (Uint32)m.gap_ms) return;
    s_last_play[s] = now;
    if (m.jitter > 0.0f) {
        s_jitter_rng = s_jitter_rng * 1664525u + 1013904223u;
        pitch *= 1.0f + m.jitter * (((s_jitter_rng >> 8) & 0xFFFF) / 32768.0f - 1.0f);
    }
    SDL_LockAudioDevice(s_dev);
    Voice* v = nullptr;
    for (Voice& c : s_voices) if (!c.active) { v = &c; break; }
    if (!v) {   // every voice busy: take the one furthest along
        v = &s_voices[0];
        for (Voice& c : s_voices) if (c.pos > v->pos) v = &c;
    }
    v->clip   = &s_clips[s];
    v->pos    = -(double)delay_secs * RATE;
    v->step   = pitch > 0.05f ? pitch : 1.0f;
    v->gain   = gain * m.gain;
    v->active = true;
    SDL_UnlockAudioDevice(s_dev);
}

void audio_play(Sfx s, float gain, float pitch) { audio_play_after(s, 0.0f, gain, pitch); }

static float curve(int v) { v = v < 0 ? 0 : v > 10 ? 10 : v; return (v / 10.0f) * (v / 10.0f); }   // quieter steps near the bottom
void audio_set_master(int v) { s_master_i = v < 0 ? 0 : v > 10 ? 10 : v; s_master.store(curve(v)); }
void audio_set_sfx(int v)    { s_sfx_i    = v < 0 ? 0 : v > 10 ? 10 : v; s_sfx.store(curve(v)); }
int  audio_master() { return s_master_i; }
int  audio_sfx()    { return s_sfx_i; }
