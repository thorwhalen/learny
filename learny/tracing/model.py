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
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from statistics import NormalDist
from typing import Any, Literal

from learny.tracing.diagnostics import (
    DEFAULT_N_BINS,
    DEFAULT_SEPARATION_THRESHOLD,
    CalibrationReport,
    LabelSeparation,
    ScoreCalibrationReport,
    calibration,
    label_separation,
    score_calibration,
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
    "DEFAULT_NULL_DRAWS",
]

#: How many posterior standard deviations below its comparator a label must be before
#: :meth:`LearnerModel.weakest` calls it a weakness. 1.0 is a one-sided ~84% credible
#: bound. With the default ``multiplicity="calibrated"`` (and ``"bonferroni"``) it is the
#: bound for the *whole set* of labels tested — a student with no real weakness gets a
#: label flagged about one time in six at most, however many labels there are — and with
#: ``multiplicity="none"`` it is per label. It stops a set of labels that never vary independently (many labels on every
#: item) from being ranked at all. Raise it when a false "practise this" is costly.
DEFAULT_CREDIBLE_BELOW = 1.0

#: What a label's weakness is measured against. ``"labels"``: the precision-weighted mean
#: of the student's *other* labels, so whatever part of a shortfall every label shares
#: cancels out. ``"global"``: the student's global skill (zero deviation), as the
#: original gate did.
#: With ``"labels"`` a student with evidence on a single label has nothing to compare it
#: with, so nothing is credibly weak.
DEFAULT_RELATIVE_TO = "labels"

#: How the bound accounts for testing several labels at once. ``"calibrated"`` raises the
#: per-label z as Bonferroni does, so the chance of *any* false flag is about
#: ``1 - Phi(credible_below)``, and measures each label against how far its contrast
#: would wander with no real weakness (:attr:`Mastery.null_var
#: <learny.tracing.estimators.Mastery.null_var>`) rather than against its posterior sd,
#: which a shrunk posterior mean stays well inside (#22). ``"bonferroni"`` does the same
#: on the posterior sd: a bound rather than a calibration, far below its target with
#: little evidence, so it costs power at cold start. ``"none"`` applies
#: ``credible_below`` to each label separately, as the original gate did.
DEFAULT_MULTIPLICITY = "calibrated"

WeakestReason = Literal["no_evidence", "no_credible_weakness"]
RelativeTo = Literal["labels", "global"]
Multiplicity = Literal["calibrated", "simulated", "bonferroni", "none"]

#: Fewest rare outcomes a label's null must rest on before its moments describe its
#: tail. A compound-Poisson fit to a label's null cumulants, ``nv`` and ``nk3``, puts
#: ``lambda = nv**3 / nk3**2`` rare jumps behind it (one wrong answer among a few that a
#: student nearly always gets right: ``lambda`` well below 1). With less than one, the
#: null is a single discrete event, no moment expansion holds, and the label is measured
#: by its posterior spread instead (#22, #35).
_MIN_RARE_EVENTS = 1.0
_RELATIVE_TO = ("labels", "global")
_MULTIPLICITY = ("calibrated", "simulated", "bonferroni", "none")

#: How many times ``weakest(multiplicity="simulated")`` replays a student's record under
#: "no label deviation". The critical value is the ``1 - Phi(z)`` quantile of the
#: smallest label statistic over the draws: 200 puts about 32 draws below it at ``z=1``.
DEFAULT_NULL_DRAWS = 200


def _bonferroni_z(z: float, m: int) -> float:
    """The per-label z that keeps the chance of any of ``m`` one-sided exceedances at
    most the chance of one at ``z``, under any dependence between them (Bonferroni).

    The labels' contrasts with each other are slightly negatively correlated, where the
    Šidák level, exact for independent tests, would be a little too lenient.

    >>> _bonferroni_z(1.0, 1)
    1.0
    >>> round(_bonferroni_z(1.0, 6), 2), round(_bonferroni_z(1.0, 20), 2)
    (1.94, 2.41)
    >>> _bonferroni_z(math.inf, 6)
    inf
    """
    alpha = NormalDist().cdf(-z)  # family-wise one-sided tail, accurate for large z
    if m <= 1 or alpha == 0.0:  # one test, or a tail beyond float resolution
        return z
    return -NormalDist().inv_cdf(alpha / m)


def _null_spreads(
    masteries: Sequence[Mastery], relative_to: RelativeTo
) -> list[tuple[float, float]]:
    """Each contrast's ``(sd, skewness)`` for a test calibrated to "no real weakness".

    The contrast and its weights are :func:`_contrasts`'s. Its posterior variance has two
    parts: each label's own residual (``var - loading**2``) and the part the labels share
    through the global skill (``(loading_i - weighted loadings)**2``). Only the first is
    sampling noise that shrinkage overstates, so only it is replaced, by each label's
    :attr:`Mastery.null_var <learny.tracing.estimators.Mastery.null_var>`. The shared
    part is kept at its posterior size: it is the direction in which the record cannot
    tell "weak overall" from "weak on this label", where a label's mean is moved by the
    priors' split of a shortfall rather than by chance (#23), and a test that ignored it
    would blame the most heavily weighted label for every shortfall.

    The skewness is the own parts' third cumulant (:attr:`Mastery.null_k3
    <learny.tracing.estimators.Mastery.null_k3>`, 0 when not tracked) over ``sd**3``;
    the shared part is taken as normal. A label without a ``null_var`` (an estimator
    that does not track it, or a label stored before it was tracked) contributes its
    posterior own residual instead, so with none tracked this is exactly the posterior
    contrast spread of :func:`_contrasts`.

    >>> from learny.tracing.estimators import Skill
    >>> ms = [Mastery(k, Skill(0.0, 1.0), deviation=Skill(0.0, 0.2), null_var=0.05)
    ...       for k in 'ab']
    >>> [(round(sd, 3), g) for sd, g in _null_spreads(ms, 'labels')]
    [(0.316, 0.0), (0.316, 0.0)]
    >>> heavy = [Mastery('a', Skill(0.0, 1.0), deviation=Skill(0.0, 0.2), null_var=0.05,
    ...                  loading=-0.4), ms[1]]
    >>> [round(sd, 3) for sd, _ in _null_spreads(heavy, 'labels')]  # the shared part stays
    [0.51, 0.51]
    >>> untracked = Mastery('a', Skill(0.0, 1.0), deviation=Skill(0.0, 0.2))
    >>> _null_spreads([untracked], 'global') == [(_contrasts([untracked], 'global')[0][1], 0.0)]
    True
    """
    loads = [float(getattr(m, "loading", 0.0) or 0.0) for m in masteries]

    def own(m: Mastery, a: float) -> tuple[float, float]:
        nv, k3 = m.null_var, float(getattr(m, "null_k3", None) or 0.0)
        if nv is None or (k3 and nv**3 < _MIN_RARE_EVENTS * k3 * k3):
            return max(m.deviation.var - a * a, 0.0), 0.0  # the posterior own residual
        return max(nv, 0.0), k3

    nvs, k3s = map(list, zip(*(own(m, a) for m, a in zip(masteries, loads))))

    def spread(var: float, k3: float) -> tuple[float, float]:
        sd = math.sqrt(var)
        return sd, (k3 / sd**3 if sd > 0 else 0.0)

    if relative_to == "global":
        return [spread(nv + a * a, k3) for nv, a, k3 in zip(nvs, loads, k3s)]
    devs = [m.deviation for m in masteries]

    def contrast(i: int) -> tuple[float, float]:
        rest = [j for j in range(len(devs)) if j != i]
        rest_prec = sum(1.0 / devs[j].var for j in rest)
        w = {j: 1.0 / devs[j].var / rest_prec for j in rest}
        shared = loads[i] - sum(w[j] * loads[j] for j in rest)
        var = nvs[i] + sum(w[j] ** 2 * nvs[j] for j in rest) + shared**2
        return spread(var, k3s[i] - sum(w[j] ** 3 * k3s[j] for j in rest))

    return [contrast(i) for i in range(len(devs))]


def _skew_corrected_z(z: float, skewness: float) -> float:
    """The lower-tail critical z for a null with this skewness, never below ``z``.

    First-order Cornish-Fisher: the lower ``Phi(-z)`` quantile of a standardised
    distribution with skewness ``g`` is about ``-z + (z**2 - 1) * g / 6``. A negative
    skew (a rare wrong answer is a large drop) moves it further out. A positive skew
    would move it in, where the expansion is least reliable and a gate would turn lax,
    so it is never allowed to.

    >>> _skew_corrected_z(2.0, 0.0), _skew_corrected_z(2.0, 1.5)
    (2.0, 2.0)
    >>> _skew_corrected_z(2.0, -1.2)
    2.6
    """
    return z + max(0.0, -skewness) * max(z * z - 1.0, 0.0) / 6.0


def _contrasts(
    masteries: Sequence[Mastery], relative_to: RelativeTo
) -> list[tuple[float, float]]:
    """Each label's ``(mean, sd)`` relative to its comparator, in the order given.

    ``"global"`` is the deviation itself. ``"labels"`` subtracts the precision-weighted
    mean of the *other* labels' deviations (leave-one-out, so a label is never compared
    with itself) and needs at least two labels. Its variance counts the covariance the
    deviations share through :attr:`Mastery.loading
    <learny.tracing.estimators.Mastery.loading>` (zero: independent posteriors).

    >>> from learny.tracing.estimators import Skill
    >>> ms = [Mastery(k, Skill(0.0, 1.0), deviation=Skill(mu, 0.2), loading=a)
    ...       for k, mu, a in (('a', -0.5, 0.0), ('b', 0.5, 0.0))]
    >>> [(round(c, 2), round(sd, 3)) for c, sd in _contrasts(ms, 'labels')]
    [(-1.0, 0.632), (1.0, 0.632)]
    >>> shared = [Mastery(m.label, m.skill, deviation=m.deviation, loading=-0.3) for m in ms]
    >>> [round(sd, 3) for _, sd in _contrasts(shared, 'labels')]  # what they share cancels
    [0.469, 0.469]
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
    loads = [float(getattr(m, "loading", 0.0) or 0.0) for m in masteries]

    def contrast(i: int) -> tuple[float, float]:
        rest = [j for j in range(len(devs)) if j != i]
        rest_prec = sum(1.0 / devs[j].var for j in rest)
        w = {j: 1.0 / devs[j].var / rest_prec for j in rest}
        rest_mu = sum(w[j] * devs[j].mu for j in rest)
        # One-factor covariance: d_j = loading_j * Z + e_j with Var(e_j) = var_j - a_j^2.
        shared = sum(w[j] * loads[j] for j in rest)
        var = (
            max(devs[i].var - loads[i] ** 2, 0.0)
            + sum(w[j] ** 2 * max(devs[j].var - loads[j] ** 2, 0.0) for j in rest)
            + (loads[i] - shared) ** 2
        )
        return devs[i].mu - rest_mu, math.sqrt(var)

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
        score: int | None = None,
        max_score: int | None = None,
        **meta: Any,
    ) -> None:
        """Log one response and fold it into the student's estimate.

        The log is written first: if updating the cache fails, the evidence survives and
        :meth:`replay` can rebuild from it. ``score`` out of ``max_score`` records an
        ordered score alongside the right/wrong ``outcome`` (see
        :class:`~learny.tracing.records.Response`); the default estimator reads only the
        outcome, :class:`~learny.tracing.estimators.PartialCreditEstimator` the score.

        >>> from learny.tracing.estimators import PartialCreditEstimator
        >>> items = {'song-7/tempo': Item('song-7/tempo', labels=('tempo',))}
        >>> model = LearnerModel(
        ...     items=items, estimator=PartialCreditEstimator(), log={}, estimates={}
        ... )
        >>> model.record('ada', 'song-7/tempo', 'correct', score=4, max_score=4)
        >>> model.mastery('ada')['tempo'].mu > 0
        True
        """
        self._fold(
            Response(
                student, item, Outcome(outcome), at=at, meta=meta,
                score=score, max_score=max_score,
            )
        )

    def record_many(self, responses: Iterable[Response]) -> None:
        """Record a batch — a whole paper, say — in the order given."""
        for response in responses:
            self._fold(replace(response, meta=dict(response.meta)))

    def _fold(self, response: Response) -> None:
        self._append(response)
        state = self._state(response.student)
        self.estimates[response.student] = self.estimator.observe(
            state, response, self.items.get(response.item)
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
        null_draws: int = DEFAULT_NULL_DRAWS,
    ) -> Weakest:
        """The labels this student is credibly weakest on — what to practise next.

        By default a label is returned only when it is credibly below the student's
        *other* labels: the upper bound ``c + z * sd`` of its contrast ``c`` — its
        :attr:`Mastery.deviation <learny.tracing.estimators.Mastery.deviation>` minus the
        precision-weighted mean deviation of every other label with evidence — is below
        zero. The survivors are ranked by posterior mean mastery, worst first, and the
        first ``n`` returned.

        Three keywords set the gate:

        * ``credible_below`` — the z of the bound (default :data:`DEFAULT_CREDIBLE_BELOW`,
          ~84% one-sided); larger ``z`` demands more certainty. With
          ``multiplicity="none"``, ``z = 0`` keeps every label merely below its
          comparator on average. ``None`` switches the gate off and ranks every
          label with evidence by posterior mean — check :meth:`separation` before
          believing that ranking.
        * ``multiplicity`` — ``"calibrated"`` (default) corrects for testing every label
          with evidence at once, so ``z`` sets the chance of *any* false flag (about
          one student in six with no real weakness, at ``z = 1``), and measures each
          contrast against its sampling spread under no real weakness
          (:attr:`Mastery.null_var <learny.tracing.estimators.Mastery.null_var>`) and
          skew (a rare wrong answer from a student who is usually right is a large
          drop), so the correction costs little power at cold start (#22). An estimator that does
          not fill ``null_var`` gets ``"bonferroni"`` (a label it leaves unfilled is
          measured by its posterior spread): the same correction on the posterior sd, which shrinkage already makes cautious when evidence is thin, so
          with a few responses per label even a large real weakness is rarely returned.
          ``"none"`` applies ``z`` to each label separately, which with six labels, a few
          hundred responses and no real weakness flags something more often than not.
          Under ``relative_to="global"`` the calibrated spread is more cautious (the
          part of a label's spread it shares with the others is counted, not removed).
          A label stored before null spreads were tracked is measured by its posterior
          spread until it is answered again.
          ``"simulated"`` replays the student's own record ``null_draws`` times with the
          answers redrawn as if no label deviated (``estimator.null_response``), and
          takes as critical value the ``1 - Phi(z)`` quantile of the most extreme label
          over the draws (a parametric-bootstrap maxT test, Westfall and Young 1993). It
          counts this record's discreteness, skew, forgetting and the dependence between
          labels exactly, so it keeps the false-flag rate on target where the moment
          corrections of ``"calibrated"`` are cautious: few answers per label, items the
          student nearly always gets right, or nearly always wrong (#35). It costs
          ``null_draws`` replays of the record per call, and is deterministic for a given
          student and record.
        * ``relative_to`` — ``"labels"`` (default) as above; ``"global"`` measures each
          label's deviation against zero, the student's global skill. The default
          estimator carries the global/label covariance, so a shortfall every item
          shares goes to the global skill, and where the record cannot tell "weak
          overall" from "weak on this label" the label's deviation stays wide rather
          than taking the blame (#23); the contrast with the other labels counts the
          covariance they share through it (:attr:`Mastery.loading
          <learny.tracing.estimators.Mastery.loading>`). Evidence on a single label is
          never a credible weakness under ``"labels"`` — there is nothing to compare it
          with. When unlabelled items carry the comparison (a label against the rest of
          the paper), use ``"global"``.

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
        if not (isinstance(n, int) and not isinstance(n, bool) and n >= 1):
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
            credible_below
            if multiplicity == "none"
            else _bonferroni_z(credible_below, len(ranked))
        )
        if multiplicity == "simulated":
            limit = self._simulated_limit(
                student, ranked, relative_to=relative_to,
                alpha=NormalDist().cdf(-credible_below), draws=null_draws,
            )
            credible = [
                m for m, (mu, sd) in zip(ranked, _contrasts(ranked, relative_to))
                if sd > 0 and mu / sd < limit
            ]
            return Weakest(credible[:n]) if credible else Weakest(reason="no_credible_weakness")
        contrasts = [(mu, sd, z) for mu, sd in _contrasts(ranked, relative_to)]
        if multiplicity == "calibrated":
            contrasts = [
                (mu, sd, _skew_corrected_z(z, g))
                for (mu, _, _), (sd, g) in zip(contrasts, _null_spreads(ranked, relative_to))
            ]
        credible = [m for m, (mu, sd, zi) in zip(ranked, contrasts) if mu + zi * sd < 0.0]
        if not credible:
            return Weakest(reason="no_credible_weakness")
        return Weakest(credible[:n])

    def _simulated_limit(
        self,
        student: str,
        ranked: Sequence[Mastery],
        *,
        relative_to: RelativeTo,
        alpha: float,
        draws: int,
    ) -> float:
        """The critical standardised contrast for ``weakest(multiplicity="simulated")``.

        Each draw replays this student's record with every answer redrawn at the
        student's global skill (no label deviation), and keeps the smallest
        ``contrast / sd`` over the labels the student has evidence on. A label is flagged
        when its own is below the ``alpha`` quantile of those minima, so the chance that
        *any* label of a student with no real weakness is flagged is ``alpha``, for this
        record's design.
        """
        if not (isinstance(draws, int) and not isinstance(draws, bool) and draws >= 1):
            raise ValueError(f"null_draws must be a positive integer, got {draws!r}")
        redraw = getattr(self.estimator, "null_response", None)
        if redraw is None:
            raise TypeError(
                f"weakest(multiplicity='simulated') needs the estimator to redraw a "
                f"response with no label deviation, and {type(self.estimator).__name__} "
                "has no null_response(); use multiplicity='calibrated' instead"
            )
        state = self._state(student)
        record = self._responses(student)
        labels = {m.label for m in ranked}
        rng = random.Random(f"learny.weakest:{student}:{len(record)}")
        minima = []
        for _ in range(draws):
            sim = self.estimator.init()
            for response in record:
                item = self.items.get(response.item)
                sim = self.estimator.observe(sim, redraw(state, response, item, rng), item)
            masteries = [m for m in self.estimator.mastery(sim).values() if m.label in labels]
            stats = [mu / sd for mu, sd in _contrasts(masteries, relative_to) if sd > 0]
            minima.append(min(stats) if stats else math.inf)
        minima.sort()
        return minima[int(alpha * draws)]

    # -- when to believe it --------------------------------------------------------

    def separation(
        self, student: str, *, threshold: float = DEFAULT_SEPARATION_THRESHOLD
    ) -> LabelSeparation:
        """How distinguishable this student's labels are; see :func:`label_separation`.

        Check ``.distinguishable`` before acting on an ordering from :meth:`weakest`.
        """
        return label_separation(
            self._state(student), estimator=self.estimator, threshold=threshold
        )

    def calibration(
        self, students: Iterable[str] | None = None, *, n_bins: int = DEFAULT_N_BINS
    ) -> CalibrationReport:
        """Prequential calibration over the log; see :func:`calibration`.

        Reads the log only; the estimate cache is neither used nor changed. With an
        estimator that reads scores, scored responses are left to
        :meth:`score_calibration`, so a log of scores alone gives an empty report here.
        """
        names = list(students) if students is not None else self._students()
        log = {name: self._responses(name) for name in names}
        return calibration(log, items=self.items, estimator=self.estimator, n_bins=n_bins)

    def score_calibration(
        self, students: Iterable[str] | None = None, *, n_bins: int = DEFAULT_N_BINS
    ) -> ScoreCalibrationReport:
        """Prequential calibration of the score forecasts; see :func:`score_calibration`.

        Reads the log only. Needs an estimator that reads scores, such as
        :class:`~learny.tracing.estimators.PartialCreditEstimator`.
        """
        names = list(students) if students is not None else self._students()
        log = {name: self._responses(name) for name in names}
        return score_calibration(
            log, items=self.items, estimator=self.estimator, n_bins=n_bins
        )

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

