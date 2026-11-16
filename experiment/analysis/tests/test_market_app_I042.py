"""The oTree app end to end, with bots (KGi-DISS-I042, gates G3, G4, G9). Each bot session
runs 'otree test' in a fresh copy of the project, so no other database is touched.
Run from the repository root. The 72-pair session takes a few minutes."""
import csv
import importlib.util
import json
import os
import random
import shutil
import statistics as st
import subprocess
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(EXP, 'tools'))
sys.path.insert(0, os.path.join(EXP, 'analysis'))
import make_board_pool as mp  # noqa: E402
import yoked_from_export as yx  # noqa: E402
import yoked_schedules as ys  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(EXP, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


en = _load('dm_engine_app', 'diss_market/engine.py')
bm = _load('dm_bots_model', 'diss_market/bots_model.py')
OTREE = shutil.which('otree')
pytestmark = pytest.mark.skipif(OTREE is None, reason='oTree is not installed')


@pytest.fixture(scope='module')
def project(tmp_path_factory):
    dst = tmp_path_factory.mktemp('otree') / 'experiment'
    shutil.copytree(EXP, dst, ignore=shutil.ignore_patterns(
        'node_modules', 'db.sqlite3', '__pycache__', 'botdata', 'analysis', 'frontend', '_generated', '.env'))
    return dst


def bots(project, config, n, out, **env):
    """one bot session; returns the rows of the app's custom export"""
    db = project / 'db.sqlite3'
    if db.exists():
        db.unlink()
    e = {k: v for k, v in os.environ.items() if not k.startswith('OTREE_')}
    e.update({k: str(v) for k, v in env.items()})
    r = subprocess.run([OTREE, 'test', config, str(n), f'--export={out}'], cwd=project, env=e, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    return list(csv.DictReader(open(os.path.join(out, 'diss_market_custom.csv'), encoding='utf-8-sig')))


def by_participant(rows):
    d = {}
    for r in rows:
        d.setdefault(r['participant'], []).append(r)
    return d


def check_against_schedule(rows, obj):
    """every stored settlement and board record is what the schedule and the engine give"""
    d = obj['design']
    for code, rs in by_participant(rows).items():
        market = sorted((r for r in rs if r['kind'] == 'market'), key=lambda r: int(r['repetition']))
        probe = sorted((r for r in rs if r['kind'] == 'probe'), key=lambda r: int(r['repetition']))
        fin = [r for r in rs if r['row_type'] == 'participant']
        assert len(market) == 6 and len(probe) == 4 and len(fin) == 1, code
        assert all(r[k] != '' for r in market for k in ('fair1', 'fair2', 'fair3', 'entitle'))
        assert sum((r['forecast_pre'] != '') + (r['forecast_post'] != '') for r in probe) == 8
        s = en.schedule_by_id(obj, int(market[0]['schedule']))
        arm, hist = market[0]['arm'], ''
        slot = next(a for a in obj['allocation'] if a['slot'] == int(market[0]['slot']))
        assert slot['schedule'] == s['id'] and slot['arm'] == arm
        for r, row in enumerate(market):
            good = row['chose_good'] == '1'
            assert (row['ticket'] == s['good_ticket']) == good
            own = en.own_bits(s, d, r, good)
            assert row['own_bits'] == own and int(row['wins']) == own.count('1')
            if row['board_source'] == 'schedule':
                assert row['board_bits'] == en.board_bits(s, d, r, arm, hist, own)
                assert row['board_regime'] == (s['rich_board'] if r == 0 else arm)
            assert row['rate_inits'] == ','.join(str(x) for x in s['starts'][r])
            hist += own
        for i, row in enumerate(probe):
            tk = s['probe'][i]
            assert (row['probe_symbol'], row['probe_shown'], row['probe_record_of']) == (tk['symbol'], tk['shown'], tk['record_of'])
        f = [(int(r['forecast_pre']), int(r['forecast_post'])) for r in probe]
        assert abs(float(fin[0]['probe_T']) - en.probe_T(s, f)) < 1e-9
        i, which, fc, outcome, won = en.paid_forecast(s, f)
        assert (int(fin[0]['paid_ticket']), fin[0]['paid_which'], int(fin[0]['paid_forecast'])) == (i, which, fc)
        pts = sum(int(r['wins']) for r in market) + sum(int(r['probe_points']) for r in probe) + (20 if won else 0)
        assert int(fin[0]['points_total']) == pts and int(fin[0]['prize_won']) == int(won)


def test_random_bots_store_exactly_what_the_schedule_says(project, tmp_path):
    obj = json.load(open(os.path.join(EXP, 'schedules', 'example_seed0_4pairs_v2.json')))
    rows = bots(project, 'market_bots_random', 10, tmp_path)              # ten arrivals for eight slots
    parts = by_participant(rows)
    assert len(parts) == 8                                               # the two without a slot never start
    assert sorted(int(rs[0]['slot']) for rs in parts.values()) == list(range(8))
    check_against_schedule(rows, obj)
    assert all(int(r['cq_attempts']) == 2 for r in rows if r['row_type'] == 'participant')


def test_bot_kernel_through_the_engine_matches_the_certification():
    """the gate kernel, played on the app's engine, gives the simulation's latent values"""
    obj = ys.make2(1500, 4242)
    d, rng = obj['design'], random.Random(1)
    L, T, same = {'HIGH': [], 'LOW': []}, {'HIGH': [], 'LOW': []}, 0
    for s in obj['schedules']:
        ch = {}
        for arm in en.ARMS:
            ag = bm.ModelAgent(seed=rng.getrandbits(40), slow=rng.random() < .5, point='P1', rule='event')
            hist, picks = '', []
            for r in range(6):
                good = ag.choose_good()
                own = en.own_bits(s, d, r, good)
                ag.observe(good, own, en.board_bits(s, d, r, arm, hist, own), en.board_regime(s, d, r, arm))
                hist += own
                picks.append(good)
            ch[arm] = picks[1:]
            L[arm].append(ag.L)
            T[arm].append(en.probe_T(s, [ag.forecasts(tk['shown'].count('1') / 10) for tk in s['probe']]))
        same += ch['HIGH'] == ch['LOW']
    assert abs(st.mean(L['HIGH']) - .109) < .02 and abs(st.mean(L['LOW']) - .869) < .02     # records/yoked_cert_I041.txt, section 0
    assert abs(same / len(obj['schedules']) - .13) < .04
    assert abs(st.mean(T['HIGH']) / st.mean(T['LOW']) - .125) < .05


def test_gate_bots_at_72_pairs_give_the_confirmatory_pair(project, tmp_path):
    sched = tmp_path / 'bots72.json'
    obj = ys.make2(72, 42)
    json.dump(obj, open(sched, 'w'))
    rows = bots(project, 'market_bots_model', 144, tmp_path / 'out', MARKET_SCHEDULE=sched)
    check_against_schedule(rows, obj)
    path = os.path.join(tmp_path / 'out', 'diss_market_custom.csv')
    parts = yx.load(path)
    assert len(parts) == 144 and all(p['complete'] for p in parts.values())
    assert all(abs(p['T'] - p['T_stored']) < 1e-9 for p in parts.values())          # T from the export = T stored
    pr = yx.pairs(parts)
    assert len(pr) == 72 and all(h['schedule'] == l['schedule'] for h, l in pr)
    res = yx.score(path)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in res.items()})
    assert res['H1a'] and res['D1'] and res['PAIR'] and not res['PHI']
    assert res['mean_fair_high'] < 40 < 60 < res['mean_fair_low']


def test_seed_wave_feeds_a_pool_and_the_pool_fills_the_board(project, tmp_path):
    sched = tmp_path / 'seed.json'
    obj = ys.make2(16, 5)
    json.dump(obj, open(sched, 'w'))
    seed_rows = bots(project, 'market_bots_seed', 32, tmp_path / 'seed', MARKET_SCHEDULE=sched)
    assert all(r['board_bits'] == '' and r['board_source'] == 'none' for r in seed_rows if r['kind'] == 'market')
    check_against_schedule(seed_rows, obj)
    export = os.path.join(tmp_path / 'seed', 'diss_market_custom.csv')
    assert mp.build([export])['streams'] == []                                       # bot records are refused …
    pool = mp.build([export], allow_bots=True)                                       # … unless asked for, as a placeholder
    assert pool['placeholder'] and len(pool['streams']) == 32 * 6 and mp.HIGH_BAND == en.HIGH_BAND
    assert mp.report(pool)['high_band_records'] >= 6
    pool_path = tmp_path / 'pool.json'
    json.dump(pool, open(pool_path, 'w'))
    rows = bots(project, 'market_bots_pool', 16, tmp_path / 'pilot', MARKET_SCHEDULE=sched, MARKET_POOL=pool_path)
    check_against_schedule(rows, obj)
    by_id = {s['id']: s for s in pool['streams']}
    k = obj['design']['settlements_per_round']
    for r in (r for r in rows if r['kind'] == 'market'):
        s = by_id[r['board_stream']]
        assert r['board_bits'] == s['bits'] and r['board_source'] == 'pool'
        if r['board_regime'] == 'HIGH':
            assert s['round'] == 0 and en.HIGH_BAND[0] <= s['bits'].count('1') / k <= en.HIGH_BAND[1]
        else:
            assert s['round'] == int(r['repetition']) - 1
            assert int(r['board_dist']) == abs(s['bits'].count('1') - int(r['wins']))
    low = [int(r['board_dist']) for r in rows if r['kind'] == 'market' and r['board_regime'] == 'LOW']
    print('LOW board, distance to own count: median', np.median(low), 'max', max(low))
    # a human session in production refuses a placeholder pool and the computer-generated board
    e = dict(OTREE_PRODUCTION='1', OTREE_ADMIN_PASSWORD='x', OTREE_SECRET_KEY='not-the-dev-key')
    for config, extra in (('market_pilot', dict(MARKET_POOL=str(pool_path))), ('market_dev', {})):
        env = {**os.environ, **e, 'MARKET_SCHEDULE': str(sched), **extra}
        r = subprocess.run([OTREE, 'create_session', config, '2'], cwd=project, env=env, capture_output=True, text=True)
        assert r.returncode != 0 and ('never shown to people' in r.stdout + r.stderr), (config, r.stdout[-800:], r.stderr[-800:])


def test_the_earlier_app_still_runs_its_bots(project, tmp_path):
    db = project / 'db.sqlite3'
    if db.exists():
        db.unlink()
    r = subprocess.run([OTREE, 'test', 'bots_random_HIGH_FULL'], cwd=project, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]


def test_the_bundle_is_built_from_the_sources_in_the_repository():
    import hashlib
    man = json.load(open(os.path.join(EXP, '_static', 'diss_market', 'build-manifest.json')))
    for rel, sha in man['sources'].items():
        assert hashlib.sha256(open(os.path.join(EXP, 'frontend', rel), 'rb').read()).hexdigest() == sha, f'{rel} changed since the bundle was built: run npm run build'
    for rel, o in man['outputs'].items():
        assert hashlib.sha256(open(os.path.join(EXP, '_static', 'diss_market', rel), 'rb').read()).hexdigest() == o['sha256'], rel
