"""From the oTree app's export to the reporting set (KGi-DISS-I042, I043).

Reads the custom export of experiment/diss_market (one 'repetition' row per participant and
repetition, one 'participant' row each) and scores it with yoked_analysis.decisions, the code
of the I041 certification. Pairs are the two participants who share a schedule; only complete
pairs enter (both finished).

Added in I043: the bet statistic B (mean over the two market pairs of the bet on the
favourable market minus the bet on the unfavourable one, halved; YES = 1, pass = 0, NO = -1)
and the decision BET (signed rank within pairs of B_LOW - B_HIGH, one-sided .005), as in
basket_cert_I043.py; and T split by kind of evidence (record pair, source pair).

    python experiment/analysis/yoked_from_export.py path/to/diss_market_custom.csv
"""
import csv
import json
import sys

import numpy as np

sys.path.insert(0, 'experiment/analysis')
import yoked_analysis as ya  # noqa: E402

N_MARKET, FAIR = 6, ('fair1', 'fair2', 'fair3')


def probe_T(rows):
    """T = mean over the two pairs of (revision after the favourable record minus revision
    after the unfavourable one), from the probe rows of one participant"""
    d = {}
    for r in rows:
        d.setdefault(int(r['probe_pair']), {})[r['probe_favourable'] == '1'] = int(r['forecast_post']) - int(r['forecast_pre'])
    return float(np.mean([p[True] - p[False] for p in d.values()]))


BET_VALUE = {'YES': 1, 'PASS': 0, 'NO': -1}


def bet_B(rows):
    d = {}
    for r in rows:
        d.setdefault(int(r['probe_pair']), {})[r['probe_favourable'] == '1'] = BET_VALUE[r['bet']]
    return float(np.mean([(p[True] - p[False]) / 2 for p in d.values()]))


def T_by_evidence(rows):
    """revision after the favourable minus after the unfavourable market, by kind of evidence"""
    d = {}
    for r in rows:
        d.setdefault((r['evidence'], r['probe_pair']), {})[r['probe_favourable'] == '1'] = \
            int(r['forecast_post']) - int(r['forecast_pre'])
    out = {}
    for (kind, _), v in d.items():
        if set(v) == {True, False}:
            out.setdefault(kind, []).append(v[True] - v[False])
    return {k: float(np.mean(v)) for k, v in out.items()}


def load(path, config=None, session=None):
    """participants keyed by code: arm, schedule, slot, per-round arrays, T. An export holds
    every session of the database: config and session keep the ones wanted."""
    parts = {}
    with open(path, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if (config and r['config'] != config) or (session and r['session'] != session):
                continue
            p = parts.setdefault(r['participant'], dict(rows=[], final=None))
            if r['row_type'] == 'repetition':
                p['rows'].append(r)
            else:
                p['final'] = r
    out = {}
    for code, p in parts.items():
        market = sorted((r for r in p['rows'] if r['kind'] == 'market'), key=lambda r: int(r['repetition']))
        probe = sorted((r for r in p['rows'] if r['kind'] == 'probe'), key=lambda r: int(r['repetition']))
        fin = p['final']
        done = (fin is not None and fin['finished'] == '1' and len(market) == N_MARKET and len(probe) == 4
                and all(r[k] != '' for r in market for k in FAIR + ('entitle',))
                and all(r['forecast_pre'] != '' and r['forecast_post'] != '' and r['bet'] in BET_VALUE for r in probe))
        base = (market or probe or [fin])[0]
        rec = dict(arm=base['arm'], schedule=int(base['schedule']), slot=int(base['slot']), session=base['session'],
                   complete=done)
        if done:
            k = len(market[0]['own_bits'])
            rec.update(fair=np.array([np.mean([int(r[x]) for x in FAIR]) for r in market]),
                       entitle=np.array([int(r['entitle']) for r in market], float),
                       win_share=np.array([int(r['wins']) / k for r in market]),
                       T=probe_T(probe), T_stored=float(fin['probe_T']), k=k,
                       B=bet_B(probe), B_stored=float(fin['bet_stat']), T_by=T_by_evidence(probe),
                       forecasts=[(int(r['forecast_pre']), int(r['forecast_post'])) for r in probe])
        out[code] = rec
    return out


def pairs(parts):
    """complete yoked pairs: (HIGH member, LOW member) by schedule, in schedule order"""
    by = {}
    for p in parts.values():
        if p['complete']:
            by.setdefault((p['session'], p['schedule']), {})[p['arm']] = p
    return [(v['HIGH'], v['LOW']) for _, v in sorted(by.items()) if set(v) == {'HIGH', 'LOW'}]


def arrays(pr, seed=0):
    """the inputs of yoked_analysis.decisions for one data set (one replicate)"""
    rng = np.random.default_rng(seed)
    hi, lo = [h for h, _ in pr], [l for _, l in pr]
    col = lambda ps, f: np.array([f(p) for p in ps])[None]
    return dict(fh=col(hi, lambda p: p['fair'][-1]), fl=col(lo, lambda p: p['fair'][-1]),
                eh=col(hi, lambda p: p['entitle'][-1]), el=col(lo, lambda p: p['entitle'][-1]),
                th=col(hi, lambda p: p['T']), tl=col(lo, lambda p: p['T']),
                fl_rounds=col(lo, lambda p: p['fair'][2:6]), wl=col(lo, lambda p: p['win_share'][3:6]),
                jit=rng.uniform(-.01, .01, (1, len(pr))))


def score(path, seed=0, config=None, session=None):
    parts = load(path, config, session)
    pr = pairs(parts)
    d = ya.decisions(arrays(pr, seed))
    out = {k: (bool(v[0]) if v.dtype == bool else float(v[0])) for k, v in d.items()}
    bh, bl = np.array([h['B'] for h, _ in pr])[None], np.array([l['B'] for _, l in pr])[None]
    out.update(BET=bool(ya.signed_rank_z(bl - bh)[0] > ya.ZC), mean_B_high=float(bh.mean()), mean_B_low=float(bl.mean()))
    for kind in ('record', 'source'):
        hk = [h['T_by'][kind] for h, _ in pr if kind in h['T_by']]
        lk = [l['T_by'][kind] for _, l in pr if kind in l['T_by']]
        if hk and lk:
            out[f'mean_T_{kind}_high'], out[f'mean_T_{kind}_low'] = float(np.mean(hk)), float(np.mean(lk))
    out.update(pairs=len(pr), participants=len(parts), complete=sum(p['complete'] for p in parts.values()),
               mean_T_high=float(np.mean([h['T'] for h, _ in pr])), mean_T_low=float(np.mean([l['T'] for _, l in pr])),
               mean_fair_high=float(np.mean([h['fair'][-1] for h, _ in pr])),
               mean_fair_low=float(np.mean([l['fair'][-1] for _, l in pr])))
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('export')
    ap.add_argument('--config', default=None)
    ap.add_argument('--session', default=None)
    a = ap.parse_args()
    print(json.dumps(score(a.export, config=a.config, session=a.session), indent=1))
