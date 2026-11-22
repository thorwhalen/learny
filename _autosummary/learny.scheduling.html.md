# learny.scheduling

Which item to ask next, and which options to show with it, from the response log.

A [`Strategy`](#learny.scheduling.Strategy) turns one learner’s responses into the next round of a choice game:
a target item drawn from the candidates, and the options to show with it (the target
plus distractors from [`learny.distractors`](learny.distractors.html.md#module-learny.distractors)). Per-item state (a Leitner box, an SM-2
ease, a memory stability) is rebuilt by replaying the responses, the same way
[`learny.tracing`](learny.tracing.html.md#module-learny.tracing) rebuilds its estimates from the append-only log, so a strategy
holds no state of its own and can be swapped at any time.

Strategies are chosen by key, which is what a settings screen offers:

```pycon
>>> import random
>>> from learny.tracing import Response
>>> log = [Response('ada', 'tsu', 'wrong', at=0.0, meta={'chosen': 'shi'})]
>>> strategy = make_strategy('confusion_weighted', epsilon_explore=0.0)
>>> round_ = strategy.next_selection(log, ['tsu', 'shi', 'so', 'n'], now=0.0,
...                                  rng=random.Random(1))
>>> round_.target in round_.options, len(round_.options)
(True, 4)
```

The keys: `uniform_random` (the baseline), `leitner` (boxes), `sm2` (SuperMemo 2,
graded by response time), `confusion_weighted` (the default: the items the learner
mixes up, against what they mix them up with), `fsrs_lite` (a memory-decay model) and
`weakest` (items on the labels [`weakest()`](learny.tracing.html.md#learny.tracing.LearnerModel.weakest) names).
Spacing intervals are in days; in a single dense sitting little is ever due, so every
scheduler falls back to an urgency ranking rather than stalling.

### Functions

| [`make_strategy`](#learny.scheduling.make_strategy)([key])   | The strategy registered under `key` (default `DEFAULT_STRATEGY`).                                                                  |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| [`list_strategies`](#learny.scheduling.list_strategies)()      | Each strategy's key, name, description, whether it is the default, and its parameters (name, type, default) for a settings screen. |

### Classes

| [`Selection`](#learny.scheduling.Selection)(target, options)                     | One round: the target item, and every option to show in display order.               |
|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`Strategy`](#learny.scheduling.Strategy)([n_choices, learner_confusions, ...]) | Picks the target, then distractors from what is known to be confusable.              |
| [`UniformRandom`](#learny.scheduling.UniformRandom)([n_choices, ...])                |                                                                                      |
| [`Leitner`](#learny.scheduling.Leitner)([n_choices, learner_confusions, ...])  |                                                                                      |
| [`SM2`](#learny.scheduling.SM2)([n_choices, learner_confusions, ...])      |                                                                                      |
| [`ConfusionWeighted`](#learny.scheduling.ConfusionWeighted)([n_choices, ...])            |                                                                                      |
| [`FSRSLite`](#learny.scheduling.FSRSLite)([n_choices, learner_confusions, ...]) |                                                                                      |
| [`Weakest`](#learny.scheduling.Weakest)([n_choices, learner_confusions, ...])  | Items on the labels the learner model says are weakest; else the least likely right. |

### *class* learny.scheduling.ConfusionWeighted(n_choices=4, learner_confusions=True, recency_halflife_days=7.0, confusion_boost=2.0, epsilon_explore=0.1, prior=1.0, floor=0.05)

Bases: [`Strategy`](#learny.scheduling.Strategy)

#### epsilon_explore *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.1*

Chance of a uniformly random target, so nothing is never asked.

#### floor *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.05*

Weight every candidate keeps.

#### learner_confusions *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= True*

Add the learner’s own confusions to the distractor similarity.

#### prior *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 1.0*

Extra weight of an item never asked, against its confusion weight.

### *class* learny.scheduling.FSRSLite(n_choices=4, learner_confusions=True, recency_halflife_days=7.0, confusion_boost=2.0, s_init=1.0, stability_growth=2.0, lapse_factor=0.5, lapse_floor=0.5, floor=0.05)

Bases: [`Strategy`](#learny.scheduling.Strategy)

#### learner_confusions *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= True*

Add the learner’s own confusions to the distractor similarity.

#### recall(item, state, now)

Probability the learner still recalls `item` now (0 if never seen).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### s_init *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 1.0*

Stability in days of a new item; multiplied by `stability_growth` on each right
answer, by `lapse_factor` on each wrong one, down to `lapse_floor`.

#### stability(responses)

`{item: (stability in days, last answered at)}`, replayed.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]]

### *class* learny.scheduling.Leitner(n_choices=4, learner_confusions=False, recency_halflife_days=7.0, confusion_boost=2.0, n_boxes=5, intervals=(1, 2, 4, 8, 16), demotion='reset')

Bases: [`Strategy`](#learny.scheduling.Strategy)

#### boxes(responses)

`{item: (box, last answered at)}`, replayed from the responses.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]]

#### demotion *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)* *= 'reset'*

`"reset"` sends a wrong answer to box 1, `"step"` down one box.

#### intervals *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[float](https://docs.python.org/3/builtins/functions.html#float), ...]* *= (1, 2, 4, 8, 16)*

Days before an item in each box is due again; extended by doubling to `n_boxes`.

### *class* learny.scheduling.SM2(n_choices=4, learner_confusions=False, recency_halflife_days=7.0, confusion_boost=2.0, ef_start=2.5, ef_min=1.3, i1=1, i2=6, fast_ms=3500, slow_ms=9000, overdue_floor=0.1)

Bases: [`Strategy`](#learny.scheduling.Strategy)

#### fast_ms *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 3500*

A right answer at most this fast (`meta['rt_ms']`) grades 5, at least this slow 3.

#### grade(r)

SM-2’s 0-5 quality for one response.

Right: 5 if fast, 3 if slow or timed out (`meta['timed_out']`), else 4. Wrong:
2 for a near miss that earned partial credit (`meta['credit']` or a score), 1
otherwise, 0 if timed out.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

#### i1 *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 1*

Days to the first and second review after a pass.

#### overdue_floor *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 0.1*

Weight the least overdue item keeps when drawing by overdueness.

#### state(responses)

`{item: {'ef', 'n', 'interval', 'last'}}`, replayed from the responses.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### *class* learny.scheduling.Selection(target, options)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One round: the target item, and every option to show in display order.

### *class* learny.scheduling.Strategy(n_choices=4, learner_confusions=False, recency_halflife_days=7.0, confusion_boost=2.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Picks the target, then distractors from what is known to be confusable.

Subclasses override `pick_target()`. Distractors come from the caller’s
`similarity`, plus the learner’s own recent confusions when
`learner_confusions` is on (the default for the strategies that model confusion;
off for the baselines, which keep no memory of the learner’s mistakes).

#### confusion_boost *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 2.0*

How much more a learner’s confusion weighs than a known similarity.

#### distractor_similarity(responses, , now)

The learner’s own confusions, recency-weighted, if `learner_confusions`.

* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### learner_confusions *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= False*

Add the learner’s own confusions to the distractor similarity.

#### n_choices *: [int](https://docs.python.org/3/builtins/functions.html#int)* *= 4*

Options per round, the target included.

#### next_selection(responses, candidates, , similarity=None, now=None, rng=None)

The next round for the learner whose `responses` these are.

`candidates` is the study set (duplicates ignored); `similarity` is what the
caller knows to be confusable, to which the learner’s own confusions are added
(never substituted, so an item not yet confused keeps its look-alikes). `now`
is POSIX time, defaulting to the clock.

* **Return type:**
  [`Selection`](#learny.scheduling.Selection)

#### recency_halflife_days *: [float](https://docs.python.org/3/builtins/functions.html#float)* *= 7.0*

A confusion’s weight halves every this many days.

### *class* learny.scheduling.UniformRandom(n_choices=4, learner_confusions=False, recency_halflife_days=7.0, confusion_boost=2.0, anti_repeat=True)

Bases: [`Strategy`](#learny.scheduling.Strategy)

#### anti_repeat *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= True*

Never ask the item just asked, when there is another.

### *class* learny.scheduling.Weakest(n_choices=4, learner_confusions=True, recency_halflife_days=7.0, confusion_boost=2.0, items=dict(), estimator=None, n_labels=3, weakest_options=dict(), floor=0.05)

Bases: [`Strategy`](#learny.scheduling.Strategy)

Items on the labels the learner model says are weakest; else the least likely right.

Replays the responses into a [`LearnerModel`](learny.tracing.html.md#learny.tracing.LearnerModel) over `items`
(whose labels say what each item exercises) and asks it for the weakest labels.
Candidates carrying those labels are drawn in proportion to their weight on them;
when no label is credibly weakest, in proportion to the chance of a wrong answer.

#### estimator *: [Callable](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[], [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

Builds the estimator; `None` for the default ([`RaschEstimator`](learny.tracing.html.md#learny.tracing.RaschEstimator)).

#### items *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Item](learny.tracing.records.html.md#learny.tracing.records.Item)]*

labels and difficulties. An item missing here has no labels.

* **Type:**
  The item bank

#### learner_confusions *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= True*

Add the learner’s own confusions to the distractor similarity.

#### n_labels *: [int](https://docs.python.org/3/builtins/functions.html#int)* *= 3*

How many weakest labels to draw from.

#### weakest_options *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]*

Passed on to [`weakest()`](learny.tracing.html.md#learny.tracing.LearnerModel.weakest) (`credible_below`…).

### learny.scheduling.list_strategies()

Each strategy’s key, name, description, whether it is the default, and its
parameters (name, type, default) for a settings screen.

```pycon
>>> [p['name'] for p in list_strategies()[0]['params']][:2]
['n_choices', 'learner_confusions']
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### learny.scheduling.make_strategy(key=None, \*\*params)

The strategy registered under `key` (default `DEFAULT_STRATEGY`).

Parameters the strategy does not have are ignored, so one settings mapping can serve
every strategy; an unknown key is an error.

```pycon
>>> make_strategy('leitner', n_boxes=3, epsilon_explore=0.2).intervals
(1, 2, 4)
>>> make_strategy('nope')
Traceback (most recent call last):
    ...
ValueError: no strategy 'nope'; known: uniform_random, leitner, sm2, confusion_weighted, fsrs_lite, weakest
```

* **Return type:**
  [`Strategy`](#learny.scheduling.Strategy)
