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

**Are its probabilities honest?** [`calibration()`](#learny.tracing.diagnostics.calibration) (right/wrong) and
[`score_calibration()`](#learny.tracing.diagnostics.score_calibration) (ordered scores) replay the log *prequentially*:
each response is predicted from the state built from the responses before it, then
folded in. Nothing is scored on data it was fitted to, so the report measures prediction,
not fit. For a learner model calibration matters more than discrimination — a 70% that
comes true 40% of the time is worse than useless when it is shown to a child.

Both are pure functions of data the model already has; neither needs a new seam, and
neither looks at more than one student at a time unless asked to.

### Module Attributes

| [`DEFAULT_SEPARATION_THRESHOLD`](#learny.tracing.diagnostics.DEFAULT_SEPARATION_THRESHOLD)   | Separation at which an ordering of labels is worth believing.                                |
|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| [`DEFAULT_N_BINS`](#learny.tracing.diagnostics.DEFAULT_N_BINS)                 | Equal-width probability bins for the reliability table.                                      |
| [`DEFAULT_SPREADS`](#learny.tracing.diagnostics.DEFAULT_SPREADS)                | the binomial default and factors of 4/3, 2 and 3 either way of it, symmetric on a log scale. |

### Functions

| [`label_separation`](#learny.tracing.diagnostics.label_separation)(state, \*[, estimator, ...])   | Separation of one student's label deviations, from their estimator state.                                                      |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| [`prequential`](#learny.tracing.diagnostics.prequential)(responses, \*, items, estimator)    | Yield `(response, p)` where `p` was predicted *before* the response was seen.                                                  |
| [`calibration`](#learny.tracing.diagnostics.calibration)(log, \*, items, estimator[, ...])   | Prequential calibration of `estimator` over the students in `log`.                                                             |
| [`score_calibration`](#learny.tracing.diagnostics.score_calibration)(log, \*, items, estimator)    | Prequential calibration of `estimator`'s score forecasts over `log`.                                                           |
| [`reads_scores`](#learny.tracing.diagnostics.reads_scores)(estimator)                         | Whether `estimator` forecasts ordered scores: it has `score_probabilities`.                                                    |
| [`compare_estimators`](#learny.tracing.diagnostics.compare_estimators)(log, \*, items, candidates)  | Replay `log` prequentially under each candidate and pick one; see [`Comparison`](#learny.tracing.diagnostics.Comparison). |
| [`fit_threshold_spread`](#learny.tracing.diagnostics.fit_threshold_spread)(log, \*, items[, ...])     | The threshold spread a log supports for `PartialCreditEstimator`.                                                              |

### Classes

| [`LabelSeparation`](#learny.tracing.diagnostics.LabelSeparation)(n_labels, observed_sd, rmse)     | How distinguishable one student's labels are from each other.                |
|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`CalibrationBin`](#learny.tracing.diagnostics.CalibrationBin)(lo, hi, n, mean_predicted, ...)   | One row of a reliability table: predictions in `[lo, hi)` and what happened. |
| [`CalibrationReport`](#learny.tracing.diagnostics.CalibrationReport)(n, log_loss, brier, ece, ...)  | Prequential scores for a set of predictions.                                 |
| [`ScoreCalibrationReport`](#learny.tracing.diagnostics.ScoreCalibrationReport)(n, log_loss, ...)         | Prequential scores for forecasts of an ordered score.                        |
| [`Comparison`](#learny.tracing.diagnostics.Comparison)(n, n_students, losses, se, best, ...) | Prequential log loss of several candidate estimators on the same log.        |

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

```pycon
>>> r = CalibrationReport.from_pairs([(0.9, 1), (0.9, 1), (0.1, 0), (0.1, 1)])
>>> r.n, round(r.brier, 3), round(r.ece, 3)
(4, 0.21, 0.25)
>>> [(b.n, b.observed_rate) for b in r.bins]
[(2, 0.5), (2, 1.0)]
```

* **Return type:**
  [`CalibrationReport`](#learny.tracing.diagnostics.CalibrationReport)

### *class* learny.tracing.diagnostics.Comparison(n, n_students, losses, se, best, chosen)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Prequential log loss of several candidate estimators on the same log.

`losses` is each candidate’s mean log loss per scored response (lower is better)
and `best` the lowest. `se` is each candidate’s standard error of its loss \*minus
the best’s\*, paired response by response and clustered by student (one student’s
responses are not independent of each other). `chosen` is the first candidate, in
the order given, whose loss is within `tolerance_se` of those standard errors of
the best: the one-standard-error rule, which keeps the candidate listed first (the
default, the simplest) unless the log says clearly otherwise. Short histories make
prequential loss favour sharper forecasts than the truth (#32); this is the guard.

### learny.tracing.diagnostics.DEFAULT_N_BINS *= 10*

Equal-width probability bins for the reliability table.

### learny.tracing.diagnostics.DEFAULT_SEPARATION_THRESHOLD *= 2.0*

Separation at which an ordering of labels is worth believing. `G = 2` is reliability
0.8, about three distinguishable strata (Wright’s `(4G + 1) / 3`) — the usual Rasch
bar for a ranking one acts on. Below `G = 1` (reliability 0.5) the spread of the
estimates is mostly their own noise.

### learny.tracing.diagnostics.DEFAULT_SPREADS *= (1.0, 0.75, 1.3333333333333333, 0.5, 2.0, 0.3333333333333333, 3.0)*

the binomial default and
factors of 4/3, 2 and 3 either way of it, symmetric on a log scale.

* **Type:**
  The spreads [`fit_threshold_spread()`](#learny.tracing.diagnostics.fit_threshold_spread) tries by default

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

### *class* learny.tracing.diagnostics.ScoreCalibrationReport(n, log_loss, base_log_loss, rps, base_rps, ece, bins)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Prequential scores for forecasts of an ordered score.

`log_loss` is minus the log probability given to the level observed; `rps` is the
ranked probability score (`_rps()`), which also charges for *how far* off a
forecast was. Both are proper (lower is better), and each has a `base_` twin: what
forecasting the observed frequency of each level, per `max_score`, would score, so
beating it means the model knows more than the average. The reliability table bins
the *expected* fraction of the maximum against the fraction observed, and `ece` is
its count-weighted mean absolute gap. Responses with different `max_score` pool on
that fraction scale.

#### *classmethod* from_forecasts(forecasts, , n_bins=10)

Build a report from `(probabilities over 0..m, level observed)` pairs.

```pycon
>>> sure = ScoreCalibrationReport.from_forecasts([([0.0, 0.0, 1.0], 2)] * 3)
>>> sure.n, round(sure.log_loss, 6), sure.rps, sure.ece
(3, 0.0, 0.0, 0.0)
>>> mixed = [([0.25, 0.5, 0.25], k) for k in (0, 1, 1, 2)]
>>> r = ScoreCalibrationReport.from_forecasts(mixed)
>>> round(r.log_loss, 3) == round(r.base_log_loss, 3), r.ece
(True, 0.0)
```

* **Return type:**
  [`ScoreCalibrationReport`](#learny.tracing.diagnostics.ScoreCalibrationReport)

### learny.tracing.diagnostics.calibration(log, , items, estimator, students=None, n_bins=10)

Prequential calibration of `estimator` over the students in `log`.

Each student is replayed on their own — no student’s responses inform another’s
predictions, exactly as in live use — and only then are the scored predictions
pooled into one table. Skips are replayed (they move the state) but not scored:
there is no right answer to compare them to.

A response with an ordered score is scored here only when the estimator reads the
right/wrong `outcome` alone (`reads_scores(estimator)` is false), because then
`predict()` forecasts that outcome. For an estimator that reads the score, the
`outcome` is only the caller’s own reading of the attempt (correct at full marks,
say), not the event its `predict()` forecasts: those responses are replayed but
scored by [`score_calibration()`](#learny.tracing.diagnostics.score_calibration) instead (#31).

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

* **Return type:**
  [`CalibrationReport`](#learny.tracing.diagnostics.CalibrationReport)

### learny.tracing.diagnostics.compare_estimators(log, , items, candidates, students=None, tolerance_se=1.0)

Replay `log` prequentially under each candidate and pick one; see [`Comparison`](#learny.tracing.diagnostics.Comparison).

`candidates` maps a name to an estimator, **most preferred first**. Every candidate
is scored on the same responses, so the comparison is paired. `tolerance_se` is how
many standard errors of slack the earlier candidates get: 1 is the usual rule, 0 is
plain arg-min. This is the tool for refitting any estimator setting on a log
(`prior_var`, `forget_per_week`, a threshold spread), one candidate per value.

```pycon
>>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
>>> log = {s: [Response(s, 'q', 'correct')] * 5 for s in 'abc'}
>>> c = compare_estimators(log, items=items, candidates={
...     'default': RaschEstimator(), 'sure': RaschEstimator(prior_var=0.01)})
>>> c.best, c.chosen
('default', 'default')
```

* **Return type:**
  [`Comparison`](#learny.tracing.diagnostics.Comparison)

### learny.tracing.diagnostics.fit_threshold_spread(log, , items, spreads=(1.0, 0.75, 1.3333333333333333, 0.5, 2.0, 0.3333333333333333, 3.0), estimator=None, students=None, tolerance_se=1.0)

The threshold spread a log supports for `PartialCreditEstimator`.

Each spread is a candidate `thresholds=spread_thresholds(spread)` on `estimator`
(default: a plain `PartialCreditEstimator`), compared by prequential score log loss
with the one-standard-error rule ([`compare_estimators()`](#learny.tracing.diagnostics.compare_estimators)), preferring spreads
nearer the binomial default (1.0) on a log scale whatever order they are given in (a
tie, such as 0.75 and 4/3, goes to the narrower). Returns the chosen spread and the
comparison, whose candidates are named `f"{spread:.4g}"`; use it as
`PartialCreditEstimator(thresholds=spread_thresholds(spread))`.

With few students the rule keeps the default unless the log is clear: at a true
spread of 2 it chose 2 in 11-15 of 30 fits with one to three students, against 17-20
of 20 with twenty (decision 11). Prefer it to arg-min when a wrong spread costs more
than a missed one.

```pycon
>>> items = {'q': Item('q', difficulty=0.5)}
>>> log = {'a': [Response('a', 'q', 'correct', score=k, max_score=2) for k in (1, 2, 1, 0)]}
>>> spread, comparison = fit_threshold_spread(log, items=items)
>>> spread   # four scores cannot overturn the default
1.0
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`Comparison`](#learny.tracing.diagnostics.Comparison)]

### learny.tracing.diagnostics.label_separation(state, , estimator=None, min_n=1, threshold=2.0)

Separation of one student’s label deviations, from their estimator state.

The state is read through `estimator.mastery()` (default: a
[`RaschEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.RaschEstimator), which also reads a plain
`{label: {"mu", "var", "n"}}` layout), from each label’s
`deviation`. Only labels with at least
`min_n` observations are counted; a label nobody has evidence on is not a label
that can be told apart from anything.

Deviations, not mastery, are what is measured: the question is whether the labels
differ *from each other*, and every label shares the same global skill.

The state holds *posteriors* (means `mu` shrunk toward zero, variances `var`),
not the likelihood-only measures the classical Rasch formula assumes. So this is the
posterior (EAP) form of the index: the signal is the spread of the posterior means,
the noise their mean posterior variance, `G = sd(mu) / sqrt(mean(var))`, i.e.
reliability `var(mu) / (var(mu) + mean(var))`. In the normal-normal case with a
correctly specified prior it equals the likelihood-based `G` in expectation,
without having to know the prior. It also stays honest when the estimator has
re-opened a stale label’s variance without moving its mean (`forget_per_week`):
that only adds noise, so it can only lower `G` – whereas undoing a presumed
shrinkage there would attribute a whole history’s mean to the little evidence the
variance still shows, and call noise distinguishable.

`var` is each deviation’s variance *given the global skill* (`var -
loading**2`). What the deviations share through the global skill – how much of
the student’s level is “overall” rather than “this label”, which a record often
cannot tell – moves them all together, so it blurs no ordering among them.

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

* **Return type:**
  [`LabelSeparation`](#learny.tracing.diagnostics.LabelSeparation)

### learny.tracing.diagnostics.prequential(responses, , items, estimator)

Yield `(response, p)` where `p` was predicted *before* the response was seen.

Pass one student’s responses in log order. Each prediction uses only the responses
that came before it, so this is the honest out-of-sample stream that calibration,
and any later hyperparameter fit, should be scored on. Every response is yielded,
skips included; filter on `response.outcome.is_scored` to score.

```pycon
>>> from learny.tracing.estimators import RaschEstimator
>>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
>>> rs = [Response('a', 'q', 'correct'), Response('a', 'q', 'correct')]
>>> [round(p, 3) for _, p in prequential(rs, items=items, estimator=RaschEstimator())]
[0.5, 0.6]
```

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Response`](learny.tracing.records.html.md#learny.tracing.records.Response), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

### learny.tracing.diagnostics.reads_scores(estimator)

Whether `estimator` forecasts ordered scores: it has `score_probabilities`.

It decides which report a scored response belongs in: an estimator without it
forecasts the right/wrong `outcome`, so the response is scored by
[`calibration()`](#learny.tracing.diagnostics.calibration); one with it is taken to forecast (and learn from) the score, so
the response is scored by [`score_calibration()`](#learny.tracing.diagnostics.score_calibration) instead. It is a check of
capability, not of what `observe` reads: an estimator that forecasts scores while
learning only from outcomes should not define `score_probabilities`.

```pycon
>>> from learny.tracing.estimators import PartialCreditEstimator, RaschEstimator
>>> reads_scores(RaschEstimator()), reads_scores(PartialCreditEstimator())
(False, True)
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### learny.tracing.diagnostics.score_calibration(log, , items, estimator, students=None, n_bins=10)

Prequential calibration of `estimator`’s score forecasts over `log`.

The twin of [`calibration()`](#learny.tracing.diagnostics.calibration) for responses with an ordered `score`: each is
forecast by `estimator.score_probabilities` from the state before it, every
response (scored, right/wrong or skipped) is replayed, and only the scored ones are
scored. The estimator must read scores ([`reads_scores()`](#learny.tracing.diagnostics.reads_scores)), such as
[`PartialCreditEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.PartialCreditEstimator).

```pycon
>>> from learny.tracing.estimators import PartialCreditEstimator
>>> items = {'q': Item('q', labels=('x',), difficulty=0.5)}
>>> log = {'a': [Response('a', 'q', 'correct', score=k, max_score=2)
...              for k in (2, 1, 2, 2, 1, 2)]}
>>> r = score_calibration(log, items=items, estimator=PartialCreditEstimator())
>>> r.n, 0.0 <= r.rps <= 1.0
(6, True)
```

* **Return type:**
  [`ScoreCalibrationReport`](#learny.tracing.diagnostics.ScoreCalibrationReport)
