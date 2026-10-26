"""The difficulty run's enemies, in the finished sheet's order: playtest/order.txt.

    python tools/playtest_order.py

The finished sheet (tools/enemy_redraw_sheet.py, enemy_rating.png) runs tier by
tier, STARTER first, ids rising within a tier. The run is the enemies on it that
are finished -- reference, fine or done in art/enemies/redraw_status.json --
and ready (include/ready.h), so every one has its own pattern. The game reads
this file on F4 (src/playtest.cpp); rerun after a tier, ready or redraw change.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enemy_tier_sheet as ets

ROOT = ets.ROOT


def finished():
    st = json.load(open(os.path.join(ROOT, 'art', 'enemies', 'redraw_status.json'), encoding='utf-8'))
    return set(st['reference']) | set(st['fine']['ids']) | set(st['done'])


def tiers():
    return re.findall(r'T_([A-Z0-9]+)', ets.table('include/enemy.h', 'ENEMY_TIERS[] = {'))


def names():
    return re.findall(r'"([^"]+)"', ets.table('src/main.cpp', 'ENEMY_NAMES[] = {'))


def sheet_order():
    # [(id, tier)] for the run, in the sheet's order
    ts, ok = tiers(), finished() & ets.ready_ids()
    return [(i, k) for k, _, _ in ets.ORDER for i, t in enumerate(ts) if t == k and i in ok]


def main():
    nm = names()
    order = sheet_order()
    left_out = sorted((finished() - ets.ready_ids()))
    os.makedirs(os.path.join(ROOT, 'playtest'), exist_ok=True)
    out = os.path.join(ROOT, 'playtest', 'order.txt')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# The difficulty run (F4): finished and ready enemies in the sheet\'s order.\n')
        f.write('# Written by tools/playtest_order.py -- id, tier, name.\n')
        for i, t in order:
            f.write('%d %s %s\n' % (i, t, nm[i]))
    print('%d enemies -> %s' % (len(order), os.path.relpath(out, ROOT)))
    print('finished but not ready (left out): %s' % (' '.join('%02d' % i for i in left_out) or 'none'))


if __name__ == '__main__':
    main()
