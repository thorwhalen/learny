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

| [`estimate_store`](#learny.tracing.estimate_store)(\*[, rootdir])       | Per-student mastery estimates, keyed by student.                                                                   |
|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| [`response_log`](#learny.tracing.response_log)(\*[, rootdir])         | The default response log, under `~/.local/share/learny/responses/`.                                                |
| [`data_dir`](#learny.tracing.data_dir)([kind, app_name])          | The per-kind data directory, created on demand.                                                                    |
| [`difficulty_from_rank`](#learny.tracing.difficulty_from_rank)(rank, n_ranks) | Map an ordinal difficulty band (1-based, 1 = easiest) to a proportion in (0, 1).                                   |
| [`mark_not_reached`](#learny.tracing.mark_not_reached)(responses)         | Flag the trailing run of blanks in one sitting as *not reached*.                                                   |
| [`expit`](#learny.tracing.expit)(x)                            | The logistic function, overflow-safe at the tails.                                                                 |
| [`logit`](#learny.tracing.logit)(p, \*[, eps])                 | Inverse of [`expit()`](#learny.tracing.expit), clamped away from 0 and 1 so it stays finite. |

### Classes

| [`LearnerModel`](#learny.tracing.LearnerModel)(\*[, items, estimator, log, ...])    | What a student knows, estimated from what they have answered.               |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`Item`](#learny.tracing.Item)(id[, labels, difficulty, meta])              | A question, with the skill labels it exercises and its observed difficulty. |
| [`Outcome`](#learny.tracing.Outcome)(\*values)                                 | What happened when a student met an item.                                   |
| [`Response`](#learny.tracing.Response)(student, item, outcome[, at, meta])      | One student meeting one item, once.                                         |
| [`Mastery`](#learny.tracing.Mastery)(label, skill[, prior_var])                | What the model believes about one student and one label.                    |
| [`Skill`](#learny.tracing.Skill)(mu, var[, n, t])                            | A Gaussian belief about one skill, on the logit scale.                      |
| [`Estimator`](#learny.tracing.Estimator)(\*args, \*\*kwargs)                     | The seam.                                                                   |
| [`RaschEstimator`](#learny.tracing.RaschEstimator)([prior_var, label_prior_var, ...]) | Online Rasch with a Gaussian posterior.                                     |
| [`ResponseLog`](#learny.tracing.ResponseLog)(\*[, rootdir])                        | The append-only record of every response.                                   |

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

### *class* learny.tracing.Item(id, labels=(), difficulty=None, meta=<factory>)

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
[`replay()`](#learny.tracing.LearnerModel.replay) can rebuild from it.

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

### *class* learny.tracing.Mastery(label, skill, prior_var=1.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What the model believes about one student and one label.

`probability` is the chance of success on an item of *average* difficulty, which is
what makes two labels comparable. `confidence` is a genuine posterior quantity, not
a heuristic: it falls out of the variance.

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
  [`Skill`](learny.tracing.estimators.html.md#learny.tracing.estimators.Skill)

#### update_difficulty *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= False*

Co-estimate item difficulty. Only sound with many learners per item; see the class
docstring for why that is off by default.

### *class* learny.tracing.Response(student, item, outcome, at=None, meta=<factory>)

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

#### *property* correct *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

True only for an outright correct answer; a skip is not a correct answer.

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#learny.tracing.Response.to_dict), tolerant of unknown keys from a future version.

* **Return type:**
  [`Response`](learny.tracing.records.html.md#learny.tracing.records.Response)

#### to_dict()

A JSON-ready dict. `Outcome` is a `str` enum, so it needs no encoding.

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

### learny.tracing.data_dir(kind='', , app_name='learny')

The per-kind data directory, created on demand.

Resolution order: the `LEARNY_DATA_DIR` environment variable, then
`config2py.AppData` if it is installed (which gets Windows right), then the XDG
default. Data is always written under a *kind* subfolder so the root stays free for
kinds that do not exist yet.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

```pycon
>>> import tempfile, os
>>> os.environ['LEARNY_DATA_DIR'] = tmp = tempfile.mkdtemp()
>>> data_dir('responses') == Path(tmp) / 'responses'
True
>>> data_dir('responses').is_dir()
True
```

### learny.tracing.difficulty_from_rank(rank, n_ranks)

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

### learny.tracing.estimate_store(, rootdir=None)

Per-student mastery estimates, keyed by student.

This is a **cache**. Anything in here can be thrown away and rebuilt by replaying
the response log, and the tests assert exactly that.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### learny.tracing.expit(x)

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

### learny.tracing.logit(p, , eps=1e-06)

Inverse of [`expit()`](#learny.tracing.expit), clamped away from 0 and 1 so it stays finite.

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

### learny.tracing.mark_not_reached(responses)

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

### learny.tracing.response_log(, rootdir=None)

The default response log, under `~/.local/share/learny/responses/`.

* **Return type:**
  [`ResponseLog`](learny.tracing.stores.html.md#learny.tracing.stores.ResponseLog)

### Modules

| [`estimators`](learny.tracing.estimators.html.md#module-learny.tracing.estimators)   | Estimators: how one response changes what we believe about a student.                |
|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`model`](learny.tracing.model.html.md#module-learny.tracing.model)             | The facade: one object that records responses and answers questions about a student. |
| [`records`](learny.tracing.records.html.md#module-learny.tracing.records)         | Core data types for learner modelling: items, outcomes, and responses.               |
| [`stores`](learny.tracing.stores.html.md#module-learny.tracing.stores)           | Where learner data lives, and how code reaches it.                                   |
