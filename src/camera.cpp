#include "camera.h"
#include "tilemap.h"   // wrap_dpx/wrap_dpy
#include <math.h>

static int to_screen(float world, float zoom) {
    return (int)floorf(world * zoom);
}

static void set_origin(Camera* cam, int ox, int oy) {
    cam->ox = ox;
    cam->oy = oy;
    cam->x  = ox / cam->zoom;
    cam->y  = oy / cam->zoom;
}

void camera_place(Camera* cam, float world_x, float world_y) {
    set_origin(cam, to_screen(world_x, cam->zoom), to_screen(world_y, cam->zoom));
}

void camera_follow(Camera* cam, float x, float y, float w, float h) {
    float z = cam->zoom;
    set_origin(cam,
               to_screen(x, z) + (int)(w * z) / 2 - cam->screen_w / 2,
               to_screen(y, z) + (int)(h * z) / 2 - cam->screen_h / 2);
}

int cam_px(const Camera* cam, float world_x) {
    return to_screen(world_x, cam->zoom) - cam->ox;
}

int cam_py(const Camera* cam, float world_y) {
    return to_screen(world_y, cam->zoom) - cam->oy;
}

// The nearest image moves a point by whole world widths, which are whole
// screen pixels at every zoom, so it is applied to the point, not the delta.
int cam_screen_x(const Camera* cam, float world_x) {
    float d = world_x - cam->x;
    return cam_px(cam, world_x + (wrap_dpx(d) - d));
}

int cam_screen_y(const Camera* cam, float world_y) {
    float d = world_y - cam->y;
    return cam_py(cam, world_y + (wrap_dpy(d) - d));
}
