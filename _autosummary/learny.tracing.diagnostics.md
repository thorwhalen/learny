# learny.tracing.diagnostics

Diagnostics: when to believe the model, and how well it has predicted so far.

A learner model that cannot say when it is guessing will eventually be shown to a learner
while it is guessing. This module answers the two questions that decide whether an
estimate is fit to show:

**Can its labels be told apart?** [`label_separation()`](#learny.tracing.diagnostics.label_separation) computes the Rasch separation
index over one student’s label *deviations* — the spread of the deviations that is not
explained by their own uncertainty, in units of that uncertainty. When labels never vary
independently of each other (an item tagged with nine labels at once, say), every
deviation stays near zero, the separation is near zero, and any ranking of the labels is
noise. The report says so rather than leaving a caller to sort noise and call it a
diagnosis.

**Are its probabilities honest?** [`calibration()`](#learny.tracing.diagnostics.calibration) replays the log *prequentially*:
each response is predicted from the state built from the responses before it, then
folded in. Nothing is scored on data it was fitted to, so the report measures prediction,
not fit. For a learner model calibration matters more than discrimination — a 70% that
comes true 40% of the time is worse than useless when it is shown to a child.

Both are pure functions of data the model already has; neither needs a new seam, and
neither looks at more than one student at a time unless asked to.

### Module Attributes

| [`DEFAULT_SEPARATION_THRESHOLD`](#learny.tracing.diagnostics.DEFAULT_SEPARATION_THRESHOLD)   | Separation at which an ordering of labels is worth believing.   |
|---------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`DEFAULT_N_BINS`](#learny.tracing.diagnostics.DEFAULT_N_BINS)                 | Equal-width probability bins for the reliability table.         |

### Functions

| [`label_separation`](#learny.tracing.diagnostics.label_separation)(state, \*[, min_n, threshold])   | Separation of one student's label deviations, from their estimator state.     |
|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`prequential`](#learny.tracing.diagnostics.prequential)(responses, \*, items, estimator)      | Yield `(response, p)` where `p` was predicted *before* the response was seen. |
| [`calibration`](#learny.tracing.diagnostics.calibration)(log, \*, items, estimator[, ...])     | Prequential calibration of `estimator` over the students in `log`.            |

### Classes

| [`LabelSeparation`](#learny.tracing.diagnostics.LabelSeparation)(n_labels, observed_sd, rmse)    | How distinguishable one student's labels are from each other.                |
|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`CalibrationBin`](#learny.tracing.diagnostics.CalibrationBin)(lo, hi, n, mean_predicted, ...)  | One row of a reliability table: predictions in `[lo, hi)` and what happened. |
| [`CalibrationReport`](#learny.tracing.diagnostics.CalibrationReport)(n, log_loss, brier, ece, ...) | Prequential scores for a set of predictions.                                 |

### *class* learny.tracing.diagnostics.CalibrationBin(lo, hi, n, mean_predicted, observed_rate)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One row of a reliability table: predictions in `[lo, hi)` and what happened.

#### *property* gap *: [float](https://docs.python.org/3/builtins/functions.html#float)*

positive means the model was too pessimistic.

* **Type:**
  Observed minus predicted

### *class* learny.tracing.diagnostics.CalibrationReport(n, log_loss, brier, ece, base_log_loss, bins)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Prequential scores for a set of predictions.

`log_loss` and `brier` are proper scoring rules (lower is better). `ece` is the
expected calibration error: the count-weighted mean absolute gap across bins.
`base_log_loss` is what always predicting the observed success rate would score,
so `log_loss < base_log_loss` means the model beats knowing only the average.

#### *classmethod* from_pairs(pairs, , n_bins=10)

Build a report from `(predicted, observed)` pairs, observed in `{0, 1}`.

* **Return type:**
  [`CalibrationReport`](#learny.tracing.diagnostics.CalibrationReport)

```pycon
>>> r = CalibrationReport.from_pairs([(0.9, 1), (0.9, 1), (0.1, 0), (0.1, 1)])
>>> r.n, round(r.brier, 3), round(r.ece, 3)
(4, 0.21, 0.25)
>>> [(b.n, b.observed_rate) for b in r.bins]
[(2, 0.5), (2, 1.0)]
```

### learny.tracing.diagnostics.DEFAULT_N_BINS *= 10*

Equal-width probability bins for the reliability table.

### learny.tracing.diagnostics.DEFAULT_SEPARATION_THRESHOLD *= 2.0*

Separation at which an ordering of labels is worth believing. `G = 2` is reliability
0.8, about three distinguishable strata (Wright’s `(4G + 1) / 3`) — the usual Rasch
bar for a ranking one acts on. Below `G = 1` (reliability 0.5) the spread of the
estimates is mostly their own noise.

### *class* learny.tracing.diagnostics.LabelSeparation(n_labels, observed_sd, rmse, threshold=2.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How distinguishable one student’s labels are from each other.

`separation` is the Rasch separation index *G*: the “true” spread of the label
deviations (observed variance minus mean error variance) divided by their root-mean
error. `reliability` is `G² / (1 + G²)`, the share of observed spread that is
signal. `distinguishable` is the verdict a caller should act on.

```pycon
>>> s = LabelSeparation(n_labels=4, observed_sd=0.75, rmse=0.3)
>>> round(s.true_sd, 3), round(s.separation, 3), round(s.reliability, 3)
(0.687, 2.291, 0.84)
>>> round(s.strata, 2)
3.39
>>> s.distinguishable
True
>>> LabelSeparation(n_labels=4, observed_sd=0.1, rmse=0.3).distinguishable
False
```

#### *property* distinguishable *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether an ordering of these labels (`weakest()`, say) is worth believing.

#### *property* reliability *: [float](https://docs.python.org/3/builtins/functions.html#float)*

the share of the observed spread that is not noise.

* **Type:**
  `G² / (1 + G²)`

#### *property* separation *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Signal-to-noise of the label spread (Rasch *G*). 0 when it is all noise.

#### *property* strata *: [float](https://docs.python.org/3/builtins/functions.html#float)*

roughly how many levels the labels fall into.

* **Type:**
  Wright’s `(4G + 1) / 3`

#### *property* true_sd *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Spread of the deviations with their measurement error removed.

### learny.tracing.diagnostics.calibration(log, , items, estimator, students=None, n_bins=10)

Prequential calibration of `estimator` over the students in `log`.

Each student is replayed on their own — no student’s responses inform another’s
predictions, exactly as in live use — and only then are the scored predictions
pooled into one table. Skips are replayed (they move the state) but not scored:
there is no right answer to compare them to.

* **Return type:**
  [`CalibrationReport`](#learny.tracing.diagnostics.CalibrationReport)

```pycon
>>> from learny.tracing.estimators import RaschEstimator
>>> items = {f'q{i}': Item(f'q{i}', labels=('x',), difficulty=0.5) for i in range(4)}
>>> log = {'a': [Response('a', f'q{i}', 'correct') for i in range(4)]}
>>> report = calibration(log, items=items, estimator=RaschEstimator())
>>> report.n
4
>>> report.log_loss < math.log(2)   # beats a coin flip once it has learned
True
```

### learny.tracing.diagnostics.label_separation(state, , min_n=1, threshold=2.0)

Separation of one student’s label deviations, from their estimator state.

Works on any state that stores labels as `{label: {"mu", "var", "n"}}` — the
[`RaschEstimator`](learny.tracing.estimators.md#learny.tracing.estimators.RaschEstimator) layout. Only labels with at least
`min_n` observations are counted; a label nobody has evidence on is not a label
that can be told apart from anything.

Deviations, not mastery, are what is measured: the question is whether the labels
differ *from each other*, and every label shares the same global skill.

* **Return type:**
  [`LabelSeparation`](#learny.tracing.diagnostics.LabelSeparation)

```pycon
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
```

### learny.tracing.diagnostics.prequential(responses, , items, estimator)

Yield `(response, p)` where `p` was predicted *before* the response was seen.

Pass one student’s responses in log order. Each prediction uses only the responses
that came before it, so this is the honest out-of-sample stream that calibration,
and any later hyperparameter fit, should be scored on. Every response is yielded,
skips included; filter on `response.outcome.is_scored` to score.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Response`](learny.tracing.records.md#learny.tracing.records.Response), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

```pycon
>>> from learny.tracing.estimators import RaschEstimator
>>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
>>> rs = [Response('a', 'q', 'correct'), Response('a', 'q', 'correct')]
>>> [round(p, 3) for _, p in prequential(rs, items=items, estimator=RaschEstimator())]
[0.5, 0.607]
```
