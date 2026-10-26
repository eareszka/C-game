// sfxdump: every synthesized sound effect written out as a WAV, to audition
// in any player, and checked -- not silent, no NaN, peak under full scale.
// Exits non-zero on a bad clip, so it can gate a build like dngportals.
//
//   make sfxdump && ./sfxdump            -> build_tmp/sfx/<name>.wav
//   ./sfxdump some/dir                   -> that directory instead
#include "audio.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <math.h>
#include <filesystem>
#include <string>

int main(int argc, char** argv) {
    std::string dir = argc > 1 ? argv[1] : "build_tmp/sfx";
    std::error_code ec;
    std::filesystem::create_directories(dir, ec);
    int bad = 0;
    printf("%-14s %7s %7s %6s\n", "clip", "secs", "peak", "rms");
    for (int i = 0; i < SFX_COUNT; i++) {
        Sfx s = (Sfx)i;
        float* buf = nullptr;
        int n = audio_render_clip(s, &buf);
        float peak = 0.0f; double sq = 0.0; bool nan = false;
        for (int k = 0; k < n; k++) {
            if (buf[k] != buf[k]) { nan = true; break; }
            float a = fabsf(buf[k]);
            if (a > peak) peak = a;
            sq += (double)buf[k] * buf[k];
        }
        float rms = n > 0 ? (float)sqrt(sq / n) : 0.0f;
        const char* why = nullptr;
        if (n <= 0)          why = "EMPTY";
        else if (nan)        why = "NAN";
        else if (peak > 1.0f) why = "CLIPS";
        else if (peak < 0.05f) why = "SILENT";
        std::string path = dir + "/" + sfx_name(s) + ".wav";
        if (!why && !audio_write_wav(path.c_str(), buf, n, audio_rate())) why = "UNWRITABLE";
        printf("%-14s %7.3f %7.3f %6.3f %s\n", sfx_name(s), n / (float)audio_rate(), peak, rms, why ? why : "");
        if (why) bad++;
        SDL_free(buf);
    }
    printf("%d clips in %s%s\n", (int)SFX_COUNT, dir.c_str(), bad ? ", BAD" : "");
    return bad ? 1 : 0;
}
