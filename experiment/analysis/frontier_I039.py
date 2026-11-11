"""KGi-DISS-I039 part F (testing, coverage, state dependence): Monte Carlo at the information
frontier, sampling from the exact likelihood tables (freeze 00_freeze_I039.yaml).
Needs records/likelihood_pools_I039.npz. Seed 136100.
    python experiment/analysis/frontier_I039.py > records/frontier_I039.txt
"""
import numpy as np
from scipy import stats as st

import estimand_core_I038 as ec
import likelihood_core_I039 as lc

rng = np.random.default_rng(136100)
Z = np.load('records/likelihood_pools_I039.npz')
G = {k: {a: Z[f"{k}_{a}"] for a in ('HIGH', 'LOW')} for k in ('P0', 'P1', 'P2', 'P3', 'P4')}
OTHER = {'P0': 'P4', 'P1': 'P4', 'P2': 'P4', 'P3': 'P4', 'P4': 'P1'}
_M = {}


def model(k, r):
    if (k, r) not in _M:
        _M[(k, r)] = lc.Model(G[k], G[OTHER[k]], r, sigmas=(12.0,))
    return _M[(k, r)]


ALPHA = ec.ALPHA1
ZC = st.norm.ppf(1 - ALPHA)
NGRID = (4, 6, 8, 10, 12, 16, 20, 24, 30, 36, 48, 60, 72)
LOG = lambda p: np.log(np.maximum(p, 1e-300))
H0 = {**lc.BASE, 'c': 0.0}


def first90(ns, pw):
    return next((n for n, p in zip(ns, pw) if p >= .90), None)


def np_power(p0, p1, n, b=20000):
    """Neyman-Pearson test of simple p0 against simple p1 (dict arm -> table); returns size, power"""
    lam = {a: LOG(p1[a]) - LOG(p0[a]) for a in p0}
    s0 = sum(lam[a][lc.sample_idx(p0[a], n, b, rng)].sum(1) for a in p0)
    s1 = sum(lam[a][lc.sample_idx(p1[a], n, b, rng)].sum(1) for a in p0)
    crit = np.quantile(s0, 1 - ALPHA, method='higher')
    return np.mean(s0 > crit), np.mean(s1 > crit)


def fieller_d1(pH, pL, n, b=20000):
    xh = lc.TGRID[lc.sample_idx(pH, n, b, rng)]
    xl = lc.TGRID[lc.sample_idx(pL, n, b, rng)]
    lo, hi = ec.fieller(xh.mean(1), xh.var(1, ddof=1) / n, xl.mean(1), xl.var(1, ddof=1) / n, 2 * n - 2)
    return np.mean(hi < 1)


print("KGi-DISS-I039 part F: power and coverage at the information frontier (seed 136100; one-sided .005)\n")

# ------------------------------------------------------------------ A. Neyman-Pearson
print("A. most powerful test of c = 0 against c = 1, gate point and nuisances known (20,000 replicates)")
print("   power by n per arm: " + "  ".join(f"{n:>5}" for n in NGRID) + "   n for .90")
resA = {}
for r in ec.RULES:
    for k in G:
        m = model(k, r)
        p0 = {a: m.pT(a, H0) for a in ('HIGH', 'LOW')}
        p1 = {a: m.pT(a, lc.BASE) for a in ('HIGH', 'LOW')}
        pw = [np_power(p0, p1, n)[1] for n in NGRID]
        fl = [fieller_d1(p1['HIGH'], p1['LOW'], n) for n in NGRID]
        resA[(k, r)] = (first90(NGRID, pw), first90(NGRID, fl))
        print(f"   {k} {r:7s} T only, NP   " + "  ".join(f"{x:.3f}" for x in pw) + f"   {resA[(k, r)][0]}")
        print(f"   {k} {r:7s} interval D1  " + "  ".join(f"{x:.3f}" for x in fl) + f"   {resA[(k, r)][1]}", flush=True)
        if k in ('P1', 'P4'):
            j0 = {a: m.pFT(a, H0).ravel() for a in ('HIGH', 'LOW')}
            j1 = {a: m.pFT(a, lc.BASE).ravel() for a in ('HIGH', 'LOW')}
            pj = [np_power(j0, j1, n)[1] for n in NGRID]
            print(f"   {k} {r:7s} (F, T), NP   " + "  ".join(f"{x:.3f}" for x in pj) + f"   {first90(NGRID, pj)}", flush=True)
size = [fieller_d1(model('P1', 'event').pT('HIGH', H0), model('P1', 'event').pT('LOW', H0), n) for n in (12, 24, 72)]
print(f"   size of the interval decision under c = 0 at n = 12, 24, 72: " + ", ".join(f"{x:.4f}" for x in size))

# ------------------------------------------------------------------ B. likelihood ratio with the baseline weight profiled
print("\nB. likelihood-ratio test with the baseline weight profiled out (event rule; 10,000 replicates; critical value set at weight .5)")
KAP = np.round(np.arange(.30, .7001, .025), 3)
for k in ('P1', 'P4'):
    m = model(k, 'event')
    tab = {(c, kp): {a: m.pT(a, {**lc.BASE, 'c': c, 'kap': kp}) for a in ('HIGH', 'LOW')} for c in (0.0, 1.0) for kp in KAP}
    LH = {c: np.array([LOG(tab[(c, kp)]['HIGH']) for kp in KAP]) for c in (0.0, 1.0)}
    LL = {c: np.array([LOG(tab[(c, kp)]['LOW']) for kp in KAP]) for c in (0.0, 1.0)}

    def glr(truth, n, b=10000):
        ch = lc.counts_of(lc.sample_idx(tab[truth]['HIGH'], n, b, rng), 161)
        cl = lc.counts_of(lc.sample_idx(tab[truth]['LOW'], n, b, rng), 161)
        l1 = (ch @ LH[1.0].T + cl @ LL[1.0].T).max(1)
        l0 = (ch @ LH[0.0].T + cl @ LL[0.0].T).max(1)
        return l1 - l0

    pw, sz = [], []
    for n in NGRID:
        crit = np.quantile(glr((0.0, 0.5), n), 1 - ALPHA, method='higher')
        pw.append(np.mean(glr((1.0, 0.5), n) > crit))
        if n in (12, 24, 72):
            sz.append((n, np.mean(glr((0.0, 0.35), n) > crit), np.mean(glr((0.0, 0.65), n) > crit)))
    print(f"   {k}: power by n  " + "  ".join(f"{x:.3f}" for x in pw) + f"   n for .90: {first90(NGRID, pw)}")
    print(f"       size when the true baseline weight is .35 | .65: " +
          "; ".join(f"n = {n}: {a:.4f} | {b:.4f}" for n, a, b in sz), flush=True)

# ------------------------------------------------------------------ C. coverage
print("\nC. profile-likelihood interval for psi (event rule, P1, 72 per arm, level .99, baseline weight profiled; 2,000 replicates)")
CG = np.round(np.arange(0, 1.0001, .025), 3)
m = model('P1', 'event')
tabs = {(c, kp): {a: m.pT(a, {**lc.BASE, 'c': c, 'kap': kp}) for a in ('HIGH', 'LOW')} for c in CG for kp in KAP}
LHc = np.array([[LOG(tabs[(c, kp)]['HIGH']) for kp in KAP] for c in CG])
LLc = np.array([[LOG(tabs[(c, kp)]['LOW']) for kp in KAP] for c in CG])
psi_c = np.array([(lc.TGRID @ tabs[(c, .5)]['HIGH']) / (lc.TGRID @ tabs[(c, .5)]['LOW']) for c in CG])
chi = st.chi2.ppf(.99, 1)
print("   truth c   psi     profile interval: coverage  median width  share with c-hat at 1 | Fieller: coverage  median width | width ratio")
for c0 in (0.5, 0.75, 0.9, 1.0):
    n, b = 72, 2000
    ih, il = lc.sample_idx(tabs[(c0, .5)]['HIGH'], n, b, rng), lc.sample_idx(tabs[(c0, .5)]['LOW'], n, b, rng)
    ch, cl = lc.counts_of(ih, 161), lc.counts_of(il, 161)
    ll = (np.einsum('bt,ckt->bck', ch, LHc) + np.einsum('bt,ckt->bck', cl, LLc)).max(2)      # profiled over the weight
    keep = 2 * (ll.max(1, keepdims=True) - ll) <= chi
    lo = np.where(keep, psi_c[None, :], np.inf).min(1)
    hi = np.where(keep, psi_c[None, :], -np.inf).max(1)
    psi0 = psi_c[list(CG).index(c0)]
    xh, xl = lc.TGRID[ih], lc.TGRID[il]
    flo, fhi = ec.fieller(xh.mean(1), xh.var(1, ddof=1) / n, xl.mean(1), xl.var(1, ddof=1) / n, 2 * n - 2)
    print(f"   {c0:<5}     {psi0:.3f}   {np.mean((lo <= psi0 + 1e-9) & (psi0 <= hi + 1e-9)):.4f}    {np.median(hi - lo):.3f}         "
          f"{np.mean(CG[ll.argmax(1)] == 1.0):.3f}                 | {np.mean((flo <= psi0) & (psi0 <= fhi)):.4f}    {np.median(fhi - flo):.3f}"
          f"        | {np.median(hi - lo) / np.median(fhi - flo):.2f}", flush=True)

# ------------------------------------------------------------------ D. state dependence
print("\nD. state dependence (the negative of mean sufficiency): T-F association within arm, 72 per arm, 4,000 replicates")


def spearman(idx):
    f, t = st.rankdata(idx // 161, axis=1), st.rankdata(idx % 161, axis=1)
    f, t = f - f.mean(1, keepdims=True), t - t.mean(1, keepdims=True)
    den = np.sqrt((f ** 2).sum(1) * (t ** 2).sum(1))
    return np.where(den > 0, (f * t).sum(1) / np.maximum(den, 1e-12), 0.0)


def e2(JH, JL, n=72, b=4000):
    rh = spearman(lc.sample_idx(JH.ravel(), n, b, rng))
    rl = spearman(lc.sample_idx(JL.ravel(), n, b, rng))
    zh, zl = np.arctanh(np.clip(rh, -.999, .999)), np.arctanh(np.clip(rl, -.999, .999))
    return (np.mean(zh * np.sqrt((n - 3) / 1.06) > ZC), np.mean((zh - zl) / np.sqrt(2 * 1.06 / (n - 3)) > ZC),
            rh.mean(), rl.mean())


print("   gate, full coupling:   E2a (HIGH only)   E2b (HIGH minus LOW)   mean Spearman HIGH / LOW")
for r in ec.RULES:
    for k in G:
        a, b_, rh, rl = e2(model(k, r).pFT('HIGH', lc.BASE), model(k, r).pFT('LOW', lc.BASE))
        print(f"   {k} {r:7s}              {a:.3f}             {b_:.3f}                  {rh:+.3f} / {rl:+.3f}", flush=True)

m = model('P1', 'event')
q, kap = lc.BASE['q'], lc.BASE['kap']
K = m.K[12.0]
i0 = int(round(-lc.WGRID[0] / lc.DW))
kw = lambda w: K[int(round((w - lc.WGRID[0]) / lc.DW))]
pF = {a: m.pFT(a, lc.BASE).sum(1) for a in ('HIGH', 'LOW')}
riv = {}
riv['R3 (ratings move, gain does not)'] = {a: np.outer(pF[a], m.pT(a, H0)) for a in pF}
gbar = G['P1']['HIGH'] @ lc.LGRID
riv['HS (everyone in HIGH slowed by the same factor)'] = {
    'HIGH': np.outer(pF['HIGH'], q * K[i0] + (1 - q) * kw(round(kap * gbar, 3))),
    'LOW': np.outer(pF['LOW'], m.pT('LOW', H0))}
zs, zw = np.polynomial.hermite_e.hermegauss(21)
zw = zw / zw.sum()
sh = {}
for a in pF:
    J = np.zeros((21, 161))
    for z, w in zip(zs, zw):
        hf = lc.report_pmf(50 + lc.BASE['a'] * (100 * lc.LGRID - 50) + 8 * z, lc.BASE['sr'])
        J += w * np.outer(G['P1'][a] @ hf, q * K[i0] + (1 - q) * kw(round(float(np.clip(kap * (1 + .3 * z), 0, 1.0)), 3)))
    sh[a] = J
riv['SH (a trait moves rating and weight in both arms)'] = sh
print("   rivals at P1 (event rule):  E2a      E2b      mean Spearman HIGH / LOW    psi")
for nm, J in riv.items():
    a, b_, rh, rl = e2(J['HIGH'], J['LOW'])
    psi = (lc.TGRID @ J['HIGH'].sum(0)) / (lc.TGRID @ J['LOW'].sum(0))
    print(f"   {nm:52s} {a:.4f}   {b_:.4f}   {rh:+.3f} / {rl:+.3f}             {psi:.3f}", flush=True)

# ------------------------------------------------------------------ E. frontier for dependence
print("\nE. frontier for state dependence in HIGH: independence with the model's own marginals against the model's joint")
NG2 = (24, 36, 48, 60, 72, 96, 120, 150, 200, 300, 450)
print("   n per arm:            " + "  ".join(f"{n:>5}" for n in NG2) + "   n for .90")
for k, r in (('P1', 'event'), ('P2', 'event'), ('P4', 'event'), ('P1', 'outcome')):
    J = model(k, r).pFT('HIGH', lc.BASE)
    ind = np.outer(J.sum(1), J.sum(0))
    pw = [np_power({'HIGH': ind.ravel()}, {'HIGH': J.ravel()}, n, b=10000)[1] for n in NG2]
    ea = [e2(J, model(k, r).pFT('LOW', lc.BASE), n=n, b=2000)[0] for n in NG2]
    print(f"   {k} {r:7s} NP        " + "  ".join(f"{x:.3f}" for x in pw) + f"   {first90(NG2, pw)}")
    print(f"   {k} {r:7s} E2a       " + "  ".join(f"{x:.3f}" for x in ea) + f"   {first90(NG2, ea)}", flush=True)

# ------------------------------------------------------------------ F. addendum AD-L2: pooled association and the conjunction
print("\nF. AD-L2: association pooled over the two arms (E2c) and its conjunction with the interval decision psi < 1; 72 per arm, 4,000 replicates")


def e2c(JH, JL, n=72, b=4000):
    ih, il = lc.sample_idx(JH.ravel(), n, b, rng), lc.sample_idx(JL.ravel(), n, b, rng)
    zh = np.arctanh(np.clip(spearman(ih), -.999, .999)) * np.sqrt((n - 3) / 1.06)
    zl = np.arctanh(np.clip(spearman(il), -.999, .999)) * np.sqrt((n - 3) / 1.06)
    assoc = (zh + zl) / np.sqrt(2) > ZC
    xh, xl = lc.TGRID[ih % 161], lc.TGRID[il % 161]
    _, hi = ec.fieller(xh.mean(1), xh.var(1, ddof=1) / n, xl.mean(1), xl.var(1, ddof=1) / n, 2 * n - 2)
    return np.mean(assoc), np.mean(hi < 1), np.mean(assoc & (hi < 1))


print("   gate, full coupling:   E2c     psi < 1    both")
for r in ec.RULES:
    for k in G:
        a, d, both = e2c(model(k, r).pFT('HIGH', lc.BASE), model(k, r).pFT('LOW', lc.BASE))
        print(f"   {k} {r:7s}           {a:.3f}   {d:.3f}      {both:.3f}", flush=True)
print("   rivals at P1 (event rule):                             E2c      psi < 1   both")
for nm, J in riv.items():
    a, d, both = e2c(J['HIGH'], J['LOW'])
    print(f"   {nm:52s} {a:.4f}   {d:.4f}    {both:.4f}", flush=True)
