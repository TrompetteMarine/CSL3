"""Fast checks of the staged power calculation (KGi-DISS-I045): the two runners against the certified
simulators, the stopping basket, the masked interval, the sample-size rule and the two-sample test.
Run from the repository root."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import market_cert_I044 as mc  # noqa: E402
import staged_power_I045 as sp  # noqa: E402
import twins_I040 as tw  # noqa: E402
import yoked_analysis as ya  # noqa: E402


def test_the_individual_runner_is_the_certified_one_when_nothing_is_changed():
    ref = tw.twins(sp.PT['P1'], 300, np.random.default_rng(3), same_person=False, indep_choice=True)
    new = sp.indiv(sp.PT['P1'], 300, np.random.default_rng(3))
    for key in ('L', 'A', 'wins'):
        for arm in sp.ARMS:
            assert np.array_equal(ref[key][arm], new[key][arm])
    assert (new['events']['HIGH'] == tw.K).all() and (new['done']['LOW'] == 1).all()


def test_the_live_runner_is_the_certified_one_without_a_basket():
    seeds = ([4, 0], [4, 1], [4, 2])
    a = mc.run(sp.PT['P4'], 40, 6, seeds, True, script2=[4, 3])
    b = sp.run_w(sp.PT['P4'], 40, 6, seeds, True, script2=[4, 3])
    assert np.array_equal(a['L'], b['L']) and np.array_equal(a['wins'], b['wins'])
    assert (b['events'] == mc.K).all()


def test_a_basket_ends_the_bidding_and_the_events():
    b = sp.indiv(sp.PT['P1'], 300, np.random.default_rng(5), quota=15)
    for arm in sp.ARMS:
        w, e, d = b['wins'][arm], b['events'][arm], b['done'][arm]
        assert (w <= 15).all() and (e <= tw.K).all()
        assert np.array_equal(d > 0, w >= 15)                               # completed exactly when the basket is held
        assert (e[d > 0] < tw.K).mean() > .9                                # a completed round has fewer events
        assert (e[d == 0] == tw.K).all()                                    # an uncompleted round has all of them
    live = sp.run_w(sp.PT['P1'], 30, 6, ([6, 0], [6, 1], [6, 2]), True, quota=10)
    assert (live['wins'] <= 10).all() and live['events'][:, 1, :, 1:].mean() < live['events'][:, 0, :, 1:].mean()   # the rich neighbour finishes sooner


def test_a_round_that_counts_for_fewer_settlements_is_shorter():
    b = sp.indiv(sp.PT['P1'], 200, np.random.default_rng(7), K=40)
    assert b['K'] == 40 and (b['events']['LOW'] == 40).all() and b['L']['HIGH'].shape == (200, 6)


def test_the_masked_interval_equals_the_plain_one_when_everybody_is_measured():
    rng = np.random.default_rng(8)
    th, tl = rng.normal(10, 20, (50, 40)), rng.normal(30, 20, (50, 40))
    full = np.ones((50, 40), bool)
    assert np.allclose(sp.fieller_masked(th, full, tl, full), ya.fieller(th, tl)[2])
    part = rng.random((50, 40)) < .7
    hi = sp.fieller_masked(th, part, tl, part)
    assert np.isfinite(hi).mean() > .9 and not np.allclose(hi, ya.fieller(th, tl)[2])


def test_the_required_n_is_the_smallest_grid_value_reaching_the_target():
    grid = (12, 24, 36, 48)
    assert sp.need((.2, .85, .93, .99), grid, .90) == 36 and sp.need((.2, .85, .93, .99), grid, .80) == 24
    assert sp.need((.1, .2, .3, .4), grid) is None and sp.show(None, grid) == '>48' and sp.show(36, grid) == '36'


def test_the_two_sample_test_keeps_its_level_and_sees_a_difference():
    rng = np.random.default_rng(9)
    x, y = rng.normal(0, 1, (4000, 6)), rng.normal(0, 1, (4000, 6))
    assert sp.welch_greater(x, y).mean() < .012
    assert sp.welch_greater(x + 3, y).mean() > .8


def test_the_triplet_test_does_not_reject_when_the_arms_are_alike():
    rng = np.random.default_rng(10)
    pool = lambda: dict(F=rng.normal(50, 10, (1500, 6)), T=rng.normal(20, 15, (1500, 6)))
    V = sp.triplet_values(pool(), pool(), pool(), pool(), rng, .2)
    old, sp.B = sp.B, 1500
    try:
        r = sp.triplet_test(V, 8, rng)
    finally:
        sp.B = old
    assert r['H1a'] < .015 and r['D1'] < .015 and r['PAIR'] <= min(r['H1a'], r['D1'])
