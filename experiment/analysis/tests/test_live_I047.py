"""KGi-DISS-I047, gate G18(a): the informed-share option of the pair simulation leaves every earlier
result where it was (run from the repository root).

The fingerprints were computed on the tree of 569c3f8, before the option existed, with numpy 2.5.3. They
are byte-level: if another numpy changes a floating-point result in the last place they fail, and the
equalities tested below them still say what matters."""
import hashlib
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import estimand_core_I038 as ec  # noqa: E402
import twins_I040 as tw  # noqa: E402

PT = {p[0]: p for p in ec.GATE_POINTS}
BEFORE = [('P1', {}, '538fad7fca73a408'),
          ('P4', dict(same_person=False, indep_choice=True), '37fba900c89ba3f7'),
          ('P1', dict(choice_free=True), '84d36f5505f20298'),
          ('P4', dict(same_person=False, indep_choice=True, choice_free=True), '302e8b5cf24cf8ff')]


def digest(b):
    h = hashlib.sha256()
    for key in ('L', 'A', 'wins'):
        for arm in tw.ARMS:
            h.update(np.ascontiguousarray(b[key][arm]).tobytes())
    h.update(b['same_choice'].tobytes())
    h.update(b['same_out'].tobytes())
    return h.hexdigest()[:16]


def same(a, b):
    return all(np.array_equal(a[key][arm], b[key][arm]) for key in ('L', 'A', 'wins') for arm in tw.ARMS) \
        and np.array_equal(a['same_choice'], b['same_choice']) and np.array_equal(a['same_out'], b['same_out'])


@pytest.mark.parametrize('point,kw,pin', BEFORE)
def test_without_the_option_the_simulation_is_the_one_before_it(point, kw, pin):
    assert digest(tw.twins(PT[point], 400, np.random.default_rng(47), **kw)) == pin


def test_nobody_informed_is_the_default():
    kw = dict(same_person=False, indep_choice=True)
    nobody = {a: np.zeros(600, bool) for a in tw.ARMS}
    assert same(tw.twins(PT['P4'], 600, np.random.default_rng(5), **kw),
                tw.twins(PT['P4'], 600, np.random.default_rng(5), informed=nobody, **kw))


def test_everybody_informed_is_the_choice_free_case():
    kw = dict(same_person=False, indep_choice=True)
    everybody = {a: np.ones(600, bool) for a in tw.ARMS}
    a = tw.twins(PT['P4'], 600, np.random.default_rng(6), choice_free=True, **kw)
    b = tw.twins(PT['P4'], 600, np.random.default_rng(6), informed=everybody, **kw)
    assert same(a, b) and b['same_choice'].all() and b['same_out'].all()


def test_an_informed_member_fills_at_the_better_goods_rate_and_the_others_below_it():
    n = 6000
    informed = {'HIGH': np.arange(n) % 2 == 0, 'LOW': np.arange(n) % 3 == 0}
    b = tw.twins(PT['P1'], n, np.random.default_rng(7), same_person=False, indep_choice=True, informed=informed)
    for arm in tw.ARMS:
        dep = b['wins'][arm][:, tw.R1:].mean(1) / tw.K              # filled share over the deprivation rounds
        assert abs(dep[informed[arm]].mean() - tw.PH2[0]) < 0.004   # the better good's chance
        assert dep[~informed[arm]].mean() < tw.PH2[0] - 0.01        # the others spend rounds on the worse good
