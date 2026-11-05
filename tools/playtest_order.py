"""The difficulty run's enemies, in the finished sheet's order: playtest/order.txt.

    python tools/playtest_order.py

The finished sheet (tools/enemy_redraw_sheet.py, enemy_rating.png) runs tier by
tier, STARTER first, ids rising within a tier. The run is every enemy on it
whose bullet patterns are done -- ready in include/ready.h -- finished art or not
(the user, 2026-10-30). The game reads this file on F4 (src/playtest.cpp); rerun
after a tier or ready change.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enemy_tier_sheet as ets

ROOT = ets.ROOT


def tiers():
    return re.findall(r'T_([A-Z0-9]+)', ets.table('include/enemy.h', 'ENEMY_TIERS[] = {'))


def names():
    return re.findall(r'"([^"]+)"', ets.table('src/main.cpp', 'ENEMY_NAMES[] = {'))


def sheet_order():
    # [(id, tier)] for the run, in the sheet's order
    ts, ok = tiers(), ets.ready_ids()
    return [(i, k) for k, _, _ in ets.ORDER for i, t in enumerate(ts) if t == k and i in ok]


def main():
    nm = names()
    order = sheet_order()
    os.makedirs(os.path.join(ROOT, 'playtest'), exist_ok=True)
    out = os.path.join(ROOT, 'playtest', 'order.txt')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# The difficulty run (F4): enemies with their bullet patterns done (ready.h), in the sheet\'s order.\n')
        f.write('# Written by tools/playtest_order.py -- id, tier, name.\n')
        for i, t in order:
            f.write('%d %s %s\n' % (i, t, nm[i]))
    print('%d enemies -> %s' % (len(order), os.path.relpath(out, ROOT)))


if __name__ == '__main__':
    main()
