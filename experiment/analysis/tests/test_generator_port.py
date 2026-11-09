"""Audit test: the vectorized market_generator kernels equal a scalar reference
written line-by-line from the frozen generators/predict_taskv3.py (I008/I014),
driven by the SAME uniform draws, under the design regime structure (P1/P3
regimes iid per participant, P2 = arm). Any porting error in update order,
clipping, trailing window, peer process or choice rule shows up as a numeric
difference. Framing (fixed-rate) is checked as: own and peer log-LR terms zero.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import market_generator as mg

T, CAD = 450, 5
PH = {1: (.65, .35), 2: (.30, .15)}
RESTO = {'FULL': (.65, .35), 'MODERATE': (.45, .35)}
NUF, NUR, TAUF, PHIM, PHIP, ALPHA, BETA = .05, .0125, .3, 1.0, .25, .2, 12.0
A0, L0, PI0, MURIG = .5, 1.0, .9, .3
GAM_AU = 0.85


def reference(kind, n, p2, seed, chi=.6, mu_ref=.65, framing=False):
    rng = np.random.default_rng(seed)
    u_r1, u_r3 = rng.random(n), rng.random(n)
    U = np.empty((T, 3, n))
    for t in range(T):
        U[t, 0], U[t, 1], U[t, 2] = rng.random(n), rng.random(n), rng.random(n)
    out = np.empty((n, T // CAD))
    for s in range(n):
        resto = 'FULL' if (s % 3) >= 2 else 'MODERATE'
        regs = ['HIGH' if u_r1[s] < .5 else 'LOW', p2, 'HIGH' if u_r3[s] < .5 else 'LOW']
        rho = .002 if s % 2 == 0 else .02
        Q = [.5, .5]; L, A = L0, A0
        lp = np.log(PI0 / (1 - PI0)); ent_exp = A0; rec_au = .5
        peer_hits = 0.0; own_recent = []; k = 0
        for t in range(T):
            ph = 0 if t < 150 else (1 if t < 300 else 2)
            mu = PH[ph + 1] if ph < 2 else RESTO[resto]
            regime = regs[ph]
            pi = 1 / (1 + np.exp(-lp))
            dq = (pi if kind == 'rival' else 1.0) * (Q[0] - Q[1])
            p0 = 1 / (1 + np.exp(-BETA * dq))
            arm = 0 if U[t, 0, s] < p0 else 1
            R = 1.0 if U[t, 1, s] < mu[arm] else 0.0
            pp = mu_ref if regime == 'HIGH' else float(np.clip(
                np.mean(own_recent[-15:]) if own_recent else .5, .05, .95))
            peer_R = 1.0 if U[t, 2, s] < pp else 0.0
            peer_hits += peer_R; peer_rate = peer_hits / (t + 1)
            own_recent.append(R)
            if kind == 'gate':
                Q[arm] += ALPHA * L * (R - Q[arm])
                D = PHIM * max(A - R, 0) + PHIP * max(R - A, 0)
                L = float(np.clip(L - NUF * max(D - TAUF, 0) + NUR * (D <= TAUF), 0, 1))
                ref = peer_rate if regime == 'HIGH' else np.mean(own_recent[-15:])
                A = float(np.clip((1 - rho) * A + rho * ((1 - chi) * R + chi * ref), 0, 1))
                trust = L
            elif kind == 'rival_au':
                u = R - GAM_AU * max(A - R, 0)
                Q[arm] = float(np.clip(Q[arm] + ALPHA * (u - Q[arm]), -1, 1))
                rec_au = .9 * rec_au + .1 * R
                ref = peer_rate if regime == 'HIGH' else np.mean(own_recent[-15:])
                A = float(np.clip((1 - rho) * A + rho * ((1 - chi) * R + chi * ref), 0, 1))
                trust = float(np.clip(1 - GAM_AU * max(A - rec_au, 0), 0, 1))
            else:
                muhat = np.clip(Q[arm], .05, .95)
                own = R * np.log(muhat / MURIG) + (1 - R) * np.log((1 - muhat) / (1 - MURIG))
                if kind == 'rival_us':
                    obs = 0.0
                else:
                    mup = np.clip(peer_rate, .05, .95)
                    obs = peer_R * np.log(mup / MURIG) + (1 - peer_R) * np.log((1 - mup) / (1 - MURIG))
                if framing:
                    own = obs = 0.0
                lp = float(np.clip(lp + own + obs, -12, 12))
                Q[arm] += ALPHA * pi * (R - Q[arm])
                trust = 1 / (1 + np.exp(-lp))
            if (t + 1) % CAD == 0:
                out[s, k] = trust; k += 1
    return out


@pytest.mark.parametrize("kind", ["gate", "rival_au", "rival", "rival_us"])
@pytest.mark.parametrize("p2", ["HIGH", "LOW"])
def test_port_equals_reference(kind, p2):
    n, seed = 60, 777
    ref = reference(kind, n, p2, seed)
    vec = mg.simulate_latent(kind, n, p2, np.random.default_rng(seed))["ratings"]
    assert np.allclose(vec.astype(float), ref, atol=1e-6), \
        f"max abs diff {np.abs(vec - ref).max():.3g}"


def test_framing_zeroes_loglr():
    ref = reference("rival_us", 60, "HIGH", 778, framing=True)
    vec = mg.simulate_latent("rival_us", 60, "HIGH", np.random.default_rng(778),
                             framing=True)["ratings"]
    assert np.allclose(vec.astype(float), ref, atol=1e-6)
    assert np.allclose(ref, ref[:, :1])          # trust never moves


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        mg.simulate_latent("typo", 5, "HIGH", np.random.default_rng(1))
