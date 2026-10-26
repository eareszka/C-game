"""Rank the difficulty run: how hard each finished enemy was for a human.

    python tools/playtest_report.py [--bot] [--run LABEL ...]

Reads playtest/trials.csv (the F4 run, src/playtest.cpp): real fights with
the knife in each tier's gear, so they run as long as the kill takes. Hits are
counted a minute, so a short fight and a long one compare fairly; the time to
kill and the accuracy are shown but not scored. Warm-ups (order -1) are left out. Per enemy, over all its scored trials (or only the --run labels):
the median hits a minute (a frame hurt is one hit, however many shots landed
in it; bars a minute counts what they took), and the median 1-5 rating (skipped ratings ignored).
The score puts both on one scale -- each a z-score across the enemies,
weighted W_HITS and W_FEEL -- so 0 is an average enemy, + harder.

Prints the enemies in the sheet's order with their score and their rank in
their tier, and flags:
    ABOVE <tier>   harder than the median of the tier above it
    BELOW <tier>   easier than the median of the tier below it
(above and below in DIFFICULTY order: the tier-1 bosses between SEVERE and
ELITE, the tier-2 bosses hardest -- not the sheet's row order)
    FEEL           the rating and the hits disagree (a z apart by FEEL_GAP)
Writes playtest/report.csv and playtest/difficulty_sheet.png: the sheet with a
score badge on each enemy, green easy to red hard (enemies not in the run faded).
--bot adds battlecensus.exe's hits for the same enemy (seed 1, 60 s), to show
where the bot and a human disagree.
"""
import argparse, csv, os, re, statistics, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enemy_tier_sheet as ets
import playtest_order as po

W_HITS, W_FEEL = 0.6, 0.4   # how much the hits and the rating count in the score
FEEL_GAP = 1.5              # z apart before the rating and the hits disagree

ROOT = ets.ROOT
# How hard the tiers are meant to be, easiest first (the user): not the sheet's rows.
DIFFICULTY = ['STARTER', 'LOW', 'MEDIUM', 'UPPER', 'HARD', 'SEVERE', 'BOSS1', 'ELITE', 'BOSS2', 'BOSS3']


def z(values):
    # {id: v} -> {id: z}
    if len(values) < 2: return {i: 0.0 for i in values}
    m, sd = statistics.mean(values.values()), statistics.pstdev(values.values()) or 1.0
    return {i: (v - m) / sd for i, v in values.items()}


def bot_hits(i):
    exe = os.path.join(ROOT, 'battlecensus.exe' if os.name == 'nt' else 'battlecensus')
    try:
        out = subprocess.run([exe, str(i), '1', '60'], cwd=ROOT, capture_output=True, text=True, timeout=600).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r'hits (\d+)', out)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bot', action='store_true', help='add battlecensus hits for each enemy')
    ap.add_argument('--run', nargs='*', help='only these run labels (e.g. 2026-10-19-fwd)')
    args = ap.parse_args()

    path = os.path.join(ROOT, 'playtest', 'trials.csv')
    if not os.path.exists(path):
        sys.exit('no %s yet: play a run first (F4 in --debug)' % os.path.relpath(path, ROOT))
    rows = [r for r in csv.DictReader(open(path, encoding='utf-8'))
            if int(r['order_index']) >= 0 and (not args.run or r['run'] in args.run)]
    if not rows: sys.exit('no scored trials')

    order = po.sheet_order()
    names = po.names()
    tier_of = dict(order)
    by = {}
    for r in rows: by.setdefault(int(r['id']), []).append(r)
    hpm = {i: statistics.median(float(r['hits_per_min']) for r in rs) for i, rs in by.items()}
    bpm = {i: statistics.median(float(r['bars']) * 60.0 / max(float(r['secs']), 1.0) for r in rs) for i, rs in by.items()}
    feel = {i: statistics.median(int(r['rating']) for r in rs if int(r['rating']))
            for i, rs in by.items() if any(int(r['rating']) for r in rs)}
    first = {i: statistics.median(float(r['first_hit_t']) for r in rs if float(r['first_hit_t']) >= 0)
             for i, rs in by.items() if any(float(r['first_hit_t']) >= 0 for r in rs)}
    ttk = {i: statistics.median(float(r['secs']) for r in rs) for i, rs in by.items()}
    acc = {i: statistics.median(float(r['accuracy']) for r in rs) for i, rs in by.items()}
    zh, zf = z(hpm), z(feel)
    score = {i: (W_HITS * zh[i] + W_FEEL * zf[i]) / (W_HITS + W_FEEL) if i in zf else zh[i] for i in hpm}

    # Each tier's median score, and each enemy's rank in its tier (1 easiest)
    played = [(i, t) for i, t in order if i in score]
    med = {t: statistics.median(score[i] for i, tt in played if tt == t) for t in {t for _, t in played}}
    tiers_played = [t for t in DIFFICULTY if t in med]
    rank = {}
    for t in tiers_played:
        for n, i in enumerate(sorted((i for i, tt in played if tt == t), key=lambda i: score[i])): rank[i] = n + 1
    flags = {}
    for i, t in played:
        f, k = [], tiers_played.index(t)
        if k + 1 < len(tiers_played) and score[i] > med[tiers_played[k + 1]]: f.append('ABOVE ' + tiers_played[k + 1])
        if k > 0 and score[i] < med[tiers_played[k - 1]]: f.append('BELOW ' + tiers_played[k - 1])
        if i in zf and abs(zh[i] - zf[i]) >= FEEL_GAP: f.append('FEEL (%s)' % ('feels harder' if zf[i] > zh[i] else 'feels easier'))
        flags[i] = f
    bot = {i: bot_hits(i) for i, _ in played} if args.bot else {}

    print('%-4s %-28s %-8s %4s %6s %6s %5s %6s %6s %4s %6s %5s%s  %s' % ('id', 'name', 'tier', 'runs', 'hits/m', 'bars/m', 'feel',
                                                           'first', 'kill', 'acc', 'score',
                                                           'rank', '   bot' if bot else '', 'flags'))
    t_prev = None
    for i, t in order:
        if t != t_prev:
            print('-- %s%s' % (t, '  (median %+.2f)' % med[t] if t in med else ''))
            t_prev = t
        if i not in score:
            print('%02d   %-28s %-8s    -  not played yet' % (i, names[i][:28], t))
            continue
        n = len(by[i])
        print('%02d   %-28s %-8s %4d %6.1f %6.1f %5s %6s %5.0fs %3.0f%% %+6.2f %2d/%-2d%s  %s' % (
            i, names[i][:28], t, n, hpm[i], bpm[i], '%.1f' % feel[i] if i in feel else '-',
            '%.1fs' % first[i] if i in first else 'none', ttk[i], acc[i], score[i], rank[i], sum(1 for _, tt in played if tt == t),
            ' %5s' % ('-' if bot.get(i) is None else bot[i]) if bot else '', ', '.join(flags[i])))

    # A suggested order, easiest first, by score alone
    print('\nby score, easiest first:')
    print('  ' + '  '.join('%02d' % i for i in sorted(score, key=lambda i: score[i])))

    out_csv = os.path.join(ROOT, 'playtest', 'report.csv')
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'name', 'tier', 'runs', 'hits_per_min', 'bars_per_min', 'feel', 'first_hit_t', 'kill_secs', 'accuracy', 'score', 'tier_rank', 'bot_hits', 'flags'])
        for i, t in played:
            w.writerow([i, names[i], t, len(by[i]), '%.2f' % hpm[i], '%.2f' % bpm[i], feel.get(i, ''), first.get(i, ''),
                        '%.1f' % ttk[i], '%.0f' % acc[i], '%.3f' % score[i], rank[i], bot.get(i, ''), '; '.join(flags[i])])

    # The sheet with a badge each: the score, green (easiest played) to red (hardest)
    lo, hi = min(score.values()), max(score.values())
    def colour(s):
        k = (s - lo) / (hi - lo) if hi > lo else 0.5
        return (int(60 + 190 * k), int(200 - 150 * k), 60)
    def tags(i):
        if i not in score: return []
        # bottom left the first flag, short (^HARD: harder than HARD's median), bottom right hits a minute
        out = [('tr', '%+.1f' % score[i], colour(score[i])), ('br', '%.0f/m' % hpm[i], (60, 60, 70))]
        if flags[i]:
            f = flags[i][0].split(' (')[0]
            out.append(('bl', f.replace('ABOVE ', '^').replace('BELOW ', 'v'), (190, 40, 40)))
        return out
    def row_note(ids):
        t = tier_of.get(next((i for i in ids if i in tier_of), -1))
        return 'median %+.2f' % med[t] if t in med else 'not played'
    out_png = os.path.join(ROOT, 'playtest', 'difficulty_sheet.png')
    ets.main(out_png, tags=tags, dim={i for i in range(len(names)) if i not in score}, row_note=row_note,
             title='Difficulty run: %d enemies, %d trials. Badge = score (0 average, + harder); ^TIER/vTIER = past that tier median; bottom right = hits a minute.'
                   % (len(score), len(rows)))
    print('\nwrote %s and %s' % (os.path.relpath(out_csv, ROOT), os.path.relpath(out_png, ROOT)))


if __name__ == '__main__':
    main()
