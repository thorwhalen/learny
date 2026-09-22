"""Tests for the diagnostics: separation, calibration, and label projection.

The finding these exist to protect: when every item carries many labels at once, the
labels cannot be told apart, and the model must be able to *say* so. All data here is
synthetic.
"""

import math
import random

import pytest

from learny.tracing import (
    Item,
    LearnerModel,
    RaschEstimator,
    Response,
    calibration,
    label_separation,
    prequential,
    restrict_labels,
)
from learny.tracing.diagnostics import CalibrationReport
from learny.tracing.estimators import expit, logit

LABELS = [f"l{i}" for i in range(9)]


def _simulate(items, true_dev, *, n, seed=0, student="s"):
    """Responses from a synthetic student with global skill 0 and given label deviations."""
    rng = random.Random(seed)
    keys = sorted(items)
    out = []
    for _ in range(n):
        item = items[rng.choice(keys)]
        w = item.weights
        dev = sum(true_dev[k] * v for k, v in w.items()) / (sum(w.values()) or 1.0)
        p = expit(dev - logit(item.difficulty))
        out.append(
            Response(student, item.id, "correct" if rng.random() < p else "wrong")
        )
    return out


@pytest.fixture
def true_dev():
    # Two labels genuinely strong, two genuinely weak, the rest average.
    dev = {label: 0.0 for label in LABELS}
    dev.update(l0=-2.0, l1=-2.0, l2=2.0, l3=2.0)
    return dev


def _model(items, responses):
    model = LearnerModel(items=items, log={}, estimates={})
    model.record_many(responses)
    return model


class TestSeparation:
    def test_every_label_on_every_item_is_indistinguishable(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=tuple(LABELS), difficulty=0.5)
            for i in range(40)
        }
        model = _model(items, _simulate(items, true_dev, n=300))
        sep = model.separation("s")
        assert sep.n_labels == 9
        assert not sep.distinguishable
        assert sep.separation < 1.0

    def test_one_label_per_item_separates(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=(LABELS[i % 9],), difficulty=0.5)
            for i in range(45)
        }
        model = _model(items, _simulate(items, true_dev, n=600))
        sep = model.separation("s")
        assert sep.distinguishable
        assert sep.reliability >= 0.8

    def test_no_evidence_is_not_distinguishable(self):
        sep = label_separation(RaschEstimator().init())
        assert sep.n_labels == 0
        assert not sep.distinguishable
        assert sep.separation == 0.0

    def test_a_single_label_is_never_distinguishable(self):
        state = {"labels": {"a": {"mu": 3.0, "var": 0.01, "n": 50}}}
        assert not label_separation(state).distinguishable

    def test_min_n_excludes_thin_labels(self):
        state = {
            "labels": {
                "a": {"mu": 1.0, "var": 0.01, "n": 50},
                "b": {"mu": -1.0, "var": 0.01, "n": 50},
                "c": {"mu": 0.0, "var": 0.2, "n": 1},
            }
        }
        assert label_separation(state, min_n=5).n_labels == 2


class TestCredibleWeakest:
    def test_default_is_unchanged(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=tuple(LABELS), difficulty=0.5)
            for i in range(40)
        }
        model = _model(items, _simulate(items, true_dev, n=100))
        assert len(model.weakest("s", n=9)) == 9

    def test_noise_yields_no_credible_weakness(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=tuple(LABELS), difficulty=0.5)
            for i in range(40)
        }
        model = _model(items, _simulate(items, true_dev, n=100))
        assert model.weakest("s", n=9, credible_below=1.0) == []

    def test_real_weaknesses_are_found(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=(LABELS[i % 9],), difficulty=0.5)
            for i in range(45)
        }
        model = _model(items, _simulate(items, true_dev, n=600))
        found = {m.label for m in model.weakest("s", n=9, credible_below=1.0)}
        assert {"l0", "l1"} <= found
        assert not found & {"l2", "l3"}


class TestCalibration:
    def test_prequential_predicts_before_it_updates(self):
        items = {"q": Item("q", labels=("x",), difficulty=0.5)}
        est = RaschEstimator()
        stream = list(
            prequential([Response("a", "q", "correct")] * 3, items=items, estimator=est)
        )
        assert stream[0][1] == pytest.approx(0.5)
        assert stream[0][1] < stream[1][1] < stream[2][1]

    def test_a_well_specified_model_is_calibrated(self, true_dev):
        items = {
            f"q{i}": Item(
                f"q{i}", labels=(LABELS[i % 9],), difficulty=0.2 + 0.6 * (i % 5) / 4
            )
            for i in range(45)
        }
        log = {
            f"s{k}": _simulate(items, true_dev, n=200, seed=k, student=f"s{k}")
            for k in range(5)
        }
        report = calibration(log, items=items, estimator=RaschEstimator())
        assert report.n == 1000
        assert report.log_loss < report.base_log_loss
        assert report.ece < 0.06
        assert sum(b.n for b in report.bins) == report.n

    def test_skips_are_replayed_but_not_scored(self):
        items = {"q": Item("q", labels=("x",), difficulty=0.5)}
        log = {"a": [Response("a", "q", "correct"), Response("a", "q", "skipped")]}
        assert calibration(log, items=items, estimator=RaschEstimator()).n == 1

    def test_empty_log_is_nan_not_an_error(self):
        report = CalibrationReport.from_pairs([])
        assert report.n == 0 and math.isnan(report.log_loss) and report.bins == ()

    def test_bad_bin_count_is_loud(self):
        with pytest.raises(ValueError):
            CalibrationReport.from_pairs([(0.5, 1)], n_bins=0)

    def test_model_calibration_reads_the_log_without_touching_the_cache(self, tmp_path):
        from learny.tracing import ResponseLog

        items = {"q": Item("q", labels=("x",), difficulty=0.5)}
        model = LearnerModel(
            items=items, log=ResponseLog(rootdir=tmp_path), estimates={}
        )
        for outcome in ("correct", "wrong", "correct"):
            model.record("a", "q", outcome)
        model.record("b", "q", "wrong")
        before = {k: dict(v) for k, v in model.estimates.items()}
        report = model.calibration()
        assert report.n == 4
        assert model.estimates == before
        assert model.calibration(["b"]).n == 1

    def test_students_are_replayed_independently(self):
        items = {"q": Item("q", labels=("x",), difficulty=0.5)}
        a = [Response("a", "q", "correct")] * 5
        b = [Response("b", "q", "wrong")]
        alone = calibration({"b": b}, items=items, estimator=RaschEstimator())
        both = calibration(
            {"a": a, "b": b}, items=items, estimator=RaschEstimator(), students=["b"]
        )
        assert alone == both


class TestRestrictLabels:
    def test_projection_keeps_weights_and_difficulty(self):
        bank = {"q": Item("q", labels={"a": 1.0, "b": 0.5}, difficulty=0.3)}
        out = restrict_labels(bank, keep={"b"})
        assert out["q"].weights == {"b": 0.5}
        assert out["q"].difficulty == 0.3

    def test_does_not_mutate_the_bank(self):
        bank = {"q": Item("q", labels=("a", "b"))}
        restrict_labels(bank, keep={"a"})
        assert bank["q"].weights == {"a": 1.0, "b": 1.0}

    def test_projection_improves_separation(self, true_dev):
        # Items tagged with a "topic" label and many co-occurring noise labels.
        rng = random.Random(1)
        items = {}
        for i in range(45):
            noise = tuple(rng.sample([f"n{j}" for j in range(8)], 6))
            items[f"q{i}"] = Item(
                f"q{i}", labels=(LABELS[i % 9],) + noise, difficulty=0.5
            )
        dev = dict(true_dev, **{f"n{j}": 0.0 for j in range(8)})
        responses = _simulate(items, dev, n=400)
        wide = _model(items, responses).separation("s")
        narrow_items = restrict_labels(items, keep=set(LABELS))
        narrow = _model(narrow_items, responses).separation("s")
        assert narrow.separation > 2 * wide.separation
