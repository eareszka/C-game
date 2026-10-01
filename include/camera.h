#ifndef CAMERA_H
#define CAMERA_H

typedef struct Camera {
    float x;
    float y;
    int screen_w;
    int screen_h;
    float zoom;   // 1.0 = normal, <1.0 = zoomed out, >1.0 = zoomed in
    // The top-left in screen pixels: x and y times the zoom, kept as whole
    // numbers. Every draw is floor(world * zoom) minus these, so two things
    // the same world distance apart are always the same screen distance
    // apart -- x and y alone cannot promise that, because at zooms like 0.75
    // and 1.5 they are not exact in a float and a draw rounds a pixel off.
    // x and y are these divided back, for working out what is in view.
    int ox;
    int oy;
} Camera;

// Put the top-left of the view at a world point, on the nearest screen pixel.
void camera_place(Camera* cam, float world_x, float world_y);

// Centre the view on a box w x h drawn at (x, y) -- the player's frame. The
// box comes out at the same screen pixel every frame, however it moves and
// at any zoom: the camera is snapped with the same rounding the box is drawn
// with, rather than from its middle, which at some zooms is half a pixel off.
void camera_follow(Camera* cam, float x, float y, float w, float h);

// Screen position of a world point as it stands, for things drawn by their
// own coordinate (tiles walking an unwrapped range).
int cam_px(const Camera* cam, float world_x);
int cam_py(const Camera* cam, float world_y);

// Screen position of a world point, taken through the nearest image of it on
// the world's wrap axis: a thing just over the seam draws beside the player
// rather than a world away. Everything that is not a tile is placed with these.
int cam_screen_x(const Camera* cam, float world_x);
int cam_screen_y(const Camera* cam, float world_y);

#endif
