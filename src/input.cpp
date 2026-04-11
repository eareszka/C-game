#include "input.h"

void input_init(Input* in) {
    in->quit = false;

    for (int i = 0; i < SDL_NUM_SCANCODES; i++) {
        in->keys[i] = KEY_UP;
    }
}

void input_begin_frame(Input* in) {
    in->quit = false;
    in->mouse_left_pressed = false;
    in->mouse_wheel = 0;

    for (int i = 0; i < SDL_NUM_SCANCODES; i++) {
        switch (in->keys[i]) {
            case KEY_PRESSED:
                in->keys[i] = KEY_HELD;
                break;

            case KEY_RELEASED:
                in->keys[i] = KEY_UP;
                break;

            default:
                break;
        }
    }
}

void input_handle_event(Input* in, const SDL_Event* e) {
    switch (e->type) {
        case SDL_QUIT:
            in->quit = true;
            break;

        case SDL_KEYDOWN: {
            SDL_Scancode key = e->key.keysym.scancode;

            if (!e->key.repeat) {
                if (in->keys[key] == KEY_UP || in->keys[key] == KEY_RELEASED) {
                    in->keys[key] = KEY_PRESSED;
                }
            }
            break;
        }

        case SDL_KEYUP: {
            SDL_Scancode key = e->key.keysym.scancode;
            in->keys[key] = KEY_RELEASED;
            break;
        }

        case SDL_MOUSEMOTION:
            in->mouse_x = e->motion.x;
            in->mouse_y = e->motion.y;
            break;

        case SDL_MOUSEBUTTONDOWN:
            in->mouse_x = e->button.x;
            in->mouse_y = e->button.y;
            if (e->button.button == SDL_BUTTON_LEFT)
                in->mouse_left_pressed = true;
            break;

        case SDL_MOUSEWHEEL:
            in->mouse_wheel += e->wheel.y;
            break;
    }
}

bool input_down(const Input* in, SDL_Scancode key) {
    return in->keys[key] == KEY_PRESSED || in->keys[key] == KEY_HELD;
}

bool input_pressed(const Input* in, SDL_Scancode key) {
    return in->keys[key] == KEY_PRESSED;
}

bool input_released(const Input* in, SDL_Scancode key) {
    return in->keys[key] == KEY_RELEASED;
}
