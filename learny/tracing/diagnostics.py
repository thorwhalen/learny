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

**Are its probabilities honest?** :func:`calibration` replays the log *prequentially*:
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
from dataclasses import dataclass
from typing import Any

from learny.tracing.estimators import Estimator
from learny.tracing.records import Item, Outcome, Response

__all__ = [
    "LabelSeparation",
    "label_separation",
    "prequential",
    "CalibrationBin",
    "CalibrationReport",
    "calibration",
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
    min_n: int = 1,
    threshold: float = DEFAULT_SEPARATION_THRESHOLD,
) -> LabelSeparation:
    """Separation of one student's label deviations, from their estimator state.

    Works on any state that stores labels as ``{label: {"mu", "var", "n"}}`` — the
    :class:`~learny.tracing.estimators.RaschEstimator` layout. Only labels with at least
    ``min_n`` observations are counted; a label nobody has evidence on is not a label
    that can be told apart from anything.

    Deviations, not mastery, are what is measured: the question is whether the labels
    differ *from each other*, and every label shares the same global skill.

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
    entries = [
        e for e in state.get("labels", {}).values() if int(e.get("n", 0)) >= min_n
    ]
    k = len(entries)
    if k == 0:
        return LabelSeparation(
            n_labels=0, observed_sd=0.0, rmse=0.0, threshold=threshold
        )
    mus = [float(e["mu"]) for e in entries]
    mean = sum(mus) / k
    observed_var = sum((m - mean) ** 2 for m in mus) / (k - 1) if k > 1 else 0.0
    mse = sum(float(e["var"]) for e in entries) / k
    return LabelSeparation(
        n_labels=k,
        observed_sd=math.sqrt(observed_var),
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
    [0.5, 0.607]
    """
    state = estimator.init()
    for response in responses:
        item = items.get(response.item) or Item(response.item)
        yield response, estimator.predict(state, item)
        state = estimator.observe(state, response, item)


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

    >>> from learny.tracing.estimators import RaschEstimator
    >>> items = {f'q{i}': Item(f'q{i}', labels=('x',), difficulty=0.5) for i in range(4)}
    >>> log = {'a': [Response('a', f'q{i}', 'correct') for i in range(4)]}
    >>> report = calibration(log, items=items, estimator=RaschEstimator())
    >>> report.n
    4
    >>> report.log_loss < math.log(2)   # beats a coin flip once it has learned
    True
    """
    if students is not None:
        names = list(students)
    elif hasattr(log, "students"):  # a ResponseLog iterates responses, not students
        names = log.students()
    else:
        names = list(log)
    pairs: list[tuple[float, float]] = []
    for name in names:
        for response, p in prequential(log[name], items=items, estimator=estimator):
            if response.outcome.is_scored:
                pairs.append((p, 1.0 if response.outcome is Outcome.CORRECT else 0.0))
    return CalibrationReport.from_pairs(pairs, n_bins=n_bins)
