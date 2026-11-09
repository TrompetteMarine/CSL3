#!/usr/bin/env python3
"""I032 frozen addendum S7 to the I029 power battery (00_freeze_I032.yaml).

Suspicion contamination is ASYMMETRIC (differential believability of the HIGH
display) and therefore a LEVEL threat that no S1-S6 shape represents (each of
those applies one mechanism to both arms, with effects injected as shifts).
This script adds the S7 cells WITHOUT touching analysis/power_free.py or
records/power_free.csv (frozen I029): it imports the frozen machinery, uses its
own seed (132400), and writes records/power_free_s7.csv.

Null-level cells (no true effect; S3 attention-mixture base): a fraction q_H of
the HIGH arm only carries a suspicion drop-inflation of s points; the blind
suspicion-probe exclusion removes each contaminated subject with probability
pi_probe. Grid q_H x s x pi_probe = {.05,.10,.20} x {5,10,15} x {0,.5,.8},
N = 320/arm, B = 2000, one-sided WMW at alpha .005. Output per cell: realized
level. The design-tolerance statement = the maximum residual contamination load
q_H * s * (1 - pi_probe) keeping level <= .005 (+2 MC SE).

One power cell for completeness: theta = .592 shift with SYMMETRIC suspicion
(q = .10 both arms, s = 10, pi_probe = .5).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import power_free as pf

SEED = 132400
B = 2000
N = 320
GRID_Q = [0.05, 0.10, 0.20]
GRID_S = [5.0, 10.0, 15.0]
GRID_PI = [0.0, 0.5, 0.8]


def draw_s3(rng, n, tau):
    """S3 base arm: 80% responsive N(25+tau,15) + 20% non-responders N(0,8)."""
    resp = rng.random(n) >= 0.20
    return np.where(resp, rng.normal(25 + tau, 15, n), rng.normal(0, 8, n))


def contaminate(x, rng, q, s, pi_probe):
    """Suspicion: fraction q gets +s drop inflation; probe removes each
    contaminated subject w.p. pi_probe (blind exclusion)."""
    sus = rng.random(len(x)) < q
    x = x + s * sus
    keep = ~(sus & (rng.random(len(x)) < pi_probe))
    return x[keep]


def main():
    rng = np.random.default_rng(SEED)
    rows = [("cell", "q_H", "s", "pi_probe", "load_qs_1mpi", "N_per_arm", "B",
             "level_or_power_WMW")]
    print("S7 null-level grid (tau=0, asymmetric contamination of HIGH only)")
    for q in GRID_Q:
        for s in GRID_S:
            for pi in GRID_PI:
                rej = 0
                for _ in range(B):
                    xl = draw_s3(rng, N, 0.0)                      # LOW: clean
                    xh = contaminate(draw_s3(rng, N, 0.0), rng, q, s, pi)
                    rej += pf.wmw_reject(xl, xh)
                lvl = rej / B
                load = q * s * (1 - pi)
                rows.append(("level", q, s, pi, f"{load:.2f}", N, B, f"{lvl:.4f}"))
                print(rows[-1], flush=True)
    # symmetric-suspicion power cell at the design basis
    tau = pf.calibrate_tau("S3", 0.592, np.random.default_rng(SEED + 1))
    rej = 0
    for _ in range(B):
        xl = contaminate(draw_s3(rng, N, 0.0), rng, 0.10, 10.0, 0.5)
        xh = contaminate(draw_s3(rng, N, tau), rng, 0.10, 10.0, 0.5)
        rej += pf.wmw_reject(xl, xh)
    rows.append(("power_sym", 0.10, 10.0, 0.5, "sym", N, B, f"{rej/B:.4f}"))
    print(rows[-1])
    out = os.path.join(HERE, "..", "records", "power_free_s7.csv")
    with open(out, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    # tolerance statement
    thr = 0.005 + 2 * np.sqrt(0.005 * 0.995 / B)
    bad = [(float(r[4]), float(r[7])) for r in rows[1:] if r[0] == "level"]
    ok_loads = sorted(l for l, v in bad if v <= thr)
    exceed = sorted((l, v) for l, v in bad if v > thr)
    print(f"\nlevel threshold (alpha + 2 MC SE) = {thr:.4f}")
    print(f"max load with level <= threshold: {ok_loads[-1] if ok_loads else None}")
    if exceed:
        print(f"smallest load exceeding threshold: {exceed[0]}")
    print(f"record -> {os.path.abspath(out)}")


if __name__ == "__main__":
    main()
