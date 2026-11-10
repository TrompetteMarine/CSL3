"""I034: is the gate outside the span of the slow-reporting utility family once
full-restoration cells are added? (freeze 00_freeze_I034.yaml, written before running)
    python experiment/analysis/span_identification_I034.py > records/span_identification_I034.txt
"""
import sys
import numpy as np
from scipy.stats import norm
sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg

rng = np.random.default_rng(133800)
NP, K, PH, SIG, A = 12000, 25, (50, 125, 75), 5.8, .5
NUF0, NUR0, SIG0 = mg.NUF, mg.NUR, dg.SIG_EPS
PTS = [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, .2918, .4),
       ('P3', .895, .25, .4), ('P4', 1.0, .25, .322)]
CELLS = [('HM', 'HIGH', (1, 0)), ('LM', 'LOW', (1, 0)), ('HF', 'HIGH', (0, 1)), ('LF', 'LOW', (0, 1))]


def cellmeans(kind, chi, s=1.0, ratio=.25, e=None):
    mus, covs = [], []
    for _, arm, resto in CELLS:
        mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
        try:
            lat = dg.simulate_design(kind, NP, arm, rng, phases=PH, cadence=K, p2_odds=(.30, .15), chi=chi,
                                     resto_mix=resto, reg3_fixed=(arm == 'HIGH'), choice_every=K)
        finally:
            mg.NUF, mg.NUR = NUF0, NUR0
        if e is not None:
            x = lat['ratings'].astype(float)
            for j in range(1, x.shape[1]):
                x[:, j] = x[:, j - 1] + e * (x[:, j] - x[:, j - 1])
            lat = dict(lat); lat['ratings'] = x.astype(np.float32)
        dg.SIG_EPS = SIG
        try:
            f, en, keep = dg.measure_design(lat, 'M2', A, rng)
        finally:
            dg.SIG_EPS = SIG0
        f = f[dg.screens_design(f, en, lat['acc1'], keep, PH[0])]
        mus.append(f.mean(0)); covs.append(np.cov(f.T))
    return np.concatenate(mus), covs


I = np.eye(10); Z = np.zeros((10, 10))
KFULL = np.block([[I, -I, Z, Z], [Z, Z, I, -I], [I, Z, -I, Z]])
KMOD = np.block([[I, -I, Z, Z]])

gate = {p[0]: cellmeans('gate', p[3], p[1], p[2]) for p in PTS}
Sig = [np.mean([gate[p[0]][1][c] for p in PTS], axis=0) for c in range(4)]
V = np.zeros((40, 40))
for c in range(4):
    V[10 * c:10 * c + 10, 10 * c:10 * c + 10] = Sig[c]
span = [cellmeans('rival_au', c)[0] for c in (.4, .6)] + [cellmeans('rival_us', .6)[0]]
span += [cellmeans('rival_au', c, e=e)[0] for e in (.5, .35, .22, .118, .06) for c in (.4, .6)]
held = {f"R3-int e={e} chi={c}": cellmeans('rival_au', c, e=e)[0] for e in (.3, .15, .09) for c in (.4, .6)}
gbar = np.mean([gate[p[0]][0] for p in PTS], axis=0)

print("I034 span identification (seed 133800; gain .5; ten rounds; n per cell)\n")
for name, Kc in (('(a) MOD cells only: HM-LM', KMOD), ('(b) MOD + FULL cells: HM-LM, HF-LF, HM-HF', KFULL)):
    V1 = Kc @ V @ Kc.T + 1e-9 * np.eye(Kc.shape[0])
    Vi = np.linalg.inv(V1)
    C = np.stack([Kc @ m for m in span], axis=1)
    U, sv, _ = np.linalg.svd(C, full_matrices=False)
    Ct = U[:, sv > .5] * sv[sv > .5]
    g = Kc @ gbar
    w = Vi @ (g - Ct @ np.linalg.solve(Ct.T @ Vi @ Ct, Ct.T @ Vi @ g))
    sd = np.sqrt(w @ V1 @ w)
    w_plain = Vi @ g
    print(f"{name}: contrast dim {Kc.shape[0]}, rival span rank kept {Ct.shape[1]}")
    zs = {p[0]: (w @ (Kc @ gate[p[0]][0])) / sd for p in PTS}
    zp = {p[0]: (w_plain @ (Kc @ gate[p[0]][0])) / np.sqrt(w_plain @ V1 @ w_plain) for p in PTS}
    zmin = min(zs.values())
    nmin = (3.858 / zmin) ** 2 if zmin > 0 else np.inf
    print("  per-participant noncentrality, span-orthogonal test: " + "  ".join(f"{k} {v:.3f}" for k, v in zs.items()))
    print(f"  (unconstrained best score, for reference: worst point {min(zp.values()):.3f} -> n {(3.858 / min(zp.values())) ** 2:.0f})")
    print(f"  n_min per cell (worst inside point): {nmin:.0f}")
    if np.isfinite(nmin):
        n = min(nmin, 2000)
        for k, m in held.items():
            z = (w @ (Kc @ m)) / sd
            print(f"    held-out {k}: false-positive probability at n={n:.0f}: {norm.cdf(z * np.sqrt(n) - 2.576):.3f}")
    print()
