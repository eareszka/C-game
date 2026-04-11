#include "camera.h"
#include <math.h>

void camera_center_on(Camera* cam, float target_x, float target_y) {
    float half_w = cam->screen_w * 0.5f / cam->zoom;
    float half_h = cam->screen_h * 0.5f / cam->zoom;
    // Snap to integer pixels so SDL's fullscreen scaling doesn't cause
    // sub-pixel jitter (non-integer scale factors magnify fractional offsets).
    cam->x = floorf(target_x - half_w);
    cam->y = floorf(target_y - half_h);
}
