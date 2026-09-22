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
- **Hyperparameter refitting.** The prequential replay in `learny.tracing.diagnostics` (`prequential()`) would fit `prior_var`, `label_prior_var`, `forget_per_week` and `abstain_weight` over a small grid. Out of scope now; it needs no new seam when it arrives.

## Decisions of 2026-09-22 (issue #5): label dimensionality, pooling, scope

### 7. Model labels as given; measure whether they can be told apart; never collapse silently

The real-data finding — nine labels per item left every label indistinguishable from overall skill, one facet (~1.7 labels per item) gave four times the separation — is structural, not only a matter of sample size. In `_aggregate` each of an item's *k* labels gets share `1/k`, so it receives `1/k²` of the item's information per response. At nine labels that is 1/81; at 1.7 it is about 1/3. More data does not fix a design in which the labels never vary independently. Caveat: the "four times" was measured on *posterior* deviations, which the prior shrinks harder the less information a label gets, so it overstates how much projection helps; on synthetic data with partial co-tagging the separation of the wide and the projected models is much closer. The structural point stands only for labels that *always* co-occur.

- **Default: labels are modelled exactly as the item bank gives them.** Whether a taxonomy should be collapsed for modelling is a judgement about that taxonomy, and auto-collapsing would silently change what a label means.
- **The model now says when its ordering is noise.** `LearnerModel.separation(student)` returns the Rasch separation index over the label *deviations* (`G = true SD / RMSE`, reliability `G²/(1+G²)`, strata `(4G+1)/3`). `distinguishable` is `G ≥ 2` — reliability 0.8, about three strata, the usual bar for a ranking one acts on. The state holds posteriors, not the likelihood-only measures the classical formula assumes, so the index is read in its posterior (EAP) form: `G = sd(mu) / sqrt(mean(var))`, reliability `var(mu) / (var(mu) + mean(var))`. Fed shrunk posteriors, the classical `sqrt(var(mu) − mean(var)) / rmse` reads about `G² − 1` in place of `G²`, so separable labels read as noise (post-merge review of #10). #11 fixed that by de-shrinking each posterior with the estimator's `label_prior_var`. That inverse is only valid while the variance comes from the prior plus evidence, and `forget_per_week` re-opens a stale label's variance without moving its mean. With timestamped responses a day or a week apart, de-shrinking called pure noise distinguishable in most runs (post-merge review of #11). The EAP form needs no prior, matches the likelihood `G` in expectation under a correct prior, and forgetting can only lower it. It is conservative when the true spread is far wider than `label_prior_var`, and that is the safe direction for a gate on acting.
- **Projection is explicit and opt-in.** `restrict_labels(items, keep=...)` projects a bank onto one facet. It lives here, not in an item-bank package, because its signature is `Mapping[str, Item] -> Mapping[str, Item]` and needs no knowledge of any taxonomy.
- **`weakest(..., credible_below=z)`** returns only labels whose deviation is credibly below the student's own global skill (upper bound `mu + z*sd` below zero); with indistinguishable labels it returns nothing, which is the honest answer. **This is the default** (`z = 1.0`, `DEFAULT_CREDIBLE_BELOW`); `credible_below=None` restores the plain ranking by posterior mean. The deviation comes through the estimator seam (`Mastery.deviation`), not the estimator's private state: an estimator that does not fill it gets a `TypeError` from the gated call rather than a silently empty answer. A negative `z` is refused. The result is a list subclass, `Weakest`, whose `.reason` says why it is empty (`no_evidence` or `no_credible_weakness`), because "no credible relative weakness" is not "nothing to practise". Known limit: the global/label split comes from the priors, so part of a uniform shortfall lands on every label, and a student weak everywhere can see several labels returned; `separation()` says whether their order means anything. A second limit: the bound is per label and not corrected for testing many labels at once, so a student with no real weakness and six separable labels gets at least one label flagged more often than not; raise `z` where a false "practise this" is costly.

### 8. Cross-student pooling: never implicit; if ever wanted, an exported, versioned prior

Confirmed as the shape, and nothing is built now — it needs a population, which is outside the regime this package is designed for. When it is wanted, a population artifact has two halves with two different homes:

- **Item difficulties** already enter through the `items=` seam, as an aggregate.
- **A population prior on label deviations** (`{label: (mu, var)}`) is a prior, so it enters as **one keyword argument on the estimator, `RaschEstimator(label_priors=...)`**, replacing the constant `Skill(0, label_prior_var)` a label starts from.

Either way the artifact is produced by a deliberate export step, versioned, and reviewable — what crosses between students is visible — never a side effect of fitting.

### 9. Scope: `learny.tracing` is the learner model; the item bank is a separate package

Item-label mapping, agent tagging, inter-rater agreement, per-label resource scoring and a faceted frontend belong to an **item-bank package that does not exist yet**. The contract between them is the one `learny` already has: the bank produces a `Mapping[str, Item]`, `Item(id, labels: Sequence[str] | Mapping[str, float], difficulty: float | None)`, with label weights carrying tagging reliability. **Dependency direction:** the bank may import `learny.tracing.records.Item`; `learny` never imports the bank.

The 11+ vocabulary game assets live in the repository under `games/eleven_plus/`, outside the package, so they are not part of the distribution (they were moved out of `learny/` before any first PyPI release). Whether and when that release happens is the owner's decision.

### Calibration reporting (was "the most important next step")

Built: `LearnerModel.calibration()` / `diagnostics.calibration()` replays the log prequentially — each prediction is made from the state before its own response — and reports log loss against the know-only-the-base-rate baseline, Brier score, expected calibration error and a reliability table. Each student is replayed alone, exactly as in live use; only the scored pairs are pooled.

## Data, and the line it does not cross

`learny` is a **public** repository. Per-student responses are personal data, and the first consumers' learners include children.

- Every example, doctest and fixture in this package is **synthetic**.
- Real responses live under `~/.local/share/learny/`, never in a repository. The default store root is the policy: a store defaulting to `./data` would invite every caller to commit it.
- `LEARNY_DATA_DIR` overrides the root for tests and CI.
- One file per student, so one learner's data can be audited, handed over or deleted on its own.
- Nothing derived from a private consumer project — its data, its measurements, or its identity — belongs in this repository. Consumer-specific integration notes live in that consumer's own repository.
