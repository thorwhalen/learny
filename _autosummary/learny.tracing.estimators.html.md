# learny.tracing.estimators

Estimators: how one response changes what we believe about a student.

The default, [`RaschEstimator`](#learny.tracing.estimators.RaschEstimator), is **online Rasch with a Gaussian posterior** — one
Newton step on the log-posterior per response, which is Glickman’s Glicko update against
an opponent of known strength. Belief about a student is:

```default
logit P(correct) = global_skill + aggregate(label skills) - item_difficulty
```

where every skill is a posterior `(mu, var)` rather than a point. Carrying the variance
is what lets the model say *how sure* it is, decay confidence over time without
pretending to know which way a skill moved, and behave sanely at zero observations — all
from one formula instead of three bolted-on heuristics.

Elo is the same update with the information term frozen: Elo’s uncertainty function
`U(n) = a/(1 + b*n)` is exactly `1/(1/var + n*I)` for constant information `I`. So
`gain='elo'` is not a different estimator, it is this one with a constant step size.

Three decisions worth knowing before reading the code:

**Item difficulty does not update by default.** Textbook Elo moves ability and item
difficulty in opposite directions from the same residual, which works when a population
pins each item down. With one or two learners — a family, a tutor, one classroom — the two
are not jointly identifiable: they absorb each other and you get a model that fits the
history perfectly and predicts nothing. The default takes difficulty as given, from an
observed source such as a published difficulty band.

**The hierarchy is the cold-start mechanism, not a refinement.** A student may have one or
two responses against any given label. A label therefore carries only a *deviation* from
that student’s global skill, shrunk hard toward zero by its prior. One paper gives the
global skill enough precision to serve as every label’s prior before any label-specific
evidence exists. So the pooling that makes sparse labels usable happens \*\*across labels
within one student\*\* — no other student need exist, and none is ever consulted.

**A skip is not a wrong answer, and not all skips are alike.** A blank at the end of a
paper is a clock, not a judgement; a blank with answers after it is an abstention, which
carries real information about confidence. They are treated differently, and neither is
scored as wrong.

### Functions

| [`logit`](#learny.tracing.estimators.logit)(p, \*[, eps])                 | Inverse of [`expit()`](#learny.tracing.estimators.expit), clamped away from 0 and 1 so it stays finite.   |
|--------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| [`expit`](#learny.tracing.estimators.expit)(x)                            | The logistic function, overflow-safe at the tails.                                                                   |
| [`difficulty_from_rank`](#learny.tracing.estimators.difficulty_from_rank)(rank, n_ranks) | Map an ordinal difficulty band (1-based, 1 = easiest) to a proportion in (0, 1).                                     |
| [`mark_not_reached`](#learny.tracing.estimators.mark_not_reached)(responses)         | Flag the trailing run of blanks in one sitting as *not reached*.                                                     |

### Classes

| [`Estimator`](#learny.tracing.estimators.Estimator)(\*args, \*\*kwargs)                     | The seam.                                                |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| [`RaschEstimator`](#learny.tracing.estimators.RaschEstimator)([prior_var, label_prior_var, ...]) | Online Rasch with a Gaussian posterior.                  |
| [`Mastery`](#learny.tracing.estimators.Mastery)(label, skill[, prior_var, deviation])     | What the model believes about one student and one label. |
| [`Skill`](#learny.tracing.estimators.Skill)(mu, var[, n, t])                            | A Gaussian belief about one skill, on the logit scale.   |

### *class* learny.tracing.estimators.Estimator(\*args, \*\*kwargs)

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
`credible_below=None`).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](#learny.tracing.estimators.Mastery)]

#### observe(state, response, item)

Return the new state after one response. Must not mutate `state`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### predict(state, item)

Probability this student answers this item correctly.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### *class* learny.tracing.estimators.Mastery(label, skill, prior_var=1.0, , deviation=None)

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

A credible interval for [`probability`](#learny.tracing.estimators.Mastery.probability).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### *property* probability *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Probability of success on an item of average difficulty for this label.

### *class* learny.tracing.estimators.RaschEstimator(prior_var=1.0, label_prior_var=0.25, guess=0.0, forget_per_week=0.02, abstain_weight=0.5, conjunctivity=0.0, gain='bayes', elo_rate=0.6, update_difficulty=False)

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
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](#learny.tracing.estimators.Mastery)]

#### observe(state, response, item)

The new state after one response. Pure: `state` is not mutated.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

#### predict(state, item, , at=None)

Probability of a correct answer, integrating over the posterior.

With no evidence the prediction sits near the item’s own base rate, but pulled
toward a coin flip — because the model is being honest that it knows nothing about
*this* student, not just repeating what it knows about the item:

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

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

#### prior_var *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 1.0*

Prior variance on the student’s global skill, in logits². 1.0 is a weak prior:
roughly, “this student is within ±2 logits of the reference population”.

#### skill(state)

The student’s global skill, independent of any label.

* **Return type:**
  [`Skill`](#learny.tracing.estimators.Skill)

#### update_difficulty *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= False*

Co-estimate item difficulty. Only sound with many learners per item; see the class
docstring for why that is off by default.

### *class* learny.tracing.estimators.Skill(mu, var, n=0, t=None)

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

### learny.tracing.estimators.difficulty_from_rank(rank, n_ranks)

Map an ordinal difficulty band (1-based, 1 = easiest) to a proportion in (0, 1).

Published difficulty is often an ordinal band rather than a measured pass rate. This
spreads `n_ranks` bands evenly across the open unit interval. It is a *prior*, not a
measurement: it says band 3 is harder than band 2, and how much is then corrected by
data.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

```pycon
>>> [round(difficulty_from_rank(r, 3), 3) for r in (1, 2, 3)]
[0.25, 0.5, 0.75]
>>> round(difficulty_from_rank(1, 1), 3)
0.5
```

### learny.tracing.estimators.expit(x)

The logistic function, overflow-safe at the tails.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

```pycon
>>> expit(0.0)
0.5
>>> round(expit(2.0), 4)
0.8808
>>> expit(-10000.0)  # a naive 1/(1+exp(-x)) would raise OverflowError here
0.0
```

### learny.tracing.estimators.logit(p, , eps=1e-06)

Inverse of [`expit()`](#learny.tracing.estimators.expit), clamped away from 0 and 1 so it stays finite.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

```pycon
>>> logit(0.5)
0.0
>>> round(logit(0.8808), 3)
2.0
>>> logit(0.0) < -10
True
```

### learny.tracing.estimators.mark_not_reached(responses)

Flag the trailing run of blanks in one sitting as *not reached*.

A blank at the end of a paper usually means the clock ran out; a blank with answered
questions after it is a decision to skip. Only the second is evidence about the
student. Pass one sitting’s responses **in the order they were presented**.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Response`](learny.tracing.records.html.md#learny.tracing.records.Response)]

```pycon
>>> from learny.tracing.records import Response, Outcome
>>> rs = [Response('a', f'q{i}', o) for i, o in
...       enumerate(['correct', 'skipped', 'wrong', 'skipped', 'skipped'])]
>>> [r.meta.get('not_reached', False) for r in mark_not_reached(rs)]
[False, False, False, True, True]
```
