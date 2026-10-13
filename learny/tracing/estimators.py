"""Estimators: how one response changes what we believe about a student.

The default, :class:`RaschEstimator`, is **online Rasch with a Gaussian posterior** — one
Newton step on the log-posterior per response, which is Glickman's Glicko update against
an opponent of known strength. Belief about a student is::

    logit P(correct) = global_skill + aggregate(label skills) - item_difficulty

where every skill is a posterior ``(mu, var)`` rather than a point, and each label also
carries its covariance with the global skill (``cov``), so the posterior is joint: a
shortfall every item shares is attributed to the global skill, not to whichever label
has the largest share of each item. Carrying the variance
is what lets the model say *how sure* it is, decay confidence over time without
pretending to know which way a skill moved, and behave sanely at zero observations — all
from one formula instead of three bolted-on heuristics.

Elo is the same update with the information term frozen: Elo's uncertainty function
``U(n) = a/(1 + b*n)`` is exactly ``1/(1/var + n*I)`` for constant information ``I``. So
``gain='elo'`` is not a different estimator, it is this one with a constant step size.

Three decisions worth knowing before reading the code:

**Item difficulty does not update by default.** Textbook Elo moves ability and item
difficulty in opposite directions from the same residual, which works when a population
pins each item down. With one or two learners — a family, a tutor, one classroom — the two
are not jointly identifiable: they absorb each other and you get a model that fits the
history perfectly and predicts nothing. The default takes difficulty as given, from an
observed source such as a published difficulty band.

**The hierarchy is the cold-start mechanism, not a refinement.** A student may have one or
two responses against any given label. A label therefore carries only a *deviation* from
that student's global skill, shrunk hard toward zero by its prior. One paper gives the
global skill enough precision to serve as every label's prior before any label-specific
evidence exists. So the pooling that makes sparse labels usable happens **across labels
within one student** — no other student need exist, and none is ever consulted.

**The posterior is joint, but stored in O(labels).** Labels are kept conditionally
independent given the global skill (a star around it): each label stores its marginal
``(mu, var)`` and ``cov`` with the global skill, and label-label covariance is implied as
``cov_a * cov_b / var_global``. One response is one rank-1 (Laplace) update of that joint
covariance, followed by the projection back onto the star that keeps every ``(global,
label)`` pair exactly. A state without ``cov`` (written before it existed) reads as
covariance 0, the mean-field state, and needs no migration. Forgetting adds independent
drift to each skill and leaves the covariances alone; the ``conjunctivity`` soft-min
shares are linearised at the posterior means, as before.

**A skip is not a wrong answer, and not all skips are alike.** A blank at the end of a
paper is a clock, not a judgement; a blank with answers after it is an abstention, which
carries real information about confidence. They are treated differently, and neither is
scored as wrong.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, NamedTuple, Protocol, runtime_checkable

from learny.tracing.records import Item, Outcome, Response

__all__ = [
    "Estimator",
    "RaschEstimator",
    "Mastery",
    "Skill",
    "logit",
    "expit",
    "difficulty_from_rank",
    "mark_not_reached",
]

_WEEK = 7 * 24 * 3600.0
_MIN_VAR = 1e-12  # floor on a stored variance, so precision-weighted reads stay finite


def _cov(entry: Mapping[str, Any] | None) -> float:
    """A label's stored covariance with the global skill; 0 (mean-field) when absent."""
    return 0.0 if entry is None else float(entry.get("cov", 0.0))


def _clamp_cov(c: float, var_a: float, var_b: float) -> float:
    """Keep a covariance inside ``|c| <= sqrt(var_a * var_b)``, against rounding."""
    bound = math.sqrt(max(var_a, 0.0) * max(var_b, 0.0))
    return max(-bound, min(bound, c))


class _Joint(NamedTuple):
    """The posterior one response is scored against; see ``RaschEstimator._joint``."""

    glob: Skill
    touched: dict[str, Skill]  # the item's labels, aged to the response
    shares: dict[str, float]  # each label's coefficient in the linear predictor
    covs: dict[str, float]  # label -> Cov(global, label), non-zero entries only
    u0: float  # Cov(global, s)
    u: dict[str, float]  # label -> Cov(label, s)
    v_s: float  # Var(s)


def expit(x: float) -> float:
    """The logistic function, overflow-safe at the tails.

    >>> expit(0.0)
    0.5
    >>> round(expit(2.0), 4)
    0.8808
    >>> expit(-10000.0)  # a naive 1/(1+exp(-x)) would raise OverflowError here
    0.0
    """
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def logit(p: float, *, eps: float = 1e-6) -> float:
    """Inverse of :func:`expit`, clamped away from 0 and 1 so it stays finite.

    >>> logit(0.5)
    0.0
    >>> round(logit(0.8808), 3)
    2.0
    >>> logit(0.0) < -10
    True
    """
    p = min(max(p, eps), 1.0 - eps)
    return math.log(p / (1.0 - p))


def difficulty_from_rank(rank: int, n_ranks: int) -> float:
    """Map an ordinal difficulty band (1-based, 1 = easiest) to a proportion in (0, 1).

    Published difficulty is often an ordinal band rather than a measured pass rate. This
    spreads ``n_ranks`` bands evenly across the open unit interval. It is a *prior*, not a
    measurement: it says band 3 is harder than band 2, and how much is then corrected by
    data.

    >>> [round(difficulty_from_rank(r, 3), 3) for r in (1, 2, 3)]
    [0.25, 0.5, 0.75]
    >>> round(difficulty_from_rank(1, 1), 3)
    0.5
    """
    if not 1 <= rank <= n_ranks:
        raise ValueError(f"rank {rank} out of range 1..{n_ranks}")
    return rank / (n_ranks + 1)


def mark_not_reached(responses: Sequence[Response]) -> list[Response]:
    """Flag the trailing run of blanks in one sitting as *not reached*.

    A blank at the end of a paper usually means the clock ran out; a blank with answered
    questions after it is a decision to skip. Only the second is evidence about the
    student. Pass one sitting's responses **in the order they were presented**.

    >>> from learny.tracing.records import Response, Outcome
    >>> rs = [Response('a', f'q{i}', o) for i, o in
    ...       enumerate(['correct', 'skipped', 'wrong', 'skipped', 'skipped'])]
    >>> [r.meta.get('not_reached', False) for r in mark_not_reached(rs)]
    [False, False, False, True, True]
    """
    out = list(responses)
    for i in range(len(out) - 1, -1, -1):
        if out[i].outcome is not Outcome.SKIPPED:
            break
        meta = dict(out[i].meta)
        meta["not_reached"] = True
        out[i] = Response(out[i].student, out[i].item, out[i].outcome, at=out[i].at, meta=meta)
    return out


@dataclass(frozen=True)
class Skill:
    """A Gaussian belief about one skill, on the logit scale.

    >>> s = Skill(mu=0.5, var=0.25, n=4)
    >>> round(s.sd, 3)
    0.5
    >>> lo, hi = s.interval()
    >>> round(lo, 2), round(hi, 2)
    (-0.48, 1.48)
    """

    mu: float
    var: float
    n: int = 0
    t: float | None = None

    @property
    def sd(self) -> float:
        return math.sqrt(self.var)

    def interval(self, z: float = 1.96) -> tuple[float, float]:
        """A credible interval on the logit scale."""
        return self.mu - z * self.sd, self.mu + z * self.sd


@dataclass(frozen=True)
class Mastery:
    """What the model believes about one student and one label.

    ``probability`` is the chance of success on an item of *average* difficulty, which is
    what makes two labels comparable. ``confidence`` is a genuine posterior quantity, not
    a heuristic: it falls out of the variance.

    ``deviation`` is the label's posterior *relative to the student's own global skill*,
    when the estimator has one (``None`` otherwise). It is what "credibly weaker than
    their own level" is judged on (:meth:`LearnerModel.weakest
    <learny.tracing.model.LearnerModel.weakest>`), so an estimator provides it through
    this field rather than a caller reading the estimator's private state.

    >>> m = Mastery('fractions', Skill(mu=0.5, var=0.25, n=4), prior_var=1.0)
    >>> round(m.probability, 3)
    0.622
    >>> round(m.confidence, 3)
    0.75
    """

    label: str
    skill: Skill
    prior_var: float = 1.0
    deviation: Skill | None = field(default=None, kw_only=True, compare=False)
    #: The deviation's loading on what every label of this student shares — for the
    #: default estimator, its covariance with the global skill over the global skill's
    #: sd — so that two labels' deviations covary by ``loading_a * loading_b``. 0 (the
    #: default) treats the deviations as independent.
    loading: float = field(default=0.0, kw_only=True, compare=False)

    @property
    def mu(self) -> float:
        return self.skill.mu

    @property
    def n(self) -> int:
        return self.skill.n

    @property
    def probability(self) -> float:
        """Probability of success on an item of average difficulty for this label."""
        return expit(self.skill.mu)

    @property
    def confidence(self) -> float:
        """How much of the prior uncertainty has been resolved, in ``[0, 1)``."""
        return max(0.0, 1.0 - self.skill.var / self.prior_var)

    def interval(self, z: float = 1.96) -> tuple[float, float]:
        """A credible interval for :attr:`probability`."""
        lo, hi = self.skill.interval(z)
        return expit(lo), expit(hi)


@runtime_checkable
class Estimator(Protocol):
    """The seam. Anything with these four methods can replace the default.

    ``observe`` must be a pure function of ``(state, response, item)``, so that folding it
    over a response log reproduces live state exactly. That is the contract which lets the
    estimator be swapped without migrating any data.
    """

    def init(self) -> dict[str, Any]:
        """A fresh state for a student who has answered nothing."""

    def observe(
        self, state: Mapping[str, Any], response: Response, item: Item | None
    ) -> dict[str, Any]:
        """Return the new state after one response. Must not mutate ``state``."""

    def predict(self, state: Mapping[str, Any], item: Item) -> float:
        """Probability this student answers this item correctly."""

    def mastery(self, state: Mapping[str, Any]) -> dict[str, Mastery]:
        """Per-label mastery, for showing the model to the learner.

        Fill each :attr:`Mastery.deviation` (the label relative to the student's global
        skill) if you can: :meth:`LearnerModel.weakest
        <learny.tracing.model.LearnerModel.weakest>` gates on it by default and raises
        ``TypeError`` for an estimator that leaves it ``None`` (callers can still pass
        ``credible_below=None``).
        """


@dataclass
class RaschEstimator:
    """Online Rasch with a Gaussian posterior. The default estimator.

    >>> est = RaschEstimator()
    >>> item = Item('q1', labels=('fractions',), difficulty=0.5)
    >>> state = est.init()
    >>> round(est.predict(state, item), 3)       # knows nothing: the item's own base rate
    0.5
    >>> state = est.observe(state, Response('ada', 'q1', Outcome.CORRECT), item)
    >>> est.predict(state, item) > 0.5           # one correct answer moves it up
    True
    >>> est.mastery(state)['fractions'].confidence > 0   # and resolves some uncertainty
    True

    Getting a *hard* item right is stronger evidence than getting an easy one right —
    which is the property a plain success/failure count cannot have:

    >>> easy, hard = Item('e', difficulty=0.1), Item('h', difficulty=0.9)
    >>> got_hard = est.observe(est.init(), Response('a', 'h', Outcome.CORRECT), hard)
    >>> got_easy = est.observe(est.init(), Response('a', 'e', Outcome.CORRECT), easy)
    >>> got_hard['global']['mu'] > got_easy['global']['mu']
    True

    A blank that the student never reached is not evidence, and changes nothing:

    >>> blank = Response('a', 'q1', Outcome.SKIPPED, meta={'not_reached': True})
    >>> est.observe(est.init(), blank, item) == est.init()
    True
    """

    #: Prior variance on the student's global skill, in logits². 1.0 is a weak prior:
    #: roughly, "this student is within ±2 logits of the reference population".
    prior_var: float = 1.0
    #: Prior variance on each label's *deviation* from the global skill. Smaller than
    #: ``prior_var`` on purpose — this is the shrinkage that keeps a label with three
    #: observations from drifting away from what the student's whole record says.
    label_prior_var: float = 0.25
    #: Probability of getting an item right by guessing. For 5-option multiple choice,
    #: 0.2. Left at 0 by default because it is a property of the assessment, not of the
    #: model, and a wrong value here quietly biases everything.
    guess: float = 0.0
    #: Variance added per week since a skill was last seen, so a stale belief re-opens to
    #: new evidence. Inflating variance says "we know less now", which is true; decaying
    #: the mean would say "the skill got worse", which is a guess.
    forget_per_week: float = 0.02
    #: Weight given to an interior blank, treated as a soft observation at the guessing
    #: rate. Scoring an abstention as wrong is more biased than ignoring it; both are worse
    #: than a half-weight soft observation.
    abstain_weight: float = 0.5
    #: 0 = compensatory (labels trade off, a weighted mean). Larger values approach
    #: weakest-link/conjunctive: the hardest label for this student dominates.
    conjunctivity: float = 0.0
    #: ``'bayes'`` uses the posterior precision as the step size. ``'elo'`` freezes it at
    #: ``elo_rate``, which is classical Elo.
    gain: str = "bayes"
    elo_rate: float = 0.6
    #: Co-estimate item difficulty. Only sound with many learners per item; see the class
    #: docstring for why that is off by default.
    update_difficulty: bool = False

    # -- state ---------------------------------------------------------------------

    def init(self) -> dict[str, Any]:
        """A fresh state: average skill at full prior uncertainty, no label evidence."""
        return {
            "global": {"mu": 0.0, "var": self.prior_var, "n": 0, "t": None},
            "labels": {},
        }

    def _skill(self, entry: Mapping[str, Any] | None, *, prior_var: float) -> Skill:
        if entry is None:
            return Skill(mu=0.0, var=prior_var, n=0, t=None)
        return Skill(
            mu=float(entry["mu"]), var=float(entry["var"]),
            n=int(entry.get("n", 0)), t=entry.get("t"),
        )

    def _aged(self, skill: Skill, now: float | None, prior_var: float) -> Skill:
        """Inflate variance for time elapsed since this skill was last seen."""
        if now is None or skill.t is None or self.forget_per_week <= 0:
            return skill
        weeks = max(0.0, (now - skill.t) / _WEEK)
        if not weeks:
            return skill
        # Capped at the prior, but never lowered: a variance the joint update has left
        # above the cap is only ever inflated, so the stored covariances stay valid.
        var = min(skill.var + self.forget_per_week * weeks, max(prior_var, skill.var))
        return Skill(mu=skill.mu, var=var, n=skill.n, t=skill.t)

    # -- the model -----------------------------------------------------------------

    def _difficulty(self, state: Mapping[str, Any], item: Item) -> float:
        """Item difficulty on the logit scale; 0 (average) when nothing is known."""
        learned = state.get("items", {}).get(item.id)
        if learned is not None:
            return float(learned["b"])
        return 0.0 if item.difficulty is None else logit(item.difficulty)

    def _shares(
        self, item: Item, skills: Mapping[str, Skill]
    ) -> dict[str, float]:
        """Each label's share of the item's linear predictor.

        With ``conjunctivity=0`` these are the normalised label weights, so the label part
        is a weighted mean of the deviations — labels compensate for each other. As
        ``conjunctivity`` grows it becomes a soft minimum, so the label the student is
        weakest on dominates, which is the conjunctive (weakest-link) reading of a
        multi-skill item. The soft-min shares are evaluated at the posterior means and
        then held fixed as the linearisation of the predictor (they are not
        differentiated), exactly as the mean-field update did.
        """
        weights = item.weights
        total = sum(weights.values())
        if not total:
            return {}
        base = {label: w / total for label, w in weights.items()}
        if self.conjunctivity <= 0:
            return base
        lam = self.conjunctivity  # soft-min: shares are the softmax of -lambda * mu
        lo = min(skills[label].mu for label in base)
        terms = {
            label: base[label] * math.exp(-lam * (skills[label].mu - lo)) for label in base
        }
        denom = sum(terms.values()) or 1.0
        return {label: t / denom for label, t in terms.items()}

    def _joint(
        self, state: Mapping[str, Any], item: Item, now: float | None
    ) -> _Joint:
        """The posterior over ``(global, the item's labels)``, aged to ``now``, and its
        covariance with the item's linear predictor.

        The posterior is a Gaussian whose labels are conditionally independent given the
        global skill (a star around it). It is stored as each skill's marginal ``(mu,
        var)`` plus each label's covariance with the global skill (``cov``, 0 when
        absent, which is the mean-field state of older versions). Label-label covariance
        is implied: ``cov_i * cov_j / var_global``. ``u`` is ``Cov(skill, s)`` for the
        linear predictor ``s = global + sum(share * label)``; a label the item does not
        carry still covaries with ``s`` through the global skill, with share 0.
        """
        glob = self._aged(
            self._skill(state.get("global"), prior_var=self.prior_var), now, self.prior_var
        )
        entries = state.get("labels", {})
        touched = {
            label: self._aged(
                self._skill(entries.get(label), prior_var=self.label_prior_var),
                now, self.label_prior_var,
            )
            for label in item.weights
        }
        shares = self._shares(item, touched)
        vg = glob.var
        # (var, cov) of every label that covaries with s: the item's own labels (aged)
        # and any other label with a covariance on the global skill (aged lazily, when
        # it is next touched -- independent drift commutes with this update).
        pairs: dict[str, tuple[float, float]] = {}
        for label, skill in touched.items():
            pairs[label] = (skill.var, _clamp_cov(_cov(entries.get(label)), vg, skill.var))
        for label, entry in entries.items():
            if label not in pairs and entry.get("cov"):
                var = float(entry["var"])
                pairs[label] = (var, _clamp_cov(float(entry["cov"]), vg, var))
        covs = {label: c for label, (_, c) in pairs.items() if c}
        u0 = vg + sum(share * pairs[label][1] for label, share in shares.items())
        u: dict[str, float] = {}
        for label, (var, c) in pairs.items():
            beta = c / vg if vg > 0 else 0.0
            u[label] = shares.get(label, 0.0) * (var - c * beta) + beta * u0
        v_s = u0 + sum(share * u[label] for label, share in shares.items())
        return _Joint(glob, touched, shares, covs, u0, u, max(v_s, 0.0))

    def predict(self, state: Mapping[str, Any], item: Item, *, at: float | None = None) -> float:
        """Probability of a correct answer, integrating over the posterior.

        With no evidence the prediction sits near the item's own base rate, but pulled
        toward a coin flip — because the model is being honest that it knows nothing about
        *this* student, not just repeating what it knows about the item:

        >>> est = RaschEstimator()
        >>> base_rate = 1 - 0.75
        >>> cold = est.predict(est.init(), Item('q', difficulty=0.75))
        >>> base_rate < cold < 0.5
        True
        >>> round(cold, 3)
        0.283

        Shrink the prior and it converges on the base rate, as it should:

        >>> sure = RaschEstimator(prior_var=1e-6)
        >>> round(sure.predict(sure.init(), Item('q', difficulty=0.75)), 3)
        0.25
        """
        joint = self._joint(state, item, at)
        label_mu = sum(
            share * joint.touched[label].mu for label, share in joint.shares.items()
        )
        s = joint.glob.mu + label_mu - self._difficulty(state, item)
        # The predictor's variance is h' Sigma h over the joint posterior, covariances
        # included, so it is the variance of the posterior the update actually carries.
        # MacKay's probit approximation to the logistic integral: uncertainty pulls the
        # prediction toward a coin flip rather than asserting the mean's confidence.
        q = expit(s / math.sqrt(1.0 + math.pi * joint.v_s / 8.0))
        return self.guess + (1.0 - self.guess) * q

    # -- the update ----------------------------------------------------------------

    def _target(self, response: Response) -> tuple[float, float] | None:
        """``(target, weight)`` for a response, or ``None`` to make no update."""
        outcome = response.outcome
        if outcome is Outcome.CORRECT:
            return 1.0, 1.0
        if outcome is Outcome.WRONG:
            return 0.0, 1.0
        if response.meta.get("not_reached"):
            return None  # the clock ran out; not evidence about the student
        if self.abstain_weight <= 0:
            return None
        # An interior blank is a decision not to answer: a soft observation at the
        # guessing rate, never a wrong answer.
        return self.guess, self.abstain_weight

    def observe(
        self, state: Mapping[str, Any], response: Response, item: Item | None
    ) -> dict[str, Any]:
        """The new state after one response. Pure: ``state`` is not mutated.

        One Newton (Laplace) step on the *joint* log-posterior over the global skill and
        every label: a rank-1 update of the covariance along ``Cov(skill, s)``. Because
        the global/label covariance is carried, a shortfall that every item shares is
        attributed to the global skill rather than to whichever label has the largest
        share of each item (#23). The result is projected back onto the stored star
        structure, which keeps every ``(global, label)`` pair exactly and drops only the
        residual label-label correlation given the global skill.
        """
        scored = self._target(response)
        if scored is None:
            return {k: (dict(v) if isinstance(v, dict) else v) for k, v in state.items()}
        if self.gain not in ("bayes", "elo"):
            raise ValueError(f"gain must be 'bayes' or 'elo', got {self.gain!r}")
        target, weight = scored
        item = item if item is not None else Item(response.item)
        now = response.at

        joint = self._joint(state, item, now)
        glob = joint.glob
        label_mu = sum(
            share * joint.touched[label].mu for label, share in joint.shares.items()
        )
        s = glob.mu + label_mu - self._difficulty(state, item)

        # Plug-in at the posterior mean for the update itself.
        q = expit(s)
        p = self.guess + (1.0 - self.guess) * q
        dp_ds = (1.0 - self.guess) * q * (1.0 - q)
        denom = max(p * (1.0 - p), 1e-9)
        score = weight * (target - p) * dp_ds / denom        # gradient of the log-likelihood
        info = weight * dp_ds * dp_ds / denom                # Fisher information

        new = {
            "global": dict(state.get("global", {})) or dict(self.init()["global"]),
            "labels": {k: dict(v) for k, v in state.get("labels", {}).items()},
        }
        if "items" in state:
            new["items"] = {k: dict(v) for k, v in state["items"].items()}

        # Bayes: the posterior gain Sigma h / (1 + info * h' Sigma h). Elo: the fixed gain
        # elo_rate * h of classical Elo, which moves only the skills the item names; the
        # covariance is tracked as in Bayes either way, for reporting.
        shrink = info / (1.0 + info * joint.v_s)
        bayes = self.gain == "bayes"
        step = score / (1.0 + info * joint.v_s)

        u0 = joint.u0
        new["global"] = {
            "mu": glob.mu + (u0 * step if bayes else self.elo_rate * score),
            "var": max(glob.var - shrink * u0 * u0, _MIN_VAR),
            "n": glob.n + 1,
            "t": now if now is not None else glob.t,
        }
        vg = new["global"]["var"]
        entries = state.get("labels", {})
        for label, u in joint.u.items():
            share = joint.shares.get(label, 0.0)
            if label in joint.shares:
                skill = joint.touched[label]
                n, t = skill.n + 1, (now if now is not None else skill.t)
                mu = skill.mu + (u * step if bayes else self.elo_rate * share * score)
            elif label in entries:  # carried along by its covariance with the global skill
                skill = self._skill(entries[label], prior_var=self.label_prior_var)
                n, t = skill.n, skill.t
                mu = skill.mu + (u * step if bayes else 0.0)
            else:  # named by an item whose weights are all zero: no evidence on it
                continue
            var = max(skill.var - shrink * u * u, _MIN_VAR)
            cov = _clamp_cov(joint.covs.get(label, 0.0) - shrink * u0 * u, vg, var)
            new["labels"][label] = {"mu": mu, "var": var, "n": n, "t": t, "cov": cov}

        if self.update_difficulty:
            items = new.setdefault("items", {})
            entry = items.setdefault(item.id, {"b": self._difficulty(state, item), "n": 0})
            rate = self.elo_rate / (1.0 + 0.05 * entry["n"])
            entry["b"] -= rate * (target - p)
            entry["n"] += 1

        return new

    # -- reading it back -------------------------------------------------------------

    def mastery(self, state: Mapping[str, Any]) -> dict[str, Mastery]:
        """Per-label mastery: the student's global skill adjusted by each label."""
        glob = self._skill(state.get("global"), prior_var=self.prior_var)
        out: dict[str, Mastery] = {}
        for label, entry in state.get("labels", {}).items():
            dev = self._skill(entry, prior_var=self.label_prior_var)
            # Var(global + deviation) includes their covariance, which the joint update
            # makes negative: the two are not learned independently.
            cov = _clamp_cov(_cov(entry), glob.var, dev.var)
            var = glob.var + dev.var + 2.0 * cov
            out[label] = Mastery(
                label=label,
                skill=Skill(mu=glob.mu + dev.mu, var=max(var, _MIN_VAR), n=dev.n, t=dev.t),
                prior_var=self.prior_var + self.label_prior_var,
                deviation=dev,
                loading=cov / glob.sd if glob.var > 0 else 0.0,
            )
        return out

    def skill(self, state: Mapping[str, Any]) -> Skill:
        """The student's global skill, independent of any label."""
        return self._skill(state.get("global"), prior_var=self.prior_var)
