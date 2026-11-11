"""KGi-DISS-I040 part 2: yoked pairs in design S1x (freeze 00_freeze_I040.yaml).

A pair is one HIGH and one LOW participant who share every random number that the design
could share: the rich-round board, the ticket-choice draws, the settlement draws and the
board draws. The gate kernel is the one in design_generator.py. Seed 137000.
    python experiment/analysis/twins_I040.py > records/twins_I040.txt
"""
import sys

import numpy as np
from scipy import stats as st

sys.path.insert(0, 'experiment/analysis')
import estimand_core_I038 as ec
import market_generator as mg
from probe_design_I037 import ODDS, P1TAG

K, R1, R2 = ec.D['k'], ec.D['r1'], ec.D['r2']
T1, T2 = R1 * K, R2 * K
PH1, MU_REF = P1TAG[ec.P1]
PH2 = ODDS[ec.D['odds']]
ARMS = ('HIGH', 'LOW')
sig = lambda x: 1 / (1 + np.exp(-x))


def twins(pt, n, rng, phip=None, same_person=True, choice_free=False):
    nuf, nur, chi = mg.NUF * pt[1], mg.NUF * pt[1] * pt[2], pt[3]
    phip = mg.PHIP if phip is None else phip
    base_rho = np.where(np.arange(n) % 2 == 0, .002, .02)
    rho = {'HIGH': base_rho, 'LOW': base_rho if same_person else rng.permutation(base_rho)}
    reg1 = rng.random(n) < 0.5
    S = {a: dict(Q=np.full((n, 2), 0.5), L=np.full(n, mg.L0), A=np.full(n, mg.A0), ring=np.zeros((n, 15)),
                 hits=np.zeros(n), arm=np.zeros(n, int)) for a in ARMS}
    rows = np.arange(n)
    ord_ok = np.ones(n, bool); same_choice = np.ones(n, bool); same_out = np.ones(n, bool)
    concl = np.ones(n, bool); n_viol = np.zeros(n)
    Lr = {a: np.empty((n, R1 + R2)) for a in ARMS}
    Ar = {a: np.empty((n, R1 + R2)) for a in ARMS}
    wins = {a: np.zeros((n, R1 + R2)) for a in ARMS}
    for t in range(T1 + T2):
        ph = 0 if t < T1 else 1
        if t % K == 0:
            uc = rng.random(n)
            for a in ARMS:
                s = S[a]
                s['arm'] = (uc >= sig(mg.BETA * (s['Q'][:, 0] - s['Q'][:, 1]))).astype(int)
                if choice_free and ph == 1:
                    s['arm'] = np.zeros(n, int)
            if ph == 1:
                same_choice &= S['HIGH']['arm'] == S['LOW']['arm']
        uo, up = rng.random(n), rng.random(n)
        cnt = min(t, 15)
        ref, out = {}, {}
        for a in ARMS:
            s = S[a]
            mu = np.where(s['arm'] == 0, (PH1 if ph == 0 else PH2)[0], (PH1 if ph == 0 else PH2)[1])
            R = (uo < mu).astype(float)
            trail = np.full(n, 0.5) if t == 0 else s['ring'][:, :cnt].mean(1)
            high = reg1 if ph == 0 else np.full(n, a == 'HIGH')
            s['hits'] += up < np.where(high, MU_REF, np.clip(trail, .05, .95))
            s['ring'][:, t % 15] = R
            trail_after = s['ring'][:, :min(t + 1, 15)].mean(1)
            q = s['Q'][rows, s['arm']]
            s['Q'][rows, s['arm']] = q + mg.ALPHA * s['L'] * (R - q)
            D = mg.PHIM * np.maximum(s['A'] - R, 0) + phip * np.maximum(R - s['A'], 0)
            s['L'] = np.clip(s['L'] - nuf * np.maximum(D - mg.TAUF, 0) + nur * (D <= mg.TAUF), 0, 1)
            ref[a] = np.where(high, s['hits'] / (t + 1), trail_after)
            s['A'] = np.clip((1 - rho[a]) * s['A'] + rho[a] * ((1 - chi) * R + chi * ref[a]), 0, 1)
            out[a] = R
            wins[a][:, t // K] += R
        if ph == 1:
            bad = ref['LOW'] > ref['HIGH'] + 1e-12
            ord_ok &= ~bad
            n_viol += bad
            same_out &= out['HIGH'] == out['LOW']
            concl &= (S['HIGH']['L'] <= S['LOW']['L'] + 1e-12) & (S['HIGH']['A'] >= S['LOW']['A'] - 1e-12)
        if (t + 1) % K == 0:
            for a in ARMS:
                Lr[a][:, t // K] = S[a]['L']
                Ar[a][:, t // K] = S[a]['A']
    return dict(L=Lr, A=Ar, wins=wins, ord_ok=ord_ok, same_choice=same_choice, same_out=same_out,
                concl=concl, viol_share=n_viol.mean() / T2)


def rating(l, rng, a=0.5, sr=5.8):
    return np.clip(np.round((50 + a * (100 * l - 50) + rng.normal(0, sr, l.shape)) / 5) * 5, 0, 100)


if __name__ == '__main__':
    rng = np.random.default_rng(137000)
    N = 20000
    PT = {p[0]: p for p in ec.GATE_POINTS}
    print("KGi-DISS-I040 part 2: yoked pairs in design S1x (20,000 pairs per cell; seed 137000)\n")

    print("gate GT: legitimacy at probe time against the I039 pools (mean; share below .05 in HIGH)")
    REF = {'P1': (0.110, 0.827, 0.869), 'P4': (0.409, 0.403, 0.874)}
    ok = True
    base = {}
    for k in ('P0', 'P1', 'P2', 'P3', 'P4'):
        base[k] = twins(PT[k], N, rng)
        if k in REF:
            h, lo = base[k]['L']['HIGH'][:, -1], base[k]['L']['LOW'][:, -1]
            d = (abs(h.mean() - REF[k][0]), abs((h < .05).mean() - REF[k][1]), abs(lo.mean() - REF[k][2]))
            ok &= max(d) <= .015
            print(f"  {k}: HIGH {h.mean():.3f} ({(h < .05).mean():.3f}), LOW {lo.mean():.3f}; I039 pools {REF[k][0]:.3f} "
                  f"({REF[k][1]:.3f}), {REF[k][2]:.3f}; largest gap {max(d):.3f}")
    print(f"  GT {'PASS' if ok else 'FAIL'}\n")

    print("A. T13 in the design as it stands, identical persons in a pair")
    print("   point  refs ordered at every   settlements with   same ticket in   same outcomes at    conclusion at every settlement:")
    print("          deprivation settlement  the order broken   every round      every settlement    all pairs | both hypotheses hold (pairs) | a hypothesis fails")
    for k, b in base.items():
        hyp = b['ord_ok'] & b['same_out']
        print(f"   {k}     {b['ord_ok'].mean():.4f}                  {b['viol_share']:.5f}            {b['same_choice'].mean():.3f}"
              f"            {b['same_out'].mean():.3f}               {b['concl'].mean():.4f}    | {b['concl'][hyp].mean():.4f} ({hyp.sum()})"
              f"            | {b['concl'][~hyp].mean():.4f}", flush=True)
    print("   weaker reading (legitimacy ordered at the six round ends only): " +
          "  ".join(f"{k} {np.mean((b['L']['HIGH'] <= b['L']['LOW'] + 1e-12).all(1)):.4f}" for k, b in base.items()))

    print("\nB. choice-free deprivation (one ticket at the better odds): same outcomes by construction")
    for k in ('P1', 'P4'):
        b = twins(PT[k], N, rng, choice_free=True)
        hyp = b['ord_ok'] & b['same_out']
        print(f"   {k}: same outcomes {b['same_out'].mean():.3f}; refs ordered {b['ord_ok'].mean():.4f}; conclusion: all pairs "
              f"{b['concl'].mean():.4f}, hypotheses hold {b['concl'][hyp].mean():.4f}; legitimacy at probe time HIGH "
              f"{b['L']['HIGH'][:, -1].mean():.3f} (with choice {base[k]['L']['HIGH'][:, -1].mean():.3f}), LOW "
              f"{b['L']['LOW'][:, -1].mean():.3f} (with choice {base[k]['L']['LOW'][:, -1].mean():.3f})", flush=True)

    print("\nC. if a win can erode fairness (phi_plus above the tolerance .3), P1, identical persons")
    print("   phi_plus   legitimacy at probe HIGH / LOW   ratio   conclusion: all pairs | hypotheses hold   "
          "legitimacy after the rich round   LOW, rounds 4-6: slope of the change in legitimacy on the round's win share")
    for pp in (0.25, 0.5, 1.0):
        b = twins(PT['P1'], N, rng, phip=pp)
        hyp = b['ord_ok'] & b['same_out']
        h, lo = b['L']['HIGH'][:, -1], b['L']['LOW'][:, -1]
        dl = (b['L']['LOW'][:, 3:6] - b['L']['LOW'][:, 2:5]).ravel()
        ws = (b['wins']['LOW'][:, 3:6] / K).ravel()
        slope = np.polyfit(ws, dl, 1)[0]
        print(f"   {pp:<5}      {h.mean():.3f} / {lo.mean():.3f}                    {h.mean() / lo.mean():.3f}   {b['concl'].mean():.4f} | "
              f"{b['concl'][hyp].mean():.4f} ({hyp.sum()})          {b['L']['LOW'][:, 0].mean():.3f}                             {slope:+.3f}", flush=True)

    print("\nD. pairs of different people (rigidity drawn independently): last fairness rating, gain .5, noise 5.8")
    print("   point   mean rating HIGH / LOW   P(LOW > HIGH within pair)   power at one-sided .005: yoked pairs, signed rank | unpaired, rank test")
    for k in ('P0', 'P1', 'P2', 'P3', 'P4'):
        b = twins(PT[k], N, rng, same_person=False)
        fh, fl = rating(b['L']['HIGH'][:, -1], rng), rating(b['L']['LOW'][:, -1], rng)
        row = []
        for npair in (18, 36, 72):
            pp = pu = 0
            for _ in range(1000):
                i = rng.integers(0, N, npair)
                d = fl[i] - fh[i]
                if np.any(d != 0):
                    pp += st.wilcoxon(d, alternative='greater', zero_method='wilcox').pvalue < .005
                j = rng.integers(0, N, npair)                     # an unrelated LOW sample: no yoking
                pu += st.mannwhitneyu(fl[j], fh[i], alternative='greater').pvalue < .005
            row.append(f"{npair} pairs {pp / 1000:.3f} | {pu / 1000:.3f}")
        print(f"   {k}      {fh.mean():.1f} / {fl.mean():.1f}             {np.mean(fl > fh) + .5 * np.mean(fl == fh):.3f}"
              f"                       " + "   ".join(row), flush=True)
