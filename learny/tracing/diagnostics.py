"""Diagnostics: when to believe the model, and how well it has predicted so far.

A learner model that cannot say when it is guessing will eventually be shown to a learner
while it is guessing. This module answers the two questions that decide whether an
estimate is fit to show:

**Can its labels be told apart?** :func:`label_separation` computes the Rasch separation
index over one student's label *deviations* — the spread of the deviations that is not
explained by their own uncertainty, in units of that uncertainty. When labels never vary
independently of each other (an item tagged with nine labels at once, say), every
deviation stays near zero, the separation is near zero, and any ranking of the labels is
noise. The report says so rather than leaving a caller to sort noise and call it a
diagnosis.

**Are its probabilities honest?** :func:`calibration` (right/wrong) and
:func:`score_calibration` (ordered scores) replay the log *prequentially*:
each response is predicted from the state built from the responses before it, then
folded in. Nothing is scored on data it was fitted to, so the report measures prediction,
not fit. For a learner model calibration matters more than discrimination — a 70% that
comes true 40% of the time is worse than useless when it is shown to a child.

Both are pure functions of data the model already has; neither needs a new seam, and
neither looks at more than one student at a time unless asked to.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from learny.tracing.estimators import (
    Estimator,
    PartialCreditEstimator,
    RaschEstimator,
    spread_thresholds,
)
from learny.tracing.records import Item, Outcome, Response

__all__ = [
    "LabelSeparation",
    "label_separation",
    "prequential",
    "CalibrationBin",
    "CalibrationReport",
    "calibration",
    "ScoreCalibrationReport",
    "score_calibration",
    "reads_scores",
    "Comparison",
    "compare_estimators",
    "fit_threshold_spread",
    "DEFAULT_SPREADS",
    "DEFAULT_SEPARATION_THRESHOLD",
    "DEFAULT_N_BINS",
]

#: Separation at which an ordering of labels is worth believing. ``G = 2`` is reliability
#: 0.8, about three distinguishable strata (Wright's ``(4G + 1) / 3``) — the usual Rasch
#: bar for a ranking one acts on. Below ``G = 1`` (reliability 0.5) the spread of the
#: estimates is mostly their own noise.
DEFAULT_SEPARATION_THRESHOLD = 2.0

#: Equal-width probability bins for the reliability table.
DEFAULT_N_BINS = 10

_EPS = 1e-12


# -- separation --------------------------------------------------------------------


@dataclass(frozen=True)
class LabelSeparation:
    """How distinguishable one student's labels are from each other.

    ``separation`` is the Rasch separation index *G*: the "true" spread of the label
    deviations (observed variance minus mean error variance) divided by their root-mean
    error. ``reliability`` is ``G² / (1 + G²)``, the share of observed spread that is
    signal. ``distinguishable`` is the verdict a caller should act on.

    >>> s = LabelSeparation(n_labels=4, observed_sd=0.75, rmse=0.3)
    >>> round(s.true_sd, 3), round(s.separation, 3), round(s.reliability, 3)
    (0.687, 2.291, 0.84)
    >>> round(s.strata, 2)
    3.39
    >>> s.distinguishable
    True
    >>> LabelSeparation(n_labels=4, observed_sd=0.1, rmse=0.3).distinguishable
    False
    """

    n_labels: int
    observed_sd: float
    rmse: float
    threshold: float = DEFAULT_SEPARATION_THRESHOLD

    @property
    def true_sd(self) -> float:
        """Spread of the deviations with their measurement error removed."""
        return math.sqrt(max(0.0, self.observed_sd**2 - self.rmse**2))

    @property
    def separation(self) -> float:
        """Signal-to-noise of the label spread (Rasch *G*). 0 when it is all noise."""
        if self.rmse <= 0:
            return math.inf if self.true_sd > 0 else 0.0
        return self.true_sd / self.rmse

    @property
    def reliability(self) -> float:
        """``G² / (1 + G²)``: the share of the observed spread that is not noise."""
        g = self.separation
        return 1.0 if math.isinf(g) else g * g / (1.0 + g * g)

    @property
    def strata(self) -> float:
        """Wright's ``(4G + 1) / 3``: roughly how many levels the labels fall into."""
        return (4.0 * self.separation + 1.0) / 3.0

    @property
    def distinguishable(self) -> bool:
        """Whether an ordering of these labels (``weakest()``, say) is worth believing."""
        return self.n_labels >= 2 and self.separation >= self.threshold


def label_separation(
    state: Mapping[str, Any],
    *,
    estimator: Estimator | None = None,
    min_n: int = 1,
    threshold: float = DEFAULT_SEPARATION_THRESHOLD,
) -> LabelSeparation:
    """Separation of one student's label deviations, from their estimator state.

    The state is read through ``estimator.mastery()`` (default: a
    :class:`~learny.tracing.estimators.RaschEstimator`, which also reads a plain
    ``{label: {"mu", "var", "n"}}`` layout), from each label's
    :attr:`~learny.tracing.estimators.Mastery.deviation`. Only labels with at least
    ``min_n`` observations are counted; a label nobody has evidence on is not a label
    that can be told apart from anything.

    Deviations, not mastery, are what is measured: the question is whether the labels
    differ *from each other*, and every label shares the same global skill.

    The state holds *posteriors* (means ``mu`` shrunk toward zero, variances ``var``),
    not the likelihood-only measures the classical Rasch formula assumes. So this is the
    posterior (EAP) form of the index: the signal is the spread of the posterior means,
    the noise their mean posterior variance, ``G = sd(mu) / sqrt(mean(var))``, i.e.
    reliability ``var(mu) / (var(mu) + mean(var))``. In the normal-normal case with a
    correctly specified prior it equals the likelihood-based ``G`` in expectation,
    without having to know the prior. It also stays honest when the estimator has
    re-opened a stale label's variance without moving its mean (``forget_per_week``):
    that only adds noise, so it can only lower ``G`` -- whereas undoing a presumed
    shrinkage there would attribute a whole history's mean to the little evidence the
    variance still shows, and call noise distinguishable.

    ``var`` is each deviation's variance *given the global skill* (``var -
    loading**2``). What the deviations share through the global skill -- how much of
    the student's level is "overall" rather than "this label", which a record often
    cannot tell -- moves them all together, so it blurs no ordering among them.

    >>> state = {"labels": {
    ...     "fractions": {"mu": 0.9, "var": 0.02, "n": 30},
    ...     "area":      {"mu": -0.8, "var": 0.02, "n": 30},
    ... }}
    >>> label_separation(state).distinguishable
    True
    >>> blurred = {"labels": {k: {"mu": 0.01 * i, "var": 0.2, "n": 3}
    ...                       for i, k in enumerate("abcdefghi")}}
    >>> label_separation(blurred).distinguishable   # nine labels, all noise
    False
    """
    estimator = RaschEstimator() if estimator is None else estimator
    masteries = [m for m in estimator.mastery(state).values() if m.n >= min_n]
    if any(m.deviation is None for m in masteries):
        raise TypeError(
            f"label_separation() reads each label's Mastery.deviation, and "
            f"{type(estimator).__name__}.mastery() does not provide one."
        )
    k = len(masteries)
    if k == 0:
        return LabelSeparation(
            n_labels=0, observed_sd=0.0, rmse=0.0, threshold=threshold
        )
    mus = [m.deviation.mu for m in masteries]
    mean = sum(mus) / k
    signal_var = sum((m - mean) ** 2 for m in mus) / (k - 1) if k > 1 else 0.0
    # The noise is each deviation's variance *given the global skill*, var - loading²:
    # the part every label shares through the global skill (how much of the student's
    # level is "overall" rather than "this label") moves all deviations together, so
    # it blurs no ordering among them (decision 10 in docs/learner-model-design.md).
    mse = sum(max(m.deviation.var - m.loading**2, 0.0) for m in masteries) / k
    # ``LabelSeparation`` reads true variance as observed minus error; in the posterior
    # form the signal is ``var(mu)`` itself, so "observed" is signal plus error.
    return LabelSeparation(
        n_labels=k,
        observed_sd=math.sqrt(signal_var + mse),
        rmse=math.sqrt(mse),
        threshold=threshold,
    )


# -- calibration -------------------------------------------------------------------


def prequential(
    responses: Iterable[Response],
    *,
    items: Mapping[str, Item],
    estimator: Estimator,
) -> Iterator[tuple[Response, float]]:
    """Yield ``(response, p)`` where ``p`` was predicted *before* the response was seen.

    Pass one student's responses in log order. Each prediction uses only the responses
    that came before it, so this is the honest out-of-sample stream that calibration,
    and any later hyperparameter fit, should be scored on. Every response is yielded,
    skips included; filter on ``response.outcome.is_scored`` to score.

    >>> from learny.tracing.estimators import RaschEstimator
    >>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
    >>> rs = [Response('a', 'q', 'correct'), Response('a', 'q', 'correct')]
    >>> [round(p, 3) for _, p in prequential(rs, items=items, estimator=RaschEstimator())]
    [0.5, 0.6]
    """
    for response, item, state in _before_each(responses, items=items, estimator=estimator):
        yield response, estimator.predict(state, item)


def _before_each(
    responses: Iterable[Response], *, items: Mapping[str, Item], estimator: Estimator
) -> Iterator[tuple[Response, Item, Mapping[str, Any]]]:
    """``(response, item, state)`` with ``state`` built from the responses before it."""
    state = estimator.init()
    for response in responses:
        item = items.get(response.item) or Item(response.item)
        yield response, item, state
        state = estimator.observe(state, response, item)


def reads_scores(estimator: Any) -> bool:
    """Whether ``estimator`` forecasts ordered scores: it has ``score_probabilities``.

    It decides which report a scored response belongs in: an estimator without it
    forecasts the right/wrong ``outcome``, so the response is scored by
    :func:`calibration`; one with it is taken to forecast (and learn from) the score, so
    the response is scored by :func:`score_calibration` instead. It is a check of
    capability, not of what ``observe`` reads: an estimator that forecasts scores while
    learning only from outcomes should not define ``score_probabilities``.

    >>> from learny.tracing.estimators import PartialCreditEstimator, RaschEstimator
    >>> reads_scores(RaschEstimator()), reads_scores(PartialCreditEstimator())
    (False, True)
    """
    return callable(getattr(estimator, "score_probabilities", None))


def _names(log: Mapping[str, Iterable[Response]], students: Iterable[str] | None) -> list[str]:
    if students is not None:
        return list(students)
    if hasattr(log, "students"):  # a ResponseLog iterates responses, not students
        return log.students()
    return list(log)


@dataclass(frozen=True)
class CalibrationBin:
    """One row of a reliability table: predictions in ``[lo, hi)`` and what happened."""

    lo: float
    hi: float
    n: int
    mean_predicted: float
    observed_rate: float

    @property
    def gap(self) -> float:
        """Observed minus predicted: positive means the model was too pessimistic."""
        return self.observed_rate - self.mean_predicted


@dataclass(frozen=True)
class CalibrationReport:
    """Prequential scores for a set of predictions.

    ``log_loss`` and ``brier`` are proper scoring rules (lower is better). ``ece`` is the
    expected calibration error: the count-weighted mean absolute gap across bins.
    ``base_log_loss`` is what always predicting the observed success rate would score,
    so ``log_loss < base_log_loss`` means the model beats knowing only the average.
    """

    n: int
    log_loss: float
    brier: float
    ece: float
    base_log_loss: float
    bins: tuple[CalibrationBin, ...]

    @classmethod
    def from_pairs(
        cls, pairs: Sequence[tuple[float, float]], *, n_bins: int = DEFAULT_N_BINS
    ) -> "CalibrationReport":
        """Build a report from ``(predicted, observed)`` pairs, observed in ``{0, 1}``.

        >>> r = CalibrationReport.from_pairs([(0.9, 1), (0.9, 1), (0.1, 0), (0.1, 1)])
        >>> r.n, round(r.brier, 3), round(r.ece, 3)
        (4, 0.21, 0.25)
        >>> [(b.n, b.observed_rate) for b in r.bins]
        [(2, 0.5), (2, 1.0)]
        """
        if n_bins < 1:
            raise ValueError(f"n_bins must be at least 1, got {n_bins}")
        n = len(pairs)
        if n == 0:
            return cls(
                n=0,
                log_loss=math.nan,
                brier=math.nan,
                ece=math.nan,
                base_log_loss=math.nan,
                bins=(),
            )

        def nll(p: float, y: float) -> float:
            p = min(max(p, _EPS), 1.0 - _EPS)
            return -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))

        rate = sum(y for _, y in pairs) / n
        buckets: dict[int, list[tuple[float, float]]] = {}
        for p, y in pairs:
            buckets.setdefault(min(int(p * n_bins), n_bins - 1), []).append((p, y))
        bins = tuple(
            CalibrationBin(
                lo=i / n_bins,
                hi=(i + 1) / n_bins,
                n=len(b),
                mean_predicted=sum(p for p, _ in b) / len(b),
                observed_rate=sum(y for _, y in b) / len(b),
            )
            for i, b in sorted(buckets.items())
        )
        return cls(
            n=n,
            log_loss=sum(nll(p, y) for p, y in pairs) / n,
            brier=sum((p - y) ** 2 for p, y in pairs) / n,
            ece=sum(b.n * abs(b.gap) for b in bins) / n,
            base_log_loss=sum(nll(rate, y) for _, y in pairs) / n,
            bins=bins,
        )


def calibration(
    log: Mapping[str, Iterable[Response]],
    *,
    items: Mapping[str, Item],
    estimator: Estimator,
    students: Iterable[str] | None = None,
    n_bins: int = DEFAULT_N_BINS,
) -> CalibrationReport:
    """Prequential calibration of ``estimator`` over the students in ``log``.

    Each student is replayed on their own — no student's responses inform another's
    predictions, exactly as in live use — and only then are the scored predictions
    pooled into one table. Skips are replayed (they move the state) but not scored:
    there is no right answer to compare them to.

    A response with an ordered score is scored here only when the estimator reads the
    right/wrong ``outcome`` alone (``reads_scores(estimator)`` is false), because then
    ``predict()`` forecasts that outcome. For an estimator that reads the score, the
    ``outcome`` is only the caller's own reading of the attempt (correct at full marks,
    say), not the event its ``predict()`` forecasts: those responses are replayed but
    scored by :func:`score_calibration` instead (#31).

    >>> from learny.tracing.estimators import RaschEstimator
    >>> items = {f'q{i}': Item(f'q{i}', labels=('x',), difficulty=0.5) for i in range(4)}
    >>> log = {'a': [Response('a', f'q{i}', 'correct') for i in range(4)]}
    >>> report = calibration(log, items=items, estimator=RaschEstimator())
    >>> report.n
    4
    >>> report.log_loss < math.log(2)   # beats a coin flip once it has learned
    True
    """
    by_score = reads_scores(estimator)
    pairs: list[tuple[float, float]] = []
    for name in _names(log, students):
        for response, p in prequential(log[name], items=items, estimator=estimator):
            if response.outcome.is_scored and not (by_score and response.score is not None):
                pairs.append((p, 1.0 if response.outcome is Outcome.CORRECT else 0.0))
    return CalibrationReport.from_pairs(pairs, n_bins=n_bins)


# -- calibration of ordered scores -------------------------------------------------


#: How far a forecast's probabilities may sum from 1 before it is refused.
_SUM_TOL = 1e-6


def _check_forecast(probs: Sequence[float], level: int) -> None:
    """Refuse a forecast that is not a distribution over two or more levels, or a level
    that is not one of them, rather than score it into a misleading number.

    >>> _check_forecast([0.5, 0.5], 1)
    >>> _check_forecast([5, 5, 5], 0)
    Traceback (most recent call last):
        ...
    ValueError: a forecast must be probabilities summing to 1, got [5, 5, 5]
    """
    if len(probs) < 2:
        raise ValueError(f"a score forecast needs at least two levels, got {list(probs)!r}")
    if not all(math.isfinite(p) and p >= 0.0 for p in probs) or abs(sum(probs) - 1.0) > _SUM_TOL:
        raise ValueError(f"a forecast must be probabilities summing to 1, got {list(probs)!r}")
    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level < len(probs):
        raise ValueError(f"level {level!r} is not one of the {len(probs)} levels forecast")


def _rps(probs: Sequence[float], level: int) -> float:
    """Ranked probability score of one forecast, scaled to ``[0, 1]``.

    The squared gap between forecast and observed cumulative distributions, summed over
    the ``m`` thresholds between the ``m + 1`` levels and divided by ``m``: a forecast one
    level off costs less than one three levels off, which log loss cannot see.

    >>> _rps([0.0, 1.0, 0.0], 1), _rps([1.0, 0.0, 0.0], 2)
    (0.0, 1.0)
    >>> _rps([0.0, 1.0, 0.0], 2)
    0.5
    """
    m = len(probs) - 1
    cum, total = 0.0, 0.0
    for j in range(m):
        cum += probs[j]
        total += (cum - (1.0 if level <= j else 0.0)) ** 2
    return total / m


@dataclass(frozen=True)
class ScoreCalibrationReport:
    """Prequential scores for forecasts of an ordered score.

    ``log_loss`` is minus the log probability given to the level observed; ``rps`` is the
    ranked probability score (:func:`_rps`), which also charges for *how far* off a
    forecast was. Both are proper (lower is better), and each has a ``base_`` twin: what
    forecasting the observed frequency of each level, per ``max_score``, would score, so
    beating it means the model knows more than the average. The reliability table bins
    the *expected* fraction of the maximum against the fraction observed, and ``ece`` is
    its count-weighted mean absolute gap. Responses with different ``max_score`` pool on
    that fraction scale.
    """

    n: int
    log_loss: float
    base_log_loss: float
    rps: float
    base_rps: float
    ece: float
    bins: tuple[CalibrationBin, ...]

    @classmethod
    def from_forecasts(
        cls,
        forecasts: Sequence[tuple[Sequence[float], int]],
        *,
        n_bins: int = DEFAULT_N_BINS,
    ) -> "ScoreCalibrationReport":
        """Build a report from ``(probabilities over 0..m, level observed)`` pairs.

        >>> sure = ScoreCalibrationReport.from_forecasts([([0.0, 0.0, 1.0], 2)] * 3)
        >>> sure.n, round(sure.log_loss, 6), sure.rps, sure.ece
        (3, 0.0, 0.0, 0.0)
        >>> mixed = [([0.25, 0.5, 0.25], k) for k in (0, 1, 1, 2)]
        >>> r = ScoreCalibrationReport.from_forecasts(mixed)
        >>> round(r.log_loss, 3) == round(r.base_log_loss, 3), r.ece
        (True, 0.0)
        """
        if n_bins < 1:
            raise ValueError(f"n_bins must be at least 1, got {n_bins}")
        n = len(forecasts)
        if n == 0:
            nan = math.nan
            return cls(n=0, log_loss=nan, base_log_loss=nan, rps=nan, base_rps=nan,
                       ece=nan, bins=())
        for probs, level in forecasts:
            _check_forecast(probs, level)

        def nll(probs: Sequence[float], level: int) -> float:
            return -math.log(min(max(probs[level], _EPS), 1.0))

        counts: dict[int, list[int]] = {}
        for probs, level in forecasts:
            counts.setdefault(len(probs), [0] * len(probs))[level] += 1
        base = {size: [c / sum(cs) for c in cs] for size, cs in counts.items()}

        buckets: dict[int, list[tuple[float, float]]] = {}
        for probs, level in forecasts:
            m = len(probs) - 1
            expected = sum(k * p for k, p in enumerate(probs)) / m
            buckets.setdefault(min(int(expected * n_bins), n_bins - 1), []).append(
                (expected, level / m)
            )
        bins = tuple(
            CalibrationBin(
                lo=i / n_bins,
                hi=(i + 1) / n_bins,
                n=len(b),
                mean_predicted=sum(e for e, _ in b) / len(b),
                observed_rate=sum(o for _, o in b) / len(b),
            )
            for i, b in sorted(buckets.items())
        )
        return cls(
            n=n,
            log_loss=sum(nll(p, k) for p, k in forecasts) / n,
            base_log_loss=sum(nll(base[len(p)], k) for p, k in forecasts) / n,
            rps=sum(_rps(p, k) for p, k in forecasts) / n,
            base_rps=sum(_rps(base[len(p)], k) for p, k in forecasts) / n,
            ece=sum(b.n * abs(b.gap) for b in bins) / n,
            bins=bins,
        )


def score_calibration(
    log: Mapping[str, Iterable[Response]],
    *,
    items: Mapping[str, Item],
    estimator: Estimator,
    students: Iterable[str] | None = None,
    n_bins: int = DEFAULT_N_BINS,
) -> ScoreCalibrationReport:
    """Prequential calibration of ``estimator``'s score forecasts over ``log``.

    The twin of :func:`calibration` for responses with an ordered ``score``: each is
    forecast by ``estimator.score_probabilities`` from the state before it, every
    response (scored, right/wrong or skipped) is replayed, and only the scored ones are
    scored. The estimator must read scores (:func:`reads_scores`), such as
    :class:`~learny.tracing.estimators.PartialCreditEstimator`.

    >>> from learny.tracing.estimators import PartialCreditEstimator
    >>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
    >>> log = {'a': [Response('a', 'q', 'correct', score=k, max_score=2)
    ...              for k in (2, 1, 2, 2, 1, 2)]}
    >>> r = score_calibration(log, items=items, estimator=PartialCreditEstimator())
    >>> r.n, 0.0 <= r.rps <= 1.0
    (6, True)
    """
    if not reads_scores(estimator):
        raise TypeError(
            f"{type(estimator).__name__} does not forecast scores (it has no "
            "score_probabilities); use calibration() for its right/wrong forecasts, or "
            "an estimator that reads scores, such as PartialCreditEstimator"
        )
    forecasts: list[tuple[list[float], int]] = []
    for name in _names(log, students):
        for response, item, state in _before_each(log[name], items=items, estimator=estimator):
            if response.score is not None:
                probs = estimator.score_probabilities(state, item, response.max_score)
                forecasts.append((list(probs), response.score))
    return ScoreCalibrationReport.from_forecasts(forecasts, n_bins=n_bins)


# -- choosing between estimators -------------------------------------------------


def _forecast_loss(
    estimator: Any, state: Mapping[str, Any], response: Response, item: Item
) -> float | None:
    """Log loss of what ``estimator`` forecasts for ``response``, or ``None`` if unscored.

    A score, for an estimator that reads scores, is scored on its level; anything else
    scored, as right/wrong against ``predict()`` (as :func:`calibration` does).
    """
    if not response.outcome.is_scored:
        return None
    if response.score is not None and reads_scores(estimator):
        probs = estimator.score_probabilities(state, item, response.max_score)
        return -math.log(min(max(probs[response.score], _EPS), 1.0))
    p = min(max(estimator.predict(state, item), _EPS), 1.0 - _EPS)
    return -math.log(p if response.outcome is Outcome.CORRECT else 1.0 - p)


@dataclass(frozen=True)
class Comparison:
    """Prequential log loss of several candidate estimators on the same log.

    ``losses`` is each candidate's mean log loss per scored response (lower is better)
    and ``best`` the lowest. ``se`` is each candidate's standard error of its loss *minus
    the best's*, paired response by response and clustered by student (one student's
    responses are not independent of each other). ``chosen`` is the first candidate, in
    the order given, whose loss is within ``tolerance_se`` of those standard errors of
    the best: the one-standard-error rule, which keeps the candidate listed first (the
    default, the simplest) unless the log says clearly otherwise. Short histories make
    prequential loss favour sharper forecasts than the truth (#32); this is the guard.
    """

    n: int
    n_students: int
    losses: Mapping[str, float]
    se: Mapping[str, float]
    best: str
    chosen: str


def compare_estimators(
    log: Mapping[str, Iterable[Response]],
    *,
    items: Mapping[str, Item],
    candidates: Mapping[str, Estimator],
    students: Iterable[str] | None = None,
    tolerance_se: float = 1.0,
) -> Comparison:
    """Replay ``log`` prequentially under each candidate and pick one; see :class:`Comparison`.

    ``candidates`` maps a name to an estimator, **most preferred first**. Every candidate
    is scored on the same responses, so the comparison is paired. ``tolerance_se`` is how
    many standard errors of slack the earlier candidates get: 1 is the usual rule, 0 is
    plain arg-min. This is the tool for refitting any estimator setting on a log
    (``prior_var``, ``forget_per_week``, a threshold spread), one candidate per value.

    >>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
    >>> log = {s: [Response(s, 'q', 'correct')] * 5 for s in 'abc'}
    >>> c = compare_estimators(log, items=items, candidates={
    ...     'default': RaschEstimator(), 'sure': RaschEstimator(prior_var=0.01)})
    >>> c.best, c.chosen
    ('default', 'default')
    """
    if not candidates:
        raise ValueError("compare_estimators needs at least one candidate")
    if len({reads_scores(est) for est in candidates.values()}) > 1:
        raise ValueError(
            "the candidates disagree on what they forecast (some read scores, some only "
            "right/wrong), so their log losses are on different events and not comparable; "
            "compare score-reading estimators with each other, outcome-reading with each other"
        )
    if not (isinstance(tolerance_se, (int, float)) and tolerance_se >= 0
            and math.isfinite(tolerance_se)):
        raise ValueError(f"tolerance_se must be a non-negative number, got {tolerance_se!r}")
    names = _names(log, students)
    records = {name: list(log[name]) for name in names}  # read once: every candidate replays it
    per: dict[str, list[list[float]]] = {}  # candidate -> per student -> losses
    for label, est in candidates.items():
        per[label] = [
            [
                loss
                for response, item, state in _before_each(records[name], items=items, estimator=est)
                if (loss := _forecast_loss(est, state, response, item)) is not None
            ]
            for name in names
        ]
    n = sum(len(ls) for ls in next(iter(per.values())))
    if n == 0:
        raise ValueError("the log has no scored responses to compare on")
    means = {label: sum(map(sum, ls)) / n for label, ls in per.items()}
    best = min(means, key=means.get)
    counted = [k for k, ls in enumerate(per[best]) if ls]

    def se_vs_best(label: str) -> float:
        if label == best:
            return 0.0
        diff = means[label] - means[best]
        if len(counted) > 1:  # clustered by student
            totals = [sum(a - b for a, b in zip(per[label][k], per[best][k])) for k in counted]
            sizes = [len(per[best][k]) for k in counted]
            s = len(counted)
            var = s / (s - 1) * sum((t - m * diff) ** 2 for t, m in zip(totals, sizes)) / n**2
        else:  # one student: per response
            d = [a - b for a, b in zip(per[label][counted[0]], per[best][counted[0]])]
            var = sum((x - diff) ** 2 for x in d) / max(len(d) - 1, 1) / len(d)
        return math.sqrt(var)

    se = {label: se_vs_best(label) for label in candidates}
    chosen = next(
        label for label in candidates if means[label] - means[best] <= tolerance_se * se[label]
    )
    return Comparison(n=n, n_students=len(counted), losses=means, se=se, best=best, chosen=chosen)


#: The spreads :func:`fit_threshold_spread` tries by default: the binomial default and
#: factors of 4/3, 2 and 3 either way of it, symmetric on a log scale.
DEFAULT_SPREADS = (1.0, 0.75, 4 / 3, 0.5, 2.0, 1 / 3, 3.0)


def fit_threshold_spread(
    log: Mapping[str, Iterable[Response]],
    *,
    items: Mapping[str, Item],
    spreads: Iterable[float] = DEFAULT_SPREADS,
    estimator: PartialCreditEstimator | None = None,
    students: Iterable[str] | None = None,
    tolerance_se: float = 1.0,
) -> tuple[float, Comparison]:
    """The threshold spread a log supports for :class:`PartialCreditEstimator`.

    Each spread is a candidate ``thresholds=spread_thresholds(spread)`` on ``estimator``
    (default: a plain ``PartialCreditEstimator``), compared by prequential score log loss
    with the one-standard-error rule (:func:`compare_estimators`), preferring spreads
    nearer the binomial default (1.0) on a log scale whatever order they are given in (a
    tie, such as 0.75 and 4/3, goes to the narrower). Returns the chosen spread and the
    comparison, whose candidates are named ``f"{spread:.4g}"``; use it as
    ``PartialCreditEstimator(thresholds=spread_thresholds(spread))``.

    With few students the rule keeps the default unless the log is clear: at a true
    spread of 2 it chose 2 in 11-15 of 30 fits with one to three students, against 17-20
    of 20 with twenty (decision 11). Prefer it to arg-min when a wrong spread costs more
    than a missed one.

    >>> items = {'q': Item('q', difficulty=0.5)}
    >>> log = {'a': [Response('a', 'q', 'correct', score=k, max_score=2) for k in (1, 2, 1, 0)]}
    >>> spread, comparison = fit_threshold_spread(log, items=items)
    >>> spread   # four scores cannot overturn the default
    1.0
    """
    base = estimator if estimator is not None else PartialCreditEstimator()
    grid = {spread_thresholds(c).spread for c in spreads}  # validates each spread
    ordered = sorted(grid, key=lambda c: (round(abs(math.log(c)), 12), c))
    by_name = {f"{c:.4g}": c for c in ordered}
    candidates = {
        name: replace(base, thresholds=spread_thresholds(c)) for name, c in by_name.items()
    }
    result = compare_estimators(
        log, items=items, candidates=candidates, students=students, tolerance_se=tolerance_se
    )
    return by_name[result.chosen], result
