"""KGi-DISS-I032 — gate G2: pipeline-vs-power-engine consistency.

Draws samples from the FROZEN I029 battery (analysis/power_free.py, untouched)
at the three frozen anchor cells (S1, S2, S6 x theta=.592 x N=320/arm) and runs
BOTH implementations of the one-sided WMW decision on the SAME draws:
power_free.wmw_reject (the engine) and stats_v2.wmw_one_sided (the pipeline).

Outputs records/g2_consistency.csv: per cell, rejection rate of each
implementation, per-sample decision agreement, and the frozen
records/power_free.csv reference value. Gate: pipeline rate within +/- .02 of
the frozen record AND per-sample agreement = 1.000 (identical statistic).
Seed 132500 (freeze I032). B = 2000.
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
sys.path.insert(0, HERE)

import power_free as pf          # frozen I029 engine
import stats_v2 as sv            # I032 pipeline modules

SEED = 132500
B = 2000
N = 320
CELLS = ["S1", "S2", "S6"]
THETA = 0.592


def frozen_reference():
    ref = {}
    with open(os.path.join(ROOT, "records", "power_free.csv")) as f:
        for row in csv.DictReader(f):
            if row["theta_label"] == "basis(.592)" and int(row["N_per_arm"]) == N:
                ref[row["shape"]] = (float(row["power_WMW"]), float(row["tau"]))
    return ref


def main():
    rng = np.random.default_rng(SEED)
    ref = frozen_reference()
    out = [("shape", "tau_frozen", "B", "N_per_arm", "rate_engine",
            "rate_pipeline", "agreement", "ref_power_WMW", "abs_dev_vs_record",
            "pass_tol_.02", "pass_agreement")]
    all_ok = True
    for shape in CELLS:
        ref_pw, tau = ref[shape]
        eng = pipe = agree = 0
        for _ in range(B):
            xl, xh = pf.draw_pair(shape, rng, N, tau)
            r_e = bool(pf.wmw_reject(xl, xh))
            r_p, _ = sv.wmw_one_sided(xl, xh, alpha=pf.ALPHA)
            eng += r_e
            pipe += r_p
            agree += (r_e == r_p)
        re_, rp_, ag_ = eng / B, pipe / B, agree / B
        dev = abs(rp_ - ref_pw)
        ok_tol = dev <= 0.02
        ok_ag = ag_ == 1.0
        all_ok &= ok_tol and ok_ag
        out.append((shape, f"{tau:.2f}", B, N, f"{re_:.4f}", f"{rp_:.4f}",
                    f"{ag_:.4f}", f"{ref_pw:.3f}", f"{dev:.4f}",
                    ok_tol, ok_ag))
        print(out[-1], flush=True)
    path = os.path.join(ROOT, "records", "g2_consistency.csv")
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(out)
    print(f"\nG2 {'PASS' if all_ok else 'FAIL'} -> {path}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
