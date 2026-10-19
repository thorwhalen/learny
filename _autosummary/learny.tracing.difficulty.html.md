# learny.tracing.difficulty

Explanatory item difficulty: which item features make an item hard.

An item bank often carries features of every item — how many glyphs it has, how
irregular its rhythm is, how frequent its words are — and a hypothesis that some of
them drive difficulty. [`fit_feature_difficulty()`](#learny.tracing.difficulty.fit_feature_difficulty) tests that hypothesis against
play. It fits the Linear Logistic Test Model (Fischer 1973) with a residual per item
(the random-item extension of De Boeck 2008):

```default
logit P(correct) = ability[student] - difficulty[item]
difficulty[item] = intercept + weights . features[item] + residual[item]
```

with Gaussian priors on every parameter, by maximum a posteriori and a Laplace
approximation, so each weight comes with a standard deviation: which features matter,
and how sure the fit is. The result predicts the difficulty of an item nobody has
played yet from its features alone, which is the cold start for a new item.

This is the one place in [`learny.tracing`](learny.tracing.html.md#module-learny.tracing) that reads *across* students, so it
follows the rule for that (decision 8 in `docs/learner-model-design.md`): it runs
only when called, over a log it is handed, and what it learns leaves as an exported,
reviewable artifact ([`FeatureDifficulty`](#learny.tracing.difficulty.FeatureDifficulty), JSON by [`to_dict()`](#learny.tracing.difficulty.FeatureDifficulty.to_dict))
that enters the learner model through the existing `items=` seam
([`apply()`](#learny.tracing.difficulty.FeatureDifficulty.apply)), never as a side effect of fitting.

### Functions

| [`fit_feature_difficulty`](#learny.tracing.difficulty.fit_feature_difficulty)(log, \*, items[, ...])   | Fit which item features predict difficulty, from a log of play.   |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| [`item_features`](#learny.tracing.difficulty.item_features)(item)                             | The default feature source: `item.meta['features']`, or `None`.   |

### Classes

| [`Estimate`](#learny.tracing.difficulty.Estimate)(mean, sd)                           | A posterior mean and standard deviation, on the logit scale.                                                          |
|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| [`FeatureDifficulty`](#learny.tracing.difficulty.FeatureDifficulty)(names, center, scale, ...) | A fitted explanatory difficulty model; see [`fit_feature_difficulty()`](#learny.tracing.difficulty.fit_feature_difficulty). |

### *class* learny.tracing.difficulty.Estimate(mean, sd)

Bases: [`NamedTuple`](https://docs.python.org/3/library/typing.html#typing.NamedTuple)

A posterior mean and standard deviation, on the logit scale.

#### mean *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Alias for field number 0

#### sd *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Alias for field number 1

### *class* learny.tracing.difficulty.FeatureDifficulty(names, center, scale, coef, covariance, residual_var, ability_mean=0.0, ability_var=1.0, residuals=dict(), anchors=0, n_students=0, n_responses=0, converged=True)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A fitted explanatory difficulty model; see [`fit_feature_difficulty()`](#learny.tracing.difficulty.fit_feature_difficulty).

Features are stored standardised (`(x - center) / scale` over the fitted items),
which is what the priors and the covariance refer to; [`weights()`](#learny.tracing.difficulty.FeatureDifficulty.weights) reports them
in each feature’s own units. `covariance` is over `(intercept, *weights)` in the
standardised form. `residual_var` is the prior variance of a new item’s departure
from what its features predict, `ability_mean` and `ability_var` the fitted
students’ ability distribution, on the scale of the bank’s given difficulties when
the fit was anchored on them. `residuals` holds each fitted item’s own departure,
as `(mean, variance, *covariance with the coefficients)`; it carries the fitted
students’ data, so [`apply()`](#learny.tracing.difficulty.FeatureDifficulty.apply) leaves it out unless asked. `converged` is false
when an iteration cap was hit (a `RuntimeWarning` said so at fit time).

#### apply(items, , features=None, overwrite=False, use_residuals=False)

A copy of `items` with each item’s `difficulty` predicted from features.

Only items without a difficulty are filled unless `overwrite=True`; an item
with no features is left as it is. The difficulty comes from the features alone
unless `use_residuals=True` adds each fitted item’s own residual. That residual
is learned from the fitted students’ answers, so feeding it back to estimate
those same students counts their answers twice; with one or two learners it is
mostly their own results (#18 review). The result is an item bank for the
`items=` seam of [`LearnerModel`](learny.tracing.model.html.md#learny.tracing.model.LearnerModel).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Item`](learny.tracing.records.html.md#learny.tracing.records.Item)]

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#learny.tracing.difficulty.FeatureDifficulty.to_dict); refuses an artifact of another schema.

* **Return type:**
  [`FeatureDifficulty`](#learny.tracing.difficulty.FeatureDifficulty)

#### predict(features, , item_id=None)

The difficulty, in logits, of an item with these features.

For any item the residual is unknown, so its prior variance `residual_var` is
added to the features’ part. Pass `item_id` of an item the model was fitted on
to use that item’s own fitted residual instead, with its posterior variance and
its covariance with the coefficients. Features far outside the fitted range are
extrapolated linearly, without warning.

* **Return type:**
  [`Estimate`](#learny.tracing.difficulty.Estimate)

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
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Estimate`](#learny.tracing.difficulty.Estimate)]

### learny.tracing.difficulty.fit_feature_difficulty(log, , items, features=None, students=None, anchor='location', ability_prior_var=None, residual_var=None, weight_prior_var=1.0, intercept_prior_var=4.0, max_iter=100, max_em_iter=200, tol=1e-09)

Fit which item features predict difficulty, from a log of play.

`features` maps an item key to `{name: value}`; by default each item’s
`meta['features']` ([`item_features()`](#learny.tracing.difficulty.item_features)). Every item answered in the log needs a
finite value for every feature named anywhere, or the fit is refused rather than
guessed. A right/wrong response counts as one trial, a score `k` out of
`max_score` as `k` successes in `max_score` trials (the binomial reading that
[`binomial_thresholds()`](learny.tracing.estimators.html.md#learny.tracing.estimators.binomial_thresholds) gives a score; other step
spacings are not modelled here); skips are not evidence about difficulty and are
left out. Guessing is not modelled.

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
  [`FeatureDifficulty`](#learny.tracing.difficulty.FeatureDifficulty)

### learny.tracing.difficulty.item_features(item)

The default feature source: `item.meta['features']`, or `None`.

```pycon
>>> item_features(Item('q', meta={'features': {'n_glyphs': 4}}))
{'n_glyphs': 4}
>>> item_features(Item('q')) is None
True
```

* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)
