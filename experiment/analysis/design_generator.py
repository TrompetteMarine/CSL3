"""Design-space generator (post-I032; for optimising task length and N).

simulate_design() is the frozen latent kernel of market_generator.simulate_latent
with the task geometry made explicit: phase lengths, rating cadence, P1/P2 odds,
initial aspiration, and an optional fixed P3 board regime. The update ORDER, the
random-number draw ORDER and every kernel line are unchanged, so with the default
geometry (150/150/150, cadence 5, P2 .30/.15) it reproduces simulate_latent bit
for bit (tests/test_design_generator.py checks all four kinds, both arms,
framing, trace). measure_design() is market_generator.measure with the rating
count taken from the data instead of the module constant (bit-identical at 90
ratings).

Rating indices returned in 'idx' (python slices over the rating axis):
  p1, p2, p3        phase ratings
  p1a, p1b          first and second half of P1 (split-sample selection/test)
  end               last 4 P2 ratings
  presel            the P2 ratings just before 'end' used for selection (up to 6)
  late              second half of P3

choice_every > 1 gives the batched-period task: one ticket choice per period of
choice_every draws (outcomes then shown as a period summary). With cadence =
choice_every there is one rating pair per period. Default 1 = the per-round task.
"""
import numpy as np

from market_generator import (PH, RESTO, NUF, NUR, TAUF, PHIM, PHIP, ALPHA, BETA,
                              A0, L0, PI0, MURIG, GAM_AU, CHI_FROZEN, SIG_EPS,
                              _sigmoid)
import market_generator as _mg


def _idx(phases, cadence):
    T1, T2, T3 = phases
    r1, r2, r3 = T1 // cadence, T2 // cadence, T3 // cadence
    p1, p2, p3 = slice(0, r1), slice(r1, r1 + r2), slice(r1 + r2, r1 + r2 + r3)
    h = r1 // 2
    end = slice(r1 + r2 - 4, r1 + r2)
    pre = slice(max(r1, r1 + r2 - 10), r1 + r2 - 4)
    late = slice(r1 + r2 + r3 - r3 // 2, r1 + r2 + r3)
    return dict(p1=p1, p2=p2, p3=p3, p1a=slice(0, h), p1b=slice(h, r1), end=end,
                presel=pre, late=late)


def simulate_design(kind, n, p2_regime, rng, phases=(150, 150, 150), cadence=5,
                    p1_odds=None, p2_odds=None, mu_ref=0.65, chi=CHI_FROZEN,
                    framing=False, resto_mix=(2, 1), rho_override=None, a0=None,
                    reg3_fixed=None, trace=False, choice_every=1):
    if kind == 'gate':
        kind = 'diss'
    if kind not in ('diss', 'rival', 'rival_us', 'rival_au'):
        raise ValueError(f"unknown generator kind {kind!r}")
    # module constants are read at call time so exploratory scalings of NUF/NUR
    # applied to market_generator also apply here
    nuf, nur = _mg.NUF, _mg.NUR
    T1, T2, T3 = phases
    T = T1 + T2 + T3
    nrate = T // cadence
    ph1 = p1_odds if p1_odds is not None else PH[1]
    ph2 = p2_odds if p2_odds is not None else PH[2]
    a_init = A0 if a0 is None else a0

    m, f = resto_mix
    resto_full = (np.arange(n) % (m + f)) >= m
    mu3 = np.where(resto_full[:, None], RESTO['FULL'], RESTO['MODERATE'])
    reg1 = rng.random(n) < 0.5
    reg3 = rng.random(n) < 0.5
    if reg3_fixed is not None:                 # draw kept: RNG order unchanged
        reg3 = np.full(n, bool(reg3_fixed))
    reg2 = np.full(n, p2_regime == 'HIGH')
    regimes = [reg1, reg2, reg3]
    rho = np.where(np.arange(n) % 2 == 0, .002, .02)
    if rho_override is not None:
        rho = np.full(n, float(rho_override))

    Q = np.full((n, 2), 0.5)
    L = np.full(n, L0)
    A = np.full(n, a_init)
    lp = np.full(n, np.log(PI0 / (1 - PI0)))
    ent_exp = np.full(n, a_init)
    rec_au = np.full(n, 0.5)
    peer_hits = np.zeros(n)
    ring = np.zeros((n, 15))
    ring_cnt = 0

    ratings = np.empty((n, nrate), dtype=np.float32)
    ent_out = np.empty((n, nrate), dtype=np.float32)
    acc_sum = np.zeros((n, 3))
    acc_late = np.zeros(n)
    late_from = T1 + T2 + T3 - T3 // 2
    ri = 0
    rows = np.arange(n)
    if trace:
        tr_R = np.empty((n, T), dtype=np.int8)
        tr_arm = np.empty((n, T), dtype=np.int8)
        tr_peer = np.empty((n, T), dtype=np.int8)

    for t in range(T):
        ph = 0 if t < T1 else (1 if t < T1 + T2 else 2)
        mu_good = np.full(n, ph1[0] if ph == 0 else ph2[0]) if ph < 2 else mu3[:, 0]
        mu_bad = np.full(n, ph1[1] if ph == 0 else ph2[1]) if ph < 2 else mu3[:, 1]

        if kind == 'diss':
            dq = Q[:, 0] - Q[:, 1]
        elif kind == 'rival':
            pi = _sigmoid(lp)
            dq = pi * (Q[:, 0] - Q[:, 1])
        else:
            dq = Q[:, 0] - Q[:, 1]
        p0 = _sigmoid(BETA * dq)
        if choice_every == 1 or t % choice_every == 0:
            # batched periods (choice_every > 1): one ticket choice per period,
            # held for the period's draws; default draws exactly as before
            arm = (rng.random(n) >= p0).astype(np.int8)
        mu_arm = np.where(arm == 0, mu_good, mu_bad)
        R = (rng.random(n) < mu_arm).astype(np.float64)

        if ring_cnt == 0:
            trail = np.full(n, 0.5)
        else:
            k = min(ring_cnt, 15)
            trail = ring[:, :k].mean(axis=1) if ring_cnt < 15 else ring.mean(axis=1)
        high_now = regimes[ph]
        p_peer = np.where(high_now, mu_ref, np.clip(trail, .05, .95))
        peer_R = (rng.random(n) < p_peer).astype(np.float64)
        peer_hits += peer_R
        peer_rate = peer_hits / (t + 1)
        if trace:
            tr_R[:, t] = R
            tr_arm[:, t] = arm
            tr_peer[:, t] = peer_R

        ring[:, t % 15] = R
        ring_cnt += 1
        k = min(ring_cnt, 15)
        trail_after = ring[:, :k].mean(axis=1) if ring_cnt < 15 else ring.mean(axis=1)

        if kind == 'diss':
            qsel = Q[rows, arm]
            Q[rows, arm] = qsel + ALPHA * L * (R - qsel)
            D = PHIM * np.maximum(A - R, 0) + PHIP * np.maximum(R - A, 0)
            L = np.clip(L - nuf * np.maximum(D - TAUF, 0) + nur * (D <= TAUF), 0, 1)
            ref = np.where(high_now, peer_rate, trail_after)
            A = np.clip((1 - rho) * A + rho * ((1 - chi) * R + chi * ref), 0, 1)
            trust = L
            ent = A
        elif kind == 'rival_au':
            u = R - GAM_AU * np.maximum(A - R, 0)
            qsel = Q[rows, arm]
            Q[rows, arm] = np.clip(qsel + ALPHA * (u - qsel), -1, 1)
            rec_au = 0.9 * rec_au + 0.1 * R
            ref = np.where(high_now, peer_rate, trail_after)
            A = np.clip((1 - rho) * A + rho * ((1 - chi) * R + chi * ref), 0, 1)
            trust = np.clip(1 - GAM_AU * np.maximum(A - rec_au, 0), 0, 1)
            ent = A
        else:
            pi = _sigmoid(lp)
            qsel = Q[rows, arm]
            muhat = np.clip(qsel, .05, .95)
            own = R * np.log(muhat / MURIG) + (1 - R) * np.log((1 - muhat) / (1 - MURIG))
            if kind == 'rival_us':
                obs = 0.0
            else:
                mup = np.clip(peer_rate, .05, .95)
                obs = peer_R * np.log(mup / MURIG) + (1 - peer_R) * np.log((1 - mup) / (1 - MURIG))
            if framing:
                own = 0.0
                obs = 0.0
            lp = np.clip(lp + own + obs, -12, 12)
            Q[rows, arm] = qsel + ALPHA * pi * (R - qsel)
            ent_exp = 0.98 * ent_exp + 0.02 * R
            trust = _sigmoid(lp)
            ent = ent_exp

        acc_sum[:, ph] += (arm == 0)
        if t >= late_from:
            acc_late += (arm == 0)
        if (t + 1) % cadence == 0:
            ratings[:, ri] = trust
            ent_out[:, ri] = ent
            ri += 1

    out = dict(ratings=ratings, ent=ent_out,
               acc1=acc_sum[:, 0] / T1, acc2=acc_sum[:, 1] / T2,
               acc3=acc_sum[:, 2] / T3, acc_late=acc_late / (T3 // 2),
               resto_full=resto_full, rho=rho, reg1=reg1, reg3=reg3,
               idx=_idx(phases, cadence), phases=phases, cadence=cadence)
    if trace:
        out.update(R=tr_R, arm=tr_arm, peer=tr_peer)
    return out


def measure_design(lat, shape, a, rng):
    """market_generator.measure with the rating count read from the data."""
    n, nr = lat['ratings'].shape
    f_lat = lat['ratings'].astype(np.float64)
    e_lat = lat['ent'].astype(np.float64)
    if shape == 'M4':
        g = np.maximum(.05, 1 + 0.6 * rng.standard_t(3, n) / np.sqrt(3))
    elif shape == 'M5':
        g = np.exp(rng.normal(-0.32, 0.8, n))
    else:
        g = np.ones(n)

    def rep(latmat):
        eps = rng.normal(0, SIG_EPS, latmat.shape)
        r = 50 + a * g[:, None] * (100 * latmat - 50) + eps
        return np.clip(np.round(r / 5) * 5, 0, 100)

    f = rep(f_lat)
    e = rep(e_lat)
    nonresp = np.zeros(n, bool)
    if shape == 'M2':
        nm = rng.random(n) < 0.15
        park = rng.uniform(20, 80, nm.sum())
        for mat in (f, e):
            w = park[:, None] + rng.normal(0, SIG_EPS, (nm.sum(), nr))
            mat[nm] = np.clip(np.round(w / 5) * 5, 0, 100)
    if shape in ('M3', 'M6'):
        nonresp = rng.random(n) < 0.20
        u = rng.uniform(20, 80, nonresp.sum())
        for mat in (f, e):
            w = u[:, None] + rng.normal(0, 8, (nonresp.sum(), nr))
            mat[nonresp] = np.clip(np.round(w / 5) * 5, 0, 100)
    keep = np.ones(n, bool)
    if shape == 'M6':
        p_ex = np.where(nonresp, 0.30, 0.075)
        keep = rng.random(n) >= p_ex
    return f, e, keep


def screens_design(f, e, acc1, keep, T1):
    """Preregistered screens (I032 AD1) with the P1 accuracy bound scaled to the
    P1 length: zero slider variance on both sliders; P1 accuracy below chance +
    2 s.e."""
    se2 = 2 * np.sqrt(0.25 / T1)
    ok = keep.copy()
    ok &= ~((f.var(axis=1) == 0) & (e.var(axis=1) == 0))
    ok &= acc1 >= 0.5 + se2
    return ok
