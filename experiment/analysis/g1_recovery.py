"""KGi-DISS-I032 — gate G1: synthetic rho recovery on the MARKET-SKINNED task.

Re-establishes the I003 identification result (slider-instrumented individual
rho, r = .91) under three design-mandated changes (freeze I032, D5/D6 + AD2):
task-v3 phase geometry (P3 = MODERATE .45/.35 or FULL .65/.35, mixed 2:1
instead of recovery_v3's (.70,.45)); APP windfall semantics (+3 points on top
of a normal trial, non-evidential — no R:=1 override, no skipped Q-update);
and the market frame's measurement model on both sliders (0-100 scale,
additive N(0,10) per rating, rounded to multiples of 5, clipped).

Cohort (AD2 = the I003 sampling design): n = 60 synthetic gate subjects, full
DISS parameter vector sampled from recovery_v3.MODELS['DISS']['sample']
(rho ~ U(.002,.05), chi ~ U(.2,.6)); P1/P3 regimes iid HIGH/LOW, P2 regime
HIGH/LOW alternating (both arms represented). Fit: DISS MAP (frozen weak
priors), L+A rating quasi-likelihood (Gaussian sigma=.10 on the 0-1 scale,
unchanged under rounding — stated), 6 Nelder-Mead starts.

Gate G1 PASSES iff pearson r(rho_hat, rho_true) >= .7. The I003 group-level
bias profile (nuF, tauF group-mean bias with bootstrap CIs; nuR bias) is
recomputed for comparison; a changed nuR picture is a surprise to report.

Seed 132100. Output records/g1_recovery_I032.csv + stdout summary.
"""
import csv
import os
import sys

import numpy as np
from scipy import stats
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

SEED = 132100
N_SUBJ = 60
T = 450
RATE_EVERY = 5
SIGR = 0.10                       # rating quasi-likelihood SD (0-1 scale)
PHIM, PHIP = 1.0, 0.25
MU_FULL = np.zeros((T, 2))
MU_FULL[:150] = (.65, .35); MU_FULL[150:300] = (.30, .15); MU_FULL[300:] = (.65, .35)
MU_MOD = MU_FULL.copy(); MU_MOD[300:] = (.45, .35)

# frozen DISS priors/ranges (recovery_v3.MODELS['DISS'], ported verbatim)
PRIOR_MU = np.array([.25, 6.5, .06, .0175, .30, .026, .40])
PRIOR_SD = np.array([.30, 7.0, .08, .025, .30, .048, .40])


def sample_theta(r):
    return np.array([r.uniform(.1, .4), r.uniform(3, 10), r.uniform(.02, .10),
                     r.uniform(.005, .03), r.uniform(.15, .45),
                     r.uniform(.002, .05), r.uniform(.2, .6)])


def in_bounds(t):
    return (0 < t[0] < 1 and 0 < t[1] < 30 and 0 <= t[2] < .5 and
            0 <= t[3] < .2 and 0 <= t[4] < 1 and 0 < t[5] < .5 and 0 <= t[6] <= 1)


def round5_clip(x, rng):
    """Market measurement on the 0-1 scale: +N(0,.10), round to .05, clip."""
    r = x + rng.normal(0, SIGR)
    return min(1.0, max(0.0, round(r * 20) / 20.0))


def generate(theta, regimes, mu, rng):
    """One subject, task-v3 market skin, app windfall semantics (windfalls are
    +points only; every trial is a normal Bernoulli trial)."""
    al, bs, nuF, nuR, tauF, rho, chi = theta
    Q = np.array([.5, .5]); L, A = 1.0, 0.5
    own_trail = 0.5
    ch = np.empty(T, np.int8); rw = np.empty(T); refs = np.empty(T)
    Lr, Ar = [], []
    for t in range(T):
        p1 = 1 / (1 + np.exp(-bs * (Q[0] - Q[1])))
        a = 0 if rng.random() < p1 else 1
        R = float(rng.random() < mu[t, a])
        pr = 0.65 if regimes[t // 150] == 'high' else min(.95, max(.05, own_trail))
        Rref = float(rng.random() < pr)
        own_trail = 0.98 * own_trail + 0.02 * R
        # DISS step (recovery_v3 order: D from pre-update A)
        D = PHIM * max(A - R, 0) + PHIP * max(R - A, 0)
        Q[a] = min(1, max(0, Q[a] + al * L * (R - Q[a])))
        L = min(1, max(0, L - nuF * max(D - tauF, 0) + nuR * (D <= tauF)))
        A = min(1, max(0, (1 - rho) * A + rho * ((1 - chi) * R + chi * Rref)))
        ch[t], rw[t], refs[t] = a, R, Rref
        if (t + 1) % RATE_EVERY == 0:
            Lr.append(round5_clip(L, rng))
            Ar.append(round5_clip(A, rng))
    return ch, rw, refs, np.array(Lr), np.array(Ar)


def nll(theta, ch, rw, refs, Lr, Ar, map_prior=True):
    if not in_bounds(theta):
        return 1e9
    al, bs, nuF, nuR, tauF, rho, chi = theta
    Q = np.array([.5, .5]); L, A = 1.0, 0.5
    ll = 0.0; ri = 0
    for t in range(T):
        p1 = 1 / (1 + np.exp(-bs * (Q[0] - Q[1])))
        p = p1 if ch[t] == 0 else 1 - p1
        ll += np.log(max(p, 1e-12))
        R, Rref = rw[t], refs[t]
        D = PHIM * max(A - R, 0) + PHIP * max(R - A, 0)
        a = ch[t]
        Q[a] = min(1, max(0, Q[a] + al * L * (R - Q[a])))
        L = min(1, max(0, L - nuF * max(D - tauF, 0) + nuR * (D <= tauF)))
        A = min(1, max(0, (1 - rho) * A + rho * ((1 - chi) * R + chi * Rref)))
        if (t + 1) % RATE_EVERY == 0:
            ll += -0.5 * ((Lr[ri] - L) / SIGR) ** 2
            ll += -0.5 * ((Ar[ri] - A) / SIGR) ** 2
            ri += 1
    out = -ll
    if map_prior:
        out += float((0.5 * ((theta - PRIOR_MU) / PRIOR_SD) ** 2).sum())
    return out


def fit(ch, rw, refs, Lr, Ar, rng, starts=6):
    best = (np.inf, None)
    for _ in range(starts):
        x0 = sample_theta(rng)
        try:
            res = minimize(lambda x: nll(x, ch, rw, refs, Lr, Ar), x0,
                           method='Nelder-Mead',
                           options=dict(maxiter=2500, xatol=1e-4, fatol=1e-3))
            if res.fun < best[0]:
                best = (res.fun, res.x)
        except Exception:
            pass
    return best


def main():
    rng = np.random.default_rng(SEED)
    pyr = np.random.default_rng(SEED + 1)
    rows = [("subj", "p2_regime", "resto", "rho_true", "rho_hat",
             "nuF_true", "nuF_hat", "tauF_true", "tauF_hat",
             "nuR_true", "nuR_hat", "chi_true", "chi_hat", "nll")]
    import random as pyrandom
    for s in range(N_SUBJ):
        r = pyrandom.Random(SEED + 10 + s)
        theta = sample_theta(r)
        p2 = 'high' if s % 2 == 0 else 'own'
        regimes = ['high' if r.random() < .5 else 'own', p2,
                   'high' if r.random() < .5 else 'own']
        mu = MU_MOD if s % 3 != 2 else MU_FULL          # 2:1 MODERATE:FULL
        srng = np.random.default_rng(SEED + 1000 + s)
        ch, rw, refs, Lr, Ar = generate(theta, regimes, mu, srng)
        frng = pyrandom.Random(SEED + 2000 + s)
        f, th_hat = fit(ch, rw, refs, Lr, Ar, frng)
        if th_hat is None:
            th_hat = np.full(7, np.nan)
        rows.append((s, p2, 'MOD' if s % 3 != 2 else 'FULL',
                     f"{theta[5]:.5f}", f"{th_hat[5]:.5f}",
                     f"{theta[2]:.5f}", f"{th_hat[2]:.5f}",
                     f"{theta[4]:.5f}", f"{th_hat[4]:.5f}",
                     f"{theta[3]:.5f}", f"{th_hat[3]:.5f}",
                     f"{theta[6]:.5f}", f"{th_hat[6]:.5f}", f"{f:.1f}"))
        print(rows[-1], flush=True)
    path = os.path.join(ROOT, "records", "g1_recovery_I032.csv")
    with open(path, "w", newline="") as fcsv:
        csv.writer(fcsv).writerows(rows)

    dat = np.array([[float(r[3]), float(r[4]), float(r[5]), float(r[6]),
                     float(r[7]), float(r[8]), float(r[9]), float(r[10]),
                     float(r[11]), float(r[12])] for r in rows[1:]], float)
    ok = ~np.isnan(dat).any(axis=1)
    d = dat[ok]
    r_rho = stats.pearsonr(d[:, 0], d[:, 1])[0]
    r_chi = stats.pearsonr(d[:, 8], d[:, 9])[0]
    boot = np.random.default_rng(SEED + 5)

    def bias_ci(tr, hat):
        b = (hat.mean() - tr.mean()) / tr.mean() * 100
        bs = [((hat[i].mean() - tr[i].mean()) / tr[i].mean() * 100)
              for i in (boot.integers(0, len(tr), len(tr)) for _ in range(2000))]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        return b, lo, hi

    print("\n== G1 summary ==")
    print(f"n fitted: {ok.sum()}/{N_SUBJ}")
    print(f"r(rho_hat, rho_true) = {r_rho:.3f}  -> G1 {'PASS' if r_rho >= .7 else 'FAIL'} (gate .7)")
    print(f"r(chi_hat, chi_true) = {r_chi:.3f}  (descriptive; I003: .62)")
    for name, i, j in [("nuF", 2, 3), ("tauF", 4, 5), ("nuR", 6, 7)]:
        b, lo, hi = bias_ci(d[:, i], d[:, j])
        print(f"group-mean bias {name}: {b:+.1f}%  [95% boot {lo:+.1f}, {hi:+.1f}]"
              f"   (I003: nuF +1.5, tauF +2.4 cover 0; nuR -30 excluded)")
    print(f"record -> {path}")


if __name__ == "__main__":
    main()
