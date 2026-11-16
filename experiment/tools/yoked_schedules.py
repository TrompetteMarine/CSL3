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

Format 2 (KGi-DISS-I042, what the oTree app reads) keeps every field of format 1 bit for bit
for the same seed and adds, from a second generator:
  board_u      the uniform behind each board bit (16-bit, hex), so the app can build the LOW
               board of the simulation: the trader wins when it is below the participant's
               own trailing rate
  good_ticket, good_side   which symbol is the better ticket and where it is shown
  starts       for each market round, the start positions of the four sliders
  probe[i]     symbol, payout chance, and the uniform of the settlement that scores forecasts
  paid_forecast, prize_u   which of the eight forecasts is paid, and the lottery draw

Format 3 (KGi-DISS-I043, the basket economy with prediction markets) keeps format 1 bit for
bit and adds, from a third generator:
  settle_u     the uniform behind the good / bad bits (16-bit, hex): the clearing price of a
               good is an increasing function of it, so an order fills exactly when its bit says
  markets      four prediction markets common to the whole file: asset, threshold, price
               history, chance of closing above, the draw that settles it, the posted bet price
  probe[i]     which market it is, and the evidence shown: 'record' (ten trial closes held
               with the participant's own tickets) or 'source' (another trader's forecast)
--no-social gives two record pairs (a seed wave; design Y's probe). --markets-from FILE reuses
the markets of an earlier file, so that forecasts made there can be shown as sources here.

    python experiment/tools/yoked_schedules.py --pairs 40 --seed 20261111 --out experiment/schedules/pilot.json
    python experiment/tools/yoked_schedules.py --pairs 40 --seed 20261111 --format 3 --out experiment/schedules/pilot_v3.json
"""
import argparse
import hashlib
import json

import numpy as np

SEL = json.load(open('records/probe_design_I037_selected.json'))['S1x']
K, R1, R2, M = SEL['k'], SEL['r1'], SEL['r2'], SEL['m']
ODDS_RICH, MU_REF = (0.75, 0.35), 0.72            # P1TAG['p75']
ODDS_DEP = (0.25, 0.10)                            # ODDS['harsh']
assert SEL['odds'] == 'harsh' and SEL.get('p1') == 'p75'
bits = lambda a: ''.join('1' if x else '0' for x in a)
TICKETS = ('SQUARE', 'TRIANGLE')
PROBE_SYMBOLS = ('CIRCLE', 'DIAMOND', 'HEXAGON', 'STAR', 'CROSS', 'PENTAGON')
PROBE_CHANCE = {True: 0.9, False: 0.1}             # DRAFT (author decision): payout chance of a probe ticket
N_ITEMS = 4                                        # three fairness items and one entitlement item
START_GRID = np.arange(10, 95, 5)                  # slider start positions
U16 = 65536


def make(pairs, seed, k=K, _keep=None):
    rng = np.random.default_rng(seed)
    scheds = []
    for sid in range(pairs):
        u = rng.random((R1 + R2) * k)
        rich = np.arange(len(u)) < R1 * k
        good = u < np.where(rich, ODDS_RICH[0], ODDS_DEP[0])
        bad = u < np.where(rich, ODDS_RICH[1], ODDS_DEP[1])
        probe = []
        for pair_no, whose in enumerate(rng.permutation(['own', 'other'])):
            for fav in rng.permutation([True, False]):
                wins = M - 1 if fav else 1
                probe.append(dict(pair=pair_no, record_of=str(whose), favourable=bool(fav),
                                  shown=bits(rng.permutation(np.arange(M) < wins))))
        rich_board = 'HIGH' if rng.random() < 0.5 else 'LOW'
        ub = rng.random(len(u))                            # the board's uniform (kept for format 2)
        if _keep is not None:
            _keep.append((u, ub))
        scheds.append(dict(id=sid, rich_board=rich_board,
                           good=bits(good), bad=bits(bad), board=bits(ub < MU_REF), probe=probe))
    alloc, slot = [], 0
    for sid in rng.permutation(pairs):                     # each schedule once per arm, arm order at random
        for arm in rng.permutation(['HIGH', 'LOW']):
            alloc.append(dict(slot=slot, schedule=int(sid), arm=str(arm)))
            slot += 1
    return dict(design=dict(rounds_rich=R1, rounds_deprivation=R2, settlements_per_round=k, odds_rich=ODDS_RICH,
                            odds_deprivation=ODDS_DEP, board_rate=MU_REF, probe_settlements=M),
                seed=seed, schedules=scheds, allocation=alloc)


def make2(pairs, seed, k=K, _keep=None):
    """format 2: format 1 plus what the oTree app needs, drawn from a second generator"""
    keep = [] if _keep is None else _keep
    obj = make(pairs, seed, k, _keep=keep)
    rng = np.random.default_rng([seed, 2])
    for s, (_, ub) in zip(obj['schedules'], keep):
        s['board_u'] = ''.join(f'{int(x):04x}' for x in np.floor(ub * U16))
        s['good_ticket'] = str(rng.choice(TICKETS))
        s['good_side'] = str(rng.choice(['left', 'right']))
        s['starts'] = [[int(x) for x in rng.choice(START_GRID, N_ITEMS)] for _ in range(R1 + R2)]
        for p, sym in zip(s['probe'], rng.permutation(PROBE_SYMBOLS)[:len(s['probe'])]):
            p['symbol'] = str(sym)
            p['chance'] = PROBE_CHANCE[p['favourable']]
            p['score_u'] = round(float(rng.random()), 6)
        s['paid_forecast'] = int(rng.integers(0, 2 * len(s['probe'])))
        s['prize_u'] = round(float(rng.random()), 6)
    obj['version'] = 2
    return obj


THRESHOLDS = (5.0, 8.0, 12.0, 20.0)
CHART_POINTS = 40
ECONOMY = dict(basket_size=6, cap=4.0, price_sigma=0.12,        # goods market
               bet_allowance=10, bet_payout=20, bet_price=50)   # points; price in cents per 100


def market_uid(m):
    """identifies a market across schedule files (a forecast is a source only for its own market)"""
    text = json.dumps([m['asset'], m['threshold'], m['chance'], m['chart']], separators=(',', ':'))
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def make_markets(rng):
    """four markets, two favourable and two unfavourable: (M1, M2) and (M3, M4) are the pairs"""
    out = []
    assets = rng.permutation(PROBE_SYMBOLS)[:4]
    thresholds = rng.permutation(THRESHOLDS)
    for i in range(4):
        fav = i % 2 == 0
        step = rng.normal(0, 1, CHART_POINTS)
        walk = np.cumsum(step)
        bridge = walk - np.arange(1, CHART_POINTS + 1) / CHART_POINTS * walk[-1]      # ends on the threshold
        thr = float(thresholds[i])
        chart = [round(float(x), 2) for x in thr * (1 + 0.02 * bridge / max(bridge.std(), 1e-9))]
        m = dict(key=f'M{i + 1}', asset=str(assets[i]), threshold=thr, chart=chart, favourable=fav,
                 chance=PROBE_CHANCE[fav], score_u=round(float(rng.random()), 6), price_yes=ECONOMY['bet_price'])
        above = m['score_u'] < m['chance']
        gap = float(rng.uniform(0.006, 0.03))
        m['close'] = round(thr * (1 + gap if above else 1 - gap), 2)
        m['uid'] = market_uid(m)
        out.append(m)
    return out


def make3(pairs, seed, k=K, social=True, markets=None):
    """format 3: the basket economy with prediction markets"""
    keep = []
    obj = make2(pairs, seed, k, _keep=keep)                # every field of formats 1 and 2, unchanged
    rng = np.random.default_rng([seed, 3])
    obj['markets'] = markets if markets is not None else make_markets(rng)
    by_key = {m['key']: m for m in obj['markets']}
    for s, (u, _) in zip(obj['schedules'], keep):
        s['settle_u'] = ''.join(f'{int(x):04x}' for x in np.floor(u * U16))
        first = int(rng.integers(0, 2))                    # which market pair this schedule's pair 0 gets
        for p in s['probe']:
            mp = first if p['pair'] == 0 else 1 - first
            m = by_key[f"M{2 * mp + (1 if p['favourable'] else 2)}"]
            p['market'] = m['key']
            p['symbol'], p['chance'], p['score_u'] = m['asset'], m['chance'], m['score_u']
            p['evidence'] = 'source' if (social and p['record_of'] == 'other') else 'record'
            p['cue'] = (90 if p['favourable'] else 10) if p['evidence'] == 'source' else None
    obj['design'].update(ECONOMY)
    obj['version'] = 3
    return obj


def verify(obj):
    """raises AssertionError if a schedule file breaks the yoking rules"""
    k = obj['design']['settlements_per_round']
    n = (R1 + R2) * k
    if obj.get('version', 1) == 3:
        keys = [m['key'] for m in obj['markets']]
        assert keys == ['M1', 'M2', 'M3', 'M4'] and [m['favourable'] for m in obj['markets']] == [True, False, True, False]
        for m in obj['markets']:
            assert len(m['chart']) == CHART_POINTS and abs(m['chart'][-1] - m['threshold']) < 0.011
            assert (m['close'] > m['threshold']) == (m['score_u'] < m['chance']) and m['uid'] == market_uid(m)
        assert len({m['asset'] for m in obj['markets']}) == 4
        for s in obj['schedules']:
            uq = np.array([int(s['settle_u'][i:i + 4], 16) for i in range(0, 4 * n, 4)]) / U16
            rich = np.arange(n) < R1 * k
            for bits_, odds in ((s['good'], (ODDS_RICH[0], ODDS_DEP[0])), (s['bad'], (ODDS_RICH[1], ODDS_DEP[1]))):
                p = np.where(rich, odds[0], odds[1])
                edge = np.abs(uq - p) < 2 / U16
                assert np.all(((np.array(list(bits_)) == '1') == (uq < p)) | edge)
            assert sorted(p['market'] for p in s['probe']) == keys
            for pr in (0, 1):
                t = [p for p in s['probe'] if p['pair'] == pr]
                assert len({p['evidence'] for p in t}) == 1 and {p['market'][1] for p in t} in ({'1', '2'}, {'3', '4'})
            for p in s['probe']:
                m = obj['markets'][keys.index(p['market'])]
                assert m['favourable'] == p['favourable'] and p['symbol'] == m['asset']
                assert (p['cue'] in (90, 10)) == (p['evidence'] == 'source')
    if obj.get('version', 1) == 2:
        for s in obj['schedules']:
            uq = np.array([int(s['board_u'][i:i + 4], 16) for i in range(0, 4 * n, 4)]) / U16
            assert len(s['board_u']) == 4 * n
            b = np.array(list(s['board'])) == '1'
            edge = np.abs(uq - MU_REF) < 2 / U16           # the stored bit comes from the unrounded draw
            assert np.all((b == (uq < MU_REF)) | edge)
            assert s['good_ticket'] in TICKETS and s['good_side'] in ('left', 'right')
            assert len(s['starts']) == R1 + R2 and all(len(r) == N_ITEMS and all(x in START_GRID for x in r) for r in s['starts'])
            assert len({p['symbol'] for p in s['probe']}) == len(s['probe'])
            assert all(p['chance'] == PROBE_CHANCE[p['favourable']] and 0 <= p['score_u'] < 1 for p in s['probe'])
            assert 0 <= s['paid_forecast'] < 2 * len(s['probe']) and 0 <= s['prize_u'] < 1
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
    ap.add_argument('--format', type=int, default=1, choices=(1, 2, 3))
    ap.add_argument('--k', type=int, default=K, help='settlements per round (120 = the certified design)')
    ap.add_argument('--no-social', action='store_true', help='format 3: both pairs get a record (seed wave)')
    ap.add_argument('--markets-from', default='', help='format 3: reuse the markets of this schedule file')
    a = ap.parse_args()
    if a.format == 3:
        mk = json.load(open(a.markets_from))['markets'] if a.markets_from else None
        obj = make3(a.pairs, a.seed, a.k, social=not a.no_social, markets=mk)
    else:
        obj = make(a.pairs, a.seed, a.k) if a.format == 1 else make2(a.pairs, a.seed, a.k)
    verify(obj)
    json.dump(obj, open(a.out, 'w'))
    print(f"{a.pairs} schedules, {len(obj['allocation'])} participant slots -> {a.out}")
