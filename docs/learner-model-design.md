# Learner modelling in `learny` — the boundaries, decided up front

Date: 2026-09-20. Scope: `learny.tracing`, v1.

## What this is

A per-student model of what a learner knows, carrying **priors** that **update from that student's own data**. It is deliberately independent of any one application: it takes a bank of labelled items and a stream of responses, and answers two questions — *how likely is this student to get this item right?* and *which labels is this student weakest on?*

## The regime it is built for

This is the part that determines every other decision, so it is stated first.

- **Few learners.** One to a handful, often exactly one. Not a MOOC, not a classroom platform. A family, a tutor, a single teacher.
- **Sparse responses.** A student may have a hundred responses in total, spread over a hundred or more labels. Most labels will have between zero and three observations for that student. **Cold start is the normal case, not an edge case.**
- **An externally calibrated item bank.** Difficulty is often already known from a source better than the local data — a published pass rate, an official difficulty band, an exam board's statistics.
- **Multi-label items with uneven tagging quality.** An item exercises several skills at once, and the labels were not all assigned with equal confidence.
- **Outcomes that are not binary.** Many assessments distinguish a wrong answer from an unanswered one, and the difference is informative.

A method that only works after a thousand responses is useless here. That rules out most of the knowledge-tracing literature as a *default*, while leaving it available as a seam.

## The one-command test (the definition of v1)

```
v1 done when:  model.record(student, item, 'correct'); model.predict(student, other_item)
               returns a calibrated probability, and model.replay() reproduces it from the log alone.
```

Covered by `learny/tracing/tests/test_model.py::TestReplayContract`.

## The seam table

Four seams. Each is one keyword argument with a default that genuinely works, and each replacement is something that **already exists** — not something imagined.

| # | Seam | v1 default (no new dependency) | Replacement already pointed at |
|---|---|---|---|
| 1 | How one response changes belief — `estimator=` | `RaschEstimator`: online Rasch with a Gaussian posterior per skill, one Newton step per response. Pure stdlib (`math`). | PFA / Best-LR logistic regression, once a population exists. Conjugate Beta-Binomial via **`ba.bayesian`** (`t/ba`, in the manifest, verified importable): `priors.from_mean_kappa` turns an observed difficulty into a prior mean and a reliability into a prior strength. A GLMM batch fit (`statsmodels`) is the same model fitted jointly. |
| 2 | What is known about each item — `items=` | A plain `{id: Item}` mapping; `Item` carries labels (optionally weighted) and an observed difficulty. | Any mapping, including a lazy one over a stored item bank. A prerequisite-graph / product-order version is described in `docs/research/multidimensional-skill-spaces.md` §7. |
| 3 | Where responses are recorded — `log=` | `ResponseLog`: append-only JSON-lines, one file per student, under `~/.local/share/learny/responses/`. A plain `dict` also works, which is what the tests use. | `s3dol` `S3Store` (in the manifest) for the same `MutableMapping` contract. |
| 4 | Where per-student estimates are cached — `estimates=` | `dol.JsonFiles` under `~/.local/share/learny/estimates/`, with a stdlib fallback so the package works with no third-party dependency at all. | Any `MutableMapping`; `s3dol`, a database, or an in-process `dict`. |

```
Surface for v1:  Python API only.
                 CLI / HTTP / MCP / frontend: question answered, not built — see below.
NOT seams:       the outcome vocabulary (three values, written directly), the log record
                 format, the logit link. These are decided, not parameterised.
```

**Would another surface need the core to change?** No. `LearnerModel` takes and returns plain data, the stores are already `MutableMapping`, and nothing touches process state. A CLI is `python-dispatching`'s job over the same facade; HTTP and MCP are the same functions again. The frontend case is the interesting one and still costs the core nothing: a browser client would reimplement the estimator rather than call Python, which is exactly why the per-student state is a **small, explicit JSON document** — two numbers per skill — rather than a pickled object.

## The five decisions that carry the design

### 1. The log is the source of truth; every estimate is a cache

The estimator **will** change — that is the entire premise of seam 1 — and a log that can be replayed makes that a re-run rather than a migration.

Enforced by `Estimator.observe` being a pure function of `(state, response, item)`, and asserted by `test_replay_reproduces_live_state`: folding `observe` over the whole log must reproduce, exactly, the state that live recording produced. If that test ever fails, the estimator has grown a dependence on something outside its inputs and is no longer swappable.

### 2. A posterior, not a point estimate

Each skill is a Gaussian `(mu, var)` on the logit scale, updated by one Newton step on the log-posterior — which is Glickman's Glicko update against an opponent of known strength, and equivalently the standard assumed-density filter for Bayesian logistic regression.

Carrying the variance is not ornamentation. It buys four things from one formula that would otherwise need four heuristics:

- **Cold start.** The step size *is* the posterior precision, so early responses move the estimate a long way and later ones refine it. There is no separate warm-up mode to get wrong.
- **Honest prediction.** Predictions integrate over the posterior (MacKay's probit approximation), so with no data the model reports something near the item's base rate *pulled toward a coin flip* — it knows the item, it does not yet know the student, and it says so.
- **A real confidence number.** `Mastery.confidence` and `Mastery.interval()` are posterior quantities, not a rescaled counter.
- **Forgetting without a guess about direction** (see 5).

Classical Elo is this same update with the information term frozen: Elo's `U(n) = a/(1 + b·n)` is exactly `1/(1/var + n·I)` for constant information `I`. So `gain='elo'` is not a rival estimator, it is this one with a constant step size — which matters because it means a consumer that wants plain Elo does not fork the model.

### 3. Item difficulty does not update by default — and that is the interesting part

Textbook Elo moves the learner's ability and the item's difficulty in opposite directions from the same residual. That is sound when many learners meet each item, because a population pins the item down.

**The common case here is one or two learners, ever.** At N=1, ability and difficulty are not jointly identifiable: they absorb each other, and you get a model that fits the history perfectly and predicts nothing. So the default treats item difficulty as **given**, from an observed external source, and updates only the learner. `update_difficulty=True` restores textbook Elo for anyone who actually has a population.

This is not a compromise. With a pre-calibrated item bank it is the better-founded model — online ability estimation against known item parameters, which is what adaptive testing has always done.

It is also why the Rasch form beats a per-label success/failure count. A Beta-Binomial tally cannot condition on the item's difficulty at update time: eight correct out of eight easy items and four out of eight mixed ones give it the same posterior. The Rasch form scores a correct answer on a hard item as more evidence, which is the whole point. (`difficulty_from_rank` is provided for banks whose published difficulty is an ordinal band rather than a measured rate — it is a prior, not a measurement.)

### 4. The pooling is across labels within one student, never across students

The question this design had to answer: how do priors pool without one student's data leaking into another's estimate?

**The default does not pool across students at all.** It pools across labels within one student:

```
logit P(correct) = global_skill + aggregate(label deviations) - item_difficulty
```

A label carries only a *deviation* from that student's own global skill, with a tight prior. With one or two observations the deviation stays near zero and the prediction falls back on the student's global skill plus the item's known difficulty; as evidence accumulates the deviation earns its place. One paper's worth of responses gives the global skill enough precision to serve as every label's prior **before any label-specific evidence exists**. The hierarchy is the cold-start mechanism, not a refinement on top of one.

Three consequences, all of them wanted:

1. **No other student need exist.** The single-student case is the default path, not a degenerate special case of a population model.
2. **The privacy boundary is structural, not procedural.** There is no code path by which one student's responses reach another's estimate. `test_one_students_data_never_touches_anothers_estimate` asserts it.
3. **The population term comes from the item bank**, which is an aggregate published by someone else and carries no individual's data.

If cross-student pooling is ever wanted, it belongs behind seam 1 as a deliberate act producing an **explicitly exported, versioned artifact** — so that what crosses between students is visible and reviewable — never as an implicit side effect of fitting.

`conjunctivity=` controls how labels combine: 0 (the default) is compensatory, a reliability-weighted mean in which strong labels offset weak ones; larger values approach weakest-link, where the label the student is worst at dominates. Real assessments contain both kinds of item, so this is a knob rather than a verdict. Label weights below 1.0 attenuate a label's influence, which is how a facet tagged with lower inter-rater agreement is stopped from moving an estimate as far as a reliably tagged one.

### 5. A skip is not a wrong answer, and not all skips are alike

`Outcome` has three values. Where an assessment's scoring rewards prudent abstention, an unanswered question is a signal about confidence and time, not about whether the student could have answered. Binarising at capture destroys that permanently, so the **log always records what actually happened** and the estimator decides what to make of it.

- A blank in the **trailing run** at the end of a sitting is a clock, not a judgement — `mark_not_reached` flags it and the default ignores it, the standard treatment for an item that was not administered.
- An **interior** blank, with answered questions after it, is a decision not to answer: a half-weight soft observation at the guessing rate. Scoring it as wrong is more biased than ignoring it; ignoring it is biased too, because abstention correlates with lower ability. A soft observation is the compromise, and it is stated as one.

`guess=` matters here and is left at 0 deliberately: the guessing rate is a property of the assessment (0.2 for five-option multiple choice), not of the model, and a wrong value quietly biases everything.

### 6. Forgetting inflates variance; it does not decay the mean

Before each update, a skill's variance grows with the time since it was last seen, capped at its prior. Inflating variance says *we know less now*, which is true. Decaying the mean would say *the skill got worse*, which is a guess — and for a learner who is also being taught elsewhere, quite possibly the wrong one. A stale belief simply re-opens so that new evidence moves it again.

## Deliberately out of scope for v1

- **Scheduling / spaced repetition.** A *retention* clock ("when should this come back?") and a *proficiency* clock ("how likely, right now?") are different models and should stay distinct. v1 is the proficiency clock only. When the retention clock is wanted, `t/kodokan/kodokan/learning.py` already implements `Leitner`, `SM2`, `FSRSLite` and `ConfusionWeighted` in Python behind a common interface, and already rebuilds state by replaying a history log — the same contract used here.
- **Item taxonomy, tagging and inter-rater agreement.** A different package: this one consumes a taxonomy, it does not define one.
- **Calibration reporting.** For a learner model, calibration matters more than AUC, and a model whose calibration you cannot plot should not be shown to a learner. v1 does not compute one. **This is the most important named next step**, and the prequential machinery for it is cheap: replay the log, score each prediction *before* its update, bin against observed frequency.
- **Hyperparameter refitting.** The same prequential replay would fit `prior_var`, `label_prior_var`, `forget_per_week` and `abstain_weight` over a small grid. Out of scope now; it needs no new seam when it arrives.

## Data, and the line it does not cross

`learny` is a **public** repository. Per-student responses are personal data, and the first consumers' learners include children.

- Every example, doctest and fixture in this package is **synthetic**.
- Real responses live under `~/.local/share/learny/`, never in a repository. The default store root is the policy: a store defaulting to `./data` would invite every caller to commit it.
- `LEARNY_DATA_DIR` overrides the root for tests and CI.
- One file per student, so one learner's data can be audited, handed over or deleted on its own.
- Nothing derived from a private consumer project — its data, its measurements, or its identity — belongs in this repository. Consumer-specific integration notes live in that consumer's own repository.
