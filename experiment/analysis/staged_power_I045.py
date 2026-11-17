"""KGi-DISS-I045: participants required by each step of a staged validation (freeze 00_freeze_I045.yaml).

Every figure is a power computed on simulated cohorts: the gate kernel as the truth, the assumed rating
and forecast noise, the assumed revision rules. Level one-sided .005 unless stated; the required n is the
smallest n of a fixed grid at which the estimated power reaches the target. Seed 141000.
    python experiment/analysis/staged_power_I045.py > records/staged_power_I045.txt
"""
import sys

import numpy as np
from scipy import stats as st

sys.path.insert(0, 'experiment/analysis')
import estimand_core_I038 as ec
import market_cert_I044 as mc
import market_generator as mg
import probe_generator as pg
import twins_I040 as tw
import yoked_analysis as ya

SEED = 141000
N, B, POOL = 20000, 2000, 3000
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
EDGE = ('P1', 'P2', 'P3', 'P4')                       # 'binding' = the largest requirement over these
GRID_P = (12, 18, 24, 30, 36, 48, 60, 72, 84, 96, 120, 144, 168, 192, 240, 288, 336, 384, 480, 576)
GRID_T = (3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32)
Z005, Z05 = st.norm.ppf(.995), st.norm.ppf(.95)
CFORM = (st.norm.ppf(.995) + st.norm.ppf(.90)) ** 2   # 14.88: two-sample constant at one-sided .005, power .90
ARMS = tw.ARMS
r5, sig = mc.r5, mc.sig


# ------------------------------------------------------------------ the individual design

def indiv(pt, n, rng, K=None, quota=None, phip=None, regime=None):
    """n yoked pairs of different people in design S1x. Without K and quota this is twins_I040.twins
    (same_person=False, indep_choice=True) draw for draw. K: settlements per round as the kernel counts
    them. quota: a basket of that many fills per round; a participant who holds it has no further outcome
    event until the next round."""
    K = tw.K if K is None else K
    regime = {'HIGH': 'HIGH', 'LOW': 'LOW'} if regime is None else regime
    nuf, nur, chi = mg.NUF * pt[1], mg.NUF * pt[1] * pt[2], pt[3]
    phip = mg.PHIP if phip is None else phip
    base_rho = np.where(np.arange(n) % 2 == 0, .002, .02)
    rho = {'HIGH': base_rho, 'LOW': rng.permutation(base_rho)}
    reg1 = rng.random(n) < 0.5
    R1, R2 = tw.R1, tw.R2
    S = {a: dict(Q=np.full((n, 2), 0.5), L=np.full(n, mg.L0), A=np.full(n, mg.A0), ring=np.zeros((n, 15)),
                 hits=np.zeros(n), arm=np.zeros(n, int), cnt=np.zeros(n, int), held=np.zeros(n)) for a in ARMS}
    rows, slot = np.arange(n), np.arange(15)[None, :]
    out = {key: {a: np.zeros((n, R1 + R2)) for a in ARMS} for key in ('L', 'A', 'wins', 'events', 'done')}
    for t in range((R1 + R2) * K):
        ph, r = (0 if t < R1 * K else 1), t // K
        if t % K == 0:
            for a in ARMS:
                s = S[a]
                s['arm'] = (rng.random(n) >= sig(mg.BETA * (s['Q'][:, 0] - s['Q'][:, 1]))).astype(int)
                s['held'] = np.zeros(n)
        uo, up = rng.random(n), rng.random(n)
        odds = tw.PH1 if ph == 0 else tw.PH2
        for a in ARMS:
            s = S[a]
            act = np.ones(n, bool) if quota is None else s['held'] < quota
            R = (uo < np.where(s['arm'] == 0, odds[0], odds[1])).astype(float)
            seen = np.minimum(s['cnt'], 15)
            trail = np.where(seen > 0, (s['ring'] * (slot < seen[:, None])).sum(1) / np.maximum(seen, 1), 0.5)
            high = reg1 if ph == 0 else np.full(n, regime[a] == 'HIGH')
            s['hits'] += up < np.where(high, tw.MU_REF, np.clip(trail, .05, .95))
            s['ring'][rows, s['cnt'] % 15] = np.where(act, R, s['ring'][rows, s['cnt'] % 15])
            s['cnt'] = s['cnt'] + act
            seen = np.minimum(s['cnt'], 15)
            trail_after = (s['ring'] * (slot < seen[:, None])).sum(1) / np.maximum(seen, 1)
            q = s['Q'][rows, s['arm']]
            s['Q'][rows, s['arm']] = np.where(act, q + mg.ALPHA * s['L'] * (R - q), q)
            D = mg.PHIM * np.maximum(s['A'] - R, 0) + phip * np.maximum(R - s['A'], 0)
            s['L'] = np.where(act, np.clip(s['L'] - nuf * np.maximum(D - mg.TAUF, 0) + nur * (D <= mg.TAUF), 0, 1), s['L'])
            ref = np.where(high, s['hits'] / (t + 1), trail_after)
            s['A'] = np.where(act, np.clip((1 - rho[a]) * s['A'] + rho[a] * ((1 - chi) * R + chi * ref), 0, 1), s['A'])
            s['held'] = s['held'] + act * R
            out['wins'][a][:, r] += act * R
            out['events'][a][:, r] += act
        if (t + 1) % K == 0:
            for a in ARMS:
                out['L'][a][:, r], out['A'][a][:, r] = S[a]['L'], S[a]['A']
                out['done'][a][:, r] = 1.0 if quota is None else S[a]['held'] >= quota
    out['K'] = K
    return out


def ratings(m, rng, noise=5.8, a=0.5):
    return r5(50 + a * (100 * m - 50) + rng.normal(0, noise, m.shape))


def revision(w, e, rng, sf=12.0):
    """post minus pre forecast on one market with evidence e (basket_cert_I043.market without the bet)"""
    b0 = np.clip(rng.normal(pg.PRIOR_MU, pg.PRIOR_SD, len(w)), 5, 95)
    return r5(b0 + w * (100 * e - b0) + rng.normal(0, sf, len(w))) - r5(b0 + rng.normal(0, sf, len(w)))


def probe(l, rule, rng, ks=0.35, c=1.0, sf=12.0, inatt=0.10):
    """T of design B: one pair on a record of ten closes and one pair on a source's forecast (weight
    ks * g). ks=None: two record pairs (design Y). Returns T and who is attentive."""
    g = 1 - c * (1 - l)
    off = rng.random(len(l)) < inatt
    w1 = np.where(off, 0.0, pg.weight(g, ec.M, rule))
    w2 = w1 if ks is None else np.where(off, 0.0, ks * g)
    pair = lambda w: revision(w, .9, rng, sf) - revision(w, .1, rng, sf)
    return 0.5 * (pair(w1) + pair(w2))


def cohort(b, rule, rng, c=1.0, **kw):
    """ratings by round and T for both arms of a pool of pairs"""
    C = {}
    for a in ARMS:
        C[a] = dict(F=ratings(b['L'][a], rng), E3=ratings(b['A'][a], rng), E1=ratings(b['A'][a], rng, noise=10.0),
                    T=probe(b['L'][a][:, -1], rule, rng, c=c, **kw), wins=b['wins'][a], done=b['done'][a][:, -1] > 0)
    C['K'] = b['K']
    return C


# ------------------------------------------------------------------ power on samples of n

def need(rates, grid, target=0.90):
    """smallest n of the grid at which the rate reaches the target (None: more than the grid)"""
    for n, p in zip(grid, rates):
        if p >= target:
            return n
    return None


def show(x, grid=GRID_P):
    return f"{x}" if x is not None else f">{grid[-1]}"


def curve(fn, grid=GRID_P, until=None):
    """fn(n) -> dict of rates; returns {key: tuple of rates over the grid}. With `until`, the scan stops
    once every key named there has reached .90, and the later entries are nan (never read by need())."""
    rows, reached = [], set()
    for n in grid:
        if until is not None and reached >= set(until):
            rows.append(None)
            continue
        rows.append(fn(n))
        reached |= {k for k, v in rows[-1].items() if v >= 0.90}
    return {k: tuple(float(r[k]) if r is not None else float('nan') for r in rows) for k in rows[0]}


def needs(cv, key, grid=GRID_P):
    return f"{show(need(cv[key], grid, .90), grid)} ({show(need(cv[key], grid, .80), grid)})"


def checks(C, n, rng, e='E1'):
    """the first wave's checks and the confirmatory pair on B samples of n pairs"""
    i = rng.integers(0, N, (B, n))
    H, L = C['HIGH'], C['LOW']
    zf = ya.signed_rank_z(L['F'][i, -1] - H['F'][i, -1])
    ze = ya.signed_rank_z(H[e][i, -1] - L[e][i, -1])
    d1 = ya.fieller(H['T'][i], L['T'][i])[2] < 1
    return dict(H1a=(zf > Z005).mean(), H1a_05=(zf > Z05).mean(), K3=(ze > Z005).mean(), K3_05=(ze > Z05).mean(),
                D1=d1.mean(), PAIR=((zf > Z005) & d1).mean())


def phi_flag(C, n, rng):
    """rate of the PHI flag (inside LOW, the fairness rating falls after rounds with more wins)"""
    i = rng.integers(0, N, (B, n))
    fr = C['LOW']['F'][i][:, :, 2:6]
    zphi, _ = ya.phi_z(fr[:, :, 1:] - fr[:, :, :-1], C['LOW']['wins'][i][:, :, 3:6] / C['K'])
    return dict(PHI=(zphi < -Z005).mean())


def rivals(C, n, rng):
    """the supporting statistics that bear on a uniform slowdown"""
    i = rng.integers(0, N, (B, n))
    H, L = C['HIGH'], C['LOW']
    fh = H['F'][i, -1] + rng.uniform(-.01, .01, (B, n))
    return dict(ASSOC_H=(ya.arm_z(H['T'][i], fh) > Z005).mean(), TOPQ=(ya.topq_p(H['T'][i], fh) < .005).mean(),
                FREEZE=(ya.freeze_upper(H['T'][i], fh, L['T'][i]) < 0.5).mean())


def fieller_masked(th, mh, tl, ml):
    """upper Fieller limit of mean(th | mh) / mean(tl | ml) per replicate (masks select who is measured)"""
    nh, nl = mh.sum(1), ml.sum(1)
    a_, b_ = (th * mh).sum(1) / np.maximum(nh, 1), (tl * ml).sum(1) / np.maximum(nl, 1)
    va = (((th - a_[:, None]) ** 2) * mh).sum(1) / np.maximum(nh - 1, 1) / np.maximum(nh, 1)
    vb = (((tl - b_[:, None]) ** 2) * ml).sum(1) / np.maximum(nl - 1, 1) / np.maximum(nl, 1)
    t2 = st.t.ppf(1 - .005, np.maximum(nh + nl - 2, 1)) ** 2
    den = b_ ** 2 - t2 * vb
    disc = np.maximum(a_ ** 2 * b_ ** 2 - den * (a_ ** 2 - t2 * va), 0)
    ok = (den > 0) & (nh > 2) & (nl > 2)
    return np.where(ok, (a_ * b_ + np.sqrt(disc)) / np.where(ok, den, 1), np.inf)


# ------------------------------------------------------------------ the live economy

def run_w(pt, S, Nm, seeds, neighbour_rich, quota=None, rich_pi=mc.RICH, script2=None):
    """market_cert_I044.run for unit orders (bit for bit without a quota), with a basket of `quota` units
    per round that ends a trader's bidding. A market with nobody left to serve keeps its last figure."""
    gs, gp, go = (np.random.default_rng(s) for s in seeds)
    g2 = go if script2 is None else np.random.default_rng(script2)
    nuf, nur, chi = mg.NUF * pt[1], mg.NUF * pt[1] * pt[2], pt[3]
    sh = (S, 2, Nm)
    rho = np.stack([np.where(gp.random((S, Nm)) < .5, .002, .02), np.where(go.random((S, Nm)) < .5, .002, .02)], 1)
    Q, L, A = np.full(sh + (2,), .5), np.full(sh, mg.L0), np.full(sh, mg.A0)
    ring, shown = np.zeros((S, 2, 15)), np.zeros((S, 2))
    Lr, wins, events = np.empty(sh + (mc.ROUNDS,)), np.zeros(sh + (mc.ROUNDS,)), np.zeros(sh + (mc.ROUNDS,))
    for t in range(mc.K * mc.ROUNDS):
        r = t // mc.K
        if t % mc.K == 0:
            uc = np.stack([gp.random((S, Nm)), go.random((S, Nm))], 1)
            arm = (uc >= sig(mg.BETA * (Q[..., 0] - Q[..., 1]))).astype(int)
            rich = (True, True) if r == 0 else (False, neighbour_rich)
            pis = np.array([rich_pi if x else mc.SCARCE for x in rich])
            held = np.zeros(sh)
        k = np.stack([gs.binomial(Nm, pis[0], (S, 2)), g2.binomial(Nm, pis[1], (S, 2))], 1)
        v = np.stack([gs.random((S, Nm)), g2.random((S, Nm))], 1)
        act = np.ones(sh, bool) if quota is None else held < quota
        R = np.zeros(sh)
        for g in (0, 1):
            m = (arm == g) & act
            win, _ = mc.auction(np.where(m, v, -1.0), m, k[..., g])
            R = np.where(win, 1.0, R)
        held += R
        nact = act.sum(-1)
        ring[..., t % 15] = R.mean(-1) if quota is None else np.where(nact > 0, R.sum(-1) / np.maximum(nact, 1), shown)
        shown = ring[..., :min(t + 1, 15)].mean(-1)
        Qc = Q.copy()
        L2, A2 = mc.kstep(Q, L, A, arm, R, shown[:, ::-1, None], rho, nuf, nur, chi)
        Q, L, A = np.where(act[..., None], Q, Qc), np.where(act, L2, L), np.where(act, A2, A)
        wins[..., r] += R
        events[..., r] += act
        if (t + 1) % mc.K == 0:
            Lr[..., r] = L
    return dict(L=Lr, wins=wins, events=events)


def triplet_pools(k, Nm, rp, tag, quota=None, inst='unit', with_null=True):
    """two HIGH pools (scripts A, B), the LOW pool whose two markets run A and B, and (with_null) two
    LOW-regime pools on A and B for the size of the fairness test"""
    p = PTS.index(k)
    sd = lambda *x: [SEED, tag, p, *x]
    if inst == 'unit':
        go = lambda seeds, rich, **kw: run_w(PT[k], POOL, Nm, seeds, rich, quota=quota, rich_pi=rp, **kw)
    else:
        go = lambda seeds, rich, **kw: mc.run(PT[k], POOL, Nm, seeds, rich, inst='div', rich_pi=rp, **kw)
    P = dict(HA=go((sd(0), sd(1), sd(2)), True), HB=go((sd(10), sd(11), sd(12)), True),
             LAB=go((sd(0), sd(3), sd(4)), False, script2=sd(10)))
    if with_null:
        P.update(LA=go((sd(0), sd(5), sd(6)), False), LB=go((sd(10), sd(15), sd(16)), False))
    return P


def triplet_measures(P, rng, rule='event', c=1.0):
    M = dict(HA=mc.measures(P['HA'], 0, rng, c, rule), HB=mc.measures(P['HB'], 0, rng, c, rule),
             L0=mc.measures(P['LAB'], 0, rng, c, rule), L1=mc.measures(P['LAB'], 1, rng, c, rule))
    if 'LA' in P:
        M.update(LA=mc.measures(P['LA'], 0, rng, c, rule), LB=mc.measures(P['LB'], 0, rng, c, rule))
    return M


def triplet_values(HA, HB, L0, L1, rng, icc):
    """per LOW session: mean fairness and mean T of its two markets and of their two HIGH twins"""
    fa, fb = mc.shift(HA['F'], icc, rng).mean(1), mc.shift(HB['F'], icc, rng).mean(1)
    ta, tb = mc.shift(HA['T'], icc, rng).mean(1), mc.shift(HB['T'], icc, rng).mean(1)
    f0, f1 = (x.mean(1) for x in mc.shift_pair(L0['F'], L1['F'], icc, rng))
    t0, t1 = (x.mean(1) for x in mc.shift_pair(L0['T'], L1['T'], icc, rng))
    return dict(fh=.5 * (fa + fb), fl=.5 * (f0 + f1), th=.5 * (ta + tb), tl=.5 * (t0 + t1))


def triplet_test(V, n, rng):
    i = rng.integers(0, len(V['fh']), (B, n))
    h = mc.paired_t((V['fl'] - V['fh'])[i])
    d = mc.fieller_m(V['th'][i], V['tl'][i])[1] < 1
    return dict(H1a=h.mean(), D1=d.mean(), PAIR=(h & d).mean())


def welch_greater(x, y):
    """one-sided Welch test that mean(x) > mean(y), per replicate, at .005"""
    vx, vy = x.var(1, ddof=1) / x.shape[1], y.var(1, ddof=1) / y.shape[1]
    df = (vx + vy) ** 2 / (vx ** 2 / (x.shape[1] - 1) + vy ** 2 / (y.shape[1] - 1))
    return (x.mean(1) - y.mean(1)) / np.sqrt(vx + vy) > st.t.ppf(.995, df)


# ------------------------------------------------------------------ the run

if __name__ == '__main__':
    if '--fast' in sys.argv:                                                           # development only; never a record
        N, B, POOL = 3000, 200, 300
        mc.B = B
    np.seterr(divide='ignore', invalid='ignore')
    rng = np.random.default_rng(SEED)
    gen = lambda *tag: np.random.default_rng([SEED, 7, *tag])
    rn = lambda r: 'one-update' if r == 'event' else 'count'
    at = lambda fn, key, ns: " / ".join(f"{fn(n)[key]:.4f}" for n in ns)
    print("KGi-DISS-I045: participants required by each step of a staged validation (seed 141000)")
    print(f"simulated cohorts: {N:,} pairs per cell (individual design), {POOL:,} sessions per arm and cell (live economy); {B:,} samples per n")
    print("one-sided .005 unless stated; 'need' = smallest n of the grid with power .90, in brackets .80; a pair is 2 people, a triplet 36 (six per market) or 24 (four)\n")

    # ---------------------------------------------------------------- pools of the individual design
    lat = {k: indiv(PT[k], N, gen(1, i)) for i, k in enumerate(PTS)}
    print("0. gates")
    for k in ('P1', 'P4'):
        ref = tw.twins(PT[k], 2000, np.random.default_rng([SEED, 0]), same_person=False, indep_choice=True)
        new = indiv(PT[k], 2000, np.random.default_rng([SEED, 0]))
        same = all(np.array_equal(ref[x][a], new[x][a]) for x in ('L', 'A', 'wins') for a in ARMS)
        print(f"   G1 {k}: the new individual runner equals twins_I040.twins on the same seed: {same}; legitimacy at probe time in the pools: HIGH "
              f"{lat[k]['L']['HIGH'][:, -1].mean():.3f} (share below .05: {(lat[k]['L']['HIGH'][:, -1] < .05).mean():.3f}), LOW {lat[k]['L']['LOW'][:, -1].mean():.3f}")
    sd = [[SEED, 9, j] for j in range(4)]
    a_, b_ = mc.run(PT['P1'], 200, 6, sd[:3], True, script2=sd[3]), run_w(PT['P1'], 200, 6, sd[:3], True, script2=sd[3])
    c_, d_ = mc.run(PT['P4'], 200, 4, sd[:3], False, rich_pi=(.6, .25)), run_w(PT['P4'], 200, 4, sd[:3], False, rich_pi=(.6, .25))
    g2 = np.array_equal(a_['L'], b_['L']) and np.array_equal(a_['wins'], b_['wins']) and np.array_equal(c_['L'], d_['L'])
    print(f"   G2 the new live runner equals market_cert_I044.run bit for bit (two settings): {g2}")

    # ---------------------------------------------------------------- 1. the first wave: assumptions
    print("\n1. first wave on the built individual app: pairs needed (level .005; in square brackets level .05)")
    print("   point   H1a fairness              K3 entitlement, one item (as built)   K3, three items (as certified)   mean ratings: fairness HIGH | LOW, entitlement HIGH | LOW")
    C = {(k, r): cohort(lat[k], r, rng) for k in PTS for r in ('event', 'outcome')}
    W1 = {}
    for k in PTS:
        cv = curve(lambda n: checks(C[k, 'event'], n, rng), until=('H1a', 'H1a_05', 'K3', 'K3_05'))
        cv3 = curve(lambda n: checks(C[k, 'event'], n, rng, e='E3'), until=('K3', 'K3_05'))
        W1[k] = (cv, cv3)
        H, L = C[k, 'event']['HIGH'], C[k, 'event']['LOW']
        print(f"   {k}      {needs(cv, 'H1a'):12s} [{needs(cv, 'H1a_05'):9s}]     {needs(cv, 'K3'):12s} [{needs(cv, 'K3_05'):9s}]"
              f"             {needs(cv3, 'K3'):12s} [{needs(cv3, 'K3_05'):9s}]          {H['F'][:, -1].mean():.1f} | {L['F'][:, -1].mean():.1f},  "
              f"{H['E1'][:, -1].mean():.1f} | {L['E1'][:, -1].mean():.1f}", flush=True)
    for k in ('P1', 'P4'):
        print(f"   {k}, power at 24 / 36 / 72 pairs, level .005: fairness {at(lambda n: checks(C[k, 'event'], n, rng), 'H1a', (24, 36, 72))}; "
              f"entitlement, one item {at(lambda n: checks(C[k, 'event'], n, rng), 'K3', (24, 36, 72))}; "
              f"three items {at(lambda n: checks(C[k, 'event'], n, rng, e='E3'), 'K3', (24, 36, 72))}", flush=True)
    print("   PHI flag (a win erodes fairness): rate of the flag inside LOW, by pairs")
    print(f"      frozen phi_plus .25 (false alarm), P1, at 36 / 72 / 144 / 288 / 576: {at(lambda n: phi_flag(C['P1', 'event'], n, rng), 'PHI', (36, 72, 144, 288, 576))}", flush=True)
    for j, pp_ in enumerate((0.5, 1.0)):
        bp = indiv(PT['P1'], N, gen(2, j), phip=pp_)
        Cp = cohort(bp, 'event', rng)
        cv = curve(lambda n: phi_flag(Cp, n, rng), until=('PHI',))
        print(f"      phi_plus {pp_}: need {needs(cv, 'PHI')} pairs; rate at 72 / 144 / 288: {at(lambda n: phi_flag(Cp, n, rng), 'PHI', (72, 144, 288))}; "
              f"legitimacy at probe time HIGH {bp['L']['HIGH'][:, -1].mean():.3f} | LOW {bp['L']['LOW'][:, -1].mean():.3f}", flush=True)

    # ---------------------------------------------------------------- 2. what the wave tells about people
    print("\n2. first wave: what it tells about people")
    latK = {(K, k): indiv(PT[k], N, gen(3, K, i), K=K) for K in (80, 40) for i, k in enumerate(EDGE)}
    pool_of = lambda K, k: lat[k] if K == 120 else latK[K, k]
    print("   (a) settlements per round as the kernel counts them: legitimacy at probe time HIGH | LOW")
    for k in EDGE:
        print(f"      {k}:   " + "   ".join(f"{K}: {pool_of(K, k)['L']['HIGH'][:, -1].mean():.3f} | {pool_of(K, k)['L']['LOW'][:, -1].mean():.3f}" for K in (120, 80, 40)))
    print("       a cell at 40 and a cell at 120 settlements per round, between participants: participants needed per cell and arm")
    G2P = tuple(n for n in GRID_P if n <= 288)
    mw = lambda x, y: st.mannwhitneyu(x, y, alternative='greater', axis=1, method='asymptotic').pvalue < .005
    for k in ('P1', 'P4'):
        f120 = {a: ratings(lat[k]['L'][a][:, -1], rng) for a in ARMS}
        f40 = {a: ratings(latK[40, k]['L'][a][:, -1], rng) for a in ARMS}

        def cell(n):
            i, j = rng.integers(0, N, (B, n)), rng.integers(0, N, (B, n))
            return dict(low=mw(f120['LOW'][i], f40['LOW'][j]).mean(), high=mw(f40['HIGH'][j], f120['HIGH'][i]).mean(),
                        contrast=mw(f120['LOW'][i] - f120['HIGH'][i], f40['LOW'][j] - f40['HIGH'][j]).mean())

        def null(n):
            i, j = rng.integers(0, N, (B, n)), rng.integers(0, N, (B, n))
            return dict(null=mw(f120['LOW'][i], f120['LOW'][j]).mean())
        cv = curve(cell, G2P, until=('low', 'high', 'contrast'))
        print(f"      {k}: control arm rated fairer at 120: need {needs(cv, 'low', G2P)}; HIGH arm rated less fair at 120: {needs(cv, 'high', G2P)}; "
              f"the HIGH-LOW contrast larger at 120: {needs(cv, 'contrast', G2P)}; size (both cells at 120) at 12 / 72 / 288: {at(null, 'null', (12, 72, 288))}; "
              f"mean ratings LOW 120 | 40: {f120['LOW'].mean():.1f} | {f40['LOW'].mean():.1f}, HIGH {f120['HIGH'].mean():.1f} | {f40['HIGH'].mean():.1f}", flush=True)

    print("   (b) the revision rule: weight at a record of 10 closes against a record of 4, within participant (control arm, P1)")
    lL = lat['P1']['L']['LOW'][:, -1]
    for world in ('outcome', 'event'):
        off = rng.random(N) < 0.10
        w10 = np.where(off, 0.0, pg.weight(lL, 10, world))
        w4 = np.where(off, 0.0, pg.weight(lL, 4, world))
        stat = (revision(w10, .9, rng) - revision(w10, .1, rng)) / 80 - (revision(w4, .75, rng) - revision(w4, .25, rng)) / 50
        cell = lambda n: dict(rule=(ya.signed_rank_z(stat[rng.integers(0, N, (B, n))]) > Z005).mean())
        cv = curve(cell, G2P, until=('rule',))
        lab = 'count rule (the weight rises with the record)' if world == 'outcome' else 'one-update rule (it does not): rejection'
        print(f"      {lab}: mean weights {w10.mean():.3f} | {w4.mean():.3f}; need {needs(cv, 'rule', G2P)} participants; "
              f"rate at 36 / 72 / 144 / 288: {at(cell, 'rule', (36, 72, 144, 288))}", flush=True)

    print("   (c) precision from a wave of n pairs (P1): control arm's mean weight W0 = mean T / 80; main-study pairs computed from the wave")
    print("       (formula 14.88 (s_H^2 + s_L^2) / (m_L (1 - psi*))^2 with psi* the model's value at the anchoring edge)")
    for r in ('event', 'outcome'):
        psi_star = C['P4', r]['HIGH']['T'].mean() / C['P4', r]['LOW']['T'].mean()
        th, tl = C['P1', r]['HIGH']['T'], C['P1', r]['LOW']['T']
        row = []
        for n in (24, 36, 48, 72, 96):
            i = rng.integers(0, N, (B, n))
            mL, sL, sH = tl[i].mean(1), tl[i].std(1, ddof=1), th[i].std(1, ddof=1)
            nf = CFORM * (sH ** 2 + sL ** 2) / (mL * (1 - psi_star)) ** 2
            row.append(f"{n}: W0 {mL.mean() / 80:.3f} se {mL.std() / 80:.3f}; sd of T {sL.mean():.1f}, rel. se {sL.std() / sL.mean():.2f}; pairs {np.median(nf):.0f} "
                       f"(80% of waves {np.quantile(nf, .1):.0f}-{np.quantile(nf, .9):.0f}; rel. sd {nf.std() / nf.mean():.2f})")
        print(f"      {rn(r):10s} rule (psi* {psi_star:.3f}):  " + "   ".join(row), flush=True)

    print("   (d) addendum AD-S1: reading the count of outcomes per round from the ratings of one cell (120 settlements shown)")
    FK = {(K, k): {a: ratings(pool_of(K, k)['L'][a], rng) for a in ARMS} for K in (120, 80, 40) for k in EDGE}
    G3P = tuple(n for n in GRID_P if n <= 144)
    for k in EDGE:
        row = []
        for K in (120, 80, 40):
            d = FK[K, k]['LOW'][:, 5] - FK[K, k]['LOW'][:, 2]
            cell = lambda n: dict(rec=(ya.signed_rank_z(d[rng.integers(0, N, (B, n))]) > Z005).mean())
            cv = curve(cell, G3P, until=('rec',))
            row.append(f"{K}: need {needs(cv, 'rec', G3P)}, rate at 24 / 72: {at(cell, 'rec', (24, 72))} (mean change {d.mean():+.1f})")
        print(f"      {k} recovery test (control arm, last rating above the rating after round 3), by the true count:   " + "   ".join(row), flush=True)
    traj = {(K, k): np.concatenate([pool_of(K, k)['L'][a].mean(0) for a in ARMS]) for K in (120, 80, 40) for k in EDGE}

    def classify(y, cands):
        yc = y - y.mean(1, keepdims=True)
        best, arg = np.full(len(y), np.inf), np.zeros(len(y), int)
        for j, key in enumerate(cands):
            xc = traj[key] - traj[key].mean()
            slope = np.maximum(yc @ xc / (xc @ xc), 0)
            rss = (yc ** 2).sum(1) - slope ** 2 * (xc @ xc)
            arg, best = np.where(rss < best, j, arg), np.minimum(rss, best)
        return np.array([c[0] for c in cands])[arg]
    for k in ('P1', 'P4'):
        for K in (120, 80, 40):
            row = []
            for n in (12, 24, 36, 72, 144):
                i = rng.integers(0, N, (B, n))
                y = np.concatenate([FK[K, k][a][i].mean(1) for a in ARMS], 1)
                known = (classify(y, [(q, k) for q in (120, 80, 40)]) == K).mean()
                unknown = (classify(y, [(q, kk) for q in (120, 80, 40) for kk in EDGE]) == K).mean()
                row.append(f"{n}: {known:.3f} | {unknown:.3f}")
            print(f"      {k} classifier, true count {K:3d}: correct with the gate point known | unknown, by pairs   " + "   ".join(row), flush=True)

    # ---------------------------------------------------------------- 3. the gate test
    print("\n3. the gate on the individual design: pairs needed for the confirmatory pair (H1a then D1) | for D1 alone | psi (pool)")
    print("   design B as built: one record pair and one source pair (weight .35), forecast noise 12, 120 settlements per round")
    G = {}
    for r in ('event', 'outcome'):
        row = []
        for k in PTS:
            cv = curve(lambda n: checks(C[k, r], n, rng), until=('PAIR', 'D1'))
            G[k, r] = cv
            row.append(f"{k}: {needs(cv, 'PAIR')} | {needs(cv, 'D1')} | {C[k, r]['HIGH']['T'].mean() / C[k, r]['LOW']['T'].mean():.3f}")
        print(f"   {rn(r):10s} rule   " + "     ".join(row), flush=True)
    print("   G6 closed form against the simulation (D1, power .90): " + "   ".join(
        f"{k} {rn(r)}: formula "
        f"{CFORM * (C[k, r]['HIGH']['T'].var() + C[k, r]['LOW']['T'].var()) / (C[k, r]['LOW']['T'].mean() - C[k, r]['HIGH']['T'].mean()) ** 2:.0f}"
        f", simulated {show(need(G[k, r]['D1'], GRID_P))}" for k in ('P1', 'P4') for r in ('event', 'outcome')))
    print("   sizes at nominal .005 [.05]: null pairs (both members on the LOW board) | the world where ratings move and the gain does not")
    nul = indiv(PT['P1'], N, gen(4), regime={'HIGH': 'LOW', 'LOW': 'LOW'})
    Cn, C0 = cohort(nul, 'event', rng), cohort(lat['P1'], 'event', rng, c=0.0)
    for n in (12, 72, 288):
        s_, s0 = checks(Cn, n, rng), checks(C0, n, rng)
        print(f"      {n:3d} pairs: H1a {s_['H1a']:.4f} [{s_['H1a_05']:.3f}]  K3 {s_['K3']:.4f} [{s_['K3_05']:.3f}]  D1 {s_['D1']:.4f}"
              f"   |   gain does not move: D1 {s0['D1']:.4f}, pair {s0['PAIR']:.4f}", flush=True)

    print("   one change at a time, one-update rule: pairs for the confirmatory pair at P1 | P4 | binding point over P1-P4")
    var = [('as built (a second draw)', {}, None), ('weight on a source .2', dict(ks=.2), None), ('weight on a source .5', dict(ks=.5), None),
           ('two record pairs (design Y)', dict(ks=None), None), ('forecast noise 8', dict(sf=8.0), None), ('forecast noise 16', dict(sf=16.0), None),
           ('20% inattentive', dict(inatt=.20), None), ('a round counts for 80 settlements', {}, 80), ('a round counts for 40 settlements', {}, 40)]
    worst_of = lambda res: max(EDGE, key=lambda k: (res[k][0] is None, res[k][0] or 0, res[k][1] is None, res[k][1] or 0))
    SENS = {}
    for rule, rows in (('event', var), ('outcome', [('count rule, as built (a second draw)', {}, None), ('count rule, a round counts for 80', {}, 80),
                                                    ('count rule, a round counts for 40', {}, 40)])):
        for lab, kw, K in rows:
            res = {}
            for k in EDGE:
                Cv = cohort(pool_of(K or 120, k), rule, rng, **kw)
                cv = curve(lambda n: checks(Cv, n, rng), until=('PAIR',))
                res[k] = (need(cv['PAIR'], GRID_P, .90), need(cv['PAIR'], GRID_P, .80), Cv['HIGH']['T'].mean() / Cv['LOW']['T'].mean())
            SENS[lab] = res
            w_ = worst_of(res)
            print(f"      {lab:38s} {show(res['P1'][0])} ({show(res['P1'][1])}) | {show(res['P4'][0])} ({show(res['P4'][1])}) | "
                  f"{w_}: {show(res[w_][0])} ({show(res[w_][1])})   psi P1 {res['P1'][2]:.3f}, P4 {res['P4'][2]:.3f}", flush=True)

    # ---------------------------------------------------------------- 4. the rivals
    print("\n4. separating the gate from a uniform slowdown: pairs needed (individual design)")
    print("   point  rule        probes             HIGH-arm association   top quarter against the rest   freeze at .5")
    RIV, PL = {}, {}
    for r in ('event', 'outcome'):
        for lab, kw in (('two record pairs', dict(ks=None)), ('record + source', {})):
            for k in ('P1', 'P2', 'P3'):
                Cv = cohort(lat[k], r, rng, **kw)
                cv = curve(lambda n: rivals(Cv, n, rng), until=('ASSOC_H', 'TOPQ', 'FREEZE'))
                RIV[k, r, lab] = cv
                print(f"   {k}     {rn(r):10s}  {lab:17s}  {needs(cv, 'ASSOC_H'):20s}   {needs(cv, 'TOPQ'):20s}           {needs(cv, 'FREEZE')}", flush=True)
    hs = dict(lat['P1'])
    hs['L'] = {'HIGH': np.repeat(np.full((N, 1), lat['P1']['L']['HIGH'][:, -1].mean()), 6, 1), 'LOW': lat['P1']['L']['LOW']}
    Ch = cohort(hs, 'event', rng, ks=None)
    Ch['HIGH']['F'] = C['P1', 'event']['HIGH']['F']                                    # ratings as in the gate world
    half = cohort(lat['P1'], 'event', rng, c=0.5, ks=None)
    print("   sizes, P1, two record pairs, at 72 / 288 pairs: uniform slowdown of HIGH (every HIGH participant at the mean gain): association "
          f"{at(lambda n: rivals(Ch, n, rng), 'ASSOC_H', (72, 288))}, top quarter {at(lambda n: rivals(Ch, n, rng), 'TOPQ', (72, 288))}"
          f"   |   freeze at .5 when the coupling is .5: {at(lambda n: rivals(half, n, rng), 'FREEZE', (72, 288))}", flush=True)
    print("   twelve successive records on a claim, each participant a unit (PLAT2): participants needed per arm")
    G4P = tuple(n for n in GRID_P if n <= 384)
    for r in ('event', 'outcome'):
        for k in ('P1', 'P2', 'P3'):
            w, off = mc.weights(lat[k]['L']['HIGH'][:, -1], 1.0, r, rng)
            wl, _ = mc.weights(lat[k]['L']['LOW'][:, -1], 1.0, r, rng)
            cl = mc.news(wl, rng)[:, None, :]
            cg, cu = mc.news(w, rng)[:, None, :], mc.news(np.where(off, 0.0, w[~off].mean()), rng)[:, None, :]
            cv = curve(lambda n: dict(plat=mc.plat2(cg, cl, n, rng)[0]), G4P, until=('plat',))
            PL[k, r] = cv['plat']
            print(f"      {k} {rn(r):10s}: need {needs(cv, 'plat', G4P)}; power at 72 / 144: {at(lambda n: dict(p=mc.plat2(cg, cl, n, rng)[0]), 'p', (72, 144))}; "
                  f"uniformly slowed HIGH arm rejected at 36 / 72 / 144 / 288: {at(lambda n: dict(p=mc.plat2(cu, cl, n, rng)[0]), 'p', (36, 72, 144, 288))}", flush=True)

    # ---------------------------------------------------------------- 5a. a completion gate in the individual design
    print("\n5a. individual design with a basket of q fills per round that ends the bidding (30 fills are expected on the better ticket)")
    print("    the prediction market is open to those who completed the last round's basket; pairs RECRUITED")
    print("    point  basket   completed the last basket HIGH | LOW   events per deprivation round   legitimacy HIGH | LOW   psi all | completers   need D1: everyone measured | completers only | need H1a")
    for k in ('P1', 'P4'):
        for j, q in enumerate((None, 20, 15, 10)):
            b = lat[k] if q is None else indiv(PT[k], N, gen(5, j, PTS.index(k)), quota=q)
            Cq = cohort(b, 'event', rng)
            H, L = Cq['HIGH'], Cq['LOW']

            def cell(n):
                i = rng.integers(0, N, (B, n))
                gated = fieller_masked(H['T'][i], H['done'][i], L['T'][i], L['done'][i]) < 1
                zf = ya.signed_rank_z(L['F'][i, -1] - H['F'][i, -1])
                return dict(all=(ya.fieller(H['T'][i], L['T'][i])[2] < 1).mean(), gated=gated.mean(), H1a=(zf > Z005).mean())
            cv = curve(cell, until=('all', 'gated', 'H1a'))
            print(f"    {k}     {str(q):>4}     {H['done'].mean():.3f} | {L['done'].mean():.3f}                       "
                  f"{b['events']['HIGH'][:, 1:].mean():5.1f}                      {b['L']['HIGH'][:, -1].mean():.3f} | {b['L']['LOW'][:, -1].mean():.3f}"
                  f"          {H['T'].mean() / L['T'].mean():.3f} | {H['T'][H['done']].mean() / L['T'][L['done']].mean():.3f}        "
                  f"{needs(cv, 'all')} | {needs(cv, 'gated')} | {needs(cv, 'H1a')}", flush=True)

    # ---------------------------------------------------------------- 5b-d. the live economy by triplets
    print("\n5b. live economy (design W) by triplets, calibrated supply: triplets needed for the confirmatory pair [people]")
    print("    a triplet = one LOW session and its two HIGH twins; session effect = intraclass correlation of a shift shared within a session")
    LIVE = {}
    for Nm, fac, tag in ((6, 1.10, 61), (4, 1.15, 41)):
        rp = tuple(fac * x for x in mc.RICH)
        ppl = lambda x: f"{x * 6 * Nm}" if x is not None else f">{GRID_T[-1] * 6 * Nm}"
        for k in ('P1', 'P4'):
            P = triplet_pools(k, Nm, rp, tag)
            for r in ('event', 'outcome'):
                Mm = triplet_measures(P, rng, r)
                cells = []
                for icc in (0.0, 0.1, 0.2):
                    cv = curve(lambda n: triplet_test(triplet_values(Mm['HA'], Mm['HB'], Mm['L0'], Mm['L1'], rng, icc), n, rng), GRID_T)
                    LIVE[Nm, k, r, icc] = cv
                    n90, n80 = need(cv['PAIR'], GRID_T, .90), need(cv['PAIR'], GRID_T, .80)
                    cells.append(f"{icc:.1f}: {show(n90, GRID_T)} ({show(n80, GRID_T)}) [{ppl(n90)} ({ppl(n80)})]")
                psi = .5 * (Mm['HA']['T'].mean() + Mm['HB']['T'].mean()) / (.5 * (Mm['L0']['T'].mean() + Mm['L1']['T'].mean()))
                print(f"    {Nm} per market, {k}, {rn(r):10s} rule (psi {psi:.3f}; legitimacy HIGH {Mm['HA']['L'].mean():.3f} | LOW "
                      f"{Mm['L0']['L'].mean():.3f}):   session effect " + "   ".join(cells), flush=True)
                if r == 'event':
                    print(f"       power of the pair at 6 / 8 / 12 triplets, session effect 0 | .1 | .2:   " + "   |   ".join(
                        " / ".join(f"{LIVE[Nm, k, r, icc]['PAIR'][GRID_T.index(n)]:.3f}" for n in (6, 8, 12)) for icc in (0.0, 0.1, 0.2)), flush=True)
            if k == 'P1':                                                              # sizes
                Mn, M0 = triplet_measures(P, rng, 'event'), triplet_measures(P, rng, 'event', c=0.0)
                row = []
                for icc in (0.0, 0.1):
                    for n in (3, 6, 12):
                        h = triplet_test(triplet_values(Mn['LA'], Mn['LB'], Mn['L0'], Mn['L1'], rng, icc), n, rng)['H1a']
                        d = triplet_test(triplet_values(M0['HA'], M0['HB'], M0['L0'], M0['L1'], rng, icc), n, rng)['D1']
                        row.append(f"{icc:.1f}/{n}: {h:.4f} | {d:.4f}")
                print(f"    {Nm} per market, sizes at P1 (session effect / triplets: H1a | D1):   " + "   ".join(row), flush=True)
            if Nm == 6:
                LIVE['pools', k] = (P, rp)

    print("\n5c. live economy with a basket of q units per round that ends a trader's bidding (six per market): triplets needed [people]")
    ppl = lambda x: f"{x * 36}" if x is not None else f">{GRID_T[-1] * 36}"
    for k in ('P1', 'P4'):
        for q in (15, 10):
            P = triplet_pools(k, 6, LIVE['pools', k][1], 70 + q, quota=q, with_null=False)
            done = (P['HA']['wins'][:, 0, :, 1:] >= q).mean()
            for r in ('event', 'outcome'):
                Mm = triplet_measures(P, rng, r)
                cells = []
                for icc in (0.0, 0.1):
                    cv = curve(lambda n: triplet_test(triplet_values(Mm['HA'], Mm['HB'], Mm['L0'], Mm['L1'], rng, icc), n, rng), GRID_T)
                    n90, n80 = need(cv['PAIR'], GRID_T, .90), need(cv['PAIR'], GRID_T, .80)
                    cells.append(f"{icc:.1f}: {show(n90, GRID_T)} ({show(n80, GRID_T)}) [{ppl(n90)} ({ppl(n80)})], at 32 triplets {cv['PAIR'][-1]:.3f}")
                psi = .5 * (Mm['HA']['T'].mean() + Mm['HB']['T'].mean()) / (.5 * (Mm['L0']['T'].mean() + Mm['L1']['T'].mean()))
                print(f"    {k}, basket {q}, {rn(r):10s} rule (psi {psi:.3f}; legitimacy HIGH {Mm['HA']['L'].mean():.3f} | LOW {Mm['L0']['L'].mean():.3f}; "
                      f"baskets completed in scarce rounds, HIGH {done:.3f}):   session effect " + "   ".join(cells), flush=True)

    print("\n5d. institution contrast: unit orders against shares, each in its own triplets (six per market): triplets needed per institution")
    for k in ('P1', 'P4'):
        Pu, Ps = LIVE['pools', k][0], triplet_pools(k, 6, LIVE['pools', k][1], 90, inst='div', with_null=False)
        Pu2 = triplet_pools(k, 6, LIVE['pools', k][1], 91, with_null=False) if k == 'P1' else None
        for r in ('event', 'outcome'):
            Mu, Ms = triplet_measures(Pu, rng, r), triplet_measures(Ps, rng, r)
            cells = []
            for icc in (0.0, 0.1):
                Vu = triplet_values(Mu['HA'], Mu['HB'], Mu['L0'], Mu['L1'], rng, icc)
                Vs = triplet_values(Ms['HA'], Ms['HB'], Ms['L0'], Ms['L1'], rng, icc)

                def cell(n):
                    i, j = rng.integers(0, POOL, (B, n)), rng.integers(0, POOL, (B, n))
                    return dict(F=welch_greater((Vu['fl'] - Vu['fh'])[i], (Vs['fl'] - Vs['fh'])[j]).mean(),
                                T=welch_greater((Vu['tl'] - Vu['th'])[i], (Vs['tl'] - Vs['th'])[j]).mean())
                cv = curve(cell, GRID_T)
                cells.append(f"{icc:.1f}: fairness {needs(cv, 'F', GRID_T)}, uptake {needs(cv, 'T', GRID_T)}")
            print(f"    {k}, {rn(r):10s} rule: fairness contrast unit {(Mu['L0']['F'].mean() - Mu['HA']['F'].mean()):.1f} | shares "
                  f"{(Ms['L0']['F'].mean() - Ms['HA']['F'].mean()):.1f} points; psi unit {Mu['HA']['T'].mean() / Mu['L0']['T'].mean():.3f} | shares "
                  f"{Ms['HA']['T'].mean() / Ms['L0']['T'].mean():.3f};   session effect " + "   ".join(cells), flush=True)
        if Pu2 is not None:
            Mu, M2 = triplet_measures(Pu, rng, 'event'), triplet_measures(Pu2, rng, 'event')
            Vu = triplet_values(Mu['HA'], Mu['HB'], Mu['L0'], Mu['L1'], rng, 0.1)
            V2 = triplet_values(M2['HA'], M2['HB'], M2['L0'], M2['L1'], rng, 0.1)
            row = []
            for n in (3, 6, 12):
                i, j = rng.integers(0, POOL, (B, n)), rng.integers(0, POOL, (B, n))
                row.append(f"{n}: {welch_greater((Vu['fl'] - Vu['fh'])[i], (V2['fl'] - V2['fh'])[j]).mean():.4f} | "
                           f"{welch_greater((Vu['tl'] - Vu['th'])[i], (V2['tl'] - V2['th'])[j]).mean():.4f}")
            print(f"    size (unit orders against unit orders, P1, session effect .1; fairness | uptake):   " + "   ".join(row), flush=True)

    # ---------------------------------------------------------------- 6. summary
    def bind(get, pts, grid=GRID_P):
        """largest requirement over the points: (need at .90, need at .80, point)"""
        cand = [(need(get(k), grid, .90), need(get(k), grid, .80), k) for k in pts]
        return max(cand, key=lambda x: (x[0] is None, x[0] or 0, x[1] is None, x[1] or 0))

    def pp(x, per, grid=GRID_P):
        return f"{x * per}" if x is not None else f">{grid[-1] * per}"
    big = lambda x: (x[0] is None, x[0] or 0, x[1] is None, x[1] or 0)
    print("\n6. summary: PEOPLE needed at the binding gate point (power .90, in brackets .80); every figure is read from the sections above")
    a, b, c = bind(lambda k: W1[k][0]['H1a'], EDGE), bind(lambda k: W1[k][0]['K3'], EDGE), bind(lambda k: W1[k][1]['K3'], EDGE)
    print(f"   first wave, assumptions (pairs x 2): fairness {pp(a[0], 2)} ({pp(a[1], 2)}) at {a[2]}; entitlement with one item {pp(b[0], 2)} ({pp(b[1], 2)}) at {b[2]}; "
          f"with three items {pp(c[0], 2)} ({pp(c[1], 2)}) at {c[2]}")
    for r, lab, l80, l40 in (('event', 'as built (a second draw)', 'a round counts for 80 settlements', 'a round counts for 40 settlements'),
                             ('outcome', 'count rule, as built (a second draw)', 'count rule, a round counts for 80', 'count rule, a round counts for 40')):
        g = bind(lambda k: G[k, r]['PAIR'], EDGE)
        rows = {x: max(((SENS[x][k][0], SENS[x][k][1], k) for k in EDGE), key=big) for x in (lab, l80, l40)}
        worst = max((g, rows[lab]), key=big)
        print(f"   the gate, individual design as built, {rn(r)} rule (two draws of the same cells: {show(g[0])} and {show(rows[lab][0])} pairs; the larger is kept): "
              f"{pp(worst[0], 2)} ({pp(worst[1], 2)}) people at {worst[2]}; if a round counts for 80 settlements: {pp(rows[l80][0], 2)} ({pp(rows[l80][1], 2)}) at {rows[l80][2]}; "
              f"for 40: {pp(rows[l40][0], 2)} ({pp(rows[l40][1], 2)}) at {rows[l40][2]}")
    for r in ('event', 'outcome'):
        cells = []
        for lab in ('record + source', 'two record pairs'):
            x = bind(lambda k: RIV[k, r, lab]['ASSOC_H'], ('P1', 'P2', 'P3'))
            cells.append(f"association, {lab}: {pp(x[0], 2)} ({pp(x[1], 2)}) at {x[2]}")
        x = bind(lambda k: PL[k, r], ('P1', 'P2', 'P3'), G4P)
        print(f"   separating the gate from a uniform slowdown, {rn(r)} rule, binding over P1-P3: " + "; ".join(cells) +
              f"; twelve-record claims (two arms): {pp(x[0], 2, G4P)} ({pp(x[1], 2, G4P)}) at {x[2]}")
    for Nm in (6, 4):
        for r in ('event', 'outcome'):
            cells = []
            for icc in (0.0, 0.1, 0.2):
                x = bind(lambda k: LIVE[Nm, k, r, icc]['PAIR'], ('P1', 'P4'), GRID_T)
                cells.append(f"{icc:.1f}: {pp(x[0], 6 * Nm, GRID_T)} ({pp(x[1], 6 * Nm, GRID_T)})")
            print(f"   live economy by triplets, {Nm} per market, {rn(r)} rule, binding over P1 and P4, by session effect:   " + "   ".join(cells))
