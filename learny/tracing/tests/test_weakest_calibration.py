"""Tests for the null-calibrated gate of ``weakest()`` (#22) and ``Mastery.null_var``.

All fixtures here are synthetic. Real learner data is personal data and never enters
this repository, which is public.
"""

import math
import random

import pytest

from learny.tracing import Item, LearnerModel, Outcome, RaschEstimator, Response

WEEK = 7 * 24 * 3600.0


def _bank(n_labels, difficulty=0.5):
    return {
        f"l{j}": Item(f"l{j}", labels=(f"l{j}",), difficulty=difficulty)
        for j in range(n_labels)
    }


def _student(
    rng, n_labels, n_responses, *, weakness=0.0, spacing=WEEK, estimator=None,
    difficulty=0.5, skip=0.0,
):
    """One simulated student: global skill ~ N(0, 1), a real deviation on l0, and
    interior skips at random with probability ``skip``."""
    theta = rng.gauss(0, 1)
    model = LearnerModel(
        items=_bank(n_labels, difficulty),
        estimator=estimator or RaschEstimator(), log={}, estimates={},
    )
    b = math.log(difficulty / (1 - difficulty))
    for i in range(n_responses):
        label = f"l{i % n_labels}"
        p = 1 / (1 + math.exp(-(theta + (weakness if label == "l0" else 0.0) - b)))
        outcome = (
            "skipped" if rng.random() < skip
            else "correct" if rng.random() < p else "wrong"
        )
        model.record("s", label, outcome, at=i * spacing)
    return model


class TestNullVariance:
    def test_a_posterior_mean_wanders_less_than_its_posterior_sd(self):
        model = _student(random.Random(0), 3, 18)
        for m in model.mastery("s").values():
            assert 0.0 < m.null_var < m.deviation.var

    def test_forgetting_reopens_the_posterior_but_not_the_null_spread(self):
        """A stale label's mean has not moved, so its sampling spread has not either:
        the identity #11 relied on (null = v - v^2 / tau^2) is not used."""
        est = RaschEstimator(forget_per_week=0.1)
        state = est.init()
        a, b = Item("a", labels=("a",), difficulty=0.5), Item("b", labels=("b",), difficulty=0.5)
        for i in range(6):
            state = est.observe(state, Response("s", "a", "wrong", at=i * 3600.0), a)
        before = est.mastery(state)["a"]
        state = est.observe(state, Response("s", "b", "correct", at=52 * WEEK), b)
        after = est._labels(state)
        assert dict(after)["a"].null_var == pytest.approx(before.null_var)

    def test_a_state_written_before_tracking_falls_back_to_the_posterior_gate(self):
        """No ``nv``: no null_var, and the calibrated gate is exactly Bonferroni."""
        model = _student(random.Random(4), 6, 60, weakness=-2.0)
        state = model.estimates["s"]
        for entry in state["labels"].values():
            entry.pop("nv")
        assert all(m.null_var is None for m in model.mastery("s").values())
        assert model.weakest("s", n=6, multiplicity="calibrated") == model.weakest(
            "s", n=6, multiplicity="bonferroni"
        )

    def test_such_a_label_starts_tracking_at_its_posterior_variance(self):
        est = RaschEstimator()
        old = {
            "global": {"mu": -0.4, "var": 0.5, "n": 6, "t": None},
            "labels": {"a": {"mu": -0.2, "var": 0.2, "n": 3, "t": None}},
        }
        new = est.observe(old, Response("s", "q", Outcome.WRONG), Item("q", labels=("a",)))
        assert 0.0 < est.mastery(new)["a"].null_var <= 0.2

    def test_a_student_who_mostly_gets_it_right_has_a_skewed_null(self):
        """A rare wrong answer is a large drop: the null's lower tail is heavy."""
        model = _student(random.Random(2), 3, 18, difficulty=0.05)
        assert all(m.null_k3 < 0 for m in model.mastery("s").values())

    def test_a_skip_adds_sampling_spread(self):
        """Whether a student skips is random too, so a skip is not noise-free."""
        est = RaschEstimator()
        item = Item("a", labels=("a",), difficulty=0.5)
        answered = est.observe(est.init(), Response("s", "a", "correct"), item)
        both = est.observe(answered, Response("s", "a", "skipped"), item)
        assert both["labels"]["a"]["nv"] > answered["labels"]["a"]["nv"]
        assert both["labels"]["a"]["nk3"] < 0  # a skip only ever pulls the label down

    def test_the_elo_gain_does_not_track_it(self):
        model = _student(random.Random(1), 3, 18, estimator=RaschEstimator(gain="elo"))
        assert all(m.null_var is None for m in model.mastery("s").values())


class TestCalibratedGate:
    """The acceptance of #22, at a size a test suite can afford (150 students per cell;
    the full grid, 1000 per cell, is in the PR)."""

    STUDENTS = 150

    def _rates(self, n_labels, n_responses, *, weakness, seed):
        rng = random.Random(seed)
        hits = {"none": 0, "bonferroni": 0, "calibrated": 0}
        for _ in range(self.STUDENTS):
            model = _student(rng, n_labels, n_responses, weakness=weakness)
            for mode in hits:
                flagged = {m.label for m in model.weakest("s", n=n_labels, multiplicity=mode)}
                hits[mode] += ("l0" in flagged) if weakness else bool(flagged)
        return {mode: h / self.STUDENTS for mode, h in hits.items()}

    @pytest.mark.parametrize("n_labels,n_responses", [(3, 18), (6, 60)])
    def test_false_flags_near_target_and_power_restored(self, n_labels, n_responses):
        false = self._rates(n_labels, n_responses, weakness=0.0, seed=1)
        found = self._rates(n_labels, n_responses, weakness=-2.0, seed=2)
        assert false["calibrated"] <= 0.16 + 0.08  # target 1 - Phi(1), 2.5 MC sd
        assert found["calibrated"] > 2 * found["bonferroni"]
        assert found["calibrated"] >= found["none"] - 0.1

    @pytest.mark.parametrize(
        "n_labels,n_responses,kw",
        [
            (20, 40, {"difficulty": 0.05}),  # mostly right, sparse: was 0.64 (#34 review)
            (6, 60, {"skip": 0.3}),  # random skips: was 0.22
            (10, 10, {"difficulty": 0.03}),  # one response per label: was 0.30
        ],
    )
    def test_false_flags_stay_near_target_off_the_grid(self, n_labels, n_responses, kw):
        rng = random.Random(5)
        flagged = sum(
            bool(_student(rng, n_labels, n_responses, **kw).weakest("s", n=n_labels))
            for _ in range(self.STUDENTS)
        )
        assert flagged / self.STUDENTS <= 0.16 + 0.08

    def test_it_is_the_default(self):
        from learny.tracing import DEFAULT_MULTIPLICITY

        assert DEFAULT_MULTIPLICITY == "calibrated"


class TestSimulatedGate:
    """weakest(multiplicity="simulated"): the null replayed on the student's own record (#35)."""

    def test_it_finds_weaknesses_the_moment_correction_cannot(self):
        """Items the student nearly always gets right, three answers per label: the
        calibrated gate is cautious there (power ~0.03), the simulated one is not."""
        rng = random.Random(30)
        hits = {"calibrated": 0, "simulated": 0}
        false = 0
        for _ in range(60):
            weak = _student(rng, 3, 9, weakness=-2.0, difficulty=0.05)
            plain = _student(rng, 3, 9, difficulty=0.05)
            for mode in hits:
                hits[mode] += "l0" in {m.label for m in weak.weakest("s", n=3, multiplicity=mode,
                                                                     null_draws=100)}
            false += bool(plain.weakest("s", n=3, multiplicity="simulated", null_draws=100))
        assert hits["simulated"] >= 3 * hits["calibrated"] and hits["simulated"] >= 8
        assert false / 60 <= 0.16 + 0.12  # target 1 - Phi(1), 2.5 MC sd at 60 students

    def test_it_is_deterministic_for_a_record(self):
        model = _student(random.Random(31), 4, 16, weakness=-2.0)
        once = model.weakest("s", n=4, multiplicity="simulated", null_draws=50)
        assert model.weakest("s", n=4, multiplicity="simulated", null_draws=50) == once

    def test_an_estimator_that_cannot_redraw_is_refused(self):
        class NoRedraw(RaschEstimator):
            null_response = None

        model = _student(random.Random(32), 3, 9, estimator=NoRedraw())
        with pytest.raises(TypeError, match="null_response"):
            model.weakest("s", multiplicity="simulated")

    @pytest.mark.parametrize("bad", [0, -5, 2.5, True])
    def test_null_draws_must_be_a_positive_integer(self, bad):
        model = _student(random.Random(33), 3, 9)
        with pytest.raises(ValueError, match="null_draws"):
            model.weakest("s", multiplicity="simulated", null_draws=bad)

    def test_too_few_draws_for_the_alpha_is_refused(self):
        """alpha * (null_draws + 1) < 1 could only flag at 1/(draws+1) > alpha: refuse."""
        model = _student(random.Random(34), 3, 9)
        # credible_below=3 -> alpha ~0.00135, which needs about 740 draws
        with pytest.raises(ValueError, match="null_draws >= 740"):
            model.weakest("s", multiplicity="simulated", credible_below=3, null_draws=200)
        assert model.weakest(
            "s", multiplicity="simulated", credible_below=3, null_draws=740
        ) is not None

    def test_a_redraw_keeps_skips_and_the_shape_of_scores(self):
        from learny.tracing import PartialCreditEstimator

        rng = random.Random(34)
        est = PartialCreditEstimator()
        state = est.init()
        item = Item("q", labels=("a",), difficulty=0.5)
        skip = Response("s", "q", "skipped", at=1.0)
        assert est.null_response(state, skip, item, rng) is skip
        scored = Response("s", "q", "wrong", at=2.0, score=1, max_score=4)
        levels = {est.null_response(state, scored, item, rng).score for _ in range(200)}
        assert levels <= set(range(5)) and len(levels) > 2
        plain = Response("s", "q", "correct", at=3.0, meta={"x": 1})
        again = RaschEstimator().null_response(state, plain, item, rng)
        assert (again.at, again.meta, again.score) == (3.0, {"x": 1}, None)


def test_simulated_with_a_missing_record_flags_nothing():
    """A state whose log was lost has no null to replay: nothing is credibly weak."""
    model = _student(random.Random(35), 3, 9)
    model.log["s"] = []
    assert not model.weakest("s", n=3, multiplicity="simulated", null_draws=50)


def test_simulated_draws_are_common_random_numbers_across_calls():
    """#45: a new answer extends each replay's random stream instead of reseeding it."""

    class Recording(RaschEstimator):
        def null_response(self, state, response, item, rng):
            streams.append(rng.getstate())
            return super().null_response(state, response, item, rng)

    n, draws = 12, 10
    runs = []
    for n_responses in (n - 1, n):  # the same student, before and after one more answer
        streams = []
        model = _student(random.Random(36), 3, n_responses, weakness=-3.0,
                         estimator=Recording())
        model.weakest("s", multiplicity="simulated", null_draws=draws)
        runs.append(streams)
    shorter, longer = runs
    assert len(shorter) == draws * (n - 1) and len(longer) == draws * n
    # each draw's first n - 1 redraws start from the same random state as before
    for d in range(draws):
        assert longer[d * n : d * n + n - 1] == shorter[d * (n - 1) : (d + 1) * (n - 1)]
