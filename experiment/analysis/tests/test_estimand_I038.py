"""Invariants of the I038 estimand code (run from the repository root)."""
import os
import sys

import numpy as np
import pytest
from scipy import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import probe_generator as pg  # noqa: E402
import estimand_core_I038 as ec  # noqa: E402


def test_generator_knobs_default_to_the_i037_draws():
    """the prior and noise knobs must not change a single draw at their defaults"""
    w = np.linspace(0, 0.9, 5000)
    new = pg._revision(w, 0.9, 12.0, np.random.default_rng(7))
    rng = np.random.default_rng(7)
    b0 = np.clip(rng.normal(50, 10, len(w)), 5, 95)
    pre = pg._round5(b0 + rng.normal(0, 12.0, len(w)))
    post = pg._round5(b0 + w * (90 - b0) + rng.normal(0, 12.0, len(w)))
    assert np.array_equal(new, post - pre)


def test_fieller_reduces_to_a_scaled_t_interval_when_the_denominator_is_exact():
    lo, hi = ec.fieller(np.array(10.0), np.array(4.0), np.array(40.0), np.array(0.0), 100)
    t = st.t.ppf(.995, 100)
    assert abs(lo - (10 - 2 * t) / 40) < 1e-12 and abs(hi - (10 + 2 * t) / 40) < 1e-12


def test_fieller_is_unbounded_when_the_denominator_is_not_separated_from_zero():
    lo, hi = ec.fieller(np.array(1.0), np.array(1.0), np.array(1.0), np.array(4.0), 50)
    assert lo == -np.inf and hi == np.inf


def test_fieller_coverage_in_the_normal_case():
    rng = np.random.default_rng(11)
    b, n = 20000, 40
    xh, xl = rng.normal(5, 15, (b, n)), rng.normal(20, 15, (b, n))
    lo, hi = ec.fieller(xh.mean(1), xh.var(1, ddof=1) / n, xl.mean(1), xl.var(1, ddof=1) / n, 2 * n - 2)
    cover = np.mean((lo <= .25) & (.25 <= hi))
    assert .985 <= cover <= .995


@pytest.mark.parametrize('shape', ['hom', 'two01', 'two51', 'skew'])
@pytest.mark.parametrize('mean_c', [.90, .95])
def test_coupling_shapes_have_the_requested_mean(shape, mean_c):
    c = ec.coupling(shape, mean_c, 400000, np.random.default_rng(3))
    assert abs(c.mean() - mean_c) < .003 and c.min() >= 0 and c.max() <= 1


def test_event_rule_makes_psi_depend_on_the_mean_coupling_only():
    rng = np.random.default_rng(5)
    lh, ll = rng.beta(1, 6, 300000), rng.beta(8, 1.5, 300000)
    v = [ec.weight_ratio(lh, ll, ec.coupling(s, .9, 300000, rng), ec.coupling(s, .9, 300000, rng), 'event')
         for s in ('hom', 'two01', 'two51', 'skew')]
    assert max(v) - min(v) < .005


def test_influence_function_standard_error_matches_monte_carlo():
    rng = np.random.default_rng(9)
    th, tl = rng.normal(6, 18, 200000), rng.normal(24, 20, 200000)
    d = ec.draw(th, tl, 72, 72, 20000, rng)
    assert abs(d['psi'].std() / ec.se_if(th, tl, 72, 72) - 1) < .05
