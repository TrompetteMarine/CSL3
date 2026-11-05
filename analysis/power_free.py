#!/usr/bin/env python3
"""I029 distribution-free power engine (frozen battery in 00_freeze_I029.yaml).

Monte Carlo power for the H1a contrast (P1->P2 fairness drop, HIGH vs LOW) under
six generative shapes violating normal theory, for (i) one-sided WMW rank-sum and
(ii) one-sided Welch t (level protected at analysis time by its studentized-
permutation implementation; power well-approximated by the plain statistic).
Effects are injected as location shifts tau calibrated PER SHAPE so that the
Mann-Whitney theta = P(X > Y) hits the frozen anchors -- never via Cohen d.

Also provides pilot-time functions: plug-in bootstrap power from an empirical
sample with exclusion screens applied inside the resampling, and a double
bootstrap correcting small-pilot optimism. Deterministic under SEED.
"""
import numpy as np
from scipy import stats

SEED = 113000
ALPHA = 0.005  # one-sided
THETAS = {"floor(.570)": 0.570, "basis(.592)": 0.592, "strong(.625)": 0.625}
NGRID = [200, 240, 280, 320, 360, 420, 480]
B = 4000  # MC replicates per cell

def round5(x):
    return np.round(x / 5.0) * 5.0

# ---- frozen shapes: baseline (LOW-arm) drop distributions -----------------------
def s1(rng, n):   # truncated normal
    return np.clip(rng.normal(25, 20, n), -40, 90)
def s2(rng, n):   # zero-inflated censored rounded
    z = rng.random(n) < 0.15
    x = round5(np.clip(rng.normal(25, 20, n), 0, 90))
    x[z] = 0.0
    return x
def s3(rng, n):   # attention mixture (non-responders carry no effect; see shift())
    return None   # handled in draw_pair
def s4(rng, n):   # heavy tails
    return 25 + 15 * rng.standard_t(3, n)
def s5(rng, n):   # right skew
    return 25 + 12 * (rng.lognormal(0, 0.8, n) - np.exp(0.32))

SHAPES = ["S1", "S2", "S3", "S4", "S5", "S6"]

def draw_pair(shape, rng, n, tau):
    """LOW and HIGH samples of size n; tau = location shift on the responsive part."""
    if shape in ("S3", "S6"):
        def arm(shift):
            resp = rng.random(n) >= 0.20
            x = np.where(resp, rng.normal(25 + shift, 15, n), rng.normal(0, 8, n))
            return x, resp
        xl, rl = arm(0.0)
        xh, rh = arm(tau)
        if shape == "S6":
            # exclusion screens: remove 12%, enriched in non-responders
            # (non-responders 3x as likely to fail screens)
            def keep(x, resp):
                p_ex = np.where(resp, 0.075, 0.30)
                return x[rng.random(n) >= p_ex]
            return keep(xl, rl), keep(xh, rh)
        return xl, xh
    f = {"S1": s1, "S2": s2, "S4": s4, "S5": s5}[shape]
    base = f(rng, n)
    high = f(rng, n) + tau
    if shape == "S2":
        high = round5(np.clip(high, 0, 90 + 40))  # re-round after shift; cap drift
    return base, high

def theta_of_tau(shape, tau, rng, n=120000):
    xl, xh = draw_pair(shape, rng, n, tau)
    m = min(len(xl), len(xh))
    xl, xh = xl[:m], xh[:m]
    # P(X_H > X_L) + .5 P(=) by comparing random pairs
    perm = rng.permutation(m)
    gt = (xh > xl[perm]).mean()
    eq = (xh == xl[perm]).mean()
    return gt + 0.5 * eq

def calibrate_tau(shape, theta_target, rng):
    lo, hi = 0.0, 40.0
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        th = theta_of_tau(shape, mid, rng)
        if th < theta_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

def wmw_reject(x, y, alpha=ALPHA):
    """One-sided (y stochastically larger): normal approx with tie correction."""
    n1, n2 = len(x), len(y)
    allv = np.concatenate([x, y])
    ranks = stats.rankdata(allv)
    u = ranks[n1:].sum() - n2 * (n2 + 1) / 2.0
    mu = n1 * n2 / 2.0
    _, cnt = np.unique(allv, return_counts=True)
    tiecorr = 1.0 - (cnt**3 - cnt).sum() / ((n1 + n2)**3 - (n1 + n2))
    sd = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0 * tiecorr)
    z = (u - mu) / sd
    return z > stats.norm.ppf(1 - alpha)

def welch_reject(x, y, alpha=ALPHA):
    t, p = stats.ttest_ind(y, x, equal_var=False, alternative="greater")
    return p < alpha

def power_cell(shape, tau, n, rng):
    rw = rt = 0
    for _ in range(B):
        xl, xh = draw_pair(shape, rng, n, tau)
        rw += wmw_reject(xl, xh)
        rt += welch_reject(xl, xh)
    return rw / B, rt / B

# ---- pilot-time machinery (executed at pilot time; defined and frozen now) ------
def bootstrap_power(pilot_drops, tau, n, alpha=ALPHA, B1=4000, rng=None):
    """Plug-in power: resample pilot empirical distribution, inject shift tau."""
    rng = rng or np.random.default_rng(SEED + 7)
    rej = 0
    for _ in range(B1):
        xl = rng.choice(pilot_drops, n, replace=True)
        xh = rng.choice(pilot_drops, n, replace=True) + tau
        rej += wmw_reject(xl, xh, alpha)
    return rej / B1

def double_bootstrap_power(pilot_drops, tau, n, B_outer=200, B_inner=800, rng=None):
    """Optimism-corrected: outer resamples of the pilot itself; report mean and
    the 10th percentile of the plug-in power distribution (planning value)."""
    rng = rng or np.random.default_rng(SEED + 11)
    vals = []
    m = len(pilot_drops)
    for _ in range(B_outer):
        p = rng.choice(pilot_drops, m, replace=True)
        vals.append(bootstrap_power(p, tau, n, B1=B_inner, rng=rng))
    v = np.array(vals)
    return v.mean(), np.percentile(v, 10)

if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    print("shape,theta_label,tau,N_per_arm,power_WMW,power_Welch")
    nstar = {}
    for shape in SHAPES:
        for lab, th in THETAS.items():
            tau = calibrate_tau(shape, th, rng)
            for n in NGRID:
                pw, pt = power_cell(shape, tau, n, rng)
                print(f"{shape},{lab},{tau:.2f},{n},{pw:.3f},{pt:.3f}", flush=True)
                if lab == "basis(.592)" and pw >= 0.90 and (shape, "wmw") not in nstar:
                    nstar[(shape, "wmw")] = n
                if lab == "basis(.592)" and pt >= 0.90 and (shape, "welch") not in nstar:
                    nstar[(shape, "welch")] = n
    print("\nN*(0.90) at theta=.592:")
    for k, v in sorted(nstar.items()):
        print(k, v)
