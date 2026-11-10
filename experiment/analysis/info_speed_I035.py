"""I035: information on the gate speed s in the ten-round task (freeze
00_freeze_I035.yaml, written before running).
    python experiment/analysis/info_speed_I035.py > records/info_speed_I035.txt
"""
import sys
import numpy as np
sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
NP, SIG, SE = 20000, 5.8, .0635
NUF0, NUR0, SIG0 = mg.NUF, mg.NUR, dg.SIG_EPS
TH0 = dict(s=.895, ratio=.25, chi=.4, a=.5)
STEP = dict(s=.1, ratio=.03, chi=.08, a=.05)
CELLS = {'HM': ('HIGH', (1, 0)), 'LM': ('LOW', (1, 0)), 'HF': ('HIGH', (0, 1)), 'LF': ('LOW', (0, 1))}
DESIGNS = [('D1 2/5/3 k25 two cells', (2, 5, 3), 25, (.30, .15), ('HM', 'LM')),
           ('D2 2/5/3 k25 four cells', (2, 5, 3), 25, (.30, .15), ('HM', 'LM', 'HF', 'LF')),
           ('D3 1/6/3 k25 four cells', (1, 6, 3), 25, (.30, .15), ('HM', 'LM', 'HF', 'LF')),
           ('D4 2/6/2 k25 four cells', (2, 6, 2), 25, (.30, .15), ('HM', 'LM', 'HF', 'LF')),
           ('D5 2/5/3 k40 four cells', (2, 5, 3), 40, (.30, .15), ('HM', 'LM', 'HF', 'LF')),
           ('D6 2/5/3 k25 P2 .25/.10 four cells', (2, 5, 3), 25, (.25, .10), ('HM', 'LM', 'HF', 'LF'))]


def ratings(th, cell, rounds, k, p2, seed):
    rng = np.random.default_rng(seed)            # common random numbers across perturbations
    arm, resto = CELLS[cell]
    mg.NUF, mg.NUR = NUF0 * th['s'], NUF0 * th['s'] * th['ratio']
    dg.SIG_EPS = SIG
    try:
        lat = dg.simulate_design('gate', NP, arm, rng, phases=tuple(k * r for r in rounds), cadence=k,
                                 p2_odds=p2, chi=th['chi'], resto_mix=resto, reg3_fixed=(arm == 'HIGH'),
                                 choice_every=k)
        f, _, _ = dg.measure_design(lat, 'M2', th['a'], rng)
    finally:
        mg.NUF, mg.NUR, dg.SIG_EPS = NUF0, NUR0, SIG0
    return f


print("I035 information on gate speed s (edge point s .895, ratio .25, chi .4, gain .5; target SE .0635)\n")
print(f"{'design':38s} {'n/cell, nuisances known':>24s} {'n/cell, nuisances unknown':>27s} {'total humans (unknown)':>23s}  corr(s, gain)")
for name, rounds, k, p2, cells in DESIGNS:
    J = np.zeros((4, 4))
    for ci, c in enumerate(cells):
        seed = 134000 + 17 * ci
        f0 = ratings(TH0, c, rounds, k, p2, seed)
        Si = np.linalg.inv(np.cov(f0.T))
        D = np.empty((10, 4))
        for j, p in enumerate(('s', 'ratio', 'chi', 'a')):
            up, dn = dict(TH0), dict(TH0)
            up[p] += STEP[p]; dn[p] -= STEP[p]
            D[:, j] = (ratings(up, c, rounds, k, p2, seed).mean(0) - ratings(dn, c, rounds, k, p2, seed).mean(0)) / (2 * STEP[p])
        J += D.T @ Si @ D
    Ji = np.linalg.inv(J)
    known, unk = 1 / (J[0, 0] * SE ** 2), Ji[0, 0] / SE ** 2
    print(f"{name:38s} {known:24.0f} {unk:27.0f} {unk * len(cells):23.0f}  {Ji[0, 3] / np.sqrt(Ji[0, 0] * Ji[3, 3]):+.2f}", flush=True)
