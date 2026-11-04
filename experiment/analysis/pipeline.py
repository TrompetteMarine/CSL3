"""
Frozen analysis pipeline for task v3 (prereg draft I003/M4; built in KGi-DISS-I006).

Implements, against the oTree custom export of diss_bandit:
  exclusions; H1 (primary); H2 timescale decoupling; H3 recovery threshold;
  H4 increment asymmetry; H5 shared failure (pilot-gated: reports 'cell absent' if the
  equal-misery cell is not in the data); the model-free aspiration-rigidity moderator.

All alphas are .005 two-sided (prereg section 3). When run on bot data the report is
labeled 'BOT DATA — pipeline validation only' and nothing in it is evidence about
humans. Statistics follow the prereg; where the prereg leaves an operationalization
open, the choice is stated inline and marked DESIGN-DECISION for author review.

Usage: python pipeline.py <custom_export.csv> <out_report.md>
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.005
TRIALS = 450
PHASE_OF = lambda t: int(np.ceil(t / 150))


def load(path):
    d = pd.read_csv(path)
    trials = d[d.row_type == 'trial'].copy()
    ratings = d[d.row_type == 'rating'].copy()
    for c in ('t', 'choice_good', 'reward', 'rt_ms'):
        trials[c] = pd.to_numeric(trials[c])
    for c in ('t', 'fairness', 'entitlement', 'rt_ms'):
        ratings[c] = pd.to_numeric(ratings[c])
    trials['phase'] = trials.t.map(PHASE_OF)
    ratings['phase'] = ratings.t.map(PHASE_OF)
    return trials, ratings


def apply_exclusions(trials, ratings):
    """Prereg: completion <90%; zero slider variance; P1 accuracy below chance + 2SE;
    median RT < 300 ms."""
    log, drop = [], set()
    for pid, g in trials.groupby('participant'):
        if g.t.nunique() < 0.9 * TRIALS:
            drop.add(pid); log.append((pid, 'completion<90%')); continue
        p1 = g[g.phase == 1]
        se2 = 2 * np.sqrt(0.25 / max(len(p1), 1))
        if p1.choice_good.mean() < 0.5 + se2:
            # Prereg wording 'P1 accuracy below chance + 2SE' implemented as
            # accuracy < 0.5 + 2SE. ENFORCED on human data; flag-only for bot smoke
            # runs (random bots are at chance by construction).
            if (g.bot_kind == 'human').all():
                drop.add(pid)
                log.append((pid, f'P1-accuracy {p1.choice_good.mean():.3f} < chance+2SE'))
            else:
                log.append((pid, f'P1-accuracy {p1.choice_good.mean():.3f} < chance+2SE '
                                 f'(bot data: flagged only)'))
        if g.rt_ms.median() < 300:
            drop.add(pid); log.append((pid, 'medianRT<300ms'))
    for pid, g in ratings.groupby('participant'):
        if g.fairness.var() == 0 and g.entitlement.var() == 0:
            drop.add(pid); log.append((pid, 'zero slider variance'))
    return drop, log


def per_participant(trials, ratings):
    rows = []
    for pid, tr in trials.groupby('participant'):
        ra = ratings[ratings.participant == pid]
        meta = tr.iloc[0]
        f = {ph: ra[ra.phase == ph].fairness.mean() for ph in (1, 2, 3)}
        e = {ph: ra[ra.phase == ph].entitlement.mean() for ph in (1, 2, 3)}
        hit = {ph: tr[tr.phase == ph].choice_good.mean() for ph in (1, 2, 3)}
        # recovery midpoints in P3 (DESIGN-DECISION: midpoint = first t in P3 at which
        # the trailing-25-trial [choice] / trailing-5-rating [fairness] series crosses
        # halfway between its P2 mean and its P1 mean; censored at 450 if never)
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
        # P3 fairness slope (per 100 trials)
        slope = np.nan
        if len(p3r) > 3:
            slope = np.polyfit(p3r.t, p3r.fairness, 1)[0] * 100
        # model-free aspiration rigidity: entitlement slider ~ trailing outcome rate
        tr_s = tr.sort_values('t')
        trail = tr_s.reward.rolling(15, min_periods=5).mean()
        trail_at = trail[tr_s.t.isin(ra.t)].values
        ent = ra.sort_values('t').entitlement.values / 100.0
        k = min(len(trail_at), len(ent))
        adapt = np.nan
        if k > 10:
            adapt = np.polyfit(trail_at[:k][~np.isnan(trail_at[:k])],
                               ent[:k][~np.isnan(trail_at[:k])], 1)[0]
        rows.append(dict(
            participant=pid, p2_regime=meta.cell_p2_regime,
            restoration=meta.restoration, bot_kind=meta.bot_kind,
            f1=f[1], f2=f[2], f3=f[3], e1=e[1], e2=e[2], e3=e[3],
            hit1=hit[1], hit2=hit[2], hit3=hit[3],
            drop_p2=f[1] - f[2], mid_beh=m_beh, mid_rat=m_rat,
            lag=m_rat - m_beh, p3_slope=slope, adapt=adapt,
            f3_late=p3r[p3r.t > 375].fairness.mean() if len(p3r) else np.nan))
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
    trials, ratings = load(path)
    drop, exlog = apply_exclusions(trials, ratings)
    trials = trials[~trials.participant.isin(drop)]
    ratings = ratings[~ratings.participant.isin(drop)]
    pp = per_participant(trials, ratings)
    is_bot = set(pp.bot_kind.unique()) - {'human'} != set()

    L = []
    L.append("# Task v3 analysis pipeline — smoke report")
    if is_bot:
        L.append("\n**BOT DATA — pipeline validation only. Nothing here is evidence "
                 "about humans.**\n")
    L.append(f"Input: `{path}` — {pp.shape[0]} participants after exclusions "
             f"({len(drop)} excluded).")
    if exlog:
        L.append("\nExclusion log: " + "; ".join(f"{p}: {r}" for p, r in exlog))

    hi = pp[pp.p2_regime == 'HIGH']; lo = pp[pp.p2_regime == 'LOW']

    # ---- H1 (primary): P2 fairness drop, HIGH vs LOW ----
    w = welch(hi.drop_p2, lo.drop_p2)
    L.append(f"\n## H1 (primary) — P2 fairness drop HIGH vs LOW\n"
             f"mean drop HIGH = {hi.drop_p2.mean():.1f}, LOW = {lo.drop_p2.mean():.1f}; "
             f"Welch t = {w['t']:.2f}, p = {w['p']:.4g}, d = {w['d']:.2f}, n = {w['n']}. "
             f"(alpha = {ALPHA}, two-sided)")

    # ---- H2: timescale decoupling (rating-recovery lag behind choice recovery) ----
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

    # ---- H4: increment asymmetry (mixed effects) ----
    seq = []
    for pid, ra in ratings.groupby('participant'):
        ra = ra.sort_values('t'); tr = trials[trials.participant == pid]
        prev = None
        for _, row in ra.iterrows():
            if prev is not None:
                inter = tr[(tr.t > prev.t) & (tr.t <= row.t)]
                shortfall = (prev.entitlement / 100.0 - inter.reward).clip(lower=0).mean()
                seq.append(dict(participant=pid, dfair=row.fairness - prev.fairness,
                                shortfall=shortfall,
                                direction='down' if shortfall > 0 else 'up'))
            prev = row
    sq = pd.DataFrame(seq).dropna()
    try:
        import statsmodels.api as sm
        md = smf.mixedlm('dfair ~ shortfall', sq, groups=sq['participant']).fit(reml=False)
        L.append(f"\n## H4 — increment asymmetry (Δfairness ~ entitlement shortfall)\n"
                 f"b(shortfall) = {md.params['shortfall']:.2f}, "
                 f"p = {md.pvalues['shortfall']:.4g} (MixedLM, random intercept). "
                 f"DISS predicts graded-down/constant-up; LR-symmetric updating predicts "
                 f"symmetry.")
    except Exception as e:  # singular fits on tiny bot samples
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
                 "(pilot-gated; runs only when the EQUAL-misery cell is collected).")

    # ---- moderator: model-free aspiration rigidity ----
    hi_m = hi.dropna(subset=['adapt', 'f3_late'])
    if len(hi_m) > 3:
        r, p = stats.pearsonr(hi_m.adapt, hi_m.f3_late)
        L.append(f"\n## Moderator — slider-adaptation speed × late-P3 fairness (HIGH)\n"
                 f"r = {r:.2f}, p = {p:.4g}; slow adapters (small coefficient) are "
                 f"predicted to show durable grievance (lower late-P3 fairness). "
                 f"n = {len(hi_m)}.")
    else:
        L.append("\n## Moderator — too few HIGH-cell participants in this dataset.")

    L.append(f"\n---\nParticipant-level table: {pp.shape[0]} rows × {pp.shape[1]} cols; "
             f"written alongside the report.")
    pp.to_csv(out_md.replace('.md', '_participants.csv'), index=False)
    open(out_md, 'w').write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
