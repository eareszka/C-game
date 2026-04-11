#include "camera.h"
#include <math.h>

void camera_center_on(Camera* cam, float cx, float cy) {
    cam->target_x = cx;
    cam->target_y = cy;
    /* Snap current position too so there is no initial slide. */
    cam->x = cx - cam->screen_w * 0.5f;
    cam->y = cy - cam->screen_h * 0.5f;
}

void camera_update(Camera* cam, float dt, float speed) {
    /* Frame-rate independent exponential lerp toward target.
       t = 1 - e^(-speed * dt)  gives the same feel at any fps. */
    float t = 1.0f - expf(-speed * dt);

    float desired_x = cam->target_x - cam->screen_w * 0.5f;
    float desired_y = cam->target_y - cam->screen_h * 0.5f;

    cam->x += (desired_x - cam->x) * t;
    cam->y += (desired_y - cam->y) * t;
}
