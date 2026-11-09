"""Audit test: the real-data pipeline (pipeline.py) reads an export in the app's
exact format and recovers the per-participant statistics that the
certification computed directly from arrays (drop, recovery, d3, P1 SD,
late-P3 accuracy), applies the confirmatory-set filter, and runs end to end.
Also: the zero-movement screen (randomized slider starts) is exercised.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import market_generator as mg
import pipeline as P


def _header():
    from importlib import util
    spec = util.spec_from_file_location(
        "app", os.path.join(HERE, "..", "diss_bandit", "__init__.py"))
    src = open(spec.origin).read()
    start = src.index("EXPORT_HEADER = [")
    end = src.index("]", src.index("'ticket'")) + 1
    ns = {}
    exec(src[start:end], ns)
    return ns["EXPORT_HEADER"]


def build_export(path, n=120, seed=11):
    hdr = _header()
    rng = np.random.default_rng(seed)
    rows, truth = [], {}
    for arm in ("HIGH", "LOW"):
        lat = mg.simulate_latent("gate", n, arm, rng)
        f, e, _ = mg.measure(lat, "M2", 1.0, rng)
        for i in range(n):
            pid = f"{arm}{i}"
            resto = "FULL" if lat["resto_full"][i] else "MODERATE"
            cfg = "main_confirmatory" if i % 10 else "dose_45"
            acc = [lat["acc1"][i], lat["acc2"][i], lat["acc3"][i]]

            def mk(kind, vals):
                r = dict.fromkeys(hdr, "")
                r.update(row_type=kind, session="s", participant=pid,
                         cell_p2_regime=arm, restoration=resto, bot_kind="human",
                         config_name=cfg, **vals)
                return [r[h] for h in hdr]

            for t in range(1, 451):
                ph = (t - 1) // 150
                a = lat["acc_late"][i] if t > 375 else acc[ph]
                k = (t - 1) % 150 if t <= 375 else t - 376
                good = int((k + 1) * a) - int(k * a)
                rows.append(mk("trial", dict(t=t, block=ph + 1, choice_good=good,
                                             reward=int(rng.random() < .5), bonus=0,
                                             peer_reward=0, peer_rate=0.5, rt_ms=600)))
            for k in range(90):
                rows.append(mk("rating", dict(t=5 * (k + 1), fairness=f[i, k],
                                              entitlement=e[i, k], rt_ms=900,
                                              fairness_init=-5, entitlement_init=-5)))
            fm = f[i:i + 1]
            truth[pid] = dict(cfg=cfg, drop=mg.drops(fm)[0], rec=mg.recovery(fm)[0],
                              d3=fm[0, 75:90].mean() - fm[0, 55:60].mean(),
                              p1sd=mg.p1_sd(fm)[0], acc_late=lat["acc_late"][i])
    pd.DataFrame(rows, columns=hdr).to_csv(path, index=False)
    return truth


def test_pipeline_recovers_certification_statistics(tmp_path):
    path = tmp_path / "export.csv"
    truth = build_export(path)
    trials, ratings, funnel = P.load(path)
    pp = P.per_participant(trials, ratings).set_index("participant")
    for pid, tv in truth.items():
        r = pp.loc[pid]
        assert abs(r.drop_p2 - tv["drop"]) < 1e-9
        assert abs(r.recovery - tv["rec"]) < 1e-9
        assert abs(r.d3 - tv["d3"]) < 1e-9
        assert abs(r.p1_sd - tv["p1sd"]) < 1e-9
        assert abs(r.acc_late - tv["acc_late"]) < 0.02      # pattern rounding only
        assert r.config_name == tv["cfg"]


def test_pipeline_runs_end_to_end_and_filters_modules(tmp_path):
    path = tmp_path / "export.csv"
    build_export(path)
    out = tmp_path / "report.md"
    P.run(str(path), str(out))
    txt = out.read_text()
    assert "Confirmatory analysis set: 216 of 240" in txt     # dose_45 rows excluded
    assert "## H1a (confirmatory)" in txt and "SIc (certified candidate)" in txt


def test_zero_movement_screen():
    rng = np.random.default_rng(0)
    rows = []
    for pid, kind in (("mover", "m"), ("never", "n"), ("partial", "p")):
        for k in range(90):
            fi, ei = 5 * int(rng.integers(0, 21)), 5 * int(rng.integers(0, 21))
            if kind == "n" or (kind == "p" and k % 2 == 0):
                fv, ev = fi, ei
            else:
                fv, ev = 5 * int(rng.integers(0, 21)), 5 * int(rng.integers(0, 21))
            rows.append(dict(participant=pid, t=5 * (k + 1), fairness=fv,
                             entitlement=ev, fairness_init=fi, entitlement_init=ei))
    ratings = pd.DataFrame(rows)
    trials = pd.DataFrame([dict(participant=p, t=t, choice_good=1, rt_ms=600,
                                bot_kind="human", phase=P.PHASE_OF(t))
                           for p in ("mover", "never", "partial") for t in range(1, 451)])
    drop, _ = P.apply_exclusions(trials, ratings, pd.DataFrame())
    assert drop == {"never"}
    assert ratings[ratings.participant == "never"].fairness.var() > 100   # old rule would keep
