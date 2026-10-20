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

### Module Attributes

| [`DEFAULT_CREDIBLE_BELOW`](#learny.tracing.model.DEFAULT_CREDIBLE_BELOW)   | How many posterior standard deviations below its comparator a label must be before [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) calls it a weakness.   |
|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`DEFAULT_RELATIVE_TO`](#learny.tracing.model.DEFAULT_RELATIVE_TO)      | the precision-weighted mean of the student's *other* labels, so whatever part of a shortfall every label shares cancels out.                                                      |
| [`DEFAULT_MULTIPLICITY`](#learny.tracing.model.DEFAULT_MULTIPLICITY)     | How the bound accounts for testing several labels at once.                                                                                                                        |
| [`DEFAULT_NULL_DRAWS`](#learny.tracing.model.DEFAULT_NULL_DRAWS)       | How many times `weakest(multiplicity="simulated")` replays a student's record under "no label deviation".                                                                         |

### Classes

| [`LearnerModel`](#learny.tracing.model.LearnerModel)(\*[, items, estimator, log, ...])   | What a student knows, estimated from what they have answered.                                                        |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| [`Weakest`](#learny.tracing.model.Weakest)([masteries, reason])                     | What [`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) returns: a list of `Mastery`, plus why. |

### learny.tracing.model.DEFAULT_CREDIBLE_BELOW *= 1.0*

How many posterior standard deviations below its comparator a label must be before
[`LearnerModel.weakest()`](#learny.tracing.model.LearnerModel.weakest) calls it a weakness. 1.0 is a one-sided ~84% credible
bound. With the default `multiplicity="calibrated"` (and `"bonferroni"`) it is the
bound for the *whole set* of labels tested — a student with no real weakness gets a
label flagged about one time in six at most, however many labels there are — and with
`multiplicity="none"` it is per label. It stops a set of labels that never vary independently (many labels on every
item) from being ranked at all. Raise it when a false “practise this” is costly.

### learny.tracing.model.DEFAULT_MULTIPLICITY *= 'calibrated'*

How the bound accounts for testing several labels at once. `"calibrated"` raises the
per-label z as Bonferroni does, so the chance of *any* false flag is about
`1 - Phi(credible_below)`, and measures each label against how far its contrast
would wander with no real weakness ([`Mastery.null_var`](learny.tracing.estimators.html.md#learny.tracing.estimators.Mastery.null_var)) rather than against its posterior sd,
which a shrunk posterior mean stays well inside (#22). `"bonferroni"` does the same
on the posterior sd: a bound rather than a calibration, far below its target with
little evidence, so it costs power at cold start. `"none"` applies
`credible_below` to each label separately, as the original gate did.

### learny.tracing.model.DEFAULT_NULL_DRAWS *= 200*

How many times `weakest(multiplicity="simulated")` replays a student’s record under
“no label deviation”. The critical value is the `1 - Phi(z)` quantile of the
smallest label statistic over the draws: 200 puts about 32 draws below it at `z=1`.

### learny.tracing.model.DEFAULT_RELATIVE_TO *= 'labels'*

the precision-weighted mean
of the student’s *other* labels, so whatever part of a shortfall every label shares
cancels out. `"global"`: the student’s global skill (zero deviation), as the
original gate did.
With `"labels"` a student with evidence on a single label has nothing to compare it
with, so nothing is credibly weak.

* **Type:**
  What a label’s weakness is measured against. `"labels"`

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

Reads the log only; the estimate cache is neither used nor changed. With an
estimator that reads scores, scored responses are left to
[`score_calibration()`](#learny.tracing.model.LearnerModel.score_calibration), so a log of scores alone gives an empty report here.

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
[`replay()`](#learny.tracing.model.LearnerModel.replay) can rebuild from it. `score` out of `max_score` records an
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

Prequential calibration of the score forecasts; see [`score_calibration()`](#learny.tracing.model.LearnerModel.score_calibration).

Reads the log only. Needs an estimator that reads scores, such as
[`PartialCreditEstimator`](learny.tracing.estimators.html.md#learny.tracing.estimators.PartialCreditEstimator).

* **Return type:**
  [`ScoreCalibrationReport`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.ScoreCalibrationReport)

#### separation(student, , threshold=2.0)

How distinguishable this student’s labels are; see `label_separation()`.

Check `.distinguishable` before acting on an ordering from [`weakest()`](#learny.tracing.model.LearnerModel.weakest).

* **Return type:**
  [`LabelSeparation`](learny.tracing.diagnostics.html.md#learny.tracing.diagnostics.LabelSeparation)

#### weakest(student, n=5, , credible_below=1.0, relative_to='labels', multiplicity='calibrated', null_draws=200)

The labels this student is credibly weakest on — what to practise next.

By default a label is returned only when it is credibly below the student’s
*other* labels: the upper bound `c + z * sd` of its contrast `c` — its
`Mastery.deviation` minus the
precision-weighted mean deviation of every other label with evidence — is below
zero. The survivors are ranked by posterior mean mastery, worst first, and the
first `n` returned.

Three keywords set the gate:

* `credible_below` — the z of the bound (default [`DEFAULT_CREDIBLE_BELOW`](#learny.tracing.model.DEFAULT_CREDIBLE_BELOW),
  ~84% one-sided); larger `z` demands more certainty. With
  `multiplicity="none"`, `z = 0` keeps every label merely below its
  comparator on average. `None` switches the gate off and ranks every
  label with evidence by posterior mean — check [`separation()`](#learny.tracing.model.LearnerModel.separation) before
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
  `"simulated"` replays the student’s own record `null_draws` times with the
  answers redrawn as if no label deviated (`estimator.null_response`), and
  takes as critical value the `1 - Phi(z)` quantile of the most extreme label
  over the draws (a parametric-bootstrap maxT test, Westfall and Young 1993). It
  counts this record’s discreteness, skew, forgetting and the dependence between
  labels exactly, so it keeps the false-flag rate on target where the moment
  corrections of `"calibrated"` are cautious: few answers per label, items the
  student nearly always gets right, or nearly always wrong (#35). It costs
  `null_draws` replays of the record per call, and is deterministic for a given
  student and record; the draws are common random numbers across calls (a new
  answer extends each replay rather than reseeding it), so the cut moves only as
  much as the record does.
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
[`Weakest`](#learny.tracing.model.Weakest)) whose `reason` is `None` when it holds labels, and
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
`deviation` — rather than silently returning nothing. With
`multiplicity="simulated"` it also raises `TypeError` when the estimator has
no `null_response`, and `ValueError` for a `null_draws` that is not a
positive integer or is too few for the false-flag rate `credible_below` sets
(it needs `null_draws >= 1 / alpha - 1`); the other modes ignore `null_draws`.

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
