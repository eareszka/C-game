#ifndef CAMERA_H
#define CAMERA_H

typedef struct Camera {
    float x;
    float y;
    int screen_w;
    int screen_h;
    float zoom;   // 1.0 = normal, <1.0 = zoomed out, >1.0 = zoomed in
} Camera;

void camera_center_on(Camera* cam, float target_x, float target_y);

// Screen position of a world point, taken through the nearest image of it on
// the world's wrap axis: a thing just over the seam draws beside the player
// rather than a world away. Everything that is not a tile is placed with these.
int cam_screen_x(const Camera* cam, float world_x);
int cam_screen_y(const Camera* cam, float world_y);

#endif
