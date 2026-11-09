"""POST-I032 EXPLORATORY — inverse calibration from the paper's ABM (NOT a
certification; any adopted rule needs an I033 freeze + certification).

Direction (author, 2026-11-09): calibrate from what the theory says we should
see, not from a generic design-basis effect. I032 fixed theta = .592 (a
literature prior) and shrank the frozen gate to it through a slider gain
a ~ .05; that shrinks every dynamic signature 20-fold (the paper's own
prediction figure has the HIGH P2 drop at ~45 points; at a = .058 it is ~2.6).
Here the theory's parameters are weakened instead, down to the edge of the
region where the paper's ABM claims still hold, and the measurement gain a is
treated as a separate, pilot-measurable nuisance.

Questions, written before the run:
Q1  Paper target: at the frozen task point (s=1, nuR/nuF=.25, chi=.6) what do
    the task signatures look like at the ABM's own link (a = 1, M2 noise)?
Q2  Theory edge, from the ABM record records/invcal.csv (engine mode invcal):
    s*     = speed scaling of (nuF, nuR) at which P_dw at the confirmatory cell
             crosses .5 (linear interpolation, part s);
    ratio* = nuR/nuF at which P_dw crosses .5 (part ratio);
    chi_min(ratio) = (A*(p) - p)/(mu_ref - p), the task's relative-deprivation
             permanence frontier, A*(p) = .3 + ratio*p/(1-p), p = .27 own P2
             rate, mu_ref = .65 (analytic; the ABM trap at rho = .002 does not
             depend on chi, so chi's edge comes from the permanence theorem).
    Points: P0 paper; P1 ABM chi=.4; P2 ratio edge; P3 speed edge; P4 anchoring
    edge (chi_min at ratio .25); P5 joint corner (s*, ratio*, chi_min(ratio*)),
    flagged as outside the theory region (both ABM edges at once).
Q3  Design at each point, M2 measurement, a in {1,.7,.5,.35,.25,.15,.1,.0578}:
    H1a  one-sided WMW .005 on the P1->P2 drop, N=320/arm (restoration 2:1),
         screens applied; asymptotic N for power .9 from theta;
    H1b-SIe   HIGH x MODERATE with the reference held fixed in P3 (P3 regime =
         arm, realised by conditioning on the iid P3 regime), above-median-drop
         half, c = rec_end - .25*drop (rec_end = late-P3 minus last 4 P2
         ratings), one-sided signed rank .005, n = 213;
    H1b-BA    between-arm rec_end, HIGH x MOD (P3 HIGH) vs LOW x MOD (P3 LOW),
         one-sided WMW .005 (gate: HIGH lower), n = 213/arm;
    the same tests on R3 cohorts at the same chi (specificity).
    a_min = smallest grid a with power >= .9.
B = 400 subsample replicates per cell from 60k/arm latent pools. Seed 132990.
Run from the repo root after the engine mode:
    (cd engine && ./target/release/rustsim invcal) && cp engine/out/invcal.csv records/
    python experiment/analysis/explore_inverse_calibration_I032pc.py > records/inverse_calibration_I032pc.txt
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import stats_v2 as sv

rng = np.random.default_rng(132990)
NPOOL = 60000
B = 400
END = slice(56, 60)
A_GRID = (1.0, .7, .5, .35, .25, .15, .1, .0578)
P_OWN, MU_REF = .27, .65
NUF0, NUR0 = mg.NUF, mg.NUR


def crossing(x, y, level=.5):
    """x ascending; y = P_dw; linear interpolation of the first crossing."""
    for i in range(len(x) - 1):
        if (y[i] - level) * (y[i + 1] - level) <= 0 and y[i] != y[i + 1]:
            return x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i])
    return np.nan


def chi_min(ratio):
    astar = .3 + ratio * P_OWN / (1 - P_OWN)
    return (astar - P_OWN) / (MU_REF - P_OWN)


inv = pd.read_csv('records/invcal.csv')
ps = inv[inv.part == 's'].sort_values('s')
pr = inv[inv.part == 'ratio'].sort_values('ratio')
s_star = crossing(ps.s.values, ps.p_dw.values)
r_star = crossing(pr.ratio.values, pr.p_dw.values)
print("POST-I032 exploratory inverse calibration (seed 132990; ABM record records/invcal.csv)\n")
print("ABM edges at the confirmatory cell (A0=.8, lam=.7, rho=.002, chi=.4; 200 runs/cell):")
print("  speed scaling s (nuF=.05s, nuR=.0125s):  " +
      "  ".join(f"{s:g}:{p:.2f}" for s, p in zip(ps.s, ps.p_dw)))
print("  ratio nuR/nuF (s=1):                     " +
      "  ".join(f"{r:g}:{p:.2f}" for r, p in zip(pr.ratio, pr.p_dw)))
pj = inv[inv.part == 'joint']
print("  joint (s, ratio) -> P_dw: " + "  ".join(f"({s:g},{r:g}):{p:.2f}" for s, r, p in zip(pj.s, pj.ratio, pj.p_dw)))
print(f"  s* = {s_star:.3f}   ratio* = {r_star:.4f}   chi_min(.25) = {chi_min(.25):.3f}   "
      f"chi_min(ratio*) = {chi_min(r_star):.3f}\n")

POINTS = [
    ('P0 paper', 1.0, .25, .6, True),
    ('P1 ABM chi', 1.0, .25, .4, True),
    ('P2 ratio edge', 1.0, r_star, .4, True),
    ('P3 speed edge', s_star, .25, .4, True),
    ('P4 anchor edge', 1.0, .25, chi_min(.25), True),
    ('P5 joint corner*', s_star, r_star, chi_min(r_star), False),
]


def gate_pool(s, ratio, chi, arm):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return mg.simulate_latent('gate', NPOOL, arm, rng, chi=chi)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


def reduce(lat, f, e, keep):
    ok = mg.screens(f, e, lat['acc1'], keep)
    drop = mg.drops(f)
    rec_end = f[:, mg.LATE_IDX].mean(1) - f[:, END].mean(1)
    mod = ~lat['resto_full']
    return dict(ok=ok, drop=drop, rec_end=rec_end, mod=mod, reg3=lat['reg3'])


def latent_summary(h, l):
    Lh, Ll = 100 * h['ratings'].astype(float), 100 * l['ratings'].astype(float)
    dh, dl = mg.drops(Lh), mg.drops(Ll)
    reh = Lh[:, mg.LATE_IDX].mean(1) - Lh[:, END].mean(1)
    rel = Ll[:, mg.LATE_IDX].mean(1) - Ll[:, END].mean(1)
    hm = (~h['resto_full']) & h['reg3']
    lm = (~l['resto_full']) & (~l['reg3'])
    hf = h['resto_full'] & h['reg3']
    return (dh.mean(), dl.mean(), reh[hm].mean(), rel[lm].mean(), reh[hf].mean(),
            (Lh[:, 0:30].mean(1) - Lh[:, END].mean(1))[hm].mean())


def powers(h, l, a):
    fh, eh, kh = mg.measure(h, 'M2', a, rng)
    fl, el, kl = mg.measure(l, 'M2', a, rng)
    H, L = reduce(h, fh, eh, kh), reduce(l, fl, el, kl)
    dH, dL = H['drop'][H['ok']], L['drop'][L['ok']]
    m = min(len(dH), len(dL), 40000)
    th = (dH[:m] > dL[rng.permutation(len(dL))[:m]]).mean() + .5 * (dH[:m] == dL[rng.permutation(len(dL))[:m]]).mean()
    hm = np.flatnonzero(H['ok'] & H['mod'] & H['reg3'])
    lm = np.flatnonzero(L['ok'] & L['mod'] & ~L['reg3'])
    ih, il = np.flatnonzero(H['ok']), np.flatnonzero(L['ok'])
    r1 = r2 = r3 = 0
    for _ in range(B):
        a1 = rng.choice(ih, 320, replace=False); b1 = rng.choice(il, 320, replace=False)
        r1 += sv.wmw_one_sided(L['drop'][b1], H['drop'][a1])[0]
        sh = rng.choice(hm, 213, replace=False); sl = rng.choice(lm, 213, replace=False)
        d = H['drop'][sh]; top = d > np.median(d)
        c = H['rec_end'][sh][top] - .25 * d[top]
        r2 += sv._signed_rank_less(c, .005)[0]
        r3 += sv.wmw_one_sided(H['rec_end'][sh], L['rec_end'][sl])[0]
    n90 = 2.48 / (th - .5) ** 2 if th > .5 else np.inf
    return th, n90, r1 / B, r2 / B, r3 / B


r3_cache = {}
for name, s, ratio, chi, inside in POINTS:
    h, l = gate_pool(s, ratio, chi, 'HIGH'), gate_pool(s, ratio, chi, 'LOW')
    key = round(chi, 4)
    if key not in r3_cache:
        r3_cache[key] = (mg.simulate_latent('rival_au', NPOOL, 'HIGH', rng, chi=chi),
                         mg.simulate_latent('rival_au', NPOOL, 'LOW', rng, chi=chi))
    rh, rl = r3_cache[key]
    print(f"=== {name}: s={s:.3f} ratio={ratio:.4f} chi={chi:.3f}" + ("" if inside else "  [outside: both ABM edges]"))
    g = latent_summary(h, l); q = latent_summary(rh, rl)
    print("  latent x100   dropH  dropL  recH|MOD,refH  recL|MOD,refL  recH|FULL  (P1-endP2)H|MOD")
    print(f"  gate        {g[0]:6.1f} {g[1]:6.1f} {g[2]:14.1f} {g[3]:14.1f} {g[4]:10.1f} {g[5]:10.1f}")
    print(f"  R3          {q[0]:6.1f} {q[1]:6.1f} {q[2]:14.1f} {q[3]:14.1f} {q[4]:10.1f} {q[5]:10.1f}")
    print("      a   | gate: theta  N.9/arm  H1a   SIe   BA  | R3: theta  H1a   SIe   BA")
    for a in A_GRID:
        gp = powers(h, l, a); rp = powers(rh, rl, a)
        print(f"  {a:6.4f}  |  {gp[0]:6.3f} {min(gp[1], 99999):8.0f} {gp[2]:5.2f} {gp[3]:5.2f} {gp[4]:5.2f} |"
              f"  {rp[0]:6.3f} {rp[2]:5.2f} {rp[3]:5.2f} {rp[4]:5.2f}")
    print()
