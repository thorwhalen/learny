---
name: learner-modelling
description: >-
  Estimate what a learner knows and what to practise, with `learny`: per-student P(correct) on an item, item difficulty (prior from a published band or item features, posterior from play), the labels a student is credibly weakest on, the next item and its distractors, and whether to trust the numbers.
  Use in any education, quiz, drill, exam-prep or learning-game app on "how hard is this question for this student", "estimate difficulty", "what should she work on", "what to practise next", "which skills is he weak on", "diagnose a student from their answers", "adaptive practice", "spaced repetition", "which features make a question hard", "feature engineering on items", "prior and posterior difficulty", "Bayesian success/failure estimate", or IRT, Rasch, Elo, LLTM, knowledge tracing, partial credit, mastery, calibration.
  Read before writing scoring, difficulty or mastery code of your own.
metadata:
  audience: users
  source: thorwhalen/learny (README, docs/learner-model-design.md, docs/research/)
---

# learner-modelling: what a learner knows, what to ask next, and when to believe it

`learny` already does this, as a library: `learny.tracing` is the learner model and `learny.scheduling` chooses the next item and its options. Write an adapter that feeds it your app's items and responses. Do not write a new estimator. If the model is missing something you need, that is an issue in learny (see the last section).

## The model in one paragraph

Each response updates a Gaussian posterior over the student's ability: one global ability plus one deviation per label (topic, skill, facet), by an online Rasch step (Glicko against an opponent of known strength). The prediction is `P(correct) = g + (1-g)·σ(θ + agg(δ_labels) − d_item)`. Item difficulty `d` is the **prior**. It comes from the bank (a published pass rate, or an ordinal band through `difficulty_from_rank`) or from item features (`fit_feature_difficulty`). It is **not** re-estimated from one or two students, because ability and difficulty are not jointly identifiable there. The design, with its fourteen decisions, is `docs/learner-model-design.md` in the learny repo.

## Task → call

| You want | Call |
|---|---|
| Record an answer, predict the next one | `LearnerModel(items=...)`, `.record(student, item, 'correct' \| 'wrong' \| 'skipped', score=, max_score=, **meta)`, `.predict(student, item)` |
| What to practise: labels credibly below the student's own level | `.weakest(student, n=5)`; `.reason` explains an empty answer; `credible_below=None` gives the plain ranking |
| Can this student's labels be told apart at all? | `.separation(student).distinguishable` |
| Are the probabilities honest? | `.calibration()` (prequential); `.score_calibration()` for star or partial-credit scores |
| Which item features make an item hard, with uncertainty, and the difficulty of an item nobody has played | `fit_feature_difficulty(log, items=items)`: `.weights()`, `.predict(features)`, `.apply(items)`, `.to_dict()` (the Linear Logistic Test Model with a residual per item) |
| Features of how one attempt was set up (number of decoys, a timer, a hint) | put them in `response.meta['features']`; `fit_feature_difficulty` reads them as per-attempt terms (`attempt_features=`) |
| A published ordinal difficulty band as a prior | `difficulty_from_rank(rank, n_ranks)` into `Item(difficulty=...)` |
| Ordered scores (1–5 stars, partial credit) | `PartialCreditEstimator()` as `estimator=`; per-item spreads from a population: `fit_item_spreads` |
| Choose between estimators or settings from your own log | `compare_estimators(log, items=, candidates={...})` |
| Which item next, and which wrong options beside it | `learny.scheduling.make_strategy(key)` (`confusion_weighted` default, `leitner`, `sm2`, `fsrs_lite`, `weakest`, `uniform_random`), `.next_selection(responses, candidates=...)` |
| Items tagged on many facets at once | `restrict_labels(items, keep=...)`: model one facet at a time |
| Blanks at the end of a paper (the clock) versus blanks mid-paper (a choice) | `mark_not_reached(responses)` |

## Rules that are easy to get wrong

- **Cold start is the normal case.** One learner, a few answers per label. Every default is built for it, so do not swap in an estimator that needs a warm-up.
- **A skip is not a wrong answer.** `Outcome` has three values. A trailing blank is "not reached" and is ignored; an interior blank counts as a half-weight observation at the guessing rate.
- **Set `guess=`** (for example 0.2 for five options), or record the options shown (`meta['shown']`, `meta['pattern']`) so the guess rate is read per response.
- **Weight labels you trust less.** `Item('q', labels={'topic': 1.0, 'trap': 0.57})` moves the estimate less for a noisily tagged facet.
- **Never pool students implicitly.** Anything learned across students (`fit_feature_difficulty`, `fit_item_spreads`) is an explicit, exported artifact that enters through `items=` or `thresholds=`. One student's answers never change another's estimate.
- **`update_difficulty=True` only with a real population.** Elo-style difficulty estimates need on the order of a hundred learners per item; below that, use `fit_feature_difficulty` to share strength across items through their features.
- **Learner data is personal data.** learny writes it under `~/.local/share/learny/` (`LEARNY_DATA_DIR`), one file per student. Keep it out of every repository, and keep it out of anything public.

## Research behind it (read before arguing with a default)

In the learny repo:

- `docs/learner-model-design.md`: the regime, the four seams, and decisions 1–14 (pooling, ordered scores, calibrated `weakest()`, the LLTM, item spreads), each with its reason.
- `docs/research/multidimensional-skill-spaces.md`: knowledge spaces, Q-matrices and cognitive diagnostic models, prerequisite sequencing, and its negative evidence.
- `docs/research/weakest-update-difficulty-mismatch.md`: a measured false-flag and power study of `weakest()`.
- `docs/research/learning-game-patterns.md` (and the `learning-game-patterns` skill): what each game form must log for the model, and its guessing rate.
- `docs/research/symbol-introduction-order.md`: choosing and ordering what to teach.

Conjugate Beta-Binomial estimates, when you want them instead of the Rasch step: the `ba` package (`ba.bayesian`). Application-specific research and decisions (a consumer's own model decision, a learning-science survey for one app) are listed in your workspace's education group routing document, when it has one (`priv group show <group>`).

## When learny lacks what you need

File it in `thorwhalen/learny` as a component issue (the need, what you tried, the smallest seam that would do it) before writing your own. The open ones include the item bank as a separate package and a curriculum optimiser.
