"""Tests for the estimator and the facade.

The contract this file exists to protect: **the log is the source of truth and every
estimate is a rebuildable cache**. If ``test_replay_reproduces_live_state`` fails, the
estimator has picked up a dependence on something outside ``(state, response, item)`` and
can no longer be swapped without a data migration.

All data here is synthetic.
"""

import random

import pytest

from learny.tracing.estimators import (
    RaschEstimator,
    difficulty_from_rank,
    expit,
    logit,
    mark_not_reached,
)
from learny.tracing.model import LearnerModel
from learny.tracing.records import Item, Outcome, Response
from learny.tracing.stores import ResponseLog

WEEK = 7 * 24 * 3600.0


@pytest.fixture
def items():
    """A tiny synthetic bank: two labels, three difficulty bands."""
    return {
        f"q{i}": Item(
            f"q{i}",
            labels=("fractions",) if i % 2 else ("fractions", "area"),
            difficulty=difficulty_from_rank((i % 3) + 1, 3),
        )
        for i in range(12)
    }


@pytest.fixture
def model(items, tmp_path):
    return LearnerModel(items=items, log=ResponseLog(rootdir=tmp_path), estimates={})


def mu(model, student):
    return model.estimates[student]["global"]["mu"]


class TestLinkFunctions:
    @pytest.mark.parametrize("p", [0.01, 0.25, 0.5, 0.75, 0.99])
    def test_logit_expit_round_trip(self, p):
        assert expit(logit(p)) == pytest.approx(p, abs=1e-5)

    def test_expit_does_not_overflow(self):
        assert expit(-1e6) == 0.0
        assert expit(1e6) == 1.0

    def test_difficulty_from_rank_is_monotone(self):
        ds = [difficulty_from_rank(r, 5) for r in range(1, 6)]
        assert ds == sorted(ds) and all(0 < d < 1 for d in ds)

    def test_rank_out_of_range_is_loud(self):
        with pytest.raises(ValueError, match="out of range"):
            difficulty_from_rank(4, 3)


class TestColdStart:
    def test_prediction_sits_between_base_rate_and_a_coin_flip(self):
        """Honest about knowing the item but not the student."""
        est = RaschEstimator()
        cold = est.predict(est.init(), Item("q", difficulty=0.75))
        assert 0.25 < cold < 0.5

    def test_a_confident_prior_recovers_the_base_rate(self):
        est = RaschEstimator(prior_var=1e-6)
        assert est.predict(est.init(), Item("q", difficulty=0.75)) == pytest.approx(0.25, abs=1e-3)

    def test_unknown_difficulty_predicts_a_coin_flip(self):
        est = RaschEstimator()
        assert est.predict(est.init(), Item("q")) == pytest.approx(0.5)

    def test_first_response_moves_more_than_the_tenth(self):
        """Cold start is handled by the shrinking posterior, not a special mode."""
        est = RaschEstimator()
        item = Item("q", labels=("a",), difficulty=0.5)
        r = Response("ada", "q", Outcome.CORRECT)
        states = [est.init()]
        for _ in range(10):
            states.append(est.observe(states[-1], r, item))
        moves = [
            states[i + 1]["global"]["mu"] - states[i]["global"]["mu"] for i in range(10)
        ]
        assert moves[0] > moves[-1] > 0

    def test_uncertainty_shrinks_with_evidence(self):
        est = RaschEstimator()
        item = Item("q", difficulty=0.5)
        state = est.init()
        before = state["global"]["var"]
        for _ in range(5):
            state = est.observe(state, Response("a", "q", Outcome.CORRECT), item)
        assert state["global"]["var"] < before


class TestDifficultyAwareness:
    def test_a_hard_item_right_is_stronger_evidence_than_an_easy_one(self):
        """The property a plain success/failure count cannot have."""
        est = RaschEstimator()
        hard = est.observe(
            est.init(), Response("a", "h", Outcome.CORRECT), Item("h", difficulty=0.9)
        )
        easy = est.observe(
            est.init(), Response("a", "e", Outcome.CORRECT), Item("e", difficulty=0.1)
        )
        assert hard["global"]["mu"] > easy["global"]["mu"]

    def test_an_easy_item_wrong_is_stronger_evidence_than_a_hard_one(self):
        est = RaschEstimator()
        easy = est.observe(
            est.init(), Response("a", "e", Outcome.WRONG), Item("e", difficulty=0.1)
        )
        hard = est.observe(
            est.init(), Response("a", "h", Outcome.WRONG), Item("h", difficulty=0.9)
        )
        assert easy["global"]["mu"] < hard["global"]["mu"]


class TestBlanks:
    def test_mark_not_reached_flags_only_the_trailing_run(self):
        rs = [
            Response("a", f"q{i}", o)
            for i, o in enumerate(["correct", "skipped", "wrong", "skipped", "skipped"])
        ]
        assert [r.meta.get("not_reached", False) for r in mark_not_reached(rs)] == [
            False, False, False, True, True,
        ]

    def test_a_not_reached_blank_is_not_evidence(self):
        est = RaschEstimator()
        blank = Response("a", "q", Outcome.SKIPPED, meta={"not_reached": True})
        assert est.observe(est.init(), blank, Item("q", difficulty=0.5)) == est.init()

    def test_an_interior_blank_is_softer_than_a_wrong_answer(self):
        """Scoring an abstention as wrong is more biased than not scoring it at all."""
        est = RaschEstimator(guess=0.2)
        item = Item("q", difficulty=0.5)
        blank = est.observe(est.init(), Response("a", "q", Outcome.SKIPPED), item)
        wrong = est.observe(est.init(), Response("a", "q", Outcome.WRONG), item)
        assert wrong["global"]["mu"] < blank["global"]["mu"] < 0

    def test_abstentions_can_be_switched_off_entirely(self):
        est = RaschEstimator(abstain_weight=0.0)
        assert est.observe(
            est.init(), Response("a", "q", Outcome.SKIPPED), Item("q")
        ) == est.init()


class TestGuessing:
    def test_a_guessable_item_right_is_weaker_evidence(self):
        item = Item("q", difficulty=0.8)
        r = Response("a", "q", Outcome.CORRECT)
        no_guess = RaschEstimator(guess=0.0)
        mcq = RaschEstimator(guess=0.2)
        assert (
            mcq.observe(mcq.init(), r, item)["global"]["mu"]
            < no_guess.observe(no_guess.init(), r, item)["global"]["mu"]
        )

    def test_prediction_never_falls_below_the_guessing_rate(self):
        est = RaschEstimator(guess=0.2)
        state = est.init()
        for _ in range(30):
            state = est.observe(state, Response("a", "q", Outcome.WRONG), Item("q", difficulty=0.5))
        assert est.predict(state, Item("q", difficulty=0.99)) >= 0.2


class TestForgetting:
    def test_variance_reopens_over_time(self):
        est = RaschEstimator(forget_per_week=0.05)
        item = Item("q", difficulty=0.5)
        state = est.observe(est.init(), Response("a", "q", Outcome.CORRECT, at=0.0), item)
        settled = state["global"]["var"]
        later = est.observe(
            state, Response("a", "q", Outcome.CORRECT, at=10 * WEEK), item
        )
        # ten weeks of inflation before this observation tightened it again
        assert later["global"]["var"] > settled * 0.9

    def test_the_mean_is_never_decayed(self):
        """Inflating variance says 'we know less'; decaying the mean would say
        'the skill got worse', which is a guess."""
        est = RaschEstimator(forget_per_week=0.05)
        item = Item("q", difficulty=0.5)
        state = est.observe(est.init(), Response("a", "q", Outcome.CORRECT, at=0.0), item)
        before = state["global"]["mu"]
        aged = est.predict(state, item, at=52 * WEEK)
        assert est.skill(state).mu == before
        assert aged < est.predict(state, item, at=0.0)  # only less certain, pulled to 0.5

    def test_variance_never_exceeds_the_prior(self):
        est = RaschEstimator(forget_per_week=10.0)
        item = Item("q", difficulty=0.5)
        state = est.observe(est.init(), Response("a", "q", Outcome.CORRECT, at=0.0), item)
        aged = est.observe(state, Response("a", "q", Outcome.CORRECT, at=99 * WEEK), item)
        assert aged["global"]["var"] <= est.prior_var


class TestAggregation:
    def test_compensatory_is_the_default(self):
        est = RaschEstimator()
        assert est.conjunctivity == 0.0

    def test_conjunctive_weights_the_weakest_label(self):
        """With conjunctivity, the label the student is worst at dominates."""
        item = Item("q", labels=("strong", "weak"), difficulty=0.5)
        state = {
            "global": {"mu": 0.0, "var": 0.2, "n": 10, "t": None},
            "labels": {
                "strong": {"mu": 1.5, "var": 0.1, "n": 10, "t": None},
                "weak": {"mu": -1.5, "var": 0.1, "n": 10, "t": None},
            },
        }
        compensatory = RaschEstimator().predict(state, item)
        conjunctive = RaschEstimator(conjunctivity=4.0).predict(state, item)
        assert conjunctive < compensatory

    def test_label_reliability_attenuates_its_influence(self):
        """A label tagged at 0.57 agreement should move the estimate less than one at 1.0."""
        est = RaschEstimator()
        r = Response("a", "q", Outcome.CORRECT)
        full = est.observe(est.init(), r, Item("q", labels={"x": 1.0}, difficulty=0.5))
        noisy = est.observe(
            est.init(), r, Item("q", labels={"x": 0.57, "y": 0.43}, difficulty=0.5)
        )
        assert abs(noisy["labels"]["x"]["mu"]) < abs(full["labels"]["x"]["mu"])


class TestLearning:
    def test_consistent_success_raises_skill(self, model):
        for i in range(10):
            model.record("ada", f"q{i}", "correct")
        assert mu(model, "ada") > 0.5

    def test_consistent_failure_lowers_skill(self, model):
        for i in range(10):
            model.record("ada", f"q{i}", "wrong")
        assert mu(model, "ada") < -0.5

    def test_labels_separate(self, model):
        """Fail only the items carrying 'area'; 'area' should end up the weaker label."""
        for i in range(12):
            good = "area" not in model.items[f"q{i}"].weights
            model.record("ada", f"q{i}", "correct" if good else "wrong")
        m = model.mastery("ada")
        assert m["area"].mu < m["fractions"].mu

    def test_thin_label_evidence_stays_near_the_global_skill(self, model):
        """The shrinkage that makes per-label estimates safe when data is scarce."""
        for i in range(10):
            model.record("ada", f"q{i}", "correct")
        state = model.estimates["ada"]
        for entry in state["labels"].values():
            assert abs(entry["mu"]) < abs(state["global"]["mu"])

    def test_weakest_returns_labels_with_evidence_only(self, model):
        model.record("ada", "q1", "wrong")  # q1 is labelled ('fractions',)
        assert [m.label for m in model.weakest("ada", credible_below=None)] == ["fractions"]

    def test_weakest_orders_several_labels_worst_first(self, model):
        """Regression: sorting must use the posterior mean, not the Skill object."""
        for i in range(12):
            good = "area" not in model.items[f"q{i}"].weights
            model.record("ada", f"q{i}", "correct" if good else "wrong")
        ranked = model.weakest("ada", n=2, credible_below=None)
        assert [m.label for m in ranked] == ["area", "fractions"]
        assert ranked[0].mu < ranked[1].mu

    def test_weakest_respects_n(self, model):
        for i in range(12):
            model.record("ada", f"q{i}", "correct")
        assert len(model.weakest("ada", n=1, credible_below=None)) == 1

    def test_mastery_reports_a_credible_interval(self, model):
        model.record("ada", "q1", "correct")
        m = model.mastery("ada")["fractions"]
        lo, hi = m.interval()
        assert 0.0 < lo < m.probability < hi < 1.0

    def test_confidence_rises_with_evidence(self, model):
        model.record("ada", "q1", "correct")
        first = model.mastery("ada")["fractions"].confidence
        for i in range(3, 12, 2):
            model.record("ada", f"q{i}", "correct")
        assert model.mastery("ada")["fractions"].confidence > first


class TestItemDifficultyIdentifiability:
    def test_difficulty_is_fixed_by_default(self, model):
        """With one learner, skill and difficulty are not jointly identifiable."""
        for i in range(6):
            model.record("ada", f"q{i}", "correct")
        assert "items" not in model.estimates["ada"]

    def test_difficulty_updates_only_when_asked(self, items, tmp_path):
        model = LearnerModel(
            items=items,
            estimator=RaschEstimator(update_difficulty=True),
            log=ResponseLog(rootdir=tmp_path),
            estimates={},
        )
        for i in range(6):
            model.record("ada", f"q{i}", "correct")
        assert "items" in model.estimates["ada"]


class TestGain:
    def test_elo_gain_is_available_and_learns(self, items, tmp_path):
        model = LearnerModel(
            items=items,
            estimator=RaschEstimator(gain="elo"),
            log=ResponseLog(rootdir=tmp_path),
            estimates={},
        )
        for i in range(10):
            model.record("ada", f"q{i}", "correct")
        assert mu(model, "ada") > 0

    def test_unknown_gain_is_loud(self):
        est = RaschEstimator(gain="magic")
        with pytest.raises(ValueError, match="gain must be"):
            est.observe(est.init(), Response("a", "q", Outcome.CORRECT), Item("q"))


class TestReplayContract:
    """The contract that lets the estimator be replaced without a data migration."""

    def test_replay_reproduces_live_state(self, model):
        rng = random.Random(0)
        for k in range(60):
            i = rng.randrange(12)
            outcome = rng.choice(["correct", "wrong", "unanswered"])
            model.record("ada", f"q{i}", outcome, at=float(k) * 3600)
        live = model.estimates["ada"]
        model.estimates.clear()
        model.replay()
        assert model.estimates["ada"] == live

    def test_replay_rebuilds_after_the_cache_is_destroyed(self, model):
        for i in range(8):
            model.record("ada", f"q{i}", "correct")
        expected = model.predict("ada", "q0")
        del model.estimates["ada"]
        model.replay("ada")
        assert model.predict("ada", "q0") == pytest.approx(expected)

    def test_replay_covers_every_student_in_the_log(self, model):
        model.record("ada", "q0", "correct")
        model.record("bob", "q1", "wrong")
        model.estimates.clear()
        model.replay()
        assert set(model.estimates) == {"ada", "bob"}

    def test_one_students_data_never_touches_anothers_estimate(self, model):
        """No pooling across students in the default. This is the privacy boundary."""
        model.record("ada", "q0", "correct")
        before = dict(model.estimates["ada"])
        for i in range(12):
            model.record("bob", f"q{i}", "wrong")
        assert model.estimates["ada"] == before

    def test_observe_does_not_mutate_the_state_it_is_given(self):
        est = RaschEstimator()
        state = est.init()
        snapshot = {
            "global": {"mu": 0.0, "var": 1.0, "n": 0, "t": None},
            "labels": {},
        }
        est.observe(state, Response("a", "q", Outcome.CORRECT), Item("q", labels=("x",)))
        assert state == snapshot

    def test_state_is_json_serialisable(self, model):
        import json

        for i in range(6):
            model.record("ada", f"q{i}", "correct", at=float(i))
        assert json.loads(json.dumps(model.estimates["ada"])) == model.estimates["ada"]


class TestUnknownItems:
    def test_a_response_to_an_unknown_item_still_counts(self, model):
        model.record("ada", "not-in-the-bank", "correct")
        assert model.estimates["ada"]["global"]["n"] == 1

    def test_predicting_an_unknown_item_is_a_coin_flip(self, model):
        assert model.predict("ada", "not-in-the-bank") == pytest.approx(0.5)
