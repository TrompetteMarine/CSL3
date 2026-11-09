# KGi-DISS-I032 — closing report

Freeze `freezes/00_freeze_I032.yaml` (closed, scorecard inside); CSL3 main from
a3dcaaf to the I032 close. Certification record `records/95_pipeline_cert_I032.md`;
technique table `experiment/TECHNIQUES.md`; bias inventory
`experiment/BIAS_INVENTORY.md`; citation log `freezes/00_citation_verification_I032.md`;
KG delta `freezes/kg_delta_I032.yaml`.

## Outcome

The synthetic certification did its job: it found, before any human was
recruited, that **the co-confirmatory H1b as drafted cannot work.** On
market-skinned synthetic cohorts with known truth, the frozen absolute-band
H1b never confirms the gate when the gate is present. Its power is .000 at the
design basis, because matching the gate to θ = .592 compresses the P3
dissociation to about 2 slider points inside a 5-point band. It is also .000 at
full scale, because the gate *declines* in P3 rather than flatlining and leaves
the band. And it confirms a gate that is absent 23% of the time when the
population mixes utility types with group-contingent types. A candidate
frozen before it was run, H1b-SIc, is powered (.904–.966) and specific (.000)
in every simulated cell. It compares each high-drop participant's P3 recovery
to their own P2 drop, so attenuation cancels, and it tests the gate's
same-person conjunction, which the composite rival cannot mimic. It is
certified as a candidate, not adopted.

What survives intact: H1a (power .911–.963 in every measurement shape, rivals
contained), gate G1 (ρ r = .914 on the market skin), gate G2 (pipeline equals
power engine on every shared draw), and the framing probe (.876 vs .010).

The second failure is theoretical. The step-versus-line dose module has no
power (.040/.026 vs R3's .044) because the gate's dose response is linear
within the session. The χ_min frontier is a statement about permanence, not
about a 150-trial drop. The I028 claim is corrected in place. The in-session
separation is the slope of the P3 response across μ_ref, which is post-hoc and
an I033 candidate.

Four defects were found and fixed before they could reach a human: a silent
dispatch fall-through (run 1 invalidated and preserved); randomized slider
starts defeating the zero-variance screen (translated to zero movement,
unit-tested); a forecast scored against an outcome the participant had already
seen; and a dose-test null that would have tested the wrong hypothesis (fixed
pre-run). One of my pre-run predictions (E4) was wrong, and it is recorded as
wrong.

## Status of the three pre-prereg gates

G1 **PASSED**. G2 **PASSED**. G3 (pilot rules) **open, author-gated**. A fourth
blocker arises from this iteration: **the H1b form**. The preregistration
cannot be filed until the author chooses it.

## Author decisions (one paragraph)

Five items need the author. (1) **H1b form:** adopt the certified H1b-SIc
(drop-conditioned, κ = .25), keep the frozen TOST knowing it is unpowered and
non-specific, or commission a different form for certification. Nothing can be
filed until this is settled. (2) **Dose module (180 participants, roughly
£1.1k):** drop it, re-specify it as the P3-slope test and certify that first
(I033), or keep it as a descriptive χ readout. (3) **Main text:** the
certification contradicts three stated items, flagged and not edited: Table 1's
H1b row and its test, the experiment paragraph's band-from-pilot-noise
sentence and power footnote, and "flatlining under moderate restoration (43 and
14)", where the generator's own numbers show a decline. Whether and when to
revise them is the author's call. (4) **Market display:** whether to show
market-maker prices at all (fixed 50/50 quotes against an experienced ~65%
rate could seed a "mispriced market" suspicion, which is harmless only while
it is symmetric across arms). (5) Unchanged and still author-side: pilot
funding (~£6.3k all-in plus pilot, less ~£1.1k if the dose module is dropped),
the ethics application, and OSF filing, all gated on the above.
