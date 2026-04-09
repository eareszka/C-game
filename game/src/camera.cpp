#include "camera.h"

void camera_center_on(Camera* cam, float target_x, float target_y) {
    float half_w = cam->screen_w * 0.5f / cam->zoom;
    float half_h = cam->screen_h * 0.5f / cam->zoom;
    cam->x = target_x - half_w;
    cam->y = target_y - half_h;
}
