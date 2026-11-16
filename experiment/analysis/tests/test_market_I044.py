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


def test_a_second_script_makes_both_markets_of_a_low_session_twins_of_high_sessions():
    a = mc.run(mc.PT['P1'], 60, 6, ([9, 0], [9, 1], [9, 2]), True)                     # HIGH session on script [9, 0]
    b = mc.run(mc.PT['P1'], 60, 6, ([9, 10], [9, 11], [9, 12]), True)                  # HIGH session on script [9, 10]
    lab = mc.run(mc.PT['P1'], 60, 6, ([9, 0], [9, 5], [9, 6]), False, script2=[9, 10])
    assert np.array_equal(lab['units'][:, 0], a['units'][:, 0]) and np.array_equal(lab['units'][:, 1], b['units'][:, 0])
    plain = mc.run(mc.PT['P1'], 60, 6, ([9, 0], [9, 5], [9, 6]), False)                # without it the neighbour draws its own script
    assert not np.array_equal(plain['units'][:, 1], b['units'][:, 0])
    assert np.array_equal(plain['units'][:, 0], lab['units'][:, 0])


def test_unit_orders_erode_faster_than_they_repair_under_a_rich_neighbour_and_shares_do_not():
    seeds = ([8, 0], [8, 1], [8, 2])
    unit, div = mc.run(mc.PT['P1'], 60, 6, seeds, True), mc.run(mc.PT['P1'], 60, 6, seeds, True, inst='div')
    per = lambda o, key: o[key][:, 0, 1:].mean() / mc.K
    assert per(unit, 'ero') > 1.5 * per(unit, 'rep') and per(div, 'rep') > 1.5 * per(div, 'ero')
    assert 0 <= per(unit, 'rep') <= .0125 and (unit['ero'] >= 0).all()                 # repair per clearing is at most the repair rate


def test_the_triplet_analysis_keeps_its_level_under_a_session_effect_shared_by_two_markets():
    rng = np.random.default_rng(5)
    noise = lambda: dict(F=rng.normal(50, 10, (3000, 6)), T=rng.normal(20, 15, (3000, 6)))
    r = mc.economy(noise(), noise(), noise(), noise(), rng, icc=.3)                     # no effect of the arm at all
    assert r['H1a_t'] < .012 and r['D1_t'] < .012
    assert r['H1a'] > r['H1a_t']                                                       # taking the markets as independent over-rejects


def test_the_plateau_statistic_is_zero_for_one_common_weight_and_positive_for_a_mixture():
    rng = np.random.default_rng(4)
    low = mc.news(np.full((1200, 6), .45), rng)
    p, delta = mc.plat2(mc.news(np.full((1200, 6), .08), rng), low, 12, rng)
    assert abs(delta) < .03 and p < .03
    mixed = np.where(rng.random((1200, 6)) < .2, .45, 0.0)                              # one in five responds, the rest never
    p, delta = mc.plat2(mc.news(mixed, rng), low, 12, rng)
    assert delta > .1 and p > .5


def test_the_sorting_benchmark_formulas_match_simulated_auctions():
    import sorting_benchmark_I044 as sb
    rng = np.random.default_rng(11)
    for n, k in ((2, 1), (5, 2), (6, 3), (3, 5)):
        v = np.sort(rng.random((200000, n)), 1)[:, ::-1]
        p = v[:, k] if k < n else np.zeros(len(v))
        s = (v[:, :min(k, n)] - p[:, None]).sum(1) / n
        assert abs(p.mean() - sb.price(k, n)) < .003 and abs(s.mean() - sb.surplus(k, n)) < .003
    assert sb.equilibria(sb.surplus, 6, sb.SCARCE) == [4] and sb.equilibria(sb.fill, 6, sb.SCARCE) == [5]
    fr, su, _ = sb.market(6, sb.SCARCE, 4)
    assert abs(fr - .200) < .001 and abs(su - .0595) < .0005


def test_a_completion_payment_can_leave_no_market_clearing_prices():
    """One square and one circle. Trader 1 values only the pair (3); trader 2 wants one unit of either (2).
    No prices and allocation leave both traders with a best bundle and every unsold unit at price 0. With
    unit demands (trader 1 wants one unit of either, worth 3) such prices exist."""
    import itertools
    bundles = [(), ('a',), ('b',), ('a', 'b')]
    grid = [x / 4 for x in range(17)]                                                  # prices 0, .25, ..., 4

    def clearing(v1, v2):
        found = []
        for pa, pb in itertools.product(grid, grid):
            p = dict(a=pa, b=pb)
            u = lambda v, s: v(s) - sum(p[x] for x in s)
            best1, best2 = max(u(v1, s) for s in bundles), max(u(v2, s) for s in bundles)
            for owner in itertools.product((0, 1, 2), repeat=2):                       # owner of a, of b; 0 = unsold
                s1 = tuple(x for x, o in zip('ab', owner) if o == 1)
                s2 = tuple(x for x, o in zip('ab', owner) if o == 2)
                if all(p[x] == 0 for x, o in zip('ab', owner) if o == 0) and u(v1, s1) == best1 and u(v2, s2) == best2:
                    found.append((pa, pb))
        return found

    one = lambda worth: (lambda s: worth if len(s) >= 1 else 0.0)
    pair = lambda s: 3.0 if len(s) == 2 else 0.0
    assert clearing(pair, one(2.0)) == []
    assert (0.0, 0.0) in clearing(one(3.0), one(2.0))
