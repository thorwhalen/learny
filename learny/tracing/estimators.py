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

An ordered score — 1 to 5 stars, partial credit — is read by
:class:`PartialCreditEstimator`, Masters' Partial Credit Model on the same predictor. It is
this estimator with one method replaced (the likelihood of a response), so everything
below holds for it too, and a right/wrong response is scored exactly as here.

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

**The posterior is joint, but stored in O(labels) and updated in O(labels on the
item).** Labels are kept conditionally independent given the global skill (a star around
it), and each is stored as its regression on the global skill: ``label = offset + beta *
global + e`` with ``Var(e) = cond_var``. Its marginal ``(mu, var)`` and its covariance
with the global skill are read back from that (``mastery()`` reports them), and
label-label covariance is implied as ``cov_a * cov_b / var_global``. One response is one
rank-1 (Laplace) update of the joint covariance, followed by the projection back onto the
star that keeps every ``(global, label)`` pair exactly; a label the item does not name
keeps its regression exactly, so only the item's labels are rewritten. Forgetting adds
independent drift to each skill and leaves the covariances alone; the global skill's
share of that is carried for all labels at once by a *frame* on the global entry. The
``conjunctivity`` soft-min shares are linearised at the posterior means, as before.
States written before this layout -- labels as ``(mu, var)``, optionally with ``cov`` --
read unchanged, and need no migration.

**A skip is not a wrong answer, and not all skips are alike.** A blank at the end of a
paper is a clock, not a judgement; a blank with answers after it is an abstention, which
carries real information about confidence. They are treated differently, and neither is
scored as wrong.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from numbers import Real
from typing import Any, NamedTuple, Protocol, runtime_checkable

from learny.tracing.records import Item, Outcome, Response

__all__ = [
    "Estimator",
    "RaschEstimator",
    "PartialCreditEstimator",
    "binomial_thresholds",
    "spread_thresholds",
    "SpreadThresholds",
    "Mastery",
    "Skill",
    "logit",
    "expit",
    "difficulty_from_rank",
    "mark_not_reached",
]

_WEEK = 7 * 24 * 3600.0
_MIN_VAR = 1e-12  # floor on a stored variance, so precision-weighted reads stay finite


#: Below this frame scale every label is re-expressed in a fresh frame (see ``_Frame``).
#: The stored slopes grow as ``1 / scale``, so this bounds the cancellation in reading a
#: label back to about ``1 / scale**2`` ulps (1e4: ~1e-12 at unit scale).
_FRAME_FLOOR = 1e-2


class _Frame(NamedTuple):
    """What forgetting has done to the global skill since every label was last written.

    A label is stored as its regression on the global skill (``label = offset + beta *
    global + e``, ``Var(e) = cond_var``), which a response that does not name the label
    leaves unchanged, so only the item's own labels are rewritten. Forgetting (drift on
    the global skill that leaves each covariance as it was) does change every label's
    regression, by the same affine map for all of them; the frame accumulates that map
    so that no label has to be rewritten either: a label stored as ``(slope, resid_var,
    offset)`` reads as ``beta = slope * scale``, ``cond_var = resid_var + slope**2 *
    resid``, ``offset = offset + slope * shift``.
    """

    scale: float = 1.0
    resid: float = 0.0
    shift: float = 0.0

    @classmethod
    def of(cls, glob: Mapping[str, Any] | None) -> _Frame:
        frame = (glob or {}).get("frame")
        if not frame:
            return cls()
        return cls(float(frame["scale"]), float(frame["resid"]), float(frame["shift"]))

    def as_dict(self) -> dict[str, float]:
        return {"scale": self.scale, "resid": self.resid, "shift": self.shift}

    def forget(self, mu: float, var: float, aged: float) -> _Frame:
        """The frame after the global variance goes from ``var`` to ``aged``."""
        if aged == var or aged <= 0:
            return self
        r = var / aged
        return _Frame(
            self.scale * r,
            self.resid + self.scale**2 * var * (1.0 - r),
            self.shift + self.scale * (1.0 - r) * mu,
        )

    def store(self, beta: float, cond_var: float, offset: float) -> dict[str, float]:
        """A label's regression, as stored in this frame."""
        slope = beta / self.scale
        return {
            "slope": slope,
            "resid_var": cond_var - slope * slope * self.resid,
            "offset": offset - slope * self.shift,
        }


def _regression(
    entry: Mapping[str, Any], frame: _Frame, glob: Skill
) -> tuple[float, float, float]:
    """``(beta, cond_var, offset)`` of a stored label on the stored global skill.

    A label written before the regression form (``mu``, ``var`` and an optional ``cov``)
    is read as its marginals at the stored global skill: ``cov`` absent, ``None`` or 0
    is the mean-field state (``beta = 0``).
    """
    if "slope" in entry:
        slope = float(entry["slope"])
        return (
            slope * frame.scale,
            float(entry["resid_var"]) + slope * slope * frame.resid,
            float(entry["offset"]) + slope * frame.shift,
        )
    mu, var = float(entry["mu"]), float(entry["var"])
    cov = float(entry.get("cov") or 0.0)
    if not cov or glob.var <= 0:
        return 0.0, var, mu
    cov = _clamp_cov(cov, glob.var, var)
    beta = cov / glob.var
    return beta, max(var - cov * beta, _MIN_VAR), mu - beta * glob.mu


def _clamp_cov(c: float, var_a: float, var_b: float) -> float:
    """Keep a covariance inside ``|c| <= sqrt(var_a * var_b)``, against rounding."""
    bound = math.sqrt(max(var_a, 0.0) * max(var_b, 0.0))
    return max(-bound, min(bound, c))


def _null(entry: Mapping[str, Any]) -> dict[str, float]:
    """A label entry's null fields (``Mastery.null_var`` and ``null_k3``), to carry them
    over when the entry is re-expressed: plain cumulants, not frame-relative, since
    neither forgetting nor a change of frame moves the label's mean."""
    return {k: float(entry[k]) for k in ("nv", "nk3") if k in entry}


class _Label(NamedTuple):
    """One label's marginal posterior and its regression on the global skill."""

    skill: Skill  # the deviation's marginal (mu, var, n, t)
    cov: float  # Cov(global, label)
    beta: float  # cov / var_global
    cond_var: float  # var - cov * beta: Var(label | global)
    null_var: float | None = None  # the deviation mean's spread with no real deviation
    null_k3: float | None = None  # and its third cumulant


class _Evidence(NamedTuple):
    """What one response says about the item's linear predictor ``s``."""

    gradient: float  # what the Bayes step moves s by, times (1 + information * v_s)
    information: float  # the curvature that shrinks the posterior along s
    residual: float  # observed minus expected, unit scale: moves a co-estimated difficulty
    elo: float  # the fixed-gain (gain='elo') step, before elo_rate
    noise: float  # Var(gradient) under the model, for a skip a bound (see _likelihood)
    noise3: float  # its third cumulant: a rare outcome is a large, one-sided jump


class _Joint(NamedTuple):
    """The posterior one response is scored against; see ``RaschEstimator._joint``."""

    glob: Skill  # aged to the response
    frame: _Frame  # the stored frame, advanced by the global's ageing
    labels: dict[str, _Label]  # the item's labels, aged to the response
    shares: dict[str, float]  # each label's coefficient in the linear predictor
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
        out[i] = replace(out[i], meta={**out[i].meta, "not_reached": True})
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
    #: How far this label's own evidence moves ``deviation.mu`` by chance, as a sampling
    #: variance, had the student no real deviation on it: the spread a test of "is this
    #: label really weaker than the others?" is calibrated to. Smaller than
    #: ``deviation.var`` because a posterior mean is shrunk, and tracked rather than
    #: derived from it because forgetting re-opens the posterior variance without moving
    #: the mean (the identity ``v - v**2 / tau**2`` breaks; #11). The part of the label's
    #: movement that rides on the global skill is common to every label and is left out,
    #: so that a leave-one-out contrast's spread is the sum of its labels' ``null_var``.
    #: ``None``: not tracked (the posterior variance is the conservative stand-in); the
    #: default estimator tracks it under ``gain='bayes'``.
    null_var: float | None = field(default=None, kw_only=True, compare=False)
    #: The third cumulant of the same sampling distribution. A student who mostly gets a
    #: label right makes a rare wrong answer a large one-sided jump, so the null is
    #: skewed and its lower tail is heavier than a normal one with ``null_var``; a test
    #: of many labels at once lives in that tail. ``None``: not tracked (no correction).
    null_k3: float | None = field(default=None, kw_only=True, compare=False)

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
        ``credible_below=None``). :attr:`Mastery.null_var` calibrates that gate; left
        ``None``, the gate falls back to the more cautious posterior bound.
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
        var = min(skill.var + self.forget_per_week * weeks, prior_var)
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
        covariance with the item's linear predictor ``s = global + sum(share * label)``.

        Labels are conditionally independent given the global skill (a star around it),
        so only the item's own labels enter: a label the item does not carry covaries
        with ``s`` only through the global skill, and is not needed to score or to
        update. Cost is O(labels on the item), however many labels the state holds.
        """
        stored = self._skill(state.get("global"), prior_var=self.prior_var)
        glob = self._aged(stored, now, self.prior_var)
        stored_frame = _Frame.of(state.get("global"))
        frame = stored_frame.forget(stored.mu, stored.var, glob.var)
        r = stored.var / glob.var if glob.var > 0 else 1.0
        entries = state.get("labels", {})
        labels: dict[str, _Label] = {}
        for label in item.weights:
            entry = entries.get(label)
            if entry is None:
                beta, cond_var, offset = 0.0, self.label_prior_var, 0.0
                n, t = 0, None
                null_var = null_k3 = 0.0  # the prior mean is exact: no sampling spread
            else:
                beta, cond_var, offset = _regression(entry, stored_frame, stored)
                n, t = int(entry.get("n", 0)), entry.get("t")
                null_var, null_k3 = _null(entry).get("nv"), _null(entry).get("nk3")
                # the global skill's ageing, which leaves Cov(global, label) as it was
                cond_var += beta * beta * stored.var * (1.0 - r)
                offset += beta * (1.0 - r) * stored.mu
                beta *= r
            cov = beta * glob.var
            marginal = Skill(
                mu=offset + beta * glob.mu, var=cond_var + beta * cov, n=n, t=t
            )
            # the label's own ageing: independent drift, so all of it is conditional
            aged = self._aged(marginal, now, self.label_prior_var)
            cond_var = max(cond_var + aged.var - marginal.var, _MIN_VAR)
            labels[label] = _Label(aged, cov, beta, cond_var, null_var, null_k3)
        shares = self._shares(item, {k: v.skill for k, v in labels.items()})
        u0 = glob.var + sum(share * labels[k].cov for k, share in shares.items())
        u = {
            k: share * labels[k].cond_var + labels[k].beta * u0
            for k, share in shares.items()
        }
        v_s = u0 + sum(share * u[k] for k, share in shares.items())
        return _Joint(glob, frame, labels, shares, u0, u, max(v_s, 0.0))

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
        q = expit(self._integrated_predictor(state, item, at))
        return self.guess + (1.0 - self.guess) * q

    def _integrated_predictor(
        self, state: Mapping[str, Any], item: Item, at: float | None
    ) -> float:
        """The item's linear predictor ``s``, scaled for its posterior uncertainty.

        The predictor's variance is h' Sigma h over the joint posterior, covariances
        included, so it is the variance of the posterior the update actually carries.
        MacKay's probit approximation to the logistic integral: ``expit`` of the result
        is ``E[expit(s)]``, so uncertainty pulls a prediction toward a coin flip rather
        than asserting the mean's confidence.
        """
        joint = self._joint(state, item, at)
        label_mu = sum(
            share * joint.labels[label].skill.mu for label, share in joint.shares.items()
        )
        s = joint.glob.mu + label_mu - self._difficulty(state, item)
        return s / math.sqrt(1.0 + math.pi * joint.v_s / 8.0)

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

    def _likelihood(
        self, response: Response, item: Item, s: float, v_s: float
    ) -> _Evidence:
        """What one response says about the predictor, whose posterior is ``N(s, v_s)``.

        The gradient and Fisher information of the response's log-likelihood with respect
        to the item's linear predictor, which is all the joint update needs; the residual
        (observed minus expected, on the unit scale) that moves a co-estimated item
        difficulty; and Elo's fixed-gain step. Here they are evaluated at the posterior
        mean (one Newton step), for a response :meth:`_target` did not discard. This is
        the one place the dichotomous model lives, so a different response model
        overrides it and inherits the rest.
        """
        target, weight = self._target(response)
        q = expit(s)
        p = self.guess + (1.0 - self.guess) * q
        dp_ds = (1.0 - self.guess) * q * (1.0 - q)
        denom = max(p * (1.0 - p), 1e-9)
        score = weight * (target - p) * dp_ds / denom        # gradient of the log-likelihood
        info = weight * dp_ds * dp_ds / denom                # Fisher information
        if response.outcome.is_scored:  # the gradient is a * (y - p), y ~ Bernoulli(p)
            a = weight * dp_ds / denom
            noise, noise3 = a * a * p * (1 - p), a**3 * p * (1 - p) * (1 - 2 * p)
        else:
            # A skip's target is fixed, but whether a student skips is random, at a rate
            # q the model does not know, and any response could have been one: over N
            # responses that adds N q (1 - q) jump**2, which is (1 - q) jump**2 per skip
            # that happened. Its bound, jump**2 (and jump**3), is charged per skip (#22).
            noise, noise3 = score * score, score**3
        return _Evidence(score, info, target - p, score, noise, noise3)

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

        Only the global skill and the item's labels are written: every other label is
        stored as its regression on the global skill, which this update leaves exactly
        as it was (see ``_Frame``).
        """
        if self._target(response) is None:
            return {k: (dict(v) if isinstance(v, dict) else v) for k, v in state.items()}
        if self.gain not in ("bayes", "elo"):
            raise ValueError(f"gain must be 'bayes' or 'elo', got {self.gain!r}")
        item = item if item is not None else Item(response.item)
        now = response.at

        joint = self._joint(state, item, now)
        glob = joint.glob
        label_mu = sum(
            share * joint.labels[label].skill.mu for label, share in joint.shares.items()
        )
        s = glob.mu + label_mu - self._difficulty(state, item)

        score, info, residual, elo, noise, noise3 = self._likelihood(
            response, item, s, joint.v_s
        )

        # Entries are replaced, never edited in place, so unchanged ones are shared.
        new = {
            "global": dict(state.get("global", {})) or dict(self.init()["global"]),
            "labels": dict(state.get("labels", {})),
        }
        if "items" in state:
            new["items"] = {k: dict(v) for k, v in state["items"].items()}
        # Written before the regression form: a label with a covariance is read relative
        # to the global skill as stored, so pin it there, in the stored frame. Any such
        # label is converted, whatever the global entry holds: a hand-made or merged state
        # can mix the two forms, and an unconverted label would not follow the global
        # skill when it moves (#27).
        stored = self._skill(state.get("global"), prior_var=self.prior_var)
        stored_frame = _Frame.of(state.get("global"))
        for label, entry in state.get("labels", {}).items():
            if "slope" not in entry and entry.get("cov"):
                new["labels"][label] = {
                    **stored_frame.store(*_regression(entry, stored_frame, stored)),
                    "n": int(entry.get("n", 0)), "t": entry.get("t"),
                    **_null(entry),
                }

        # Bayes: the posterior gain Sigma h / (1 + info * h' Sigma h). Elo: the fixed gain
        # elo_rate * h of classical Elo, which moves only the skills the item names; the
        # covariance is tracked as in Bayes either way, for reporting.
        shrink = info / (1.0 + info * joint.v_s)
        bayes = self.gain == "bayes"
        step = score / (1.0 + info * joint.v_s)

        u0 = joint.u0
        moved = u0 * step if bayes else self.elo_rate * elo
        mu_g = glob.mu + moved
        vg = max(glob.var - shrink * u0 * u0, _MIN_VAR)
        frame = joint.frame
        if not bayes:
            # A label Elo does not name keeps its mean although the global skill moved.
            frame = frame._replace(shift=frame.shift - frame.scale * moved)
        if frame.scale < _FRAME_FLOOR:
            # Re-express every stored label in a fresh frame before the stored slopes grow
            # large enough to cost precision: O(labels), once per many weeks of drift. It
            # comes before the item's labels are written, so they are stored in the fresh
            # frame directly rather than in the collapsed one and re-expressed (#27).
            fresh = _Frame()
            for label, entry in new["labels"].items():
                if "slope" in entry:
                    new["labels"][label] = {
                        **fresh.store(*_regression(entry, frame, glob)),
                        "n": entry["n"], "t": entry["t"],
                        **_null(entry),
                    }
            frame = fresh
        for label, share in joint.shares.items():
            lab, u = joint.labels[label], joint.u[label]
            mu = lab.skill.mu + (u * step if bayes else self.elo_rate * share * elo)
            var = max(lab.skill.var - shrink * u * u, _MIN_VAR)
            cov = _clamp_cov(lab.cov - shrink * u0 * u, vg, var)
            beta = cov / vg
            new["labels"][label] = {
                **frame.store(beta, max(var - cov * beta, _MIN_VAR), mu - beta * mu_g),
                "n": lab.skill.n + 1,
                "t": now if now is not None else lab.skill.t,
            }
            if bayes:
                # A label stored before this was tracked starts, conservatively, at its
                # posterior variance. The gain is the stored offset's, which moves by
                # u - beta' * u0 = share * Var(label | global) + (beta - beta') * u0: the
                # rest of the label's move rides on the global skill, is common to every
                # label, and cancels in a contrast between them (Mastery.null_var).
                before = lab.skill.var if lab.null_var is None else lab.null_var
                before3 = 0.0 if lab.null_k3 is None else lab.null_k3
                gain = (u - beta * u0) / (1.0 + info * joint.v_s)
                decay = 1.0 - gain * info * share
                new["labels"][label]["nv"] = decay * decay * before + gain * gain * noise
                new["labels"][label]["nk3"] = decay**3 * before3 + gain**3 * noise3
        new["global"] = {
            "mu": mu_g,
            "var": vg,
            "n": glob.n + 1,
            "t": now if now is not None else glob.t,
            "frame": frame.as_dict(),
        }

        if self.update_difficulty:
            items = new.setdefault("items", {})
            entry = items.setdefault(item.id, {"b": self._difficulty(state, item), "n": 0})
            rate = self.elo_rate / (1.0 + 0.05 * entry["n"])
            entry["b"] -= rate * residual
            entry["n"] += 1

        return new

    # -- reading it back -------------------------------------------------------------

    def _labels(self, state: Mapping[str, Any]) -> Iterable[tuple[str, _Label]]:
        """Every stored label's marginal posterior, at the stored global skill."""
        glob = self._skill(state.get("global"), prior_var=self.prior_var)
        frame = _Frame.of(state.get("global"))
        for label, entry in state.get("labels", {}).items():
            beta, cond_var, offset = _regression(entry, frame, glob)
            cov = beta * glob.var
            skill = Skill(
                mu=offset + beta * glob.mu,
                var=cond_var + beta * cov,
                n=int(entry.get("n", 0)),
                t=entry.get("t"),
            )
            null = _null(entry)
            yield label, _Label(skill, cov, beta, cond_var, null.get("nv"), null.get("nk3"))

    def mastery(self, state: Mapping[str, Any]) -> dict[str, Mastery]:
        """Per-label mastery: the student's global skill adjusted by each label."""
        glob = self._skill(state.get("global"), prior_var=self.prior_var)
        out: dict[str, Mastery] = {}
        for label, lab in self._labels(state):
            dev = lab.skill
            # Var(global + deviation) includes their covariance, which the joint update
            # makes negative: the two are not learned independently.
            var = glob.var + dev.var + 2.0 * lab.cov
            out[label] = Mastery(
                label=label,
                skill=Skill(mu=glob.mu + dev.mu, var=max(var, _MIN_VAR), n=dev.n, t=dev.t),
                prior_var=self.prior_var + self.label_prior_var,
                deviation=dev,
                loading=lab.cov / glob.sd if glob.var > 0 else 0.0,
                null_var=lab.null_var,
                null_k3=lab.null_k3,
            )
        return out

    def skill(self, state: Mapping[str, Any]) -> Skill:
        """The student's global skill, independent of any label."""
        return self._skill(state.get("global"), prior_var=self.prior_var)


# -- ordered scores ----------------------------------------------------------------

#: Step thresholds for an item scored ``0..max_score``: ``max_score`` logits, step ``k``
#: being the predictor at which levels ``k - 1`` and ``k`` are equally likely, relative to
#: the item's difficulty. The ``thresholds`` seam of :class:`PartialCreditEstimator`.
Thresholds = Callable[[Item, int], Sequence[float]]


def binomial_thresholds(item: Item, max_score: int) -> list[float]:
    """Thresholds under which a score out of ``m`` is ``m`` steps taken at one rate.

    ``tau_k = log(k / (m - k + 1))``. With these, the Partial Credit Model's distribution
    of the score is binomial with step rate ``expit(skill - difficulty)``, so the expected
    *fraction* of the maximum equals the right/wrong model's probability of a correct
    answer, and an item's ``difficulty`` means the same thing however it is scored. That
    is why it is the default: it is the one choice that keeps an externally calibrated
    difficulty meaningful with no new parameters (with ``guess=0``: a score is never a
    guess). It is not a claim that the steps really are independent, and it makes a score
    out of ``m`` carry up to ``m`` times the evidence of one right/wrong answer; thresholds
    spread wider apart carry less.

    >>> binomial_thresholds(Item('q'), 1)  # one step: the right/wrong model
    [0.0]
    >>> [round(t, 3) for t in binomial_thresholds(Item('q'), 4)]
    [-1.386, -0.405, 0.405, 1.386]
    """
    return [math.log(k / (max_score - k + 1)) for k in range(1, max_score + 1)]


@dataclass(frozen=True)
class SpreadThresholds:
    """Binomial thresholds stretched by ``spread``; see :func:`spread_thresholds`.

    A frozen dataclass rather than a closure, so an estimator holding one pickles, and
    two with the same spread compare equal.
    """

    spread: float

    def __post_init__(self) -> None:
        if isinstance(self.spread, bool) or not (
            isinstance(self.spread, (int, float)) and self.spread > 0
            and math.isfinite(self.spread)
        ):
            raise ValueError(f"spread must be a positive number, got {self.spread!r}")

    def __call__(self, item: Item, max_score: int) -> list[float]:
        return [self.spread * t for t in binomial_thresholds(item, max_score)]


def spread_thresholds(spread: float) -> SpreadThresholds:
    """Binomial thresholds stretched by ``spread``: ``tau_k = spread * log(k / (m - k + 1))``.

    ``spread=1`` is :func:`binomial_thresholds`. A wider spread makes the middle levels
    more likely and the extremes rarer, so one score carries less evidence; narrower
    makes a score sharper. It keeps the thresholds centred, so an item's ``difficulty``
    still sits at the middle of its scale. :func:`~learny.tracing.diagnostics.fit_threshold_spread`
    picks ``spread`` from a log.

    >>> [round(t, 3) for t in spread_thresholds(2.0)(Item('q'), 2)]
    [-1.386, 1.386]
    >>> spread_thresholds(1.0)(Item('q'), 4) == binomial_thresholds(Item('q'), 4)
    True
    >>> spread_thresholds(2.0) == spread_thresholds(2.0)
    True
    """
    return SpreadThresholds(spread)


@dataclass(frozen=True)
class ItemSpreads:
    """Per-item threshold spreads from a table, ``fallback`` for the items it does not hold.

    The ``thresholds`` seam's reader for the table
    :func:`~learny.tracing.diagnostics.fit_item_spreads` exports: an item in ``spreads``
    gets ``spread_thresholds(spreads[item.id])``, any other item ``fallback(item, m)``
    (default :func:`binomial_thresholds`; usually the global spread the table was fitted
    against). ``to_dict``/``from_dict`` carry the table, not the fallback, which is code.

    >>> t = ItemSpreads({'sharp': 0.5}, fallback=spread_thresholds(2.0))
    >>> [round(x, 3) for x in t(Item('sharp'), 2)], [round(x, 3) for x in t(Item('other'), 2)]
    ([-0.347, 0.347], [-1.386, 1.386])
    >>> ItemSpreads.from_dict(t.to_dict(), fallback=spread_thresholds(2.0)) == t
    True
    """

    spreads: Mapping[str, float]
    fallback: Thresholds = binomial_thresholds

    #: The ``schema`` tag of :meth:`to_dict`, so a reader can tell a table it understands.
    schema = "learny.item_spreads/1"

    def __post_init__(self) -> None:
        table = {str(item_id): SpreadThresholds(c).spread for item_id, c in self.spreads.items()}
        object.__setattr__(self, "spreads", table)

    def __call__(self, item: Item, max_score: int) -> Sequence[float]:
        spread = self.spreads.get(item.id)
        if spread is None:
            return self.fallback(item, max_score)
        return SpreadThresholds(spread)(item, max_score)

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "spreads": dict(self.spreads)}

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any], *, fallback: Thresholds = binomial_thresholds
    ) -> ItemSpreads:
        if data.get("schema") != cls.schema:
            raise ValueError(
                f"not an item spreads table: schema {data.get('schema')!r}, "
                f"expected {cls.schema!r}"
            )
        return cls(data["spreads"], fallback=fallback)


def _level_probabilities(s: float, taus: Sequence[float]) -> list[float]:
    """``P(X = k)`` for ``k = 0..len(taus)`` under the Partial Credit Model at ``s``."""
    eta = [0.0]
    for tau in taus:
        eta.append(eta[-1] + s - tau)
    top = max(eta)  # subtracted before exponentiating, so no level overflows
    weights = [math.exp(e - top) for e in eta]
    total = sum(weights)
    return [w / total for w in weights]


def _posterior_mode(
    s: float,
    v: float,
    gradient: Callable[[float], float],
    information: Callable[[float], float],
    *,
    steps: int,
    tol: float = 1e-12,
) -> float | None:
    """The mode of ``N(t; s, v) * likelihood(t)`` for a log-concave likelihood.

    ``gradient`` and ``information`` are the log-likelihood's first derivative and minus
    its second. The objective's derivative ``f`` falls monotonically, so the mode lies
    between ``s`` and the first Newton step from it. Safeguarded Newton inside that
    bracket: a Newton step is taken only when it lands strictly inside the bracket and
    the previous step converged fast enough, otherwise the bracket is bisected, and the
    bracket shrinks at every evaluation, so it cannot cycle. ``None`` when there is
    nothing to iterate (``steps <= 1``, or no posterior width).
    """
    if steps <= 1 or not v > 0:
        return None

    def f(t: float) -> float:
        return -(t - s) / v + gradient(t)

    lo, hi = sorted((s, s + v * gradient(s)))
    t, ft = s, f(s)
    dx = dx_old = hi - lo
    for _ in range(steps):
        if ft == 0.0 or hi - lo <= tol * (1.0 + abs(t)):
            return t
        slope = 1.0 / v + information(t)  # -f'(t) > 0
        newton = t + ft / slope
        dx_old, dx = dx, (newton - t)
        if not lo < newton < hi or abs(2.0 * ft) > abs(dx_old * slope):
            dx = 0.5 * (hi - lo)
            newton = lo + dx
        if abs(newton - t) <= tol * (1.0 + abs(t)):
            return newton
        t, ft = newton, f(newton)
        if ft > 0:
            lo = t
        else:
            hi = t
    return t


@dataclass
class PartialCreditEstimator(RaschEstimator):
    """Masters' Partial Credit Model on the Rasch predictor: reads an ordered score.

    A response with a ``score`` out of ``max_score`` is scored on its levels
    ``0..max_score``, with ``s`` the same predictor as :class:`RaschEstimator`'s (global
    skill plus label deviations minus item difficulty)::

        P(X = k)  proportional to  exp(sum over j <= k of (s - tau_j))

    The thresholds ``tau_j`` come from the ``thresholds`` seam, by default
    :func:`binomial_thresholds`. The log-likelihood's gradient in ``s`` is
    ``k - E[X]`` and its Fisher information ``Var[X]``, which is all the joint update
    needs, so the hierarchy, forgetting, the global/label covariance and replay are the
    default estimator's, unchanged. For a score the update iterates to the posterior mode
    along the predictor (``mode_steps``), since one Newton step overshoots on a surprising
    score out of many levels. A response *without* a score is a right/wrong answer and is
    scored exactly as :class:`RaschEstimator` scores it — guessing, skips and all.

    **``guess`` applies only to responses without a score**: a score is never modelled as
    a guess, so on a multiple-choice item that is also scored, ``expected_score`` is not
    ``max_score * predict()`` unless ``guess=0``. For a score, ``outcome`` is not read,
    and a score that contradicts it is not an error: the outcome is the caller's own
    right/wrong reading of the attempt.

    >>> est = PartialCreditEstimator()
    >>> item = Item('song-7/tempo', labels=('tempo',), difficulty=0.5)
    >>> def skill_after(stars):
    ...     r = Response('ada', item.id, 'correct', score=stars - 1, max_score=4)
    ...     return est.observe(est.init(), r, item)['global']['mu']
    >>> skill_after(2) < skill_after(3) < skill_after(4) < skill_after(5)
    True
    >>> skill_after(3)  # the middle of the scale on an average item is no news
    0.0
    >>> est.expected_score(est.init(), item, 4)
    2.0

    ``predict`` keeps the :class:`Estimator` meaning, the probability of a correct
    answer on a right/wrong reading of the item; :meth:`expected_score` and
    :meth:`score_probabilities` answer for a score.
    """

    #: How an item scored ``0..max_score`` places its steps; see :data:`Thresholds`.
    thresholds: Thresholds = binomial_thresholds
    #: Newton iterations allowed to find the posterior mode along the predictor for a
    #: score. One step (the right/wrong update's plug-in) is fine for a few stars but
    #: overshoots on a surprising score out of many levels, whose gradient is bounded by
    #: ``max_score`` rather than by 1; iterating to the mode (a Laplace step) does not.
    #: ``1`` restores the plain one-step update.
    mode_steps: int = 50

    def __post_init__(self) -> None:
        if isinstance(self.mode_steps, bool) or not isinstance(self.mode_steps, int) \
                or self.mode_steps < 1:
            raise ValueError(f"mode_steps must be an int >= 1, got {self.mode_steps!r}")

    def _taus(self, item: Item, max_score: int) -> list[float]:
        taus = list(self.thresholds(item, max_score))
        if len(taus) != max_score:
            raise ValueError(
                f"thresholds({item.id!r}, {max_score}) returned {len(taus)} thresholds; "
                f"a score out of {max_score} needs exactly {max_score}"
            )
        bad = [t for t in taus if isinstance(t, bool) or not isinstance(t, Real)
               or not math.isfinite(t)]
        if bad:
            raise ValueError(
                f"thresholds({item.id!r}, {max_score}) must be finite numbers (logits), "
                f"got {bad!r}"
            )
        return [float(t) for t in taus]

    def _likelihood(
        self, response: Response, item: Item, s: float, v_s: float
    ) -> _Evidence:
        if response.score is None:
            return super()._likelihood(response, item, s, v_s)
        k, m = response.score, response.max_score
        taus = self._taus(item, m)

        def moments(t: float) -> tuple[float, float]:
            probs = _level_probabilities(t, taus)
            mean = sum(j * p for j, p in enumerate(probs))
            return mean, max(sum(j * j * p for j, p in enumerate(probs)) - mean * mean, 0.0)

        mean, var = moments(s)
        third = sum((j - mean) ** 3 * p for j, p in enumerate(_level_probabilities(s, taus)))
        residual = k - mean
        mode = _posterior_mode(s, v_s, lambda t: k - moments(t)[0],
                               lambda t: moments(t)[1], steps=self.mode_steps)
        if mode is None:  # one step, or no posterior width to move in
            gradient, info = residual, var
        else:
            info = moments(mode)[1]
            # the gradient that makes the shared rank-1 update land on the mode, with the
            # posterior's curvature taken there: a Laplace step along the predictor
            gradient = (mode - s) * (1.0 + info * v_s) / v_s
        # d(mode)/dk = v / (1 + v * info), so the effective gradient moves one for one
        # with the score: its sampling variance is the score's, Var[X] at the plug-in.
        return _Evidence(gradient, info, residual / m, residual / m, var, third)

    def score_probabilities(
        self,
        state: Mapping[str, Any],
        item: Item,
        max_score: int,
        *,
        at: float | None = None,
    ) -> list[float]:
        """``P(score = k)`` for ``k = 0..max_score``, over the posterior.

        The posterior is integrated with the same probit approximation as
        :meth:`~RaschEstimator.predict`, so with the default thresholds and ``guess=0``
        the expected score is exactly ``max_score * predict()``; both are approximations
        to the posterior integral. Guessing is not modelled for a score (see the class).

        >>> est = PartialCreditEstimator()
        >>> [round(p, 3) for p in est.score_probabilities(est.init(), Item('q'), 2)]
        [0.25, 0.5, 0.25]
        """
        s = self._integrated_predictor(state, item, at)
        return _level_probabilities(s, self._taus(item, max_score))

    def expected_score(
        self,
        state: Mapping[str, Any],
        item: Item,
        max_score: int,
        *,
        at: float | None = None,
    ) -> float:
        """The expected score out of ``max_score``; see :meth:`score_probabilities`."""
        probs = self.score_probabilities(state, item, max_score, at=at)
        return sum(k * p for k, p in enumerate(probs))
