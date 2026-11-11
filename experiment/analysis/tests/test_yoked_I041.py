"""Invariants of the I041 yoked design: schedules, reporting set (run from the repository root)."""
import os
import sys

import numpy as np
from scipy import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import yoked_analysis as ya  # noqa: E402
import yoked_schedules as ys  # noqa: E402


def test_schedules_obey_the_yoking_rules_and_the_odds():
    obj = ys.make(200, 7)
    assert ys.verify(obj)
    g = np.array([[c == '1' for c in s['good']] for s in obj['schedules']])
    b = np.array([[c == '1' for c in s['bad']] for s in obj['schedules']])
    k = ys.R1 * ys.K
    assert abs(g[:, :k].mean() - .75) < .01 and abs(b[:, :k].mean() - .35) < .01
    assert abs(g[:, k:].mean() - .25) < .01 and abs(b[:, k:].mean() - .10) < .01
    assert abs(np.mean([[c == '1' for c in s['board']] for s in obj['schedules']]) - .72) < .01
    assert ys.make(5, 3) == ys.make(5, 3)                       # a seed fixes the file


def test_a_broken_schedule_is_caught():
    obj = ys.make(2, 1)
    s = obj['schedules'][0]
    i = s['good'].index('0')
    s['bad'] = s['bad'][:i] + '1' + s['bad'][i + 1:]            # the worse ticket wins where the better loses
    try:
        ys.verify(obj)
    except AssertionError:
        return
    raise AssertionError('verify accepted a schedule that breaks the yoking rule')


def test_signed_rank_matches_scipy():
    rng = np.random.default_rng(0)
    d = np.round(rng.normal(3, 10, (100, 40)) / 5) * 5
    p = [st.wilcoxon(x[x != 0], alternative='greater', correction=False, method='approx').pvalue for x in d]
    assert np.allclose(st.norm.sf(ya.signed_rank_z(d)), p)


def test_paired_interval_equals_unpaired_one_without_covariance():
    rng = np.random.default_rng(1)
    th, tl = rng.normal(5, 15, (1, 5000)), rng.normal(25, 15, (1, 5000))
    _, lo, hi = ya.fieller(th, tl)
    _, lo_p, hi_p = ya.fieller(th, tl, paired=True)
    assert abs(hi - hi_p) < 0.01 and abs(lo - lo_p) < 0.01 and lo < 0.2 < hi


def test_decisions_on_a_clear_case_and_on_a_null():
    rng = np.random.default_rng(2)
    b, n = 200, 72
    base = dict(fl_rounds=np.round(rng.normal(65, 6, (b, n, 4)) / 5) * 5, wl=rng.normal(.2, .05, (b, n, 3)),
                jit=rng.uniform(-.01, .01, (b, n)))
    clear = dict(base, fh=rng.normal(30, 8, (b, n)), fl=rng.normal(68, 8, (b, n)), eh=rng.normal(46, 6, (b, n)),
                 el=rng.normal(38, 6, (b, n)), th=rng.normal(3, 18, (b, n)), tl=rng.normal(31, 20, (b, n)))
    out = ya.decisions(clear)
    assert out['H1a'].mean() > .99 and out['K3'].mean() > .99 and out['D1'].mean() > .99 and out['PHI'].mean() < .05
    null = dict(base, fh=rng.normal(60, 8, (b, n)), fl=rng.normal(60, 8, (b, n)), eh=rng.normal(40, 6, (b, n)),
                el=rng.normal(40, 6, (b, n)), th=rng.normal(30, 20, (b, n)), tl=rng.normal(30, 20, (b, n)))
    out = ya.decisions(null)
    assert max(out[k].mean() for k in ('H1a', 'K3', 'D1', 'FREEZE', 'ASSOC', 'PAIR', 'FULL')) < .05


def test_by_arm_statistics_match_scipy_and_hold_their_size():
    rng = np.random.default_rng(3)
    t, f = np.round(rng.normal(10, 20, (400, 72)) / 2.5) * 2.5, rng.normal(40, 10, (400, 72))
    p = ya.topq_p(t, f)
    for i in (0, 7, 399):
        o = np.argsort(f[i])
        ref = st.mannwhitneyu(t[i][o[54:]], t[i][o[:54]], alternative='greater', method='asymptotic').pvalue
        assert abs(p[i] - ref) < 1e-12
    assert (p < .05).mean() < .09 and (ya.arm_z(t, f) > st.norm.ppf(.95)).mean() < .09     # independent T and F
    tt = t + 1.5 * (f - 40)                                                                  # T rises with F
    assert (ya.topq_p(tt, f) < .005).mean() > .8 and (ya.arm_z(tt, f) > ya.ZC).mean() > .9
