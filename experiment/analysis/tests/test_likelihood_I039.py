"""Invariants of the I039 likelihood code (run from the repository root)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import estimand_core_I038 as ec  # noqa: E402
import likelihood_core_I039 as lc  # noqa: E402
import probe_generator as pg  # noqa: E402


def test_kernel_is_a_distribution_with_the_right_mean():
    w = np.array([0.0, 0.2, 0.5])
    k = lc.kernel_T(w, 12.0)
    assert np.allclose(k.sum(1), 1.0, atol=1e-9) and (k >= 0).all()
    assert np.allclose(k @ lc.TGRID, 80 * w, atol=0.3)          # the pair cancels the prior


def test_kernel_matches_the_simulator():
    rng = np.random.default_rng(4)
    sim = pg.probe_stat(np.full(200000, 0.3 / pg.OMEGA), 1.0, ec.M, ec.SCHEME, 12.0, 'event', rng, inattentive=0.0)
    emp = np.bincount(np.round((sim + 200) / 2.5).astype(int), minlength=161) / len(sim)
    assert 0.5 * np.abs(emp - lc.kernel_T(np.array([0.3]), 12.0)[0]).sum() < 0.02


def test_binning_keeps_mass_mean_and_atoms():
    rng = np.random.default_rng(5)
    l = np.r_[np.zeros(3000), rng.random(7000)]
    g = lc.bin_pool(l)
    assert abs(g.sum() - 1) < 1e-12 and abs(g @ lc.LGRID - l.mean()) < 1e-9 and g[0] >= 0.3
    s = lc.shift_pool(g, 0.01)
    assert abs(s.sum() - 1) < 1e-12 and 0.009 < s @ lc.LGRID - g @ lc.LGRID <= 0.01 and s[0] == 0.0


def test_information_is_symmetric_positive_and_zero_without_dependence():
    g = {'HIGH': lc.bin_pool(np.r_[np.zeros(800), np.full(200, 0.6)]), 'LOW': lc.bin_pool(np.full(1000, 0.9))}
    m = lc.Model(g, g, 'event', sigmas=(12.0,))
    info = m.info(dict(lc.BASE), ['c', 'kap', 'q'], False)
    for arm in info:
        assert np.allclose(info[arm], info[arm].T) and np.linalg.eigvalsh(info[arm]).min() > -1e-9
    # at c = 0 nobody's weight depends on legitimacy: the depth carries no information about T
    th0 = {**lc.BASE, 'c': 0.0}
    assert abs(m.info(th0, ['lam'], False)['HIGH'][0, 0]) < 1e-12
    # and psi is 1
    assert abs(m.psi(th0) - 1) < 1e-9


def test_joint_table_has_the_marginal_of_the_probe_table():
    g = {'HIGH': lc.bin_pool(np.r_[np.zeros(500), np.full(500, 0.7)]), 'LOW': lc.bin_pool(np.full(1000, 0.9))}
    m = lc.Model(g, g, 'outcome', sigmas=(12.0,))
    j = m.pFT('HIGH', dict(lc.BASE))
    assert abs(j.sum() - 1) < 1e-9 and np.allclose(j.sum(0), m.pT('HIGH', dict(lc.BASE)), atol=1e-12)


def test_aggregation_identity_on_a_random_population():
    rng = np.random.default_rng(6)
    g, d = rng.random(5000), rng.normal(0, 1, 5000) + 2 * rng.random(5000)
    assert abs((g * d).mean() - (g.mean() * d.mean() + np.cov(g, d, bias=True)[0, 1])) < 1e-12
    # horizon inequality: population residual against the representative agent's
    for t in (1, 2, 5, 20):
        assert ((1 - 0.5 * g) ** t).mean() >= (1 - 0.5 * g.mean()) ** t - 1e-12
