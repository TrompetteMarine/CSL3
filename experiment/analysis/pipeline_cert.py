"""KGi-DISS-I032 — synthetic pipeline certification (agenda item A).

Runs the preregistered analysis pipeline end-to-end on market-skinned
synthetic cohorts from the four frozen generators, under the measurement
battery of 00_freeze_I032.yaml (+ addenda AD1/AD2). Expected outcomes E1-E8
are frozen in that file; this script only measures them.

Phases:
  1. calibration: per measurement shape, root-find the attenuation a so the
     GATE generator's Mann-Whitney theta = .592 on a 60k/arm draw; record the
     R3 and gate predicted P2->late-P3 recoveries and late-P3 accuracies at
     that a (criterion-iii constants and floor sanity).
  2. H1a/verdict Monte Carlo: B=1000 replicates per (generator x shape) cell;
     fresh latent draws, paired across shapes within a generator (stated);
     full pipeline per replicate: screens -> H1a WMW (.005 one-sided, Welch
     co-reported) -> gatekept H1b (frozen TOST and the AD-frozen repair
     candidate) -> verdict.
  3. dose module (B=500): gate at chi=.6 and chi=.4, R3; cells mu_ref
     .45/.55/.65 (n=90/90/320), M2 measurement at its calibrated a;
     second-difference studentized centered-bootstrap test (inner B=2000).
  4. framing module (B=500): framing arm (n=90, HIGH x MODERATE, fixed-rate
     instructions) vs the same generator's LOW arm (n=320); one-sided WMW .05.

Outputs records/pipeline_cert_I032.csv (+ _calib.csv); seeds from the freeze.
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
B_H1A = 1000
B_MOD = 500
N_ARM = 320
N_REC = 360            # recruited per arm (M6 cells analyze survivors)
BATCH = 50             # replicates per latent batch
FLOOR_ACC = 0.70
SHAPES = ["M1", "M2", "M3", "M4", "M5", "M6"]
GEN_SHAPES = {
    "gate": SHAPES + ["M2anchor"],
    "rival_au": SHAPES,
    "rival": ["M2", "M6"],
    "rival_us": ["M2", "M6"],
}


def gen_arm(kind, nrep, n, p2, rng, **kw):
    """nrep stacked replicates of one arm; returns latent dict of width nrep*n."""
    return mg.simulate_latent(kind, nrep * n, p2, rng, **kw)


def slice_rep(lat, r, n):
    s = slice(r * n, (r + 1) * n)
    return {k: v[s] for k, v in lat.items()}


def apply_shape(lat, shape, a, rng):
    if shape == "M2anchor":
        return mg.measure_anchored(lat, a, rng)
    return mg.measure(lat, shape, a, rng)


# -------------------------------------------------------------- 1. calibration
def theta_pooled(dh, dl, rng, reps=3):
    m = min(len(dh), len(dl))
    vals = []
    for _ in range(reps):
        perm = rng.permutation(m)
        gt = (dh[:m] > dl[perm]).mean()
        eq = (dh[:m] == dl[perm]).mean()
        vals.append(gt + 0.5 * eq)
    return float(np.mean(vals))


def calibrate(shape, lat_h, lat_l, rng_meas_seed):
    lo, hi = 0.01, 1.5
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        rng = np.random.default_rng(rng_meas_seed)   # fixed draws across bisection
        fh, _, kh = apply_shape(lat_h, shape, mid, rng)
        fl, _, kl = apply_shape(lat_l, shape, mid, rng)
        dh, dl = mg.drops(fh[kh]), mg.drops(fl[kl])
        th = theta_pooled(dh, dl, np.random.default_rng(rng_meas_seed + 1))
        if th > 0.592:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def run_calibration():
    rng = np.random.default_rng(SEED + 1)
    lat_h = mg.simulate_latent("gate", 60000, "HIGH", rng)
    lat_l = mg.simulate_latent("gate", 60000, "LOW", rng)
    lat_r3 = mg.simulate_latent("rival_au", 40000, "HIGH", rng)
    rows = [("shape", "a_star", "theta_check", "r3_recovery_mean",
             "gate_recovery_mean", "gate_acclate_mean", "r3_acclate_mean")]
    a_map, r3rec_map = {}, {}
    for i, shape in enumerate(SHAPES + ["M2anchor"]):
        a = calibrate(shape, lat_h, lat_l, SEED + 100 + i)
        rngv = np.random.default_rng(SEED + 200 + i)
        fh, _, kh = apply_shape(lat_h, shape, a, rngv)
        fl, _, kl = apply_shape(lat_l, shape, a, rngv)
        th = theta_pooled(mg.drops(fh[kh]), mg.drops(fl[kl]),
                          np.random.default_rng(SEED + 300 + i))
        f3, _, k3 = apply_shape(lat_r3, shape, a, rngv)
        mod3 = k3 & ~lat_r3["resto_full"]
        modh = kh & ~lat_h["resto_full"]
        r3rec = float(mg.recovery(f3[mod3]).mean())
        grec = float(mg.recovery(fh[modh]).mean())
        gacc = float(lat_h["acc_late"][modh].mean())
        r3acc = float(lat_r3["acc_late"][mod3].mean())
        a_map[shape], r3rec_map[shape] = a, r3rec
        rows.append((shape, f"{a:.4f}", f"{th:.4f}", f"{r3rec:.2f}",
                     f"{grec:.2f}", f"{gacc:.4f}", f"{r3acc:.4f}"))
        print(rows[-1], flush=True)
    with open(os.path.join(ROOT, "records", "pipeline_cert_I032_calib.csv"),
              "w", newline="") as f:
        csv.writer(f).writerows(rows)
    return a_map, r3rec_map


# ------------------------------------------------------- 2. H1a / verdict MC
def verdict_cell(kind, shape, a, r3rec, seed):
    rng = np.random.default_rng(seed)
    cnt = dict(h1a=0, welch=0, tost=0, nonsup=0, acc=0, r3x=0,
               verdict_frozen=0, verdict_repair=0)
    th_sum = deq_sum = sig_sum = 0.0
    done = 0
    while done < B_H1A:
        nrep = min(BATCH, B_H1A - done)
        lat_h = gen_arm(kind, nrep, N_REC, "HIGH", rng)
        lat_l = gen_arm(kind, nrep, N_REC, "LOW", rng)
        fh, eh, kh = apply_shape(lat_h, shape, a, rng)
        fl, el, kl = apply_shape(lat_l, shape, a, rng)
        okh = mg.screens(fh, eh, lat_h["acc1"], kh)
        okl = mg.screens(fl, el, lat_l["acc1"], kl)
        for r in range(nrep):
            s = slice(r * N_REC, (r + 1) * N_REC)
            mh, ml = okh[s].copy(), okl[s].copy()
            if shape != "M6":                      # recruit 320 (first 320 rows)
                mh[N_ARM:] = False
                ml[N_ARM:] = False
            dh = mg.drops(fh[s][mh])
            dl = mg.drops(fl[s][ml])
            rej, _ = sv.wmw_one_sided(dl, dh, sv.ALPHA_CONF)
            wrej, _ = sv.welch_one_sided(dl, dh, sv.ALPHA_CONF)
            cnt["welch"] += wrej
            th_sum += sv.theta_hat(dl, dh)
            if rej:
                cnt["h1a"] += 1
                mod = mh & ~lat_h["resto_full"][s]
                rec = mg.recovery(fh[s][mod])
                deq, sig = sv.delta_eq_rule(mg.p1_sd(fh[s][mod]))
                deq_sum += deq
                sig_sum += sig
                acc_ok = lat_h["acc_late"][s][mod].mean() >= FLOOR_ACC
                tost_ok, _, _ = sv.h1b_tost_frozen(rec, deq)
                ns_ok, _ = sv.h1b_nonsuperiority(rec, deq)
                r3_ok = deq < r3rec
                cnt["acc"] += acc_ok
                cnt["tost"] += tost_ok
                cnt["nonsup"] += ns_ok
                cnt["r3x"] += r3_ok
                cnt["verdict_frozen"] += (acc_ok and tost_ok and r3_ok)
                cnt["verdict_repair"] += (acc_ok and ns_ok and r3_ok)
            done += 1
    B = B_H1A
    nh1a = max(cnt["h1a"], 1)
    return dict(generator=kind, shape=shape, B=B, a=f"{a:.4f}",
                h1a_rate=cnt["h1a"] / B, welch_rate=cnt["welch"] / B,
                theta_mean=th_sum / B,
                acc_rate_gated=cnt["acc"] / nh1a,
                tost_rate_gated=cnt["tost"] / nh1a,
                nonsup_rate_gated=cnt["nonsup"] / nh1a,
                r3x_rate_gated=cnt["r3x"] / nh1a,
                verdict_frozen_rate=cnt["verdict_frozen"] / B,
                verdict_repair_rate=cnt["verdict_repair"] / B,
                deq_mean=deq_sum / nh1a, sigma_r_mean=sig_sum / nh1a)


# ------------------------------------------------------------- 3. dose module
def dose_cell(kind, chi, a, seed):
    rng = np.random.default_rng(seed)
    rej = 0
    c_sum = 0.0
    for b in range(B_MOD):
        lat45 = mg.simulate_latent(kind, 90, "HIGH", rng, mu_ref=0.45, chi=chi)
        lat55 = mg.simulate_latent(kind, 90, "HIGH", rng, mu_ref=0.55, chi=chi)
        lat65 = mg.simulate_latent(kind, N_ARM, "HIGH", rng, mu_ref=0.65, chi=chi)
        cells = []
        for lat in (lat45, lat55, lat65):
            f, e, k = mg.measure(lat, "M2", a, rng)
            ok = mg.screens(f, e, lat["acc1"], k)
            cells.append(mg.drops(f[ok]))
        r, C, t, p = sv.dose_second_difference(*cells, B=2000,
                                               seed=int(rng.integers(1 << 31)))
        rej += r
        c_sum += C
    return dict(generator=kind, chi=chi, B=B_MOD, reject_rate=rej / B_MOD,
                C_mean=c_sum / B_MOD)


# ---------------------------------------------------------- 4. framing module
def framing_cell(kind, a, seed):
    rng = np.random.default_rng(seed)
    rej = 0
    for b in range(B_MOD):
        latf = mg.simulate_latent(kind, 90, "HIGH", rng,
                                  framing=True, resto_mix=(1, 0))
        latl = mg.simulate_latent(kind, N_ARM, "LOW", rng)
        ff, ef, kf = mg.measure(latf, "M2", a, rng)
        fl, el, kl = mg.measure(latl, "M2", a, rng)
        okf = mg.screens(ff, ef, latf["acc1"], kf)
        okl = mg.screens(fl, el, latl["acc1"], kl)
        r, _ = sv.framing_test(mg.drops(ff[okf]), mg.drops(fl[okl]))
        rej += r
    return dict(generator=kind, B=B_MOD, reject_rate=rej / B_MOD)


def main():
    t0 = time.time()
    print("== calibration ==", flush=True)
    a_map, r3rec_map = run_calibration()

    rows = []
    print("== H1a / verdict MC ==", flush=True)
    for kind, shapes in GEN_SHAPES.items():
        for j, shape in enumerate(shapes):
            cell_seed = SEED + 10000 + 100 * list(GEN_SHAPES).index(kind) + j
            res = verdict_cell(kind, shape, a_map[shape], r3rec_map[shape],
                               cell_seed)
            rows.append(res)
            print({k: (f"{v:.4f}" if isinstance(v, float) else v)
                   for k, v in res.items()}, f"[{time.time()-t0:.0f}s]",
                  flush=True)

    print("== dose module ==", flush=True)
    dose_rows = [dose_cell("gate", 0.6, a_map["M2"], SEED + 20000),
                 dose_cell("gate", 0.4, a_map["M2"], SEED + 20001),
                 dose_cell("rival_au", 0.6, a_map["M2"], SEED + 20002)]
    for d in dose_rows:
        print(d, flush=True)

    print("== framing module ==", flush=True)
    fr_rows = [framing_cell("gate", a_map["M2"], SEED + 30000),
               framing_cell("rival_us", a_map["M2"], SEED + 30001)]
    for d in fr_rows:
        print(d, flush=True)

    out = os.path.join(ROOT, "records", "pipeline_cert_I032.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section"] + list(rows[0].keys()))
        for r in rows:
            w.writerow(["h1a_verdict"] + list(r.values()))
        w.writerow(["section"] + list(dose_rows[0].keys()))
        for r in dose_rows:
            w.writerow(["dose"] + list(r.values()))
        w.writerow(["section"] + list(fr_rows[0].keys()))
        for r in fr_rows:
            w.writerow(["framing"] + list(r.values()))
    print(f"done in {time.time()-t0:.0f}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
