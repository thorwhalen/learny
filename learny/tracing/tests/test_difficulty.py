"""Tests for explanatory item difficulty (#18): ``fit_feature_difficulty``.

All fixtures here are synthetic. Real learner data is personal data and never enters
this repository, which is public.
"""

import json
import math
import random

import pytest

from learny.tracing import (
    FeatureDifficulty,
    Item,
    LearnerModel,
    Response,
    fit_feature_difficulty,
)
from learny.tracing.estimators import expit, logit

TRUE = {"length": 0.8, "rarity": -0.5, "noise": 0.0}
RESID_SD = 0.4


def fit(log, **kw):
    """The fit at the world's true residual variance, unless a test says otherwise:
    estimating it (the default) runs EM, which a fast suite can afford once."""
    kw.setdefault("residual_var", RESID_SD**2)
    return fit_feature_difficulty(log, **kw)


def _world(seed=0, *, students=30, per_student=40, n_items=60, resid_sd=RESID_SD, scored=False):
    """A bank whose difficulty is linear in two of three features, plus a residual."""
    rng = random.Random(seed)
    bank = {
        f"q{i}": Item(f"q{i}", meta={"features": {n: rng.gauss(0, 1) for n in TRUE}})
        for i in range(n_items)
    }
    b = {
        q: 0.3 + sum(w * it.meta["features"][n] for n, w in TRUE.items()) + rng.gauss(0, resid_sd)
        for q, it in bank.items()
    }
    log = {}
    for s in range(students):
        theta = rng.gauss(0, 1)
        rs = []
        for _ in range(per_student):
            q = rng.choice(sorted(bank))
            p = expit(theta - b[q])
            if scored:
                k = sum(rng.random() < p for _ in range(4))
                rs.append(Response(f"s{s}", q, "correct" if k == 4 else "wrong", score=k, max_score=4))
            else:
                rs.append(Response(f"s{s}", q, rng.random() < p))
        log[f"s{s}"] = rs
    return bank, b, log


class TestFit:
    def test_recovers_the_weights_within_their_uncertainty(self):
        bank, _, log = _world()
        w = fit(log, items=bank).weights()
        for name, true in TRUE.items():
            assert abs(w[name].mean - true) < 2.5 * w[name].sd, name
        assert w["length"].mean > 2 * w["length"].sd  # a real feature is found
        assert abs(w["noise"].mean) < 2.5 * w["noise"].sd  # an irrelevant one is not

    def test_scores_count_as_binomial_trials_and_sharpen_the_fit(self):
        bank, _, plain = _world(seed=1)
        _, _, scored = _world(seed=1, scored=True)
        sd_plain = fit(plain, items=bank).weights()["length"].sd
        sd_scored = fit(scored, items=bank).weights()["length"].sd
        assert sd_scored < sd_plain

    def test_one_student_is_enough_to_rank_features(self):
        """The cold-start regime: one learner, every item once."""
        rng = random.Random(2)
        bank = {f"q{i}": Item(f"q{i}", meta={"features": {"length": i % 8}}) for i in range(80)}
        log = {"ada": [Response("ada", q, rng.random() < expit(-(0.5 * (i % 8) - 1.5)))
                       for i, q in enumerate(bank)]}
        w = fit(log, items=bank).weights()["length"]
        assert w.mean > 2 * w.sd

    def test_the_residual_variance_is_estimated_unless_given(self):
        bank, _, log = _world(seed=3, resid_sd=1.0)
        assert fit_feature_difficulty(log, items=bank).residual_var > 0.3
        assert fit(log, items=bank, residual_var=0.2).residual_var == 0.2

    def test_skips_are_not_evidence_about_difficulty(self):
        bank, _, log = _world(seed=4)
        with_skips = {s: rs + [Response(s, "q0", "skipped")] for s, rs in log.items()}
        a = fit(log, items=bank)
        b = fit(with_skips, items=bank)
        assert a.coef == pytest.approx(b.coef)


class TestPredictAndApply:
    def test_an_unseen_item_is_predicted_from_its_features_with_honest_width(self):
        bank, _, log = _world(seed=5)
        model = fit(log, items=bank)
        x = {"length": 1.5, "rarity": -1.0, "noise": 0.0}
        new = model.predict(x)
        assert abs(new.mean - (0.3 + 0.8 * 1.5 + 0.5)) < 2.5 * new.sd
        assert new.sd ** 2 > model.residual_var  # the residual is unknown for it

    def test_a_fitted_item_keeps_its_own_residual(self):
        bank, b, log = _world(seed=6, students=60)
        model = fit(log, items=bank)
        q = "q7"
        x = bank[q].meta["features"]
        own = model.predict(x, item_id=q)
        assert own.mean - model.predict(x).mean == pytest.approx(model.residuals[q])
        assert abs(own.mean - b[q]) < abs(model.predict(x).mean - b[q]) + 0.5

    def test_apply_fills_the_bank_for_the_items_seam(self):
        bank, _, log = _world(seed=7)
        model = fit(log, items=bank)
        given = {**bank, "fixed": Item("fixed", difficulty=0.9, meta={"features": dict.fromkeys(TRUE, 0.0)})}
        filled = model.apply(given)
        assert filled["fixed"].difficulty == 0.9  # a given difficulty is kept
        assert all(0.0 < filled[q].difficulty < 1.0 for q in bank)
        assert model.apply(given, overwrite=True)["fixed"].difficulty != 0.9
        lm = LearnerModel(items=filled, log={}, estimates={})
        hard = max(bank, key=lambda q: filled[q].difficulty)
        easy = min(bank, key=lambda q: filled[q].difficulty)
        assert lm.predict("new", hard) < lm.predict("new", easy)

    def test_the_artifact_round_trips_through_json(self):
        bank, _, log = _world(seed=8)
        model = fit(log, items=bank)
        again = FeatureDifficulty.from_dict(json.loads(json.dumps(model.to_dict())))
        assert again == model
        with pytest.raises(ValueError, match="schema"):
            FeatureDifficulty.from_dict({**model.to_dict(), "schema": "something/else"})

    def test_logit_scale_matches_the_bank(self):
        """apply() writes a proportion failing, the bank's convention."""
        bank, _, log = _world(seed=9)
        model = fit(log, items=bank)
        q = "q3"
        filled = model.apply(bank)[q]
        assert logit(filled.difficulty) == pytest.approx(
            model.predict(bank[q].meta["features"], item_id=q).mean, abs=1e-6
        )


class TestRefusals:
    def test_an_item_without_features_is_loud(self):
        bank, _, log = _world(seed=10)
        bank = {**bank, "q0": Item("q0")}
        with pytest.raises(ValueError, match="without features"):
            fit(log, items=bank)

    def test_an_item_missing_one_feature_is_loud(self):
        bank, _, log = _world(seed=11)
        bank = {**bank, "q0": Item("q0", meta={"features": {"length": 1.0}})}
        with pytest.raises(ValueError, match="lack a value"):
            fit(log, items=bank)

    def test_a_constant_feature_is_loud(self):
        rng = random.Random(12)
        bank = {f"q{i}": Item(f"q{i}", meta={"features": {"k": 3.0}}) for i in range(5)}
        log = {"a": [Response("a", q, rng.random() < 0.5) for q in bank]}
        with pytest.raises(ValueError, match="same value on every fitted item"):
            fit(log, items=bank)

    def test_features_can_come_from_outside_the_bank(self):
        bank, _, log = _world(seed=13)
        external = {q: it.meta["features"] for q, it in bank.items()}
        plain = {q: Item(q) for q in bank}
        a = fit(log, items=plain, features=external)
        b = fit(log, items=bank)
        assert a.coef == pytest.approx(b.coef)

    @pytest.mark.parametrize("bad", [0.0, -1.0, math.nan])
    def test_a_bad_prior_is_loud(self, bad):
        bank, _, log = _world(seed=14, students=2, per_student=5)
        with pytest.raises(ValueError, match="positive number"):
            fit(log, items=bank, weight_prior_var=bad)
