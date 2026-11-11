"""Invariants of the I040 yoked-pair simulator (run from the repository root)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import estimand_core_I038 as ec  # noqa: E402
import twins_I040 as tw  # noqa: E402

PT = {p[0]: p for p in ec.GATE_POINTS}


def test_reference_monotonicity_holds_whenever_its_hypotheses_do():
    b = tw.twins(PT['P1'], 3000, np.random.default_rng(1))
    hyp = b['ord_ok'] & b['same_out']
    assert hyp.sum() > 300 and b['concl'][hyp].all()            # Lean T13, numerically


def test_choice_free_pairs_share_every_outcome():
    b = tw.twins(PT['P1'], 1500, np.random.default_rng(2), choice_free=True)
    assert b['same_out'].all() and b['same_choice'].all()


def test_same_outcomes_exactly_when_same_tickets():
    b = tw.twins(PT['P4'], 1500, np.random.default_rng(3))
    assert (b['same_out'] <= b['same_choice']).all()            # same outcomes imply same tickets here
    assert 0.2 < b['same_choice'].mean() < 0.95


def test_legitimacy_levels_match_the_task_generator():
    b = tw.twins(PT['P1'], 6000, np.random.default_rng(4))
    assert abs(b['L']['HIGH'][:, -1].mean() - 0.110) < 0.03 and abs(b['L']['LOW'][:, -1].mean() - 0.869) < 0.03


def test_ratings_are_on_the_scale():
    r = tw.rating(np.linspace(0, 1, 50), np.random.default_rng(5))
    assert r.min() >= 0 and r.max() <= 100 and np.all(r % 5 == 0)
