#include "camera.h"

void camera_center_on(Camera* cam, float target_x, float target_y) {
    cam->x = (int)(target_x - cam->screen_w * 0.5f);
    cam->y = (int)(target_y - cam->screen_h * 0.5f);
}
