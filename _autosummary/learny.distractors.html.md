# learny.distractors

Which wrong options to show beside the right one, from what the learner confuses.

A choice game (pick the match among k) is only as informative as its distractors: random
ones are easy to rule out, while the ones a learner actually mistakes for the target are
what they need to practise telling apart. This module chooses them from two sources,
merged: a **similarity** the caller knows in advance (look-alike glyphs, near-homophones,
similar poses) and the learner’s own **confusions**, read from the wrong picks in their
response log (`meta['chosen']`; see [`CHOICE_META_KEYS`](learny.tracing.records.html.md#learny.tracing.records.CHOICE_META_KEYS)).

A similarity is a plain `{target: {option: weight}}` mapping, so any source can supply
one. The three steps compose:

```pycon
>>> import random
>>> from learny.tracing import Response
>>> log = [Response('ada', 'tsu', 'wrong', at=0.0, meta={'chosen': 'shi'})]
>>> looks_alike = {'tsu': {'so': 1.0}}
>>> sim = merge_similarity(looks_alike, confusion_weights(log, now=0.0))
>>> sorted(sim['tsu'])
['shi', 'so']
>>> sorted(pick_distractors('tsu', ['tsu', 'shi', 'so', 'n', 'ka'], n=2, similarity=sim,
...                         rng=random.Random(0)))
['shi', 'so']
```

### Module Attributes

| [`Similarity`](#learny.distractors.Similarity)              | how confusable each option is with each target.                                      |
|--------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`DEFAULT_HALFLIFE_DAYS`](#learny.distractors.DEFAULT_HALFLIFE_DAYS)   | A confusion's weight halves every this many days.                                    |
| [`DEFAULT_MIN_SHORTFALL`](#learny.distractors.DEFAULT_MIN_SHORTFALL)   | a near miss is still a confusion worth practising.                                   |
| [`DEFAULT_CONFUSION_BOOST`](#learny.distractors.DEFAULT_CONFUSION_BOOST) | How much more the learner's own confusions weigh than a similarity known in advance. |

### Functions

| [`confusion_weights`](#learny.distractors.confusion_weights)(responses, \*[, ...])            | The learner's confusions as a similarity: recent wrong picks weigh most.   |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`merge_similarity`](#learny.distractors.merge_similarity)(base, overlay, \*[, boost])       | `base` plus `boost` times `overlay`, target by target.                     |
| [`pick_distractors`](#learny.distractors.pick_distractors)(target, candidates, \*, n[, ...]) | `n` options from `candidates` other than `target`, the confusable first.   |

### learny.distractors.DEFAULT_CONFUSION_BOOST *= 2.0*

How much more the learner’s own confusions weigh than a similarity known in advance.

### learny.distractors.DEFAULT_HALFLIFE_DAYS *= 7.0*

A confusion’s weight halves every this many days.

### learny.distractors.DEFAULT_MIN_SHORTFALL *= 0.25*

a near miss is
still a confusion worth practising.

* **Type:**
  The weight a wrong pick keeps however much partial credit it earned

### learny.distractors.Similarity

how confusable each option is with each target.

* **Type:**
  `{target: {option: weight}}`

alias of [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

### learny.distractors.confusion_weights(responses, , halflife_days=7.0, now=None, symmetric=True, min_shortfall=0.25)

The learner’s confusions as a similarity: recent wrong picks weigh most.

Each wrong response that recorded `meta['chosen']` adds to `[item][chosen]` a
weight halved every `halflife_days` of age (`None`: no decay; an unknown `at`
counts in full), times the share of credit it missed (a near miss with partial
credit, [`credit_of()`](learny.tracing.records.html.md#learny.tracing.records.credit_of), counts less, but never under
`min_shortfall`). With `symmetric=True` (the
default) each confusion also counts the other way: if `tsu` is taken for `shi`,
the two are hard to tell apart whichever is asked. For plain counts, use
[`confusions()`](learny.tracing.records.html.md#learny.tracing.records.confusions).

```pycon
>>> week = 7 * 86_400.0
>>> log = [Response('ada', 'tsu', 'wrong', at=0.0, meta={'chosen': 'shi'}),
...        Response('ada', 'tsu', 'wrong', at=week, meta={'chosen': 'shi'})]
>>> confusion_weights(log, now=week)
{'tsu': {'shi': 1.5}, 'shi': {'tsu': 1.5}}
>>> confusion_weights(log, halflife_days=None, symmetric=False)
{'tsu': {'shi': 2.0}}
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

### learny.distractors.merge_similarity(base, overlay, , boost=2.0)

`base` plus `boost` times `overlay`, target by target.

Adds rather than replaces, so a target the learner has never confused keeps its
known look-alikes, and the ones they have confused are weighted up.

```pycon
>>> merge_similarity({'a': {'b': 1.0}}, {'a': {'b': 1.0, 'c': 0.5}, 'd': {'a': 1.0}})
{'a': {'b': 3.0, 'c': 1.0}, 'd': {'a': 2.0}}
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

### learny.distractors.pick_distractors(target, candidates, , n, similarity=None, rng, top_up=True)

`n` options from `candidates` other than `target`, the confusable first.

Drawn in proportion to `similarity[target]`; when that runs out (or there is
none), topped up at random from the remaining candidates so the round still has
`n` distractors whenever there are enough candidates (`top_up=False` to keep only
the similar ones).

```pycon
>>> pick_distractors('a', ['a', 'b', 'c', 'd'], n=2, similarity={'a': {'d': 1.0}},
...                  rng=Random(0))[0]
'd'
>>> len(pick_distractors('a', ['a', 'b'], n=3, rng=Random(0)))
1
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
