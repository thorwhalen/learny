"""Core data types for learner modelling: items, outcomes, and responses.

Also the names of what a choice game records in a response's ``meta``
(:data:`CHOICE_META_KEYS`), with :func:`guess_of` and :func:`confusions` to read them.

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

from collections import Counter
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, asdict, replace
from enum import Enum
from numbers import Integral, Real
from typing import Any

__all__ = [
    "Outcome",
    "Item",
    "Response",
    "LabelWeights",
    "restrict_labels",
    "CHOICE_META_KEYS",
    "GUESS_IS_ONE_OVER_K",
    "META_SHOWN",
    "META_CHOSEN",
    "META_RT_MS",
    "META_PROMPT",
    "META_ANSWER",
    "META_PATTERN",
    "META_GUESS",
    "META_SPEC",
    "META_SESSION",
    "META_NOT_REACHED",
    "guess_of",
    "confusions",
]

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

    **An ordered score** — 1 to 5 stars, partial credit — goes in ``score`` out of
    ``max_score``, on the consecutive levels ``0..max_score``: map 1–5 stars to
    ``score=stars - 1, max_score=4``, and three ordered levels such as 1/3/5 stars to
    ``0, 1, 2`` of ``2`` (a level that can never occur is not a level). ``outcome`` stays
    the dichotomous view of the same attempt, so an estimator that only reads outcomes
    (the default) is unaffected, and one that reads scores
    (:class:`~learny.tracing.estimators.PartialCreditEstimator`) can replay the same log.
    One response carries one score: an attempt scored on several sub-scales is several
    responses, one per sub-scale.

    >>> r = Response("cora", "song-7/tempo", "correct", score=3, max_score=4)
    >>> r.to_dict()['score'], Response.from_dict(r.to_dict()) == r
    (3, True)
    >>> 'score' in Response("cora", "2004-q7", "correct").to_dict()  # unscored: as before
    False
    >>> Response("cora", "q", "skipped", score=0, max_score=4)
    Traceback (most recent call last):
        ...
    ValueError: Response 'q': a skipped response has no score (got score=0)

    **A choice game** (the learner picks among options shown) writes its facts into
    ``meta`` under the names in :data:`CHOICE_META_KEYS`: ``shown`` (option ids in display
    order), ``chosen`` (the pick), ``rt_ms`` (response time), ``prompt`` and ``answer``
    (the sides shown and asked for), ``pattern`` (``'M1'``...), ``guess``, ``spec`` and
    ``session``. :func:`guess_of` reads the guess rate from them and :func:`confusions`
    the wrong picks. Other keys are allowed and kept as they are.

    >>> r = Response("ada", "ni", "wrong", meta={"shown": ["ni", "wo", "ta"], "chosen": "wo",
    ...              "rt_ms": 1840, "pattern": "M1"})
    >>> guess_of(r), Response.from_dict(r.to_dict()) == r
    (0.3333333333333333, True)
    """

    student: str
    item: str
    outcome: Outcome
    at: float | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)
    #: The ordered score, in ``0..max_score``; ``None`` for a right/wrong response.
    score: int | None = field(default=None, kw_only=True)
    #: The highest score this attempt could have earned; set exactly when ``score`` is.
    max_score: int | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        # Accept a plain string so callers can build from JSON without importing Outcome.
        object.__setattr__(self, "outcome", Outcome(self.outcome))
        if self.score is None and self.max_score is None:
            return
        if self.score is None or self.max_score is None:
            raise ValueError(
                f"Response {self.item!r}: score and max_score go together, got "
                f"score={self.score!r}, max_score={self.max_score!r}"
            )
        if not self.outcome.is_scored:
            raise ValueError(
                f"Response {self.item!r}: a skipped response has no score "
                f"(got score={self.score!r})"
            )
        for name in ("score", "max_score"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise TypeError(f"Response {self.item!r}: {name} must be an int, got {value!r}")
            object.__setattr__(self, name, int(value))  # a numpy int serialises as int
        if not 0 <= self.score <= self.max_score or self.max_score < 1:
            raise ValueError(
                f"Response {self.item!r}: need 0 <= score <= max_score and max_score >= 1, "
                f"got score={self.score!r}, max_score={self.max_score!r}"
            )

    @property
    def correct(self) -> bool:
        """True only for an outright correct answer; a skip is not a correct answer."""
        return self.outcome is Outcome.CORRECT

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict. ``Outcome`` is a ``str`` enum, so it needs no encoding.

        An unscored response leaves ``score`` and ``max_score`` out, so a right/wrong log
        is written exactly as it was before scores existed.
        """
        d = asdict(self)
        d["outcome"] = self.outcome.value
        if self.score is None:
            del d["score"], d["max_score"]
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Response":
        """Inverse of :meth:`to_dict`, tolerant of unknown keys from a future version."""
        known = {"student", "item", "outcome", "at", "meta", "score", "max_score"}
        return cls(**{k: v for k, v in d.items() if k in known})


# -- what a choice game writes into Response.meta ---------------------------------
#
# A game where the learner picks among options shown (pick-the-match and its kin, see
# ``docs/research/learning-game-patterns.md`` section 5) records the same facts whatever
# its UI: the options, the pick, the time taken, the guess rate. These names are the
# contract, shared with the TypeScript side; ``meta`` stays open to any other key.

#: Option ids in display order, the correct one included. An option id is the id of the
#: item it shows, so a wrong pick names the item it was mistaken for.
META_SHOWN = "shown"
#: The option id the learner picked; absent on a skip.
META_CHOSEN = "chosen"
#: Response time, in milliseconds.
META_RT_MS = "rt_ms"
#: The side(s) of the item shown as the prompt (``'fr.text'``, ``['zh.hanzi']``...).
META_PROMPT = "prompt"
#: The side(s) the options were shown in, i.e. what was asked for.
META_ANSWER = "answer"
#: The pattern id: ``'M1'`` (pick the match among k), ``'M2'``, ``'P1'``...
META_PATTERN = "pattern"
#: The probability of a correct answer by chance, when the game knows it.
META_GUESS = "guess"
#: The game settings this response was played under (an id, or the spec itself).
META_SPEC = "spec"
#: The id of the sitting this response belongs to.
META_SESSION = "session"

#: Set by :func:`~learny.tracing.estimators.mark_not_reached` on a blank the clock ran
#: out before: not evidence about the student. Any game may write it, not only choice games.
META_NOT_REACHED = "not_reached"

#: Every meta key a choice game writes, in the order above.
CHOICE_META_KEYS = (
    META_SHOWN,
    META_CHOSEN,
    META_RT_MS,
    META_PROMPT,
    META_ANSWER,
    META_PATTERN,
    META_GUESS,
    META_SPEC,
    META_SESSION,
)

#: Patterns whose chance rate is one over the number of options shown: one correct
#: option among k (M1), one correct target among k (M4).
GUESS_IS_ONE_OVER_K = frozenset({"M1", "M4"})


def guess_of(
    response: Response | Mapping[str, Any], *, default: float | None = None
) -> float | None:
    """The chance of answering ``response``'s item right by guessing, from its meta.

    An explicit ``meta['guess']`` wins. Otherwise, for a pattern in
    :data:`GUESS_IS_ONE_OVER_K`, it is one over the number of options shown. Otherwise
    ``default``, which is where a model-wide ``guess=`` comes in. The guess rate is a
    property of the game that produced the response, so a log mixing 2-option and
    4-option rounds carries the right rate on each one. ``response`` may also be just a
    ``meta`` mapping, to get the rate of a round before it is played.

    >>> guess_of(Response('ada', 'ni', 'correct', meta={'pattern': 'M1', 'shown': ['ni', 'wo', 'ta', 'hao']}))
    0.25
    >>> guess_of(Response('ada', 'ni', 'wrong', meta={'guess': 0.5, 'pattern': 'M1', 'shown': ['ni', 'wo', 'ta']}))
    0.5
    >>> guess_of(Response('ada', 'ni', 'correct'), default=0.2)  # nothing in meta
    0.2
    >>> guess_of({'pattern': 'M1', 'shown': ['ni', 'wo']})  # a round about to be played
    0.5
    >>> guess_of(Response('ada', 'ni', 'correct', meta={'pattern': 'P1'})) is None  # typed: no k
    True
    >>> guess_of(Response('ada', 'ni', 'correct', meta={'guess': 1.0}))
    Traceback (most recent call last):
        ...
    ValueError: Response 'ni': meta['guess'] must be a number in [0, 1), got 1.0
    """
    meta = response.meta if isinstance(response, Response) else response
    if META_GUESS in meta:
        g = meta[META_GUESS]
        if isinstance(g, bool) or not isinstance(g, Real) or not 0.0 <= g < 1.0:
            where = f"Response {response.item!r}" if isinstance(response, Response) else "meta"
            raise ValueError(
                f"{where}: meta[{META_GUESS!r}] must be a number "
                f"in [0, 1), got {g!r}"
            )
        return float(g)
    shown = meta.get(META_SHOWN)
    if meta.get(META_PATTERN) in GUESS_IS_ONE_OVER_K and shown:
        return 1.0 / len(shown)
    return default


def confusions(responses: Iterable[Response]) -> Counter[tuple[str, str]]:
    """How often each item was answered with each wrong option: ``(item, chosen) -> n``.

    Read from wrong responses that recorded ``meta['chosen']``; everything else is
    skipped. This is what a distractor policy feeds on (offer the learner the options
    they actually mistake for this item) and what tells two labels apart. Pass one
    student's responses for their confusions, everyone's for the population's.

    >>> log = [
    ...     Response('ada', 'tsu', 'wrong', meta={'chosen': 'shi'}),
    ...     Response('ada', 'tsu', 'wrong', meta={'chosen': 'shi'}),
    ...     Response('ada', 'tsu', 'correct', meta={'chosen': 'tsu'}),
    ...     Response('ada', 'so', 'wrong', meta={'chosen': 'n'}),
    ...     Response('ada', 'so', 'wrong'),            # no pick recorded: not counted
    ... ]
    >>> confusions(log)
    Counter({('tsu', 'shi'): 2, ('so', 'n'): 1})
    """
    return Counter(
        (r.item, chosen)
        for r in responses
        if r.outcome is Outcome.WRONG
        and (chosen := r.meta.get(META_CHOSEN)) is not None
        and chosen != r.item
    )


def restrict_labels(
    items: Mapping[str, Item],
    *,
    keep: Collection[str] | Callable[[str], bool],
    drop_unlabelled: bool = False,
) -> dict[str, Item]:
    """Project an item bank onto a subset of its labels — one facet, say.

    Labels that never vary independently of each other cannot be told apart: tag every
    item with nine labels and each label's deviation stays at the student's global
    skill, whatever the data. Modelling one facet at a time is often what makes labels
    separable (:func:`~learny.tracing.diagnostics.label_separation` measures it).
    *Which* labels belong together is a judgement about the taxonomy, so the library
    never collapses anything by itself; this is the explicit, opt-in way to do it.

    ``keep`` is a collection of labels or a predicate on a label. Weights are preserved.
    An item left with no labels still carries its difficulty and still informs the
    student's global skill, so it is kept unless ``drop_unlabelled=True``.

    >>> bank = {
    ...     'q1': Item('q1', labels={'topic:fractions': 1.0, 'trap:units': 0.6}),
    ...     'q2': Item('q2', labels=('trap:units',), difficulty=0.7),
    ... }
    >>> topics = restrict_labels(bank, keep=lambda label: label.startswith('topic:'))
    >>> topics['q1'].weights, topics['q2'].weights, topics['q2'].difficulty
    ({'topic:fractions': 1.0}, {}, 0.7)
    >>> sorted(restrict_labels(bank, keep={'topic:fractions'}, drop_unlabelled=True))
    ['q1']
    """
    if isinstance(keep, str):  # a str is a Collection of characters: never meant
        raise TypeError(
            f"keep={keep!r} is a single string; pass a collection such as {{{keep!r}}}, "
            "or a predicate such as lambda label: label.startswith(...)"
        )
    wanted = keep if callable(keep) else frozenset(keep).__contains__

    def project(item: Item) -> Item:
        weights = {label: w for label, w in item.weights.items() if wanted(label)}
        return replace(item, labels=weights)

    projected = {key: project(item) for key, item in items.items()}
    if drop_unlabelled:
        projected = {key: item for key, item in projected.items() if item.weights}
    return projected
