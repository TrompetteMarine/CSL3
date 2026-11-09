"""design_generator must reproduce market_generator bit for bit at the default
geometry (all kinds, both arms, framing, trace) and its measurement layer must
equal market_generator.measure at 90 ratings for every shape."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import market_generator as mg  # noqa: E402
import design_generator as dg  # noqa: E402

KEYS = ('ratings', 'ent', 'acc1', 'acc2', 'acc3', 'acc_late', 'resto_full', 'rho',
        'reg1', 'reg3', 'R', 'arm', 'peer')


@pytest.mark.parametrize('kind', ['gate', 'rival', 'rival_us', 'rival_au'])
@pytest.mark.parametrize('arm', ['HIGH', 'LOW'])
@pytest.mark.parametrize('framing', [False, True])
def test_default_geometry_identical(kind, arm, framing):
    a = mg.simulate_latent(kind, 300, arm, np.random.default_rng(11), framing=framing, trace=True)
    b = dg.simulate_design(kind, 300, arm, np.random.default_rng(11), framing=framing, trace=True)
    for k in KEYS:
        assert np.array_equal(a[k], b[k]), k


@pytest.mark.parametrize('shape', ['M1', 'M2', 'M3', 'M4', 'M5', 'M6'])
def test_measure_identical(shape):
    lat = mg.simulate_latent('gate', 400, 'HIGH', np.random.default_rng(3))
    x = mg.measure(lat, shape, .3, np.random.default_rng(5))
    y = dg.measure_design(lat, shape, .3, np.random.default_rng(5))
    for u, v in zip(x, y):
        assert np.array_equal(u, v)


def test_short_geometry_runs_and_fixes_regime():
    lat = dg.simulate_design('gate', 200, 'HIGH', np.random.default_rng(1),
                             phases=(40, 90, 60), cadence=5, reg3_fixed=True)
    assert lat['ratings'].shape == (200, 38)
    assert lat['reg3'].all()
    i = lat['idx']
    assert (i['p1'].stop, i['p2'].stop, i['p3'].stop) == (8, 26, 38)
