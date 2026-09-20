# learny.tracing.model

The facade: one object that records responses and answers questions about a student.

`LearnerModel` is the thing most callers touch. It owns four collaborators, each one a
constructor argument with a working default, so the simple case needs no arguments at all
and every part can be replaced without touching the others:

| `items`     | what is known about each question (labels, difficulty)                                                                                     |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `estimator` | how one response changes belief ([`RaschEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.RaschEstimator)) |
| `log`       | the append-only record of responses — the source of truth                                                                                  |
| `estimates` | the cache of per-student state, rebuildable from `log`                                                                                     |

### Classes

| [`LearnerModel`](#learny.tracing.model.LearnerModel)(\*[, items, estimator, log, ...])   | What a student knows, estimated from what they have answered.   |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|

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

#### mastery(student)

Per-label mastery for one student, weakest first when sorted by skill.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mastery`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery)]

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

#### weakest(student, n=5)

The `n` labels this student looks weakest on — what to practise next.

Labels with no evidence are not included: the model has nothing to say about
them, and saying it anyway is how a learner model loses trust.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Mastery`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery)]
