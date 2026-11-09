"""KGi-DISS-I032 run 3 — scale-invariant H1b candidates (freeze AD3 + AD4).

Run 2 (pipeline_cert.py) is untouched and reported against E1-E8. This script
measures E9-E14 only:
  attenuation reading: gate and R3 x M1..M6 at the run-2 calibrated a (read
    from records/pipeline_cert_I032_calib.csv), B = 1000, seed base +40000;
  heterogeneity reading: a = 1, M2 layer, B = 500, seed base +50000 —
    composite R3+R4 (no gate), mixture gate+R4, mixture gate+R3 (feasibility),
    pure R3.
Statistics per replicate: H1a WMW (gatekeeper) -> frozen H1b (two-sided TOST,
delta_eq, criterion iii) | H1b-SI (kappa .25; sensitivities kappa 0, .40) |
H1b-SIc (kappa .25 on the above-median-drop half). Accuracy floor .70 applies
to every form. Output records/pipeline_cert_I032_run3.csv.
"""
import csv
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import market_generator as mg
import stats_v2 as sv

SEED = 132000
N_ARM, N_REC = 320, 360
FLOOR_ACC = 0.70
KAPPA = 0.25
KAPPA_SENS = (0.0, 0.40)
SHAPES = ["M1", "M2", "M3", "M4", "M5", "M6"]


def read_calib():
    a, r3rec = {}, {}
    with open(os.path.join(ROOT, "records", "pipeline_cert_I032_calib.csv")) as f:
        for row in csv.DictReader(f):
            a[row["shape"]] = float(row["a_star"])
            r3rec[row["shape"]] = float(row["r3_recovery_mean"])
    return a, r3rec


def r3_normalized_recovery(a, shape, rng, n=40000):
    """Scale-free criterion (iii): R3 HIGHxMOD ratio of cell means rec/drop."""
    lat = mg.simulate_latent("rival_au", n, "HIGH", rng)
    f, _, k = mg.measure(lat, shape, a, rng)
    mod = k & ~lat["resto_full"]
    return float(mg.recovery(f[mod]).mean() / mg.drops(f[mod]).mean())


def mix_latent(kind_a, kind_b, share_a, n, p2, rng):
    """Per-subject mixture: kind_a w.p. share_a, else kind_b. Both cohorts
    share the deterministic resto/rho index patterns, so row-wise selection
    is consistent."""
    la = mg.simulate_latent(kind_a, n, p2, rng)
    lb = mg.simulate_latent(kind_b, n, p2, rng)
    pick = rng.random(n) < share_a
    out = {}
    for key in la:
        va, vb = la[key], lb[key]
        if va.ndim == 2:
            out[key] = np.where(pick[:, None], va, vb)
        else:
            out[key] = np.where(pick, va, vb)
    out["is_a"] = pick
    return out


def theta_at(gen, n, shape, a, seed):
    rng = np.random.default_rng(seed)
    lh, ll = gen(n, "HIGH", rng), gen(n, "LOW", rng)
    fh, eh, kh = mg.measure(lh, shape, a, rng)
    fl, el, kl = mg.measure(ll, shape, a, rng)
    dh = mg.drops(fh[mg.screens(fh, eh, lh["acc1"], kh)])
    dl = mg.drops(fl[mg.screens(fl, el, ll["acc1"], kl)])
    m = min(len(dh), len(dl))
    perm = rng.permutation(m)
    return float((dh[:m] > dl[perm]).mean() + 0.5 * (dh[:m] == dl[perm]).mean())


def root_share(kind_a, kind_b, seed, n=20000):
    """Share of kind_a giving theta = .592 at a = 1 (M2). Returns
    (share or None, theta(share=0), theta(share=1))."""
    g = lambda s: (lambda nn, p2, rng: mix_latent(kind_a, kind_b, s, nn, p2, rng))
    t0 = theta_at(g(0.0), n, "M2", 1.0, seed)
    t1 = theta_at(g(1.0), n, "M2", 1.0, seed)
    lo_t, hi_t = min(t0, t1), max(t0, t1)
    if not (lo_t <= 0.592 <= hi_t):
        return None, t0, t1
    lo, hi = 0.0, 1.0
    inc = t1 > t0
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        th = theta_at(g(mid), n, "M2", 1.0, seed)
        if (th < 0.592) == inc:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), t0, t1


def evaluate(fh, eh, kh, lat_h, fl, el, kl, lat_l, s, recruit_all, r3rec, r3norm, cnt):
    mh = mg.screens(fh[s], eh[s], lat_h["acc1"][s], kh[s])
    ml = mg.screens(fl[s], el[s], lat_l["acc1"][s], kl[s])
    if not recruit_all:
        mh[N_ARM:] = False
        ml[N_ARM:] = False
    dh, dl = mg.drops(fh[s][mh]), mg.drops(fl[s][ml])
    rej, _ = sv.wmw_one_sided(dl, dh, sv.ALPHA_CONF)
    if not rej:
        return
    cnt["h1a"] += 1
    mod = mh & ~lat_h["resto_full"][s]
    fm = fh[s][mod]
    rec, drp = mg.recovery(fm), mg.drops(fm)
    acc_ok = lat_h["acc_late"][s][mod].mean() >= FLOOR_ACC
    deq, _ = sv.delta_eq_rule(mg.p1_sd(fm))
    tost_ok, _, _ = sv.h1b_tost_frozen(rec, deq)
    cnt["frozen"] += acc_ok and tost_ok and (deq < r3rec)
    c = rec - KAPPA * drp
    si_ok, _ = sv._signed_rank_less(c, sv.ALPHA_CONF)
    si_iii = KAPPA < r3norm
    cnt["si"] += acc_ok and si_ok and si_iii
    for kk in KAPPA_SENS:
        ok, _ = sv._signed_rank_less(rec - kk * drp, sv.ALPHA_CONF)
        cnt[f"si_k{kk}"] += acc_ok and ok and (kk < r3norm)
    upper = drp > np.median(drp)
    cu = c[upper]
    sic_ok, _ = sv._signed_rank_less(cu, sv.ALPHA_CONF)
    cnt["sic"] += acc_ok and sic_ok and si_iii


def run_cell(gen, shape, a, B, seed, recruit_all, r3rec, r3norm, batch=50):
    rng = np.random.default_rng(seed)
    keys = ["h1a", "frozen", "si", "sic"] + [f"si_k{k}" for k in KAPPA_SENS]
    cnt = {k: 0 for k in keys}
    done = 0
    while done < B:
        nrep = min(batch, B - done)
        lat_h = gen(nrep * N_REC, "HIGH", rng)
        lat_l = gen(nrep * N_REC, "LOW", rng)
        fh, eh, kh = mg.measure(lat_h, shape, a, rng)
        fl, el, kl = mg.measure(lat_l, shape, a, rng)
        for r in range(nrep):
            s = slice(r * N_REC, (r + 1) * N_REC)
            evaluate(fh, eh, kh, lat_h, fl, el, kl, lat_l, s, recruit_all,
                     r3rec, r3norm, cnt)
            done += 1
    return {k: v / B for k, v in cnt.items()}


def main():
    t0 = time.time()
    a_map, r3rec_map = read_calib()
    out = [["reading", "cell", "shape", "a", "share", "B", "r3_norm_recovery",
            "h1a_rate", "verdict_frozen", "verdict_SI_k.25", "verdict_SIc_k.25",
            "verdict_SI_k0", "verdict_SI_k.40"]]

    def row(reading, cell, shape, a, share, B, r3n, res):
        out.append([reading, cell, shape, f"{a:.4f}", share, B, f"{r3n:.3f}",
                    f"{res['h1a']:.4f}", f"{res['frozen']:.4f}", f"{res['si']:.4f}",
                    f"{res['sic']:.4f}", f"{res['si_k0.0']:.4f}",
                    f"{res['si_k0.4']:.4f}"])
        print(out[-1], f"[{time.time()-t0:.0f}s]", flush=True)

    print("== attenuation reading ==", flush=True)
    for j, shape in enumerate(SHAPES):
        a = a_map[shape]
        r3n = r3_normalized_recovery(a, shape, np.random.default_rng(SEED + 39000 + j))
        for i, kind in enumerate(["gate", "rival_au"]):
            gen = (lambda kk: (lambda n, p2, rng: mg.simulate_latent(kk, n, p2, rng)))(kind)
            res = run_cell(gen, shape, a, 1000, SEED + 40000 + 100 * i + j,
                           shape == "M6", r3rec_map[shape], r3n)
            row("attenuation", kind, shape, a, "", 1000, r3n, res)

    print("== heterogeneity reading (a = 1, M2) ==", flush=True)
    r3n1 = r3_normalized_recovery(1.0, "M2", np.random.default_rng(SEED + 49000))
    r3rec1 = float(np.mean(mg.recovery(
        mg.measure(mg.simulate_latent("rival_au", 40000, "HIGH",
                                      np.random.default_rng(SEED + 49001)),
                   "M2", 1.0, np.random.default_rng(SEED + 49002))[0])))
    specs = [("composite_R3+R4", "rival_au", "rival_us"),
             ("mixture_gate+R4", "gate", "rival_us"),
             ("mixture_gate+R3", "gate", "rival_au")]
    for k, (name, ka, kb) in enumerate(specs):
        share, t0_, t1_ = root_share(ka, kb, SEED + 48000 + k)
        if share is None:
            out.append(["heterogeneity", name, "M2", "1.0000", "INFEASIBLE", 0,
                        f"{r3n1:.3f}", f"theta(share=0)={t0_:.3f}",
                        f"theta(share=1)={t1_:.3f}", "", "", "", ""])
            print(out[-1], flush=True)
            continue
        gen = (lambda A, Bk, S: (lambda n, p2, rng: mix_latent(A, Bk, S, n, p2, rng)))(ka, kb, share)
        res = run_cell(gen, "M2", 1.0, 500, SEED + 50000 + k, False, r3rec1, r3n1)
        row("heterogeneity", name, "M2", 1.0, f"{share:.4f}", 500, r3n1, res)
    gen = lambda n, p2, rng: mg.simulate_latent("rival_au", n, p2, rng)
    res = run_cell(gen, "M2", 1.0, 500, SEED + 50010, False, r3rec1, r3n1)
    row("heterogeneity", "pure_R3", "M2", 1.0, "1.0", 500, r3n1, res)

    path = os.path.join(ROOT, "records", "pipeline_cert_I032_run3.csv")
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(out)
    print(f"done in {time.time()-t0:.0f}s -> {path}", flush=True)


if __name__ == "__main__":
    main()
