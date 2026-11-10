"""Exploratory (pre-I035; not a certification). Question, written before running:
how much of the between-participant variance of the frozen scores is predictable
WITHOUT humans, from (i) each participant's own realised win counts per round
(observable, model-free covariate; linear regression within arm) and (ii) the
gate simulator run on that participant's realised outcomes (oracle upper bound:
knows the rigidity type)? Covariate adjustment with such a prediction keeps the
randomised test valid and cuts the needed n by about the factor (1 - R^2).
Ten-round task, three-item scale, M2, theory point P1; weights re-derived as in
AD-O1 (S-a) at gain .5. Seed 133900.
    python experiment/analysis/abm_substitution_I035pre.py > records/abm_substitution_I035pre.txt
"""
import sys
import numpy as np
sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
rng = np.random.default_rng(133900)
NP, K, PH, SIG = 20000, 25, (50, 125, 75), 5.8
SIG0 = dg.SIG_EPS


def cell(arm, a):
    lat = dg.simulate_design('gate', NP, arm, rng, phases=PH, cadence=K, p2_odds=(.30, .15), chi=.4,
                             resto_mix=(1, 0), reg3_fixed=(arm == 'HIGH'), choice_every=K, trace=True)
    dg.SIG_EPS = SIG
    try:
        f, e, keep = dg.measure_design(lat, 'M2', a, rng)
    finally:
        dg.SIG_EPS = SIG0
    ok = dg.screens_design(f, e, lat['acc1'], keep, PH[0])
    wins = lat['R'].reshape(NP, 10, K).sum(2).astype(float)
    peer = lat['peer'].reshape(NP, 10, K).sum(2).astype(float)
    return f[ok], 100 * lat['ratings'][ok].astype(float), wins[ok], peer[ok]


def r2(y, X):
    X1 = np.c_[np.ones(len(X)), X]
    h = len(y) // 2                      # fit on one half, evaluate on the other
    b = np.linalg.lstsq(X1[:h], y[:h], rcond=None)[0]
    res = y[h:] - X1[h:] @ b
    return 1 - res.var() / y[h:].var()


H, L = cell('HIGH', .5), cell('LOW', .5)
d = L[0].mean(0) - H[0].mean(0)
Sig = .5 * (np.cov(H[0].T) + np.cov(L[0].T))
w = np.linalg.solve(Sig, d)
print("ABM substitution, exploratory (seed 133900): share of score variance predictable without humans")
print(f"{'gain':>5s} {'arm':>5s} {'R2 own win counts':>18s} {'R2 wins + board':>16s} {'R2 simulator oracle':>20s}")
for a in (.25, .5, 1.0):
    for arm in ('HIGH', 'LOW'):
        f, lat, wins, peer = cell(arm, a)
        s = f @ w
        print(f"{a:5.2f} {arm:>5s} {r2(s, wins):18.3f} {r2(s, np.c_[wins, peer]):16.3f} {r2(s, (lat @ w)[:, None]):20.3f}")
