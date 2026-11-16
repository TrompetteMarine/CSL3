"""The live economy of KGi-DISS-I044: the auctioneer, the bridge to the certified kernel, the twin
script, and the two model results the design rests on. Run from the repository root."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import market_cert_I044 as mc  # noqa: E402


def test_the_price_clears_the_market_and_the_units_go_to_the_highest_bids():
    rng = np.random.default_rng(1)
    for _ in range(400):
        N, k = int(rng.integers(2, 10)), int(rng.integers(0, 11))
        m, bid = rng.random(N) < .7, rng.random(N)
        b = np.where(m, bid, -1.0)
        win, price = mc.auction(b[None, None], m[None, None], np.array([[k]]))
        win, price, n = win[0, 0], float(price[0, 0]), int(m.sum())
        assert win.sum() == min(k, n) and not win[~m].any()
        if n > k:                                           # some bid loses: the price is the highest losing bid
            assert price == np.sort(bid[m])[::-1][k] and (k == 0 or bid[win].min() > price)
        else:                                               # supply covers every bidder: the reserve
            assert price == 0.0
        assert ((b > price) & m).sum() <= k and ((b >= price) & m).sum() >= min(k, n)


def test_truthful_bidding_is_a_best_reply_under_the_highest_losing_bid_price():
    assert mc.x3(np.random.default_rng(2), 60) == 0.0


def test_the_kernel_step_reproduces_the_certified_individual_design():
    s = mc.solo(mc.PT['P1'], 6000, np.random.default_rng(3))
    assert abs(s['HIGH'].mean() - .109) < .03 and abs(s['LOW'].mean() - .869) < .03     # records/yoked_cert_I041.txt, section 0


def test_twin_sessions_share_the_focal_script_and_differ_in_the_neighbour():
    seeds = lambda a: ([7, 0], [7, 1 + 2 * a], [7, 2 + 2 * a])
    h, lo = mc.run(mc.PT['P1'], 60, 6, seeds(0), True), mc.run(mc.PT['P1'], 60, 6, seeds(1), False)
    assert np.array_equal(h['units'][:, 0], lo['units'][:, 0])                         # the same scripted supply
    assert not np.array_equal(h['units'][:, 1], lo['units'][:, 1])
    assert (h['sold'] <= h['units']).all() and (lo['sold'] <= lo['units']).all()
    fill = lambda o, m: o['wins'][:, m, :, 1:].mean() / mc.K
    assert fill(h, 1) > .55 and fill(lo, 1) < .3 and abs(fill(h, 0) - fill(lo, 0)) < .03
    assert h['L'][:, 0, :, -1].mean() < lo['L'][:, 0, :, -1].mean() - .4               # the contrast is there
    assert (h['cash'] >= 0).all()                                                      # a filled unit never costs more than its value


def test_divisible_clearing_leaves_legitimacy_intact_in_the_model():
    seeds = ([8, 0], [8, 1], [8, 2])
    div, unit = mc.run(mc.PT['P1'], 60, 6, seeds, True, inst='div'), mc.run(mc.PT['P1'], 60, 6, seeds, True)
    assert div['L'][:, 0, :, -1].mean() > .85 > .4 > unit['L'][:, 0, :, -1].mean()


def test_the_plateau_statistic_is_zero_for_one_common_weight_and_positive_for_a_mixture():
    rng = np.random.default_rng(4)
    low = mc.news(np.full((1200, 6), .45), rng)
    p, delta = mc.plat2(mc.news(np.full((1200, 6), .08), rng), low, 12, rng)
    assert abs(delta) < .03 and p < .03
    mixed = np.where(rng.random((1200, 6)) < .2, .45, 0.0)                              # one in five responds, the rest never
    p, delta = mc.plat2(mc.news(mixed, rng), low, 12, rng)
    assert delta > .1 and p > .5
