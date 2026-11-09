"""Audit tests for stats_v2: each function against an independent reference, and
null-level checks of every test the certification relies on, at the alphas
actually used. Monte Carlo checks report Clopper-Pearson bounds.
"""
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stats_v2 as sv


def cp_upper(k, n, conf=.95):
    return 1.0 if k == n else stats.beta.ppf(1 - (1 - conf) / 2, k + 1, n - k)


def cp_lower(k, n, conf=.95):
    return 0.0 if k == 0 else stats.beta.ppf((1 - conf) / 2, k, n - k + 1)


def r5(x):
    return np.round(x / 5) * 5


# ------------------------------------------------------------------ WMW
def test_wmw_matches_scipy_with_ties():
    rng = np.random.default_rng(1)
    for _ in range(50):
        x = r5(rng.normal(20, 15, 300)); y = r5(rng.normal(23, 15, 280))
        z = sv.wmw_z(x, y)
        p_ref = stats.mannwhitneyu(y, x, alternative="greater", use_continuity=False,
                                   method="asymptotic").pvalue
        assert abs(stats.norm.sf(z) - p_ref) < 1e-10


def test_theta_hat_is_U_over_n1n2():
    rng = np.random.default_rng(2)
    x = r5(rng.normal(0, 10, 120)); y = r5(rng.normal(2, 10, 140))
    U = stats.mannwhitneyu(y, x, method="asymptotic").statistic
    assert abs(sv.theta_hat(x, y) - U / (len(x) * len(y))) < 1e-12


def test_hodges_lehmann_bruteforce():
    rng = np.random.default_rng(3)
    x, y = rng.normal(0, 1, 31), rng.normal(.5, 1, 27)
    diffs = sorted(b - a for a in x for b in y)
    assert abs(sv.hodges_lehmann(x, y) - float(np.median(diffs))) < 1e-12


def test_wmw_level_one_sided_005_with_heavy_ties():
    rng = np.random.default_rng(4)
    n, k = 20000, 0
    for _ in range(n):
        x = r5(np.clip(rng.normal(25, 20, 320), 0, 90))
        y = r5(np.clip(rng.normal(25, 20, 320), 0, 90))
        k += sv.wmw_one_sided(x, y, .005)[0]
    assert cp_lower(k, n) <= .005 <= cp_upper(k, n), f"level {k/n:.4f}"


# ------------------------------------------------ studentized permutation Welch
def test_studentized_permutation_level_heteroskedastic():
    """Unequal n and variances (the case where unstudentized permutation fails)."""
    rng = np.random.default_rng(5)
    n, k = 600, 0
    for i in range(n):
        x = rng.normal(0, 1, 60); y = rng.normal(0, 3, 240)
        k += sv.studentized_permutation_welch(x, y, alpha=.05, B=499, seed=i)[0]
    assert cp_lower(k, n) <= .05 <= cp_upper(k, n), f"level {k/n:.3f}"


# ------------------------------------------------------- H1b signed-rank pieces
def test_signed_rank_level_at_null_boundary():
    rng = np.random.default_rng(6)
    n, k = 20000, 0
    for _ in range(n):
        c = rng.standard_t(4, 106)            # median exactly 0, heavy-ish tails
        k += sv._signed_rank_less(c, .005)[0]
    assert cp_lower(k, n) <= .005 <= cp_upper(k, n), f"level {k/n:.4f}"


def test_tost_rejects_only_inside_band():
    rng = np.random.default_rng(7)
    inside = rng.normal(0, 3, 400)
    outside = rng.normal(-12, 3, 400)
    assert sv.h1b_tost_frozen(inside, 5.0)[0]
    assert not sv.h1b_tost_frozen(outside, 5.0)[0]


def test_delta_eq_rule():
    assert sv.delta_eq_rule(np.array([4.0, 6.0, 8.0]))[0] == 5.0
    assert sv.delta_eq_rule(np.array([20.0, 22.0, 24.0]))[0] == 11.0


# ------------------------------------------------------------- dose contrast
def test_dose_second_difference_level_under_graded_line():
    """Null = cell means on a line, unequal variances and sizes (the R3 shape).
    A label-permutation test would reject here by construction (AD1)."""
    rng = np.random.default_rng(8)
    n, k = 400, 0
    for i in range(n):
        d45 = rng.normal(10, 6, 90); d55 = rng.normal(15, 9, 90); d65 = rng.normal(20, 12, 320)
        k += sv.dose_second_difference(d45, d55, d65, B=999, seed=i)[0]
    assert cp_lower(k, n) <= .05 <= cp_upper(k, n), f"level {k/n:.3f}"


def test_dose_detects_a_step():
    rng = np.random.default_rng(9)
    d45 = rng.normal(10, 6, 90); d55 = rng.normal(10, 6, 90); d65 = rng.normal(25, 6, 320)
    assert sv.dose_second_difference(d45, d55, d65, B=999, seed=1)[0]
