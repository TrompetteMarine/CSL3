"""KGi-DISS-I032 — distribution-free test modules for the prereg pipeline.

Independent implementations (not imports) of the statistics shared with the
I029 power engine: gate G2 (records/g2_consistency.csv) tests, rather than
assumes, agreement with analysis/power_free.py on battery draws.

Modules: one-sided tie-corrected WMW (+ theta-hat and Hodges-Lehmann shift);
one-sided Welch and its studentized permutation version (real-data form);
Wilcoxon signed-rank TOST pieces for H1b (frozen two-sided form and the
one-sided non-superiority repair candidate, both per 00_freeze_I032.yaml);
the dose second-difference contrast with a studentized within-cell-centered
bootstrap null (freeze addendum AD1); the framing-probe WMW.

The certification Monte Carlo calls these per replicate; no vectorized test
variants exist (one code path for real data and for certification).
"""
import numpy as np
from scipy import stats

ALPHA_CONF = 0.005   # confirmatory, one-sided (H1a) / per-TOST-leg (H1b)
ALPHA_MOD = 0.05     # module-level secondaries (dose, framing)


# ---------------------------------------------------------------- WMW (one-sided)
def wmw_z(x, y):
    """z for H1: y stochastically larger than x; tie-corrected normal approx
    (same statistic as power_free.wmw_reject, implemented independently)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n1, n2 = len(x), len(y)
    allv = np.concatenate([x, y])
    ranks = stats.rankdata(allv)
    u = ranks[n1:].sum() - n2 * (n2 + 1) / 2.0
    mu = n1 * n2 / 2.0
    _, cnt = np.unique(allv, return_counts=True)
    tiecorr = 1.0 - (cnt ** 3 - cnt).sum() / ((n1 + n2) ** 3 - (n1 + n2))
    sd = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0 * max(tiecorr, 1e-12))
    return (u - mu) / sd


def wmw_one_sided(x, y, alpha=ALPHA_CONF):
    """Reject iff y stochastically larger at one-sided alpha."""
    z = wmw_z(x, y)
    return bool(z > stats.norm.ppf(1 - alpha)), z


def theta_hat(x, y):
    """Mann-Whitney theta = P(Y > X) + .5 P(Y = X)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    gt = (y[:, None] > x[None, :]).mean()
    eq = (y[:, None] == x[None, :]).mean()
    return gt + 0.5 * eq


def hodges_lehmann(x, y):
    """Median of pairwise differences y_j - x_i."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    return float(np.median(y[:, None] - x[None, :]))


# ------------------------------------------------------------------ Welch family
def welch_one_sided(x, y, alpha=ALPHA_CONF):
    """Plain one-sided Welch (MC co-report; see I029 note)."""
    t, p = stats.ttest_ind(y, x, equal_var=False, alternative="greater")
    return bool(p < alpha), float(t)


def welch_t_stat(x, y):
    nx, ny = len(x), len(y)
    vx, vy = x.var(ddof=1), y.var(ddof=1)
    se = np.sqrt(vx / nx + vy / ny)
    return (y.mean() - x.mean()) / max(se, 1e-12)


def studentized_permutation_welch(x, y, alpha=ALPHA_CONF, B=4999, seed=0):
    """One-sided studentized permutation Welch (Chung-Romano class) — the
    real-data co-report. Level asymptotically valid under heteroskedasticity."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float); y = np.asarray(y, float)
    t_obs = welch_t_stat(x, y)
    pooled = np.concatenate([x, y]); nx = len(x)
    cnt = 0
    for _ in range(B):
        perm = rng.permutation(pooled)
        cnt += welch_t_stat(perm[:nx], perm[nx:]) >= t_obs
    p = (cnt + 1) / (B + 1)
    return bool(p < alpha), float(t_obs), float(p)


# ------------------------------------------------------- H1b rank TOST machinery
def _signed_rank_less(d, alpha):
    """One-sided Wilcoxon signed-rank: reject iff median(d) < 0 evidence at
    alpha. Normal approximation with ties/zeros dropped (scipy default)."""
    d = np.asarray(d, float)
    d = d[d != 0]
    if len(d) < 10:
        return False, np.nan
    try:
        res = stats.wilcoxon(d, alternative="less", method="approx")
    except ValueError:
        return False, np.nan
    return bool(res.pvalue < alpha), float(res.pvalue)


def h1b_tost_frozen(recovery, delta_eq, alpha=ALPHA_CONF):
    """Frozen form (prereg): two one-sided signed-rank tests — recovery inside
    (-delta_eq, +delta_eq). Returns (pass, p_upper, p_lower)."""
    up, p_up = _signed_rank_less(np.asarray(recovery) - delta_eq, alpha)    # < +delta
    lo, p_lo = _signed_rank_less(-(np.asarray(recovery) + delta_eq), alpha)  # > -delta
    return bool(up and lo), p_up, p_lo


def h1b_nonsuperiority(recovery, delta_eq, alpha=ALPHA_CONF):
    """Repair candidate (freeze I032): one-sided non-superiority — reject
    H0: recovery >= +delta_eq in favour of recovery < +delta_eq."""
    ok, p = _signed_rank_less(np.asarray(recovery) - delta_eq, alpha)
    return bool(ok), p


def delta_eq_rule(p1_rating_sd_per_subject):
    """delta_eq = max(5, .5*sigma_r); sigma_r = median within-subject SD of P1
    fairness ratings (pre-stated operationalization; pilot supplies the real
    value before filing)."""
    sigma_r = float(np.nanmedian(p1_rating_sd_per_subject))
    return max(5.0, 0.5 * sigma_r), sigma_r


# ----------------------------------------------------------------- dose contrast
def dose_second_difference(d45, d55, d65, B=4000, seed=0, alpha=ALPHA_MOD):
    """C = mean(d65) - 2*mean(d55) + mean(d45); two-sided studentized test with
    a within-cell-centered bootstrap null (freeze addendum AD1: a label
    permutation would test equality of distributions, which the graded rival
    violates by construction)."""
    rng = np.random.default_rng(seed)
    cells = [np.asarray(d, float) for d in (d45, d55, d65)]
    w = np.array([1.0, -2.0, 1.0])

    def contrast(cs):
        m = np.array([c.mean() for c in cs])
        v = np.array([c.var(ddof=1) / len(c) for c in cs])
        C = (w * m).sum()
        se = np.sqrt((w ** 2 * v).sum())
        return C, max(se, 1e-12)

    C_obs, se_obs = contrast(cells)
    t_obs = C_obs / se_obs
    centered = [c - c.mean() for c in cells]
    tb = np.empty(B)
    for b in range(B):
        cs = [rng.choice(c, len(c), replace=True) for c in centered]
        Cb, seb = contrast(cs)
        tb[b] = Cb / seb
    p = (np.sum(np.abs(tb) >= abs(t_obs)) + 1) / (B + 1)
    return bool(p < alpha), float(C_obs), float(t_obs), float(p)


# ----------------------------------------------------------------- framing probe
def framing_test(framing_drops, low_drops, alpha=ALPHA_MOD):
    """One-sided WMW: framing-arm drops stochastically larger than LOW-arm
    drops (gate: drop persists under fixed-rate framing; R4 banks evidence)."""
    return wmw_one_sided(low_drops, framing_drops, alpha)
