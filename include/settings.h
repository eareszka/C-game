#ifndef SETTINGS_H
#define SETTINGS_H

// The player's settings, kept in settings.txt beside game.exe (main chdirs
// there), one "key=value" a line. Missing file or key: the default. Written
// whenever the OPTIONS page or F11 changes one. Not the save: a setting is
// the machine's, not the game's.
struct Settings {
    int master_volume = 7;    // 0..10
    int sfx_volume    = 10;   // 0..10
    int fullscreen    = 0;    // 0 / 1
};

Settings* settings();         // the one set
void      settings_load();    // from settings.txt; defaults when it is missing
bool      settings_save();    // to settings.txt; false when it can't be written
void      settings_apply_audio();   // push the volumes into the mixer

#endif
