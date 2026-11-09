"""POST-HOC EXPLORATION after the I032 close: anatomy of the frozen H1b failure.

Not a certification. No frozen record is altered. Every number here is a
diagnostic for an author decision, labelled post-hoc. Questions, stated before
running (committed with this script):

 Q1 mechanism   Under MODERATE restoration, does the gate's trust keep falling
                in P3 because aspiration A stays above the critical A*? Split by
                the P3 reference regime, which is iid in the design.
 Q2 baseline    The frozen statistic is rec = late-P3 - P2 mean. How much of it
                is the P2 decline still unfinished at the P2 midpoint, and how
                much is a genuine P3 response?
 Q3 scale       Frozen H1b verdict rate for the gate and for R3 across the
                attenuation a in [.05, 1]. Conjecture: zero at every a, because
                the band must sit between the gate's movement and the rival's,
                which needs |rec_gate| < rec_R3.
 Q4 route       Does the failure depend on HOW the effect is deflated to the
                design basis theta = .592? Four routes: attenuation a; rating
                noise sigma_eps (a = 1); anchoring chi (a = 1); rigidity rho
                (single value, a = 1). For each: frozen H1b, H1b-SI and H1b-SIc
                verdict rates for the gate (power) and for R3 (false positives).
 Q5 aggregation In the full-scale R3+R4 composite (no gate), decompose the
                HIGH x MODERATE recovery distribution by type and show why a
                pooled two-sided equivalence test passes.

Seed base 133000. Output records/h1b_anatomy_I032pc.txt (+ .csv for Q3/Q4).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import market_generator as mg
import pipeline_cert_run3 as r3   # certified run-3 test machinery, reused unchanged

SEED = 133000
OUT = []


def log(s=""):
    print(s, flush=True)
    OUT.append(s)


def trust(lat):
    return 100 * lat["ratings"].astype(float)


def gen_factory(kind, chi=mg.CHI_FROZEN, rho=None):
    return lambda n, p2, rng: mg.simulate_latent(kind, n, p2, rng, chi=chi,
                                                 rho_override=rho)


# ------------------------------------------------------------------ Q1 + Q2
def q1_q2():
    log("== Q1/Q2 latent anatomy, HIGH P2 arm, MODERATE only, n = 40000 ==")
    for kind in ("gate", "rival_au", "rival_us"):
        rng = np.random.default_rng(SEED + 1)
        lat = mg.simulate_latent(kind, 40000, "HIGH", rng, resto_mix=(1, 0))
        L = trust(lat)
        P1, P2 = L[:, 0:30].mean(1), L[:, 30:60].mean(1)
        lP2, lP3 = L[:, 45:60].mean(1), L[:, 75:90].mean(1)
        rec = lP3 - P2
        log(f"{kind:9s} P1 {P1.mean():5.1f}  P2 mean {P2.mean():5.1f}  late-P2 {lP2.mean():5.1f}"
            f"  late-P3 {lP3.mean():5.1f}  | rec {rec.mean():+6.1f} = unfinished-P2 "
            f"{(lP2 - P2).mean():+6.1f} + P3-response {(lP3 - lP2).mean():+6.1f}")
        series = " ".join(f"{L[:, k].mean():5.1f}" for k in range(59, 90, 6))
        log(f"          trust at t=300,330,...,450: {series}")
        if kind == "gate":
            A = lat["ent"].astype(float)
            mu = lat["acc3"] * .45 + (1 - lat["acc3"]) * .35
            astar = .3 + .25 * mu / (1 - mu)
            aL = A[:, 75:90].mean(1)
            for name, m in (("all", np.ones(len(rec), bool)),
                            ("P3 regime HIGH", lat["reg3"]),
                            ("P3 regime LOW", ~lat["reg3"])):
                log(f"   {name:15s} n={m.sum():5d}  late-P3 A {aL[m].mean():.3f} vs A* "
                    f"{astar[m].mean():.3f}  share A>A* {np.mean(aL[m] > astar[m]):.3f}  "
                    f"rec {rec[m].mean():+6.1f}  P3-response {(lP3 - lP2)[m].mean():+6.1f}")
            for r in (.002, .02):
                m = lat["rho"] == r
                log(f"   rho={r:<5}          rec {rec[m].mean():+6.1f}  P3-response "
                    f"{(lP3 - lP2)[m].mean():+6.1f}  share A>A* {np.mean(aL[m] > astar[m]):.3f}")
    log()


# ------------------------------------------------------------------- Q3
def r3_constants(gen_r3, shape, a, seed, n=40000):
    rng = np.random.default_rng(seed)
    lat = gen_r3(n, "HIGH", rng)
    f, _, k = mg.measure(lat, shape, a, rng)
    mod = k & ~lat["resto_full"]
    rec, drp = mg.recovery(f[mod]), mg.drops(f[mod])
    return float(rec.mean()), float(rec.mean() / drp.mean())


def measured_recs(gen, shape, a, seed, n=40000):
    rng = np.random.default_rng(seed)
    lat = gen(n, "HIGH", rng)
    f, _, k = mg.measure(lat, shape, a, rng)
    mod = k & ~lat["resto_full"]
    deq, _ = r3.sv.delta_eq_rule(mg.p1_sd(f[mod]))
    rec = mg.recovery(f[mod])
    return float(np.median(rec)), deq, float(np.mean(np.abs(rec) < deq))


def q3(rows):
    log("== Q3 frozen H1b across attenuation a (M2 noise; B = 200 per cell) ==")
    g, rv = gen_factory("gate"), gen_factory("rival_au")
    for j, a in enumerate((.05, .1, .2, .3, .45, .6, .8, 1.0)):
        r3rec, r3n = r3_constants(rv, "M2", a, SEED + 300 + j)
        mg_med, deq, inside = measured_recs(g, "M2", a, SEED + 320 + j)
        rg = r3.run_cell(g, "M2", a, 200, SEED + 340 + j, False, r3rec, r3n)
        rr = r3.run_cell(rv, "M2", a, 200, SEED + 360 + j, False, r3rec, r3n)
        feas = abs(mg_med) < deq < r3rec
        log(f"a={a:<5} gate median rec {mg_med:+6.1f} (share inside band {inside:.2f}) | "
            f"delta_eq {deq:4.1f} | R3 mean rec {r3rec:+6.1f} | band between them: "
            f"{'yes' if feas else 'no '} | frozen verdict gate {rg['frozen']:.3f} "
            f"R3 {rr['frozen']:.3f} | SIc gate {rg['sic']:.3f} R3 {rr['sic']:.3f}")
        rows.append(["Q3", "attenuation", f"a={a}", f"band_between={feas}",
                     f"{mg_med:.2f}", f"{deq:.2f}", f"{r3rec:.2f}",
                     rg["h1a"], rg["frozen"], rg["si"], rg["sic"],
                     rr["h1a"], rr["frozen"], rr["si"], rr["sic"]])
    log()


# ------------------------------------------------------------------- Q4
def bisect(f, lo, hi, iters=14):
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None, flo, fhi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if fm * flo > 0:
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi), None, None


def q4(rows):
    log("== Q4 routes to the design basis theta = .592 (B = 300 per cell) ==")
    routes = []
    # attenuation (certified a* for M2)
    routes.append(("attenuation a", dict(a=0.0578, sig=10.0, chi=.6, rho=None)))
    # noise
    def th_noise(s):
        mg.SIG_EPS = s
        t = r3.theta_at(gen_factory("gate"), 20000, "M2", 1.0, SEED + 400)
        mg.SIG_EPS = 10.0
        return t - .592
    s_star, *_ = bisect(th_noise, 10.0, 400.0)
    routes.append(("noise sigma_eps", dict(a=1.0, sig=s_star, chi=.6, rho=None)))
    # anchoring chi
    th_chi = lambda c: r3.theta_at(gen_factory("gate", chi=c), 20000, "M2", 1.0,
                                   SEED + 401) - .592
    c_star, *_ = bisect(th_chi, 0.0, 0.6)
    routes.append(("anchoring chi", dict(a=1.0, sig=10.0, chi=c_star, rho=None)))
    # rigidity rho
    th_rho = lambda r: r3.theta_at(gen_factory("gate", rho=r), 20000, "M2", 1.0,
                                   SEED + 402) - .592
    r_star, f0, f1 = bisect(th_rho, 0.0002, 0.05)
    routes.append(("rigidity rho", dict(a=1.0, sig=10.0, chi=.6, rho=r_star,
                                        endpoints=(f0, f1))))
    for i, (name, p) in enumerate(routes):
        if (name == "noise sigma_eps" and p["sig"] is None) or \
           (name == "anchoring chi" and p["chi"] is None) or \
           (name == "rigidity rho" and p["rho"] is None):
            log(f"{name:16s} UNREACHABLE: theta-.592 at endpoints {p.get('endpoints')}")
            rows.append(["Q4", name, "UNREACHABLE"])
            continue
        mg.SIG_EPS = p["sig"]
        g = gen_factory("gate", chi=p["chi"], rho=p["rho"])
        rv = gen_factory("rival_au", chi=p["chi"], rho=p["rho"])
        th = r3.theta_at(g, 20000, "M2", p["a"], SEED + 410 + i)
        r3rec, r3n = r3_constants(rv, "M2", p["a"], SEED + 420 + i)
        gmed, deq, inside = measured_recs(g, "M2", p["a"], SEED + 430 + i)
        rg = r3.run_cell(g, "M2", p["a"], 300, SEED + 440 + i, False, r3rec, r3n)
        rr = r3.run_cell(rv, "M2", p["a"], 300, SEED + 450 + i, False, r3rec, r3n)
        mg.SIG_EPS = 10.0
        par = (f"a={p['a']:.4f} sigma={p['sig']:.1f} chi={p['chi']:.3f} "
               f"rho={'mix' if p['rho'] is None else round(p['rho'], 5)}")
        log(f"{name:16s} {par}  theta {th:.3f}")
        log(f"   gate median rec {gmed:+6.1f} | delta_eq {deq:5.1f} | R3 rec {r3rec:+6.1f}"
            f" | R3 rec/drop {r3n:.2f} | H1a gate {rg['h1a']:.3f} R3 {rr['h1a']:.3f}")
        log(f"   verdict gate: frozen {rg['frozen']:.3f}  SI {rg['si']:.3f}  SIc {rg['sic']:.3f}"
            f"   |  R3: frozen {rr['frozen']:.3f}  SI {rr['si']:.3f}  SIc {rr['sic']:.3f}")
        rows.append(["Q4", name, par, f"{th:.4f}", f"{gmed:.2f}", f"{deq:.2f}",
                     f"{r3rec:.2f}", rg["h1a"], rg["frozen"], rg["si"], rg["sic"],
                     rr["h1a"], rr["frozen"], rr["si"], rr["sic"]])
    log()


# ------------------------------------------------------------------- Q5
def q5():
    log("== Q5 the no-gate composite (R3 share .5595, a = 1, M2), HIGH x MODERATE ==")
    rng = np.random.default_rng(SEED + 500)
    lat = r3.mix_latent("rival_au", "rival_us", .5595, 60000, "HIGH", rng)
    f, e, k = mg.measure(lat, "M2", 1.0, rng)
    ok = mg.screens(f, e, lat["acc1"], k) & ~lat["resto_full"]
    rec, drp, isr3 = mg.recovery(f[ok]), mg.drops(f[ok]), lat["is_a"][ok]
    deq, _ = r3.sv.delta_eq_rule(mg.p1_sd(f[ok]))
    for name, m in (("R3 types", isr3), ("R4 types", ~isr3), ("pooled", np.ones(len(rec), bool))):
        log(f"{name:9s} share {m.mean():.3f}  drop mean {drp[m].mean():6.1f}  rec mean "
            f"{rec[m].mean():+6.1f}  rec median {np.median(rec[m]):+6.1f}  "
            f"inside +/-{deq:.1f}: {np.mean(np.abs(rec[m]) < deq):.3f}")
    hi = drp > np.median(drp)
    log(f"above-median-drop half: R3 share {isr3[hi].mean():.3f}; its rec median "
        f"{np.median(rec[hi]):+6.1f} (H1b-SIc conditions here)")
    log()


def main():
    rows = [["q", "cell", "a_or_params", "theta_or_gmed", "gate_med_rec", "delta_eq",
             "r3_rec", "gate_h1a", "gate_frozen", "gate_si", "gate_sic",
             "r3_h1a", "r3_frozen", "r3_si", "r3_sic"]]
    q1_q2()
    q5()
    q3(rows)
    q4(rows)
    with open(os.path.join(ROOT, "records", "h1b_anatomy_I032pc.txt"), "w") as fh:
        fh.write("POST-HOC exploration after I032 close (see script docstring)\n\n")
        fh.write("\n".join(OUT) + "\n")
    with open(os.path.join(ROOT, "records", "h1b_anatomy_I032pc.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(rows)


if __name__ == "__main__":
    main()
