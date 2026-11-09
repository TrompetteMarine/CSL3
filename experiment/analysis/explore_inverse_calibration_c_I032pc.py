"""POST-I032 EXPLORATORY, part c (written AFTER reading part b; NOT a
certification).

Part b: the depth-normalised H1b-SId (kappa = .364 from the theory-region rule,
records/inverse_calibration_b_I032pc.txt) is powered at every theory point at
a >= .5, but conditioning on above-median measured depth costs power at low gain
(ratio edge .72 at a=.25, .01 at a=.15) while the unconditional form is not
specific against a slow integrating-utility rival (eta=.005: .84-1.00 at a=1).
Mechanism suspected: depth and rec_end share the end-of-P2 ratings (and P1), so
selecting high measured depth selects favourable noise -> regression to the mean
inflates the selected subjects' recovery.

Questions, written before this run (kappa fixed at .364):
Qc1 SId-S, split-sample conditioning: select on depth_sel = mean(P1 ratings
    0:15) - mean(P2 ratings 50:56), above median; test on c = (late-P3 - endP2)
    - kappa*(mean(P1 ratings 15:30) - endP2), endP2 = ratings 56:60. Selection
    and test use disjoint ratings. One-sided signed rank .005, n = 213.
Qc2 SId-BA, between arms: unconditional c (P1 = ratings 0:30) in HIGH x MOD
    (P3 HIGH) vs LOW x MOD (P3 LOW), one-sided WMW .005 (gate: HIGH lower),
    n = 213/arm. Composite-proof by randomisation if rivals are arm-symmetric.
Qc3 Power at P0-P5, a in {1,.5,.35,.25,.15,.1}; false positives for R3
    (chi .6, .4), R3-int (eta .01, .005; chi .4, .6) and the I032 AD4 composite
    (R3 share .5595 + R4, same mixture in both arms) at a in {1,.35,.15}.
B = 400; 60k/arm pools. Seed 133010. Run from the repo root:
    python experiment/analysis/explore_inverse_calibration_c_I032pc.py > records/inverse_calibration_c_I032pc.txt
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import stats_v2 as sv

rng = np.random.default_rng(133010)
NPOOL, B, NCELL, KAPPA, R3_SHARE = 60000, 400, 213, .364, .5595
A_GRID = (1.0, .5, .35, .25, .15, .1)
P_OWN, MU_REF = .27, .65
NUF0, NUR0 = mg.NUF, mg.NUR


def crossing(x, y, level=.5):
    for i in range(len(x) - 1):
        if (y[i] - level) * (y[i + 1] - level) <= 0 and y[i] != y[i + 1]:
            return x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i])
    return np.nan


def chi_min(ratio):
    return (.3 + ratio * P_OWN / (1 - P_OWN) - P_OWN) / (MU_REF - P_OWN)


inv = pd.read_csv('records/invcal.csv')
ps, pr = inv[inv.part == 's'].sort_values('s'), inv[inv.part == 'ratio'].sort_values('ratio')
s_star, r_star = crossing(ps.s.values, ps.p_dw.values), crossing(pr.ratio.values, pr.p_dw.values)
POINTS = [('P0 paper', 1.0, .25, .6), ('P1 ABM chi', 1.0, .25, .4),
          ('P2 ratio edge', 1.0, r_star, .4), ('P3 speed edge', s_star, .25, .4),
          ('P4 anchor edge', 1.0, .25, chi_min(.25)), ('P5 corner*', s_star, r_star, chi_min(r_star))]


def sim(kind, arm, chi, s=1.0, ratio=.25):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return mg.simulate_latent(kind, NPOOL, arm, rng, chi=chi)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


def ema_lat(lat, eta):
    x = lat['ratings'].astype(np.float64)
    e5 = 1 - (1 - eta) ** 5
    out = np.empty_like(x)
    out[:, 0] = x[:, 0]
    for k in range(1, x.shape[1]):
        out[:, k] = out[:, k - 1] + e5 * (x[:, k] - out[:, k - 1])
    d = dict(lat)
    d['ratings'] = out.astype(np.float32)
    return d


def measured(lat, a, arm):
    f, e, keep = mg.measure(lat, 'M2', a, rng)
    ok = mg.screens(f, e, lat['acc1'], keep)
    end = f[:, 56:60].mean(1)
    late = f[:, mg.LATE_IDX].mean(1)
    sel = f[:, 0:15].mean(1) - f[:, 50:56].mean(1)
    c_split = (late - end) - KAPPA * (f[:, 15:30].mean(1) - end)
    c_full = (late - end) - KAPPA * (f[:, 0:30].mean(1) - end)
    reg = lat['reg3'] if arm == 'HIGH' else ~lat['reg3']
    idx = np.flatnonzero(ok & (~lat['resto_full']) & reg)
    return sel, c_split, c_full, idx


def sids(m, sub):
    sel, cs, _, _ = m
    top = sel[sub] > np.median(sel[sub])
    return sv._signed_rank_less(cs[sub][top], .005)[0]


def run(mh, ml):
    r1 = r2 = 0
    for _ in range(B):
        sh = rng.choice(mh[3], NCELL, replace=False)
        sl = rng.choice(ml[3], NCELL, replace=False)
        r1 += sids(mh, sh)
        r2 += sv.wmw_one_sided(mh[2][sh], ml[2][sl])[0]
    return r1 / B, r2 / B


def run_composite(m3h, m4h, m3l, m4l):
    r1 = r2 = 0
    for _ in range(B):
        out = []
        for m3, m4 in ((m3h, m4h), (m3l, m4l)):
            k3 = rng.binomial(NCELL, R3_SHARE)
            a = rng.choice(m3[3], k3, replace=False); b = rng.choice(m4[3], NCELL - k3, replace=False)
            out.append((np.concatenate([m3[0][a], m4[0][b]]), np.concatenate([m3[1][a], m4[1][b]]),
                        np.concatenate([m3[2][a], m4[2][b]])))
        (selh, csh, cfh), (_, _, cfl) = out
        top = selh > np.median(selh)
        r1 += sv._signed_rank_less(csh[top], .005)[0]
        r2 += sv.wmw_one_sided(cfh, cfl)[0]
    return r1 / B, r2 / B


print(f"POST-I032 exploratory inverse calibration, part c (seed 133010; kappa = {KAPPA})\n")
print("power: SId-S (split-sample conditioning) | SId-BA (between arms), n = 213/arm, alpha .005")
print(f"{'a':>6s} " + " ".join(f"{p[0][:14]:>15s}" for p in POINTS))
pools = {p[0]: (sim('gate', 'HIGH', p[3], p[1], p[2]), sim('gate', 'LOW', p[3], p[1], p[2])) for p in POINTS}
for a in A_GRID:
    row = []
    for p in POINTS:
        h, l = pools[p[0]]
        pw = run(measured(h, a, 'HIGH'), measured(l, a, 'LOW'))
        row.append(f"{pw[0]:5.2f} |{pw[1]:5.2f}")
    print(f"{a:6.3f} " + " ".join(f"{x:>15s}" for x in row))

print("\nfalse positives: SId-S | SId-BA")
r3 = {chi: (sim('rival_au', 'HIGH', chi), sim('rival_au', 'LOW', chi)) for chi in (.6, .4)}
r4 = (sim('rival_us', 'HIGH', .6), sim('rival_us', 'LOW', .6))
rivals = [('R3 chi .6', r3[.6]), ('R3 chi .4', r3[.4])]
for eta in (.01, .005):
    for chi in (.4, .6):
        rivals.append((f"R3-int {eta} chi {chi}", (ema_lat(r3[chi][0], eta), ema_lat(r3[chi][1], eta))))
for nm, (h, l) in rivals:
    out = []
    for a in (1.0, .35, .15):
        pw = run(measured(h, a, 'HIGH'), measured(l, a, 'LOW'))
        out.append(f"a={a:g}: {pw[0]:.3f}|{pw[1]:.3f}")
    print(f"  {nm:20s} " + "  ".join(out))
for chi in (.6, .4):
    out = []
    for a in (1.0, .35, .15):
        pw = run_composite(measured(r3[chi][0], a, 'HIGH'), measured(r4[0], a, 'HIGH'),
                           measured(r3[chi][1], a, 'LOW'), measured(r4[1], a, 'LOW'))
        out.append(f"a={a:g}: {pw[0]:.3f}|{pw[1]:.3f}")
    print(f"  composite R3({chi})+R4  " + "  ".join(out))
