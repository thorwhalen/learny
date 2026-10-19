# learny.tracing.records

Core data types for learner modelling: items, outcomes, and responses.

These are the vocabulary every other module in [`learny.tracing`](learny.tracing.html.md#module-learny.tracing) speaks. They are
deliberately small and serialisable: a [`Response`](#learny.tracing.records.Response) is what gets appended to the
append-only log that is the system’s single source of truth, so its shape is a
long-lived commitment while everything derived from it is a rebuildable cache.

The three-valued [`Outcome`](#learny.tracing.records.Outcome) is not an accident. Many assessments distinguish a
wrong answer from an unanswered one — competition scoring often rewards prudent
abstention — so collapsing `SKIPPED` into `WRONG` destroys signal at the point of
capture, where it can never be recovered. Estimators decide what to do with a skip;
the log records what happened.

### Module Attributes

| [`LabelWeights`](#learny.tracing.records.LabelWeights)   | A mapping from label to the weight that label carries for an item.   |
|-----------------------------------------------------------------|----------------------------------------------------------------------|

### Functions

| [`restrict_labels`](#learny.tracing.records.restrict_labels)(items, \*, keep[, ...])   | Project an item bank onto a subset of its labels — one facet, say.   |
|--------------------------------------------------------------------------------------------|----------------------------------------------------------------------|

### Classes

| [`Outcome`](#learny.tracing.records.Outcome)(\*values)                                 | What happened when a student met an item.                                   |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`Item`](#learny.tracing.records.Item)(id[, labels, difficulty, meta])              | A question, with the skill labels it exercises and its observed difficulty. |
| [`Response`](#learny.tracing.records.Response)(student, item, outcome[, at, meta, ...]) | One student meeting one item, once.                                         |

### *class* learny.tracing.records.Item(id, labels=(), difficulty=None, meta=dict())

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

### learny.tracing.records.LabelWeights

A mapping from label to the weight that label carries for an item. Weights are
usually 1.0 (the label applies) but may be attenuated — by a facet’s measured
inter-rater reliability, for instance — so that a noisily-assigned label moves a
mastery estimate less than a reliably-assigned one.

alias of [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### *class* learny.tracing.records.Outcome(\*values)

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

### *class* learny.tracing.records.Response(student, item, outcome, at=None, meta=dict(), , score=None, max_score=None)

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

Inverse of [`to_dict()`](#learny.tracing.records.Response.to_dict), tolerant of unknown keys from a future version.

* **Return type:**
  [`Response`](#learny.tracing.records.Response)

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

### learny.tracing.records.restrict_labels(items, , keep, drop_unlabelled=False)

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
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Item`](#learny.tracing.records.Item)]
