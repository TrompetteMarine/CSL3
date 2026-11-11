"""The reporting set of the yoked design (KGi-DISS-I041). Every function takes arrays whose
first axis is the replicate and whose second axis is the pair, so the same code scores one
pilot data set (one replicate) and a Monte Carlo certification (many).

    H1a     last fairness rating, LOW above HIGH within pairs (signed rank)
    K3      last entitlement rating, HIGH above LOW within pairs (signed rank)
    D1      psi = mean(T_HIGH) / mean(T_LOW) below 1 (Fieller upper limit)
    FREEZE  uptake ratio of the lowest-rated third of HIGH below a bound
    ASSOC   within-arm rank association of T and the last fairness rating, pooled
    PHI     in LOW, slope of the change in the fairness rating on the round's win share < 0

Addendum AD-Y2 (the association by arm; decisions() keeps its frozen outputs and adds these):
    ASSOC_H, ASSOC_L   the rank association within HIGH only and within LOW only
    TOPQ               within HIGH, the top quarter by rating revises more than the rest (rank sum)
"""
import numpy as np
from scipy import stats as st

ALPHA1 = 0.005
ZC = st.norm.ppf(1 - ALPHA1)


def signed_rank_z(d):
    """Wilcoxon signed-rank z for H1: differences tend to be positive. Zero differences are
    dropped; tied absolute differences get average ranks; variance = sum of squared ranks / 4."""
    d = np.asarray(d, float)
    a = np.where(d == 0, np.nan, np.abs(d))
    r = np.nan_to_num(st.rankdata(a, axis=1, nan_policy='omit'), nan=0.0)
    wplus = (r * (d > 0)).sum(1)
    den = np.sqrt((r ** 2).sum(1) / 4)
    return np.where(den > 0, (wplus - r.sum(1) / 2) / np.maximum(den, 1e-12), 0.0)


def fieller(th, tl, paired=False, level=1 - 2 * ALPHA1):
    """psi-hat and confidence limits for mean(th) / mean(tl); (-inf, inf) if the denominator
    is not separated from zero. paired=True uses the within-pair covariance."""
    n = th.shape[1]
    mh, ml = th.mean(1), tl.mean(1)
    vh, vl = th.var(1, ddof=1) / n, tl.var(1, ddof=1) / n
    cov = ((th - mh[:, None]) * (tl - ml[:, None])).sum(1) / (n - 1) / n if paired else 0.0
    t = st.t.ppf(.5 + level / 2, (n - 1) if paired else (2 * n - 2))
    a, b, c = ml ** 2 - t ** 2 * vl, mh * ml - t ** 2 * cov, mh ** 2 - t ** 2 * vh
    disc = np.maximum(b ** 2 - a * c, 0.0)
    ok = a > 0
    lo = np.where(ok, (b - np.sqrt(disc)) / np.where(ok, a, 1.0), -np.inf)
    hi = np.where(ok, (b + np.sqrt(disc)) / np.where(ok, a, 1.0), np.inf)
    return mh / ml, lo, hi


def freeze_upper(th, fh, tl, share=1 / 3, level=1 - 2 * ALPHA1):
    """upper limit of mean(T | lowest-rated share of HIGH) / mean(T | LOW); ties in the rating
    must be broken by the caller (add a small jitter)"""
    n = th.shape[1]
    k = int(n * share)
    ts = np.take_along_axis(th, np.argsort(fh, axis=1)[:, :k], axis=1)
    mh, ml = ts.mean(1), tl.mean(1)
    vh, vl = ts.var(1, ddof=1) / k, tl.var(1, ddof=1) / n
    t = st.t.ppf(.5 + level / 2, k + n - 2)
    a, b, c = ml ** 2 - t ** 2 * vl, mh * ml, mh ** 2 - t ** 2 * vh
    return np.where(a > 0, (b + np.sqrt(np.maximum(b ** 2 - a * c, 0))) / np.where(a > 0, a, 1.0), np.inf)


def spearman(x, y):
    rx, ry = st.rankdata(x, axis=1), st.rankdata(y, axis=1)
    rx, ry = rx - rx.mean(1, keepdims=True), ry - ry.mean(1, keepdims=True)
    den = np.sqrt((rx ** 2).sum(1) * (ry ** 2).sum(1))
    return np.where(den > 0, (rx * ry).sum(1) / np.maximum(den, 1e-12), 0.0)


def arm_z(t, f):
    """z of the rank association of T and the rating within one arm"""
    n = t.shape[1]
    return np.arctanh(np.clip(spearman(t, f), -.999, .999)) * np.sqrt((n - 3) / 1.06)


def topq_p(t, f, share=0.25):
    """one-sided rank-sum p-value that the top share by rating has larger T than the rest;
    ties in the rating must be broken by the caller"""
    n = t.shape[1]
    k = int(n * share)
    ts = np.take_along_axis(t, np.argsort(f, axis=1), axis=1)
    return st.mannwhitneyu(ts[:, n - k:], ts[:, :n - k], alternative='greater', axis=1, method='asymptotic').pvalue


def assoc_z(th, fh, tl, fl):
    n = th.shape[1]
    z = lambda r: np.arctanh(np.clip(r, -.999, .999)) * np.sqrt((n - 3) / 1.06)
    return (z(spearman(th, fh)) + z(spearman(tl, fl))) / np.sqrt(2)


def phi_z(dF, ws):
    """z of the pooled slope of dF on ws (arrays replicate x participant x round),
    participant-clustered; a strongly negative value flags wins that erode fairness"""
    xc, yc = ws - ws.mean((1, 2), keepdims=True), dF - dF.mean((1, 2), keepdims=True)
    sxx = (xc ** 2).sum((1, 2))
    slope = (xc * yc).sum((1, 2)) / sxx
    res = yc - slope[:, None, None] * xc
    se = np.sqrt(((xc * res).sum(2) ** 2).sum(1)) / sxx
    return slope / se, slope


def decisions(d):
    """d: dict of arrays (replicate x pair [x round]): fh, fl, eh, el (last ratings), th, tl
    (probe statistics), fl_rounds (LOW fairness, rounds 3-6), wl (LOW win share, rounds 4-6),
    jit (tie-breaking jitter for the HIGH rating). Returns the six decisions and psi-hat."""
    psi, lo, hi = fieller(d['th'], d['tl'])
    _, _, hi_p = fieller(d['th'], d['tl'], paired=True)
    zphi, slope = phi_z(d['fl_rounds'][:, :, 1:] - d['fl_rounds'][:, :, :-1], d['wl'])
    out = dict(H1a=signed_rank_z(d['fl'] - d['fh']) > ZC, K3=signed_rank_z(d['eh'] - d['el']) > ZC,
               D1=hi < 1, D1_paired=hi_p < 1,
               FREEZE=freeze_upper(d['th'], d['fh'] + d['jit'], d['tl']) < 0.5,
               ASSOC=assoc_z(d['th'], d['fh'] + d['jit'], d['tl'], d['fl'] + d['jit']) > ZC,
               PHI=zphi < -ZC, psi=psi, psi_lo=lo, psi_hi=hi, phi_slope=slope)
    out['PAIR'] = out['H1a'] & out['D1']
    out['FULL'] = out['H1a'] & out['K3'] & out['D1'] & out['FREEZE'] & out['ASSOC'] & ~out['PHI']
    rest = out['H1a'] & out['K3'] & out['D1'] & out['FREEZE'] & ~out['PHI']          # AD-Y2
    out['ASSOC_H'] = arm_z(d['th'], d['fh'] + d['jit']) > ZC
    out['ASSOC_L'] = arm_z(d['tl'], d['fl'] + d['jit']) > ZC
    out['TOPQ'] = topq_p(d['th'], d['fh'] + d['jit']) < ALPHA1
    out['FULL_H'], out['FULL_T'] = rest & out['ASSOC_H'], rest & out['TOPQ']
    return out
