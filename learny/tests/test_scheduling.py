"""Tests for learny.scheduling and learny.distractors (ported from kodokan's learning.py)."""

import random

import pytest

from learny import scheduling as S
from learny._sampling import SECONDS_PER_DAY
from learny.distractors import confusion_weights, pick_distractors
from learny.tracing import Item, Response

NOW = 1_782_000_000.0
SET = ["a", "b", "c", "d", "e", "f"]


def _rec(item, correct, *, chosen=None, days_ago=0.0, rt=2000, student="ada", **meta):
    chosen = chosen if chosen is not None else (item if correct else "x")
    return Response(
        student, item, "correct" if correct else "wrong",
        at=NOW - days_ago * SECONDS_PER_DAY,
        meta={"chosen": chosen, "shown": [item, "x", "y", "z"], "rt_ms": rt, "pattern": "M1", **meta},
    )


def _picks(strategy, log, candidates=SET, n=60, **kw):
    return [strategy.next_selection(log, candidates, now=NOW, rng=random.Random(i), **kw) for i in range(n)]


@pytest.mark.parametrize("key", list(S.STRATEGIES))
def test_each_strategy_returns_a_valid_round(key):
    strategy = S.make_strategy(key)
    log = [_rec("a", False, chosen="b", days_ago=1), _rec("c", True, days_ago=1)]
    sel = strategy.next_selection(log, SET, now=NOW, rng=random.Random(0))
    assert sel.target in SET and sel.target in sel.options
    assert len(sel.options) == len(set(sel.options)) == 4
    assert set(sel.options) <= set(SET)


@pytest.mark.parametrize("key", list(S.STRATEGIES))
def test_each_strategy_handles_a_cold_start(key):
    sel = S.make_strategy(key).next_selection([], SET, now=NOW, rng=random.Random(0))
    assert sel.target in SET


def test_registry_and_default():
    keys = {s["key"] for s in S.list_strategies()}
    assert {"uniform_random", "leitner", "sm2", "confusion_weighted", "fsrs_lite", "weakest"} == keys
    assert S.DEFAULT_STRATEGY == "confusion_weighted"
    assert S.make_strategy().key == "confusion_weighted"
    with pytest.raises(ValueError, match="known: uniform_random"):
        S.make_strategy("nonexistent")


def test_empty_candidates_is_an_error():
    with pytest.raises(ValueError, match="at least one candidate"):
        S.make_strategy().next_selection([], [], now=NOW)


def test_uniform_never_repeats_the_last_item():
    strategy = S.make_strategy("uniform_random")
    assert "a" not in {s.target for s in _picks(strategy, [_rec("a", True)], n=50)}


def test_confusion_weights_follow_wrong_picks_only():
    log = [_rec("a", False, chosen="b", days_ago=1)] * 3 + [_rec("a", True, days_ago=1)]
    directed = confusion_weights(log, now=NOW, symmetric=False)
    assert directed["a"]["b"] > 0 and "b" not in directed
    assert confusion_weights(log, now=NOW)["b"]["a"] == directed["a"]["b"]


def test_confusion_weights_decay_and_partial_credit():
    fresh = confusion_weights([_rec("a", False, chosen="b")], now=NOW, symmetric=False)["a"]["b"]
    old = confusion_weights([_rec("a", False, chosen="b", days_ago=7)], now=NOW, symmetric=False)["a"]["b"]
    assert old == pytest.approx(fresh / 2)
    near = Response("ada", "a", "wrong", at=NOW, meta={"chosen": "b"}, score=3, max_score=4)
    assert confusion_weights([near], now=NOW, symmetric=False)["a"]["b"] == 0.25  # the floor


def test_confusion_weighted_targets_the_confused_item_and_its_confuser():
    strategy = S.make_strategy("confusion_weighted", epsilon_explore=0.0)
    log = [_rec("a", False, chosen="b", days_ago=1) for _ in range(6)]
    log += [_rec(k, True, days_ago=1) for k in ("c", "d", "e", "f") for _ in range(2)]
    sels = _picks(strategy, log)
    targets = [s.target for s in sels]
    assert targets.count("a") > targets.count("c")
    assert any("b" in s.options for s in sels if s.target == "a")


def test_known_similarity_survives_a_logged_confusion():
    """A logged confusion adds to the caller's look-alikes; it never replaces them."""
    looks_alike = {"c": {"d": 10.0}}
    strategy = S.make_strategy("confusion_weighted", epsilon_explore=0.0)
    log = [_rec("a", False, chosen="b", days_ago=1)]
    sels = _picks(strategy, log, ["c", "d", "e", "f", "g"], n=40, similarity=looks_alike)
    c_rounds = [s for s in sels if s.target == "c"]
    assert c_rounds and all("d" in s.options for s in c_rounds)


def test_pick_distractors_tops_up_and_never_returns_the_target():
    out = pick_distractors("a", ["a", "b", "c", "d"], n=3, similarity={"a": {"b": 1.0}}, rng=random.Random(0))
    assert sorted(out) == ["b", "c", "d"]
    assert pick_distractors("a", ["a", "b", "c"], n=2, similarity={"a": {"b": 1.0}}, rng=random.Random(0), top_up=False) == ["b"]


def test_leitner_promotes_and_demotes():
    strategy = S.make_strategy("leitner")
    log = [_rec("a", False, days_ago=0.01) for _ in range(3)] + [_rec("b", True, days_ago=0.01) for _ in range(3)]
    boxes = strategy.boxes(log)
    assert boxes["a"][0] == 1 and boxes["b"][0] == 4
    with pytest.raises(ValueError, match="demotion"):
        S.Leitner(demotion="drop")


def test_a_skip_is_not_a_lapse():
    log = [_rec("a", True), Response("ada", "a", "skipped", at=NOW)]
    assert S.make_strategy("leitner").boxes(log)["a"][0] == 2
    assert S.make_strategy("fsrs_lite").stability(log)["a"][0] == 2.0


def test_sm2_and_fsrs_interleave():
    log = [_rec(k, True, days_ago=2) for k in ("a", "b", "c", "d")]
    for key in ("sm2", "fsrs_lite"):
        picks = {s.target for s in _picks(S.make_strategy(key), log, ["a", "b", "c", "d"], n=30)}
        assert len(picks) > 1, f"{key} repeats a single item"


def test_sm2_grades_by_response_time_and_asks_unseen_first():
    strategy = S.make_strategy("sm2")
    assert strategy.grade(_rec("a", True, rt=1000)) == 5
    assert strategy.grade(_rec("a", True, rt=12000)) == 3
    assert strategy.grade(_rec("a", False, timed_out=True)) == 0
    near = Response("ada", "a", "wrong", meta={"chosen": "b"}, score=1, max_score=4)
    assert strategy.grade(near) == 2
    picks = {s.target for s in _picks(strategy, [_rec("a", True, days_ago=0.01)], ["a", "b", "c", "d"], n=20)}
    assert "a" not in picks


def test_weakest_asks_about_the_weak_label():
    items = {k: Item(k, labels=("kata",) if k in "ab" else ("words",), difficulty=0.5) for k in SET}
    log = [_rec(k, k not in "ab", days_ago=1) for k in SET for _ in range(4)]
    strategy = S.make_strategy("weakest", items=items, weakest_options={"multiplicity": "none"})
    targets = [s.target for s in _picks(strategy, log, n=30)]
    assert sum(t in "ab" for t in targets) > len(targets) / 2


def test_other_students_responses_do_not_leak_into_confusions():
    """Callers pass one learner's responses; the strategy reads only what it is given."""
    log = [_rec("a", False, chosen="b", student="bo")]
    mine = [r for r in log if r.student == "ada"]
    assert S.make_strategy().distractor_similarity(mine, now=NOW) is None


def test_baselines_keep_no_memory_of_confusions():
    log = [_rec("a", False, chosen="b")]
    for key in ("uniform_random", "leitner", "sm2"):
        assert S.make_strategy(key).distractor_similarity(log, now=NOW) is None
    assert S.make_strategy("uniform_random", learner_confusions=True).distractor_similarity(log, now=NOW)


def test_near_miss_credit_from_meta():
    """A float near-miss credit in meta, not an ordered score, drives SM-2 and the weights."""
    near = _rec("a", False, chosen="b", credit=0.4)
    assert S.make_strategy("sm2").grade(near) == 2
    assert confusion_weights([near], now=NOW, symmetric=False)["a"]["b"] == pytest.approx(0.6)


def test_list_strategies_is_json_ready():
    import json

    listed = S.list_strategies()
    json.dumps(listed)
    leitner = next(s for s in listed if s["key"] == "leitner")
    assert {"name": "intervals", "type": "tuple", "default": [1, 2, 4, 8, 16]} in leitner["params"]
