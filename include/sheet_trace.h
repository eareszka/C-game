#ifndef SHEET_TRACE_H
#define SHEET_TRACE_H

// Which cells of assets/tileset.png does the game actually draw?
//
// Only the sheetcensus build defines SHEET_TRACE. It compiles every game source
// with this header forced in first (-include), so each SDL_RenderCopy in the
// game reports its texture and source rect before doing the copy. The macro
// names itself inside its own expansion, which the preprocessor leaves alone,
// so the real call still happens. The shipping build never sees any of this.
//
// SDL.h comes first so the real prototype is declared before the macro exists;
// the sources' own later #include of it is a no-op behind SDL's include guard.
#include <SDL2/SDL.h>

#ifdef SHEET_TRACE
void sheet_trace(SDL_Texture* tex, const SDL_Rect* src);
#define SDL_RenderCopy(r, t, s, d) (sheet_trace((t), (s)), SDL_RenderCopy((r), (t), (s), (d)))
#endif

#endif
