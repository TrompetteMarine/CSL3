"""POST-HOC EXPLORATION after the I032 close, part 2: is the P2-mean baseline the
defect? Not a certification; nothing frozen is altered; any candidate found here
must be frozen and certified (I033) before it can be proposed for the prereg.

Prompted by explore_h1b_anatomy.py Q1/Q2: under MODERATE the gate's latent trust
reaches ~21.7 at t=300 and stays flat through P3 (21.6 late), while the frozen
statistic rec = late-P3 - P2 mean reads -32.5 because the gate is still
collapsing during P2. Questions, stated before running:

 B1 latent    restoration response d3 = late-P3 - endP2 (endP2 = mean of the
              last 5 ratings before restoration, t = 280..300) for gate (all,
              by P3 regime), R3, R4.
 B2 measured  three H1b statistics, each gated by H1a and the .70 accuracy
              floor, one-sided Wilcoxon signed-rank at .005, kappa = .25:
                S0  certified H1b-SIc (P2-mean baseline, high-drop half)
                S1  end-baseline, all HIGH x MODERATE subjects:
                    median(d3 - kappa*drop) < 0
                S2  end-baseline, high-drop half (S1 conditioned like SIc)
              cells: gate and R3 at the certified attenuation a* = .0578 (M2)
              and at a = 1; no-gate composite R3+R4 (share .5595) and gate+R4
              mixture (share .5765) at a = 1. B = 200 per cell.
Seed base 134000. Output records/h1b_baseline_I032pc.txt.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import market_generator as mg
import pipeline_cert_run3 as r3

SEED = 134000
KAPPA = 0.25
OUT = []


def log(s=""):
    print(s, flush=True)
    OUT.append(s)


def end_p2(f):
    return f[:, 55:60].mean(axis=1)


def d3(f):
    return f[:, 75:90].mean(axis=1) - end_p2(f)


def b1():
    log("== B1 latent restoration response d3 = late-P3 - endP2 (MODERATE, HIGH arm, n=40000) ==")
    for kind in ("gate", "rival_au", "rival_us"):
        lat = mg.simulate_latent(kind, 40000, "HIGH", np.random.default_rng(SEED + 1),
                                 resto_mix=(1, 0))
        L = 100 * lat["ratings"].astype(float)
        dd = d3(L)
        line = (f"{kind:9s} endP2 {end_p2(L).mean():5.1f}  late-P3 {L[:, 75:90].mean():5.1f}"
                f"  d3 mean {dd.mean():+6.1f}  (frozen rec {mg.recovery(L).mean():+6.1f})")
        if kind == "gate":
            line += (f" | P3 HIGH d3 {dd[lat['reg3']].mean():+5.1f}, P3 LOW d3 "
                     f"{dd[~lat['reg3']].mean():+5.1f}")
        log(line)
    log()


def run_cell(gen, a, B, seed):
    rng = np.random.default_rng(seed)
    cnt = dict(h1a=0, S0=0, S1=0, S2=0)
    done, batch, N_ARM = 0, 50, 320
    while done < B:
        nrep = min(batch, B - done)
        lh, ll = gen(nrep * 360, "HIGH", rng), gen(nrep * 360, "LOW", rng)
        fh, eh, kh = mg.measure(lh, "M2", a, rng)
        fl, el, kl = mg.measure(ll, "M2", a, rng)
        for r in range(nrep):
            s = slice(r * 360, (r + 1) * 360)
            mh = mg.screens(fh[s], eh[s], lh["acc1"][s], kh[s]); mh[N_ARM:] = False
            ml = mg.screens(fl[s], el[s], ll["acc1"][s], kl[s]); ml[N_ARM:] = False
            rej, _ = r3.sv.wmw_one_sided(mg.drops(fl[s][ml]), mg.drops(fh[s][mh]), .005)
            done += 1
            if not rej:
                continue
            cnt["h1a"] += 1
            mod = mh & ~lh["resto_full"][s]
            fm = fh[s][mod]
            if lh["acc_late"][s][mod].mean() < .70:
                continue
            drp, rec, dd = mg.drops(fm), mg.recovery(fm), d3(fm)
            up = drp > np.median(drp)
            cnt["S0"] += r3.sv._signed_rank_less((rec - KAPPA * drp)[up], .005)[0]
            cnt["S1"] += r3.sv._signed_rank_less(dd - KAPPA * drp, .005)[0]
            cnt["S2"] += r3.sv._signed_rank_less((dd - KAPPA * drp)[up], .005)[0]
    return {k: v / B for k, v in cnt.items()}


def b2():
    log("== B2 measured verdict rates (gated by H1a + accuracy floor; B = 200) ==")
    g = lambda n, p2, rng: mg.simulate_latent("gate", n, p2, rng)
    rv = lambda n, p2, rng: mg.simulate_latent("rival_au", n, p2, rng)
    comp = lambda n, p2, rng: r3.mix_latent("rival_au", "rival_us", .5595, n, p2, rng)
    gr4 = lambda n, p2, rng: r3.mix_latent("gate", "rival_us", .5765, n, p2, rng)
    cells = [("gate, a*=.0578", g, .0578, "power"), ("R3, a*=.0578", rv, .0578, "false+"),
             ("gate, a=1", g, 1.0, "power"), ("R3, a=1", rv, 1.0, "false+"),
             ("composite R3+R4, a=1", comp, 1.0, "false+"),
             ("gate+R4 mixture, a=1", gr4, 1.0, "power")]
    for i, (name, gen, a, kind) in enumerate(cells):
        res = run_cell(gen, a, 200, SEED + 100 + i)
        log(f"{name:24s} [{kind:6s}] H1a {res['h1a']:.3f} | S0 (certified SIc) {res['S0']:.3f}"
            f" | S1 end-baseline {res['S1']:.3f} | S2 end-baseline+high-drop {res['S2']:.3f}")
    log()


if __name__ == "__main__":
    b1()
    b2()
    with open(os.path.join(ROOT, "records", "h1b_baseline_I032pc.txt"), "w") as fh:
        fh.write("POST-HOC exploration part 2 (see script docstring)\n\n" + "\n".join(OUT) + "\n")
