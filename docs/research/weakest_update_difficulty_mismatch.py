"""Measure the ``update_difficulty`` replay mismatch of ``weakest(multiplicity="simulated")`` (#46).

With ``RaschEstimator(update_difficulty=True)`` the simulated null redraws every answer at
the difficulties the student's state *ended* with, while each replay starts from
``init()`` and relearns them from the prior on the redrawn answers. This script measures
how much that costs, on the synthetic students of
``learny/tracing/tests/test_weakest_calibration.py``, by comparing the rate at which
``weakest`` flags anything for a student with no real weakness (target ``1 - Phi(1)``,
about 0.159) and the rate it finds a real weakness of ``-2`` logits on ``l0``, across:

* ``fixed`` -- ``update_difficulty=False`` (the default estimator), as the reference;
* ``current`` -- ``update_difficulty=True`` as shipped before #48 (the mismatch);
* ``prior_redraw`` -- the redraw uses the prior difficulties the replay starts from;
* ``seeded_replay`` -- each replay starts from the learned difficulties the redraw uses.

The last two are the two ways to remove the mismatch. Every variant sees the same
students (common random numbers). Synthetic data only.

Since #48 the shipped ``RaschEstimator(update_difficulty=True)`` is ``prior_redraw``;
``current`` keeps the old redraw through :class:`LearnedRedraw`.

Usage::

    python docs/research/weakest_update_difficulty_mismatch.py [--students 400] [--draws 200] [--jobs 2]
"""

from __future__ import annotations

import argparse
import copy
import math
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from learny.tracing import Item, LearnerModel, RaschEstimator, Response

WEEK = 7 * 24 * 3600.0
#: (labels, responses, item difficulty as P(correct) at skill 0, skip probability):
#: the cells of test_weakest_calibration.py.
CELLS = (
    (3, 18, 0.5, 0.0),
    (6, 60, 0.5, 0.0),
    (3, 9, 0.05, 0.0),
    (20, 40, 0.05, 0.0),
    (6, 60, 0.5, 0.3),
    (10, 10, 0.03, 0.0),
)
WEAKNESS = -2.0
VARIANTS = ("fixed", "current", "prior_redraw", "seeded_replay")


class LearnedRedraw(RaschEstimator):
    """Redraws at the difficulties the state ended with: the behaviour before #48."""

    def null_response(self, state, response, item, rng):
        self._ended_with = state
        return super().null_response(state, response, item, rng)

    def _null_difficulty(self, item):
        return self._difficulty(self._ended_with, item)


class PriorRedraw(RaschEstimator):
    """Redraws at the prior difficulties, the ones each replay starts from."""

    def null_response(self, state, response, item, rng):
        return super().null_response(
            {k: v for k, v in state.items() if k != "items"}, response, item, rng
        )


@dataclass
class SeededReplay(RaschEstimator):
    """Each replay starts from the learned difficulties the redraw uses (``seed``)."""

    seed: dict[str, Any] = field(default_factory=dict)

    def init(self):
        state = super().init()
        if self.seed:
            state["items"] = copy.deepcopy(self.seed)
        return state


def _estimator(variant: str) -> RaschEstimator:
    if variant == "fixed":
        return RaschEstimator()
    if variant == "current":
        return LearnedRedraw(update_difficulty=True)
    if variant == "prior_redraw":
        return PriorRedraw(update_difficulty=True)
    return SeededReplay(update_difficulty=True)


def _record(rng, n_labels, n_responses, *, difficulty, skip, weakness):
    """One synthetic student's answers, as in the calibration tests."""
    theta = rng.gauss(0, 1)
    b = math.log(difficulty / (1 - difficulty))
    out = []
    for i in range(n_responses):
        label = f"l{i % n_labels}"
        p = 1 / (1 + math.exp(-(theta + (weakness if label == "l0" else 0.0) - b)))
        outcome = (
            "skipped" if rng.random() < skip
            else "correct" if rng.random() < p else "wrong"
        )
        out.append((label, outcome, i * WEEK))
    return out


def _flags(record, variant, *, n_labels, difficulty, draws):
    items = {
        f"l{j}": Item(f"l{j}", labels=(f"l{j}",), difficulty=difficulty)
        for j in range(n_labels)
    }
    model = LearnerModel(items=items, estimator=_estimator(variant), log={}, estimates={})
    for label, outcome, at in record:
        model.record("s", label, outcome, at=at)
    if variant == "seeded_replay":
        model.estimator.seed = model.estimates["s"].get("items", {})
    flagged = model.weakest("s", n=n_labels, multiplicity="simulated", null_draws=draws)
    return {m.label for m in flagged}


def _cell(args):
    (n_labels, n_responses, difficulty, skip), students, draws, seed = args
    counts = {(v, w): 0 for v in VARIANTS for w in ("null", "weak")}
    for weakness, key in ((0.0, "null"), (WEAKNESS, "weak")):
        rng = random.Random(f"{seed}:{n_labels}:{n_responses}:{difficulty}:{skip}:{key}")
        for _ in range(students):
            record = _record(
                rng, n_labels, n_responses, difficulty=difficulty, skip=skip, weakness=weakness
            )
            for variant in VARIANTS:
                flagged = _flags(record, variant, n_labels=n_labels, difficulty=difficulty, draws=draws)
                counts[variant, key] += bool(flagged) if key == "null" else ("l0" in flagged)
    return {k: c / students for k, c in counts.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--students", type=int, default=400)
    parser.add_argument("--draws", type=int, default=200)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--seed", default="46")
    args = parser.parse_args(argv)
    jobs = [(cell, args.students, args.draws, args.seed) for cell in CELLS]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(_cell, jobs))
    sd = math.sqrt(0.159 * 0.841 / args.students)
    print(f"students per cell: {args.students}, null_draws: {args.draws}, "
          f"Monte Carlo sd of a false-flag rate near 0.159: {sd:.3f}\n")
    print("| labels | responses | difficulty | skip | "
          + " | ".join(f"false: {v}" for v in VARIANTS) + " | "
          + " | ".join(f"power: {v}" for v in VARIANTS) + " |")
    print("|" + "---|" * (4 + 2 * len(VARIANTS)))
    for (n_labels, n_responses, difficulty, skip), rates in zip(CELLS, results):
        row = [str(n_labels), str(n_responses), f"{difficulty:g}", f"{skip:g}"]
        row += [f"{rates[v, 'null']:.3f}" for v in VARIANTS]
        row += [f"{rates[v, 'weak']:.3f}" for v in VARIANTS]
        print("| " + " | ".join(row) + " |")


if __name__ == "__main__":
    main()
