"""
Frozen analysis pipeline for task v3, market skin — v2 (KGi-DISS-I032;
supersedes the I006 build, which tested H1 by two-sided Welch and predates the
I025 gatekeeping and the I029 distribution-free decisions).

Implements, against the oTree custom export of diss_bandit:
  preregistered exclusions (incl. the pilot-calibrated suspicion-probe hook);
  H1a (confirmatory): one-sided tie-corrected WMW on the P1->P2 fairness drop,
    HIGH vs LOW P2 regime, alpha = .005, theta-hat + Hodges-Lehmann reported,
    studentized permutation Welch co-reported;
  H1b (co-confirmatory, tested ONLY if H1a rejects): accuracy floor AND the
    rank equivalence machinery of stats_v2 (frozen two-sided TOST and the
    I032 one-sided non-superiority form are BOTH computed and labeled; which
    is confirmatory is fixed by the preregistration text in force) AND the
    delta_eq < R3-predicted-recovery exclusion check;
  H2 timescale decoupling; H3 recovery threshold; H4 increment asymmetry;
  H5 shared failure (pilot-gated); the model-free rho moderator;
  dose module (second-difference contrast) and framing probe when those cells
  are present in the data.

All confirmatory alphas .005 (serial gatekeeping; prereg §3). On bot data the
report is labeled 'BOT DATA — pipeline validation only'. Where the prereg
leaves an operationalization open the choice is stated inline and marked
DESIGN-DECISION for author review.

Usage: python pipeline.py <custom_export.csv> <out_report.md>
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats_v2 as sv

ALPHA = 0.005
TRIALS = 450
PHASE_OF = lambda t: int(np.ceil(t / 150))
R3_PRED_RECOVERY = None   # frozen-form criterion (iii), absolute units (design basis)
KAPPA = 0.25              # H1b-SI / H1b-SIc (freeze I032 AD3/AD4)
# Scale-free criterion (iii): kappa must sit below R3's predicted normalized
# recovery; certified minimum across measurement shapes (records/
# pipeline_cert_I032_run3.csv, attenuation rows, column r3_norm_recovery).
_RUN3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                     'records', 'pipeline_cert_I032_run3.csv')
try:
    _r = pd.read_csv(_RUN3)
    R3_NORM_RECOVERY = float(_r[_r.reading == 'attenuation'].r3_norm_recovery.min())
except Exception:          # record absent: criterion reported as not evaluated
    R3_NORM_RECOVERY = None
# AUDIT: the confirmatory analysis set. Dose, framing, pilot and pool sessions
# share p2_regime labels with the core and must never enter H1a/H1b.
CONFIRMATORY_PREFIXES = ('main_confirmatory', 'cell_', 'bots_')
SUSPICION_CUT = None      # pilot-calibrated (prereg: applied blind); None = off
UNMOVED_CUT = None        # pilot-calibrated partial-mover screen; None = off


def load(path):
    d = pd.read_csv(path)
    trials = d[d.row_type == 'trial'].copy()
    ratings = d[d.row_type == 'rating'].copy()
    funnel = d[d.row_type == 'funnel'].copy() if 'funnel' in set(d.row_type) else d.iloc[0:0]
    for c in ('t', 'choice_good', 'reward', 'rt_ms'):
        trials[c] = pd.to_numeric(trials[c])
    for c in ('t', 'fairness', 'entitlement', 'rt_ms'):
        ratings[c] = pd.to_numeric(ratings[c])
    trials['phase'] = trials.t.map(PHASE_OF)
    ratings['phase'] = ratings.t.map(PHASE_OF)
    return trials, ratings, funnel


def apply_exclusions(trials, ratings, funnel):
    """Prereg: completion <90%; zero slider variance; P1 accuracy below
    chance + 2SE; median RT < 300 ms; pilot-calibrated suspicion probes applied
    blind to condition (hook below; OFF until the pilot fixes the cut)."""
    log, drop = [], set()
    for pid, g in trials.groupby('participant'):
        if g.t.nunique() < 0.9 * TRIALS:
            drop.add(pid); log.append((pid, 'completion<90%')); continue
        p1 = g[g.phase == 1]
        se2 = 2 * np.sqrt(0.25 / max(len(p1), 1))
        if p1.choice_good.mean() < 0.5 + se2:
            if (g.bot_kind == 'human').all():
                drop.add(pid)
                log.append((pid, f'P1-accuracy {p1.choice_good.mean():.3f} < chance+2SE'))
            else:
                log.append((pid, f'P1-accuracy {p1.choice_good.mean():.3f} < chance+2SE '
                                 f'(bot data: flagged only)'))
        if g.rt_ms.median() < 300:
            drop.add(pid); log.append((pid, 'medianRT<300ms'))
    # Zero-variance screen, translated for randomized slider starts (I032,
    # TECHNIQUES.md #10b): with a random start on every rating, a participant
    # who never touches the slider reports a fresh random value each time, so
    # 'zero variance of the report' no longer catches them. The frozen screen's
    # intent is restored exactly as 'zero MOVEMENT': reported == logged start on
    # every rating of both sliders. When no start values are logged (I006
    # exports), the original zero-variance rule applies unchanged.
    has_init = ('fairness_init' in ratings.columns and
                pd.to_numeric(ratings.fairness_init, errors='coerce').ge(0).any())
    for pid, g in ratings.groupby('participant'):
        if has_init:
            fi = pd.to_numeric(g.fairness_init, errors='coerce')
            ei = pd.to_numeric(g.entitlement_init, errors='coerce')
            if ((g.fairness == fi) & (g.entitlement == ei)).all():
                drop.add(pid); log.append((pid, 'zero slider movement (randomized starts)'))
        elif g.fairness.var() == 0 and g.entitlement.var() == 0:
            drop.add(pid); log.append((pid, 'zero slider variance'))
    # Reserved (pilot-calibrated, OFF until the pilot sets it): partial movers,
    # fraction of unmoved ratings >= UNMOVED_CUT. Not a preregistered screen yet.
    if SUSPICION_CUT is not None and len(funnel):
        for _, row in funnel.iterrows():
            try:
                if float(row.get('rig_suspicion') or 0) >= SUSPICION_CUT:
                    drop.add(row.participant)
                    log.append((row.participant, f'suspicion>= {SUSPICION_CUT} (blind)'))
            except (TypeError, ValueError):
                pass
    return drop, log


def per_participant(trials, ratings):
    rows = []
    for pid, tr in trials.groupby('participant'):
        ra = ratings[ratings.participant == pid]
        meta = tr.iloc[0]
        f = {ph: ra[ra.phase == ph].fairness.mean() for ph in (1, 2, 3)}
        e = {ph: ra[ra.phase == ph].entitlement.mean() for ph in (1, 2, 3)}
        hit = {ph: tr[tr.phase == ph].choice_good.mean() for ph in (1, 2, 3)}
        p3t = tr[tr.phase == 3].sort_values('t')
        half_beh = (hit[1] + hit[2]) / 2
        beh = p3t.choice_good.rolling(25, min_periods=10).mean()
        cross = p3t.t[beh >= half_beh]
        m_beh = int(cross.iloc[0]) if len(cross) else TRIALS
        p3r = ra[ra.phase == 3].sort_values('t')
        half_rat = (f[1] + f[2]) / 2
        rr = p3r.fairness.rolling(5, min_periods=2).mean()
        crossr = p3r.t[rr >= half_rat]
        m_rat = int(crossr.iloc[0]) if len(crossr) else TRIALS
        slope = np.nan
        if len(p3r) > 3:
            slope = np.polyfit(p3r.t, p3r.fairness, 1)[0] * 100
        tr_s = tr.sort_values('t')
        trail = tr_s.reward.rolling(15, min_periods=5).mean()
        trail_at = trail[tr_s.t.isin(ra.t)].values
        ent = ra.sort_values('t').entitlement.values / 100.0
        k = min(len(trail_at), len(ent))
        adapt = np.nan
        if k > 10:
            adapt = np.polyfit(trail_at[:k][~np.isnan(trail_at[:k])],
                               ent[:k][~np.isnan(trail_at[:k])], 1)[0]
        p1r = ra[ra.phase == 1].fairness
        endp2 = ra[(ra.t >= 280) & (ra.t <= 300)].fairness.mean()
        late3 = p3r[p3r.t > 375].fairness.mean() if len(p3r) else np.nan
        rows.append(dict(
            participant=pid, p2_regime=meta.cell_p2_regime,
            restoration=meta.restoration, bot_kind=meta.bot_kind,
            f1=f[1], f2=f[2], f3=f[3], e1=e[1], e2=e[2], e3=e[3],
            hit1=hit[1], hit2=hit[2], hit3=hit[3],
            acc_late=tr[tr.t > 375].choice_good.mean(),
            drop_p2=f[1] - f[2], mid_beh=m_beh, mid_rat=m_rat,
            lag=m_rat - m_beh, p3_slope=slope, adapt=adapt,
            p1_sd=p1r.std(ddof=1) if len(p1r) > 2 else np.nan,
            f3_late=p3r[p3r.t > 375].fairness.mean() if len(p3r) else np.nan,
            recovery=(late3 - f[2]) if len(p3r) else np.nan,
            end_p2=endp2, d3=(late3 - endp2) if len(p3r) else np.nan,
            config_name=(meta.config_name if 'config_name' in tr.columns else '')))
    return pd.DataFrame(rows)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        return dict(t=np.nan, p=np.nan, d=np.nan, n=(len(a), len(b)))
    t, p = stats.ttest_ind(a, b, equal_var=False)
    sp = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    d = (a.mean() - b.mean()) / sp if sp > 0 else np.nan
    return dict(t=t, p=p, d=d, n=(len(a), len(b)))


def run(path, out_md):
    trials, ratings, funnel = load(path)
    drop, exlog = apply_exclusions(trials, ratings, funnel)
    trials = trials[~trials.participant.isin(drop)]
    ratings = ratings[~ratings.participant.isin(drop)]
    pp = per_participant(trials, ratings)
    is_bot = set(pp.bot_kind.unique()) - {'human'} != set()

    L = []
    L.append("# Task v3 (market skin) analysis pipeline v2 — report")
    if is_bot:
        L.append("\n**BOT DATA — pipeline validation only. Nothing here is evidence "
                 "about humans.**\n")
    L.append(f"Input: `{path}` — {pp.shape[0]} participants after exclusions "
             f"({len(drop)} excluded). Suspicion hook: "
             f"{'OFF (pre-pilot)' if SUSPICION_CUT is None else SUSPICION_CUT}.")
    if exlog:
        L.append("\nExclusion log: " + "; ".join(f"{p}: {r}" for p, r in exlog))

    # AUDIT: confirmatory set by session config; modules analysed separately
    if pp.config_name.astype(str).str.len().gt(0).any():
        conf = pp[pp.config_name.astype(str).str.startswith(CONFIRMATORY_PREFIXES)]
        L.append(f"Confirmatory analysis set: {len(conf)} of {len(pp)} participants "
                 f"(config prefixes {CONFIRMATORY_PREFIXES}).")
    else:
        conf = pp
        L.append("WARNING: export has no config_name column (pre-audit export); "
                 "all participants treated as confirmatory.")
    hi = conf[conf.p2_regime == 'HIGH']; lo = conf[conf.p2_regime == 'LOW']
    dh = hi.drop_p2.dropna().values; dl = lo.drop_p2.dropna().values

    # ---- H1a (confirmatory): one-sided WMW, HIGH drops > LOW drops ----
    h1a = False
    if len(dh) > 5 and len(dl) > 5:
        h1a, z = sv.wmw_one_sided(dl, dh, ALPHA)
        th = sv.theta_hat(dl, dh)
        hl = sv.hodges_lehmann(dl, dh)
        wrej, wt, wp = sv.studentized_permutation_welch(dl, dh, ALPHA, B=1999)
        L.append(f"\n## H1a (confirmatory) — P2 fairness drop, HIGH vs LOW\n"
                 f"one-sided WMW z = {z:.2f} -> {'REJECT' if h1a else 'no rejection'} "
                 f"at alpha = {ALPHA}; theta-hat = {th:.3f}, Hodges-Lehmann shift = "
                 f"{hl:.1f} pts; studentized permutation Welch co-report: t = {wt:.2f}, "
                 f"p = {wp:.4g} ({'reject' if wrej else 'no rejection'}). "
                 f"n = ({len(dh)}, {len(dl)}).")
    else:
        L.append("\n## H1a — too few participants per arm in this dataset.")

    # ---- H1b (gatekept): only if H1a rejects ----
    # Four forms are computed and labelled; WHICH is confirmatory is fixed by the
    # preregistration text in force (author decision after I032; records/
    # 95_pipeline_cert_I032.md, 97_h1b_anatomy_I032pc.md):
    #   FROZEN  two-sided rank TOST on late-P3 - P2mean within +/-delta_eq
    #           (FAILED certification: unpowered at every slider gain; 23% false
    #           positives vs a no-gate composite)
    #   SI      one-sided signed-rank on c = rec - kappa*drop, all HIGH x MOD
    #   SIc     SI on the above-median-drop half (certified candidate)
    #   SIc-E   SIc with the end-of-P2 baseline (d3 = late-P3 - mean(t=280..300));
    #           EXPLORATORY, not certified (I033 obligation)
    if h1a:
        cell = hi[(hi.restoration == 'MODERATE')].dropna(subset=['recovery', 'drop_p2'])
        rec, drp = cell.recovery.values, cell.drop_p2.values
        deq, sig = sv.delta_eq_rule(cell.p1_sd.dropna().values)
        accm = cell.acc_late.mean()
        acc_ok = accm >= 0.70
        tost_ok, p_up, p_lo = sv.h1b_tost_frozen(rec, deq)
        r3_abs_ok = True if R3_PRED_RECOVERY is None else deq < R3_PRED_RECOVERY
        si_iii = None if R3_NORM_RECOVERY is None else KAPPA < R3_NORM_RECOVERY
        c = rec - KAPPA * drp
        up = drp > np.median(drp)
        si_ok, p_si = sv._signed_rank_less(c, ALPHA)
        sic_ok, p_sic = sv._signed_rank_less(c[up], ALPHA)
        ce = (cell.d3.values - KAPPA * drp)[up]
        sice_ok, p_sice = sv._signed_rank_less(ce[~np.isnan(ce)], ALPHA)
        iii_txt = ("not evaluated (record absent)" if si_iii is None else
                   f"kappa {KAPPA} {'<' if si_iii else '>='} R3 normalized recovery "
                   f"{R3_NORM_RECOVERY:.3f} -> {'PASS' if si_iii else 'FAIL'}")
        verdict = lambda ok: 'PASS' if (acc_ok and ok and si_iii is not False) else 'FAIL'
        L.append(f"\n## H1b (co-confirmatory, gatekept) — HIGH x MODERATE "
                 f"(n = {len(cell)}; above-median-drop half n = {int(up.sum())})\n"
                 f"(i) late-P3 accuracy = {accm:.3f} (floor 0.70: "
                 f"{'PASS' if acc_ok else 'FAIL'}); scale-free (iii): {iii_txt}.\n"
                 f"- FROZEN two-sided TOST (failed certification): sigma_r = {sig:.1f}, "
                 f"delta_eq = {deq:.1f}, mean rec = {np.mean(rec):.1f}: "
                 f"{'PASS' if (acc_ok and tost_ok and r3_abs_ok) else 'FAIL'} "
                 f"(p_upper {p_up:.3g}, p_lower {p_lo:.3g}).\n"
                 f"- SI (all): {verdict(si_ok)} (p = {p_si:.3g}).\n"
                 f"- **SIc (certified candidate)**: {verdict(sic_ok)} (p = {p_sic:.3g}).\n"
                 f"- SIc-E end-of-P2 baseline (exploratory, uncertified): "
                 f"{verdict(sice_ok)} (p = {p_sice:.3g}); mean d3 = "
                 f"{np.nanmean(cell.d3.values):.1f}.\n"
                 f"The confirmatory form is the one fixed in the preregistration in force.")
    else:
        L.append("\n## H1b — gatekept: not tested (H1a did not reject).")

    # ---- H2: timescale decoupling ----
    w2 = welch(hi.lag, lo.lag)
    L.append(f"\n## H2 — recovery-midpoint lag (rating − choice), HIGH vs LOW\n"
             f"mean lag HIGH = {hi.lag.mean():.0f} trials, LOW = {lo.lag.mean():.0f}; "
             f"Welch t = {w2['t']:.2f}, p = {w2['p']:.4g}, d = {w2['d']:.2f}. "
             f"Midpoints censored at 450 count as no recovery.")

    # ---- H3: reference x restoration interaction on P3 rating slope ----
    import statsmodels.formula.api as smf
    sub = pp.dropna(subset=['p3_slope'])
    ncells = sub.groupby(['p2_regime', 'restoration']).ngroups
    if sub.restoration.nunique() > 1 and sub.p2_regime.nunique() > 1 and ncells == 4:
        m = smf.ols('p3_slope ~ C(p2_regime) * C(restoration)', data=sub).fit()
        term = [x for x in m.params.index if ':' in x]
        tt = term[0] if term else None
        L.append(f"\n## H3 — P3 rating slope, regime × restoration interaction\n"
                 f"interaction {tt}: b = {m.params.get(tt, np.nan):.2f}, "
                 f"p = {m.pvalues.get(tt, np.nan):.4g} (OLS; mixed model on human data).")
    else:
        L.append(f"\n## H3 — regime × restoration interaction: "
                 f"**incomplete 2×2 crossing in this dataset ({ncells}/4 cells)** — "
                 f"interaction not estimable; runs on the full design.")

    # ---- H4: increment asymmetry ----
    seq = []
    for pid, ra in ratings.groupby('participant'):
        ra = ra.sort_values('t'); tr = trials[trials.participant == pid]
        prev = None
        for _, row in ra.iterrows():
            if prev is not None:
                inter = tr[(tr.t > prev.t) & (tr.t <= row.t)]
                shortfall = (prev.entitlement / 100.0 - inter.reward).clip(lower=0).mean()
                seq.append(dict(participant=pid, dfair=row.fairness - prev.fairness,
                                shortfall=shortfall))
            prev = row
    sq = pd.DataFrame(seq).dropna()
    try:
        md = smf.mixedlm('dfair ~ shortfall', sq, groups=sq['participant']).fit(reml=False)
        L.append(f"\n## H4 — increment asymmetry (Δfairness ~ entitlement shortfall)\n"
                 f"b(shortfall) = {md.params['shortfall']:.2f}, "
                 f"p = {md.pvalues['shortfall']:.4g} (MixedLM, random intercept). "
                 f"DISS predicts graded-down/constant-up.")
    except Exception as e:
        L.append(f"\n## H4 — MixedLM did not converge on this dataset ({e}); "
                 f"OLS fallback: b = "
                 f"{np.polyfit(sq.shortfall, sq.dfair, 1)[0]:.2f}.")

    # ---- H5: shared failure (pilot-gated) ----
    if 'EQUAL' in set(pp.p2_regime.unique()):
        eq = pp[pp.p2_regime == 'EQUAL']
        w5 = welch(hi.drop_p2, eq.drop_p2)
        L.append(f"\n## H5 — shared failure: HIGH vs EQUAL-misery drop: "
                 f"t = {w5['t']:.2f}, p = {w5['p']:.4g}, d = {w5['d']:.2f}.")
    else:
        L.append("\n## H5 — shared-failure cell absent from this dataset "
                 "(pilot-gated).")

    # ---- dose module (SUSPENDED after I032 certification; computed if present) ----
    cfgn = pp.config_name.astype(str)
    d45 = pp[cfgn == 'dose_45'].drop_p2.dropna().values
    d55 = pp[cfgn == 'dose_55'].drop_p2.dropna().values
    if len(d45) > 10 and len(d55) > 10 and len(dh) > 10:
        rej, Cst, tst, p = sv.dose_second_difference(d45, d55, dh)
        L.append(f"\n## Dose module (SUSPENDED: failed certification, E6) — "
                 f"second difference C = {Cst:.1f}, t = {tst:.2f}, p = {p:.4g} "
                 f"({'reject linearity' if rej else 'no rejection'}; descriptive only).")
    else:
        L.append("\n## Dose module — dose cells absent from this dataset.")

    # ---- framing probe (when present) ----
    fr = pp[cfgn == 'framing_probe'].drop_p2.dropna().values
    if len(fr) > 10 and len(dl) > 10:
        rejf, zf = sv.framing_test(fr, dl)
        L.append(f"\n## Framing probe — one-sided WMW framing vs LOW: z = {zf:.2f} "
                 f"-> {'reject' if rejf else 'no rejection'} (alpha .05).")
    else:
        L.append("\n## Framing probe — framing cell absent from this dataset.")

    # ---- moderator: model-free aspiration rigidity ----
    hi_m = hi.dropna(subset=['adapt', 'f3_late'])
    if len(hi_m) > 3:
        r, p = stats.pearsonr(hi_m.adapt, hi_m.f3_late)
        L.append(f"\n## Moderator — slider-adaptation speed × late-P3 fairness (HIGH)\n"
                 f"r = {r:.2f}, p = {p:.4g}; n = {len(hi_m)}.")
    else:
        L.append("\n## Moderator — too few HIGH-cell participants in this dataset.")

    L.append(f"\n---\nParticipant-level table: {pp.shape[0]} rows × {pp.shape[1]} cols; "
             f"written alongside the report.")
    pp.to_csv(out_md.replace('.md', '_participants.csv'), index=False)
    open(out_md, 'w').write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
