// Approved crafting, capped loot, save migration, and menu rendering checks.
// Run from the repository root: build.bat craftcheck && craftcheck.exe
#include "crafting.h"
#include "loot.h"
#include "battle.h"
#include "game_menu.h"
#include "legacy_player_v2.h"
#include "save.h"
#include "dungeon.h"
#include "story.h"
#include <SDL2/SDL_image.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <filesystem>
#include <set>
#include <algorithm>

static Player fresh_player(){
 Player p={};p.stats.hp=p.stats.max_hp=1000;p.level=1;
 for(int w=0;w<WEAPON_COUNT;w++)p.arsenal[w]=Weapon{(WeaponType)w,MAT_STONE};
 return p;
}
static const Craft& result(Item item){for(int i=0;i<craft_count();i++)if(!craft_at(i).is_weapon&&craft_at(i).item==item)return craft_at(i);assert(false);return craft_at(0);}
static const Craft& weapon(WeaponType w){for(int i=0;i<craft_count();i++)if(craft_at(i).is_weapon&&craft_at(i).weapon==w)return craft_at(i);assert(false);return craft_at(0);}
static void fill(Player& p,const Recipe& r){for(int i=0;i<r.n;i++)item_slot(&p,r.c[i].item)=r.c[i].amount;}
static void catalog_checks(){
 assert(craft_count()==23);assert(ITEM_COUNT>64);std::set<int> books;
 for(int i=0;i<craft_count();i++){
  const Craft& c=craft_at(i);assert(c.n>0&&c.n<=4);assert(item_is_book(c.needs));assert(books.insert(c.needs).second);assert(c.price>0&&c.price<=500);
  if(c.is_weapon&&c.weapon==WEAPON_SCYTHE)assert(c.price==500);else assert(c.price<500);
  Player p=fresh_player();Recipe r=craft_recipe(&p,c,MAT_STONE);fill(p,r);
  assert(!craft_ready(&p,c));assert(!craft_make(&p,c));
  item_slot(&p,ITEM_GOLD)=c.price-1;assert(!craft_buy_book(&p,c));assert(item_count(&p,ITEM_GOLD)==c.price-1);
  item_slot(&p,ITEM_GOLD)=c.price;assert(craft_buy_book(&p,c));assert(item_count(&p,ITEM_GOLD)==0);assert(item_found(&p,c.needs));
  item_slot(&p,ITEM_GOLD)=999;assert(!craft_buy_book(&p,c));assert(item_count(&p,ITEM_GOLD)==999);
  assert(craft_ready(&p,c));int hp=p.stats.hp;assert(craft_make(&p,c));assert(p.stats.hp==hp);assert(item_count(&p,c.needs)==1);
  for(int j=0;j<r.n;j++)assert(item_count(&p,r.c[j].item)==0);
  if(c.is_weapon)assert(p.owned[c.weapon]&&p.arsenal[c.weapon].material==MAT_STONE);
  else {assert(item_count(&p,c.item)==1);item_slot(&p,c.item)=c.max;fill(p,r);assert(!craft_ready(&p,c));assert(!craft_make(&p,c));}
 }
 assert(result(ITEM_SWIFT_BOOTS).n==4);assert(result(ITEM_SAIL).in[0].amount==6);assert(result(ITEM_BINOCULARS).in[0].amount==2);
 assert(item_limit(ITEM_MEDKIT)==999&&item_limit(ITEM_ESCAPE_CHARM)==1&&item_limit(ITEM_SLEEPING_BAG)==0);
 assert(!strcmp(item_name(ITEM_ESSENCE),"SPIRIT ESSENCE"));assert(!strcmp(item_name(ITEM_WHITE_FUR),"FUR"));
 Player p=fresh_player();const Craft& c=weapon(WEAPON_SCYTHE);item_slot(&p,c.needs)=1;fill(p,craft_recipe(&p,c,MAT_STONE));assert(craft_make(&p,c));
 p.arsenal[c.weapon].oil=3;p.arsenal[c.weapon].echo=1;fill(p,craft_recipe(&p,c,MAT_BRONZE));assert(craft_make(&p,c));
 assert(p.arsenal[c.weapon].material==MAT_BRONZE&&p.arsenal[c.weapon].oil==3&&p.arsenal[c.weapon].echo==1);assert(item_count(&p,ITEM_REAPERS_EDGE)==0);
 assert(craft_best_ore(&p,c)==-1);item_slot(&p,ITEM_OILBLOOM)=99;while(p.arsenal[c.weapon].oil<WEAPON_OIL_MAX)assert(craft_oil(&p,c.weapon));assert(!craft_oil(&p,c.weapon));
 item_slot(&p,ITEM_ESSENCE)=4;assert(craft_echo(&p,c.weapon));assert(!craft_echo(&p,c.weapon));
 for(int i=0;i<ITEM_COUNT;i++){item_mark_found(&p,(Item)i);assert(item_found(&p,(Item)i));assert(item_icon((Item)i)>=0&&item_icon((Item)i)<LEGACY_ITEM_COUNT);}
 puts("recipes/books: 23 recipes, caps, costs, upgrades and discovery checked");
}
static void loot_checks(){
 LootRolls rolls={};for(int& r:rolls.ore)r=9999;int out[ITEM_COUNT];
 const int unassigned[]={4,19,23,26,40,47,54,65,76,82,91,92,94,100};
 for(int enemy:unassigned){battle_loot(enemy,0,rolls,out);for(int v:out)assert(v==0);}
 for(int enemy=0;enemy<ENEMY_COUNT;enemy++)for(int count:{0,1,5,6,1024,100000}){
  int base[ITEM_COUNT];battle_loot(enemy,0,rolls,base);battle_loot(enemy,count,rolls,out);
  assert(out[ITEM_WOOD]-base[ITEM_WOOD]+out[ITEM_STONE]-base[ITEM_STONE]==std::min(6,count));
  for(int i=0;i<ITEM_COUNT;i++)if(i!=ITEM_WOOD&&i!=ITEM_STONE)assert(out[i]==base[i]);
 }
 battle_loot(51,1024,rolls,out);assert(out[ITEM_FLOWER]==1&&out[ITEM_OILBLOOM]==1&&out[ITEM_WATER_RING]==1);
 battle_loot(62,1024,rolls,out);assert(out[ITEM_WHITE_FUR]==1&&out[ITEM_BONE]==1&&out[ITEM_HIDE]==0);
 for(int e:{7,97}){battle_loot(e,1024,rolls,out);assert(out[ITEM_EVERLASTING_EMBER]==1&&out[ITEM_LAVA_CHARM]==1);}
 const int chance[]={10000,4000,2000,1000,500,200,50};
 for(int e:{31,33}){
  int totals[MAT_COUNT]={};for(int r=0;r<10000;r++){for(int& value:rolls.ore)value=r;battle_loot(e,0,rolls,out);for(int m=0;m<MAT_COUNT;m++)totals[m]+=out[ore_item((Material)m)];}
  for(int m=0;m<MAT_COUNT;m++)assert(totals[m]==chance[m]);
  for(int m=1;m<MAT_COUNT;m++){
   for(int& v:rolls.ore)v=9999;rolls.ore[m]=chance[m]-1;battle_loot(e,0,rolls,out);assert(out[ore_item((Material)m)]==1);
   rolls.ore[m]++;battle_loot(e,0,rolls,out);assert(out[ore_item((Material)m)]==0);
  }
 }
 for(int& r:rolls.ore)r=0;for(int e=0;e<ENEMY_COUNT;e++)if(e!=31&&e!=33){battle_loot(e,100000,rolls,out);for(int m=1;m<MAT_COUNT;m++)assert(out[ore_item((Material)m)]==0);}
 Player p=fresh_player();int actual[ITEM_COUNT];bool found[ITEM_COUNT];std::fill(out,out+ITEM_COUNT,0);
 item_slot(&p,ITEM_HIDE)=998;out[ITEM_HIDE]=6;item_slot(&p,ITEM_LAVA_CHARM)=999;out[ITEM_LAVA_CHARM]=1;out[ITEM_EYE_LENS]=1;
 credit_loot(&p,out,actual,found);assert(actual[ITEM_HIDE]==1&&actual[ITEM_LAVA_CHARM]==0&&actual[ITEM_EYE_LENS]==1&&found[ITEM_EYE_LENS]);assert(!found[ITEM_LAVA_CHARM]);
 Input in={};p=fresh_player();p.owned[WEAPON_KNIFE]=true;BattleScene scene(&p,7);const_cast<Enemy*>(scene.hud_enemy())->take_damage(1e9f);
 for(int i=0;i<30&&scene.get_phase()!=BATTLE_PHASE_VICTORY;i++)scene.update(&in,0.1f);
 assert(scene.get_phase()==BATTLE_PHASE_VICTORY);assert(item_count(&p,ITEM_LAVA_CHARM)==1&&item_count(&p,ITEM_EVERLASTING_EMBER)==1);
 for(int i=0;i<30;i++)scene.update(&in,0.1f);assert(item_count(&p,ITEM_LAVA_CHARM)==1);
 puts("loot: all 101 enemies, cancellation caps, ore thresholds, saturation and victory integration checked");
}

template<class P>struct SaveFixture{char magic[4];unsigned version,player_size,seed;float x,y;P player;uint8_t explored[EXPLORE_H][EXPLORE_W];uint8_t landmarks[MAX_LANDMARKS/8];DungeonChestRecord chests[MAX_DUNGEON_CHEST_RECORDS];StoryFlags story;};
static void save_checks(){
 namespace fs=std::filesystem;fs::path original=fs::current_path();fs::create_directories("build_tmp/crafting_qa/saves");fs::current_path("build_tmp/crafting_qa/saves");
 static uint8_t explored[EXPLORE_H][EXPLORE_W]={};Player p=fresh_player();item_slot(&p,ITEM_BINOCULARS)=1;item_mark_found(&p,ITEM_BINOCULARS);item_slot(&p,ITEM_ENCHANTED_WOOD)=17;explored[1][2]=1;
 assert(save_write(42,12,34,p,explored));Player got={};unsigned seed;float x,y;assert(save_read(&seed,&x,&y,&got,explored));assert(seed==42&&x==12&&y==34&&item_count(&got,ITEM_ENCHANTED_WOOD)==17&&item_found(&got,ITEM_BINOCULARS));
 static SaveFixture<LegacyPlayerV2> old={};memcpy(old.magic,"FCC1",4);old.version=2;old.player_size=sizeof(LegacyPlayerV2);old.seed=123;old.x=7;old.y=9;
 memcpy(&old.player,&p,sizeof(LegacyPlayerV2));old.player.parts[PART_FUR]=6;old.player.sail=1;old.player.books[2]=1;old.explored[3][4]=1;old.landmarks[0]=5;old.story=*story_flags();
 const size_t sizes[]={sizeof(old),offsetof(SaveFixture<LegacyPlayerV2>,story),(offsetof(SaveFixture<LegacyPlayerV2>,landmarks)+MAX_LANDMARKS/8+3)&~(size_t)3,(offsetof(SaveFixture<LegacyPlayerV2>,landmarks)+3)&~(size_t)3};
 for(size_t size:sizes){FILE* f=fopen("save.dat","wb");assert(f);assert(fwrite(&old,1,size,f)==size);fclose(f);memset(&got,0,sizeof(got));assert(save_read(&seed,&x,&y,&got,explored));assert(seed==123&&x==7&&y==9&&got.sail==1&&got.books[2]==1&&item_count(&got,ITEM_WHITE_FUR)==6&&explored[3][4]);assert(item_count(&got,ITEM_BINOCULARS)==0&&got.found_extra[0]==0);}
 FILE* f=fopen("save.dat","wb");fwrite(&old,1,12,f);fclose(f);assert(!save_read(&seed,&x,&y,&got,explored));fs::current_path(original);
 puts("saves: V3 round trip, all four V2 lengths, expanded inventory and truncation rejection checked");
}
static void render_checks(){
 namespace fs=std::filesystem;fs::create_directories("build_tmp/crafting_qa");
 SDL_Surface* surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);assert(surface);SDL_Renderer* renderer=SDL_CreateSoftwareRenderer(surface);assert(renderer);
 Player p=fresh_player();p.owned[WEAPON_KNIFE]=true;for(int i=0;i<ITEM_COUNT;i++)item_slot(&p,(Item)i)=std::min(99,item_limit((Item)i));
 GameMenu menu;game_menu_toggle(&menu);menu.cmd=1;menu.focus=FOCUS_ACTIONS;
 auto capture=[&](const char* file){SDL_SetRenderDrawColor(renderer,24,32,24,255);SDL_RenderClear(renderer);game_menu_draw(&menu,&p,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,file)==0);};
 for(int i=0;i<craft_count();i++){menu.sel=i;capture("build_tmp/crafting_qa/recipe.png");if(!craft_at(i).is_weapon&&craft_at(i).item==ITEM_SWIFT_BOOTS)capture("build_tmp/crafting_qa/swift_boots.png");}
 game_menu_open_shop(&menu);menu.sel=craft_count()-1;capture("build_tmp/crafting_qa/scythe_shop.png");
 int gold=item_count(&p,ITEM_GOLD);Input in={};in.keys[SDL_SCANCODE_Z]=KEY_PRESSED;game_menu_update(&menu,&p,&in,0.1f);assert(item_count(&p,ITEM_GOLD)==gold);
 game_menu_toggle(&menu);game_menu_toggle(&menu);menu.cmd=0;menu.focus=FOCUS_LIST;menu.sel=WEAPON_COUNT+ITEM_COUNT-3;capture("build_tmp/crafting_qa/inventory.png");
 Player unprepared=fresh_player();GameMenu locked;game_menu_toggle(&locked);locked.cmd=1;locked.focus=FOCUS_ACTIONS;locked.sel=craft_count()-1;SDL_RenderClear(renderer);game_menu_draw(&locked,&unprepared,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/locked_scythe.png")==0);
 Player buyer=fresh_player();item_slot(&buyer,ITEM_GOLD)=999;GameMenu store;game_menu_open_shop(&store);store.sel=craft_count()-1;
 Input buy={};game_menu_update(&store,&buyer,&buy,0.1f);assert(item_count(&buyer,ITEM_GOLD)==999);buy.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 game_menu_update(&store,&buyer,&buy,0.1f);assert(item_count(&buyer,ITEM_GOLD)==499&&item_count(&buyer,ITEM_SCYTHE_BOOK)==1);
 game_menu_update(&store,&buyer,&buy,0.1f);assert(item_count(&buyer,ITEM_GOLD)==499);
 Player hero=fresh_player();hero.owned[WEAPON_KNIFE]=true;Input empty={};
 {BattleScene victory(&hero,51);for(int i=0;i<40;i++)victory.update(&empty,0.1f);const_cast<Enemy*>(victory.hud_enemy())->take_damage(1e9f);
  for(int i=0;i<30;i++)victory.update(&empty,0.1f);assert(victory.get_phase()==BATTLE_PHASE_VICTORY);victory.draw(renderer,nullptr);SDL_RenderPresent(renderer);
  assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/victory.png")==0);
 }
 game_menu_free(&store);game_menu_free(&locked);game_menu_free(&menu);SDL_DestroyRenderer(renderer);SDL_FreeSurface(surface);
 puts("menus: every recipe, four ingredients, book shop, full inventory and locked recipe rendered");
}
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SDL_setenv("SDL_VIDEODRIVER","dummy",1);assert(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_TIMER)==0);
 catalog_checks();loot_checks();save_checks();render_checks();
 for(int w=0;w<WEAPON_COUNT;w++){ProjectileProfile p=weapon_profile((WeaponType)w);assert(fabsf(faster_fire_rate(p.fire_rate,0)-p.fire_rate)<0.001f);assert(fabsf(faster_fire_rate(p.fire_rate,WEAPON_OIL_MAX)-TOUHOU_FIRE_RATE)<0.001f);assert(fabsf(faster_fire_rate(p.fire_rate,WEAPON_OIL_MAX)*faster_damage(p.fire_rate,p.damage,WEAPON_OIL_MAX)/(p.fire_rate*p.damage)-FASTER_DPS_AT_MAX)<0.001f);}
 SDL_Quit();puts("craftcheck: ok");return 0;
}