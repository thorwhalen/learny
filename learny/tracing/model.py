"""The facade: one object that records responses and answers questions about a student.

``LearnerModel`` is the thing most callers touch. It owns four collaborators, each one a
constructor argument with a working default, so the simple case needs no arguments at all
and every part can be replaced without touching the others:

==================  ==========================================================
``items``           what is known about each question (labels, difficulty)
``estimator``       how one response changes belief (:class:`~learny.tracing.estimators.RaschEstimator`)
``log``             the append-only record of responses — the source of truth
``estimates``       the cache of per-student state, rebuildable from ``log``
==================  ==========================================================
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from learny.tracing.estimators import RaschEstimator, Estimator, Mastery
from learny.tracing.records import Item, Outcome, Response
from learny.tracing.stores import ResponseLog, estimate_store, response_log

__all__ = ["LearnerModel"]


class LearnerModel:
    """What a student knows, estimated from what they have answered.

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

    Getting a hard item wrong should leave the student looking weaker on the labels it
    exercises than a student who has answered nothing:

    >>> model.mastery('ada')['area'].mu < model.mastery('ada')['fractions'].mu
    True
    """

    def __init__(
        self,
        *,
        items: Mapping[str, Item] | None = None,
        estimator: Estimator | None = None,
        log: ResponseLog | Any | None = None,
        estimates: Mapping[str, Any] | None = None,
    ):
        self.items = dict(items) if items is not None else {}
        self.estimator = estimator if estimator is not None else RaschEstimator()
        self.log = log if log is not None else response_log()
        self.estimates = estimates if estimates is not None else estimate_store()

    # -- recording ---------------------------------------------------------------

    def record(
        self,
        student: str,
        item: str,
        outcome: Outcome | str | bool,
        *,
        at: float | None = None,
        **meta: Any,
    ) -> None:
        """Log one response and fold it into the student's estimate.

        The log is written first: if updating the cache fails, the evidence survives and
        :meth:`replay` can rebuild from it.
        """
        response = Response(student, item, Outcome(outcome), at=at, meta=meta)
        self._append(response)
        state = self._state(student)
        self.estimates[student] = self.estimator.observe(
            state, response, self.items.get(item)
        )

    def record_many(self, responses: Iterable[Response]) -> None:
        """Record a batch — a whole paper, say — in the order given."""
        for response in responses:
            self.record(
                response.student,
                response.item,
                response.outcome,
                at=response.at,
                **dict(response.meta),
            )

    # -- asking ------------------------------------------------------------------

    def predict(self, student: str, item: str | Item) -> float:
        """Probability that ``student`` answers ``item`` correctly."""
        item_obj = item if isinstance(item, Item) else self.items.get(item, Item(item))
        return self.estimator.predict(self._state(student), item_obj)

    def mastery(self, student: str) -> dict[str, Mastery]:
        """Per-label mastery for one student, weakest first when sorted by skill."""
        return self.estimator.mastery(self._state(student))

    def weakest(self, student: str, n: int = 5) -> list[Mastery]:
        """The ``n`` labels this student looks weakest on — what to practise next.

        Labels with no evidence are not included: the model has nothing to say about
        them, and saying it anyway is how a learner model loses trust.
        """
        ranked = sorted(self.mastery(student).values(), key=lambda m: m.mu)
        return ranked[:n]

    # -- the contract that makes the estimator replaceable ------------------------

    def replay(self, student: str | None = None) -> None:
        """Rebuild estimates from the log, discarding the cache.

        This is what makes changing the estimator a re-run rather than a migration, and
        it is asserted by the tests: folding ``observe`` over the log must reproduce the
        state that live recording produced.
        """
        students = [student] if student is not None else self._students()
        for name in students:
            state = self.estimator.init()
            for response in self._responses(name):
                state = self.estimator.observe(
                    state, response, self.items.get(response.item)
                )
            self.estimates[name] = state

    # -- store plumbing ----------------------------------------------------------
    # `log` is either a ResponseLog or any mapping-like stand-in (a plain dict is
    # genuinely useful in tests and notebooks), so these three adapt to both.

    def _append(self, response: Response) -> None:
        if hasattr(self.log, "append"):
            self.log.append(response)
        else:
            self.log.setdefault(response.student, []).append(response)

    def _students(self) -> list[str]:
        if hasattr(self.log, "students"):
            return self.log.students()
        return sorted(self.log)

    def _responses(self, student: str) -> list[Response]:
        try:
            return list(self.log[student])
        except KeyError:
            return []

    def _state(self, student: str) -> dict[str, Any]:
        try:
            return dict(self.estimates[student])
        except KeyError:
            return self.estimator.init()
