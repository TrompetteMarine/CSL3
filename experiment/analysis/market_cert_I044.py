"""KGi-DISS-I044: the yoked design as a live economy (freeze 00_freeze_I044.yaml).

A session holds two markets of N traders. Supply of each good and every trader's private value
are scripted for each of the 720 clearings. At each clearing a Walrasian auctioneer clears each
good: the scripted units go to the highest bids and the price is the highest losing bid (the
lowest market-clearing price), or the reserve when supply exceeds bidders. The reference a
trader sees is the other market's fills. Twin sessions share the focal market's script and
differ in the neighbour's supply (rich: HIGH; equally scarce: LOW) and in the people.

The gate kernel is the one of twins_I040.twins, step for step (gate X1). Seed 140000.
    python experiment/analysis/market_cert_I044.py > records/market_cert_I044.txt
"""
import sys

import numpy as np
from scipy import stats as st

sys.path.insert(0, 'experiment/analysis')
import estimand_core_I038 as ec
import market_generator as mg
import probe_generator as pg
import yoked_analysis as ya
from probe_design_I037 import ODDS, P1TAG

SEED = 140000
K, ROUNDS = 120, 6
RICH, SCARCE = (0.55, 0.22), (0.15, 0.05)       # arrival chance per trader slot and clearing: (plentiful good, other good)
POOL, B = 2400, 2000
SIG_R, SIG_F = 5.8, 12.0
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
CHECKS = dict(n=0, bad=0)
sig = lambda x: 1 / (1 + np.exp(-x))
r5 = lambda x: np.clip(np.round(x / 5) * 5, 0, 100)
tcrit = lambda df: st.t.ppf(1 - ec.ALPHA1, df)


# ------------------------------------------------------------------ the kernel step (shared with the bridge)

def kstep(Q, L, A, arm, R, ref, rho, nuf, nur, chi):
    """one outcome event of the gate kernel; the order of the updates is that of twins_I040.twins"""
    q = np.take_along_axis(Q, arm[..., None], -1)[..., 0]
    np.put_along_axis(Q, arm[..., None], (q + mg.ALPHA * L * (R - q))[..., None], -1)
    D = mg.PHIM * np.maximum(A - R, 0) + mg.PHIP * np.maximum(R - A, 0)
    L = np.clip(L - nuf * np.maximum(D - mg.TAUF, 0) + nur * (D <= mg.TAUF), 0, 1)
    A = np.clip((1 - rho) * A + rho * ((1 - chi) * R + chi * ref), 0, 1)
    return L, A


def solo(pt, n, rng):
    """the certified individual design (fixed fill chances, a board per person) on kstep: gate X1"""
    nuf, nur, chi = mg.NUF * pt[1], mg.NUF * pt[1] * pt[2], pt[3]
    (ph1, mu_ref), ph2 = P1TAG[ec.P1], ODDS[ec.D['odds']]
    out = {}
    for regime in ('HIGH', 'LOW'):
        rho = np.where(rng.random(n) < .5, .002, .02)
        Q, L, A = np.full((n, 2), .5), np.full(n, mg.L0), np.full(n, mg.A0)
        ring, hits, reg1 = np.zeros((n, 15)), np.zeros(n), rng.random(n) < .5
        for t in range(K * ROUNDS):
            odds = ph1 if t < K else ph2
            if t % K == 0:
                arm = (rng.random(n) >= sig(mg.BETA * (Q[:, 0] - Q[:, 1]))).astype(int)
            R = (rng.random(n) < np.where(arm == 0, odds[0], odds[1])).astype(float)
            trail = np.full(n, .5) if t == 0 else ring[:, :min(t, 15)].mean(1)
            high = reg1 if t < K else np.full(n, regime == 'HIGH')
            hits += rng.random(n) < np.where(high, mu_ref, np.clip(trail, .05, .95))
            ring[:, t % 15] = R
            ref = np.where(high, hits / (t + 1), ring[:, :min(t + 1, 15)].mean(1))
            L, A = kstep(Q, L, A, arm, R, ref, rho, nuf, nur, chi)
        out[regime] = L
    return out


# ------------------------------------------------------------------ a pool of sessions

def run(pt, S, N, seeds, neighbour_rich, inst='unit', ref='trail', shade=False, reversal=None):
    """S sessions of two markets (0 focal, 1 neighbour) of N traders. seeds: focal script (shared by
    twins), focal people, neighbour (script and people)."""
    gs, gp, go = (np.random.default_rng(s) for s in seeds)
    nuf, nur, chi = mg.NUF * pt[1], mg.NUF * pt[1] * pt[2], pt[3]
    sh = (S, 2, N)
    rho = np.stack([np.where(gp.random((S, N)) < .5, .002, .02), np.where(go.random((S, N)) < .5, .002, .02)], 1)
    mark = np.stack([gp.uniform(0, .5, (S, N)), go.uniform(0, .5, (S, N))], 1) if shade else np.zeros(sh)
    Q, L, A = np.full(sh + (2,), .5), np.full(sh, mg.L0), np.full(sh, mg.A0)
    ring, cum = np.zeros((S, 2, 15)), np.zeros((S, 2))
    Lr, wins = np.empty(sh + (ROUNDS,)), np.zeros(sh + (ROUNDS,))
    cash, units, sold, on0 = np.zeros(sh), np.zeros((S, 2, ROUNDS)), np.zeros((S, 2, ROUNDS)), np.zeros((S, 2, ROUNDS))
    for t in range(K * ROUNDS):
        r = t // K
        if t % K == 0:
            uc = np.stack([gp.random((S, N)), go.random((S, N))], 1)
            arm = (uc >= sig(mg.BETA * (Q[..., 0] - Q[..., 1]))).astype(int)        # the good bid for in this round
            on0[..., r] = (arm == 0).mean(-1)
            rich = (True, True) if r == 0 else (False, neighbour_rich)
            pis = np.array([RICH if x else SCARCE for x in rich])
            if reversal is not None and r >= reversal:                              # scarce markets: the plentiful good switches
                pis = np.where(np.array(rich)[:, None], pis, pis[:, ::-1])
        k = np.stack([gs.binomial(N, pis[0], (S, 2)), go.binomial(N, pis[1], (S, 2))], 1)
        v = np.stack([gs.random((S, N)), go.random((S, N))], 1)
        bid = v * (1 - mark)
        R = np.zeros(sh)
        for g in (0, 1):
            m = arm == g
            n, kg = m.sum(-1), k[..., g]
            units[..., r] += kg
            sold[..., r] += np.minimum(kg, n)
            if inst == 'unit':
                b = np.where(m, bid, -1.0)
                above = (b[..., None, :] > b[..., :, None]).sum(-1)                 # bids strictly above one's own
                win = m & (above < kg[..., None])
                price = np.where(m & ~win, b, 0.0).max(-1)                          # highest losing bid; reserve 0
                R = np.where(win, 1.0, R)
                cash += np.where(win, v - price[..., None], 0.0)
                if t % 40 == 0:                                                     # gate X2: the price clears the market
                    hi = ((b > price[..., None]) & m).sum(-1)
                    ge = ((b >= price[..., None]) & m).sum(-1)
                    CHECKS['n'] += hi.size
                    CHECKS['bad'] += int(((hi > kg) | (ge < np.minimum(kg, n))).sum())
            else:                                                                   # divisible: every bidder gets the same share
                R = np.where(m, np.minimum(1.0, kg / np.maximum(n, 1))[..., None], R)
        fill = R.mean(-1)
        ring[..., t % 15] = fill
        cum += fill
        shown = ring[..., :min(t + 1, 15)].mean(-1) if ref == 'trail' else cum / (t + 1)
        L, A = kstep(Q, L, A, arm, R, shown[:, ::-1, None], rho, nuf, nur, chi)     # the reference is the other market
        wins[..., r] += R
        if (t + 1) % K == 0:
            Lr[..., r] = L
    return dict(L=Lr, wins=wins, cash=cash, units=units, sold=sold, on0=on0)


def twins(cfg, k, N=6, **kw):
    """a HIGH pool and its LOW twin pool: same focal script, other people, other neighbour"""
    c, p = CFG.index(cfg), PTS.index(k)
    return {arm: run(PT[k], POOL, N, ([SEED, c, p, 0], [SEED, c, p, 1 + 2 * a], [SEED, c, p, 2 + 2 * a]), arm == 'HIGH', **kw)
            for a, arm in enumerate(('HIGH', 'LOW'))}


# ------------------------------------------------------------------ what is measured on a trader

def rev(w, e, rng):
    b0 = np.clip(rng.normal(pg.PRIOR_MU, pg.PRIOR_SD, w.shape), 5, 95)
    pre = r5(b0 + rng.normal(0, SIG_F, w.shape))
    belief = b0 + w * (100 * e - b0)
    return r5(belief + rng.normal(0, SIG_F, w.shape)) - pre, belief


def weights(L, c, rule, rng):
    g = 1 - c * (1 - L)
    return np.where(rng.random(L.shape) < 0.10, 0.0, pg.weight(g, ec.M, rule))


def measures(o, mkt, rng, c=1.0, rule='event'):
    """last fairness rating, probe statistic (two record pairs) and beliefs of the traders of one market"""
    L = o['L'][:, mkt, :, -1]
    F = r5(50 + .5 * (100 * L - 50) + rng.normal(0, SIG_R, L.shape))
    w = weights(L, c, rule, rng)
    (d1, b1), (d0, b0), (e1, _), (e0, _) = rev(w, .9, rng), rev(w, .1, rng), rev(w, .9, rng), rev(w, .1, rng)
    return dict(F=F, T=.5 * ((d1 - d0) + (e1 - e0)), w=w, L=L, bel=(b1, b0))


def shift(x, icc, rng):
    """a session effect: one normal shift per market, with the given intraclass correlation"""
    if icc == 0:
        return x
    sd = np.sqrt(x.var(1, ddof=1).mean())
    return x + sd * np.sqrt(icc / (1 - icc)) * rng.normal(size=(len(x), 1))


def icc1(x):
    """intraclass correlation of a trader-level variable (one-way analysis of variance)"""
    n = x.shape[1]
    msb, msw = n * x.mean(1).var(ddof=1), x.var(1, ddof=1).mean()
    return (msb - msw) / (msb + (n - 1) * msw)


# ------------------------------------------------------------------ tests on markets

def h1a_m(fh, fl):
    d = fl - fh
    return d.mean(1) / (d.std(1, ddof=1) / np.sqrt(d.shape[1])) > tcrit(d.shape[1] - 1)


def fieller_m(th, tl):
    """ratio of the means of market values and its upper limit (t quantile, 2S - 2 df)"""
    S = th.shape[1]
    a, b = th.mean(1), tl.mean(1)
    va, vb = th.var(1, ddof=1) / S, tl.var(1, ddof=1) / S
    t2 = tcrit(2 * S - 2) ** 2
    den = b ** 2 - t2 * vb
    disc = a ** 2 * b ** 2 - den * (a ** 2 - t2 * va)
    ok = (den > 0) & (b > 0) & (disc >= 0)
    return a / b, np.where(ok, (a * b + np.sqrt(np.maximum(disc, 0))) / np.where(ok, den, 1), np.inf)


def paired_t(d):
    return d.mean(1) / (d.std(1, ddof=1) / np.sqrt(d.shape[1])) > tcrit(d.shape[1] - 1)


def conf(H, Lo, S, rng, icc=0.0):
    """rates of the market-level confirmatory pair on B samples of S twin sessions"""
    fh, fl = shift(H['F'], icc, rng).mean(1), shift(Lo['F'], icc, rng).mean(1)
    th, tl = shift(H['T'], icc, rng).mean(1), shift(Lo['T'], icc, rng).mean(1)
    i = rng.integers(0, len(fh), (B, S))
    psi, hi = fieller_m(th[i], tl[i])
    h, d = h1a_m(fh[i], fl[i]), hi < 1
    return dict(H1a=h.mean(), D1=d.mean(), PAIR=(h & d).mean(), psi=psi.mean())


def naive(H, Lo, S, rng, icc=0.0):
    """the individual-level tests of I041 on the same data (traders in the same slot of twin markets as pairs)"""
    fh, fl, th, tl = (shift(x, icc, rng) for x in (H['F'], Lo['F'], H['T'], Lo['T']))
    i = rng.integers(0, len(fh), (B, S))
    flat = lambda x: x[i].reshape(B, -1)
    return dict(H1a=(ya.signed_rank_z(flat(fl) - flat(fh)) > ya.ZC).mean(), D1=(ya.fieller(flat(th), flat(tl))[2] < 1).mean())


# ------------------------------------------------------------------ twelve records on one claim

def news(w, rng, steps=12):
    """closure after each record: the forecast contrast (favourable minus unfavourable claim) as a
    share of the gap between the two kinds of evidence; shape (..., steps)"""
    out = 0.0
    k = np.arange(1, steps + 1)
    for e in (.9, .1):
        b0 = np.clip(rng.normal(pg.PRIOR_MU, pg.PRIOR_SD, w.shape), 5, 95)
        f0 = r5(b0 + rng.normal(0, SIG_F, w.shape))
        belief = b0[..., None] + (100 * e - b0[..., None]) * (1 - (1 - w[..., None]) ** k)
        f = r5(belief + rng.normal(0, SIG_F, belief.shape))
        out = out + (f - f0[..., None]) * (1 if e > .5 else -1)
    return out / 80.0


def plat(c, S, rng):
    """PLAT on B samples of S markets: delta = [1 - (1 - E)^(11/4)] - L > 0"""
    E, Lw = c[..., 2:5].mean(-1).mean(1), c[..., 9:12].mean(-1).mean(1)             # market means
    i = rng.integers(0, len(E), (B, S))
    e, l = E[i], Lw[i]
    eb = np.clip(e.mean(1), -1, .999)
    delta = 1 - (1 - eb) ** 2.75 - l.mean(1)
    ge = 2.75 * (1 - eb) ** 1.75
    see, sll = e.var(1, ddof=1), l.var(1, ddof=1)
    sel = ((e - e.mean(1, keepdims=True)) * (l - l.mean(1, keepdims=True))).sum(1) / (S - 1)
    se = np.sqrt(np.maximum(ge ** 2 * see + sll - 2 * ge * sel, 1e-12) / S)
    return (delta / se > tcrit(S - 1)).mean(), delta.mean(), E.mean(), Lw.mean()


# ------------------------------------------------------------------ the claim market

def lmsr(belief, stake, rng, b=60.0, passes=1):
    """price of a claim in each market after every trader has moved it toward their belief within their stake"""
    S, N = belief.shape
    P, rows = np.full(S, .5), np.arange(S)
    tgt = np.clip(belief / 100, .02, .98)
    for _ in range(passes):
        order = np.argsort(rng.random((S, N)), 1)
        for j in range(N):
            i = order[:, j]
            q, m = tgt[rows, i], stake[rows, i]
            up = q > P
            cost = np.where(up, b * np.log((1 - P) / (1 - q)), b * np.log(P / q))
            part = np.where(up, 1 - (1 - P) * np.exp(-m / b), P * np.exp(-m / b))
            P = np.where(cost <= m, q, part)
    return P


def price_response(o, M, rng, share=.25, passes=1):
    stake = share * 5 * o['cash'][:, 0]
    return lmsr(M['bel'][0], stake, rng, passes=passes) - lmsr(M['bel'][1], stake, rng, passes=passes)


def x3(rng, n=200):
    """gate X3: under the highest-losing-bid price no unilateral change of a bid raises a trader's surplus"""
    worst = 0.0
    for _ in range(n):
        N, k = int(rng.integers(2, 9)), int(rng.integers(1, 6))
        v = rng.random(N)

        def surplus(bids, i):
            order = np.argsort(-bids)
            if i not in order[:k]:
                return 0.0
            return v[i] - (bids[order[k]] if N > k else 0.0)
        for i in range(N):
            base = surplus(v.copy(), i)
            for alt in np.linspace(0, 1.2, 61):
                bids = v.copy()
                bids[i] = alt
                worst = max(worst, surplus(bids, i) - base)
    return worst


CFG = ('base', 'div', 'cum', 'shade', 'rev5', 'N4', 'N8')
KW = dict(base={}, div=dict(inst='div'), cum=dict(ref='cum'), shade=dict(shade=True), rev5=dict(reversal=4),
          N4=dict(N=4), N8=dict(N=8))

if __name__ == '__main__':
    rng = np.random.default_rng([SEED, 99])
    f3 = lambda x: f"{x:.3f}"
    print(f"KGi-DISS-I044: the yoked design as a live economy ({POOL} sessions per arm and cell; {B} samples; seed {SEED})")
    print("markets of 6 traders and 12 twin sessions (72 traders per arm) unless stated; one-sided .005; t quantiles on market values\n")

    print("0. gates")
    s = solo(PT['P1'], 20000, np.random.default_rng([SEED, 98]))
    print(f"   X1 bridge, P1: the kernel step with one trader, fixed fill chances and a board: legitimacy at probe time HIGH {s['HIGH'].mean():.3f} "
          f"(share below .05: {(s['HIGH'] < .05).mean():.3f}), LOW {s['LOW'].mean():.3f}; certified .109 (.827), .869")
    print(f"   X3 truthful bidding: largest gain from changing one bid in 200 clearings: {x3(np.random.default_rng([SEED, 97])):.2e}")

    base = {k: twins('base', k) for k in PTS}
    M = {k: {a: measures(base[k][a], 0, rng) for a in ('HIGH', 'LOW')} for k in PTS}
    print(f"   X2 market clearing: {CHECKS['bad']} violations in {CHECKS['n']} checked clearings (so far)\n")

    print("1. levels in the live economy (focal market; unit orders; trailing reference)")
    print("   point  legitimacy at probe time HIGH (share below .05) | LOW   last fairness HIGH | LOW   fill rate, scarce rounds HIGH | LOW   "
          "cash earned HIGH | LOW   advantaged neighbour: legitimacy, fill rate")
    for k in PTS:
        h, lo = base[k]['HIGH'], base[k]['LOW']
        Lh, Ll = h['L'][:, 0, :, -1], lo['L'][:, 0, :, -1]
        fr = lambda o: o['wins'][:, 0, :, 1:].mean() / K
        print(f"   {k}     {Lh.mean():.3f} ({(Lh < .05).mean():.3f}) | {Ll.mean():.3f}                      {M[k]['HIGH']['F'].mean():.1f} | {M[k]['LOW']['F'].mean():.1f}"
              f"            {fr(h):.4f} | {fr(lo):.4f}                 {h['cash'][:, 0].mean():.2f} | {lo['cash'][:, 0].mean():.2f}"
              f"        {h['L'][:, 1, :, -1].mean():.3f}, {h['wins'][:, 1, :, 1:].mean() / K:.3f}", flush=True)
    h, lo = base['P1']['HIGH'], base['P1']['LOW']
    print("   P1 by round, legitimacy HIGH: " + " ".join(f3(x) for x in h['L'][:, 0].mean((0, 1))) + " | LOW: " + " ".join(f3(x) for x in lo['L'][:, 0].mean((0, 1))))
    print("   P1 intraclass correlation within a market (the model alone): fills in scarce rounds HIGH | LOW "
          f"{icc1(h['wins'][:, 0, :, 1:].sum(-1)):+.3f} | {icc1(lo['wins'][:, 0, :, 1:].sum(-1)):+.3f}; last fairness "
          f"{icc1(M['P1']['HIGH']['F']):+.3f} | {icc1(M['P1']['LOW']['F']):+.3f}; probe statistic {icc1(M['P1']['HIGH']['T']):+.3f} | {icc1(M['P1']['LOW']['T']):+.3f}")

    print("\n2. the confirmatory pair on markets (H1a_M | D1_M | both), mean psi-hat")
    print("   rule     point   12 twin sessions, no session effect      8 twin sessions                     12, intraclass correlation .2")
    Mo = {k: {a: measures(base[k][a], 0, rng, rule='outcome') for a in ('HIGH', 'LOW')} for k in PTS}
    for rule, MM in (('event', M), ('outcome', Mo)):
        for k in PTS:
            a, b, c = (conf(MM[k]['HIGH'], MM[k]['LOW'], S, rng, icc) for S, icc in ((12, 0), (8, 0), (12, .2)))
            cell = lambda s: f"{s['H1a']:.3f} | {s['D1']:.3f} | {s['PAIR']:.3f}  psi {s['psi']:.3f}"
            print(f"   {rule:7s}  {k}      {cell(a)}     {cell(b)}     {cell(c)}", flush=True)

    print("\n3. sizes at nominal .005, P1 (D1: ratings move, the gain does not; H1a: both markets on the LOW regime)")
    Mnull = {a: measures(base['P1'][a], 0, rng, c=0.0) for a in ('HIGH', 'LOW')}
    Mlow2 = measures(base['P1']['LOW'], 1, rng)
    print("   intraclass correlation   market-level D1_M | H1a_M        individual-level tests of I041: D1 | H1a")
    for icc in (0.0, 0.1, 0.2):
        d = conf(Mnull['HIGH'], Mnull['LOW'], 12, rng, icc)['D1']
        hh = conf(Mlow2, M['P1']['LOW'], 12, rng, icc)['H1a']
        nd = naive(Mnull['HIGH'], Mnull['LOW'], 12, rng, icc)['D1']
        nh = naive(Mlow2, M['P1']['LOW'], 12, rng, icc)['H1a']
        print(f"   {icc:.1f}                      {d:.4f} | {hh:.4f}                 {nd:.4f} | {nh:.4f}", flush=True)

    print("\n4. variants at P1 and P4: legitimacy at probe time HIGH | LOW, mean psi-hat, D1_M at 12 twin sessions (one-update rule)")
    var = {}
    for cfg in CFG[1:5]:
        for k in ('P1', 'P4'):
            o = twins(cfg, k, **KW[cfg])
            mm = {a: measures(o[a], 0, rng) for a in ('HIGH', 'LOW')}
            s = conf(mm['HIGH'], mm['LOW'], 12, rng)
            var[cfg, k] = o
            gini = lambda x: (np.abs(x[:, :, None] - x[:, None, :]).mean((1, 2)) / (2 * np.maximum(x.mean(1), 1e-9))).mean()
            wl = o['LOW']['wins'][:, 0, :, 1:].sum(-1)
            print(f"   {cfg:6s} {k}   {o['HIGH']['L'][:, 0, :, -1].mean():.3f} | {o['LOW']['L'][:, 0, :, -1].mean():.3f}   psi {s['psi']:.3f}   "
                  f"H1a_M {s['H1a']:.3f}  D1_M {s['D1']:.3f}   inequality of fills within a LOW market (Gini) {gini(wl):.3f}", flush=True)
    wl = base['P1']['LOW']['wins'][:, 0, :, 1:].sum(-1)
    print(f"   (base P1: Gini {(np.abs(wl[:, :, None] - wl[:, None, :]).mean((1, 2)) / (2 * wl.mean(1))).mean():.3f})")

    print("\n5. market size at 72 traders per arm, intraclass correlation .1: D1_M (one-update rule)")
    for k in ('P1', 'P4'):
        row = []
        for cfg, N, S in (('N4', 4, 18), ('base', 6, 12), ('N8', 8, 9)):
            o = base[k] if cfg == 'base' else twins(cfg, k, **KW[cfg])
            mm = {a: measures(o[a], 0, rng) for a in ('HIGH', 'LOW')}
            s = conf(mm['HIGH'], mm['LOW'], S, rng, .1)
            row.append(f"{S} markets of {N}: {s['D1']:.3f} (legitimacy {o['HIGH']['L'][:, 0, :, -1].mean():.3f} | {o['LOW']['L'][:, 0, :, -1].mean():.3f})")
        print(f"   {k}   " + "     ".join(row), flush=True)

    print("\n6. procurement as a collective outcome: share of scripted units sold, LOW minus HIGH, and EFF at 12 twin sessions")
    for label, src, rounds in (('no reversal, rounds 2-6', base, slice(1, 6)), ('plentiful good switched at round 5, rounds 5-6', {k: var['rev5', k] for k in ('P1', 'P4')}, slice(4, 6))):
        for k in ('P1', 'P4'):
            o = src[k]
            ab = {a: o[a]['sold'][:, 0, rounds].sum(-1) / o[a]['units'][:, 0, rounds].sum(-1) for a in o}
            i = rng.integers(0, POOL, (B, 12))
            eff = paired_t((ab['LOW'] - ab['HIGH'])[i]).mean()
            stick = o['HIGH']['on0'][:, 0, 5] - o['LOW']['on0'][:, 0, 5]
            print(f"   {label}, {k}: sold HIGH {ab['HIGH'].mean():.4f}, LOW {ab['LOW'].mean():.4f}, difference {ab['LOW'].mean() - ab['HIGH'].mean():+.4f}, EFF {eff:.3f}; "
                  f"round 6, share of orders on the good that was plentiful at first: HIGH minus LOW {stick.mean():+.3f}, test {paired_t(stick[i]).mean():.3f}", flush=True)

    print("\n7. twelve records on one claim (HIGH arm): PLAT, mean delta, closure after records 3-5 and 10-12")
    print("   rule     point   gate world                              HIGH uniformly slowed, 10% inattentive      uniformly slowed, nobody inattentive")
    for rule in ('event', 'outcome'):
        for k in ('P0', 'P1', 'P4'):
            L = base[k]['HIGH']['L'][:, 0, :, -1]
            w = weights(L, 1.0, rule, rng)
            att = w > 0
            cells = []
            for ww in (w, np.where(att, w[att].mean(), 0.0), np.full(w.shape, w[att].mean())):
                p, d, e, l = plat(news(ww, rng), 12, rng)
                cells.append(f"{p:.3f}  delta {d:+.3f}  ({e:.3f}, {l:.3f})")
            print(f"   {rule:7s}  {k}      " + "      ".join(cells), flush=True)
    wl = weights(base['P1']['LOW']['L'][:, 0, :, -1], 1.0, 'event', rng)
    p, d, e, l = plat(news(wl, rng), 12, rng)
    print(f"   LOW arm, P1, one-update rule (10% inattentive): PLAT {p:.3f}  delta {d:+.3f}  ({e:.3f}, {l:.3f})")

    print("\n8. the claim market (market maker): price response (favourable minus unfavourable claim) HIGH | LOW, ratio, PRICE at 12 twin sessions")
    for k in PTS:
        pr = {a: price_response(base[k][a], M[k][a], rng) for a in ('HIGH', 'LOW')}
        i = rng.integers(0, POOL, (B, 12))
        ratio, hi = fieller_m(pr['HIGH'][i], pr['LOW'][i])
        h = base[k]['HIGH']
        c, Lh = h['cash'][:, 0], h['L'][:, 0, :, -1]
        r = np.corrcoef((c - c.mean(1, keepdims=True)).ravel(), (Lh - Lh.mean(1, keepdims=True)).ravel())[0, 1]
        print(f"   {k}   {pr['HIGH'].mean():.3f} | {pr['LOW'].mean():.3f}   ratio of means {pr['HIGH'].mean() / pr['LOW'].mean():.3f} "
              f"(psi-hat from forecasts {M[k]['HIGH']['T'].mean() / M[k]['LOW']['T'].mean():.3f})   PRICE {(hi < 1).mean():.3f}   "
              f"cash and legitimacy within HIGH markets r = {r:+.3f}", flush=True)
    for label, kw in (('two passes', dict(passes=2)), ('stake a tenth of the bankroll', dict(share=.1))):
        pr = {a: price_response(base['P1'][a], M['P1'][a], rng, **kw) for a in ('HIGH', 'LOW')}
        print(f"   P1, {label}: {pr['HIGH'].mean():.3f} | {pr['LOW'].mean():.3f}, ratio {pr['HIGH'].mean() / pr['LOW'].mean():.3f}")
    print(f"\n   X2 market clearing, whole run: {CHECKS['bad']} violations in {CHECKS['n']} checked clearings")
