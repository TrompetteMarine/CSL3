"""I036 analysis (freeze 00_freeze_I036.yaml): census table from records/bgt.csv,
mean-field logit-conformity fixed points, and the evidence-uptake probe.
    python experiment/analysis/bgt_I036.py > records/bgt_I036.txt
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg

sig = lambda x: 1 / (1 + np.exp(-x))
print("KGi-DISS-I036 behavioural game theory analysis\n")

# ---------------------------------------------------------------- census
d = pd.read_csv('records/bgt.csv')
d['choice'] = np.where(d.m2 < .3, 'wrong', np.where(d.m2 > .7, 'correct', 'mixed'))
d['trust'] = np.where(d.l2 >= .3, 'trusting', 'distrusting')
print("A. End states of community 2 (300 runs per cell; share of runs)")
print(f"{'cell':40s} {'wrong+distrust':>14s} {'wrong+trust':>12s} {'correct+trust':>14s} {'correct+distrust':>17s} {'mixed':>6s}")
for name, g in d.groupby('cell', sort=False):
    f = lambda c, t: ((g.choice == c) & (g.trust == t)).mean()
    print(f"{name:40s} {f('wrong','distrusting'):14.3f} {f('wrong','trusting'):12.3f} {f('correct','trusting'):14.3f} "
          f"{f('correct','distrusting'):17.3f} {(g.choice == 'mixed').mean():6.3f}")

# ---------------------------------------------------------------- mean field
def fixed_points(dq, lam, gam, beta=12.0, f1=1.0):
    p = np.linspace(1e-6, 1 - 1e-6, 200001)
    g = sig(beta * (dq + lam * ((1 - gam) * (2 * p - 1) * np.abs(2 * p - 1) + gam * f1))) - p
    idx = np.flatnonzero(np.sign(g[:-1]) != np.sign(g[1:]))
    return [(p[i], 'stable' if g[i] > 0 else 'unstable') for i in idx]

print("\nB. Mean-field logit-conformity equilibria of community 2 (other community on the better option)")
for lam, gam in ((.7, .1), (.3, .1), (.7, 0.0), (.7, .3)):
    crit = None
    for dq in np.arange(-.3, 1.0001, .005):
        if not any(s == 'stable' and p < .5 for p, s in fixed_points(dq, lam, gam)):
            crit = dq; break
    out = []
    for dq in (-.24, 0.0, .2):
        fp = fixed_points(dq, lam, gam)
        out.append(f"dQ={dq:+.2f}: " + ", ".join(f"{p:.3f} ({s})" for p, s in fp))
    print(f"  lambda={lam} Gamma={gam}: wrong-consensus equilibrium exists for dQ < {crit:.3f}")
    for o in out:
        print("      " + o)

# ---------------------------------------------------------------- probe
print("\nC. Evidence-uptake probe after the deprivation rounds (forecast revision; noise sd 12 per report)")
rng = np.random.default_rng(134100)
NUF0, NUR0 = mg.NUF, mg.NUR
PTS = [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, .2918, .4), ('P3', .895, .25, .4), ('P4', 1.0, .25, .322)]
LEV, SD = .4, 12.0
for dname, k, p2 in (('k 25', 25, (.30, .15)), ('k 40', 40, (.30, .15)), ('k 40, P2 .25/.10', 40, (.25, .10))):
    Ls = {}
    for name, s, ratio, chi in PTS:
        mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
        try:
            for arm in ('HIGH', 'LOW'):
                lat = dg.simulate_design('gate', 12000, arm, rng, phases=(2 * k, 5 * k, 3 * k), cadence=k,
                                         p2_odds=p2, chi=chi, resto_mix=(1, 0), reg3_fixed=(arm == 'HIGH'), choice_every=k)
                Ls[(name, arm)] = lat['ratings'][:, 6].astype(float)
        finally:
            mg.NUF, mg.NUR = NUF0, NUR0
    print(f"  design {dname}: legitimacy at end of round 7, HIGH / LOW mean: " +
          "  ".join(f"{n} {Ls[(n,'HIGH')].mean():.2f}/{Ls[(n,'LOW')].mean():.2f}" for n, *_ in PTS))
    for m in (3, 5, 7, 10):
        res = []
        for probes in (1, 3):
            worst = np.inf
            for name, *_ in PTS:
                wh = 1 - (1 - .2 * Ls[(name, 'HIGH')]) ** m
                wl = 1 - (1 - .2 * Ls[(name, 'LOW')]) ** m
                diff = 100 * LEV * (wl.mean() - wh.mean())
                var = 2 * SD ** 2 / probes + .5 * ((100 * LEV) ** 2) * (wh.var() + wl.var())
                worst = min(worst, diff / np.sqrt(var))
            res.append((worst, 2 * (3.858 / worst) ** 2))
        print(f"      m={m:2d} draws shown: one probe d={res[0][0]:.2f} n/arm {res[0][1]:5.0f} | three probes d={res[1][0]:.2f} n/arm {res[1][1]:5.0f}")
