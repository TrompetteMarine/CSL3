"""KGi-DISS-I040 part 3: human tests of the kernel and aggregation theorems, evaluated on
the model's own distributions (freeze 00_freeze_I040.yaml). Needs
records/likelihood_pools_I039.npz. Seed 137100.
    python experiment/analysis/theorem_tests_I040.py > records/theorem_tests_I040.txt
"""
import numpy as np
from scipy import stats as st

import estimand_core_I038 as ec
import likelihood_core_I039 as lc
import probe_generator as pg

rng = np.random.default_rng(137100)
Z = np.load('records/likelihood_pools_I039.npz')
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
G = {k: {a: Z[f"{k}_{a}"] for a in ('HIGH', 'LOW')} for k in PTS}
_M = {}
model = lambda k, r: _M.setdefault((k, r), lc.Model(G[k], G['P4' if k != 'P4' else 'P1'], r, sigmas=(12.0,)))
ZC = st.norm.ppf(.995)
print("KGi-DISS-I040 part 3: tests of the kernel and aggregation theorems on the model's own distributions (seed 137100)\n")


def draw(k, r, c, n, b):
    """b samples of n HIGH participants (rating F, revision T) and n LOW revisions"""
    m = model(k, r)
    th = {**lc.BASE, 'c': c}
    ih = lc.sample_idx(m.pFT('HIGH', th).ravel(), n, b, rng)
    tl = lc.TGRID[lc.sample_idx(m.pT('LOW', th), n, b, rng)]
    f = lc.REP[ih // 161] + rng.uniform(-.01, .01, ih.shape)        # random tie-break among equal ratings
    return f, lc.TGRID[ih % 161], tl


# ------------------------------------------------------------------ A. T6: freeze
print("A. T6 (freeze). Stratum = the third of HIGH with the lowest fairness rating. Decision 'residual uptake below")
print("   delta' = upper limit of E[T | stratum] / E[T | LOW] below delta (one-sided .005). 4,000 replicates.")
print("   point rule     coupling   uptake ratio in the stratum   decision rate, delta .25: n = 72 | 150 | 300      delta .5: n = 72 | 150 | 300")
for r in ec.RULES:
    for k in ('P1', 'P2', 'P4'):
        for c in (1.0, 0.9, 0.75, 0.5):
            row, ratio = {}, None
            for n in (72, 150, 300):
                f, t, tl = draw(k, r, c, n, 4000)
                kk = n // 3
                order = np.argsort(f, axis=1)[:, :kk]
                ts = np.take_along_axis(t, order, axis=1)
                _, hi = ec.fieller(ts.mean(1), ts.var(1, ddof=1) / kk, tl.mean(1), tl.var(1, ddof=1) / n, kk + n - 2)
                row[n] = (np.mean(hi < .25), np.mean(hi < .5))
                ratio = ts.mean() / tl.mean()
            print(f"   {k}    {r:7s}  {c:<4}       {ratio:.3f}                         "
                  + " | ".join(f"{row[n][0]:.3f}" for n in row) + "                    " + " | ".join(f"{row[n][1]:.3f}" for n in row), flush=True)

# ------------------------------------------------------------------ B. T8 / T15: state dependence by strata
print("\nB. T8 / T15 (state dependence) within HIGH, 72 per arm, full coupling: one-sided rank tests at .005 that revision is larger")
print("   where the rating is higher. 2,000 replicates. (I039 Spearman, HIGH only, one-update rule: P1 .294, P2 .410, P3 .313, P4 .999)")
print("   point rule      top third vs bottom third   top half vs bottom half   top quarter vs the rest   Spearman")


def split_power(f, t, lo_q, hi_q):
    n = f.shape[1]
    order = np.argsort(f, axis=1)
    lo = np.take_along_axis(t, order[:, :int(n * lo_q)], axis=1)
    hi = np.take_along_axis(t, order[:, n - int(n * hi_q):], axis=1)
    return np.mean([st.mannwhitneyu(hi[i], lo[i], alternative='greater').pvalue < .005 for i in range(len(f))])


def spearman_power(f, t):
    rf, rt = st.rankdata(f, axis=1), st.rankdata(t, axis=1)
    rf, rt = rf - rf.mean(1, keepdims=True), rt - rt.mean(1, keepdims=True)
    r = (rf * rt).sum(1) / np.sqrt((rf ** 2).sum(1) * (rt ** 2).sum(1))
    return np.mean(np.arctanh(np.clip(r, -.999, .999)) * np.sqrt((f.shape[1] - 3) / 1.06) > ZC)


for r in ec.RULES:
    for k in PTS:
        f, t, _ = draw(k, r, 1.0, 72, 2000)
        print(f"   {k}    {r:7s}   {split_power(f, t, 1 / 3, 1 / 3):.3f}                       {split_power(f, t, .5, .5):.3f}"
              f"                     {split_power(f, t, .75, .25):.3f}                     {spearman_power(f, t):.3f}", flush=True)
m = model('P1', 'event')
pf = m.pFT('HIGH', lc.BASE).sum(1)
ind = np.outer(pf, m.pT('HIGH', lc.BASE)).ravel()                   # same marginals, no dependence
ih = lc.sample_idx(ind, 72, 2000, rng)
f0, t0 = lc.REP[ih // 161] + rng.uniform(-.01, .01, ih.shape), lc.TGRID[ih % 161]
print(f"   size when revision does not depend on the rating (P1 marginals): {split_power(f0, t0, 1 / 3, 1 / 3):.4f}, "
      f"{split_power(f0, t0, .5, .5):.4f}, {split_power(f0, t0, .75, .25):.4f}, {spearman_power(f0, t0):.4f}")

# ------------------------------------------------------------------ C. T12: two types
print("\nC. T12 (two-type inversion) applied to the model's own HIGH gain distribution, gain = 1 - c (1 - legitimacy):")
print("   returned coupling (and shut share) at each true coupling")
print("   point   " + "   ".join(f"c = {c:<4}        " for c in (1.0, .9, .75, .5)))
for k in PTS:
    row = []
    for c in (1.0, .9, .75, .5):
        g = 1 - c * (1 - lc.LGRID)
        psi = G[k]['HIGH'] @ g
        v = G[k]['HIGH'] @ (g - psi) ** 2
        ch = (v + (1 - psi) ** 2) / (1 - psi)
        row.append(f"{ch:.3f} ({(1 - psi) / ch:.3f})")
    print(f"   {k}      " + "    ".join(row))

# ------------------------------------------------------------------ D. T10: two-record probe
print("\nD. T10 (two records per ticket): excess of the normalised dispersion of revision weights in HIGH over LOW,")
print("   D = V_H / m_H^2 - V_L / m_L^2 with V = m (1 - m) - (second-step response); 400,000 simulated participants per arm")


def two_step(k, r, n, sigma=12.0, q=0.10):
    out = {}
    for arm in ('HIGH', 'LOW'):
        l = rng.choice(lc.LGRID, size=n, p=G[k][arm] / G[k][arm].sum())
        w = np.where(rng.random(n) < q, 0.0, pg.weight(l, ec.M, r))
        t1, t2 = np.zeros(n), np.zeros(n)
        for _ in range(2):                                          # two pairs of tickets
            for e, sgn in ((0.9, 1.0), (0.1, -1.0)):
                b0 = np.clip(rng.normal(50, 10, n), 5, 95)
                b1 = b0 + w * (100 * e - b0)
                b2 = b1 + w * (100 * e - b1)
                r0, r1, r2 = (pg._round5(x + rng.normal(0, sigma, n)) for x in (b0, b1, b2))
                t1 += sgn * (r1 - r0) / 2
                t2 += sgn * (r2 - r1) / 2
        out[arm] = (t1 / 80, t2 / 80, w)
    return out


for k, r in (('P1', 'event'), ('P4', 'event'), ('P1', 'outcome'), ('P4', 'outcome')):
    d = two_step(k, r, 400000)
    stat, var, line = {}, {}, []
    for arm, (a1, a2, w) in d.items():
        m1, m2 = a1.mean(), a2.mean()
        v = m1 * (1 - m1) - m2
        infl = ((1 - 2 * m1) * (a1 - m1) - (a2 - m2)) / m1 ** 2 - 2 * v / m1 ** 3 * (a1 - m1)
        stat[arm], var[arm] = v / m1 ** 2, infl.var()
        line.append(f"{arm}: mean weight {m1:.3f} (true {w.mean():.3f}), dispersion {v:.4f} (true variance {w.var():.4f})")
    D = stat['HIGH'] - stat['LOW']
    n90 = (ZC + st.norm.ppf(.90)) ** 2 * (var['HIGH'] + var['LOW']) / D ** 2
    msg = f"   {k} {r:7s}: " + "; ".join(line) + f"; D = {D:.3f}; asymptotic n per arm for .90: {n90:,.0f}"
    if n90 <= 2000:
        n = int(np.ceil(n90)); hit = 0
        for _ in range(1000):
            est, se2 = {}, {}
            for arm, (a1, a2, w) in d.items():
                i = rng.integers(0, len(a1), n)
                x1, x2 = a1[i], a2[i]
                m1, m2 = x1.mean(), x2.mean()
                v = m1 * (1 - m1) - m2
                infl = ((1 - 2 * m1) * (x1 - m1) - (x2 - m2)) / m1 ** 2 - 2 * v / m1 ** 3 * (x1 - m1)
                est[arm], se2[arm] = v / m1 ** 2, infl.var(ddof=1) / n
            hit += (est['HIGH'] - est['LOW']) / np.sqrt(se2['HIGH'] + se2['LOW']) > ZC
        msg += f"; Monte Carlo power at that n: {hit / 1000:.3f}"
    print(msg, flush=True)

# ------------------------------------------------------------------ E. T14 under both rules
print("\nE. T14 (psi >= 1 - c), from the likelihood tables: smallest margin psi - (1 - c) over couplings 0, .25, .5, .75, .85, .9, .95, 1")
for r in ec.RULES:
    row = []
    for k in PTS:
        mg_ = min(model(k, r).psi({**lc.BASE, 'c': c}) - (1 - c) for c in (0.0, .25, .5, .75, .85, .9, .95, 1.0))
        row.append(f"{k} {mg_:+.3f}")
    print(f"   {r:7s}: " + "   ".join(row))
