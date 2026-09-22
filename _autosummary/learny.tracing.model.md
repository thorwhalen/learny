# learny.tracing.model

The facade: one object that records responses and answers questions about a student.

`LearnerModel` is the thing most callers touch. It owns four collaborators, each one a
constructor argument with a working default, so the simple case needs no arguments at all
and every part can be replaced without touching the others:

| `items`     | what is known about each question (labels, difficulty)                                                                                     |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `estimator` | how one response changes belief ([`RaschEstimator`](learny.tracing.estimators.md#learny.tracing.estimators.RaschEstimator)) |
| `log`       | the append-only record of responses — the source of truth                                                                                  |
| `estimates` | the cache of per-student state, rebuildable from `log`                                                                                     |

### Module Attributes

| [`DEFAULT_CREDIBLE_BELOW`](#learny.tracing.model.DEFAULT_CREDIBLE_BELOW)   | How many posterior standard deviations below the student's own level a label's deviation must be before [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) calls it a weakness.   |
|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

### Classes

| [`LearnerModel`](#learny.tracing.model.LearnerModel)(\*[, items, estimator, log, ...])   | What a student knows, estimated from what they have answered.                                                        |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| [`Weakest`](#learny.tracing.model.Weakest)([masteries, reason])                     | What [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) returns: a list of `Mastery`, plus why. |

### learny.tracing.model.DEFAULT_CREDIBLE_BELOW *= 1.0*

How many posterior standard deviations below the student’s own level a label’s
deviation must be before [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) calls it a weakness. 1.0 is a
one-sided ~84% credible bound *per label*. It stops a set of labels that never vary
independently (many labels on every item) from being ranked at all, and fires on a few
papers of real evidence. It is **not** corrected for testing many labels at once: a
student with no real weakness and six separable labels gets at least one label flagged
more often than not. Raise `credible_below` when a false “practise this” is costly.

### *class* learny.tracing.model.LearnerModel(, items=None, estimator=None, log=None, estimates=None)

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

Prequential calibration over the log; see [`calibration()`](#learny.tracing.model.LearnerModel.calibration).

Reads the log only; the estimate cache is neither used nor changed.

* **Return type:**
  [`CalibrationReport`](learny.tracing.diagnostics.md#learny.tracing.diagnostics.CalibrationReport)

#### mastery(student)

Per-label mastery for one student, weakest first when sorted by skill.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](learny.tracing.estimators.md#learny.tracing.estimators.Mastery)]

#### predict(student, item)

Probability that `student` answers `item` correctly.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### record(student, item, outcome, , at=None, \*\*meta)

Log one response and fold it into the student’s estimate.

The log is written first: if updating the cache fails, the evidence survives and
[`replay()`](#learny.tracing.model.LearnerModel.replay) can rebuild from it.

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

#### separation(student, , threshold=2.0)

How distinguishable this student’s labels are; see `label_separation()`.

Check `.distinguishable` before acting on an ordering from [`weakest()`](#learny.tracing.model.LearnerModel.weakest).
The deviations are de-shrunk with this model’s own estimator prior.

* **Return type:**
  [`LabelSeparation`](learny.tracing.diagnostics.md#learny.tracing.diagnostics.LabelSeparation)

#### weakest(student, n=5, , credible_below=1.0)

The labels this student is credibly weakest on — what to practise next.

By default a label is returned only when its deviation from the student’s *own*
global skill is credibly negative: the upper bound `mu + z * sd` of
`Mastery.deviation` is below
zero, with `z = credible_below` (default [`DEFAULT_CREDIBLE_BELOW`](#learny.tracing.model.DEFAULT_CREDIBLE_BELOW)). The
survivors are ranked worst first and the first `n` returned. `z = 0` keeps
every label whose deviation is merely below zero on average; larger `z`
demands more certainty. The bound is per label, with no correction for how many
labels are tested (see [`DEFAULT_CREDIBLE_BELOW`](#learny.tracing.model.DEFAULT_CREDIBLE_BELOW)), so with several separable
labels a label or two can pass by chance. `credible_below=None` switches the gate off and ranks
every label with evidence by posterior mean — check [`separation()`](#learny.tracing.model.LearnerModel.separation) before
believing that ranking.

Labels with no evidence are never included: the model has nothing to say about
them, and saying it anyway is how a learner model loses trust.

**An empty answer is common and says why.** The result is a list (a
[`Weakest`](#learny.tracing.model.Weakest)) whose `reason` is `None` when it holds labels, and
otherwise one of:

* `"no_evidence"` — the student has answered nothing that carries a label;
* `"no_credible_weakness"` — there is evidence, but no label is credibly
  below the student’s own level. That is a statement about *relative*
  weakness, not “nothing to practise”: practise at the student’s overall level
  (`model.estimator.skill(state)` for the default estimator).

With the default estimator the split between “globally weak” and “weak on this
label” comes from the priors, so part of a uniform shortfall is attributed to
every label: a student who gets nearly everything wrong can see several labels
returned here, in an order that means little. [`separation()`](#learny.tracing.model.LearnerModel.separation) says whether
an order among the returned labels is worth believing.

Raises `ValueError` for a negative `credible_below` (which would admit labels
credibly *above* the student’s level), and `TypeError` when the gate is on but
the estimator’s [`Mastery`](learny.tracing.estimators.md#learny.tracing.estimators.Mastery) values carry no
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
```

* **Return type:**
  [`Weakest`](#learny.tracing.model.Weakest)

### *class* learny.tracing.model.Weakest(masteries=(), , reason=None)

Bases: [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

What [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) returns: a list of `Mastery`, plus why.

It *is* a list — it compares, iterates, slices and serialises like one — so callers
that treat the result as a list keep working. `reason` is `None` when the list is
non-empty and says why it is empty otherwise; see [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest). It
describes the answer as returned: slicing gives a plain list, and a caller that
mutates the result owns keeping `reason` meaningful.

```pycon
>>> w = Weakest(reason='no_evidence')
>>> w == [], w.reason
(True, 'no_evidence')
```
