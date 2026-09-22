"""Tests for the diagnostics: separation, calibration, and label projection.

The finding these exist to protect: when every item carries many labels at once, the
labels cannot be told apart, and the model must be able to *say* so. All data here is
synthetic.
"""

import math
import random

import pytest

from learny.tracing import (
    DEFAULT_CREDIBLE_BELOW,
    Item,
    LearnerModel,
    Mastery,
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
    def test_none_ranks_every_label_with_evidence(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=tuple(LABELS), difficulty=0.5)
            for i in range(40)
        }
        model = _model(items, _simulate(items, true_dev, n=100))
        assert len(model.weakest("s", n=9, credible_below=None)) == 9

    def test_the_gate_is_the_default(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=tuple(LABELS), difficulty=0.5)
            for i in range(40)
        }
        model = _model(items, _simulate(items, true_dev, n=100))
        assert model.weakest("s", n=9) == model.weakest(
            "s", n=9, credible_below=DEFAULT_CREDIBLE_BELOW
        )
        assert model.weakest("s", n=9).reason == "no_credible_weakness"

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
        # The truth lives in one "topic" label per item; six co-occurring tags are noise.
        # Projecting onto the topics concentrates each response's evidence on them.
        rng = random.Random(1)
        items = {}
        for i in range(45):
            noise = tuple(rng.sample([f"n{j}" for j in range(8)], 6))
            items[f"q{i}"] = Item(
                f"q{i}", labels=(LABELS[i % 9],) + noise, difficulty=0.5
            )
        narrow_items = restrict_labels(items, keep=set(LABELS))
        for seed in range(3):
            responses = _simulate(narrow_items, true_dev, n=400, seed=seed)
            wide = _model(items, responses).separation("s")
            narrow = _model(narrow_items, responses).separation("s")
            assert narrow.distinguishable
            assert narrow.separation > wide.separation

    def test_a_single_string_is_refused(self):
        # A str is a Collection of characters: keep="topic:x" would keep nothing.
        bank = {"q": Item("q", labels=("topic:x", "t"))}
        with pytest.raises(TypeError, match="single string"):
            restrict_labels(bank, keep="topic:x")

    def test_item_fields_survive(self):
        bank = {"q": Item("q", labels=("a", "b"), difficulty=0.4, meta={"src": "x"})}
        out = restrict_labels(bank, keep={"a"})["q"]
        assert (out.id, out.difficulty, dict(out.meta)) == ("q", 0.4, {"src": "x"})


class TestSeparationUndoesShrinkage:
    """The Rasch formula needs unshrunk measures; the state holds posteriors."""

    PRIOR = 0.25

    def _posterior(self, x, s2):
        """The normal-normal posterior a ``N(0, PRIOR)`` prior makes of measure ``x``."""
        var = 1.0 / (1.0 / self.PRIOR + 1.0 / s2)
        return {"mu": x * var / s2, "var": var, "n": 10}

    def test_recovers_the_likelihood_measures_exactly(self):
        xs, s2 = [-1.5, -0.5, 0.0, 0.5, 1.5], 0.1
        state = {"labels": {f"l{i}": self._posterior(x, s2) for i, x in enumerate(xs)}}
        sep = label_separation(state, label_prior_var=self.PRIOR)
        assert sep.rmse == pytest.approx(math.sqrt(s2))
        mean = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))
        assert sep.observed_sd == pytest.approx(sd)

    def test_shrunk_reading_calls_separable_labels_noise(self):
        # True G = sqrt(2.5 / 0.4 - 1) ~ 2.3: separable. Read without undoing the
        # prior's shrinkage, the same state looks like noise.
        xs, s2 = [-2.0, -1.0, 0.0, 1.0, 2.0], 0.4
        state = {"labels": {f"l{i}": self._posterior(x, s2) for i, x in enumerate(xs)}}
        assert label_separation(state, label_prior_var=self.PRIOR).distinguishable
        assert not label_separation(state, label_prior_var=None).distinguishable

    def test_a_label_with_only_its_prior_is_left_out(self):
        state = {
            "labels": {
                "a": self._posterior(1.0, 0.05),
                "b": self._posterior(-1.0, 0.05),
                "c": {"mu": 0.0, "var": self.PRIOR, "n": 1},  # e.g. forgotten back
            }
        }
        assert label_separation(state, label_prior_var=self.PRIOR).n_labels == 2

    def test_no_true_spread_is_not_distinguishable(self):
        items = {
            f"q{i}": Item(f"q{i}", labels=(LABELS[i % 9],), difficulty=0.5)
            for i in range(45)
        }
        flat = {label: 0.0 for label in LABELS}
        for seed in range(10):
            model = _model(items, _simulate(items, flat, n=300, seed=seed))
            assert not model.separation("s").distinguishable

    def test_model_uses_its_own_estimator_prior(self, true_dev):
        items = {
            f"q{i}": Item(f"q{i}", labels=(LABELS[i % 9],), difficulty=0.5)
            for i in range(45)
        }
        est = RaschEstimator(label_prior_var=1.0)
        model = LearnerModel(items=items, estimator=est, log={}, estimates={})
        model.record_many(_simulate(items, true_dev, n=300))
        state = model.estimates["s"]
        assert model.separation("s") == label_separation(state, label_prior_var=1.0)


class TestWeakestContract:
    """The concerns raised on #7 before the gate became the default."""

    @pytest.fixture
    def split_items(self):
        return {
            f"q{i}": Item(f"q{i}", labels=("area" if i % 2 else "sums",))
            for i in range(40)
        }

    def test_negative_z_is_refused(self, split_items):
        model = _model(split_items, [])
        with pytest.raises(ValueError, match="credible_below"):
            model.weakest("s", credible_below=-0.5)
        with pytest.raises(ValueError):
            model.weakest("s", credible_below=float("nan"))

    def test_zero_z_is_the_posterior_mean_below_zero(self, split_items):
        model = _model(split_items, [])
        for i in range(40):
            model.record("s", f"q{i}", "wrong" if i % 2 else "correct")
        assert [m.label for m in model.weakest("s", credible_below=0.0)] == ["area"]

    def test_no_evidence_says_so(self, split_items):
        result = _model(split_items, []).weakest("s")
        assert result == [] and result.reason == "no_evidence"
        assert _model(split_items, []).weakest("s", credible_below=None).reason == (
            "no_evidence"
        )

    def test_labels_level_with_the_student_are_no_credible_weakness(self, split_items):
        model = _model(split_items, [])
        for i in range(40):  # half right on each label: nothing stands out
            model.record("s", f"q{i}", "correct" if i % 4 < 2 else "wrong")
        result = model.weakest("s")
        assert result == [] and result.reason == "no_credible_weakness"
        assert len(model.weakest("s", credible_below=None)) == 2

    def test_a_non_empty_result_has_no_reason(self, split_items):
        model = _model(split_items, [])
        for i in range(40):
            model.record("s", f"q{i}", "wrong" if i % 2 else "correct")
        result = model.weakest("s")
        assert [m.label for m in result] == ["area"] and result.reason is None
        assert isinstance(result, list)

    def test_default_estimator_fills_the_deviation(self, split_items):
        model = _model(split_items, [])
        model.record("s", "q1", "wrong")
        m = model.mastery("s")["area"]
        state = model.estimates["s"]
        assert m.deviation.mu == pytest.approx(state["labels"]["area"]["mu"])
        assert m.deviation.var == pytest.approx(state["labels"]["area"]["var"])
        assert m.mu == pytest.approx(state["global"]["mu"] + m.deviation.mu)

    def test_an_estimator_without_deviation_is_an_error_not_silence(self, split_items):
        class NoDeviation(RaschEstimator):
            def mastery(self, state):
                return {
                    k: Mastery(v.label, v.skill, v.prior_var)
                    for k, v in super().mastery(state).items()
                }

        model = LearnerModel(
            items=split_items, estimator=NoDeviation(), log={}, estimates={}
        )
        model.record("s", "q1", "wrong")
        with pytest.raises(TypeError, match="deviation"):
            model.weakest("s")
        assert [m.label for m in model.weakest("s", credible_below=None)] == ["area"]
        # no evidence at all is still an answer, not an error
        assert model.weakest("t").reason == "no_evidence"
