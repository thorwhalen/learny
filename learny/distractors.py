"""Which wrong options to show beside the right one, from what the learner confuses.

A choice game (pick the match among k) is only as informative as its distractors: random
ones are easy to rule out, while the ones a learner actually mistakes for the target are
what they need to practise telling apart. This module chooses them from two sources,
merged: a **similarity** the caller knows in advance (look-alike glyphs, near-homophones,
similar poses) and the learner's own **confusions**, read from the wrong picks in their
response log (``meta['chosen']``; see :data:`~learny.tracing.records.CHOICE_META_KEYS`).

A similarity is a plain ``{target: {option: weight}}`` mapping, so any source can supply
one. The three steps compose:

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
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from collections.abc import Iterable, Mapping
from random import Random

from learny._sampling import days_since, weighted_sample
from learny.tracing.records import META_CHOSEN, Outcome, Response, credit_of

__all__ = [
    "Similarity",
    "DEFAULT_HALFLIFE_DAYS",
    "DEFAULT_MIN_SHORTFALL",
    "DEFAULT_CONFUSION_BOOST",
    "confusion_weights",
    "merge_similarity",
    "pick_distractors",
]

#: ``{target: {option: weight}}``: how confusable each option is with each target.
Similarity = Mapping[str, Mapping[str, float]]

#: A confusion's weight halves every this many days.
DEFAULT_HALFLIFE_DAYS = 7.0
#: The weight a wrong pick keeps however much partial credit it earned: a near miss is
#: still a confusion worth practising.
DEFAULT_MIN_SHORTFALL = 0.25
#: How much more the learner's own confusions weigh than a similarity known in advance.
DEFAULT_CONFUSION_BOOST = 2.0


def confusion_weights(
    responses: Iterable[Response],
    *,
    halflife_days: float | None = DEFAULT_HALFLIFE_DAYS,
    now: float | None = None,
    symmetric: bool = True,
    min_shortfall: float = DEFAULT_MIN_SHORTFALL,
) -> dict[str, dict[str, float]]:
    """The learner's confusions as a similarity: recent wrong picks weigh most.

    Each wrong response that recorded ``meta['chosen']`` adds to ``[item][chosen]`` a
    weight halved every ``halflife_days`` of age (``None``: no decay; an unknown ``at``
    counts in full), times the share of credit it missed (a near miss with partial
    credit, :func:`~learny.tracing.records.credit_of`, counts less, but never under
    ``min_shortfall``). With ``symmetric=True`` (the
    default) each confusion also counts the other way: if ``tsu`` is taken for ``shi``,
    the two are hard to tell apart whichever is asked. For plain counts, use
    :func:`~learny.tracing.records.confusions`.

    >>> week = 7 * 86_400.0
    >>> log = [Response('ada', 'tsu', 'wrong', at=0.0, meta={'chosen': 'shi'}),
    ...        Response('ada', 'tsu', 'wrong', at=week, meta={'chosen': 'shi'})]
    >>> confusion_weights(log, now=week)
    {'tsu': {'shi': 1.5}, 'shi': {'tsu': 1.5}}
    >>> confusion_weights(log, halflife_days=None, symmetric=False)
    {'tsu': {'shi': 2.0}}
    """
    if now is None and halflife_days is not None:
        now = time.time()
    out: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in responses:
        chosen = r.meta.get(META_CHOSEN)
        if r.outcome is not Outcome.WRONG or chosen is None or chosen == r.item:
            continue
        decay = 1.0
        if halflife_days is not None:
            age = days_since(r.at, now)
            if math.isfinite(age):
                decay = 0.5 ** (age / max(halflife_days, 1e-9))
        w = decay * max(1.0 - credit_of(r), min_shortfall)
        out[r.item][chosen] += w
        if symmetric:
            out[chosen][r.item] += w
    return {k: dict(v) for k, v in out.items()}


def merge_similarity(
    base: Similarity | None, overlay: Similarity | None, *, boost: float = DEFAULT_CONFUSION_BOOST
) -> dict[str, dict[str, float]]:
    """``base`` plus ``boost`` times ``overlay``, target by target.

    Adds rather than replaces, so a target the learner has never confused keeps its
    known look-alikes, and the ones they have confused are weighted up.

    >>> merge_similarity({'a': {'b': 1.0}}, {'a': {'b': 1.0, 'c': 0.5}, 'd': {'a': 1.0}})
    {'a': {'b': 3.0, 'c': 1.0}, 'd': {'a': 2.0}}
    """
    out = {k: dict(v) for k, v in (base or {}).items()}
    for k, row in (overlay or {}).items():
        d = out.setdefault(k, {})
        for j, w in row.items():
            d[j] = d.get(j, 0.0) + boost * w
    return out


def pick_distractors(
    target: str,
    candidates: Iterable[str],
    *,
    n: int,
    similarity: Similarity | None = None,
    rng: Random,
    top_up: bool = True,
) -> list[str]:
    """``n`` options from ``candidates`` other than ``target``, the confusable first.

    Drawn in proportion to ``similarity[target]``; when that runs out (or there is
    none), topped up at random from the remaining candidates so the round still has
    ``n`` distractors whenever there are enough candidates (``top_up=False`` to keep only
    the similar ones).

    >>> pick_distractors('a', ['a', 'b', 'c', 'd'], n=2, similarity={'a': {'d': 1.0}},
    ...                  rng=Random(0))[0]
    'd'
    >>> len(pick_distractors('a', ['a', 'b'], n=3, rng=Random(0)))
    1
    """
    pool = [k for k in dict.fromkeys(candidates) if k != target]
    sims = (similarity or {}).get(target, {})
    weights = [sims.get(k, 0.0) for k in pool]
    similar = [k for k, w in zip(pool, weights) if w > 0]
    chosen = weighted_sample(similar, [w for w in weights if w > 0], n, rng)
    if top_up and len(chosen) < n:
        rest = [k for k in pool if k not in chosen]
        rng.shuffle(rest)
        chosen += rest[: n - len(chosen)]
    return chosen[:n]
