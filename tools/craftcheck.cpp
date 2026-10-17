// Approved crafting, capped loot, save migration, and menu rendering checks.
// Run from the repository root: build.bat craftcheck && craftcheck.exe
#include "crafting.h"
#include "loot.h"
#include "battle.h"
#include "game_menu.h"
#include "interior.h"
#include "legacy_player_v2.h"
#include "legacy_player_v3.h"
#include "legacy_player_v4.h"
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
 static uint8_t explored[EXPLORE_H][EXPLORE_W]={};Player p=fresh_player();p.poisoned=1;p.poison_timer=0.75f;item_slot(&p,ITEM_SWIFT_BOOTS)=1;p.footwear=1;item_slot(&p,ITEM_BINOCULARS)=1;item_mark_found(&p,ITEM_BINOCULARS);item_slot(&p,ITEM_ENCHANTED_WOOD)=17;explored[1][2]=1;
 assert(save_write(42,12,34,p,explored));Player got={};unsigned seed;float x,y;assert(save_read(&seed,&x,&y,&got,explored));assert(got.poisoned&&got.poison_timer==0.75f&&got.footwear);assert(seed==42&&x==12&&y==34&&item_count(&got,ITEM_ENCHANTED_WOOD)==17&&item_found(&got,ITEM_BINOCULARS));
 static SaveFixture<LegacyPlayerV2> old={};memcpy(old.magic,"FCC1",4);old.version=2;old.player_size=sizeof(LegacyPlayerV2);old.seed=123;old.x=7;old.y=9;
 memcpy(&old.player,&p,sizeof(LegacyPlayerV2));old.player.parts[PART_FUR]=6;old.player.sail=1;old.player.books[2]=1;old.explored[3][4]=1;old.landmarks[0]=5;old.story=*story_flags();
 const size_t sizes[]={sizeof(old),offsetof(SaveFixture<LegacyPlayerV2>,story),(offsetof(SaveFixture<LegacyPlayerV2>,landmarks)+MAX_LANDMARKS/8+3)&~(size_t)3,(offsetof(SaveFixture<LegacyPlayerV2>,landmarks)+3)&~(size_t)3};
 for(size_t size:sizes){FILE* f=fopen("save.dat","wb");assert(f);assert(fwrite(&old,1,size,f)==size);fclose(f);memset(&got,0,sizeof(got));assert(save_read(&seed,&x,&y,&got,explored));assert(seed==123&&x==7&&y==9&&got.sail==1&&got.books[2]==1&&item_count(&got,ITEM_WHITE_FUR)==6&&explored[3][4]);assert(item_count(&got,ITEM_BINOCULARS)==0&&got.found_extra[0]==0);}
 static SaveFixture<LegacyPlayerV3> v3={};memcpy(v3.magic,"FCC1",4);v3.version=3;v3.player_size=sizeof(LegacyPlayerV3);v3.seed=321;v3.x=12;v3.y=34;memcpy(&v3.player,&p,sizeof(v3.player));v3.explored[1][2]=1;v3.landmarks[0]=7;v3.story=*story_flags();
 FILE* f3=fopen("save.dat","wb");assert(f3);assert(fwrite(&v3,1,sizeof(v3),f3)==sizeof(v3));fclose(f3);
 assert(save_read(&seed,&x,&y,&got,explored));assert(seed==321&&x==12&&y==34&&!got.poisoned&&got.poison_timer==0&&item_count(&got,ITEM_ENCHANTED_WOOD)==17&&item_found(&got,ITEM_BINOCULARS)&&explored[1][2]&&tilemap_landmarks_opened()[0]==7);
 static SaveFixture<LegacyPlayerV4> v4={};memcpy(v4.magic,"FCC1",4);v4.version=4;v4.player_size=sizeof(LegacyPlayerV4);v4.seed=456;memcpy(&v4.player,&p,sizeof(v4.player));
 FILE* f4=fopen("save.dat","wb");assert(f4);assert(fwrite(&v4,1,sizeof(v4),f4)==sizeof(v4));fclose(f4);
 assert(save_read(&seed,&x,&y,&got,explored));assert(seed==456&&got.poisoned&&got.poison_timer==0.75f&&got.footwear&&item_count(&got,ITEM_SWIFT_BOOTS)==1);
 got.footwear=0;assert(save_write(seed,x,y,got,explored));assert(save_read(&seed,&x,&y,&got,explored));assert(!got.footwear&&item_count(&got,ITEM_SWIFT_BOOTS)==1);
 item_slot(&got,ITEM_DIVING_FINS)=1;assert(item_equip_footwear(&got,ITEM_DIVING_FINS,true));assert(save_write(seed,x,y,got,explored));assert(save_read(&seed,&x,&y,&got,explored));assert(got.footwear==FOOTWEAR_DIVING_FINS&&item_footwear_equipped(&got,ITEM_DIVING_FINS)&&!item_footwear_equipped(&got,ITEM_SWIFT_BOOTS));
 FILE* f=fopen("save.dat","wb");fwrite(&old,1,12,f);fclose(f);assert(!save_read(&seed,&x,&y,&got,explored));fs::current_path(original);
 puts("saves: V5 equipped/unequipped round trip, V4/V3 migration, all four V2 lengths and truncation rejection checked");
}
static void swift_boots_checks(){
 Player p=fresh_player();float speed,anim;Input in={};
 player_gait(&in,&speed,&anim,&p);assert(speed==120&&fabsf(anim-0.2f)<0.001f);
 item_slot(&p,ITEM_SWIFT_BOOTS)=1;
 player_gait(&in,&speed,&anim,&p);assert(speed==120);assert(item_equip_swift_boots(&p,true));
 player_gait(&in,&speed,&anim,&p);assert(speed==180&&fabsf(anim-0.2f/1.5f)<0.001f);
 // Vehicle and swimming callers omit the player to preserve their gait.
 player_gait(&in,&speed,&anim);assert(speed==120&&fabsf(anim-0.2f)<0.001f);
 in.keys[SDL_SCANCODE_LSHIFT]=KEY_HELD;
 player_gait(&in,&speed,&anim,&p);assert(speed==360);
 in.keys[SDL_SCANCODE_LCTRL]=KEY_HELD;
 player_gait(&in,&speed,&anim,&p);assert(speed==60&&fabsf(anim-0.3f)<0.001f);
 item_slot(&p,ITEM_SWIFT_BOOTS)=2;in={};player_gait(&in,&speed,&anim,&p);assert(speed==180);
 item_slot(&p,ITEM_SWIFT_BOOTS)=1;
 // Exercise actual room movement and removal of the equipment bonus.
 InteriorMap room={};for(auto& row:room.tiles)for(auto& tile:row)tile=INT_FLOOR;
 InteriorPlayer ip={};ip.x=100;ip.y=100;in.keys[SDL_SCANCODE_RIGHT]=KEY_HELD;
 interior_player_update(&ip,&p,&in,0.1f,&room);assert(fabsf(ip.x-118)<0.001f);
 assert(item_equip_swift_boots(&p,false));ip.x=100;
 interior_player_update(&ip,&p,&in,0.1f,&room);assert(fabsf(ip.x-112)<0.001f);
 assert(item_equip_swift_boots(&p,true));ip.x=100;in.keys[SDL_SCANCODE_LSHIFT]=KEY_HELD;
 interior_player_update(&ip,&p,&in,0.1f,&room);assert(fabsf(ip.x-136)<0.001f);
 assert(item_count(&p,ITEM_SWIFT_BOOTS)==1);
 // Inventory exposes a repeatable equip/unequip action without spending boots.
 GameMenu menu;game_menu_toggle(&menu);menu.focus=FOCUS_LIST;Input use={};use.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 item_slot(&p,ITEM_SWIFT_BOOTS)=1;game_menu_update(&menu,&p,&use,0.1f);assert(menu.focus==FOCUS_ACTIONS);
 game_menu_update(&menu,&p,&use,0.1f);assert(!p.footwear);
 game_menu_update(&menu,&p,&use,0.1f);assert(p.footwear&&item_count(&p,ITEM_SWIFT_BOOTS)==1);
 item_slot(&p,ITEM_SWIFT_BOOTS)=0;player_gait(&in,&speed,&anim,&p);assert(speed==PLAYER_RUN_SPEED);assert(!item_equip_swift_boots(&p,true));
 assert(item_equip_swift_boots(&p,false));game_menu_free(&menu);
 puts("swift boots: equip/unequip, walk/run boost, crouch priority, no stacking and room movement checked");
}
static void diving_fins_checks(){
 Player p=fresh_player();Input in={};float speed,anim;
 assert(player_swim_speed(&p,&in)==90);assert(!item_equip_footwear(&p,ITEM_DIVING_FINS,true));
 item_slot(&p,ITEM_DIVING_FINS)=1;item_slot(&p,ITEM_SWIFT_BOOTS)=1;
 assert(player_swim_speed(&p,&in)==90);assert(item_equip_footwear(&p,ITEM_DIVING_FINS,true));
 assert(player_swim_speed(&p,&in)==135);player_gait(&in,&speed,&anim,&p);assert(speed==120);
 in.keys[SDL_SCANCODE_LSHIFT]=KEY_HELD;assert(player_swim_speed(&p,&in)==270);
 assert(item_equip_swift_boots(&p,true));assert(!item_footwear_equipped(&p,ITEM_DIVING_FINS));assert(player_swim_speed(&p,&in)==180);
 player_gait(&in,&speed,&anim,&p);assert(speed==360);
 assert(item_equip_footwear(&p,ITEM_DIVING_FINS,true));assert(!item_footwear_equipped(&p,ITEM_SWIFT_BOOTS));
 assert(item_equip_swift_boots(&p,false));assert(item_footwear_equipped(&p,ITEM_DIVING_FINS));
 assert(item_equip_footwear(&p,ITEM_DIVING_FINS,false));in={};assert(player_swim_speed(&p,&in)==90);
 // Actual swimming update: same input and easing, fins travel 50% farther.
 static DungeonMap water={};water.type=DUNGEON_ENT_OASIS;
 Camera cam={};cam.zoom=1;cam.screen_w=640;cam.screen_h=480;
 Input right={};right.keys[SDL_SCANCODE_RIGHT]=KEY_HELD;
 DungeonPlayer normal={};normal.x=normal.y=200;
 dungeon_player_update(&normal,&p,&right,0.05f,&water,&cam,true);
 assert(item_equip_footwear(&p,ITEM_DIVING_FINS,true));DungeonPlayer faster={};faster.x=faster.y=200;
 dungeon_player_update(&faster,&p,&right,0.05f,&water,&cam,true);
 assert(fabsf((faster.x-200)/(normal.x-200)-1.5f)<0.001f);
 // Inventory-only fins can be equipped and removed without consumption.
 p=fresh_player();item_slot(&p,ITEM_DIVING_FINS)=1;GameMenu m;game_menu_toggle(&m);m.focus=FOCUS_LIST;
 Input use={};use.keys[SDL_SCANCODE_Z]=KEY_PRESSED;game_menu_update(&m,&p,&use,0.1f);game_menu_update(&m,&p,&use,0.1f);
 assert(item_footwear_equipped(&p,ITEM_DIVING_FINS));game_menu_update(&m,&p,&use,0.1f);assert(p.footwear==FOOTWEAR_NONE&&item_count(&p,ITEM_DIVING_FINS)==1);game_menu_free(&m);
 puts("diving fins: swimming boost, one footwear slot, switching, land exclusion, actual swim movement and menu checked");
}
static void poison_checks(){
 Player p=fresh_player();p.stats.hp=60;player_poison_tick(&p,5);assert(p.stats.hp==60);
 p.poisoned=1;player_poison_tick(&p,0.5f);assert(p.stats.hp==60);player_poison_tick(&p,0.5f);assert(p.stats.hp==59);
 player_poison_tick(&p,3);assert(p.stats.hp==56);
 player_poison_tick(&p,1000);assert(p.stats.hp==1&&p.poisoned);
 player_poison_tick(&p,1000);assert(p.stats.hp==1);
 p.stats.hp=0;player_poison_tick(&p,5);assert(p.stats.hp==0);
 p.stats.hp=1;item_slot(&p,ITEM_MEDKIT)=1;assert(item_use_medkit(&p));assert(p.stats.hp==1000&&p.poisoned);player_poison_tick(&p,1);assert(p.stats.hp==999);
 assert(!item_use_antidote(&p));item_slot(&p,ITEM_ANTIDOTE)=2;p.poison_timer=0.75f;
 assert(item_use_antidote(&p));assert(!p.poisoned&&p.poison_timer==0&&p.stats.hp==999&&item_count(&p,ITEM_ANTIDOTE)==1);
 player_poison_tick(&p,5);assert(p.stats.hp==999);assert(!item_use_antidote(&p));assert(item_count(&p,ITEM_ANTIDOTE)==1);
 p=fresh_player();p.poisoned=1;p.stats.hp=1;item_slot(&p,ITEM_ANTIDOTE)=2;
 GameMenu m;game_menu_toggle(&m);m.focus=FOCUS_LIST;Input use={};use.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 game_menu_update(&m,&p,&use,0.1f);assert(m.focus==FOCUS_ACTIONS);
 m.healing_block="EXPLORATION ONLY";game_menu_update(&m,&p,&use,0.1f);assert(p.poisoned&&item_count(&p,ITEM_ANTIDOTE)==2);
 m.healing_block=nullptr;game_menu_update(&m,&p,&use,0.1f);assert(!p.poisoned&&p.stats.hp==1&&item_count(&p,ITEM_ANTIDOTE)==1);
 game_menu_update(&m,&p,&use,0.1f);assert(item_count(&p,ITEM_ANTIDOTE)==1);game_menu_free(&m);
 // The actual battle scene uses the same effect, only once combat is active.
 for(int hp:{60,2}){
  p=fresh_player();p.stats.hp=hp;p.poisoned=1;p.poison_timer=0.95f;p.owned[WEAPON_KNIFE]=true;
  BattleScene battle(&p,7);Input empty={};
  for(int i=0;i<20&&battle.get_phase()!=BATTLE_PHASE_FIGHTING;i++)battle.update(&empty,0.1f);
  assert(battle.hud_hp()==hp);battle.update(&empty,0.1f);
  assert(battle.hud_hp()==hp-1&&p.stats.hp==hp-1&&battle.get_phase()==BATTLE_PHASE_FIGHTING);
  p.poisoned=0;battle.update(&empty,0.1f);assert(battle.hud_hp()==hp-1);
 }
 puts("poison: timed drain, 1 HP floor, healing persistence, Antidote use, menu restrictions and battle effect checked");
}
static void band_aid_checks(){
 Player p=fresh_player();p.stats.max_hp=60;p.stats.hp=40;
 assert(!item_use_band_aid(&p));assert(p.stats.hp==40);
 item_slot(&p,ITEM_BAND_AID)=5;
 assert(item_use_band_aid(&p));assert(p.stats.hp==45&&item_count(&p,ITEM_BAND_AID)==4);
 p.stats.hp=58;assert(item_use_band_aid(&p));assert(p.stats.hp==60&&item_count(&p,ITEM_BAND_AID)==3);
 assert(!item_use_band_aid(&p));assert(item_count(&p,ITEM_BAND_AID)==3);
 p.stats.hp=0;assert(!item_use_band_aid(&p));assert(p.stats.hp==0&&item_count(&p,ITEM_BAND_AID)==3);
 p.stats.hp=40;
 GameMenu m;game_menu_toggle(&m);m.cmd=0;m.focus=FOCUS_LIST;
 Input use={};use.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 game_menu_update(&m,&p,&use,0.1f);assert(m.focus==FOCUS_ACTIONS);
 const char* blocks[]={"EXPLORATION ONLY","BATTLE IS STARTING","TRANSITION IN PROGRESS"};
 for(const char* block:blocks){m.healing_block=block;game_menu_update(&m,&p,&use,0.1f);assert(m.note==block);assert(p.stats.hp==40&&item_count(&p,ITEM_BAND_AID)==3);}
 m.healing_block=nullptr;m.chased=true;
 for(int i=0;i<3;i++)game_menu_update(&m,&p,&use,0.1f);
 assert(p.stats.hp==55&&item_count(&p,ITEM_BAND_AID)==0);
 game_menu_update(&m,&p,&use,0.1f);assert(p.stats.hp==55);
 game_menu_free(&m);
 puts("band-aids: one-bar healing, cap, full/dead/missing inventory, exploration restrictions and depletion checked");
}
static void medkit_checks(){
 Player p=fresh_player();p.stats.max_hp=60;p.stats.hp=1;
 assert(!item_use_medkit(&p));assert(p.stats.hp==1);
 item_slot(&p,ITEM_MEDKIT)=5;
 assert(item_use_medkit(&p));assert(p.stats.hp==60&&item_count(&p,ITEM_MEDKIT)==4);
 assert(!item_use_medkit(&p));assert(item_count(&p,ITEM_MEDKIT)==4);
 p.stats.hp=0;assert(!item_use_medkit(&p));assert(p.stats.hp==0&&item_count(&p,ITEM_MEDKIT)==4);
 p.stats.hp=59;assert(item_use_medkit(&p));assert(p.stats.hp==60&&item_count(&p,ITEM_MEDKIT)==3);
 p.stats.hp=1;
 GameMenu m;game_menu_toggle(&m);m.focus=FOCUS_LIST;
 Input use={};use.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 game_menu_update(&m,&p,&use,0.1f);assert(m.focus==FOCUS_ACTIONS);
 const char* blocks[]={"EXPLORATION ONLY","BATTLE IS STARTING","TRANSITION IN PROGRESS"};
 for(const char* block:blocks){m.healing_block=block;game_menu_update(&m,&p,&use,0.1f);assert(m.note==block);assert(p.stats.hp==1&&item_count(&p,ITEM_MEDKIT)==3);}
 m.healing_block=nullptr;m.chased=true;
 game_menu_update(&m,&p,&use,0.1f);assert(p.stats.hp==60&&item_count(&p,ITEM_MEDKIT)==2);
 game_menu_update(&m,&p,&use,0.1f);assert(p.stats.hp==60&&item_count(&p,ITEM_MEDKIT)==2);
 p.stats.hp=1;item_slot(&p,ITEM_MEDKIT)=1;game_menu_update(&m,&p,&use,0.1f);
 assert(p.stats.hp==60&&item_count(&p,ITEM_MEDKIT)==0);
 p.stats.hp=1;game_menu_update(&m,&p,&use,0.1f);assert(p.stats.hp==1);
 game_menu_free(&m);
 puts("medkits: full recovery, no waste at full HP, no revival, exploration restrictions and depletion checked");
}
static void escape_menu_checks(){
 Player p=fresh_player();item_slot(&p,ITEM_ESCAPE_CHARM)=1;
 GameMenu m;game_menu_toggle(&m);m.cmd=0;m.focus=FOCUS_LIST;
 Input use={};use.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 // With only the charm owned, it is inventory row zero.
 game_menu_update(&m,&p,&use,0.1f);assert(m.focus==FOCUS_ACTIONS);
 const char* blocks[]={"ONLY IN A DUNGEON","NOT IN A FIGHT","BATTLE IS STARTING","TRANSITION IN PROGRESS"};
 for(const char* block:blocks){m.escape_block=block;game_menu_update(&m,&p,&use,0.1f);assert(!m.escape_request);assert(m.note==block);}
 m.escape_block=nullptr;m.chased=true;
 for(int i=0;i<2;i++){game_menu_update(&m,&p,&use,0.1f);assert(m.escape_request);assert(item_count(&p,ITEM_ESCAPE_CHARM)==1);m.escape_request=false;}
 item_slot(&p,ITEM_ESCAPE_CHARM)=0;game_menu_update(&m,&p,&use,0.1f);assert(!m.escape_request);
 game_menu_free(&m);
 puts("escape menu: blocked contexts, pursuit, repeated use and retained charm checked");
}
static void render_checks(){
 namespace fs=std::filesystem;fs::create_directories("build_tmp/crafting_qa");
 SDL_Surface* surface=SDL_CreateRGBSurfaceWithFormat(0,640,480,32,SDL_PIXELFORMAT_RGBA32);assert(surface);SDL_Renderer* renderer=SDL_CreateSoftwareRenderer(surface);assert(renderer);
 Player p=fresh_player();p.owned[WEAPON_KNIFE]=true;for(int i=0;i<ITEM_COUNT;i++)item_slot(&p,(Item)i)=std::min(99,item_limit((Item)i));
 GameMenu menu;game_menu_toggle(&menu);menu.cmd=1;menu.focus=FOCUS_ACTIONS;
 auto capture=[&](const char* file){SDL_SetRenderDrawColor(renderer,24,32,24,255);SDL_RenderClear(renderer);game_menu_draw(&menu,&p,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,file)==0);};
 for(int i=0;i<craft_count();i++){menu.sel=i;capture("build_tmp/crafting_qa/recipe.png");if(!craft_at(i).is_weapon&&craft_at(i).item==ITEM_SWIFT_BOOTS)capture("build_tmp/crafting_qa/swift_boots.png");}
 static const Item scythe_stock[]={ITEM_SCYTHE_BOOK};
 game_menu_open_shop(&menu,scythe_stock,1);assert(menu.sel==craft_count()-1);menu.focus=FOCUS_LIST;capture("build_tmp/crafting_qa/scythe_shop.png");
 int gold=item_count(&p,ITEM_GOLD);Input in={};in.keys[SDL_SCANCODE_Z]=KEY_PRESSED;game_menu_update(&menu,&p,&in,0.1f);assert(item_count(&p,ITEM_GOLD)==gold);
 game_menu_toggle(&menu);game_menu_toggle(&menu);menu.cmd=0;menu.focus=FOCUS_LIST;menu.sel=WEAPON_COUNT+ITEM_COUNT-3;capture("build_tmp/crafting_qa/inventory.png");
 // MAKE navigation skips unknown recipes, keeps Knife, and includes owned books
 // even when their ingredients are missing. Shop navigation remains unfiltered.
 Player novice=fresh_player();GameMenu filtered;game_menu_toggle(&filtered);filtered.cmd=1;filtered.focus=FOCUS_LIST;
 Input nav={};nav.keys[SDL_SCANCODE_DOWN]=KEY_PRESSED;
 game_menu_update(&filtered,&novice,&nav,0.1f);assert(filtered.sel==0);
 nav={};nav.keys[SDL_SCANCODE_RIGHT]=KEY_PRESSED;
 game_menu_update(&filtered,&novice,&nav,0.1f);assert(filtered.sel==0);
 item_slot(&novice,ITEM_ANTIDOTE_BOOK)=1;
 game_menu_update(&filtered,&novice,&nav,0.1f);assert(filtered.sel==4);
 assert(!craft_ready(&novice,craft_at(filtered.sel)));
 nav={};nav.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 game_menu_update(&filtered,&novice,&nav,0.1f);game_menu_update(&filtered,&novice,&nav,0.1f);
 assert(item_count(&novice,ITEM_ANTIDOTE)==0);
 item_slot(&novice,ITEM_ANTIDOTE_BOOK)=0;nav={};game_menu_update(&filtered,&novice,&nav,0.1f);assert(filtered.sel==0);
 game_menu_free(&filtered);
 Player unprepared=fresh_player();item_slot(&unprepared,ITEM_SCYTHE_BOOK)=1;GameMenu locked;game_menu_toggle(&locked);locked.cmd=1;locked.focus=FOCUS_ACTIONS;locked.sel=craft_count()-1;SDL_RenderClear(renderer);game_menu_draw(&locked,&unprepared,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/locked_scythe.png")==0);
 Player buyer=fresh_player();item_slot(&buyer,ITEM_GOLD)=999;GameMenu store;game_menu_open_shop(&store,scythe_stock,1);store.focus=FOCUS_LIST;
 Input buy={};game_menu_update(&store,&buyer,&buy,0.1f);assert(item_count(&buyer,ITEM_GOLD)==999);buy.keys[SDL_SCANCODE_Z]=KEY_PRESSED;
 game_menu_update(&store,&buyer,&buy,0.1f);assert(item_count(&buyer,ITEM_GOLD)==499&&item_count(&buyer,ITEM_SCYTHE_BOOK)==1);
 game_menu_update(&store,&buyer,&buy,0.1f);assert(item_count(&buyer,ITEM_GOLD)==499);
 Player charm_owner=fresh_player();item_slot(&charm_owner,ITEM_ESCAPE_CHARM)=1;GameMenu charm_menu;game_menu_toggle(&charm_menu);charm_menu.focus=FOCUS_ACTIONS;charm_menu.escape_block=nullptr;SDL_RenderClear(renderer);game_menu_draw(&charm_menu,&charm_owner,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/escape_charm.png")==0);game_menu_free(&charm_menu);
 Player patient=fresh_player();patient.stats.hp=50;patient.stats.max_hp=60;item_slot(&patient,ITEM_BAND_AID)=5;
 GameMenu band_menu;game_menu_toggle(&band_menu);band_menu.focus=FOCUS_ACTIONS;SDL_RenderClear(renderer);game_menu_draw(&band_menu,&patient,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/band_aid.png")==0);game_menu_free(&band_menu);
 Player med_patient=fresh_player();med_patient.stats.hp=1;med_patient.stats.max_hp=60;item_slot(&med_patient,ITEM_MEDKIT)=5;
 GameMenu med_menu;game_menu_toggle(&med_menu);med_menu.focus=FOCUS_ACTIONS;SDL_RenderClear(renderer);game_menu_draw(&med_menu,&med_patient,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/medkit.png")==0);game_menu_free(&med_menu);
 Player poisoned_patient=fresh_player();poisoned_patient.poisoned=1;item_slot(&poisoned_patient,ITEM_ANTIDOTE)=5;
 GameMenu antidote_menu;game_menu_toggle(&antidote_menu);antidote_menu.focus=FOCUS_ACTIONS;SDL_RenderClear(renderer);game_menu_draw(&antidote_menu,&poisoned_patient,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/antidote.png")==0);game_menu_free(&antidote_menu);
 Player boot_owner=fresh_player();item_slot(&boot_owner,ITEM_SWIFT_BOOTS)=1;item_equip_swift_boots(&boot_owner,true);
 GameMenu boots_menu;game_menu_toggle(&boots_menu);boots_menu.focus=FOCUS_LIST;SDL_RenderClear(renderer);game_menu_draw(&boots_menu,&boot_owner,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/swift_boots_active.png")==0);game_menu_free(&boots_menu);
 Player fin_owner=fresh_player();item_slot(&fin_owner,ITEM_DIVING_FINS)=1;item_equip_footwear(&fin_owner,ITEM_DIVING_FINS,true);
 GameMenu fin_menu;game_menu_toggle(&fin_menu);fin_menu.focus=FOCUS_ACTIONS;SDL_RenderClear(renderer);game_menu_draw(&fin_menu,&fin_owner,renderer);SDL_RenderPresent(renderer);assert(IMG_SavePNG(surface,"build_tmp/crafting_qa/diving_fins.png")==0);game_menu_free(&fin_menu);
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
 catalog_checks();loot_checks();save_checks();swift_boots_checks();diving_fins_checks();poison_checks();band_aid_checks();medkit_checks();escape_menu_checks();render_checks();
 for(int w=0;w<WEAPON_COUNT;w++){ProjectileProfile p=weapon_profile((WeaponType)w);assert(fabsf(faster_fire_rate(p.fire_rate,0)-p.fire_rate)<0.001f);assert(fabsf(faster_fire_rate(p.fire_rate,WEAPON_OIL_MAX)-TOUHOU_FIRE_RATE)<0.001f);assert(fabsf(faster_fire_rate(p.fire_rate,WEAPON_OIL_MAX)*faster_damage(p.fire_rate,p.damage,WEAPON_OIL_MAX)/(p.fire_rate*p.damage)-FASTER_DPS_AT_MAX)<0.001f);}
 SDL_Quit();puts("craftcheck: ok");return 0;
}