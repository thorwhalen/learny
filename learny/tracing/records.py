"""Core data types for learner modelling: items, outcomes, and responses.

These are the vocabulary every other module in :mod:`learny.tracing` speaks. They are
deliberately small and serialisable: a :class:`Response` is what gets appended to the
append-only log that is the system's single source of truth, so its shape is a
long-lived commitment while everything derived from it is a rebuildable cache.

The three-valued :class:`Outcome` is not an accident. Many assessments distinguish a
wrong answer from an unanswered one — competition scoring often rewards prudent
abstention — so collapsing ``SKIPPED`` into ``WRONG`` destroys signal at the point of
capture, where it can never be recovered. Estimators decide what to do with a skip;
the log records what happened.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

__all__ = ["Outcome", "Item", "Response", "LabelWeights"]

#: Spellings seen in real answer keys, mapped to the canonical three. Extend by passing
#: your own mapping at the adapter boundary rather than editing this.
_OUTCOME_ALIASES = {
    "right": "correct", "ok": "correct", "c": "correct", "true": "correct", "1": "correct",
    "incorrect": "wrong", "false": "wrong", "0": "wrong", "w": "wrong", "x": "wrong",
    "unanswered": "skipped", "blank": "skipped", "skip": "skipped", "omitted": "skipped",
    "none": "skipped", "": "skipped",
}


class Outcome(str, Enum):
    """What happened when a student met an item.

    ``str``-valued so it serialises to JSON as itself, with no encoder needed:

    >>> import json
    >>> json.dumps({"status": Outcome.CORRECT})
    '{"status": "correct"}'
    >>> Outcome("wrong") is Outcome.WRONG
    True
    """

    CORRECT = "correct"
    WRONG = "wrong"
    SKIPPED = "skipped"

    @classmethod
    def _missing_(cls, value: object) -> "Outcome | None":
        """Accept the vocabularies real datasets use, and plain booleans.

        Source data rarely spells these three the same way, and forcing every caller to
        write a mapping is the kind of friction that gets solved with a silent
        ``bool(status == 'correct')`` — which is exactly how a skip becomes a wrong
        answer. Accepting the common spellings here keeps that decision explicit.

        >>> Outcome(True) is Outcome.CORRECT
        True
        >>> Outcome('unanswered') is Outcome.SKIPPED
        True
        >>> Outcome('Blank') is Outcome.SKIPPED
        True
        >>> Outcome('incorrect') is Outcome.WRONG
        True
        >>> Outcome('fnord')
        Traceback (most recent call last):
            ...
        ValueError: 'fnord' is not a valid outcome; expected one of correct, wrong, skipped (or a known alias such as 'unanswered', 'blank', 'incorrect')
        """
        if isinstance(value, bool):
            return cls.CORRECT if value else cls.WRONG
        if isinstance(value, str):
            alias = _OUTCOME_ALIASES.get(value.strip().lower())
            if alias is not None:
                return cls(alias)
        raise ValueError(
            f"{value!r} is not a valid outcome; expected one of "
            f"correct, wrong, skipped (or a known alias such as "
            f"'unanswered', 'blank', 'incorrect')"
        )

    @property
    def is_scored(self) -> bool:
        """Whether this outcome carries evidence about ability.

        A skip is evidence about *confidence or time*, not about whether the student
        could have answered, so estimators are entitled to ignore it.

        >>> [o.is_scored for o in Outcome]
        [True, True, False]
        """
        return self is not Outcome.SKIPPED


#: A mapping from label to the weight that label carries for an item. Weights are
#: usually 1.0 (the label applies) but may be attenuated — by a facet's measured
#: inter-rater reliability, for instance — so that a noisily-assigned label moves a
#: mastery estimate less than a reliably-assigned one.
LabelWeights = Mapping[str, float]


@dataclass(frozen=True)
class Item:
    """A question, with the skill labels it exercises and its observed difficulty.

    ``labels`` is this item's row of the Q-matrix: which knowledge components the item
    draws on. ``difficulty`` is an *externally observed* difficulty on the unit
    interval — the proportion of a reference population expected to get it wrong — and
    is the strongest prior available before a given student has answered anything.
    Leave it ``None`` when nothing observed is available.

    >>> item = Item("2004-q7", labels=("fractions", "area"), difficulty=0.4)
    >>> item.weights
    {'fractions': 1.0, 'area': 1.0}
    >>> Item("q1", labels={"fractions": 0.85, "traps": 0.57}).weights["traps"]
    0.57
    """

    id: str
    labels: Sequence[str] | LabelWeights = ()
    difficulty: float | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.difficulty is not None and not 0.0 <= self.difficulty <= 1.0:
            raise ValueError(
                f"Item {self.id!r}: difficulty must be in [0, 1] "
                f"(the proportion expected to fail it), got {self.difficulty!r}"
            )

    @property
    def weights(self) -> dict[str, float]:
        """Labels as a ``{label: weight}`` mapping, whichever form they were given in."""
        if isinstance(self.labels, Mapping):
            return dict(self.labels)
        return {label: 1.0 for label in self.labels}


@dataclass(frozen=True)
class Response:
    """One student meeting one item, once. The unit of the append-only log.

    ``at`` is a POSIX timestamp. It is kept because order and elapsed time are what any
    later model of forgetting will need, and a log that did not record it cannot be
    replayed into one.

    >>> r = Response("cora", "2004-q7", Outcome.CORRECT, at=1_700_000_000.0)
    >>> r.correct
    True
    >>> Response.from_dict(r.to_dict()) == r
    True
    """

    student: str
    item: str
    outcome: Outcome
    at: float | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Accept a plain string so callers can build from JSON without importing Outcome.
        object.__setattr__(self, "outcome", Outcome(self.outcome))

    @property
    def correct(self) -> bool:
        """True only for an outright correct answer; a skip is not a correct answer."""
        return self.outcome is Outcome.CORRECT

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict. ``Outcome`` is a ``str`` enum, so it needs no encoding."""
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Response":
        """Inverse of :meth:`to_dict`, tolerant of unknown keys from a future version."""
        known = {f for f in ("student", "item", "outcome", "at", "meta")}
        return cls(**{k: v for k, v in d.items() if k in known})
