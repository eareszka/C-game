#pragma once
#include <SDL2/SDL.h>
#include <cmath>
#include "camera.h"

// Two side cels per profile, edited directly from the approved walking art.
// Choose the profile
// that faces upward after rotation, with the head toward the pillow.
// Crop transparent margins so the visible body, rather than its canvas,
// is centered on the bed. Match standing NPCs: two world pixels per art pixel.
// The middle of a bed's mattress, in room pixels, from the numbers the room's
// design gives bed() (tools/interior_room.py): x0 its front's left end, fy
// its front row, flip its head at the right. The body is 22 design pixels
// wide (x0 + 2 unflipped), its top 8 rows deep running back up and to the
// right -- to the left when flipped -- and 5 up; design pixels are 2 room
// pixels from (32, 49).
inline void npc_bed_centre(int x0,int fy,bool flip,float* x,float* y) {
    const float body=x0+(flip?0:2),across=11,back=flip?-4.5f:4.5f;
    *x=2*(body+across+back+32);
    *y=2*(fy-5-4+49);
}
inline void npc_sleep_draw(SDL_Renderer* renderer,SDL_Texture* sheet,
                           const Camera* camera,float center_x,float center_y,
                           bool head_right,double seconds) {
    const int breath=(int)std::fmod(seconds/.9,2.0);
    SDL_Rect src={((head_right?0:2)+breath)*14+2,4,11,16};
    const int width=(int)(src.w*2*camera->zoom),height=(int)(src.h*2*camera->zoom);
    SDL_Rect dst={cam_screen_x(camera,center_x)-width/2,
                  cam_screen_y(camera,center_y)-height/2,width,height};
    SDL_RenderCopyEx(renderer,sheet,&src,&dst,head_right?90:-90,nullptr,SDL_FLIP_NONE);

    // Compact 5x5 Zs keep the cream fill and crisp black outlines.
    // Hold them bright for most of the rise, then fade in two discrete steps.
    Uint8 old_r,old_g,old_b,old_a;
    SDL_BlendMode old_blend;
    SDL_GetRenderDrawColor(renderer,&old_r,&old_g,&old_b,&old_a);
    SDL_GetRenderDrawBlendMode(renderer,&old_blend);
    SDL_SetRenderDrawBlendMode(renderer,SDL_BLENDMODE_BLEND);
    for(int i=0;i<3;i++) {
        const double age=std::fmod(seconds+i*1.1,3.3)/3.3;
        const float x=2*std::round((center_x+(head_right?8:-16)+
                         (float)(std::sin(age*5+i)*3))/2);
        const float y=2*std::round((center_y-20-(float)(age*42))/2);
        constexpr float pixel=1;
        constexpr unsigned glyph[]={31,2,4,8,31};
        const Uint8 alpha=age<.8?255:age<.9?170:85;
        for(int pass=0;pass<2;pass++) {
          // Full one-art-pixel outline, like the villagers, rather than a glow.
          SDL_SetRenderDrawColor(renderer,pass?232:0,pass?224:0,pass?192:0,alpha);
          const int radius=pass?0:1;
          for(int row=0;row<5;row++)for(int col=0;col<5;col++) {
            if(!(glyph[row]&(1u<<(4-col))))continue;
            const float left=x+(col-radius)*pixel,top=y+(row-radius)*pixel;
            int x0=cam_screen_x(camera,left),y0=cam_screen_y(camera,top);
            SDL_Rect dot={x0,y0,cam_screen_x(camera,left+(1+2*radius)*pixel)-x0,
                               cam_screen_y(camera,top+(1+2*radius)*pixel)-y0};
            SDL_RenderFillRect(renderer,&dot);
          }
        }
    }
    SDL_SetRenderDrawColor(renderer,old_r,old_g,old_b,old_a);
    SDL_SetRenderDrawBlendMode(renderer,old_blend);
}
