"""Invariants of the evidence-uptake probe simulator."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import probe_generator as pg  # noqa: E402


def test_pair_cancels_prior_and_recovers_weight():
    rng = np.random.default_rng(1)
    mult = np.full(200000, 0.5)
    t = pg.probe_stat(mult, 1.0, 7, 'pair', 0.0, 'outcome', rng, inattentive=0.0)
    w = pg.weight(0.5, 7, 'outcome')
    assert abs(t.mean() - 100 * w * (6 / 7 - 1 / 7)) < 0.5       # rounding to 5 only


@pytest.mark.parametrize('scheme', ['single', 'pair', 'pair2', 'did'])
def test_no_coupling_no_arm_difference(scheme):
    rng = np.random.default_rng(2)
    hi = pg.probe_stat(np.full(60000, 0.2), 0.0, 7, scheme, 12.0, 'outcome', rng)
    lo = pg.probe_stat(np.full(60000, 0.9), 0.0, 7, scheme, 12.0, 'outcome', rng)
    assert abs(pg.theta(hi, lo) - 0.5) < 0.01


def test_coupling_orders_arms_and_did_removes_disengagement():
    rng = np.random.default_rng(3)
    hi = pg.probe_stat(np.full(60000, 0.3), 1.0, 7, 'pair', 12.0, 'outcome', rng)
    lo = pg.probe_stat(np.full(60000, 0.8), 1.0, 7, 'pair', 12.0, 'outcome', rng)
    assert pg.theta(hi, lo) > 0.55
    # no gate (multiplier 1), extra inattention in HIGH only
    hi = pg.probe_stat(np.ones(60000), 1.0, 7, 'pair', 12.0, 'outcome', rng, extra_inattentive=0.2)
    lo = pg.probe_stat(np.ones(60000), 1.0, 7, 'pair', 12.0, 'outcome', rng)
    assert pg.theta(hi, lo) > 0.53                                 # raw pair is fooled
    hi = pg.probe_stat(np.ones(60000), 1.0, 7, 'did', 12.0, 'outcome', rng, extra_inattentive=0.2)
    lo = pg.probe_stat(np.ones(60000), 1.0, 7, 'did', 12.0, 'outcome', rng)
    assert abs(pg.theta(hi, lo) - 0.5) < 0.01                      # difference-in-differences is not


def test_theta_matches_bruteforce():
    rng = np.random.default_rng(4)
    a, b = np.round(rng.normal(0, 3, 300)), np.round(rng.normal(1, 3, 280))
    brute = ((b[:, None] > a[None, :]).mean() + 0.5 * (b[:, None] == a[None, :]).mean())
    assert abs(pg.theta(a, b) - brute) < 1e-12
