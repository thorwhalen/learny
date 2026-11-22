"""Which item to ask next, and which options to show with it, from the response log.

A :class:`Strategy` turns one learner's responses into the next round of a choice game:
a target item drawn from the candidates, and the options to show with it (the target
plus distractors from :mod:`learny.distractors`). Per-item state (a Leitner box, an SM-2
ease, a memory stability) is rebuilt by replaying the responses, the same way
:mod:`learny.tracing` rebuilds its estimates from the append-only log, so a strategy
holds no state of its own and can be swapped at any time.

Strategies are chosen by key, which is what a settings screen offers:

>>> import random
>>> from learny.tracing import Response
>>> log = [Response('ada', 'tsu', 'wrong', at=0.0, meta={'chosen': 'shi'})]
>>> strategy = make_strategy('confusion_weighted', epsilon_explore=0.0)
>>> round_ = strategy.next_selection(log, ['tsu', 'shi', 'so', 'n'], now=0.0,
...                                  rng=random.Random(1))
>>> round_.target in round_.options, len(round_.options)
(True, 4)

The keys: ``uniform_random`` (the baseline), ``leitner`` (boxes), ``sm2`` (SuperMemo 2,
graded by response time), ``confusion_weighted`` (the default: the items the learner
mixes up, against what they mix them up with), ``fsrs_lite`` (a memory-decay model) and
``weakest`` (items on the labels :meth:`~learny.tracing.LearnerModel.weakest` names).
Spacing intervals are in days; in a single dense sitting little is ever due, so every
scheduler falls back to an urgency ranking rather than stalling.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import MISSING, dataclass, field, fields
from random import Random
from typing import Any, ClassVar

from learny._sampling import days_since, weighted_sample
from learny.distractors import (
    DEFAULT_CONFUSION_BOOST,
    DEFAULT_HALFLIFE_DAYS,
    Similarity,
    confusion_weights,
    merge_similarity,
    pick_distractors,
)
from learny.tracing.records import META_RT_MS, META_TIMED_OUT, Item, Response, credit_of

__all__ = [
    "Selection",
    "Strategy",
    "UniformRandom",
    "Leitner",
    "SM2",
    "ConfusionWeighted",
    "FSRSLite",
    "Weakest",
    "STRATEGIES",
    "DEFAULT_STRATEGY",
    "make_strategy",
    "list_strategies",
]

@dataclass(frozen=True)
class Selection:
    """One round: the target item, and every option to show in display order."""

    target: str
    options: tuple[str, ...]


def _by_item(responses: Iterable[Response]) -> dict[str, list[Response]]:
    """Responses grouped by item, oldest first (an unknown time sorts first)."""
    by: dict[str, list[Response]] = defaultdict(list)
    for r in responses:
        by[r.item].append(r)
    for rs in by.values():
        rs.sort(key=lambda r: -math.inf if r.at is None else r.at)
    return by


# -- the base ------------------------------------------------------------------------


@dataclass
class Strategy:
    """Picks the target, then distractors from what is known to be confusable.

    Subclasses override :meth:`pick_target`. Distractors come from the caller's
    ``similarity``, plus the learner's own recent confusions when
    ``learner_confusions`` is on (the default for the strategies that model confusion;
    off for the baselines, which keep no memory of the learner's mistakes).
    """

    key: ClassVar[str] = "base"
    name: ClassVar[str] = "Base"
    description: ClassVar[str] = ""

    #: Options per round, the target included.
    n_choices: int = 4
    #: Add the learner's own confusions to the distractor similarity.
    learner_confusions: bool = False
    #: A confusion's weight halves every this many days.
    recency_halflife_days: float = DEFAULT_HALFLIFE_DAYS
    #: How much more a learner's confusion weighs than a known similarity.
    confusion_boost: float = DEFAULT_CONFUSION_BOOST

    def pick_target(
        self, responses: Sequence[Response], candidates: Sequence[str], *, now: float, rng: Random
    ) -> str:
        raise NotImplementedError

    def distractor_similarity(
        self, responses: Sequence[Response], *, now: float
    ) -> Similarity | None:
        """The learner's own confusions, recency-weighted, if ``learner_confusions``."""
        if not self.learner_confusions:
            return None
        return confusion_weights(responses, halflife_days=self.recency_halflife_days, now=now) or None

    def next_selection(
        self,
        responses: Iterable[Response],
        candidates: Iterable[str],
        *,
        similarity: Similarity | None = None,
        now: float | None = None,
        rng: Random | None = None,
    ) -> Selection:
        """The next round for the learner whose ``responses`` these are.

        ``candidates`` is the study set (duplicates ignored); ``similarity`` is what the
        caller knows to be confusable, to which the learner's own confusions are added
        (never substituted, so an item not yet confused keeps its look-alikes). ``now``
        is POSIX time, defaulting to the clock.
        """
        responses = list(responses)
        candidates = list(dict.fromkeys(candidates))
        if not candidates:
            raise ValueError("next_selection needs at least one candidate item")
        now = time.time() if now is None else now
        rng = rng if rng is not None else Random()
        target = self.pick_target(responses, candidates, now=now, rng=rng)
        sim = merge_similarity(
            similarity, self.distractor_similarity(responses, now=now), boost=self.confusion_boost
        )
        options = [
            *pick_distractors(target, candidates, n=self.n_choices - 1, similarity=sim, rng=rng),
            target,
        ]
        rng.shuffle(options)
        return Selection(target, tuple(options))


# -- strategies ----------------------------------------------------------------------


@dataclass
class UniformRandom(Strategy):
    key: ClassVar[str] = "uniform_random"
    name: ClassVar[str] = "Uniform random"
    description: ClassVar[str] = "No memory: every item in the set is equally likely. The baseline."

    #: Never ask the item just asked, when there is another.
    anti_repeat: bool = True

    def pick_target(self, responses, candidates, *, now, rng):
        last = responses[-1].item if responses else None
        pool = [k for k in candidates if k != last] if self.anti_repeat else []
        return rng.choice(pool or list(candidates))


@dataclass
class Leitner(Strategy):
    key: ClassVar[str] = "leitner"
    name: ClassVar[str] = "Leitner boxes"
    description: ClassVar[str] = (
        "Spaced repetition by boxes: a right answer moves an item up a box (seen less "
        "often), a wrong answer drops it back."
    )

    n_boxes: int = 5
    #: Days before an item in each box is due again; extended by doubling to ``n_boxes``.
    intervals: tuple[float, ...] = (1, 2, 4, 8, 16)
    #: ``"reset"`` sends a wrong answer to box 1, ``"step"`` down one box.
    demotion: str = "reset"

    def __post_init__(self) -> None:
        if self.demotion not in ("reset", "step"):
            raise ValueError(f"demotion must be 'reset' or 'step', got {self.demotion!r}")
        iv = list(self.intervals) or [1]
        while len(iv) < self.n_boxes:
            iv.append(iv[-1] * 2)
        self.intervals = tuple(iv[: self.n_boxes])

    def boxes(self, responses: Iterable[Response]) -> dict[str, tuple[int, float | None]]:
        """``{item: (box, last answered at)}``, replayed from the responses."""
        out = {}
        for k, rs in _by_item(responses).items():
            b = 1
            for r in rs:
                if r.correct:
                    b = min(b + 1, self.n_boxes)
                elif r.outcome.is_scored:
                    b = 1 if self.demotion == "reset" else max(b - 1, 1)
            out[k] = (b, rs[-1].at)
        return out

    def pick_target(self, responses, candidates, *, now, rng):
        state = self.boxes(responses)
        due, urgency = [], []
        for k in candidates:
            box, last = state.get(k, (1, None))
            if k not in state or days_since(last, now) >= self.intervals[box - 1]:
                due.append(k)
                urgency.append(self.n_boxes - box + 1)  # lower boxes weigh more
        if due:
            return weighted_sample(due, urgency, 1, rng)[0]
        # nothing due in this sitting: review the least-learned box
        floor = min(state[k][0] for k in candidates)
        return rng.choice([k for k in candidates if state[k][0] == floor])


@dataclass
class SM2(Strategy):
    key: ClassVar[str] = "sm2"
    name: ClassVar[str] = "SuperMemo SM-2"
    description: ClassVar[str] = (
        "Classic spaced repetition: each item gets its own ease; right answers stretch "
        "the interval, mistakes reset it."
    )

    ef_start: float = 2.5
    ef_min: float = 1.3
    #: Days to the first and second review after a pass.
    i1: float = 1
    i2: float = 6
    #: A right answer at most this fast (``meta['rt_ms']``) grades 5, at least this slow 3.
    fast_ms: float = 3500
    slow_ms: float = 9000
    #: Weight the least overdue item keeps when drawing by overdueness.
    overdue_floor: float = 0.1

    def grade(self, r: Response) -> int:
        """SM-2's 0-5 quality for one response.

        Right: 5 if fast, 3 if slow or timed out (``meta['timed_out']``), else 4. Wrong:
        2 for a near miss that earned partial credit (``meta['credit']`` or a score), 1
        otherwise, 0 if timed out.
        """
        if r.meta.get(META_TIMED_OUT):
            return 3 if r.correct else 0
        rt = r.meta.get(META_RT_MS)
        if r.correct:
            if rt is not None and rt <= self.fast_ms:
                return 5
            if rt is not None and rt >= self.slow_ms:
                return 3
            return 4
        return 2 if credit_of(r) > 0 else 1

    def state(self, responses: Iterable[Response]) -> dict[str, dict[str, Any]]:
        """``{item: {'ef', 'n', 'interval', 'last'}}``, replayed from the responses."""
        out = {}
        for k, rs in _by_item(responses).items():
            ef, n, interval = self.ef_start, 0, 0.0
            for r in rs:
                if not r.outcome.is_scored:
                    continue
                q = self.grade(r)
                ef = max(self.ef_min, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
                if q >= 3:
                    interval = self.i1 if n == 0 else self.i2 if n == 1 else round(interval * ef)
                    n += 1
                else:
                    n, interval = 0, self.i1
            out[k] = {"ef": ef, "n": n, "interval": interval, "last": rs[-1].at}
        return out

    def pick_target(self, responses, candidates, *, now, rng):
        st = self.state(responses)
        unseen = [k for k in candidates if k not in st]
        if unseen:
            return rng.choice(unseen)
        # weighted by how overdue, not the most overdue, so a dense sitting interleaves
        overdue = {k: days_since(st[k]["last"], now) - st[k]["interval"] for k in candidates}
        lo = min(overdue.values())
        if not math.isfinite(lo):
            return rng.choice(list(candidates))
        return weighted_sample(candidates, [overdue[k] - lo + self.overdue_floor for k in candidates], 1, rng)[0]


@dataclass
class ConfusionWeighted(Strategy):
    key: ClassVar[str] = "confusion_weighted"
    name: ClassVar[str] = "Confusion-weighted"
    description: ClassVar[str] = (
        "Focuses on the items you actually mix up, and pits them against the very items "
        "you confuse them with. Recommended."
    )

    learner_confusions: bool = True
    #: Chance of a uniformly random target, so nothing is never asked.
    epsilon_explore: float = 0.1
    #: Extra weight of an item never asked, against its confusion weight.
    prior: float = 1.0
    #: Weight every candidate keeps.
    floor: float = 0.05

    def pick_target(self, responses, candidates, *, now, rng):
        if not responses or rng.random() < self.epsilon_explore:
            return rng.choice(list(candidates))
        conf = confusion_weights(
            responses, halflife_days=self.recency_halflife_days, now=now, symmetric=False
        )
        seen = {r.item for r in responses}
        weights = [
            sum(conf.get(k, {}).values()) + (self.prior if k not in seen else 0.0) + self.floor
            for k in candidates
        ]
        return weighted_sample(candidates, weights, 1, rng)[0]


@dataclass
class FSRSLite(Strategy):
    key: ClassVar[str] = "fsrs_lite"
    name: ClassVar[str] = "FSRS-lite (memory model)"
    description: ClassVar[str] = (
        "Models how memory of each item decays and asks it again just before you would "
        "forget it."
    )

    learner_confusions: bool = True
    #: Stability in days of a new item; multiplied by ``stability_growth`` on each right
    #: answer, by ``lapse_factor`` on each wrong one, down to ``lapse_floor``.
    s_init: float = 1.0
    stability_growth: float = 2.0
    lapse_factor: float = 0.5
    lapse_floor: float = 0.5
    floor: float = 0.05

    def stability(self, responses: Iterable[Response]) -> dict[str, tuple[float, float | None]]:
        """``{item: (stability in days, last answered at)}``, replayed."""
        out = {}
        for k, rs in _by_item(responses).items():
            s = self.s_init
            for r in rs:
                if r.correct:
                    s *= self.stability_growth
                elif r.outcome.is_scored:
                    s = max(self.lapse_floor, s * self.lapse_factor)
            out[k] = (s, rs[-1].at)
        return out

    def recall(self, item: str, state: Mapping[str, tuple[float, float | None]], now: float) -> float:
        """Probability the learner still recalls ``item`` now (0 if never seen)."""
        if item not in state:
            return 0.0
        s, last = state[item]
        return math.exp(-days_since(last, now) / max(s, 1e-9))

    def pick_target(self, responses, candidates, *, now, rng):
        st = self.stability(responses)
        unseen = [k for k in candidates if k not in st]
        if unseen:
            return rng.choice(unseen)
        # weighted by forgetting, not the most forgotten, so a dense sitting interleaves
        weights = [1.0 - self.recall(k, st, now) + self.floor for k in candidates]
        return weighted_sample(candidates, weights, 1, rng)[0]


@dataclass
class Weakest(Strategy):
    """Items on the labels the learner model says are weakest; else the least likely right.

    Replays the responses into a :class:`~learny.tracing.LearnerModel` over ``items``
    (whose labels say what each item exercises) and asks it for the weakest labels.
    Candidates carrying those labels are drawn in proportion to their weight on them;
    when no label is credibly weakest, in proportion to the chance of a wrong answer.
    """

    key: ClassVar[str] = "weakest"
    name: ClassVar[str] = "Weakest skills"
    description: ClassVar[str] = (
        "Asks about the skills the learner model is confident you are weakest on, and "
        "otherwise what you are least likely to get right."
    )

    learner_confusions: bool = True
    #: The item bank: labels and difficulties. An item missing here has no labels.
    items: Mapping[str, Item] = field(default_factory=dict)
    #: Builds the estimator; ``None`` for the default (:class:`~learny.tracing.RaschEstimator`).
    estimator: Callable[[], Any] | None = None
    #: How many weakest labels to draw from.
    n_labels: int = 3
    #: Passed on to :meth:`~learny.tracing.LearnerModel.weakest` (``credible_below``...).
    weakest_options: Mapping[str, Any] = field(default_factory=dict)
    floor: float = 0.05

    def pick_target(self, responses, candidates, *, now, rng):
        from learny.tracing import LearnerModel  # the model is only needed here

        if not responses:
            return rng.choice(list(candidates))
        model = LearnerModel(
            items=self.items,
            estimator=self.estimator() if self.estimator else None,
            log={},
            estimates={},
        )
        model.record_many(responses)
        student = responses[-1].student
        weak = {m.label for m in model.weakest(student, self.n_labels, **self.weakest_options)}
        bank = {k: self.items.get(k, Item(k)) for k in candidates}
        on_weak = [sum(w for lb, w in bank[k].weights.items() if lb in weak) for k in candidates]
        if any(on_weak):
            return weighted_sample(candidates, on_weak, 1, rng)[0]
        misses = [1.0 - model.predict(student, bank[k]) + self.floor for k in candidates]
        return weighted_sample(candidates, misses, 1, rng)[0]


# -- the registry --------------------------------------------------------------------

STRATEGIES: dict[str, type[Strategy]] = {
    c.key: c for c in (UniformRandom, Leitner, SM2, ConfusionWeighted, FSRSLite, Weakest)
}
DEFAULT_STRATEGY = ConfusionWeighted.key


def make_strategy(key: str | None = None, **params: Any) -> Strategy:
    """The strategy registered under ``key`` (default :data:`DEFAULT_STRATEGY`).

    Parameters the strategy does not have are ignored, so one settings mapping can serve
    every strategy; an unknown key is an error.

    >>> make_strategy('leitner', n_boxes=3, epsilon_explore=0.2).intervals
    (1, 2, 4)
    >>> make_strategy('nope')
    Traceback (most recent call last):
        ...
    ValueError: no strategy 'nope'; known: uniform_random, leitner, sm2, confusion_weighted, fsrs_lite, weakest
    """
    key = key or DEFAULT_STRATEGY
    if key not in STRATEGIES:
        raise ValueError(f"no strategy {key!r}; known: {', '.join(STRATEGIES)}")
    cls = STRATEGIES[key]
    valid = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in params.items() if k in valid})


def list_strategies() -> list[dict[str, Any]]:
    """Each strategy's key, name, description, whether it is the default, and its
    parameters (name, type, default) for a settings screen.

    >>> [p['name'] for p in list_strategies()[0]['params']][:2]
    ['n_choices', 'learner_confusions']
    """

    def params(cls: type[Strategy]) -> list[dict[str, Any]]:
        out = []
        for f in fields(cls):
            if f.default is not MISSING and isinstance(f.default, (bool, int, float, str, tuple)):
                default = list(f.default) if isinstance(f.default, tuple) else f.default
                out.append({"name": f.name, "type": type(f.default).__name__, "default": default})
        return out

    return [
        {
            "key": k,
            "name": c.name,
            "description": c.description,
            "is_default": k == DEFAULT_STRATEGY,
            "params": params(c),
        }
        for k, c in STRATEGIES.items()
    ]
