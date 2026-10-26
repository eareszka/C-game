#include "settings.h"
#include "audio.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static const char* SETTINGS_PATH = "settings.txt";
static Settings s_settings;

Settings* settings() { return &s_settings; }

static int clamp(int v, int lo, int hi) { return v < lo ? lo : v > hi ? hi : v; }

void settings_load() {
    s_settings = Settings{};
    FILE* f = fopen(SETTINGS_PATH, "r");
    if (!f) return;
    char line[128];
    while (fgets(line, sizeof(line), f)) {
        char* eq = strchr(line, '=');
        if (!eq) continue;
        *eq = 0;
        int v = atoi(eq + 1);
        if      (strcmp(line, "master")     == 0) s_settings.master_volume = clamp(v, 0, 10);
        else if (strcmp(line, "sfx")        == 0) s_settings.sfx_volume    = clamp(v, 0, 10);
        else if (strcmp(line, "fullscreen") == 0) s_settings.fullscreen    = v ? 1 : 0;
    }
    fclose(f);
}

bool settings_save() {
    FILE* f = fopen(SETTINGS_PATH, "w");
    if (!f) return false;
    fprintf(f, "master=%d\nsfx=%d\nfullscreen=%d\n",
            s_settings.master_volume, s_settings.sfx_volume, s_settings.fullscreen);
    fclose(f);
    return true;
}

void settings_apply_audio() {
    audio_set_master(s_settings.master_volume);
    audio_set_sfx(s_settings.sfx_volume);
}
