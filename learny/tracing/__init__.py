"""Learner modelling: what a student knows, estimated from what they have answered.

The shape of this subpackage in one paragraph: responses go into an **append-only log**
which is the single source of truth; everything else — per-student mastery estimates
included — is a cache that can be rebuilt by replaying that log. That constraint is what
lets the estimator be replaced later without a data migration, and it is why
:meth:`~learny.tracing.model.LearnerModel.replay` exists and is tested.

>>> from learny.tracing import Item, LearnerModel
>>> items = {'q1': Item('q1', labels=('fractions',), difficulty=0.5)}
>>> model = LearnerModel(items=items, log={}, estimates={})   # in-memory, for the doctest
>>> model.record('ada', 'q1', 'correct')
>>> model.predict('ada', 'q1') > 0.5
True
"""

from learny.tracing.diagnostics import (
    CalibrationBin,
    CalibrationReport,
    LabelSeparation,
    calibration,
    label_separation,
    prequential,
)
from learny.tracing.estimators import (
    Estimator,
    Mastery,
    RaschEstimator,
    Skill,
    difficulty_from_rank,
    expit,
    logit,
    mark_not_reached,
)
from learny.tracing.model import LearnerModel
from learny.tracing.records import Item, LabelWeights, Outcome, Response, restrict_labels
from learny.tracing.stores import ResponseLog, data_dir, estimate_store, response_log

__all__ = [
    # the facade most callers want
    "LearnerModel",
    # the vocabulary
    "Item",
    "Outcome",
    "Response",
    "Mastery",
    "Skill",
    "LabelWeights",
    # the seams
    "Estimator",
    "RaschEstimator",
    "ResponseLog",
    "estimate_store",
    "response_log",
    "data_dir",
    # when to believe it
    "LabelSeparation",
    "label_separation",
    "CalibrationReport",
    "CalibrationBin",
    "calibration",
    "prequential",
    # helpers
    "restrict_labels",
    "difficulty_from_rank",
    "mark_not_reached",
    "expit",
    "logit",
]
