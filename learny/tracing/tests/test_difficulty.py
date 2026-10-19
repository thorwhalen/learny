"""Tests for explanatory item difficulty (#18): ``fit_feature_difficulty``.

All fixtures here are synthetic. Real learner data is personal data and never enters
this repository, which is public.
"""

import json
import math
import random
from dataclasses import replace

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
        assert own.mean - model.predict(x).mean == pytest.approx(model.residuals[q][0])
        assert abs(own.mean - b[q]) < abs(model.predict(x).mean - b[q]) + 0.5
        assert own.sd < model.predict(x).sd  # its own answers narrow it

    def test_apply_uses_features_alone_unless_asked(self):
        """A fitted residual carries the fitted students' answers (#18 review)."""
        bank, _, log = _world(seed=16)
        model = fit(log, items=bank)
        x = bank["q2"].meta["features"]
        plain = model.apply(bank)["q2"].difficulty
        own = model.apply(bank, use_residuals=True)["q2"].difficulty
        assert logit(plain) == pytest.approx(model.predict(x).mean, abs=1e-9)
        assert logit(own) == pytest.approx(model.predict(x, item_id="q2").mean, abs=1e-9)

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
            model.predict(bank[q].meta["features"]).mean, abs=1e-6
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


class TestScaleAndConvergence:
    def test_anchored_items_put_the_fit_on_the_banks_scale(self):
        """Strong students (mean ability +2) and half the bank published: without
        anchors the filled items sit ~2 logits off the published ones (#18 review)."""
        rng = random.Random(20)
        bank, b = {}, {}
        for i in range(60):
            x = {"length": rng.gauss(0, 1)}
            b[f"q{i}"] = 0.3 + 0.8 * x["length"] + rng.gauss(0, 0.3)
            published = expit(b[f"q{i}"]) if i % 2 else None
            bank[f"q{i}"] = Item(f"q{i}", difficulty=published, meta={"features": x})
        log = {}
        for s in range(30):
            theta = 2.0 + rng.gauss(0, 1)
            log[f"s{s}"] = [Response(f"s{s}", q, rng.random() < expit(theta - b[q]))
                            for q in (rng.choice(sorted(bank)) for _ in range(40))]
        anchored = fit_feature_difficulty(log, items=bank)
        floating = fit_feature_difficulty(log, items=bank, anchor="none")
        unpublished = [q for q in bank if bank[q].difficulty is None]

        def offset(model):
            filled = model.apply(bank)
            return sum(logit(filled[q].difficulty) - b[q] for q in unpublished) / len(unpublished)

        assert anchored.anchors == 30 and floating.anchors == 0
        assert abs(offset(anchored)) < 0.3
        assert offset(floating) < -1.0
        assert anchored.ability_mean > 1.5

    @staticmethod
    def _half_published(spread=1.0, *, all_published=False, seed=24):
        """A bank half (or all) published on a scale ``spread`` times the play's."""
        rng = random.Random(seed)
        bank, b = {}, {}
        for i in range(40):
            x = {"length": rng.gauss(0, 1)}
            b[f"q{i}"] = 0.3 + 0.8 * x["length"] + rng.gauss(0, 0.3)
            pub = expit(spread * b[f"q{i}"]) if (all_published or i % 2) else None
            bank[f"q{i}"] = Item(f"q{i}", difficulty=pub, meta={"features": x})
        log = {}
        for s in range(30):
            theta = rng.gauss(0, 1)
            log[f"s{s}"] = [Response(f"s{s}", q, rng.random() < expit(theta - b[q]))
                            for q in (rng.choice(sorted(bank)) for _ in range(40))]
        return bank, log

    def test_location_anchoring_leaves_the_weights_to_play(self):
        """A published scale half as wide as play's must not bend the weights."""
        bank, log = self._half_published(spread=0.5)
        located = fit(log, items=bank)
        unanchored = fit(log, items=bank, anchor="none")
        exact = fit(log, items=bank, anchor="exact")
        assert located.weights()["length"].mean == pytest.approx(
            unanchored.weights()["length"].mean
        )
        assert located.weights()["length"].sd == pytest.approx(
            unanchored.weights()["length"].sd
        )
        assert exact.weights()["length"].mean < located.weights()["length"].mean

    def test_a_fully_published_bank_still_learns_from_play(self):
        bank, log = self._half_published(all_published=True)
        flipped = {s: [Response(r.student, r.item, not r.correct) for r in rs]
                   for s, rs in log.items()}
        assert fit(log, items=bank).weights() != fit(flipped, items=bank).weights()

    def test_an_anchor_at_zero_or_one_is_skipped_with_a_warning(self):
        bank, log = self._half_published()
        bank = {**bank, "q1": replace(bank["q1"], difficulty=1.0)}
        with pytest.warns(RuntimeWarning, match="exactly 0 or 1"):
            model = fit(log, items=bank)
        assert model.anchors == 19

    def test_a_log_with_no_wrong_answers_warns(self):
        bank, _, log = _world(seed=25, students=3, per_student=10)
        perfect = {s: [Response(r.student, r.item, True) for r in rs] for s, rs in log.items()}
        with pytest.warns(RuntimeWarning, match="not identified"):
            fit(perfect, items=bank)

    def test_an_unknown_anchor_mode_is_loud(self):
        bank, _, log = _world(seed=26, students=2, per_student=5)
        with pytest.raises(ValueError, match="anchor must be one of"):
            fit(log, items=bank, anchor=True)

    def test_hitting_an_iteration_cap_warns_and_is_recorded(self):
        bank, _, log = _world(seed=21)
        with pytest.warns(RuntimeWarning, match="iteration cap"):
            model = fit(log, items=bank, max_iter=1)
        assert not model.converged
        assert FeatureDifficulty.from_dict(model.to_dict()).converged is False

    @pytest.mark.parametrize("bad", [math.nan, None, "3", True])
    def test_a_feature_that_is_not_a_finite_number_is_loud(self, bad):
        bank, _, log = _world(seed=22)
        bank = {**bank, "q0": Item("q0", meta={"features": {**bank["q0"].meta["features"], "length": bad}})}
        with pytest.raises(ValueError, match="finite number"):
            fit(log, items=bank)

    def test_a_student_not_in_the_log_is_loud(self):
        bank, _, log = _world(seed=23)
        with pytest.raises(KeyError, match="not in the log"):
            fit(log, items=bank, students=["s0", "nobody"])
