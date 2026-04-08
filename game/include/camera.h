#ifndef CAMERA_H
#define CAMERA_H

typedef struct Camera {
    float x;
    float y;
    int screen_w;
    int screen_h;
} Camera;

void camera_center_on(Camera* cam, float target_x, float target_y);

#endif
