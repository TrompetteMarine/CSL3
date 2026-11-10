"""I033 AD-O1: simulation-derived linear scores for the ten-round task (protocol
frozen in freezes/00_freeze_I033.yaml AD_O1 before running).
    python experiment/analysis/optimal_scores_I033.py > records/optimal_scores_I033.txt
"""
import sys
import numpy as np
sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
import stats_v2 as sv

NP, B, K, PH, SIG = 12000, 300, 25, (50, 125, 75), 5.8
NGRID = (40, 60, 80, 100, 130, 160, 200, 250)
NUF0, NUR0, SIG0 = mg.NUF, mg.NUR, dg.SIG_EPS
PTS = [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, .2918, .4),
       ('P3', .895, .25, .4), ('P4', 1.0, .25, .322)]


def sim(rng, kind, arm, chi, s=1.0, ratio=.25):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return dg.simulate_design(kind, NP, arm, rng, phases=PH, cadence=K, p2_odds=(.30, .15),
                                  chi=chi, resto_mix=(1, 0), reg3_fixed=(arm == 'HIGH'), choice_every=K)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


def ema(lat, e):
    x = lat['ratings'].astype(float); o = x.copy()
    for j in range(1, x.shape[1]):
        o[:, j] = o[:, j - 1] + e * (x[:, j] - o[:, j - 1])
    d = dict(lat); d['ratings'] = o.astype(np.float32); return d


def meas(rng, lat, a):
    dg.SIG_EPS = SIG
    try:
        f, e, keep = dg.measure_design(lat, 'M2', a, rng)
    finally:
        dg.SIG_EPS = SIG0
    return f[dg.screens_design(f, e, lat['acc1'], keep, PH[0])]


def pools(rng, a, rivals=False):
    out = {p[0]: (meas(rng, sim(rng, 'gate', 'HIGH', p[3], p[1], p[2]), a),
                  meas(rng, sim(rng, 'gate', 'LOW', p[3], p[1], p[2]), a)) for p in PTS}
    if rivals:
        for c in (.4, .6):
            h, l = sim(rng, 'rival_au', 'HIGH', c), sim(rng, 'rival_au', 'LOW', c)
            out[f'R3 {c}'] = (meas(rng, h, a), meas(rng, l, a))
            if c == .4:
                for e in (.22, .118):
                    out[f'R3-int {e}'] = (meas(rng, ema(h, e), a), meas(rng, ema(l, e), a))
        out['R4'] = (meas(rng, sim(rng, 'rival_us', 'HIGH', .6), a), meas(rng, sim(rng, 'rival_us', 'LOW', .6), a))
    return out


def power(rng, sh, sl, n):
    return np.mean([sv.wmw_one_sided(rng.choice(sh, n, replace=False), rng.choice(sl, n, replace=False))[0]
                    for _ in range(B)])


def nmin(c):
    for j, (n, p) in enumerate(zip(NGRID, c)):
        if p >= .9:
            return float(n) if j == 0 else NGRID[j - 1] + (.9 - c[j - 1]) * (n - NGRID[j - 1]) / (p - c[j - 1])
    return np.inf


# ---- training: weights at a = .5
rng = np.random.default_rng(133700)
tr = pools(rng, .5, rivals=True)
d = np.mean([tr[p[0]][1].mean(0) - tr[p[0]][0].mean(0) for p in PTS], axis=0)
Sig = np.mean([np.cov(tr[p[0]][i].T) for p in PTS for i in (0, 1)], axis=0)
Si = np.linalg.inv(Sig)
C = np.stack([tr[f'R3 {c}'][1].mean(0) - tr[f'R3 {c}'][0].mean(0) for c in (.4, .6)], axis=1)
w_a = Si @ d
w_b = Si @ (d - C @ np.linalg.solve(C.T @ Si @ C, C.T @ Si @ d))
w_drop = np.r_[np.full(2, .5), np.full(5, -.2), np.zeros(3)]          # P1 mean - P2 mean
norm = lambda w: w / np.abs(w).sum()
print("AD-O1 simulation-derived scores, ten-round task (weights trained at a=.5, seed 133700; test seed 133701)\n")
print("rounds:            " + " ".join(f"{j:6d}" for j in range(1, 11)) + "   (1-2 rich, 3-7 deprivation, 8-10 restoration)")
print("gate LOW-HIGH mean " + " ".join(f"{x:6.1f}" for x in d))
print("R3 (.4) LOW-HIGH   " + " ".join(f"{x:6.1f}" for x in C[:, 0]))
print("w_a (normalised)   " + " ".join(f"{x:6.2f}" for x in norm(w_a)))
print("w_b (normalised)   " + " ".join(f"{x:6.2f}" for x in norm(w_b)))

# ---- test
rng = np.random.default_rng(133701)
for a in (.25, .5, 1.0):
    te = pools(rng, a, rivals=True)
    print(f"\na = {a}: worst-inside-point power by n")
    res = {}
    for nm, w in (('P1-P2 drop', w_drop), ('S-a', w_a), ('S-b', w_b)):
        cur = [min(power(rng, te[p[0]][0] @ w, te[p[0]][1] @ w, n) for p in PTS) for n in NGRID]
        res[nm] = nmin(cur)
        print(f"  {nm:11s} " + " ".join(f"{n}:{c:.2f}" for n, c in zip(NGRID, cur)) + f"   n_min {res[nm]:.0f}")
    print("  S-b false positives (n=130 | n=250):")
    for r in ('R3 0.4', 'R3 0.6', 'R3-int 0.22', 'R3-int 0.118', 'R4'):
        print(f"    {r:14s} {power(rng, te[r][0] @ w_b, te[r][1] @ w_b, 130):.3f} | {power(rng, te[r][0] @ w_b, te[r][1] @ w_b, 250):.3f}")
    h3, l3, h4, l4 = te['R3 0.6'][0] @ w_b, te['R3 0.6'][1] @ w_b, te['R4'][0] @ w_b, te['R4'][1] @ w_b
    fp = []
    for n in (130, 250):
        r = 0
        for _ in range(B):
            k = rng.binomial(n, .5595, 2)
            xh = np.r_[rng.choice(h3, k[0], replace=False), rng.choice(h4, n - k[0], replace=False)]
            xl = np.r_[rng.choice(l3, k[1], replace=False), rng.choice(l4, n - k[1], replace=False)]
            r += sv.wmw_one_sided(xh, xl)[0]
        fp.append(r / B)
    print(f"    composite      {fp[0]:.3f} | {fp[1]:.3f}")
