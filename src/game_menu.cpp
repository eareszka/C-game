#include "game_menu.h"
#include "crafting.h"
#include "battle.h"
#include "core.h"
#include "fc_palette.h"
#include <SDL2/SDL_image.h>
#include <algorithm>
#include <sstream>
#include <string>
namespace {
    enum {
        ITEMS, MAKE, SAVE, CLOSE, COMMANDS
    };
    const char* commands[] = { "ITEMS","MAKE","SAVE","CLOSE" };
    const SDL_Color white = { 252,252,252,255 }
    ,grey = { 120,120,120,255 }
    ,yellow = { 255,255,80,255 };
    struct Entry {
        bool weapon;
        int id;
    };
    struct Action {
        int kind;
        bool ready;
        const char* why;
        int ore;
        char label[48];
    };
    enum {
        MAKE_ACTION,EQUIP_ACTION,OIL_ACTION,ECHO_ACTION
    };
    const int rows=6,row_height=25,divider=205,col_w=(LST_W-24)/2,cost_y=LST_Y+LST_H-42;
    void text(SDL_Renderer* r,const char* s,int x,int y,int scale,SDL_Color c=white){
        char b[128];
        SDL_strlcpy(b,s?s:"",sizeof(b));
        for(int i=1;b[i];i++)b[i]=(char)SDL_tolower(b[i]);
        draw_text(r,b,x,y,scale,c.r,c.g,c.b);
    }
    void fitted(SDL_Renderer* r,const char* s,int x,int y,int width,int scale,SDL_Color c){
        char b[128];
        SDL_strlcpy(b,s,sizeof(b));
        if(text_width(b,scale)>width){
            while(b[0] && text_width(b,scale)+text_width("...",scale)>width)b[SDL_strlen(b)-1]=0;
            SDL_strlcat(b,"...",sizeof(b));
        }
        text(r,b,x,y,scale,c);
    }
    void wrapped(SDL_Renderer* r,const char* s,int x,int y,int width,int lines,SDL_Color c=white){
        std::istringstream words(s?s:"");
        std::string word,line;
        int n=0;
        while(words>>word){
            std::string next=line+(line.empty()?"":" ")+word;
            if(!line.empty()&&text_width(next.c_str(),2)>width){
                text(r,line.c_str(),x,y+22*n,2,c);
                if(++n>=lines)return;
                line=word;
            }
            else line=next;
        }
        if(!line.empty()&&n<lines)text(r,line.c_str(),x,y+22*n,2,c);
    }
    void sheets(GameMenu* m,SDL_Renderer* r){
        if(m->tried)return;
        m->tried=true;
        m->items=IMG_LoadTexture(r,"assets/items.png");
        m->weapons=IMG_LoadTexture(r,WEAPON_ICON_SHEET);
    }
    void icon(GameMenu* m,SDL_Renderer* r,Item it,int x,int y,int size){
        if(!m->items)return;
        SDL_Rect a = { item_icon(it)*16,0,16,16 }
        ,b = { x,y,size,size };
        SDL_RenderCopy(r,m->items,&a,&b);
    }
    // Where a recipe stands in its column: weapons, then travel, charms, gear,
    // seeing; the used-up ones healing, cures, bombs, the fire. A new recipe
    // goes last until it is given a group.
    int group(const Craft& c){
        if(c.is_weapon)return 0;
        switch(c.item){
            case ITEM_RAFT: case ITEM_SAIL: return 1;
            case ITEM_ESCAPE_CHARM: case ITEM_O2_CHARM: return 2;
            case ITEM_COLD_GEAR: case ITEM_DIVING_FINS: case ITEM_SWIFT_BOOTS: return 3;
            case ITEM_SPYGLASS: case ITEM_COMPASS: case ITEM_BINOCULARS: return 4;
            case ITEM_BAND_AID: case ITEM_MEDKIT: return 5;
            case ITEM_ANTIDOTE: return 6;
            case ITEM_BOMB: case ITEM_SMOKE_BOMB: return 7;
            case ITEM_CAMPFIRE: return 8;
            default: return 9;
        }
    }
    // MAKE and the shop in two columns: what is made once, then what is used
    // up (a recipe the player may hold 999 of). out: craft indices by group,
    // each group in the catalog's (unlock) order.
    int column(int col,int out[]){
        int n=0;
        for(int i=0;i<craft_count();i++)if((craft_at(i).max==999)==(col==1))out[n++]=i;
        std::stable_sort(out,out+n,[](int a,int b){ return group(craft_at(a))<group(craft_at(b)); });
        return n;
    }
    // Craft sel's column and its row there.
    void place(int sel,int* col,int* row){
        int list[64];
        *col=craft_at(sel).max==999;
        int n=column(*col,list);
        *row=int(std::find(list,list+n,sel)-list);
    }
    // The arrows: MAKE/shop up and down a column, left and right across to
    // the other at the same row; ITEMS a grid read left to right.
    void move(GameMenu* m,int count,bool grouped,bool up,bool down,bool left,bool right){
        if(grouped){
            int col,row,list[64];
            place(m->sel,&col,&row);
            if(((left&&col==1)||(right&&col==0))&&column(!col,list))col=!col;
            int n=column(col,list);
            row+=down-up;
            m->sel=list[std::max(0,std::min(row,n-1))];
            return;
        }
        if(left&&m->sel%2)m->sel--;
        if(right&&m->sel%2==0&&m->sel+1<count)m->sel++;
        if(up&&m->sel>=2)m->sel-=2;
        if(down)m->sel=m->sel+2<count?m->sel+2:(m->sel/2+1)*2<count?count-1:m->sel;
    }
    int inventory(const Player* p,Entry out[]){
        int n=0;
        for(int w=0;w<WEAPON_COUNT;w++)if(p->owned[w])out[n++] = { true,w };
        for(int i=0;i<ITEM_COUNT;i++)if(i!=ITEM_SLEEPING_BAG&&item_count(p,(Item)i)>0)out[n++] = { false,i };
        return n;
    }
    int actions(const GameMenu* m,const Player* p,const Entry* entries,Action out[]){
        int n=0;
        if(m->cmd==MAKE){
            const Craft& c=craft_at(m->sel);
            int ore=c.is_weapon?craft_best_ore(p,c):-1;
            if(c.is_weapon&&ore<0)ore=p->owned[c.weapon]?p->arsenal[c.weapon].material+1:MAT_STONE;
            Item missing=craft_missing(p,c);
            Action& a=out[n++];
            a = { MAKE_ACTION,craft_ready(p,c),"NEED MORE MATERIALS",ore,"MAKE" };
            if(missing!=ITEM_COUNT)a.why=item_source(missing);
            else if(craft_at_max(p,c))a.why="ALREADY HAVE";
            if(c.is_weapon){
                if(ore>=MAT_COUNT){
                    a.ore=-1;
                    a.ready=false;
                    a.why="ALREADY BEST";
                    SDL_strlcpy(a.label,"BEST ORE",sizeof(a.label));
                }
                else SDL_snprintf(a.label,sizeof(a.label),"MAKE IN %s",item_name(ore_item((Material)ore)));
                if(p->owned[c.weapon]){
                    const Weapon& w=p->arsenal[c.weapon];
                    out[n] = { OIL_ACTION,w.oil<WEAPON_OIL_MAX&&can_afford(p,oil_recipe(w)),w.oil>=WEAPON_OIL_MAX?"ALREADY MAX":"NEED MORE MATERIALS",-1,"" };
                    SDL_snprintf(out[n].label,sizeof(out[n].label),"FASTER %d/%d",w.oil,WEAPON_OIL_MAX);
                    n++;
                    out[n] = { ECHO_ACTION,w.echo<WEAPON_ECHO_MAX&&can_afford(p,echo_recipe(w)),w.echo>=WEAPON_ECHO_MAX?"ALREADY MAX":"NEED MORE MATERIALS",-1,"" };
                    SDL_snprintf(out[n].label,sizeof(out[n].label),"MORE SHOTS %d/%d",w.echo,WEAPON_ECHO_MAX);
                    n++;
                }
            }
        }
        else if(m->cmd==ITEMS&&entries[m->sel].weapon&&p->equipped!=entries[m->sel].id)out[n++] = { EQUIP_ACTION,true,"",-1,"EQUIP" };
        return n;
    }
    // What it costs, along the foot of the box: each thing's picture with
    // have/need beside it (grey when short), a "+" between them.
    // ponytail: no wrap; four costs at 999/6 fill ~390 of the 446px.
    void cost(GameMenu* m,const Player* p,SDL_Renderer* r,const Recipe& recipe){
        int x=LST_X+14;
        for(int i=0;i<recipe.n;i++){
            const Cost& c=recipe.c[i];
            if(i){
                text(r,"+",x+10,cost_y+8,2);
                x+=20+text_width("+",2);
            }
            icon(m,r,c.item,x,cost_y,32);
            x+=36;
            char b[24];
            SDL_snprintf(b,sizeof(b),"%d/%d",item_count(p,c.item),c.amount);
            text(r,b,x,cost_y+8,2,item_count(p,c.item)>=c.amount?white:grey);
            x+=text_width(b,2);
        }
    }
}
void game_menu_say(GameMenu* m,const char* note){
    m->note=note;
    m->note_t=1.8f;
}
void game_menu_toggle(GameMenu* m){
    m->open=!m->open;
    m->shop=false;
    m->focus=FOCUS_COMMANDS;
    m->sel=0;
    m->note_t=0;
}
void game_menu_open_shop(GameMenu* m){
    m->open=true;
    m->shop=true;
    m->focus=FOCUS_LIST;
    m->sel=0;
    m->note_t=0;
}
void game_menu_update(GameMenu* m,Player* p,const Input* in,float dt){
    if(!m->open)return;
    m->note_t=std::max(0.0f,m->note_t-dt);
    bool up=input_pressed(in,SDL_SCANCODE_UP),down=input_pressed(in,SDL_SCANCODE_DOWN),left=input_pressed(in,SDL_SCANCODE_LEFT),right=input_pressed(in,SDL_SCANCODE_RIGHT),ok=input_pressed(in,SDL_SCANCODE_Z)||input_pressed(in,SDL_SCANCODE_RETURN),back=input_pressed(in,SDL_SCANCODE_X);
    if(m->shop){
        if(back){
            m->open=false;
            m->shop=false;
            return;
        }
        move(m,craft_count(),true,up,down,left,right);
        if(ok){
            const Craft& c=craft_at(m->sel);
            game_menu_say(m,craft_buy_book(p,c)?"BOOK PURCHASED":item_count(p,c.needs)?"ALREADY OWNED":"NOT ENOUGH GOLD");
        }
        return;
    }
    if(m->focus==FOCUS_COMMANDS){
        if(up)m->cmd=(m->cmd+COMMANDS-1)%COMMANDS;
        if(down)m->cmd=(m->cmd+1)%COMMANDS;
        if(back||(ok&&m->cmd==CLOSE)){
            m->open=false;
            return;
        }
        if(ok&&m->cmd==SAVE){
            if(m->save_block)game_menu_say(m,m->save_block);
            else m->save_request=true;
            return;
        }
        if(ok){
            m->focus=FOCUS_LIST;
            m->sel=0;
        }
        return;
    }
    Entry entries[ITEM_COUNT+WEAPON_COUNT];
    int count=m->cmd==MAKE?craft_count():inventory(p,entries);
    if(!count){
        if(back)m->focus=FOCUS_COMMANDS;
        return;
    }
    m->sel=std::min(m->sel,count-1);
    if(m->focus==FOCUS_LIST){
        if(back){
            m->focus=FOCUS_COMMANDS;
            return;
        }
        move(m,count,m->cmd==MAKE,up,down,left,right);
        Action a[3];
        if(ok&&actions(m,p,entries,a)){
            m->focus=FOCUS_ACTIONS;
            m->act=0;
        }
        return;
    }
    if(back){
        m->focus=FOCUS_LIST;
        return;
    }
    Action a[3];
    int n=actions(m,p,entries,a);
    if(!n){
        m->focus=FOCUS_LIST;
        return;
    }
    m->act=std::min(m->act,n-1);
    if(up)m->act=std::max(0,m->act-1);
    if(down)m->act=std::min(n-1,m->act+1);
    if(!ok)return;
    Action& chosen=a[m->act];
    bool done=false;
    if(chosen.ready){
        if(chosen.kind==EQUIP_ACTION)done=craft_equip(p,(WeaponType)entries[m->sel].id);
        else{
            const Craft& c=craft_at(m->sel);
            done=chosen.kind==MAKE_ACTION?craft_make(p,c):chosen.kind==OIL_ACTION?craft_oil(p,c.weapon):craft_echo(p,c.weapon);
        }
    }
    game_menu_say(m,done?"DONE":chosen.why);
}
void game_menu_draw(GameMenu* m,const Player* p,SDL_Renderer* r){
    if(!m->open)return;
    sheets(m,r);
    draw_nes_panel(r,CMD_X,CMD_Y,CMD_W,CMD_H);
    if(m->shop){
        text(r,"BOOKS",CMD_X+12,CMD_Y+12,2,yellow);
        char b[32];
        SDL_snprintf(b,sizeof(b),"GOLD %d",item_count(p,ITEM_GOLD));
        text(r,b,CMD_X+12,CMD_Y+42,2);
    }
    else for(int i=0;i<COMMANDS;i++){
        // Yellow where the player is, grey where they were.
        bool here=i==m->cmd&&m->focus==FOCUS_COMMANDS;
        SDL_Color c=here?yellow:white;
        draw_text(r,commands[i],CMD_X+28,CMD_Y+12+i*24,2,c.r,c.g,c.b);
        if(i==m->cmd)text(r,GLYPH_CURSOR,CMD_X+10,CMD_Y+12+i*24,2,here?yellow:grey);
    }
    draw_nes_panel(r,PRE_X,PRE_Y,PRE_W,PRE_H);
    text(r,"Z: CHOOSE",PRE_X+10,PRE_Y+PRE_H-52,2,grey);
    text(r,"X: BACK",PRE_X+10,PRE_Y+PRE_H-28,2,grey);
    draw_nes_panel(r,LST_X,LST_Y,LST_W,LST_H);
    Entry entries[ITEM_COUNT+WEAPON_COUNT];
    int n=(m->shop||m->cmd==MAKE)?craft_count():m->cmd==ITEMS?inventory(p,entries):0;
    if(m->cmd==SAVE&&!m->shop){
        wrapped(r,m->save_block?m->save_block:"Z: SAVE THE GAME",LST_X+15,LST_Y+20,LST_W-30,3);
        if(m->note_t>0&&m->note)fitted(r,m->note,LST_X+14,LST_Y+LST_H-28,LST_W-28,2,yellow);
        return;
    }
    if(m->cmd==CLOSE&&!m->shop)return;
    if(!n){
        text(r,"NOTHING YET",LST_X+16,LST_Y+16,2,grey);
        return;
    }
    int selected=std::min(m->sel,n-1);
    bool grouped=m->shop||m->cmd==MAKE;
    // One entry of the list in its cell: x is the column's left edge.
    auto cell=[&](int i,int x,int y){
        char line[128],quantity[32] = {  };
        SDL_Color c=white;
        if(grouped){
            const Craft& cr=craft_at(i);
            SDL_strlcpy(line,m->shop?item_name(cr.needs):craft_name(cr),sizeof(line));
            if(m->shop)SDL_snprintf(quantity,sizeof(quantity),item_count(p,cr.needs)?"OWNED":"%d G",cr.price);
            if(!(m->shop?item_count(p,ITEM_GOLD)>=cr.price&&!item_count(p,cr.needs):craft_ready(p,cr)))c=grey;
        }
        else if(entries[i].weapon){
            SDL_strlcpy(line,weapon_name((WeaponType)entries[i].id),sizeof(line));
            if(p->equipped==entries[i].id)SDL_strlcpy(quantity,"IN HAND",sizeof(quantity));
        }
        else{
            SDL_strlcpy(line,item_name((Item)entries[i].id),sizeof(line));
            SDL_snprintf(quantity,sizeof(quantity),"x%d",item_count(p,(Item)entries[i].id));
        }
        bool here=i==selected&&(m->shop||m->focus==FOCUS_LIST);
        if(i==selected&&(m->shop||m->focus!=FOCUS_COMMANDS))text(r,GLYPH_CURSOR,x,y+4,2,here?yellow:grey);
        int qw=text_width(quantity,2);
        fitted(r,line,x+16,y+4,col_w-28-qw,2,here?yellow:c);
        text(r,quantity,x+col_w-8-qw,y+4,2,c);
    };
    // The cursor's column, when it is longer than the box: the speech box's
    // blinking arrow, at the column's right under its last row.
    auto more=[&](int x,bool longer){
        if(longer&&(SDL_GetTicks()/300)%2==0)
            text(r,GLYPH_MORE,x+col_w-8-text_width(GLYPH_MORE,2),divider-16,2);
    };
    if(grouped){
        int sel_col,sel_row;
        place(selected,&sel_col,&sel_row);
        for(int col=0;col<2;col++){
            int list[64],len=column(col,list),x=LST_X+12+col*col_w;
            int top=col==sel_col?std::max(0,sel_row-rows+1):0;
            for(int k=top;k<len&&k<top+rows;k++)cell(list[k],x,LST_Y+12+(k-top)*row_height);
            more(x,col==sel_col&&len>rows);
        }
    }
    else{
        int top=std::max(0,selected/2-rows+1);
        for(int i=top*2;i<n&&i<(top+rows)*2;i++)cell(i,LST_X+12+(i%2)*col_w,LST_Y+12+(i/2-top)*row_height);
        int col=selected%2;
        more(LST_X+12+col*col_w,(n+1-col)/2>rows);
    }
    fc_draw_color(r,252,252,252,255);
    SDL_Rect rule = { LST_X+8,divider,LST_W-16,2 };
    SDL_RenderFillRect(r,&rule);
    if(m->shop||m->cmd==MAKE){
        const Craft& c=craft_at(selected);
        fitted(r,craft_name(c),LST_X+14,218,LST_W-28,2,white);
        if(c.is_weapon)game_menu_draw_weapon(m,r,c.weapon,p->owned[c.weapon]?p->arsenal[c.weapon].material:MAT_STONE,PRE_X+24,PRE_Y+28,64);
        else icon(m,r,c.item,PRE_X+24,PRE_Y+28,64);
        Recipe recipe;
        bool requires_book = m->shop;
        if(m->shop){
            char b[96];
            SDL_snprintf(b,sizeof(b),"BOOK PRICE: %d GOLD",c.price);
            text(r,b,LST_X+14,250,2,yellow);
            text(r,item_count(p,c.needs)?"ALREADY OWNED":"Z: BUY BOOK",LST_X+14,274,2);
            recipe=craft_recipe(p,c,c.is_weapon?MAT_STONE:-1);
        }
        else{
            Action a[3];
            int na=actions(m,p,entries,a);
            for(int i=0;i<na;i++){
                if(m->focus==FOCUS_ACTIONS&&m->act==i)text(r,GLYPH_CURSOR,LST_X+12,250+i*24,2,yellow);
                fitted(r,a[i].label,LST_X+28,250+i*24,LST_W-44,2,a[i].ready?white:grey);
            }
            int ai=m->focus==FOCUS_ACTIONS?std::min(m->act,na-1):0;
            requires_book = a[ai].kind == MAKE_ACTION;
            recipe=a[ai].kind==OIL_ACTION?oil_recipe(p->arsenal[c.weapon]):a[ai].kind==ECHO_ACTION?echo_recipe(p->arsenal[c.weapon]):craft_recipe(p,c,a[ai].ore);
        }
        char b[128];
        SDL_snprintf(b,sizeof(b),"%s: %s (KEPT)",item_count(p,c.needs)?"BOOK OWNED":"NEED BOOK",item_name(c.needs));
        if (requires_book) fitted(r,b,LST_X+14,cost_y-24,LST_W-28,2,item_count(p,c.needs)?white:grey);
        cost(m,p,r,recipe);
    }
    else{
        Entry e=entries[selected];
        if(e.weapon){
            game_menu_draw_weapon(m,r,(WeaponType)e.id,p->arsenal[e.id].material,PRE_X+24,PRE_Y+28,64);
            text(r,weapon_name((WeaponType)e.id),LST_X+14,218,2);
            text(r,p->equipped==e.id?"IN HAND":"Z: CHOOSE, THEN EQUIP",LST_X+14,254,2);
        }
        else{
            Item it=(Item)e.id;
            icon(m,r,it,PRE_X+24,PRE_Y+28,64);
            fitted(r,item_name(it),LST_X+14,218,LST_W-28,2,white);
            if(const char* desc=item_description(it)){
                wrapped(r,desc,LST_X+14,250,LST_W-28,3);
                if((it>=ITEM_BAND_AID&&it<=ITEM_BINOCULARS)||it==ITEM_LAVA_CHARM||it==ITEM_PLAGUE_RESIDUE)text(r,"NOT USABLE YET",LST_X+14,314,2,grey);
            }
            else{
                text(r,"USED FOR:",LST_X+14,250,2,grey);
                const char* uses[24];
                int nu=item_uses(it,uses,24);
                char b[512] = {  };
                for(int i=0;i<nu;i++){
                    if(i)SDL_strlcat(b,", ",sizeof(b));
                    SDL_strlcat(b,uses[i],sizeof(b));
                }
                wrapped(r,nu?b:"NOTHING YET",LST_X+14,273,LST_W-28,3);
            }
            // Gives way to the answer to Z, which takes its place.
            const char* src=item_source(it);
            if(src&&!(m->note_t>0&&m->note))wrapped(r,src,LST_X+14,365,LST_W-28,2,grey);
        }
    }
    if(m->note_t>0&&m->note)fitted(r,m->note,LST_X+14,grouped?cost_y-50:LST_Y+LST_H-28,LST_W-28,2,yellow);
}
void game_menu_draw_item(GameMenu* m,SDL_Renderer* r,int item,int x,int y,int size){
    sheets(m,r);
    icon(m,r,(Item)item,x,y,size);
}
void game_menu_draw_weapon(GameMenu* m,SDL_Renderer* r,WeaponType w,Material ore,int x,int y,int size,Uint8 shade){
    sheets(m,r);
    if(!m->weapons)return;
    SDL_SetTextureColorMod(m->weapons,shade,shade,shade);
    SDL_Rect a = { (int)w*16,(int)ore*16,16,16 }
    ,b = { x,y,size,size };
    SDL_RenderCopy(r,m->weapons,&a,&b);
    SDL_SetTextureColorMod(m->weapons,255,255,255);
}
const char* game_menu_ore_name(Material m){
    return m==MAT_REALITY_SHARD?"SHARD":item_name(ore_item(m));
}
void game_menu_free(GameMenu* m){
    if(m->items)SDL_DestroyTexture(m->items);
    if(m->weapons)SDL_DestroyTexture(m->weapons);
    m->items=m->weapons=nullptr;
    m->tried=false;
}
