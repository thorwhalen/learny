"""Time and sampling helpers shared by :mod:`learny.scheduling` and :mod:`learny.distractors`."""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from random import Random
from typing import TypeVar

SECONDS_PER_DAY = 86_400.0

#: The weight a zero or negative weight is raised to, so every item keeps some chance.
_TINY = 1e-9

T = TypeVar("T", bound=Hashable)


def days_since(at: float | None, now: float) -> float:
    """Days from POSIX time ``at`` to ``now``; infinite when ``at`` is unknown.

    >>> days_since(0.0, 2 * SECONDS_PER_DAY), days_since(None, 0.0)
    (2.0, inf)
    """
    return (now - at) / SECONDS_PER_DAY if at is not None else math.inf


def weighted_sample(items: Sequence[T], weights: Sequence[float], k: int, rng: Random) -> list[T]:
    """``k`` distinct items drawn without replacement, each in proportion to its weight.

    A weight of zero or less still has a vanishing chance, so every item can come up
    once the weighted ones are used.

    >>> weighted_sample(['a', 'b', 'c'], [0, 0, 5], 1, Random(0))
    ['c']
    >>> sorted(weighted_sample(['a', 'b', 'c'], [1, 1, 1], 5, Random(0)))
    ['a', 'b', 'c']
    """
    pool, ws = list(items), [max(float(w), _TINY) for w in weights]
    out: list[T] = []
    for _ in range(min(k, len(pool))):
        r, acc = rng.random() * sum(ws), 0.0
        for i, w in enumerate(ws):
            acc += w
            if r <= acc or i == len(ws) - 1:
                out.append(pool.pop(i))
                ws.pop(i)
                break
    return out
