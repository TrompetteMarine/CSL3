"""KGi-DISS-I032 — market-skinned synthetic cohorts for pipeline certification.

Latent kernels are VERBATIM vectorized ports of the frozen generator
generators/predict_taskv3.py (I008/I014): 'diss' (gate), 'rival' (R1-global
fixed-hypothesis Bayesian), 'rival_us' (R4 group-contingent), 'rival_au'
(R3 aspiration-in-utility). The port preserves the frozen update ORDER and the
frozen idiosyncrasies (e.g. rival_us scales the Q-update but not the choice
logit by pi), the cumulative-session peer rate, and the trailing-15 own band
computed BEFORE the current trial's outcome is appended.

Differences from predict_taskv3, all design-mandated and frozen in
00_freeze_I032.yaml:
 - regime structure follows the DESIGN/prereg: P1/P3 regimes iid HIGH/LOW per
   participant, P2 regime = the assigned arm (predict_taskv3 held one regime
   for the whole session);
 - restoration mixed MODERATE:FULL 2:1 per arm (participant level);
 - windfalls are non-evidential and carry no latent update (app semantics, D5);
 - mu_ref is a parameter (dose cells .45/.55; default .65);
 - framing='group_fixed_rate' zeroes both log-LR terms of the group-contingent
   kernel (the announcement makes outcomes uninformative between fair-fixed and
   rigged; frozen I012 anchor: '~no P2 drop'). The gate kernel is unchanged by
   framing.

The measurement layer (shapes M1-M6 + anchoring variant) is applied AFTER the
latent pass, per 00_freeze_I032.yaml + addendum AD1.
"""
import numpy as np

T = 450
CAD = 5
NRATE = T // CAD                  # 90 ratings
PH = {1: (.65, .35), 2: (.30, .15)}
RESTO = {'FULL': (.65, .35), 'MODERATE': (.45, .35)}
NUF, NUR, TAUF, PHIM, PHIP, ALPHA, BETA = .05, .0125, .3, 1.0, .25, .2, 12.0
A0, L0, PI0, MURIG = .5, 1.0, .9, .3
GAM_AU = 0.85
CHI_FROZEN = 0.6                  # predict_taskv3 frozen value (D4: .4 companion)
SIG_EPS = 10.0                    # per-rating noise, 0-100 scale (I003 SIGR x100)

P1_IDX = slice(0, 30)
P2_IDX = slice(30, 60)
P3_IDX = slice(60, 90)
LATE_IDX = slice(75, 90)          # ratings at t > 375


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def simulate_latent(kind, n, p2_regime, rng, mu_ref=0.65, chi=CHI_FROZEN,
                    framing=False, resto_mix=(2, 1), rho_override=None):
    """One latent cohort. p2_regime: 'HIGH' or 'LOW' (scalar; one arm per call).
    Returns dict of latent per-subject arrays:
      ratings (n, 90) trust in [0,1]; ent (n, 90) aspiration proxy in [0,1];
      acc1/acc2/acc3/acc_late (n,) accuracy means; resto (n,) str array;
      rho (n,) frozen mixture.
    """
    # Kind guard (I032 run-1 defect): 'gate' is an alias of 'diss'; any other
    # unknown kind RAISES. Run 1 passed 'gate', which silently fell through to
    # the else-branch below and ran the R1-global kernel, invalidating every
    # gate and dose cell (records/pipeline_cert_I032_run1_INVALID.log).
    if kind == 'gate':
        kind = 'diss'
    if kind not in ('diss', 'rival', 'rival_us', 'rival_au'):
        raise ValueError(f"unknown generator kind {kind!r}")

    # participant-level factors
    m, f = resto_mix
    resto_full = (np.arange(n) % (m + f)) >= m          # 2:1 MODERATE:FULL
    mu3 = np.where(resto_full[:, None], RESTO['FULL'], RESTO['MODERATE'])
    reg1 = rng.random(n) < 0.5                           # P1 HIGH?
    reg3 = rng.random(n) < 0.5                           # P3 HIGH?
    reg2 = np.full(n, p2_regime == 'HIGH')
    regimes = [reg1, reg2, reg3]
    rho = np.where(np.arange(n) % 2 == 0, .002, .02)     # frozen mixture
    if rho_override is not None:                         # post-I032 exploration only
        rho = np.full(n, float(rho_override))

    Q = np.full((n, 2), 0.5)
    L = np.full(n, L0)
    A = np.full(n, A0)
    lp = np.full(n, np.log(PI0 / (1 - PI0)))
    ent_exp = np.full(n, A0)
    rec_au = np.full(n, 0.5)
    peer_hits = np.zeros(n)
    ring = np.zeros((n, 15))
    ring_cnt = 0

    ratings = np.empty((n, NRATE), dtype=np.float32)
    ent_out = np.empty((n, NRATE), dtype=np.float32)
    acc_sum = np.zeros((n, 3))
    acc_late = np.zeros(n)
    ri = 0
    rows = np.arange(n)

    for t in range(T):
        ph = 0 if t < 150 else (1 if t < 300 else 2)
        mu_good = np.full(n, PH[1][0] if ph == 0 else PH[2][0]) if ph < 2 else mu3[:, 0]
        mu_bad = np.full(n, PH[1][1] if ph == 0 else PH[2][1]) if ph < 2 else mu3[:, 1]

        if kind == 'diss':
            dq = Q[:, 0] - Q[:, 1]
        elif kind == 'rival':
            pi = _sigmoid(lp)
            dq = pi * (Q[:, 0] - Q[:, 1])
        else:                                   # rival_us, rival_au: frozen 1.0 factor
            dq = Q[:, 0] - Q[:, 1]
        p0 = _sigmoid(BETA * dq)
        arm = (rng.random(n) >= p0).astype(np.int8)       # 0 = good
        mu_arm = np.where(arm == 0, mu_good, mu_bad)
        R = (rng.random(n) < mu_arm).astype(np.float64)

        # peer outcome: trailing-15 own band BEFORE appending R (frozen order)
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

        # append own outcome to the ring
        ring[:, t % 15] = R
        ring_cnt += 1
        k = min(ring_cnt, 15)
        trail_after = ring[:, :k].mean(axis=1) if ring_cnt < 15 else ring.mean(axis=1)

        if kind == 'diss':
            qsel = Q[rows, arm]
            Q[rows, arm] = qsel + ALPHA * L * (R - qsel)
            D = PHIM * np.maximum(A - R, 0) + PHIP * np.maximum(R - A, 0)
            L = np.clip(L - NUF * np.maximum(D - TAUF, 0) + NUR * (D <= TAUF), 0, 1)
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
        else:                                   # 'rival' (R1-global) / 'rival_us' (R4)
            pi = _sigmoid(lp)
            qsel = Q[rows, arm]
            muhat = np.clip(qsel, .05, .95)
            own = R * np.log(muhat / MURIG) + (1 - R) * np.log((1 - muhat) / (1 - MURIG))
            if kind == 'rival_us':
                obs = 0.0
            else:
                mup = np.clip(peer_rate, .05, .95)
                obs = peer_R * np.log(mup / MURIG) + (1 - peer_R) * np.log((1 - mup) / (1 - MURIG))
            if framing:                          # group_fixed_rate: uninformative
                own = 0.0
                obs = 0.0
            lp = np.clip(lp + own + obs, -12, 12)
            Q[rows, arm] = qsel + ALPHA * pi * (R - qsel)
            ent_exp = 0.98 * ent_exp + 0.02 * R
            trust = _sigmoid(lp)
            ent = ent_exp

        acc_sum[:, ph] += (arm == 0)
        if t >= 375:
            acc_late += (arm == 0)
        if (t + 1) % CAD == 0:
            ratings[:, ri] = trust
            ent_out[:, ri] = ent
            ri += 1

    return dict(ratings=ratings, ent=ent_out,
                acc1=acc_sum[:, 0] / 150, acc2=acc_sum[:, 1] / 150,
                acc3=acc_sum[:, 2] / 150, acc_late=acc_late / 75,
                resto_full=resto_full, rho=rho, reg1=reg1, reg3=reg3)


# ------------------------------------------------------------- measurement layer
def measure(lat, shape, a, rng):
    """Apply measurement shape (freeze I032 + AD1) to a latent cohort dict.
    Returns reported fairness (n,90), reported entitlement (n,90), and the
    stochastic-exclusion keep-mask (M6 only; else all-True)."""
    n = lat['ratings'].shape[0]
    f_lat = lat['ratings'].astype(np.float64)
    e_lat = lat['ent'].astype(np.float64)

    if shape == 'M4':
        g = np.maximum(.05, 1 + 0.6 * rng.standard_t(3, n) / np.sqrt(3))
    elif shape == 'M5':
        g = np.exp(rng.normal(-0.32, 0.8, n))
    else:                                        # M1, M2, M3, M6: g = 1
        g = np.ones(n)

    def rep(latmat):
        eps = rng.normal(0, SIG_EPS, latmat.shape)
        r = 50 + a * g[:, None] * (100 * latmat - 50) + eps
        return np.clip(np.round(r / 5) * 5, 0, 100)

    f = rep(f_lat)
    e = rep(e_lat)

    nonresp = np.zeros(n, bool)
    if shape == 'M2':                            # wobble-parked never-movers (AD1)
        nm = rng.random(n) < 0.15
        park = rng.uniform(20, 80, nm.sum())
        for mat in (f, e):
            w = park[:, None] + rng.normal(0, SIG_EPS, (nm.sum(), NRATE))
            mat[nm] = np.clip(np.round(w / 5) * 5, 0, 100)
    if shape in ('M3', 'M6'):                    # non-responders, no effect
        nonresp = rng.random(n) < 0.20
        u = rng.uniform(20, 80, nonresp.sum())
        for mat in (f, e):
            w = u[:, None] + rng.normal(0, 8, (nonresp.sum(), NRATE))
            mat[nonresp] = np.clip(np.round(w / 5) * 5, 0, 100)

    keep = np.ones(n, bool)
    if shape == 'M6':                            # stochastic screens, enriched 3x
        p_ex = np.where(nonresp, 0.30, 0.075)
        keep = rng.random(n) >= p_ex
    return f, e, keep


def measure_anchored(lat, a, rng, lam=0.3):
    """Anchoring variant: AR(1) on the reported fairness series (M2 base)."""
    f, e, keep = measure(lat, 'M2', a, rng)
    fa = f.copy()
    for k in range(1, NRATE):
        fa[:, k] = np.clip(np.round((lam * fa[:, k - 1] + (1 - lam) * f[:, k]) / 5) * 5, 0, 100)
    return fa, e, keep


# ----------------------------------------------------- pipeline-side reductions
def screens(f, e, acc1, keep):
    """Preregistered screens active in certification (AD1): zero slider
    variance; P1 accuracy below chance + 2SE; plus the stochastic keep mask."""
    se2 = 2 * np.sqrt(0.25 / 150)
    ok = keep.copy()
    ok &= ~((f.var(axis=1) == 0) & (e.var(axis=1) == 0))
    ok &= acc1 >= 0.5 + se2
    return ok


def drops(f):
    return f[:, P1_IDX].mean(axis=1) - f[:, P2_IDX].mean(axis=1)


def recovery(f):
    return f[:, LATE_IDX].mean(axis=1) - f[:, P2_IDX].mean(axis=1)


def p1_sd(f):
    return f[:, P1_IDX].std(axis=1, ddof=1)
