"""Fidelity of the oTree task engine to the certified design (KGi-DISS-I042 gates G1, G2;
KGi-DISS-I043 gate H1: prices, markets, bets and sources). Run from the repository root."""
import importlib.util
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(EXP, 'tools'))
import yoked_schedules as ys  # noqa: E402

spec = importlib.util.spec_from_file_location('dm_engine', os.path.join(EXP, 'diss_market', 'engine.py'))
en = importlib.util.module_from_spec(spec)
spec.loader.exec_module(en)


def reference_low_board(uq, own):
    """the rule of twins_I040.twins, written with its ring buffer: the board trader wins when
    the board uniform is below the participant's trailing rate BEFORE the settlement"""
    ring, out = np.zeros(15), []
    for t in range(len(own)):
        cnt = min(t, 15)
        trail = 0.5 if t == 0 else ring[:cnt].mean()
        out.append(uq[t] < np.clip(trail, .05, .95))
        ring[t % 15] = own[t]
    return np.array(out)


def play(obj, s, arm, choices):
    d = obj['design']
    hist, own_all, board_all = '', [], []
    for r, good in enumerate(choices):
        own = en.own_bits(s, d, r, good)
        board_all.append(en.board_bits(s, d, r, arm, hist, own))
        own_all.append(own)
        hist += own
    return own_all, board_all


def test_settlements_and_boards_follow_the_schedule_and_the_simulation_rule():
    obj = ys.make3(200, 42)
    assert ys.verify(obj) and en.check_schedules(obj)
    d, rng = obj['design'], np.random.default_rng(1)
    k, nr = d['settlements_per_round'], en.n_rounds(d)
    gap_low, rate_high = [], []
    for s in obj['schedules']:
        choices = [bool(x) for x in rng.random(nr) < .7]
        uq = np.array([int(s['board_u'][i:i + 4], 16) for i in range(0, 4 * nr * k, 4)]) / 65536
        for arm in en.ARMS:
            own, board = play(obj, s, arm, choices)
            flat = np.array([c == '1' for c in ''.join(own)])
            src = np.concatenate([np.array(list((s['good'] if g else s['bad'])[r * k:(r + 1) * k])) == '1'
                                  for r, g in enumerate(choices)])
            assert np.array_equal(flat, src)                                   # own = the chosen ticket's bits
            ref_low = reference_low_board(uq, flat)
            for r in range(nr):
                got = np.array(list(board[r])) == '1'
                regime = s['rich_board'] if r < d['rounds_rich'] else arm
                want = (np.array(list(s['board'][r * k:(r + 1) * k])) == '1') if regime == 'HIGH' else ref_low[r * k:(r + 1) * k]
                assert np.array_equal(got, want), (s['id'], arm, r)
                if r >= d['rounds_rich']:
                    (rate_high if arm == 'HIGH' else gap_low).append(got.mean() - (0 if arm == 'HIGH' else flat[r * k:(r + 1) * k].mean()))
    assert abs(np.mean(rate_high) - .72) < .01                                 # HIGH board at the board rate
    assert abs(np.mean(gap_low)) < .02                                         # LOW board at the participant's own level


def test_members_of_a_pair_share_outcomes_and_the_rich_round_board():
    obj = ys.make3(50, 7)
    d = obj['design']
    for s in obj['schedules']:
        ch = [True] * en.n_rounds(d)
        (own_h, board_h), (own_l, board_l) = play(obj, s, 'HIGH', ch), play(obj, s, 'LOW', ch)
        assert own_h == own_l                                                  # same tickets, same outcomes
        assert board_h[0] == board_l[0]                                        # same board in the rich round
        assert board_h[1:] != board_l[1:]


def test_each_format_keeps_the_one_before_and_the_example_files():
    a, b, c = ys.make(6, 11), ys.make2(6, 11), ys.make3(6, 11)
    for sa, sb, sc in zip(a['schedules'], b['schedules'], c['schedules']):
        assert all(sa[k] == sb[k] == sc[k] for k in ('id', 'rich_board', 'good', 'bad', 'board'))
        assert all({k: p2[k] for k in p1} == p1 for p1, p2 in zip(sa['probe'], sb['probe']))
        # format 3 keeps every format-2 field of a schedule except what a market now carries
        assert all(sb[k] == sc[k] for k in sb if k != 'probe')
        assert all(p2[k] == p3[k] for p2, p3 in zip(sb['probe'], sc['probe']) for k in ('pair', 'record_of', 'favourable', 'shown'))
    assert a['allocation'] == b['allocation'] == c['allocation'] and a['design'] == b['design']
    assert all(c['design'][k] == v for k, v in b['design'].items())
    ex2 = json.load(open(os.path.join(EXP, 'schedules', 'example_seed0_4pairs_v2.json')))
    assert ex2 == json.loads(json.dumps(ys.make2(4, 0)))
    ex3 = json.load(open(os.path.join(EXP, 'schedules', 'example_seed0_4pairs_v3.json')))
    assert ex3 == json.loads(json.dumps(ys.make3(4, 0))) and ys.verify(ex3)
    seed = json.load(open(os.path.join(EXP, 'schedules', 'example_seed0_4pairs_v3_nosocial.json')))
    assert seed == json.loads(json.dumps(ys.make3(4, 0, social=False))) and ys.verify(seed)
    for old in (a, b):
        with pytest.raises(en.ScheduleError):
            en.check_schedules(old)                                            # the app refuses formats 1 and 2


def test_an_order_fills_exactly_when_the_clearing_price_is_at_or_below_the_cap():
    """gate H1: the price path is a display of the schedule's own outcome, never a second draw"""
    obj = ys.make3(120, 77)
    d = obj['design']
    cap, k = d['cap'], d['settlements_per_round']
    lo, hi = en.price_range(d)
    flo, fhi = en.price_range(d, obj['schedules'])
    assert lo <= flo < cap < fhi <= hi
    share = {True: [], False: []}
    for s in obj['schedules']:
        for r in range(en.n_rounds(d)):
            for good in (True, False):
                path, bits = en.price_path(s, d, r, good), en.own_bits(s, d, r, good)
                assert len(path) == k and all(round(p, 2) == p for p in path)
                assert [p <= cap for p in path] == [c == '1' for c in bits]
                assert flo <= min(path) and max(path) <= fhi
                if r >= d['rounds_rich']:
                    share[good].append(np.mean([p <= cap for p in path]))
            # one draw per clearing: the good's price and the other good's price move together
            a, b = en.price_path(s, d, 1, True), en.price_path(s, d, 1, False)
            assert np.corrcoef(a, b)[0, 1] > .95 and np.mean(np.array(a) < np.array(b)) > .97
    assert abs(np.mean(share[True]) - .25) < .01 and abs(np.mean(share[False]) - .10) < .01
    assert [en.baskets(g, d) for g in (0, 5, 6, 13)] == [0, 0, 1, 2]


def test_markets_are_common_to_a_file_and_evidence_follows_the_pair():
    obj = ys.make3(60, 5)
    d = obj['design']
    ms = obj['markets']
    assert [m['key'] for m in ms] == ['M1', 'M2', 'M3', 'M4'] and len({m['uid'] for m in ms}) == 4
    assert sum(m['favourable'] for m in ms) == 2 and len({m['asset'] for m in ms}) == 4
    for m in ms:
        assert m['chart'][-1] == m['threshold'] and len(m['chart']) == ys.CHART_POINTS      # the chart ends on the line
        assert m['chance'] == (.9 if m['favourable'] else .1) and m['uid'] == ys.market_uid(m)
        assert (m['close'] > m['threshold']) == en.market_closes_above(m)
        assert [en.bet_points(m, b, d) for b in ('PASS',)] == [d['bet_allowance']]
        won, lost = (20, 0) if en.market_closes_above(m) else (0, 20)
        assert (en.bet_points(m, 'YES', d), en.bet_points(m, 'NO', d)) == (won, lost)
        with pytest.raises(en.ScheduleError):
            en.bet_points(m, 'MAYBE', d)
    first = {}
    for s in obj['schedules']:
        got = [en.market_of(obj, s, i) for i in range(4)]
        assert sorted(g['key'] for g in got) == ['M1', 'M2', 'M3', 'M4']
        for g, tk in zip(got, s['probe']):
            assert (g['pair'], g['favourable'], g['shown'].count('1')) == (tk['pair'], tk['favourable'], 9 if tk['favourable'] else 1)
            assert g['evidence'] == ('source' if tk['record_of'] == 'other' else 'record')
            assert g['cue'] == ((90 if g['favourable'] else 10) if g['evidence'] == 'source' else None)
        by_pair = {}
        for g in got:
            by_pair.setdefault(g['pair'], []).append(g)
        assert all(len(v) == 2 and v[0]['favourable'] != v[1]['favourable'] and v[0]['evidence'] == v[1]['evidence']
                   for v in by_pair.values())
        assert {v[0]['evidence'] for v in by_pair.values()} == {'record', 'source'}
        first[got[0]['key']] = first.get(got[0]['key'], 0) + 1
    assert len(first) == 4                                                     # the order of the markets varies over schedules
    plain = ys.make3(10, 5, social=False)
    assert all(tk['evidence'] == 'record' and tk['cue'] is None for s in plain['schedules'] for tk in s['probe'])
    reuse = ys.make3(10, 99, markets=obj['markets'])
    assert reuse['markets'] == obj['markets'] and ys.verify(reuse)
    dear = json.loads(json.dumps(obj))
    dear['markets'][0]['price_yes'] = 30                                       # a NO ticket would cost 14 of a 10-point allowance
    with pytest.raises(en.ScheduleError):
        en.check_schedules(dear)


def test_bet_statistic_and_sources_from_a_pool():
    obj = ys.make3(30, 8)
    rng = np.random.default_rng(3)
    val = {'YES': 1, 'PASS': 0, 'NO': -1}
    for s in obj['schedules']:
        ms = [en.market_of(obj, s, i) for i in range(4)]
        bets = [en.BETS[i] for i in rng.integers(0, 3, 4)]
        d = {(m['pair'], m['favourable']): val[b] for m, b in zip(ms, bets)}
        assert en.bet_statistic(ms, bets) == ((d[0, True] - d[0, False]) / 2 + (d[1, True] - d[1, False]) / 2) / 2
    assert en.bet_statistic(ms, ['YES' if m['favourable'] else 'NO' for m in ms]) == 1
    m_up = next(m for m in obj['markets'] if m['favourable'])
    m_dn = next(m for m in obj['markets'] if not m['favourable'])
    src = lambda i, m, f, t: dict(id=f'x{i}', market_uid=m['uid'], forecast=f, right_others=t, others=3)
    pool = dict(sources=[src(1, m_up, 95, 3), src(2, m_up, 85, 3), src(3, m_up, 90, 2), src(4, m_up, 70, 3),
                         src(5, m_dn, 20, 1), src(6, m_dn, 5, 1), src(7, m_dn, 40, 3)])
    picks = {en.pool_source(pool, m_up, 1, sid)['id'] for sid in range(40)}
    assert picks == {'x1', 'x2'}                       # the best track record first, then nearest to 90: 95 and 85 tie
    assert en.pool_source(pool, m_dn, 1, 0)['id'] == 'x6'                      # 5 is nearer to 10 than 20
    assert en.pool_source(pool, m_up, 1, 7) == en.pool_source(pool, m_up, 1, 7)   # both members of a pair: same source
    with pytest.raises(en.ScheduleError):
        en.pool_source(dict(sources=[src(4, m_up, 70, 3)]), m_up, 1, 0)        # nothing inside the band
    with pytest.raises(en.ScheduleError):
        en.pool_source(dict(sources=[dict(file='old.csv', sha256='0')]), m_up, 1, 0)   # a format-1 pool has no forecasts


def test_probe_statistic_and_the_paid_forecast():
    obj = ys.make3(40, 3)
    rng = np.random.default_rng(5)
    for s in obj['schedules']:
        f = [(int(a), int(b)) for a, b in rng.integers(0, 21, (4, 2)) * 5]
        d = {(tk['pair'], tk['favourable']): post - pre for tk, (pre, post) in zip(s['probe'], f)}
        assert en.probe_T(s, f) == 0.5 * ((d[0, True] - d[0, False]) + (d[1, True] - d[1, False]))
        i, which, fc, out, won = en.paid_forecast(s, f)
        assert fc == f[i][0 if which == 'pre' else 1] and out == int(s['probe'][i]['score_u'] < s['probe'][i]['chance'])
        assert won == (s['prize_u'] < 1 - (out - fc / 100) ** 2)
    s = dict(obj['schedules'][0], prize_u=0.5, paid_forecast=0)
    s['probe'] = [dict(s['probe'][0], score_u=0.0, chance=0.9)] + s['probe'][1:]
    assert en.paid_forecast(s, [(100, 0)] + [(50, 50)] * 3)[4] is True          # a sure, correct forecast always wins
    assert en.paid_forecast(s, [(0, 0)] + [(50, 50)] * 3)[4] is False           # a sure, wrong forecast never wins


def test_pool_board_rules():
    obj = ys.make3(8, 9)
    d, k = obj['design'], obj['design']['settlements_per_round']
    rng = np.random.default_rng(2)
    mk = lambda i, r, p: dict(id=f's{i}', round=r, bits=''.join('1' if x else '0' for x in rng.random(k) < p))
    pool = dict(placeholder=False, streams=[mk(i, 0, .75) for i in range(30)] + [mk(100 + i, 0, .35) for i in range(10)]
                + [mk(1000 * r + i, r, p) for r in range(1, 6) for i, p in enumerate([.25] * 15 + [.10] * 15)])
    assert en.check_pool(pool, d, allow_placeholder=False)
    with pytest.raises(en.ScheduleError):
        en.check_pool(dict(pool, placeholder=True), d, allow_placeholder=False)
    s = next(x for x in obj['schedules'] if x['rich_board'] == 'HIGH')
    own = en.own_bits(s, d, 0, True)
    assert en.pool_board(pool, d, s, 0, 'HIGH', own, 1)[0] == en.pool_board(pool, d, s, 0, 'LOW', own, 1)[0]   # rich round: one record for the pair
    used = []
    for r in range(1, 6):
        own = en.own_bits(s, d, r, True)
        hi, _ = en.pool_board(pool, d, s, r, 'HIGH', own, 1, used)
        assert hi['round'] == 0 and .65 <= hi['bits'].count('1') / k <= .80 and hi['id'] not in used
        used.append(hi['id'])
        lo, dist = en.pool_board(pool, d, s, r, 'LOW', own, 1)
        best = min(abs(x['bits'].count('1') - own.count('1')) for x in pool['streams'] if x['round'] == r)
        assert lo['round'] == r and dist == best == abs(lo['bits'].count('1') - own.count('1'))
