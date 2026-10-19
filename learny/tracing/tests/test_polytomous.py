"""Tests for ordered scores: ``Response.score`` and :class:`PartialCreditEstimator`.

All fixtures here are synthetic. Real learner data is personal data and never enters
this repository, which is public.
"""

import json
import math

import pytest

from learny.tracing import (
    Item,
    LearnerModel,
    PartialCreditEstimator,
    RaschEstimator,
    Response,
    ResponseLog,
    binomial_thresholds,
)

WEEK = 7 * 24 * 3600.0


def _fold(est, responses, items):
    state = est.init()
    for r in responses:
        state = est.observe(state, r, items.get(r.item))
    return state


def _assert_states_close(a, b, *, tol=1e-9):
    """Two nested estimator states equal up to float rounding."""
    assert type(a) is type(b)
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        for k in a:
            _assert_states_close(a[k], b[k], tol=tol)
    elif isinstance(a, float):
        assert math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    else:
        assert a == b


ITEMS = {
    "q1": Item("q1", labels=("fractions",), difficulty=0.3),
    "q2": Item("q2", labels={"fractions": 1.0, "area": 0.6}, difficulty=0.7),
    "q3": Item("q3", labels=("area",), difficulty=0.5),
}


class TestResponseScore:
    def test_score_and_max_score_go_together(self):
        with pytest.raises(ValueError, match="go together"):
            Response("a", "q", "correct", score=2)
        with pytest.raises(ValueError, match="go together"):
            Response("a", "q", "correct", max_score=4)

    @pytest.mark.parametrize("score,max_score", [(-1, 4), (5, 4), (0, 0)])
    def test_score_out_of_range_is_loud(self, score, max_score):
        with pytest.raises(ValueError, match="0 <= score <= max_score"):
            Response("a", "q", "correct", score=score, max_score=max_score)

    @pytest.mark.parametrize("score,max_score", [(2.5, 4), (3.0, 4), (True, 1), ("3", 4)])
    def test_score_must_be_an_int(self, score, max_score):
        with pytest.raises(TypeError, match="must be an int"):
            Response("a", "q", "correct", score=score, max_score=max_score)

    def test_a_skip_has_no_score(self):
        with pytest.raises(ValueError, match="skipped response has no score"):
            Response("a", "q", "skipped", score=0, max_score=4)

    def test_unscored_log_lines_are_unchanged(self):
        """A right/wrong response serialises exactly as it did before scores existed."""
        d = Response("a", "q", "correct", at=1.0).to_dict()
        assert d == {"student": "a", "item": "q", "outcome": "correct", "at": 1.0, "meta": {}}

    def test_scored_response_survives_the_log(self, tmp_path):
        log = ResponseLog(rootdir=tmp_path)
        scored = Response("a", "q", "wrong", at=1.0, score=1, max_score=4)
        log.append(scored)
        log.append(Response("a", "q", "correct", at=2.0))
        assert log["a"] == [scored, Response("a", "q", "correct", at=2.0)]
        lines = (tmp_path / "a.jsonl").read_text().splitlines()
        assert json.loads(lines[0])["score"] == 1
        assert "score" not in json.loads(lines[1])


class TestPartialCredit:
    def test_unscored_responses_score_exactly_as_rasch(self):
        """Guessing, skips and forgetting included: the right/wrong path is Rasch's."""
        kw = dict(guess=0.2, conjunctivity=1.0)
        rs = [
            Response("a", "q1", "correct", at=0.0),
            Response("a", "q2", "skipped", at=WEEK),
            Response("a", "q3", "wrong", at=2 * WEEK),
            Response("a", "q2", "skipped", at=3 * WEEK, meta={"not_reached": True}),
        ]
        pcm = _fold(PartialCreditEstimator(**kw), rs, ITEMS)
        assert pcm == _fold(RaschEstimator(**kw), rs, ITEMS)

    @pytest.mark.parametrize(
        "kw", [{}, {"gain": "elo"}, {"update_difficulty": True}, {"conjunctivity": 2.0}]
    )
    def test_one_step_score_is_the_rasch_model(self, kw):
        """With one Newton step, a score out of 1 under the default thresholds is a
        right/wrong answer (with ``guess=0``: a score is never a guess)."""
        outcomes = ["correct", "wrong", "correct", "correct", "wrong"]
        items = ["q1", "q2", "q3", "q2", "q1"]
        scored = [
            Response("a", i, o, at=k * WEEK, score=int(o == "correct"), max_score=1)
            for k, (i, o) in enumerate(zip(items, outcomes))
        ]
        plain = [Response("a", i, o, at=k * WEEK) for k, (i, o) in enumerate(zip(items, outcomes))]
        _assert_states_close(
            _fold(PartialCreditEstimator(mode_steps=1, **kw), scored, ITEMS),
            _fold(RaschEstimator(**kw), plain, ITEMS),
        )

    @pytest.mark.parametrize("m", [4, 20, 100, 1000])
    def test_a_surprising_score_lands_on_the_posterior_mode(self, m):
        """No overshoot on many levels: the update is a Laplace step to the mode."""
        prior_mu, prior_var = 3.0, 0.5
        est = PartialCreditEstimator(prior_var=prior_var)
        state = {"global": {"mu": prior_mu, "var": prior_var, "n": 0, "t": None},
                 "labels": {}}
        r = Response("a", "q", "wrong", score=0, max_score=m)
        got = est.observe(state, r, Item("q"))["global"]["mu"]

        def objective(t):  # log prior + binomial log-likelihood of 0 out of m
            return -((t - prior_mu) ** 2) / (2 * prior_var) - m * math.log1p(math.exp(t))

        grid = [prior_mu - 20 + i * 1e-4 for i in range(int(23 / 1e-4))]
        brute = max(grid, key=objective)
        assert got == pytest.approx(brute, abs=1e-3)

    def test_the_mode_is_found_across_the_range(self):
        """Safeguarded Newton never stalls: checked against bisection, a slow but sure
        root-finder, over random priors and scores (the #33 review found a two-cycle)."""
        import random

        from learny.tracing.estimators import _posterior_mode

        rng = random.Random(0)
        for _ in range(2000):
            m = rng.randint(2, 1000)
            k = rng.randint(0, m)
            s, v = rng.uniform(-12, 12), 10 ** rng.uniform(-6, 1)

            def g(t):  # binomial log-likelihood of k out of m: gradient and information
                return k - m * (1.0 / (1.0 + math.exp(-t)) if t > -700 else 0.0)

            def info(t):
                p = 1.0 / (1.0 + math.exp(-t)) if t > -700 else 0.0
                return m * p * (1.0 - p)

            lo, hi = s - v * m - 1, s + v * m + 1
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if -(mid - s) / v + g(mid) > 0 else (lo, mid)
            got = _posterior_mode(s, v, g, info, steps=50)
            assert got == pytest.approx(0.5 * (lo + hi), abs=1e-6), (m, k, s, v)

    @pytest.mark.parametrize("steps", [49, 50, 51])
    def test_a_near_flat_tail_does_not_freeze_the_update(self, steps):
        """0 of 1000 from N(10, 1): where information ~ 0 a Newton step used to bounce
        between the bracket's ends and leave the skill where it started."""
        est = PartialCreditEstimator(prior_var=1.0, mode_steps=steps)
        state = {"global": {"mu": 10.0, "var": 1.0, "n": 0, "t": None}, "labels": {}}
        r = Response("a", "q", "wrong", score=0, max_score=1000)
        assert est.observe(state, r, Item("q"))["global"]["mu"] == pytest.approx(-4.24, abs=0.01)

    @pytest.mark.parametrize("bad", [0, 2.5, True])
    def test_mode_steps_is_checked_up_front(self, bad):
        with pytest.raises(ValueError, match="mode_steps"):
            PartialCreditEstimator(mode_steps=bad)

    def test_the_elo_step_is_on_the_unit_scale(self):
        """A full score moves Elo by at most ``elo_rate``, however many levels it has."""
        est = PartialCreditEstimator(gain="elo")
        for m in (1, 4, 100):
            r = Response("a", "q", "correct", score=m, max_score=m)
            mu = est.observe(est.init(), r, Item("q"))["global"]["mu"]
            assert 0 < mu <= est.elo_rate

    def test_the_default_estimator_ignores_the_score(self):
        """The default stays Rasch on ``outcome``: adding a score changes nothing."""
        est = RaschEstimator()
        with_score = Response("a", "q1", "wrong", score=3, max_score=4)
        without = Response("a", "q1", "wrong")
        assert est.observe(est.init(), with_score, ITEMS["q1"]) == est.observe(
            est.init(), without, ITEMS["q1"]
        )

    def test_more_stars_mean_more_skill(self):
        est = PartialCreditEstimator()
        item = ITEMS["q3"]
        mus = [
            est.observe(est.init(), Response("a", "q3", "correct", score=k, max_score=4), item)[
                "global"
            ]["mu"]
            for k in range(5)
        ]
        assert mus == sorted(mus) and mus[0] < 0 < mus[-1]
        assert mus[2] == pytest.approx(0.0)  # mid-scale on an average item: no news

    def test_a_score_out_of_m_is_m_steps_under_binomial_thresholds(self):
        """Expected score is ``m`` times the right/wrong probability, at any state."""
        est = PartialCreditEstimator()
        state = _fold(
            est,
            [Response("a", "q1", "correct", score=3, max_score=4),
             Response("a", "q2", "wrong")],
            ITEMS,
        )
        for item in ITEMS.values():
            assert est.expected_score(state, item, 4) == pytest.approx(
                4 * est.predict(state, item)
            )

    def test_score_probabilities_are_a_distribution_even_at_the_tails(self):
        est = PartialCreditEstimator(prior_var=1e-6)
        for difficulty in (1e-9, 0.5, 1 - 1e-9):
            probs = est.score_probabilities(est.init(), Item("q", difficulty=difficulty), 6)
            assert len(probs) == 7 and sum(probs) == pytest.approx(1.0)
            assert all(0.0 <= p <= 1.0 for p in probs)

    def test_thresholds_are_a_seam(self):
        """Steps spread wider apart make one score carry less evidence."""

        def spread(item, max_score):
            return [3.0 * t for t in binomial_thresholds(item, max_score)]

        r = Response("a", "q3", "correct", score=4, max_score=4)
        default = PartialCreditEstimator().observe(PartialCreditEstimator().init(), r, ITEMS["q3"])
        wide_est = PartialCreditEstimator(thresholds=spread)
        wide = wide_est.observe(wide_est.init(), r, ITEMS["q3"])
        assert wide["global"]["var"] > default["global"]["var"]

    @pytest.mark.parametrize("bad", [math.nan, math.inf, "0.5", True])
    def test_non_finite_or_non_numeric_thresholds_are_loud(self, bad):
        est = PartialCreditEstimator(thresholds=lambda item, m: [0.0] * (m - 1) + [bad])
        r = Response("a", "q3", "correct", score=2, max_score=4)
        with pytest.raises(ValueError, match="finite numbers"):
            est.observe(est.init(), r, ITEMS["q3"])

    def test_a_wrong_number_of_thresholds_is_loud(self):
        est = PartialCreditEstimator(thresholds=lambda item, m: [0.0])
        r = Response("a", "q3", "correct", score=2, max_score=4)
        with pytest.raises(ValueError, match="needs exactly 4"):
            est.observe(est.init(), r, ITEMS["q3"])

    def test_a_co_estimated_difficulty_moves_with_the_score(self):
        est = PartialCreditEstimator(update_difficulty=True)
        item = Item("q", difficulty=0.5)

        def b_after(score):
            r = Response("a", "q", "correct", score=score, max_score=4)
            return est.observe(est.init(), r, item)["items"]["q"]["b"]

        assert b_after(4) < 0.0 < b_after(0)  # a high score says the item is easier


class TestThroughTheFacade:
    def test_replay_reproduces_live_state_with_scores(self, tmp_path):
        """The log contract holds for scores: replaying the file gives the live state."""
        model = LearnerModel(
            items=ITEMS,
            estimator=PartialCreditEstimator(),
            log=ResponseLog(rootdir=tmp_path),
            estimates={},
        )
        model.record("a", "q1", "correct", at=0.0, score=4, max_score=4)
        model.record("a", "q2", "wrong", at=WEEK, score=1, max_score=4)
        model.record("a", "q3", "correct", at=2 * WEEK)
        live = model.estimates["a"]
        model.replay("a")
        assert model.estimates["a"] == live

    def test_record_many_keeps_the_score(self):
        model = LearnerModel(
            items=ITEMS, estimator=PartialCreditEstimator(), log={}, estimates={}
        )
        r = Response("a", "q1", "wrong", score=4, max_score=4, meta={"stars": 5})
        model.record_many([r])
        assert model.log["a"] == [r]
        assert model.mastery("a")["fractions"].mu > 0  # read the score, not the outcome

    def test_sub_scores_as_responses_on_facet_items(self):
        """One attempt with three sub-scores is three responses, one per facet item."""
        facets = ("reaction", "tempo", "rhythm")
        items = {f"song-7/{f}": Item(f"song-7/{f}", labels=(f,)) for f in facets}
        model = LearnerModel(
            items=items, estimator=PartialCreditEstimator(), log={}, estimates={}
        )
        for facet, stars in zip(facets, (5, 3, 1)):
            model.record("a", f"song-7/{facet}", "correct", at=0.0,
                         score=stars - 1, max_score=4)
        m = model.mastery("a")
        assert m["reaction"].mu > m["tempo"].mu > m["rhythm"].mu


class TestScoreCalibration:
    """Score forecasts are scored against scores (#31), right/wrong against outcomes."""

    @staticmethod
    def _log(students=40, n=30, m=4, seed=0):
        """Binomial scores, the default thresholds' own model, so a sound estimator."""
        import random

        rng = random.Random(seed)
        items = {f"q{j}": Item(f"q{j}", labels=(f"l{j % 3}",), difficulty=0.2 + 0.2 * (j % 4))
                 for j in range(12)}
        log = {}
        for s in range(students):
            theta = rng.gauss(0, 1)
            rs = []
            for i in range(n):
                item = items[f"q{i % 12}"]
                p = 1 / (1 + math.exp(-(theta - math.log(item.difficulty / (1 - item.difficulty)))))
                k = sum(rng.random() < p for _ in range(m))
                rs.append(Response(f"s{s}", item.id, "correct" if k == m else "wrong",
                                   at=i * 3600.0, score=k, max_score=m))
            log[f"s{s}"] = rs
        return items, log

    def test_a_sound_model_beats_the_base_rates_and_is_calibrated(self):
        from learny.tracing import score_calibration

        items, log = self._log()
        r = score_calibration(log, items=items, estimator=PartialCreditEstimator())
        assert r.n == 40 * 30
        assert r.log_loss < r.base_log_loss and r.rps < r.base_rps
        assert r.ece < 0.05

    def test_wrong_thresholds_score_worse(self):
        from learny.tracing import score_calibration

        def spread(item, m):
            return [3.0 * t for t in binomial_thresholds(item, m)]

        items, log = self._log()
        good = score_calibration(log, items=items, estimator=PartialCreditEstimator())
        bad = score_calibration(
            log, items=items, estimator=PartialCreditEstimator(thresholds=spread)
        )
        assert bad.log_loss > good.log_loss and bad.rps > good.rps

    def test_a_scored_response_goes_to_the_report_its_estimator_forecasts(self):
        """The bug #31 fixes: a score model's predict() was scored against the caller's
        dichotomised outcome, which is not the event it forecasts."""
        from learny.tracing import calibration

        items, log = self._log(students=3, n=10)
        log["s0"].append(Response("s0", "q0", "correct"))  # one right/wrong response
        assert calibration(log, items=items, estimator=PartialCreditEstimator()).n == 1
        assert calibration(log, items=items, estimator=RaschEstimator()).n == 31

    def test_an_estimator_that_reads_only_outcomes_is_refused(self):
        from learny.tracing import score_calibration

        items, log = self._log(students=1, n=2)
        with pytest.raises(TypeError, match="does not forecast scores"):
            score_calibration(log, items=items, estimator=RaschEstimator())

    def test_through_the_facade(self):
        from learny.tracing import score_calibration

        items, log = self._log(students=3, n=10)
        model = LearnerModel(items=items, estimator=PartialCreditEstimator(),
                             log=log, estimates={})
        assert model.score_calibration() == score_calibration(
            log, items=items, estimator=model.estimator
        )

    def test_nothing_scored_is_nan_not_an_error(self):
        from learny.tracing import ScoreCalibrationReport

        r = ScoreCalibrationReport.from_forecasts([])
        assert r.n == 0 and math.isnan(r.log_loss) and r.bins == ()

    def test_a_level_outside_the_forecast_is_loud(self):
        from learny.tracing import ScoreCalibrationReport

        with pytest.raises(ValueError, match="not one of the 3 levels"):
            ScoreCalibrationReport.from_forecasts([([0.2, 0.5, 0.3], 3)])

    @pytest.mark.parametrize(
        "probs", [[5.0, 5.0, 5.0], [0.5, math.nan, 0.5], [1.0], [-0.5, 1.5]]
    )
    def test_a_forecast_that_is_not_a_distribution_is_loud(self, probs):
        from learny.tracing import ScoreCalibrationReport

        with pytest.raises(ValueError, match="forecast"):
            ScoreCalibrationReport.from_forecasts([(probs, 0)])
