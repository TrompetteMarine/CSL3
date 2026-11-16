"""Fidelity of the oTree task engine to the certified design (KGi-DISS-I042, gates G1, G2).
Run from the repository root."""
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
    obj = ys.make2(200, 42)
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
    obj = ys.make2(50, 7)
    d = obj['design']
    for s in obj['schedules']:
        ch = [True] * en.n_rounds(d)
        (own_h, board_h), (own_l, board_l) = play(obj, s, 'HIGH', ch), play(obj, s, 'LOW', ch)
        assert own_h == own_l                                                  # same tickets, same outcomes
        assert board_h[0] == board_l[0]                                        # same board in the rich round
        assert board_h[1:] != board_l[1:]


def test_format_2_keeps_format_1_and_the_example_file():
    a, b = ys.make(6, 11), ys.make2(6, 11)
    for sa, sb in zip(a['schedules'], b['schedules']):
        assert all(sa[k] == sb[k] for k in ('id', 'rich_board', 'good', 'bad', 'board'))
        assert all({k: p2[k] for k in p1} == p1 for p1, p2 in zip(sa['probe'], sb['probe']))
    assert a['allocation'] == b['allocation'] and a['design'] == b['design']
    ex = json.load(open(os.path.join(EXP, 'schedules', 'example_seed0_4pairs_v2.json')))
    assert ex == json.loads(json.dumps(ys.make2(4, 0)))
    with pytest.raises(en.ScheduleError):
        en.check_schedules(a)                                                  # the app refuses format 1


def test_probe_statistic_and_the_paid_forecast():
    obj = ys.make2(40, 3)
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
    obj = ys.make2(8, 9)
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
