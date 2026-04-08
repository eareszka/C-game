#ifndef INPUT_H
#define INPUT_H

#include <SDL2/SDL.h>
#include <stdbool.h>

typedef enum {
    KEY_UP,
    KEY_PRESSED,
    KEY_HELD,
    KEY_RELEASED
} KeyState;

typedef struct Input {
    bool quit;
    KeyState keys[SDL_NUM_SCANCODES];
} Input;

void input_init(Input* in);
void input_begin_frame(Input* in);
void input_handle_event(Input* in, const SDL_Event* e);

bool input_down(const Input* in, SDL_Scancode key);
bool input_pressed(const Input* in, SDL_Scancode key);
bool input_released(const Input* in, SDL_Scancode key);

#endif
