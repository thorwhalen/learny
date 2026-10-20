# learny.tracing

Learner modelling: what a student knows, estimated from what they have answered.

The shape of this subpackage in one paragraph: responses go into an **append-only log**
which is the single source of truth; everything else — per-student mastery estimates
included — is a cache that can be rebuilt by replaying that log. That constraint is what
lets the estimator be replaced later without a data migration, and it is why
[`replay()`](learny.tracing.model.html.md#learny.tracing.model.LearnerModel.replay) exists and is tested.

```pycon
>>> from learny.tracing import Item, LearnerModel
>>> items = {'q1': Item('q1', labels=('fractions',), difficulty=0.5)}
>>> model = LearnerModel(items=items, log={}, estimates={})   # in-memory, for the doctest
>>> model.record('ada', 'q1', 'correct')
>>> model.predict('ada', 'q1') > 0.5
True
```

### Functions

| [`estimate_store`](#learny.tracing.estimate_store)(\*[, rootdir])                  | Per-student mastery estimates, keyed by student.                                                                               |
|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| [`response_log`](#learny.tracing.response_log)(\*[, rootdir])                    | The default response log, under `~/.local/share/learny/responses/`.                                                            |
| [`data_dir`](#learny.tracing.data_dir)([kind, app_name])                     | The per-kind data directory, created on demand.                                                                                |
| [`label_separation`](#learny.tracing.label_separation)(state, \*[, estimator, ...])  | Separation of one student's label deviations, from their estimator state.                                                      |
| [`calibration`](#learny.tracing.calibration)(log, \*, items, estimator[, ...])  | Prequential calibration of `estimator` over the students in `log`.                                                             |
| [`score_calibration`](#learny.tracing.score_calibration)(log, \*, items, estimator)   | Prequential calibration of `estimator`'s score forecasts over `log`.                                                           |
| [`reads_scores`](#learny.tracing.reads_scores)(estimator)                        | Whether `estimator` forecasts ordered scores: it has `score_probabilities`.                                                    |
| [`compare_estimators`](#learny.tracing.compare_estimators)(log, \*, items, candidates) | Replay `log` prequentially under each candidate and pick one; see [`Comparison`](#learny.tracing.Comparison). |
| [`fit_threshold_spread`](#learny.tracing.fit_threshold_spread)(log, \*, items[, ...])    | The threshold spread a log supports for [`PartialCreditEstimator`](#learny.tracing.PartialCreditEstimator).               |
| [`prequential`](#learny.tracing.prequential)(responses, \*, items, estimator)   | Yield `(response, p)` where `p` was predicted *before* the response was seen.                                                  |
| [`fit_feature_difficulty`](#learny.tracing.fit_feature_difficulty)(log, \*, items[, ...])  | Fit which item features predict difficulty, from a log of play.                                                                |
| [`attempt_features`](#learny.tracing.attempt_features)(response)                     | The default per-attempt feature source: `response.meta['features']`, or `None`.                                                |
| [`item_features`](#learny.tracing.item_features)(item)                            | The default feature source: `item.meta['features']`, or `None`.                                                                |
| [`restrict_labels`](#learny.tracing.restrict_labels)(items, \*, keep[, ...])        | Project an item bank onto a subset of its labels — one facet, say.                                                             |
| [`difficulty_from_rank`](#learny.tracing.difficulty_from_rank)(rank, n_ranks)            | Map an ordinal difficulty band (1-based, 1 = easiest) to a proportion in (0, 1).                                               |
| [`binomial_thresholds`](#learny.tracing.binomial_thresholds)(item, max_score)           | Thresholds under which a score out of `m` is `m` steps taken at one rate.                                                      |
| [`spread_thresholds`](#learny.tracing.spread_thresholds)(spread)                      | Binomial thresholds stretched by `spread`: `tau_k = spread * log(k / (m - k + 1))`.                                            |
| [`mark_not_reached`](#learny.tracing.mark_not_reached)(responses)                    | Flag the trailing run of blanks in one sitting as *not reached*.                                                               |
| [`expit`](#learny.tracing.expit)(x)                                       | The logistic function, overflow-safe at the tails.                                                                             |
| [`logit`](#learny.tracing.logit)(p, \*[, eps])                            | Inverse of [`expit()`](#learny.tracing.expit), clamped away from 0 and 1 so it stays finite.             |

### Classes

| [`LearnerModel`](#learny.tracing.LearnerModel)(\*[, items, estimator, log, ...])    | What a student knows, estimated from what they have answered.                                                         |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| [`Weakest`](#learny.tracing.Weakest)([masteries, reason])                      | What [`LearnerModel.weakest()`](#learny.tracing.LearnerModel.weakest) returns: a list of `Mastery`, plus why.  |
| [`Item`](#learny.tracing.Item)(id[, labels, difficulty, meta])              | A question, with the skill labels it exercises and its observed difficulty.                                           |
| [`Outcome`](#learny.tracing.Outcome)(\*values)                                 | What happened when a student met an item.                                                                             |
| [`Response`](#learny.tracing.Response)(student, item, outcome[, at, meta, ...]) | One student meeting one item, once.                                                                                   |
| [`Mastery`](#learny.tracing.Mastery)(label, skill[, prior_var, ...])           | What the model believes about one student and one label.                                                              |
| [`Skill`](#learny.tracing.Skill)(mu, var[, n, t])                            | A Gaussian belief about one skill, on the logit scale.                                                                |
| [`Estimator`](#learny.tracing.Estimator)(\*args, \*\*kwargs)                     | The seam.                                                                                                             |
| [`RaschEstimator`](#learny.tracing.RaschEstimator)([prior_var, label_prior_var, ...]) | Online Rasch with a Gaussian posterior.                                                                               |
| [`PartialCreditEstimator`](#learny.tracing.PartialCreditEstimator)([prior_var, ...])          | Masters' Partial Credit Model on the Rasch predictor: reads an ordered score.                                         |
| [`ResponseLog`](#learny.tracing.ResponseLog)(\*[, rootdir])                        | The append-only record of every response.                                                                             |
| [`LabelSeparation`](#learny.tracing.LabelSeparation)(n_labels, observed_sd, rmse)      | How distinguishable one student's labels are from each other.                                                         |
| [`CalibrationReport`](#learny.tracing.CalibrationReport)(n, log_loss, brier, ece, ...)   | Prequential scores for a set of predictions.                                                                          |
| [`CalibrationBin`](#learny.tracing.CalibrationBin)(lo, hi, n, mean_predicted, ...)    | One row of a reliability table: predictions in `[lo, hi)` and what happened.                                          |
| [`ScoreCalibrationReport`](#learny.tracing.ScoreCalibrationReport)(n, log_loss, ...)          | Prequential scores for forecasts of an ordered score.                                                                 |
| [`Comparison`](#learny.tracing.Comparison)(n, n_students, losses, se, best, ...)  | Prequential log loss of several candidate estimators on the same log.                                                 |
| [`FeatureDifficulty`](#learny.tracing.FeatureDifficulty)(names, center, scale, ...)      | A fitted explanatory difficulty model; see [`fit_feature_difficulty()`](#learny.tracing.fit_feature_difficulty). |
| [`Estimate`](#learny.tracing.Estimate)(mean, sd)                                | A posterior mean and standard deviation, on the logit scale.                                                          |

### *class* learny.tracing.CalibrationBin(lo, hi, n, mean_predicted, observed_rate)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One row of a reliability table: predictions in `[lo, hi)` and what happened.

#### *property* gap *: [float](https://docs.python.org/3/builtins/functions.html#float)*

positive means the model was too pessimistic.

* **Type:**
  Observed minus predicted

### *class* learny.tracing.CalibrationReport(n, log_loss, brier, ece, base_log_loss, bins)

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
  [`CalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.CalibrationReport)

### *class* learny.tracing.Comparison(n, n_students, losses, se, best, chosen)

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

### *class* learny.tracing.Estimate(mean, sd)

Bases: [`NamedTuple`](https://docs.python.org/3/library/typing.html#typing.NamedTuple)

A posterior mean and standard deviation, on the logit scale.

#### mean *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Alias for field number 0

#### sd *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Alias for field number 1

### *class* learny.tracing.Estimator(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

The seam. Anything with these four methods can replace the default.

`observe` must be a pure function of `(state, response, item)`, so that folding it
over a response log reproduces live state exactly. That is the contract which lets the
estimator be swapped without migrating any data.

#### init()

A fresh state for a student who has answered nothing.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### mastery(state)

Per-label mastery, for showing the model to the learner.

Fill each `Mastery.deviation` (the label relative to the student’s global
skill) if you can: [`LearnerModel.weakest`](learny.tracing.model.html.md#learny.tracing.model.LearnerModel.weakest) gates on it by default and raises
`TypeError` for an estimator that leaves it `None` (callers can still pass
`credible_below=None`). [`Mastery.null_var`](#learny.tracing.Mastery.null_var) calibrates that gate; left
`None`, the gate falls back to the more cautious posterior bound.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery)]

#### observe(state, response, item)

Return the new state after one response. Must not mutate `state`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### predict(state, item)

Probability this student answers this item correctly.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### *class* learny.tracing.FeatureDifficulty(names, center, scale, coef, covariance, residual_var, ability_mean=0.0, ability_var=1.0, residuals=dict(), anchors=0, n_students=0, n_responses=0, converged=True, attempt_names=(), attempt_center=(), attempt_scale=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A fitted explanatory difficulty model; see [`fit_feature_difficulty()`](#learny.tracing.fit_feature_difficulty).

Features are stored standardised (`(x - center) / scale` over the fitted items),
which is what the priors and the covariance refer to; [`weights()`](#learny.tracing.FeatureDifficulty.weights) reports them
in each feature’s own units. `covariance` is over `(intercept, *weights)` in the
standardised form. `residual_var` is the prior variance of a new item’s departure
from what its features predict, `ability_mean` and `ability_var` the fitted
students’ ability distribution, on the scale of the bank’s given difficulties when
the fit was anchored on them. `residuals` holds each fitted item’s own departure,
as `(mean, variance, *covariance with the coefficients)`; it carries the fitted
students’ data, so [`apply()`](#learny.tracing.FeatureDifficulty.apply) leaves it out unless asked. `converged` is false
when an iteration cap was hit (a `RuntimeWarning` said so at fit time).

Per-attempt features (`attempt_names`, standardised over the fitted attempts by
`attempt_center` and `attempt_scale`) add their weights after the item weights,
so `coef` and `covariance` are over `(intercept, *weights, *attempt weights)`;
[`attempt_weights()`](#learny.tracing.FeatureDifficulty.attempt_weights) reports them. They have no residual: an attempt’s setup
moves the difficulty of whatever item it is played with by its weights alone.

#### apply(items, , features=None, overwrite=False, use_residuals=False)

A copy of `items` with each item’s `difficulty` predicted from features.

Only items without a difficulty are filled unless `overwrite=True`; an item
with no features is left as it is, and per-attempt features are taken at the
fitted attempts’ average. The difficulty comes from the features alone
unless `use_residuals=True` adds each fitted item’s own residual. That residual
is learned from the fitted students’ answers, so feeding it back to estimate
those same students counts their answers twice; with one or two learners it is
mostly their own results (#18 review). The result is an item bank for the
`items=` seam of [`LearnerModel`](learny.tracing.model.html.md#learny.tracing.model.LearnerModel).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Item`](learny.tracing.records.html.md#learny.tracing.records.Item)]

#### attempt_weights()

Each per-attempt feature’s weight, as [`weights()`](#learny.tracing.FeatureDifficulty.weights) reports the item ones.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Estimate`](learny.tracing.difficulty.html.md#learny.tracing.difficulty.Estimate)]

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#learny.tracing.FeatureDifficulty.to_dict); refuses an artifact of another schema.

* **Return type:**
  [`FeatureDifficulty`](learny.tracing.difficulty.html.md#learny.tracing.difficulty.FeatureDifficulty)

#### predict(features, , attempt=None, item_id=None)

The difficulty, in logits, of an item with these features.

For any item the residual is unknown, so its prior variance `residual_var` is
added to the features’ part. Pass `item_id` of an item the model was fitted on
to use that item’s own fitted residual instead, with its posterior variance and
its covariance with the coefficients. Features far outside the fitted range are
extrapolated linearly, without warning.

`attempt` gives the per-attempt features of one way of playing the item (a new
song with 3 decoys); left `None`, the attempt is the fitted attempts’ average.

* **Return type:**
  [`Estimate`](learny.tracing.difficulty.html.md#learny.tracing.difficulty.Estimate)

#### to_dict()

A JSON-ready dict: the artifact to store, version and review.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### weights()

Each feature’s weight in logits of difficulty per unit of the feature.

Positive: more of the feature makes an item harder. The sd is the weight’s
posterior sd; a weight within about two of zero is not distinguishable from
“this feature does not matter”. Two features that move together split their
weight between them, each with a wide sd.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Estimate`](learny.tracing.difficulty.html.md#learny.tracing.difficulty.Estimate)]

### *class* learny.tracing.Item(id, labels=(), difficulty=None, meta=dict())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A question, with the skill labels it exercises and its observed difficulty.

`labels` is this item’s row of the Q-matrix: which knowledge components the item
draws on. `difficulty` is an *externally observed* difficulty on the unit
interval — the proportion of a reference population expected to get it wrong — and
is the strongest prior available before a given student has answered anything.
Leave it `None` when nothing observed is available.

```pycon
>>> item = Item("2004-q7", labels=("fractions", "area"), difficulty=0.4)
>>> item.weights
{'fractions': 1.0, 'area': 1.0}
>>> Item("q1", labels={"fractions": 0.85, "traps": 0.57}).weights["traps"]
0.57
```

#### *property* weights *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [float](https://docs.python.org/3/builtins/functions.html#float)]*

Labels as a `{label: weight}` mapping, whichever form they were given in.

### *class* learny.tracing.LabelSeparation(n_labels, observed_sd, rmse, threshold=2.0)

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

### *class* learny.tracing.LearnerModel(, items=None, estimator=None, log=None, estimates=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What a student knows, estimated from what they have answered.

```pycon
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
```

Getting a hard item wrong should leave the student looking weaker on the labels it
exercises than a student who has answered nothing:

```pycon
>>> model.mastery('ada')['area'].mu < model.mastery('ada')['fractions'].mu
True
```

#### calibration(students=None, , n_bins=10)

Prequential calibration over the log; see [`calibration()`](#learny.tracing.calibration).

Reads the log only; the estimate cache is neither used nor changed. With an
estimator that reads scores, scored responses are left to
[`score_calibration()`](#learny.tracing.score_calibration), so a log of scores alone gives an empty report here.

* **Return type:**
  [`CalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.CalibrationReport)

#### mastery(student)

Per-label mastery for one student, weakest first when sorted by skill.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery)]

#### predict(student, item)

Probability that `student` answers `item` correctly.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### record(student, item, outcome, , at=None, score=None, max_score=None, \*\*meta)

Log one response and fold it into the student’s estimate.

The log is written first: if updating the cache fails, the evidence survives and
[`replay()`](#learny.tracing.LearnerModel.replay) can rebuild from it. `score` out of `max_score` records an
ordered score alongside the right/wrong `outcome` (see
[`Response`](learny.tracing.records.html.md#learny.tracing.records.Response)); the default estimator reads only the
outcome, [`PartialCreditEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.PartialCreditEstimator) the score.

```pycon
>>> from learny.tracing.estimators import PartialCreditEstimator
>>> items = {'song-7/tempo': Item('song-7/tempo', labels=('tempo',))}
>>> model = LearnerModel(
...     items=items, estimator=PartialCreditEstimator(), log={}, estimates={}
... )
>>> model.record('ada', 'song-7/tempo', 'correct', score=4, max_score=4)
>>> model.mastery('ada')['tempo'].mu > 0
True
```

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### record_many(responses)

Record a batch — a whole paper, say — in the order given.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### replay(student=None)

Rebuild estimates from the log, discarding the cache.

This is what makes changing the estimator a re-run rather than a migration, and
it is asserted by the tests: folding `observe` over the log must reproduce the
state that live recording produced.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### score_calibration(students=None, , n_bins=10)

Prequential calibration of the score forecasts; see [`score_calibration()`](#learny.tracing.score_calibration).

Reads the log only. Needs an estimator that reads scores, such as
[`PartialCreditEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.PartialCreditEstimator).

* **Return type:**
  [`ScoreCalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.ScoreCalibrationReport)

#### separation(student, , threshold=2.0)

How distinguishable this student’s labels are; see [`label_separation()`](#learny.tracing.label_separation).

Check `.distinguishable` before acting on an ordering from [`weakest()`](#learny.tracing.LearnerModel.weakest).

* **Return type:**
  [`LabelSeparation`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.LabelSeparation)

#### weakest(student, n=5, , credible_below=1.0, relative_to='labels', multiplicity='calibrated')

The labels this student is credibly weakest on — what to practise next.

By default a label is returned only when it is credibly below the student’s
*other* labels: the upper bound `c + z * sd` of its contrast `c` — its
`Mastery.deviation` minus the
precision-weighted mean deviation of every other label with evidence — is below
zero. The survivors are ranked by posterior mean mastery, worst first, and the
first `n` returned.

Three keywords set the gate:

* `credible_below` — the z of the bound (default `DEFAULT_CREDIBLE_BELOW`,
  ~84% one-sided); larger `z` demands more certainty. With
  `multiplicity="none"`, `z = 0` keeps every label merely below its
  comparator on average. `None` switches the gate off and ranks every
  label with evidence by posterior mean — check [`separation()`](#learny.tracing.LearnerModel.separation) before
  believing that ranking.
* `multiplicity` — `"calibrated"` (default) corrects for testing every label
  with evidence at once, so `z` sets the chance of *any* false flag (about
  one student in six with no real weakness, at `z = 1`), and measures each
  contrast against its sampling spread under no real weakness
  ([`Mastery.null_var`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery.null_var)) and
  skew (a rare wrong answer from a student who is usually right is a large
  drop), so the correction costs little power at cold start (#22). An estimator that does
  not fill `null_var` gets `"bonferroni"` (a label it leaves unfilled is
  measured by its posterior spread): the same correction on the posterior sd, which shrinkage already makes cautious when evidence is thin, so
  with a few responses per label even a large real weakness is rarely returned.
  `"none"` applies `z` to each label separately, which with six labels, a few
  hundred responses and no real weakness flags something more often than not.
  Under `relative_to="global"` the calibrated spread is more cautious (the
  part of a label’s spread it shares with the others is counted, not removed).
  A label stored before null spreads were tracked is measured by its posterior
  spread until it is answered again.
* `relative_to` — `"labels"` (default) as above; `"global"` measures each
  label’s deviation against zero, the student’s global skill. The default
  estimator carries the global/label covariance, so a shortfall every item
  shares goes to the global skill, and where the record cannot tell “weak
  overall” from “weak on this label” the label’s deviation stays wide rather
  than taking the blame (#23); the contrast with the other labels counts the
  covariance they share through it ([`Mastery.loading`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery.loading)). Evidence on a single label is
  never a credible weakness under `"labels"` — there is nothing to compare it
  with. When unlabelled items carry the comparison (a label against the rest of
  the paper), use `"global"`.

`multiplicity="none", relative_to="global"` restores the original per-label gate.

Labels with no evidence are never included: the model has nothing to say about
them, and saying it anyway is how a learner model loses trust.

**An empty answer is common and says why.** The result is a list (a
[`Weakest`](#learny.tracing.Weakest)) whose `reason` is `None` when it holds labels, and
otherwise one of:

* `"no_evidence"` — the student has answered nothing that carries a label;
* `"no_credible_weakness"` — there is evidence, but no label is credibly
  below the rest of the student’s record. That is a statement about *relative*
  weakness, not “nothing to practise”: practise at the student’s overall level
  (`model.estimator.skill(state)` for the default estimator).

Raises `ValueError` for a negative `credible_below` (which would admit labels
credibly *above* their comparator) or an unknown `relative_to` /
`multiplicity`, and `TypeError` when the gate is on but
the estimator’s [`Mastery`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery) values carry no
`deviation` — rather than silently returning nothing.

```pycon
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
```

* **Return type:**
  [`Weakest`](learny.tracing.model.html.md#learny.tracing.model.Weakest)

### *class* learny.tracing.Mastery(label, skill, prior_var=1.0, , deviation=None, loading=0.0, null_var=None, null_k3=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What the model believes about one student and one label.

`probability` is the chance of success on an item of *average* difficulty, which is
what makes two labels comparable. `confidence` is a genuine posterior quantity, not
a heuristic: it falls out of the variance.

`deviation` is the label’s posterior *relative to the student’s own global skill*,
when the estimator has one (`None` otherwise). It is what “credibly weaker than
their own level” is judged on ([`LearnerModel.weakest`](learny.tracing.model.html.md#learny.tracing.model.LearnerModel.weakest)), so an estimator provides it through
this field rather than a caller reading the estimator’s private state.

```pycon
>>> m = Mastery('fractions', Skill(mu=0.5, var=0.25, n=4), prior_var=1.0)
>>> round(m.probability, 3)
0.622
>>> round(m.confidence, 3)
0.75
```

#### *property* confidence *: [float](https://docs.python.org/3/builtins/functions.html#float)*

How much of the prior uncertainty has been resolved, in `[0, 1)`.

#### interval(z=1.96)

A credible interval for [`probability`](#learny.tracing.Mastery.probability).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### loading *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.0*

The deviation’s loading on what every label of this student shares — for the
default estimator, its covariance with the global skill over the global skill’s
sd — so that two labels’ deviations covary by `loading_a * loading_b`. 0 (the
default) treats the deviations as independent.

#### null_k3 *: [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

The third cumulant of the same sampling distribution. A student who mostly gets a
label right makes a rare wrong answer a large one-sided jump, so the null is
skewed and its lower tail is heavier than a normal one with `null_var`; a test
of many labels at once lives in that tail. `None`: not tracked (no correction).

#### null_var *: [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

How far this label’s own evidence moves `deviation.mu` by chance, as a sampling
variance, had the student no real deviation on it: the spread a test of “is this
label really weaker than the others?” is calibrated to. Smaller than
`deviation.var` because a posterior mean is shrunk, and tracked rather than
derived from it because forgetting re-opens the posterior variance without moving
the mean (the identity `v - v**2 / tau**2` breaks; #11). The part of the label’s
movement that rides on the global skill is common to every label and is left out,
so that a leave-one-out contrast’s spread is the sum of its labels’ `null_var`.
`None`: not tracked (the posterior variance is the conservative stand-in); the
default estimator tracks it under `gain='bayes'`.

#### *property* probability *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Probability of success on an item of average difficulty for this label.

### *class* learny.tracing.Outcome(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What happened when a student met an item.

`str`-valued so it serialises to JSON as itself, with no encoder needed:

```pycon
>>> import json
>>> json.dumps({"status": Outcome.CORRECT})
'{"status": "correct"}'
>>> Outcome("wrong") is Outcome.WRONG
True
```

#### *property* is_scored *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether this outcome carries evidence about ability.

A skip is evidence about *confidence or time*, not about whether the student
could have answered, so estimators are entitled to ignore it.

```pycon
>>> [o.is_scored for o in Outcome]
[True, True, False]
```

### *class* learny.tracing.PartialCreditEstimator(prior_var=1.0, label_prior_var=0.25, guess=0.0, forget_per_week=0.02, abstain_weight=0.5, conjunctivity=0.0, gain='bayes', elo_rate=0.6, update_difficulty=False, thresholds=<function binomial_thresholds>, mode_steps=50)

Bases: [`RaschEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.RaschEstimator)

Masters’ Partial Credit Model on the Rasch predictor: reads an ordered score.

A response with a `score` out of `max_score` is scored on its levels
`0..max_score`, with `s` the same predictor as [`RaschEstimator`](#learny.tracing.RaschEstimator)’s (global
skill plus label deviations minus item difficulty):

```default
P(X = k)  proportional to  exp(sum over j <= k of (s - tau_j))
```

The thresholds `tau_j` come from the `thresholds` seam, by default
[`binomial_thresholds()`](#learny.tracing.binomial_thresholds). The log-likelihood’s gradient in `s` is
`k - E[X]` and its Fisher information `Var[X]`, which is all the joint update
needs, so the hierarchy, forgetting, the global/label covariance and replay are the
default estimator’s, unchanged. For a score the update iterates to the posterior mode
along the predictor (`mode_steps`), since one Newton step overshoots on a surprising
score out of many levels. A response *without* a score is a right/wrong answer and is
scored exactly as [`RaschEstimator`](#learny.tracing.RaschEstimator) scores it — guessing, skips and all.

**\`\`guess\`\` applies only to responses without a score**: a score is never modelled as
a guess, so on a multiple-choice item that is also scored, `expected_score` is not
`max_score * predict()` unless `guess=0`. For a score, `outcome` is not read,
and a score that contradicts it is not an error: the outcome is the caller’s own
right/wrong reading of the attempt.

```pycon
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
```

`predict` keeps the [`Estimator`](#learny.tracing.Estimator) meaning, the probability of a correct
answer on a right/wrong reading of the item; [`expected_score()`](#learny.tracing.PartialCreditEstimator.expected_score) and
[`score_probabilities()`](#learny.tracing.PartialCreditEstimator.score_probabilities) answer for a score.

#### expected_score(state, item, max_score, , at=None)

The expected score out of `max_score`; see [`score_probabilities()`](#learny.tracing.PartialCreditEstimator.score_probabilities).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### mode_steps *: [int](https://docs.python.org/3/builtins/functions.html#int)* *= 50*

Newton iterations allowed to find the posterior mode along the predictor for a
score. One step (the right/wrong update’s plug-in) is fine for a few stars but
overshoots on a surprising score out of many levels, whose gradient is bounded by
`max_score` rather than by 1; iterating to the mode (a Laplace step) does not.
`1` restores the plain one-step update.

#### score_probabilities(state, item, max_score, , at=None)

`P(score = k)` for `k = 0..max_score`, over the posterior.

The posterior is integrated with the same probit approximation as
[`predict()`](#learny.tracing.RaschEstimator.predict), so with the default thresholds and `guess=0`
the expected score is exactly `max_score * predict()`; both are approximations
to the posterior integral. Guessing is not modelled for a score (see the class).

```pycon
>>> est = PartialCreditEstimator()
>>> [round(p, 3) for p in est.score_probabilities(est.init(), Item('q'), 2)]
[0.25, 0.5, 0.25]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### thresholds(max_score)

How an item scored `0..max_score` places its steps; see `Thresholds`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

### *class* learny.tracing.RaschEstimator(prior_var=1.0, label_prior_var=0.25, guess=0.0, forget_per_week=0.02, abstain_weight=0.5, conjunctivity=0.0, gain='bayes', elo_rate=0.6, update_difficulty=False)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Online Rasch with a Gaussian posterior. The default estimator.

```pycon
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
```

Getting a *hard* item right is stronger evidence than getting an easy one right —
which is the property a plain success/failure count cannot have:

```pycon
>>> easy, hard = Item('e', difficulty=0.1), Item('h', difficulty=0.9)
>>> got_hard = est.observe(est.init(), Response('a', 'h', Outcome.CORRECT), hard)
>>> got_easy = est.observe(est.init(), Response('a', 'e', Outcome.CORRECT), easy)
>>> got_hard['global']['mu'] > got_easy['global']['mu']
True
```

A blank that the student never reached is not evidence, and changes nothing:

```pycon
>>> blank = Response('a', 'q1', Outcome.SKIPPED, meta={'not_reached': True})
>>> est.observe(est.init(), blank, item) == est.init()
True
```

#### abstain_weight *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.5*

Weight given to an interior blank, treated as a soft observation at the guessing
rate. Scoring an abstention as wrong is more biased than ignoring it; both are worse
than a half-weight soft observation.

#### conjunctivity *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.0*

0 = compensatory (labels trade off, a weighted mean). Larger values approach
weakest-link/conjunctive: the hardest label for this student dominates.

#### forget_per_week *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.02*

Variance added per week since a skill was last seen, so a stale belief re-opens to
new evidence. Inflating variance says “we know less now”, which is true; decaying
the mean would say “the skill got worse”, which is a guess.

#### gain *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)* *= 'bayes'*

`'bayes'` uses the posterior precision as the step size. `'elo'` freezes it at
`elo_rate`, which is classical Elo.

#### guess *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.0*

Probability of getting an item right by guessing. For 5-option multiple choice,
0.2. Left at 0 by default because it is a property of the assessment, not of the
model, and a wrong value here quietly biases everything.

#### init()

A fresh state: average skill at full prior uncertainty, no label evidence.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### label_prior_var *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.25*

Prior variance on each label’s *deviation* from the global skill. Smaller than
`prior_var` on purpose — this is the shrinkage that keeps a label with three
observations from drifting away from what the student’s whole record says.

#### mastery(state)

Per-label mastery: the student’s global skill adjusted by each label.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery)]

#### observe(state, response, item)

The new state after one response. Pure: `state` is not mutated.

One Newton (Laplace) step on the *joint* log-posterior over the global skill and
every label: a rank-1 update of the covariance along `Cov(skill, s)`. Because
the global/label covariance is carried, a shortfall that every item shares is
attributed to the global skill rather than to whichever label has the largest
share of each item (#23). The result is projected back onto the stored star
structure, which keeps every `(global, label)` pair exactly and drops only the
residual label-label correlation given the global skill.

Only the global skill and the item’s labels are written: every other label is
stored as its regression on the global skill, which this update leaves exactly
as it was (see `_Frame`).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### predict(state, item, , at=None)

Probability of a correct answer, integrating over the posterior.

With no evidence the prediction sits near the item’s own base rate, but pulled
toward a coin flip — because the model is being honest that it knows nothing about
*this* student, not just repeating what it knows about the item:

```pycon
>>> est = RaschEstimator()
>>> base_rate = 1 - 0.75
>>> cold = est.predict(est.init(), Item('q', difficulty=0.75))
>>> base_rate < cold < 0.5
True
>>> round(cold, 3)
0.283
```

Shrink the prior and it converges on the base rate, as it should:

```pycon
>>> sure = RaschEstimator(prior_var=1e-6)
>>> round(sure.predict(sure.init(), Item('q', difficulty=0.75)), 3)
0.25
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### prior_var *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 1.0*

Prior variance on the student’s global skill, in logits². 1.0 is a weak prior:
roughly, “this student is within ±2 logits of the reference population”.

#### skill(state)

The student’s global skill, independent of any label.

* **Return type:**
  [`Skill`](learny.tracing.estimators.html.md#learny.tracing.estimators.Skill)

#### update_difficulty *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= False*

Co-estimate item difficulty. Only sound with many learners per item; see the class
docstring for why that is off by default.

### *class* learny.tracing.Response(student, item, outcome, at=None, meta=dict(), , score=None, max_score=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One student meeting one item, once. The unit of the append-only log.

`at` is a POSIX timestamp. It is kept because order and elapsed time are what any
later model of forgetting will need, and a log that did not record it cannot be
replayed into one.

```pycon
>>> r = Response("cora", "2004-q7", Outcome.CORRECT, at=1_700_000_000.0)
>>> r.correct
True
>>> Response.from_dict(r.to_dict()) == r
True
```

**An ordered score** — 1 to 5 stars, partial credit — goes in `score` out of
`max_score`, on the consecutive levels `0..max_score`: map 1–5 stars to
`score=stars - 1, max_score=4`, and three ordered levels such as 1/3/5 stars to
`0, 1, 2` of `2` (a level that can never occur is not a level). `outcome` stays
the dichotomous view of the same attempt, so an estimator that only reads outcomes
(the default) is unaffected, and one that reads scores
([`PartialCreditEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.PartialCreditEstimator)) can replay the same log.
One response carries one score: an attempt scored on several sub-scales is several
responses, one per sub-scale.

```pycon
>>> r = Response("cora", "song-7/tempo", "correct", score=3, max_score=4)
>>> r.to_dict()['score'], Response.from_dict(r.to_dict()) == r
(3, True)
>>> 'score' in Response("cora", "2004-q7", "correct").to_dict()  # unscored: as before
False
>>> Response("cora", "q", "skipped", score=0, max_score=4)
Traceback (most recent call last):
    ...
ValueError: Response 'q': a skipped response has no score (got score=0)
```

#### *property* correct *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

True only for an outright correct answer; a skip is not a correct answer.

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#learny.tracing.Response.to_dict), tolerant of unknown keys from a future version.

* **Return type:**
  [`Response`](learny.tracing.records.html.md#learny.tracing.records.Response)

#### max_score *: [int](https://docs.python.org/3/builtins/functions.html#int) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

The highest score this attempt could have earned; set exactly when `score` is.

#### score *: [int](https://docs.python.org/3/builtins/functions.html#int) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

The ordered score, in `0..max_score`; `None` for a right/wrong response.

#### to_dict()

A JSON-ready dict. `Outcome` is a `str` enum, so it needs no encoding.

An unscored response leaves `score` and `max_score` out, so a right/wrong log
is written exactly as it was before scores existed.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* learny.tracing.ResponseLog(, rootdir=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The append-only record of every response. The single source of truth.

One JSON-lines file per student, so one student’s data can be handed over, audited
or deleted on its own — which matters when the data is a child’s.

Append-only is not fastidiousness: the estimator *will* change, and a log that can
be replayed is what makes changing it a re-run rather than a migration.

```pycon
>>> import tempfile
>>> from learny.tracing.records import Response, Outcome
>>> log = ResponseLog(rootdir=tempfile.mkdtemp())
>>> log.append(Response('ada', 'q1', Outcome.CORRECT, at=1.0))
>>> log.append(Response('ada', 'q2', Outcome.SKIPPED, at=2.0))
>>> log.append(Response('bob', 'q1', Outcome.WRONG, at=1.5))
>>> sorted(log.students())
['ada', 'bob']
>>> [r.item for r in log['ada']]
['q1', 'q2']
>>> len(list(log))
3
```

#### append(response)

Append one response. Never rewrites or reorders what is already there.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### extend(responses)

Append many responses, grouped so each student’s file is opened once.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### students()

Every student with at least one logged response.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### *class* learny.tracing.ScoreCalibrationReport(n, log_loss, base_log_loss, rps, base_rps, ece, bins)

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
  [`ScoreCalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.ScoreCalibrationReport)

### *class* learny.tracing.Skill(mu, var, n=0, t=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A Gaussian belief about one skill, on the logit scale.

```pycon
>>> s = Skill(mu=0.5, var=0.25, n=4)
>>> round(s.sd, 3)
0.5
>>> lo, hi = s.interval()
>>> round(lo, 2), round(hi, 2)
(-0.48, 1.48)
```

#### interval(z=1.96)

A credible interval on the logit scale.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### *class* learny.tracing.Weakest(masteries=(), , reason=None)

Bases: [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

What [`LearnerModel.weakest()`](#learny.tracing.LearnerModel.weakest) returns: a list of `Mastery`, plus why.

It *is* a list — it compares, iterates, slices and serialises like one — so callers
that treat the result as a list keep working. `reason` is `None` when the list is
non-empty and says why it is empty otherwise; see [`LearnerModel.weakest()`](#learny.tracing.LearnerModel.weakest). It
describes the answer as returned: slicing gives a plain list, and a caller that
mutates the result owns keeping `reason` meaningful.

```pycon
>>> w = Weakest(reason='no_evidence')
>>> w == [], w.reason
(True, 'no_evidence')
```

### learny.tracing.attempt_features(response)

The default per-attempt feature source: `response.meta['features']`, or `None`.

These describe how one attempt was set up (`n_decoys`, a mix with vocals), so the
same item can be harder on one attempt than on another.

```pycon
>>> attempt_features(Response('s', 'q', True, meta={'features': {'n_decoys': 3}}))
{'n_decoys': 3}
>>> attempt_features(Response('s', 'q', True)) is None
True
```

* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### learny.tracing.binomial_thresholds(item, max_score)

Thresholds under which a score out of `m` is `m` steps taken at one rate.

`tau_k = log(k / (m - k + 1))`. With these, the Partial Credit Model’s distribution
of the score is binomial with step rate `expit(skill - difficulty)`, so the expected
*fraction* of the maximum equals the right/wrong model’s probability of a correct
answer, and an item’s `difficulty` means the same thing however it is scored. That
is why it is the default: it is the one choice that keeps an externally calibrated
difficulty meaningful with no new parameters (with `guess=0`: a score is never a
guess). It is not a claim that the steps really are independent, and it makes a score
out of `m` carry up to `m` times the evidence of one right/wrong answer; thresholds
spread wider apart carry less.

```pycon
>>> binomial_thresholds(Item('q'), 1)  # one step: the right/wrong model
[0.0]
>>> [round(t, 3) for t in binomial_thresholds(Item('q'), 4)]
[-1.386, -0.405, 0.405, 1.386]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

### learny.tracing.calibration(log, , items, estimator, students=None, n_bins=10)

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
scored by [`score_calibration()`](#learny.tracing.score_calibration) instead (#31).

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
  [`CalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.CalibrationReport)

### learny.tracing.compare_estimators(log, , items, candidates, students=None, tolerance_se=1.0)

Replay `log` prequentially under each candidate and pick one; see [`Comparison`](#learny.tracing.Comparison).

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
  [`Comparison`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.Comparison)

### learny.tracing.data_dir(kind='', , app_name='learny')

The per-kind data directory, created on demand.

Resolution order: the `LEARNY_DATA_DIR` environment variable, then
`config2py.AppData` if it is installed (which gets Windows right), then the XDG
default. Data is always written under a *kind* subfolder so the root stays free for
kinds that do not exist yet.

```pycon
>>> import tempfile, os
>>> os.environ['LEARNY_DATA_DIR'] = tmp = tempfile.mkdtemp()
>>> data_dir('responses') == Path(tmp) / 'responses'
True
>>> data_dir('responses').is_dir()
True
```

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### learny.tracing.difficulty_from_rank(rank, n_ranks)

Map an ordinal difficulty band (1-based, 1 = easiest) to a proportion in (0, 1).

Published difficulty is often an ordinal band rather than a measured pass rate. This
spreads `n_ranks` bands evenly across the open unit interval. It is a *prior*, not a
measurement: it says band 3 is harder than band 2, and how much is then corrected by
data.

```pycon
>>> [round(difficulty_from_rank(r, 3), 3) for r in (1, 2, 3)]
[0.25, 0.5, 0.75]
>>> round(difficulty_from_rank(1, 1), 3)
0.5
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### learny.tracing.estimate_store(, rootdir=None)

Per-student mastery estimates, keyed by student.

This is a **cache**. Anything in here can be thrown away and rebuilt by replaying
the response log, and the tests assert exactly that.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### learny.tracing.expit(x)

The logistic function, overflow-safe at the tails.

```pycon
>>> expit(0.0)
0.5
>>> round(expit(2.0), 4)
0.8808
>>> expit(-10000.0)  # a naive 1/(1+exp(-x)) would raise OverflowError here
0.0
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### learny.tracing.fit_feature_difficulty(log, \*, items, features=None, attempt_features=<function attempt_features>, students=None, anchor='location', ability_prior_var=None, residual_var=None, weight_prior_var=1.0, intercept_prior_var=4.0, max_iter=100, max_em_iter=200, tol=1e-09)

Fit which item features predict difficulty, from a log of play.

`features` maps an item key to `{name: value}`; by default each item’s
`meta['features']` ([`item_features()`](#learny.tracing.item_features)). Every item answered in the log needs a
finite value for every feature named anywhere, or the fit is refused rather than
guessed. A right/wrong response counts as one trial, a score `k` out of
`max_score` as `k` successes in `max_score` trials (the binomial reading that
[`binomial_thresholds()`](learny.tracing.estimators.html.md#learny.tracing.estimators.binomial_thresholds) gives a score; other step
spacings are not modelled here); skips are not evidence about difficulty and are
left out. Guessing is not modelled.

**Per-attempt features.** `attempt_features` reads, from each response, features
of how that attempt was set up (by default `response.meta['features']`, see
[`attempt_features()`](#learny.tracing.attempt_features); `None` ignores them). They enter the same linear
predictor, `difficulty = intercept + w . x_item + v . x_attempt + residual_item`,
standardised over the fitted attempts and with the same weight prior, but with no
residual of their own. If any scored attempt has them, every one needs a finite
value for each, or the fit is refused. A given `difficulty` that anchors the scale
is the item’s at the average attempt.

**The scale.** Every answered item that already has a `difficulty` can anchor
the fit to the bank’s scale. `anchor="location"` (the default) fits on play alone
and then shifts the intercept (and the students’ mean ability) so that the anchors’
fitted difficulties average their given ones: filled items land where the bank’s
would, while the weights stay exactly what play says, whatever the bank’s spread
(a published band from [`difficulty_from_rank()`](learny.tracing.estimators.html.md#learny.tracing.estimators.difficulty_from_rank) is
an ordering, not a scale). `anchor="exact"` holds each anchor at its given value
instead, which also lets the given values inform the weights; it trusts them, spread
included, and a bank anchored throughout is then a regression of the given values
on the features, with play only placing the students. `anchor="none"` keeps the
fitted students’ scale (mean ability 0). A given difficulty of exactly 0 or 1 has no
finite logit and is skipped as an anchor, with a warning.

**What it assumes about the log.** Each student has one ability over the log
(learning within the window is not modelled, so fit on a window short enough for
that). Which items a student was given may depend on their *earlier answers*, as an
adaptive game’s choice does, but not on anything about them the log does not show:
stronger students steered to harder items by some other route confound ability
with difficulty, and no fit of this log can undo that.

**The priors.** Weights are per *standard deviation* of each feature across the
fitted items, so `weight_prior_var=1` says a one-sd change in a feature plausibly
moves difficulty by up to a logit or two, whatever its units. `residual_var` (how
far an item may sit from what its features predict) and `ability_prior_var` (how
spread the students are) are estimated from the log when left `None` (empirical
Bayes, by EM; the ability spread only with two or more students, else 1.0), which is what keeps the weights’ sds honest: fixed below the truth,
the 95% intervals covered the true weights 72-80% of the time; estimated, 93-97%
(`docs/learner-model-design.md`, decision 13). With around 15 responses per item
the estimates run about 20% low, as Laplace estimates of variance components do on
right/wrong data.

```pycon
>>> import random
>>> rng = random.Random(0)
>>> bank = {f'q{i}': Item(f'q{i}', meta={'features': {'length': i % 6}}) for i in range(30)}
>>> log = {}
>>> for s in range(20):
...     theta = rng.gauss(0, 1)
...     log[f's{s}'] = [
...         Response(f's{s}', q, rng.random() < expit(theta - (0.6 * bank[q].meta['features']['length'] - 1.5)))
...         for q in bank]
>>> model = fit_feature_difficulty(log, items=bank)
>>> w = model.weights()['length']
>>> abs(w.mean - 0.6) < 2 * w.sd, w.mean > 2 * w.sd   # recovered, and it matters
(True, True)
>>> model.predict({'length': 5}).mean > model.predict({'length': 0}).mean
True
```

* **Return type:**
  [`FeatureDifficulty`](learny.tracing.difficulty.html.md#learny.tracing.difficulty.FeatureDifficulty)

### learny.tracing.fit_threshold_spread(log, , items, spreads=(1.0, 0.75, 1.3333333333333333, 0.5, 2.0, 0.3333333333333333, 3.0), estimator=None, students=None, tolerance_se=1.0)

The threshold spread a log supports for [`PartialCreditEstimator`](#learny.tracing.PartialCreditEstimator).

Each spread is a candidate `thresholds=spread_thresholds(spread)` on `estimator`
(default: a plain `PartialCreditEstimator`), compared by prequential score log loss
with the one-standard-error rule ([`compare_estimators()`](#learny.tracing.compare_estimators)), preferring spreads
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
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`Comparison`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.Comparison)]

### learny.tracing.item_features(item)

The default feature source: `item.meta['features']`, or `None`.

```pycon
>>> item_features(Item('q', meta={'features': {'n_glyphs': 4}}))
{'n_glyphs': 4}
>>> item_features(Item('q')) is None
True
```

* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### learny.tracing.label_separation(state, , estimator=None, min_n=1, threshold=2.0)

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
  [`LabelSeparation`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.LabelSeparation)

### learny.tracing.logit(p, , eps=1e-06)

Inverse of [`expit()`](#learny.tracing.expit), clamped away from 0 and 1 so it stays finite.

```pycon
>>> logit(0.5)
0.0
>>> round(logit(0.8808), 3)
2.0
>>> logit(0.0) < -10
True
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### learny.tracing.mark_not_reached(responses)

Flag the trailing run of blanks in one sitting as *not reached*.

A blank at the end of a paper usually means the clock ran out; a blank with answered
questions after it is a decision to skip. Only the second is evidence about the
student. Pass one sitting’s responses **in the order they were presented**.

```pycon
>>> from learny.tracing.records import Response, Outcome
>>> rs = [Response('a', f'q{i}', o) for i, o in
...       enumerate(['correct', 'skipped', 'wrong', 'skipped', 'skipped'])]
>>> [r.meta.get('not_reached', False) for r in mark_not_reached(rs)]
[False, False, False, True, True]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Response`](learny.tracing.records.html.md#learny.tracing.records.Response)]

### learny.tracing.prequential(responses, , items, estimator)

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

### learny.tracing.reads_scores(estimator)

Whether `estimator` forecasts ordered scores: it has `score_probabilities`.

It decides which report a scored response belongs in: an estimator without it
forecasts the right/wrong `outcome`, so the response is scored by
[`calibration()`](#learny.tracing.calibration); one with it is taken to forecast (and learn from) the score, so
the response is scored by [`score_calibration()`](#learny.tracing.score_calibration) instead. It is a check of
capability, not of what `observe` reads: an estimator that forecasts scores while
learning only from outcomes should not define `score_probabilities`.

```pycon
>>> from learny.tracing.estimators import PartialCreditEstimator, RaschEstimator
>>> reads_scores(RaschEstimator()), reads_scores(PartialCreditEstimator())
(False, True)
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### learny.tracing.response_log(, rootdir=None)

The default response log, under `~/.local/share/learny/responses/`.

* **Return type:**
  [`ResponseLog`](learny.tracing.stores.html.md#learny.tracing.stores.ResponseLog)

### learny.tracing.restrict_labels(items, , keep, drop_unlabelled=False)

Project an item bank onto a subset of its labels — one facet, say.

Labels that never vary independently of each other cannot be told apart: tag every
item with nine labels and each label’s deviation stays at the student’s global
skill, whatever the data. Modelling one facet at a time is often what makes labels
separable ([`label_separation()`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.label_separation) measures it).
*Which* labels belong together is a judgement about the taxonomy, so the library
never collapses anything by itself; this is the explicit, opt-in way to do it.

`keep` is a collection of labels or a predicate on a label. Weights are preserved.
An item left with no labels still carries its difficulty and still informs the
student’s global skill, so it is kept unless `drop_unlabelled=True`.

```pycon
>>> bank = {
...     'q1': Item('q1', labels={'topic:fractions': 1.0, 'trap:units': 0.6}),
...     'q2': Item('q2', labels=('trap:units',), difficulty=0.7),
... }
>>> topics = restrict_labels(bank, keep=lambda label: label.startswith('topic:'))
>>> topics['q1'].weights, topics['q2'].weights, topics['q2'].difficulty
({'topic:fractions': 1.0}, {}, 0.7)
>>> sorted(restrict_labels(bank, keep={'topic:fractions'}, drop_unlabelled=True))
['q1']
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Item`](learny.tracing.records.html.md#learny.tracing.records.Item)]

### learny.tracing.score_calibration(log, , items, estimator, students=None, n_bins=10)

Prequential calibration of `estimator`’s score forecasts over `log`.

The twin of [`calibration()`](#learny.tracing.calibration) for responses with an ordered `score`: each is
forecast by `estimator.score_probabilities` from the state before it, every
response (scored, right/wrong or skipped) is replayed, and only the scored ones are
scored. The estimator must read scores ([`reads_scores()`](#learny.tracing.reads_scores)), such as
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
  [`ScoreCalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.ScoreCalibrationReport)

### learny.tracing.spread_thresholds(spread)

Binomial thresholds stretched by `spread`: `tau_k = spread * log(k / (m - k + 1))`.

`spread=1` is [`binomial_thresholds()`](#learny.tracing.binomial_thresholds). A wider spread makes the middle levels
more likely and the extremes rarer, so one score carries less evidence; narrower
makes a score sharper. It keeps the thresholds centred, so an item’s `difficulty`
still sits at the middle of its scale. [`fit_threshold_spread()`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.fit_threshold_spread)
picks `spread` from a log.

```pycon
>>> [round(t, 3) for t in spread_thresholds(2.0)(Item('q'), 2)]
[-1.386, 1.386]
>>> spread_thresholds(1.0)(Item('q'), 4) == binomial_thresholds(Item('q'), 4)
True
>>> spread_thresholds(2.0) == spread_thresholds(2.0)
True
```

* **Return type:**
  [`SpreadThresholds`](learny.tracing.estimators.html.md#learny.tracing.estimators.SpreadThresholds)

### Modules

| [`diagnostics`](learny.tracing.diagnostics.html.md#module-learny.tracing.diagnostics)   | Diagnostics: when to believe the model, and how well it has predicted so far.        |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`difficulty`](learny.tracing.difficulty.html.md#module-learny.tracing.difficulty)     | Explanatory item difficulty: which item features make an item hard.                  |
| [`estimators`](learny.tracing.estimators.html.md#module-learny.tracing.estimators)     | Estimators: how one response changes what we believe about a student.                |
| [`model`](learny.tracing.model.html.md#module-learny.tracing.model)               | The facade: one object that records responses and answers questions about a student. |
| [`records`](learny.tracing.records.html.md#module-learny.tracing.records)           | Core data types for learner modelling: items, outcomes, and responses.               |
| [`stores`](learny.tracing.stores.html.md#module-learny.tracing.stores)             | Where learner data lives, and how code reaches it.                                   |
