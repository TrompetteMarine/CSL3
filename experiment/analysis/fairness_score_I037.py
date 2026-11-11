"""KGi-DISS-I037 part C: the fairness reference-effect score without the accuracy screen
(freeze 00_freeze_I037.yaml). Needs records/probe_design_I037_selected.json.
Training seed 134400, test seed 134401.
    python experiment/analysis/fairness_score_I037.py > records/fairness_score_I037.txt
"""
import json
import sys

import numpy as np

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
import probe_generator as pg
import stats_v2 as sv
from probe_design_I037 import ODDS, P1TAG, chi_min

NP, SIG, B = 12000, 5.8, 400
NUF0, NUR0, SIG0 = mg.NUF, mg.NUR, dg.SIG_EPS
sel = json.load(open('records/probe_design_I037_selected.json'))


def pts_for(p2, mu_ref=.65):
    return [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, .2918, .4), ('P3', .895, .25, .4),
            ('P4', 1.0, .25, chi_min(p2, mu_ref))]


def cell(rng, kind, arm, phases, k, p2, chi, a, nrate, s=1.0, ratio=.25, old_screen=False, p1='p65'):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    dg.SIG_EPS = SIG
    try:
        lat = dg.simulate_design(kind, NP, arm, rng, phases=phases, cadence=k, p1_odds=P1TAG[p1][0], p2_odds=p2,
                                 mu_ref=P1TAG[p1][1], chi=chi, resto_mix=(1, 0), reg3_fixed=(arm == 'HIGH'),
                                 choice_every=k)
        f, e, keep = dg.measure_design(lat, 'M2', a, rng)
    finally:
        mg.NUF, mg.NUR, dg.SIG_EPS = NUF0, NUR0, SIG0
    ok = keep & ~((f.var(axis=1) == 0) & (e.var(axis=1) == 0))          # zero-variance screen only
    if old_screen:
        return (ok & (lat['acc1'] >= .5 + 2 * np.sqrt(.25 / phases[0]))).mean() / ok.mean()
    return f[ok][:, :nrate]


def power(rng, sh, sl, n):
    return np.mean([sv.wmw_one_sided(rng.choice(sh, n, replace=False), rng.choice(sl, n, replace=False))[0]
                    for _ in range(B)])


print("KGi-DISS-I037 part C: fairness scores without the accuracy screen (train 134400, test 134401)\n")
d = sel['S1x'] if ('S1x' in sel and sel['S1x']['n'] < sel['S1']['n']) else sel['S1']   # the certified design (AD-B3)
CASES = [('ten-round design 2/5/3, 25 draws (AD-O1 erratum)', (50, 125, 75), 25, ODDS['std'], 10, 'p65'),
         (f"certified probe design {d['r1']}+{d['r2']} rounds, {d['k']} draws, {d['odds']}, {d.get('p1', 'p65')}",
          (d['r1'] * d['k'], d['r2'] * d['k'], d['k']), d['k'], ODDS[d['odds']], d['r1'] + d['r2'], d.get('p1', 'p65'))]
for name, phases, k, p2, nrate, p1 in CASES:
    pts = pts_for(p2, P1TAG[p1][1])
    _cell = cell
    cell = lambda *a, _c=_cell, _p=p1, **kw: _c(*a, p1=_p, **kw)
    tr = np.random.default_rng(134400)
    kept = np.mean([cell(tr, 'gate', arm, phases, k, p2, .4, .5, nrate, old_screen=True) for arm in ('HIGH', 'LOW')])
    H = {p[0]: cell(tr, 'gate', 'HIGH', phases, k, p2, p[3], .5, nrate, p[1], p[2]) for p in pts}
    L = {p[0]: cell(tr, 'gate', 'LOW', phases, k, p2, p[3], .5, nrate, p[1], p[2]) for p in pts}
    dvec = np.mean([L[p[0]].mean(0) - H[p[0]].mean(0) for p in pts], axis=0)
    Sig = np.mean([np.cov(X[p[0]].T) for p in pts for X in (H, L)], axis=0)
    Si = np.linalg.inv(Sig)
    w_a = Si @ dvec
    R3 = [cell(tr, 'rival_au', 'LOW', phases, k, p2, c, .5, nrate).mean(0) -
          cell(tr, 'rival_au', 'HIGH', phases, k, p2, c, .5, nrate).mean(0) for c in (.4, .6)]
    C = np.stack(R3, axis=1)
    w_b = Si @ (dvec - C @ np.linalg.solve(C.T @ Si @ C, C.T @ Si @ dvec))
    print(f"=== {name}: {nrate} fairness ratings; the old accuracy screen would keep {kept:.2f} of participants")
    te = np.random.default_rng(134401)
    for a in (.25, .5, 1.0):
        res = {}
        for nm, w in (('S-a', w_a), ('S-b', w_b)):
            th = min(pg.theta(cell(te, 'gate', 'HIGH', phases, k, p2, p[3], a, nrate, p[1], p[2]) @ w,
                              cell(te, 'gate', 'LOW', phases, k, p2, p[3], a, nrate, p[1], p[2]) @ w) for p in pts)
            res[nm] = pg.n_asymptotic(th)
        line = f"  gain {a}: n per arm  S-a {res['S-a']:.0f}   S-b {res['S-b']:.0f}"
        if a == .5:
            n = int(np.ceil(res['S-a']))
            pw = min(power(te, cell(te, 'gate', 'HIGH', phases, k, p2, p[3], a, nrate, p[1], p[2]) @ w_a,
                           cell(te, 'gate', 'LOW', phases, k, p2, p[3], a, nrate, p[1], p[2]) @ w_a, n) for p in pts)
            line += f"   (Monte Carlo power of S-a at n = {n}: {pw:.3f})"
        print(line, flush=True)
    cell = _cell
    print()
