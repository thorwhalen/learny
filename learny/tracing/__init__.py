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
    Comparison,
    LabelSeparation,
    ScoreCalibrationReport,
    calibration,
    compare_estimators,
    fit_item_spreads,
    fit_threshold_spread,
    label_separation,
    prequential,
    reads_scores,
    score_calibration,
)
from learny.tracing.difficulty import (
    Estimate,
    FeatureDifficulty,
    fit_feature_difficulty,
    attempt_features,
    item_features,
)
from learny.tracing.estimators import (
    Estimator,
    ItemSpreads,
    Mastery,
    PartialCreditEstimator,
    RaschEstimator,
    Skill,
    binomial_thresholds,
    difficulty_from_rank,
    spread_thresholds,
    expit,
    logit,
    mark_not_reached,
)
from learny.tracing.model import (
    DEFAULT_CREDIBLE_BELOW,
    DEFAULT_MULTIPLICITY,
    DEFAULT_RELATIVE_TO,
    LearnerModel,
    Weakest,
)
from learny.tracing.records import Item, LabelWeights, Outcome, Response, restrict_labels
from learny.tracing.stores import ResponseLog, data_dir, estimate_store, response_log

__all__ = [
    # the facade most callers want
    "LearnerModel",
    "Weakest",
    "DEFAULT_CREDIBLE_BELOW",
    "DEFAULT_RELATIVE_TO",
    "DEFAULT_MULTIPLICITY",
    # the vocabulary
    "Item",
    "Outcome",
    "Response",
    "Mastery",
    "Skill",
    "LabelWeights",
    # the seams
    "Estimator",
    "ItemSpreads",
    "RaschEstimator",
    "PartialCreditEstimator",
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
    "ScoreCalibrationReport",
    "score_calibration",
    "reads_scores",
    # choosing settings from a log
    "compare_estimators",
    "Comparison",
    "fit_item_spreads",
    "fit_threshold_spread",
    "prequential",
    # what item features say about difficulty, across students (an exported artifact)
    "fit_feature_difficulty",
    "FeatureDifficulty",
    "Estimate",
    "attempt_features",
    "item_features",
    # helpers
    "restrict_labels",
    "difficulty_from_rank",
    "binomial_thresholds",
    "spread_thresholds",
    "mark_not_reached",
    "expit",
    "logit",
]
