# I032 audit — everything delivered, before Docker and oTree deployment

Date 2026-11-09. Scope: every I032 artifact (freeze and addenda, generator,
statistics, certification runs, G1/G2/S7, post-hoc anatomy, oTree app, analysis
pipeline, pool tool, design documents, prereg draft, citation log, Project
mirrors, memory record). Self-conducted, so it is not independent review. It
is, however, mechanized wherever possible: reruns from committed code, scalar
reference implementations, scipy references, null-level Monte Carlo, an
app-format end-to-end test, bot sessions that assert their own invariants, and
git chronology. Everything mechanized is committed as tests or scripts and can
be re-run by anyone.

## Verdict

The certification results stand and reproduce (see Reproduction). **The oTree
instrument, as delivered at the I032 close, would not have run the experiment
that was certified.** Three critical defects, now fixed in code:
1. With a real pilot pool, HIGH and LOW participants would both have seen
   deprivation peers, so there would have been no manipulation.
2. The peer statistic would have kept only 31% of the certified reference gap.
3. A forecast bonus was promised to participants and never paid.

Six high-severity defects were also fixed. All 17 session configs pass the
bots, 23 tests pass, and the production guards fire. Two design questions those
fixes raise need the author before any human is recruited (§ Author decisions).

## Findings

Severity: CRITICAL = invalidates the experiment or breaks the no-deception
protocol; HIGH = wrong claim, data-integrity or budget error; MEDIUM;
LOW. Status: FIXED (code + test), RESTATED (wording corrected to the evidence),
OPEN.

| ID | Sev | Area | Finding | Evidence | Status |
|---|---|---|---|---|---|
| C1 | CRITICAL | peer pool / selection | The design's HIGH source is infeasible: standard-schedule participants earn ~.28 in P2 (450-trial rate .44–.50), so none can supply a P2 window in [.60,.70]. The code selected on the 450-trial rate, found no candidate and **silently fell back to `streams[0]`, a deprivation peer**. LOW selection compared 450-trial rates to the participant's end-of-P1 trailing rate (~.60), found none, and took the nearest (also deprivation peers). With a real pilot pool, both arms would have seen deprivation peers in P2 | arithmetic in this audit; code at a3dcaaf..360439c `_pick_peer_stream` | FIXED in code: selection on the current-block window rate; LOW = same-schedule stream matched on previous-block rate; rich-rule pool-source config `pool_rich`; pool tool emits schedule + block rates + feasibility. **Design decision OPEN** (wording, pool size) |
| C2 | CRITICAL | displayed reference | The board showed the peer's cumulative rate since round 1. For a LOW deprivation peer that is ~.50 on average in P2 (.60 → .44), against ~.28 actual P2 play, so the HIGH−LOW displayed gap is .10 against the .33 the certified generator assumed (31%). The generator anchors LOW to the participant's own trailing band | arithmetic in this audit | FIXED: trailing-15 win rate, identical statistic in both arms; label and instructions updated. Author to confirm |
| C3 | CRITICAL | truthfulness | The instructions promise a forecast bonus ("one forecast round is drawn… 10-point bonus with probability 1 − (o − f)²"); the code never paid it | code review | FIXED: settled once at the funnel (seeded, idempotent), added to points, shown on the results page, exported; bot-tested |
| H1 | HIGH | data integrity | A page reload re-sent `start`, which **reset the block counter, re-drew the peer and replayed settlements**, duplicating trials and points | code review | FIXED: per-block server state; a reload resumes with any owed screen; choices refused while a screen is owed; duplicate or unsolicited submissions refused. `bots_refresh`: 6 reloads per participant, exactly 450 trials / 90 ratings / 30 forecasts / 2 WTP each |
| H2 | HIGH | budget | `points_to_currency = 0.02` would pay ~£6.30 per participant against DESIGN's ~£1.10, and the participation fee was £2.00 against £4.20. Across ~1,120 recruits the budget error is ~£5.6k | settings vs DESIGN §2 | FIXED to DESIGN (£4.20 + £0.0035/point); author to confirm |
| H3 | HIGH | analysis integrity | `pipeline.py` detected dose/framing cells by the *session code* (random 8 characters), so those modules were never analysed. In a combined export, H1a pooled every HIGH-P2 participant, including dose and framing cells, which contaminates the confirmatory test | code review | FIXED: confirmatory set by config name; modules by config name; end-to-end test (216 of 240 kept) |
| H4 | HIGH | claim vs code | Docs said the pipeline computes "the frozen and candidate forms" of H1b; it computed the frozen form and a non-superiority variant, not the certified H1b-SIc | code review | FIXED: frozen, SI, SIc and an exploratory end-of-P2 variant, all labelled |
| H5 | HIGH | truthfulness | A human session with no pool path would silently show the **simulated** placeholder pool | code review | FIXED: refused in production mode (tested); bot sessions still allowed |
| H6 | HIGH | export | No config name, schedule, peer stream, ticket, betting familiarity, comprehension attempts, reloads, forecast bonus or payoff in the export | code review | FIXED (columns appended; old positions unchanged) |
| M1 | MED | assignment | Independent coin flips per participant: HIGH/LOW split SD ~13 over 720 recruits, against a 360/arm plan | code review | FIXED: permuted blocks of 6 per session (exact 4/2/4/2 in a 12-person test) |
| M2 | MED | deployment | `SECRET_KEY` hard-coded | settings | FIXED: from env; refused in production (tested) |
| M3 | MED | certification scope | The secondaries H2–H4 and the ρ moderator were **never certified** on synthetic cohorts; I032 certified H1a, H1b, dose, framing and ρ recovery. H4's mixed model can be singular on simulated data | this audit | OPEN — I033 |
| M4 | MED | claim strength | Point estimates were reported as passes where 95% Clopper–Pearson intervals straddle the threshold (see Statistical restatements) | records | RESTATED below |
| M5 | MED | provenance | Run 1, G1 and run 3 were launched before their scripts' first commit | git chronology | Closed by bit-identical reproduction from the committed code (below) |
| M6 | MED | provenance | AD3's κ = .25 rationale quoted R3's normalized recovery as +.66 without a logged computation; recomputed from records +.694 (gate −.751 confirmed). Conclusion unchanged | records/h1b_anatomy | Logged |
| M7 | MED | test coverage | The comprehension quiz's error path was untested; "unit-tested" (zero-movement screen) had no committed test | — | FIXED: bots submit a wrong answer that must fail; screen test committed |
| M8 | MED | provenance | `records/dose_posthoc_I032.txt` was produced by an inline snippet; no committed code generated it | session record | FIXED: committed verbatim as `dose_posthoc_I032.py`; regenerates the record byte-for-byte |
| L1 | LOW | repo | 7 `.pyc` files committed; no `.gitignore` | git | FIXED |
| L2 | LOW | docs | REPRODUCIBILITY said the bundle holds simulated referee reports (the rule keeps them out; none are in the repo). No I032 section. Experiment README described I006 | — | FIXED |
| L3 | LOW | citation | `HamJenkins2025`: first author "Ham, Hackjin" is wrong (title page: **Huang Ham**), article number missing, no verification record | author's PDF title page | FIXED in `refs.bib` (metadata only, no prose); logged |
| L4 | LOW | bots | The bot's forecast used the good ticket's value regardless of the SQUARE mapping | code review | FIXED (bot data only) |
| L5 | LOW | wording | The forecast asks whether SQUARE pays next round, which is scored even when SQUARE is not chosen, and participants never see that settlement | code review | OPEN — wording ("whether or not you choose it") |
| L6 | LOW | pool sizing | A rich-rule participant reaches the .60 HIGH band only with accuracy ≳ .83 | arithmetic | OPEN — size pool-source sessions from the pilot |

## What held (verified this audit)

- **Generator port.** All four kernels (gate, R1-global, R4, R3), both arms,
  plus the framing variant equal a scalar line-by-line port of the frozen
  `predict_taskv3.py` driven by the same uniforms, to 1e-6
  (`tests/test_generator_port.py`).
- **Statistics.** WMW equals scipy to 1e-10 with heavy ties; θ̂ = U/(n₁n₂);
  Hodges–Lehmann matches brute force. Null levels sit inside 95% CP intervals at
  the alphas used: one-sided WMW at .005 (20,000 nulls, rounded data);
  studentized permutation Welch under heteroskedasticity with unequal n (.05);
  signed rank at the H1b null boundary (.005); the dose test under a graded line
  (.05), which confirms the AD1 repair was needed (`tests/test_stats.py`).
- **Pipeline.** It reads an app-format export and recovers the certification's
  per-participant statistics exactly (drop, recovery, d3, P1 SD); module
  filtering works; the zero-movement screen catches never-movers that the
  variance rule misses (variance 968) (`tests/test_pipeline_e2e.py`).
- **oTree persistence.** `participant.vars` is marked changed on every access
  and pickled whole, so nested state survives across live requests (oTree
  source, `database.py`).
- **Chronology.** Every addendum (AD1–AD4) and every exploration question set
  was committed before the run it governs (git log). The one gap is M5.
- **Numbers.** Every scorecard figure in the closing report, certification
  record, DESIGN, TASK_SPEC, PRIORS, prereg draft, anatomy record and memory was
  re-derived from the record CSVs and matches.
- **Citations.** Every reference used in the design documents has a
  verification entry. The one gap found (Ham & Jenkins) is fixed.
- **Simulated referee material** is absent from the public repo.

## Statistical restatements (95% Clopper–Pearson)

| Claim as written | Interval | Restated |
|---|---|---|
| H1a power ≥ .90 in every shape | M1 .911 [.892, .928]; other shapes' lower bounds ≥ .917 | ≥ .90 in point estimate everywhere; M1's interval includes .89 |
| H1b-SIc power .904–.966 | M1 .904 [.884, .922] | M1 marginal at 95% |
| SIc false positives .000 vs composite | 0/500, upper .007 | "none in 500 (95% upper .007)": passes the frozen criterion, does not demonstrate ≤ .005 |
| R3 false positives (SI/SIc) .000 | 0/1000 per shape, upper .004 | demonstrated ≤ .005 |
| R4 H1a level | M6 .004 [.001, .010] | passes the frozen criterion; ≤ .005 not demonstrated at B = 1000 |
| G1 r = .914 | Fisher-z 95% [.859, .948] | robustly above .7 |
| framing .876 vs .010 | [.844, .904] vs [.003, .023] | robust |

## Reproduction

Every seeded record was regenerated from the committed code (2026-11-09,
13:47–14:30 UTC) and compared byte-for-byte with the committed version. **All
are identical.**

| Record | Script | Result |
|---|---|---|
| `g2_consistency.csv` | `g2_consistency.py` | identical |
| `power_free_s7.csv` (+ log) | `analysis/power_free_s7.py` | identical |
| `g1_recovery_I032.csv` (+ summary) | `g1_recovery.py` | identical |
| `pipeline_cert_I032_calib.csv` | `pipeline_cert.py` | identical |
| `pipeline_cert_I032.csv` | `pipeline_cert.py` | identical |
| `pipeline_cert_I032_run3.csv` | `pipeline_cert_run3.py` | identical |
| `h1b_anatomy_I032pc.{txt,csv}` | `explore_h1b_anatomy.py` | identical |
| `h1b_baseline_I032pc.txt` | `explore_h1b_baseline.py` | identical |
| `dose_posthoc_I032.txt` | inline snippet → committed in the audit as `dose_posthoc_I032.py` | identical |

This closes M5: the three scripts launched before their first commit (run 1,
G1, run 3) are, as committed, the code that produced the records. One further
provenance gap was found here and closed (M8 below). Hashes of every record and
script are in `records/manifest_I032.sha256` (`sha256sum -c` to verify).

## Author decisions (before any human is recruited)

1. **Trader-board wording and the rich-rule pool.** Truthful HIGH peers must come
   from rich-rule sessions. The instructions already say rules differ across
   sessions, but saying so explicitly on the board changes what the global-rig
   Bayesian rival should infer from a successful peer. Choose the wording;
   I can then re-run the R1-global cell under the chosen reading.
2. **Displayed statistic.** Trailing-15 (built, generator-consistent) or another
   window. Cumulative is not an option: it keeps 31% of the manipulated gap.
3. **Payment.** Confirm £4.20 + £0.0035/point (~£1.10), or restate the budget.
4. **Pool-source size**, from the pilot's accuracy distribution (rich-rule
   participants need accuracy ≳ .83 to qualify as HIGH).
5. Carried from I032: the H1b form; the dose module; the two flagged main-text
   items.

## Docker / oTree-phase checklist (what is not yet built)

Prolific integration (participant label, completion redirect, return codes);
a pinned dependency file (`otree==6.0.15`, numpy/scipy/pandas/statsmodels
versions); Postgres via `DATABASE_URL`; environment variables
`OTREE_PRODUCTION`, `OTREE_SECRET_KEY`, `OTREE_ADMIN_PASSWORD`;
inactivity/timeout handling on the 28-minute live page; desktop-only enforcement
(currently left to the Prolific filter); export and backup procedure; a smoke
test of the image running `otree test` on every config plus `pytest`.
