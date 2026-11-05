# Citation verification log — KGi-DISS-I004 (D7 gate)

Rule: every load-bearing technical citation added in I004 is verified against an
authoritative record before use. Internal theorem/section numbers are cited ONLY
when independently verified; otherwise the result is cited at content level.

| Key | Claim cited for | Verified facts | Source of verification | NOT asserted |
|---|---|---|---|---|
| Hajek1982 | drift conditions with bounded increments => exponential hitting/occupation-time bounds (Prop. resignation (ii)) | Hajek, "Hitting-Time and Occupation-Time Bounds Implied by Drift Analysis with Applications", Adv. Appl. Prob. 14(3):502-525, 1982 | JSTOR/record check (I004, prior turn) | internal theorem numbers |
| BenaimWeibull2003 | finite-N population averages track mean-field ODE with exp(-cN) error on finite horizons | Benaim & Weibull, "Deterministic Approximation of Stochastic Evolution in Games", Econometrica 71(3):873-903, 2003 | Econometrica record check (I004, prior turn) | internal theorem numbers |
| Borkar2008 | constant-stepsize SA -> mean ODE on finite rescaled horizons (Ch. 9); two-timescale slow-fast (Ch. 6); stochastic recursive inclusions for piecewise-smooth drift (Ch. 5) | Borkar, "Stochastic Approximation: A Dynamical Systems Viewpoint", Hindustan Book Agency, TRIM 48, 2008. ToC verified: Ch.5 "Stochastic Recursive Inclusions", Ch.6 "Multiple Timescales" (6.1 Two timescales), Ch.9 "Constant Stepsize Algorithms" | publisher preview PDF ToC (e-bookshelf), 2026-11-04 | theorem numbers within chapters |
| KushnerYin2003 | weak convergence of constant-gain interpolations to the mean ODE | Kushner & Yin, "Stochastic Approximation and Recursive Algorithms and Applications", 2nd ed., Springer, Stochastic Modelling and Applied Probability, 2003; publisher description confirms "complete development of both probability one and weak convergence methods", constant-step/two-timescale coverage | MPDL ebook bibliographic record, 2026-11-04 | chapter/theorem numbers |
| Benaim1999 | interpolated SA process is an asymptotic pseudotrajectory; limit sets in chain-recurrent set of the semiflow | Benaim, "Dynamics of Stochastic Approximation Algorithms", Seminaire de Probabilites XXXIII, LNM 1709, pp. 1-68, Springer, 1999, DOI 10.1007/BFb0096509 | Utah lnm bibliography record, 2026-11-04 | internal theorem numbers |
| BLM2013 | Hoeffding's inequality for weighted sums of bounded independent variables (Prop. resignation (i)) | Boucheron, Lugosi & Massart, "Concentration Inequalities: A Nonasymptotic Theory of Independence", OUP, 2013, ISBN 978-0-19-953525-5 | bibliographic record (spdes-bib / WorldCat), 2026-11-04 | the book-internal theorem number for Hoeffding (commonly quoted as Thm 2.8) could NOT be confirmed from an authoritative source; cited at content level only |

Usage discipline applied in supplement.tex:
- Resignation proof (i): Hoeffding bound computed explicitly from the EWMA weight norm
  rho/(2-rho); only the inequality itself is imported (BLM2013).
- Resignation proof (ii): drift lower bound and increment bound computed in-model;
  Hajek1982 imported for the drift-to-hitting-time conversion.
- Race proposition: ODE integration is self-contained; KushnerYin2003/Borkar2008 Ch.9
  license the small-gain reading, BenaimWeibull2003 the finite-N reading; kinks and
  reflection flagged as outside the cited theorems' global hypotheses.
- SA section: Benaim1999 for APT/chain-recurrence framing; Borkar2008 Ch.5/Ch.6 for
  inclusions and two-timescale; open problems retained verbatim.

## I012 additions (all web-verified 2026-11-04)
| Key | Verified facts | Source |
|---|---|---|
| AkerlofDickens1982 | AER 72:307-319, 1982 | Palgrave reference entry |
| Rabin1994 | JEBO 23(2):177-194, 1994 | RePEc handle eee:jeborg:v:23:y:1994:i:2:p:177-194 |
| Benabou2013 | REStud 80(2):429-462, 2013 | RePEc handle oup:restud:v:80:y:2013:i:2:p:429-462 |
| HegselmannKrause2002 | JASSS 5(3), 2002 | jasss.org/5/3/2.html |
| Bohren2016 | JET 163:222-247, 2016 | RePEc handle eee:jetheo:v:163:y:2016:i:c:p:222-247 |

## I014 additions (verified 2026-11-04)
- FudenbergLevine1993: Econometrica 61(3):523-545 (econometricsociety.org 1993/05 issue 3; RePEc ecm:emetrp:v61y1993i3p523-45). Cited for: self-confirming equilibrium concept. Content level: concept attribution only.
- EvansHonkapohja2001: Princeton UP 2001, ISBN 9780691049212 (press.princeton.edu). Cited for: adaptive learning in macroeconomics, corpus attribution only.
- ChoWilliamsSargent2002: REStud 69(1):1-40 (RePEc oup:restud:v69y2002i1p1-40). Cited for: escape dynamics concept attribution only.
- BoydRicherson1985: Univ. of Chicago Press 1985, ISBN 9780226069333 (press/record pages). Cited for: conformist transmission sustaining maladaptive traditions, concept attribution only.

## I015 additions (verified 2026-11-04; colleague-feedback integration)
- AxelrodHamilton1981: Science 211(4489):1390-1396 (ADS bibcode 1981Sci...211.1390A confirms vol/start page; PubMed 7466396). Concept attribution: reputation/cooperation.
- PescetelliYeung2021: JEP:General 150(3):507-526, doi 10.1037/xge0000960 (publisher record). Confidence-weighted advice taking / trust formation.
- PescetelliHauperichYeung2021: Cognition 215:104810, doi 10.1016/j.cognition.2021.104810. Confidence and advice seeking.
- Wittmann2016: Neuron 91(2):482-493, doi 10.1016/j.neuron.2016.06.022 (PMC4961240). Self-other mergence in frontal cortex.
- Wittmann2025: Nature 641:707-717, doi 10.1038/s41586-025-08705-9 (publisher page). dmPFC basis functions for social decisions.
- Lefebvre2017: Nat Hum Behav 1:0067, doi 10.1038/s41562-017-0067 (publisher page). Optimistic RL / asymmetric learning rates.
- CazeVanDerMeer2013: Biol Cybern 107(6):711-719, doi 10.1007/s00422-013-0571-5 (Springer page). Normative account of differential learning rates.
All content-level claims limited to topic attribution; no internal theorem/figure numbers cited.

## I016 additions (verified 2026-11-04; Manohar-coauthored lesion papers)
- Lockwood2024: Nat Hum Behav 8(7):1403-1416, doi 10.1038/s41562-024-01899-4 (Birmingham Pure record + PMC11272586). vmPFC necessary for prosocial motivation.
- Gueguen2025: Brain 148(10):3537-3550, doi 10.1093/brain/awaf056 (Birmingham Pure record). vmPFC lesions disrupt learning to reward others.
Both concept attribution only.

## I018 additions (verified 2026-11-05)
- Muller2013: EM&S 48:37-48 (UFZ publisher-linked page). ODD+D protocol.
- Grimm2020: JASSS 23(2):7, doi 10.18564/jasss.4259 (USGS record + RePEc). ODD second update.

## I019 additions (verified 2026-11-05; echo-chamber positioning)
- Nguyen2020: Episteme 17(2):141-161 (PhilArchive record + Cambridge issue). Bubble/echo-chamber distinction (omission vs discrediting).
- Bail2018: PNAS 115(37):9216-9221, doi 10.1073/pnas.1804840115 (Duke Scholars). Cross-cutting exposure can backfire.
- Cinelli2021: PNAS 118(9):e2023301118, doi 10.1073/pnas.2023301118 (Recercat record). Echo-chamber measurement/homophilous structure.
All concept attribution only.
