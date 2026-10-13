"""The facade: one object that records responses and answers questions about a student.

``LearnerModel`` is the thing most callers touch. It owns four collaborators, each one a
constructor argument with a working default, so the simple case needs no arguments at all
and every part can be replaced without touching the others:

==================  ==========================================================
``items``           what is known about each question (labels, difficulty)
``estimator``       how one response changes belief (:class:`~learny.tracing.estimators.RaschEstimator`)
``log``             the append-only record of responses — the source of truth
``estimates``       the cache of per-student state, rebuildable from ``log``
==================  ==========================================================
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from statistics import NormalDist
from typing import Any, Literal

from learny.tracing.diagnostics import (
    DEFAULT_N_BINS,
    DEFAULT_SEPARATION_THRESHOLD,
    CalibrationReport,
    LabelSeparation,
    calibration,
    label_separation,
)
from learny.tracing.estimators import RaschEstimator, Estimator, Mastery
from learny.tracing.records import Item, Outcome, Response
from learny.tracing.stores import ResponseLog, estimate_store, response_log

__all__ = [
    "LearnerModel",
    "Weakest",
    "DEFAULT_CREDIBLE_BELOW",
    "DEFAULT_RELATIVE_TO",
    "DEFAULT_MULTIPLICITY",
]

#: How many posterior standard deviations below its comparator a label must be before
#: :meth:`LearnerModel.weakest` calls it a weakness. 1.0 is a one-sided ~84% credible
#: bound. With the default ``multiplicity="sidak"`` it is the bound for the *whole set*
#: of labels tested — a student with no real weakness gets a label flagged at most about
#: one time in six, however many labels there are — and with ``multiplicity="none"`` it is per
#: label. It stops a set of labels that never vary independently (many labels on every
#: item) from being ranked at all. Raise it when a false "practise this" is costly.
DEFAULT_CREDIBLE_BELOW = 1.0

#: What a label's weakness is measured against. ``"labels"``: the precision-weighted mean
#: of the student's *other* labels, so a shortfall shared by every label — which the
#: default estimator splits between global skill and each label by its priors — cancels
#: out. ``"global"``: the student's global skill (zero deviation), as the original gate
#: did.
#: With ``"labels"`` a student with evidence on a single label has nothing to compare it
#: with, so nothing is credibly weak.
DEFAULT_RELATIVE_TO = "labels"

#: How the bound accounts for testing several labels at once. ``"sidak"`` raises the
#: per-label z so the chance of *any* false flag is at most ``1 - Phi(credible_below)``
#: (less in practice: a shrunk posterior's sd overstates how far its mean wanders);
#: ``"none"`` applies ``credible_below`` to each label separately, as the original
#: gate did.
DEFAULT_MULTIPLICITY = "sidak"

WeakestReason = Literal["no_evidence", "no_credible_weakness"]
RelativeTo = Literal["labels", "global"]
Multiplicity = Literal["sidak", "none"]
_RELATIVE_TO = ("labels", "global")
_MULTIPLICITY = ("sidak", "none")


def _sidak_z(z: float, m: int) -> float:
    """The per-label z that keeps the chance of any of ``m`` one-sided exceedances at
    the chance of one at ``z`` (Šidák, exact for independent tests).

    >>> _sidak_z(1.0, 1)
    1.0
    >>> round(_sidak_z(1.0, 6), 2), round(_sidak_z(1.0, 20), 2)
    (1.91, 2.38)
    >>> _sidak_z(math.inf, 6)
    inf
    """
    alpha = NormalDist().cdf(-z)  # family-wise one-sided tail, accurate for large z
    if m <= 1 or alpha == 0.0:  # one test, or a tail beyond float resolution
        return z
    per_label = -math.expm1(math.log1p(-alpha) / m)
    return -NormalDist().inv_cdf(per_label)


def _contrasts(
    masteries: Sequence[Mastery], relative_to: RelativeTo
) -> list[tuple[float, float]]:
    """Each label's ``(mean, sd)`` relative to its comparator, in the order given.

    ``"global"`` is the deviation itself. ``"labels"`` subtracts the precision-weighted
    mean of the *other* labels' deviations (leave-one-out, so a label is never compared
    with itself) and needs at least two labels; posteriors are treated as independent,
    as the estimator stores them.
    """
    devs = [m.deviation for m in masteries]
    if relative_to == "global":
        return [(d.mu, d.sd) for d in devs]
    for m, d in zip(masteries, devs):
        if not d.var > 0:
            raise ValueError(
                f"Label {m.label!r} has a deviation variance of {d.var!r}; measuring "
                "it against the other labels needs a positive posterior variance."
            )

    def contrast(i: int) -> tuple[float, float]:
        rest = [d for j, d in enumerate(devs) if j != i]
        rest_prec = sum(1.0 / d.var for d in rest)
        rest_mu = sum(d.mu / d.var for d in rest) / rest_prec
        return devs[i].mu - rest_mu, math.sqrt(devs[i].var + 1.0 / rest_prec)

    return [contrast(i) for i in range(len(devs))]


class Weakest(list):
    """What :meth:`LearnerModel.weakest` returns: a list of ``Mastery``, plus why.

    It *is* a list — it compares, iterates, slices and serialises like one — so callers
    that treat the result as a list keep working. ``reason`` is ``None`` when the list is
    non-empty and says why it is empty otherwise; see :meth:`LearnerModel.weakest`. It
    describes the answer as returned: slicing gives a plain list, and a caller that
    mutates the result owns keeping ``reason`` meaningful.

    >>> w = Weakest(reason='no_evidence')
    >>> w == [], w.reason
    (True, 'no_evidence')
    """

    def __init__(
        self, masteries: Iterable[Mastery] = (), *, reason: WeakestReason | None = None
    ):
        super().__init__(masteries)
        self.reason = reason


class LearnerModel:
    """What a student knows, estimated from what they have answered.

    >>> items = {
    ...     'q1': Item('q1', labels=('fractions',), difficulty=0.25),
    ...     'q2': Item('q2', labels=('fractions', 'area'), difficulty=0.75),
    ... }
    >>> model = LearnerModel(items=items, log={}, estimates={})
    >>> round(model.predict('ada', 'q2'), 3)  # no data: near the item's own pass rate
    0.286
    >>> model.record('ada', 'q1', 'correct')
    >>> model.record('ada', 'q2', 'wrong')
    >>> 0.0 < model.predict('ada', 'q2') < 1.0
    True
    >>> sorted(model.mastery('ada'))
    ['area', 'fractions']

    Getting a hard item wrong should leave the student looking weaker on the labels it
    exercises than a student who has answered nothing:

    >>> model.mastery('ada')['area'].mu < model.mastery('ada')['fractions'].mu
    True
    """

    def __init__(
        self,
        *,
        items: Mapping[str, Item] | None = None,
        estimator: Estimator | None = None,
        log: ResponseLog | Any | None = None,
        estimates: Mapping[str, Any] | None = None,
    ):
        self.items = dict(items) if items is not None else {}
        self.estimator = estimator if estimator is not None else RaschEstimator()
        self.log = log if log is not None else response_log()
        self.estimates = estimates if estimates is not None else estimate_store()

    # -- recording ---------------------------------------------------------------

    def record(
        self,
        student: str,
        item: str,
        outcome: Outcome | str | bool,
        *,
        at: float | None = None,
        **meta: Any,
    ) -> None:
        """Log one response and fold it into the student's estimate.

        The log is written first: if updating the cache fails, the evidence survives and
        :meth:`replay` can rebuild from it.
        """
        response = Response(student, item, Outcome(outcome), at=at, meta=meta)
        self._append(response)
        state = self._state(student)
        self.estimates[student] = self.estimator.observe(
            state, response, self.items.get(item)
        )

    def record_many(self, responses: Iterable[Response]) -> None:
        """Record a batch — a whole paper, say — in the order given."""
        for response in responses:
            self.record(
                response.student,
                response.item,
                response.outcome,
                at=response.at,
                **dict(response.meta),
            )

    # -- asking ------------------------------------------------------------------

    def predict(self, student: str, item: str | Item) -> float:
        """Probability that ``student`` answers ``item`` correctly."""
        item_obj = item if isinstance(item, Item) else self.items.get(item, Item(item))
        return self.estimator.predict(self._state(student), item_obj)

    def mastery(self, student: str) -> dict[str, Mastery]:
        """Per-label mastery for one student, weakest first when sorted by skill."""
        return self.estimator.mastery(self._state(student))

    def weakest(
        self,
        student: str,
        n: int = 5,
        *,
        credible_below: float | None = DEFAULT_CREDIBLE_BELOW,
        relative_to: RelativeTo = DEFAULT_RELATIVE_TO,
        multiplicity: Multiplicity = DEFAULT_MULTIPLICITY,
    ) -> Weakest:
        """The labels this student is credibly weakest on — what to practise next.

        By default a label is returned only when it is credibly below the student's
        *other* labels: the upper bound ``c + z * sd`` of its contrast ``c`` — its
        :attr:`Mastery.deviation <learny.tracing.estimators.Mastery.deviation>` minus the
        precision-weighted mean deviation of every other label with evidence — is below
        zero. The survivors are ranked worst first and the first ``n`` returned.

        Three keywords set the gate:

        * ``credible_below`` — the z of the bound (default :data:`DEFAULT_CREDIBLE_BELOW`,
          ~84% one-sided); larger ``z`` demands more certainty. With
          ``multiplicity="none"``, ``z = 0`` keeps every label merely below its
          comparator on average. ``None`` switches the gate off and ranks every
          label with evidence by posterior mean — check :meth:`separation` before
          believing that ranking.
        * ``multiplicity`` — ``"sidak"`` (default) corrects for testing every label with
          evidence at once, so ``z`` bounds the chance of *any* false flag; ``"none"``
          applies ``z`` to each label separately, which with six labels and no real
          weakness flags something more often than not.
        * ``relative_to`` — ``"labels"`` (default) as above; ``"global"`` measures each
          label's deviation against zero, the student's global skill. With the default
          estimator that split comes from the priors, so part of a uniform shortfall
          lands on every label and a student weak everywhere sees several labels
          returned; measured against the other labels, a shared shortfall cancels. So
          evidence on a single label is never a credible weakness here — there is
          nothing to compare it with. When unlabelled items carry the comparison (a
          label against the rest of the paper), use ``"global"``.

        ``multiplicity="none", relative_to="global"`` restores the original per-label gate.

        Labels with no evidence are never included: the model has nothing to say about
        them, and saying it anyway is how a learner model loses trust.

        **An empty answer is common and says why.** The result is a list (a
        :class:`Weakest`) whose ``reason`` is ``None`` when it holds labels, and
        otherwise one of:

        * ``"no_evidence"`` — the student has answered nothing that carries a label;
        * ``"no_credible_weakness"`` — there is evidence, but no label is credibly
          below the rest of the student's record. That is a statement about *relative*
          weakness, not "nothing to practise": practise at the student's overall level
          (``model.estimator.skill(state)`` for the default estimator).

        Raises ``ValueError`` for a negative ``credible_below`` (which would admit labels
        credibly *above* their comparator) or an unknown ``relative_to`` /
        ``multiplicity``, and ``TypeError`` when the gate is on but
        the estimator's :class:`~learny.tracing.estimators.Mastery` values carry no
        ``deviation`` — rather than silently returning nothing.

        >>> items = {f'q{i}': Item(f'q{i}', labels=('area' if i % 2 else 'sums',))
        ...          for i in range(40)}
        >>> model = LearnerModel(items=items, log={}, estimates={})
        >>> model.weakest('ada')
        []
        >>> model.weakest('ada').reason
        'no_evidence'
        >>> for i in range(40):  # right on every sum, wrong on every area question
        ...     model.record('ada', f'q{i}', 'wrong' if i % 2 else 'correct')
        >>> [m.label for m in model.weakest('ada')]
        ['area']
        >>> [m.label for m in model.weakest('ada', credible_below=None)]  # plain ranking
        ['area', 'sums']
        >>> [m.label for m in model.weakest('ada', relative_to='global', multiplicity='none')]
        ['area']
        """
        if not (isinstance(n, int) and n >= 1):
            raise ValueError(f"n must be a positive integer, got {n!r}")
        if credible_below is not None and not credible_below >= 0:
            raise ValueError(
                f"credible_below must be >= 0 (or None to rank without a gate), got "
                f"{credible_below!r}: a negative z admits labels credibly above the "
                "student's own level."
            )
        if relative_to not in _RELATIVE_TO:
            raise ValueError(
                f"relative_to must be one of {_RELATIVE_TO}, got {relative_to!r}"
            )
        if multiplicity not in _MULTIPLICITY:
            raise ValueError(
                f"multiplicity must be one of {_MULTIPLICITY}, got {multiplicity!r}"
            )
        ranked = sorted(self.mastery(student).values(), key=lambda m: m.mu)
        if not ranked:
            return Weakest(reason="no_evidence")
        if credible_below is None:
            return Weakest(ranked[:n])
        if any(m.deviation is None for m in ranked):
            raise TypeError(
                f"weakest(credible_below={credible_below!r}) needs each Mastery to carry "
                f"a .deviation (the label relative to the student's global skill), and "
                f"{type(self.estimator).__name__}.mastery() does not provide one. Fill "
                "Mastery.deviation in the estimator, or pass credible_below=None to rank "
                "by posterior mean without the gate."
            )
        if relative_to == "labels" and len(ranked) < 2:
            return Weakest(reason="no_credible_weakness")
        z = (
            _sidak_z(credible_below, len(ranked))
            if multiplicity == "sidak"
            else credible_below
        )
        credible = [
            m
            for m, (mu, sd) in zip(ranked, _contrasts(ranked, relative_to))
            if mu + z * sd < 0.0
        ]
        if not credible:
            return Weakest(reason="no_credible_weakness")
        return Weakest(credible[:n])

    # -- when to believe it --------------------------------------------------------

    def separation(
        self, student: str, *, threshold: float = DEFAULT_SEPARATION_THRESHOLD
    ) -> LabelSeparation:
        """How distinguishable this student's labels are; see :func:`label_separation`.

        Check ``.distinguishable`` before acting on an ordering from :meth:`weakest`.
        """
        return label_separation(self._state(student), threshold=threshold)

    def calibration(
        self, students: Iterable[str] | None = None, *, n_bins: int = DEFAULT_N_BINS
    ) -> CalibrationReport:
        """Prequential calibration over the log; see :func:`calibration`.

        Reads the log only; the estimate cache is neither used nor changed.
        """
        names = list(students) if students is not None else self._students()
        log = {name: self._responses(name) for name in names}
        return calibration(log, items=self.items, estimator=self.estimator, n_bins=n_bins)

    # -- the contract that makes the estimator replaceable ------------------------

    def replay(self, student: str | None = None) -> None:
        """Rebuild estimates from the log, discarding the cache.

        This is what makes changing the estimator a re-run rather than a migration, and
        it is asserted by the tests: folding ``observe`` over the log must reproduce the
        state that live recording produced.
        """
        students = [student] if student is not None else self._students()
        for name in students:
            state = self.estimator.init()
            for response in self._responses(name):
                state = self.estimator.observe(
                    state, response, self.items.get(response.item)
                )
            self.estimates[name] = state

    # -- store plumbing ----------------------------------------------------------
    # `log` is either a ResponseLog or any mapping-like stand-in (a plain dict is
    # genuinely useful in tests and notebooks), so these three adapt to both.

    def _append(self, response: Response) -> None:
        if hasattr(self.log, "append"):
            self.log.append(response)
        else:
            self.log.setdefault(response.student, []).append(response)

    def _students(self) -> list[str]:
        if hasattr(self.log, "students"):
            return self.log.students()
        return sorted(self.log)

    def _responses(self, student: str) -> list[Response]:
        try:
            return list(self.log[student])
        except KeyError:
            return []

    def _state(self, student: str) -> dict[str, Any]:
        try:
            return dict(self.estimates[student])
        except KeyError:
            return self.estimator.init()

