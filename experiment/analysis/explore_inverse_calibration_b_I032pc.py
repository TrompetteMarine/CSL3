"""POST-I032 EXPLORATORY, part b (written AFTER reading part a's output for
P0-P3; NOT a certification; any adopted form needs I033 freeze + fresh seeds).

Part a found the MODERATE flatline (and so H1b-SIe / H1b-BA) vanishes at the
ABM ratio edge (nuR/nuF = .29): the gate recovers +8.3 there, like R3 (+8.8),
yet relative to the depth it reached (P1 - end-of-P2 = 50.1) that is a small
fraction (.17) against R3's .61. SIe normalised recovery by the P2-MEAN drop,
which understates the gate's depth (its collapse is unfinished within P2).

Questions, written before this run:
Qb1 Depth-normalised form H1b-SId: in HIGH x MODERATE with the reference held
    fixed (P3 regime = arm), c_i = rec_end_i - kappa * depth_i, depth = P1 mean
    - mean of the last 4 P2 ratings, rec_end = late-P3 mean - that same end-P2
    mean; above-median-depth half; one-sided signed rank at .005; n = 213.
    kappa from the theory region, rule fixed here: kappa = midpoint of
    (max over inside points P0-P4 of the gate's latent fraction mean(rec_end)/
    mean(depth)) and (min over the same points of R3's fraction).
Qb2 Power across points P0-P5 and gains a in {1,.5,.35,.25,.15,.1}.
Qb3 Specificity (false positives): R3; integrating R3 (EMA eta .01, .005 of R3's
    latent trust, measured after filtering); the no-gate composite of I032 AD4
    (R3 share .5595, rest R4), drawn per replicate. Unconditional on H1a.
B = 400 subsample replicates; 60k/arm latent pools. Seed 133000.
Run from the repo root (needs records/invcal.csv):
    python experiment/analysis/explore_inverse_calibration_b_I032pc.py > records/inverse_calibration_b_I032pc.txt
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import stats_v2 as sv

rng = np.random.default_rng(133000)
NPOOL, B, NCELL = 60000, 400, 213
END = slice(56, 60)
A_GRID = (1.0, .5, .35, .25, .15, .1)
P_OWN, MU_REF, R3_SHARE = .27, .65, .5595
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
POINTS = [('P0 paper', 1.0, .25, .6, True), ('P1 ABM chi', 1.0, .25, .4, True),
          ('P2 ratio edge', 1.0, r_star, .4, True), ('P3 speed edge', s_star, .25, .4, True),
          ('P4 anchor edge', 1.0, .25, chi_min(.25), True),
          ('P5 joint corner*', s_star, r_star, chi_min(r_star), False)]


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


def cell_idx(lat):          # HIGH x MODERATE with P3 regime HIGH (reference fixed)
    return np.flatnonzero((~lat['resto_full']) & lat['reg3'])


def latent_frac(lat):
    L = 100 * lat['ratings'].astype(float)
    i = cell_idx(lat)
    endp2 = L[i][:, END].mean(1)
    depth = L[i][:, 0:30].mean(1) - endp2
    rec = L[i][:, mg.LATE_IDX].mean(1) - endp2
    return rec.mean() / depth.mean(), rec.mean(), depth.mean()


def measured(lat, a):
    f, e, keep = mg.measure(lat, 'M2', a, rng)
    ok = mg.screens(f, e, lat['acc1'], keep)
    endp2 = f[:, END].mean(1)
    depth = f[:, 0:30].mean(1) - endp2
    rec = f[:, mg.LATE_IDX].mean(1) - endp2
    idx = np.intersect1d(cell_idx(lat), np.flatnonzero(ok))
    return depth, rec, idx


def sid(depth, rec, kappa, cond=True):
    if cond:
        top = depth > np.median(depth)
        depth, rec = depth[top], rec[top]
    return sv._signed_rank_less(rec - kappa * depth, .005)[0]


def power(depth, rec, idx, kappa):
    r1 = r2 = 0
    for _ in range(B):
        sub = rng.choice(idx, NCELL, replace=False)
        r1 += sid(depth[sub], rec[sub], kappa)
        r2 += sid(depth[sub], rec[sub], kappa, cond=False)
    return r1 / B, r2 / B


def power_composite(m3, m4, kappa):
    (d3, c3, i3), (d4, c4, i4) = m3, m4
    r = 0
    for _ in range(B):
        k3 = rng.binomial(NCELL, R3_SHARE)
        a = rng.choice(i3, k3, replace=False); b = rng.choice(i4, NCELL - k3, replace=False)
        r += sid(np.concatenate([d3[a], d4[b]]), np.concatenate([c3[a], c4[b]]), kappa)
    return r / B


print("POST-I032 exploratory inverse calibration, part b (seed 133000)\n")
gate, r3 = {}, {}
for name, s, ratio, chi, inside in POINTS:
    gate[name] = sim('gate', 'HIGH', chi, s, ratio)
    key = round(chi, 4)
    if key not in r3:
        r3[key] = sim('rival_au', 'HIGH', chi)
fr_g = {n: latent_frac(gate[n]) for n, *_ in POINTS}
fr_r = {round(c, 4): latent_frac(r3[round(c, 4)]) for *_, c, _ in POINTS}
inside = [p for p in POINTS if p[4]]
gmax = max(fr_g[p[0]][0] for p in inside)
rmin = min(fr_r[round(p[3], 4)][0] for p in inside)
kappa = .5 * (gmax + rmin)
print("latent HIGH x MOD (reference fixed): fraction = rec_end/depth  (rec_end, depth)")
for name, s, ratio, chi, ins in POINTS:
    g, q = fr_g[name], fr_r[round(chi, 4)]
    print(f"  {name:18s} gate {g[0]:+.3f} ({g[1]:+.1f}, {g[2]:.1f})   R3 {q[0]:+.3f} ({q[1]:+.1f}, {q[2]:.1f})")
print(f"kappa rule: max gate fraction (inside) = {gmax:+.3f}; min R3 fraction (inside) = {rmin:+.3f}; "
      f"kappa = {kappa:.3f}\n")

r4_pool = sim('rival_us', 'HIGH', .6)          # R4 ignores the peer; chi irrelevant
print("H1b-SId power (above-median-depth | unconditional), n = 213, alpha .005")
print(f"{'a':>6s} " + " ".join(f"{p[0][:14]:>15s}" for p in POINTS))
for a in A_GRID:
    row = []
    for name, *_ in POINTS:
        pw = power(*measured(gate[name], a), kappa)
        row.append(f"{pw[0]:6.2f} |{pw[1]:5.2f}")
    print(f"{a:6.3f} " + " ".join(f"{x:>15s}" for x in row))

print("\nfalse positives of H1b-SId (above-median-depth | unconditional)")
rivals = [('R3 chi .6', r3[.6]), ('R3 chi .4', r3[.4]),
          ('R3-int .01 chi .4', ema_lat(r3[.4], .01)), ('R3-int .005 chi .4', ema_lat(r3[.4], .005)),
          ('R3-int .01 chi .6', ema_lat(r3[.6], .01)), ('R3-int .005 chi .6', ema_lat(r3[.6], .005))]
for nm, lat in rivals:
    fr = latent_frac(lat)
    out = []
    for a in (1.0, .35, .15):
        pw = power(*measured(lat, a), kappa)
        out.append(f"a={a:g}: {pw[0]:.3f}|{pw[1]:.3f}")
    print(f"  {nm:20s} latent frac {fr[0]:+.3f} (rec {fr[1]:+.1f}, depth {fr[2]:.1f})   " + "  ".join(out))
fr4 = latent_frac(r4_pool)
print(f"  R4 alone: latent frac {fr4[0]:+.3f} (rec {fr4[1]:+.1f}, depth {fr4[2]:.1f})")
for chi in (.6, .4):
    out = []
    for a in (1.0, .35, .15):
        out.append(f"a={a:g}: {power_composite(measured(r3[chi], a), measured(r4_pool, a), kappa):.3f}")
    print(f"  composite R3({chi})+R4, above-median-depth: " + "  ".join(out))
