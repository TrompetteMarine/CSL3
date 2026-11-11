"""Pre-drawn schedules for the yoked ten-repetition design (KGi-DISS-I041).

A schedule fixes everything the experimenter draws, before the session, for one pair (one
HIGH and one LOW participant):
  rich_board   board shown to BOTH members in the rich round ('HIGH' or 'LOW')
  good, bad    for every settlement, whether the better and the worse ticket win; both come
               from one uniform draw, so the same ticket pays the same to both members and
               the better ticket wins whenever the worse one does
  board        for every settlement, whether the HIGH board's trader wins (rate MU_REF)
  probe        four probe tickets: which is favourable, whose record it is, the order of the
               ten settlements shown
The LOW board is not scheduled: it replays the participant's own trailing record.

    python experiment/tools/yoked_schedules.py --pairs 40 --seed 20261111 --out experiment/schedules/pilot.json
"""
import argparse
import json

import numpy as np

SEL = json.load(open('records/probe_design_I037_selected.json'))['S1x']
K, R1, R2, M = SEL['k'], SEL['r1'], SEL['r2'], SEL['m']
ODDS_RICH, MU_REF = (0.75, 0.35), 0.72            # P1TAG['p75']
ODDS_DEP = (0.25, 0.10)                            # ODDS['harsh']
assert SEL['odds'] == 'harsh' and SEL.get('p1') == 'p75'
bits = lambda a: ''.join('1' if x else '0' for x in a)


def make(pairs, seed):
    rng = np.random.default_rng(seed)
    scheds = []
    for sid in range(pairs):
        u = rng.random((R1 + R2) * K)
        rich = np.arange(len(u)) < R1 * K
        good = u < np.where(rich, ODDS_RICH[0], ODDS_DEP[0])
        bad = u < np.where(rich, ODDS_RICH[1], ODDS_DEP[1])
        probe = []
        for pair_no, whose in enumerate(rng.permutation(['own', 'other'])):
            for fav in rng.permutation([True, False]):
                wins = M - 1 if fav else 1
                probe.append(dict(pair=pair_no, record_of=str(whose), favourable=bool(fav),
                                  shown=bits(rng.permutation(np.arange(M) < wins))))
        scheds.append(dict(id=sid, rich_board='HIGH' if rng.random() < 0.5 else 'LOW',
                           good=bits(good), bad=bits(bad), board=bits(rng.random(len(u)) < MU_REF), probe=probe))
    alloc, slot = [], 0
    for sid in rng.permutation(pairs):                     # each schedule once per arm, arm order at random
        for arm in rng.permutation(['HIGH', 'LOW']):
            alloc.append(dict(slot=slot, schedule=int(sid), arm=str(arm)))
            slot += 1
    return dict(design=dict(rounds_rich=R1, rounds_deprivation=R2, settlements_per_round=K, odds_rich=ODDS_RICH,
                            odds_deprivation=ODDS_DEP, board_rate=MU_REF, probe_settlements=M),
                seed=seed, schedules=scheds, allocation=alloc)


def verify(obj):
    """raises AssertionError if a schedule file breaks the yoking rules"""
    n = (R1 + R2) * K
    for s in obj['schedules']:
        g, b = np.array(list(s['good'])) == '1', np.array(list(s['bad'])) == '1'
        assert len(g) == len(b) == len(s['board']) == n
        assert not np.any(b & ~g)                          # the better ticket wins whenever the worse does
        assert s['rich_board'] in ('HIGH', 'LOW') and len(s['probe']) == 4
        for pr in (0, 1):
            t = [p for p in s['probe'] if p['pair'] == pr]
            assert sorted(p['favourable'] for p in t) == [False, True] and len({p['record_of'] for p in t}) == 1
            for p in t:
                assert len(p['shown']) == M and p['shown'].count('1') == (M - 1 if p['favourable'] else 1)
        assert {p['record_of'] for p in s['probe']} == {'own', 'other'}
    ids = [s['id'] for s in obj['schedules']]
    for arm in ('HIGH', 'LOW'):
        assert sorted(a['schedule'] for a in obj['allocation'] if a['arm'] == arm) == sorted(ids)
    for a, b in zip(obj['allocation'][0::2], obj['allocation'][1::2]):
        assert a['schedule'] == b['schedule'] and {a['arm'], b['arm']} == {'HIGH', 'LOW'}
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', type=int, required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    obj = make(a.pairs, a.seed)
    verify(obj)
    json.dump(obj, open(a.out, 'w'))
    print(f"{a.pairs} schedules, {len(obj['allocation'])} participant slots -> {a.out}")
