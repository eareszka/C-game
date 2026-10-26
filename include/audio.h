#ifndef AUDIO_H
#define AUDIO_H

// Sound. A small mixer on SDL's own audio callback -- no SDL_mixer, no extra
// DLLs -- playing short clips the game synthesizes at start-up (src/audio.cpp,
// the recipes): layered oscillators with real envelopes, a low-pass and a
// short echo, so it sits nearer the SNES than the NES while staying retro.
//
// Any clip can be replaced without touching code: a WAV at
// assets/sound/<name>.wav, where <name> is the enum's name without SFX_ in
// lower case (shot.wav, enemy_hit.wav, ...), is loaded in place of the
// synthesized one. The stairs have always been one (stairs.wav).
//
// Every call is a no-op until audio_init has run, so the headless tools --
// which link this file through HEADLESS_OBJ but never init it -- stay silent.
enum Sfx {
    // Battle
    SFX_SHOT,          // the player's volley leaves
    SFX_ENEMY_HIT,     // a shot lands (gated like the white flash)
    SFX_GRAZE,         // an enemy shot passes within the graze margin
    SFX_HURT,          // the player loses bars: with the hitstop and red flash
    SFX_ENRAGE,        // the enemy crosses its phase line
    SFX_SWAP,          // Q / E / X changed the weapon
    SFX_VICTORY,       // the fight is won
    SFX_PICKUP,        // a cancelled bullet or drop reaches the player
    SFX_DEFEAT,        // the player's last bar went
    SFX_BATTLE_START,  // the wipe into a fight
    // Menus and speech
    SFX_CURSOR,        // the selection moved
    SFX_CONFIRM,       // a choice taken
    SFX_BACK,          // a step back out
    SFX_DENY,          // a choice refused (NEED MORE MATERIALS, NOT ENOUGH GOLD...)
    SFX_DONE,          // a craft, purchase, heal or cure went through
    SFX_TEXT_BLIP,     // letters typing in the speech box
    // The maps
    SFX_SWING,         // the weapon swung or thrown on the map
    SFX_NODE_HIT,      // it struck a tree, rock, vein or stone
    SFX_NODE_BREAK,    // and that broke
    SFX_CHEST,         // a chest opened
    SFX_LEVEL_UP,      // a level gained
    SFX_STAIRS,        // a door, stair or entrance taken
    SFX_COUNT
};

// The clip's file name without .wav: the enum's name in lower case, no SFX_.
const char* sfx_name(Sfx s);

// Open the device and build the clips. False (and silence) when there is no
// audio device; the game runs on regardless.
bool audio_init();
void audio_shutdown();
bool audio_ready();

// Play a clip now, or after a delay. gain scales the clip's own loudness;
// pitch resamples it (2.0 an octave up). Clips that fire many times a second
// (shots, hits, grazes, text) keep a minimum gap, so a burst is one sound,
// not a buzz.
void audio_play(Sfx s, float gain = 1.0f, float pitch = 1.0f);
void audio_play_after(Sfx s, float delay_secs, float gain = 1.0f, float pitch = 1.0f);

// Volumes 0..10, as the OPTIONS page shows them. Master scales everything;
// sfx the effects (music, when there is any, will have its own).
void audio_set_master(int v);
void audio_set_sfx(int v);
int  audio_master();
int  audio_sfx();

// For tools/sfxdump: the synthesized clip (never the WAV override) as float
// samples at audio_rate(). Needs no device. Free with SDL_free.
int  audio_render_clip(Sfx s, float** out);
int  audio_rate();
// A 16-bit mono WAV of samples in [-1, 1].
bool audio_write_wav(const char* path, const float* samples, int n, int rate);

#endif
