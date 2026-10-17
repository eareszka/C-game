// The story's rules, checked: the stage read off the beaten bits, which boss
// sites stand at each stage, the lead's compass across the seam, and on real
// worlds that every laid site is on walkable ground of its kind and far enough
// from the start. Exits non-zero on the first broken rule.
//   make storycheck && ./storycheck [seed ...]      (default seeds 1 15 387 2026)
#include "story.h"
#include "tilemap.h"
#include "towns.h"     // TOWN1_HALL_DOOR_*
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static Tilemap g_map;

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);   // every line out before an assert can cut it short
    // The stage from the bits, and the bits from the stage.
    for (int s = 0; s < STORY_STAGE_COUNT; s++) {
        story_set_stage((StoryStage)s);
        assert(story_stage() == (StoryStage)s);
    }
    story_flags()->beaten = 0;
    assert(story_stage() == STORY_ARC1 && !story_beaten(6));
    story_mark_beaten(6);
    story_mark_beaten(17);                              // not a boss: nothing
    assert(story_beaten(6) && story_flags()->beaten == 1u && story_stage() == STORY_ARC1);
    story_set_stage(STORY_TURN);
    story_mark_beaten(52);
    assert(story_stage() == STORY_TURN && story_tier2_kills() == 1);

    // Sites: a stand-in world with every site laid at the middle.
    memset(&g_map, 0, sizeof(g_map));
    for (int i = 0; i < STORY_BOSS_COUNT; i++) g_map.boss_sites[i] = { (short)(MAP_WIDTH / 2), (short)(MAP_HEIGHT / 2) };
    story_set_stage(STORY_ARC1);
    assert(story_site_active(&g_map, 0) && story_site_active(&g_map, 3) && !story_site_active(&g_map, 4) && !story_site_active(&g_map, STORY_ANAYE));
    story_set_stage(STORY_TURN);
    assert(story_site_active(&g_map, 4) && story_site_active(&g_map, 6) && !story_site_active(&g_map, STORY_ANAYE));
    story_mark_beaten(44);
    assert(!story_site_active(&g_map, 5) && story_site_active(&g_map, 4));
    story_set_stage(STORY_DESCENT);
    assert(story_site_active(&g_map, STORY_ANAYE) && !story_site_active(&g_map, 4));
    story_set_stage(STORY_OPEN);
    assert(!story_site_active(&g_map, STORY_ANAYE) && !story_site_active(&g_map, STORY_SWARM));
    g_map.boss_sites[2] = { -1, -1 };
    assert(!story_site_active(&g_map, 2));

    // The lead's compass, the short way round the wrap axis.
    char lead[96];
    g_map.boss_sites[0] = { 20, (short)(MAP_HEIGHT / 2) };
    story_lead(&g_map, 40, MAP_HEIGHT / 2, 6, lead, sizeof(lead));
    assert(strncmp(lead, "West,", 5) == 0);
    story_lead(&g_map, MAP_WIDTH - 20, MAP_HEIGHT / 2, 6, lead, sizeof(lead));   // across the seam on an E-W wrap: east is nearer
    g_map.wrap_axis = WRAP_X;
    story_lead(&g_map, MAP_WIDTH - 20, MAP_HEIGHT / 2, 6, lead, sizeof(lead));
    printf("across the seam: %s\n", lead);
    story_lead(&g_map, 20, MAP_HEIGHT / 2 + 300, 6, lead, sizeof(lead));
    assert(strncmp(lead, "North,", 6) == 0);
    story_lead(&g_map, 20, MAP_HEIGHT / 2, 49, lead, sizeof(lead));
    assert(strstr(lead, "nobody knows"));

    // Real worlds: every laid site stands on walkable ground of its kind, out
    // of the start, and the sea boss and the swarm have none.
    static const unsigned DEFAULT_SEEDS[] = { 1, 15, 387, 2026 };
    int nseeds = argc > 1 ? argc - 1 : (int)(sizeof(DEFAULT_SEEDS) / sizeof(DEFAULT_SEEDS[0]));
    for (int k = 0; k < nseeds; k++) {
        unsigned seed = argc > 1 ? (unsigned)strtoul(argv[k + 1], nullptr, 10) : DEFAULT_SEEDS[k];
        memset(&g_map, 0, sizeof(g_map));
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        printf("seed %u\n", seed);
        // The coastal town's hall has its temporary door, opening room 3.
        if (g_map.towns[1].x >= 0) {
            bool hall = false;
            for (int d = 0; d < g_map.num_doors; d++)
                if (g_map.doors[d].x == g_map.towns[1].x + TOWN1_HALL_DOOR_X && g_map.doors[d].y == g_map.towns[1].y + TOWN1_HALL_DOOR_Y)
                    hall = g_map.doors[d].interior_id == 3 && g_map.doors[d].w == TOWN1_HALL_DOOR_W;
            assert(hall && "town 1's hall door is registered");
            printf("  hall door at %d,%d\n", g_map.towns[1].x + TOWN1_HALL_DOOR_X, g_map.towns[1].y + TOWN1_HALL_DOOR_Y);
            // The lighthouse's door (room 4) lies near the town, the wharf has a
            // tip on deck, and the keeper's bat has a tree to roost in.
            int lh = g_map.lighthouse_door;
            assert(lh >= 0 && lh < g_map.num_doors && g_map.doors[lh].interior_id == 4 && "the lighthouse has its door");
            assert(g_map.wharf_tip.x >= 0 && tilemap_is_walkable(&g_map, g_map.wharf_tip.x, g_map.wharf_tip.y) && "the wharf has a tip on deck");
            int tree = story_quest_tree(&g_map);
            assert(tree >= 0 && "a large tree for the keeper's bat");
            printf("  lighthouse door at %d,%d  wharf tip %d,%d  quest tree at %d,%d\n", g_map.doors[lh].x, g_map.doors[lh].y,
                   g_map.wharf_tip.x, g_map.wharf_tip.y, g_map.dungeon_entrances[tree].x, g_map.dungeon_entrances[tree].y);
        }
        // The notes out of doors: the cave-mouth ones on walkable ground, the
        // sea ones on water (none without a shore east of the cave).
        for (int i = 0; i < story_note_count(); i++) {
            int tx, ty;
            if (!story_note_world_tile(&g_map, i, &tx, &ty)) continue;
            int t = g_map.tiles[ty][tx];
            assert((t == TILE_WATER || tilemap_is_walkable(&g_map, tx, ty)) && "a note lies where it can be reached");
        }
        // The hole: at the turn the ground round the island's cave goes to
        // wasteland, the mouth and the water untouched, and the mouth refuses
        // the boy until Anaye falls.
        {
            int mouth = g_map.tiles[DNG_FIXED_CAVE_Y][DNG_FIXED_CAVE_X];
            story_set_stage(STORY_ARC1);
            story_hole_apply(&g_map);
            assert(g_map.tiles[DNG_FIXED_CAVE_Y][DNG_FIXED_CAVE_X - 3] != TILE_WASTELAND && !story_hole_blocked());
            story_set_stage(STORY_TURN);
            story_hole_apply(&g_map);
            int waste = 0, water_kept = true;
            for (int dy = -STORY_HOLE_R; dy <= STORY_HOLE_R; dy++)
                for (int dx = -STORY_HOLE_R; dx <= STORY_HOLE_R; dx++) {
                    if (dx * dx + dy * dy > STORY_HOLE_R * STORY_HOLE_R) continue;
                    int t = g_map.tiles[DNG_FIXED_CAVE_Y + dy][DNG_FIXED_CAVE_X + dx];
                    waste += t == TILE_WASTELAND;
                    if (t == TILE_GRASS || t == TILE_MEADOW) water_kept = false;   // nothing green left
                }
            assert(waste > 60 && water_kept && g_map.tiles[DNG_FIXED_CAVE_Y][DNG_FIXED_CAVE_X] == mouth && story_hole_blocked());
            story_set_stage(STORY_OPEN);
            assert(!story_hole_blocked());
            printf("  the hole: %d tiles of wasteland round the cave\n", waste);
            story_set_stage(STORY_ARC1);
        }
        // Every village's speaker stands on its street.
        for (int v = 0; v < g_map.num_villages; v++) {
            int tx, ty;
            story_village_npc_tile(&g_map, v, &tx, &ty);
            assert(tilemap_is_walkable(&g_map, tx, ty) && village_at(&g_map, tx, ty) == v && "a villager stands on the street");
        }
        printf("  %d villages, every speaker on the street\n", g_map.num_villages);
        // Town 0 has exactly its two standing residents, on clear ground,
        // in addition to every village speaker even when all villages exist.
        {
            Player player = {};
            StoryWhere where = { STATE_OVERWORLD, &g_map, -1, -1, &player, false };
            StoryNpcPos people[32];
            int count = story_npcs_here(where, people, 32), residents = 0, skins = 0;
            for (int j = 0; j < count; j++) {
                int skin = story_npc_sprite(people[j]);
                if (skin < 0) continue;
                residents++;
                skins |= 1 << skin;
                float fx = people[j].x + 14, fy = people[j].y + 39;
                assert(!tilemap_pixel_solid(&g_map, fx - 6, fy));
                assert(!tilemap_pixel_solid(&g_map, fx + 6, fy));
                assert(fx >= g_map.towns[0].x * TILE_SIZE && fx < (g_map.towns[0].x + TOWN_W) * TILE_SIZE);
                assert(fy >= g_map.towns[0].y * TILE_SIZE && fy < (g_map.towns[0].y + TOWN_H) * TILE_SIZE);
                const char* line = story_npc_line(people[j], where);
                assert(line && line[0]);
            }
            assert(residents == 2 && skins == 6 && count == g_map.num_villages + 2);
            where.state = STATE_INTERIOR;
            count = story_npcs_here(where, people, 32);
            for (int j = 0; j < count; j++) assert(story_npc_sprite(people[j]) < 0);
            printf("  town 0: farmer and glasses on clear ground; dialogue ready\n");
        }
        for (int i = 0; i < STORY_BOSS_COUNT; i++) {
            BossSite s = g_map.boss_sites[i];
            if (i == STORY_SWARM) { assert(s.x < 0); continue; }
            if (i == 2) {   // the sea boss: on the ocean off the wharf, or nowhere without a wharf
                if (g_map.wharf_tip.x < 0) { assert(s.x < 0); continue; }
                assert(s.x >= 0 && g_map.tiles[s.y][s.x] == TILE_WATER && "Physeter floats on the sea");
                printf("  boss  49 at %4d,%4d on the sea, %d tiles off the tip\n", s.x, s.y,
                       abs(wrap_dx(s.x - g_map.wharf_tip.x)) + abs(wrap_dy(s.y - g_map.wharf_tip.y)));
                continue;
            }
            if (i == STORY_ANAYE) { assert(s.x == DNG_FIXED_CAVE_X && s.y == DNG_FIXED_CAVE_Y); continue; }
            printf("  boss %3d at %4d,%4d tile %2d\n", STORY_BOSSES[i], s.x, s.y, s.x >= 0 ? g_map.tiles[s.y][s.x] : -1);
            assert(s.x >= 0 && "every land boss has a site");
            assert(tilemap_is_walkable(&g_map, s.x, s.y) && "a site stands on walkable ground");
            int t = g_map.tiles[s.y][s.x];
            assert((t == TILE_GRASS || t == TILE_MEADOW || t == TILE_SAND || t == TILE_SNOW) && "a site stands on open ground");
            int dx = wrap_dx(s.x - MAP_WIDTH / 2), dy = wrap_dy(s.y - MAP_HEIGHT / 2);
            assert(sqrtf((float)dx * dx + (float)dy * dy) >= 150.0f && "a site is out of the start");
            for (int j = 0; j < i; j++) {
                BossSite o = g_map.boss_sites[j];
                if (o.x < 0 || j == STORY_ANAYE) continue;
                assert((abs(wrap_dx(o.x - s.x)) >= 40 || abs(wrap_dy(o.y - s.y)) >= 40) && "sites keep apart");
            }
        }
    }
    printf("storycheck: ok\n");
    return 0;
}
