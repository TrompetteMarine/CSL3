"""POST-HOC / EXPLORATORY (written after explore_h1b_candidates_I032pc.py Q3; NOT a
certification).

Q4  The P3-reversal behavioural contrast (late-P3 correct-choice rate, HIGH - LOW)
    is large under the frozen gate. How much survives if the latent gate is
    weaker? Scale the delegitimation rate NUF by s in {1, .5, .25, .125}; report
    the latent fairness H1a theta (no measurement layer) and the reversal contrast
    with its standardized size d and asymptotic one-sided WMW-free z-test power at
    n = 320/arm, alpha .005 (normal approximation on the per-subject late-P3
    correct rate; choices carry no slider attenuation). R3 shown for reference
    (no NUF). MODERATE:FULL = 2:1 as in the design; reversal in both.

Seed 132970. Run from the repo root:
    python experiment/analysis/explore_reversal_strength_I032pc.py > records/reversal_strength_I032pc.txt
"""
import sys

import numpy as np
from scipy.stats import norm

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg

rng = np.random.default_rng(132970)
N = 20000
n = 320
NUF0 = mg.NUF
REV = {'FULL': (.35, .65), 'MODERATE': (.35, .45)}


def run(kind, arm, s):
    saved = dict(mg.RESTO)
    mg.RESTO.update(REV)
    mg.NUF = NUF0 * s
    try:
        lat = mg.simulate_latent(kind, N, arm, rng)
    finally:
        mg.RESTO.clear()
        mg.RESTO.update(saved)
        mg.NUF = NUF0
    return lat


print("POST-HOC exploratory reversal-contrast strength (seed 132970; n=20000/arm; MOD:FULL 2:1)")
print(f"{'model':10s} {'NUF x':>5s} {'H1a theta':>9s} {'corrH':>6s} {'corrL':>6s} {'diff':>6s} {'d':>6s} {'power':>6s}")
for kind, scales in (('gate', (1, .5, .25, .125)), ('rival_au', (1,))):
    for s in scales:
        h, l = run(kind, 'HIGH', s), run(kind, 'LOW', s)
        dh = mg.drops(100 * h['ratings'].astype(float))
        dl = mg.drops(100 * l['ratings'].astype(float))
        th = (dh > dl[rng.permutation(N)]).mean()
        ch, cl = 1 - h['acc_late'], 1 - l['acc_late']
        diff = ch.mean() - cl.mean()
        sd = np.sqrt((ch.var() + cl.var()) / 2)
        d = diff / sd
        z = abs(d) * np.sqrt(n / 2)
        pw = norm.cdf(z - norm.ppf(.995))
        print(f"{'gate' if kind == 'gate' else 'R3':10s} {s:5.3f} {th:9.3f} {ch.mean():6.3f} {cl.mean():6.3f} {diff:+6.3f} {d:+6.2f} {pw:6.3f}")
