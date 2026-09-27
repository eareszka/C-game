#include "camera.h"
#include "tilemap.h"   // wrap_dpx/wrap_dpy
#include <math.h>

void camera_center_on(Camera* cam, float target_x, float target_y) {
    float half_w = cam->screen_w * 0.5f / cam->zoom;
    float half_h = cam->screen_h * 0.5f / cam->zoom;
    // Quantise to the sub-pixel grid for this zoom level so that
    // (cam->x * zoom) is always an integer — every tile lands on
    // an exact screen pixel with no half-pixel stretching.
    float unit = 1.0f / cam->zoom;
    cam->x = floorf((target_x - half_w) / unit) * unit;
    cam->y = floorf((target_y - half_h) / unit) * unit;
}

int cam_screen_x(const Camera* cam, float world_x) {
    return (int)(wrap_dpx(world_x - cam->x) * cam->zoom);
}

int cam_screen_y(const Camera* cam, float world_y) {
    return (int)(wrap_dpy(world_y - cam->y) * cam->zoom);
}
