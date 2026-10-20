# The `update_difficulty` replay mismatch of `weakest(multiplicity="simulated")`

Measured 2026-10-20 for [#46](https://github.com/thorwhalen/learny/issues/46). Synthetic students only; reproduce with [`weakest_update_difficulty_mismatch.py`](weakest_update_difficulty_mismatch.py) (`--students 300 --draws 200`, about an hour on two cores).

## The question

Before [#48](https://github.com/thorwhalen/learny/issues/48), with `RaschEstimator(update_difficulty=True)`, the simulated null redraws every answer at the difficulties the student's state *ended* with, while each replay starts from `init()` and relearns them from the prior on the redrawn answers. Does that mismatch move the false-flag rate off its target (`1 - Phi(1)`, about 0.159, at the default `credible_below=1`)?

## What was compared

On the cells of `learny/tracing/tests/test_weakest_calibration.py`, with the same students for every variant (common random numbers):

- `fixed`: `update_difficulty=False`, the default estimator, as the reference;
- `current`: `update_difficulty=True` as shipped (the mismatch);
- `prior_redraw`: the redraw uses the prior difficulties, the ones each replay starts from;
- `seeded_replay`: each replay starts from the learned difficulties the redraw uses.

`false` is the share of students with no real weakness for whom `weakest` returns anything; `power` is the share of students with a real weakness of -2 logits on `l0` for whom `l0` is returned. 300 students per cell, `null_draws=200`; the Monte Carlo sd of a rate near 0.159 is 0.021.

## Results

| labels | responses | difficulty | skip | false: fixed | false: current | false: prior_redraw | false: seeded_replay | power: fixed | power: current | power: prior_redraw | power: seeded_replay |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 18 | 0.5 | 0 | 0.190 | 0.090 | 0.213 | 0.160 | 0.443 | 0.263 | 0.400 | 0.353 |
| 6 | 60 | 0.5 | 0 | 0.187 | 0.070 | 0.183 | 0.147 | 0.617 | 0.330 | 0.483 | 0.460 |
| 3 | 9 | 0.05 | 0 | 0.113 | 0.100 | 0.113 | 0.037 | 0.347 | 0.283 | 0.323 | 0.210 |
| 20 | 40 | 0.05 | 0 | 0.120 | 0.113 | 0.113 | 0.067 | 0.063 | 0.060 | 0.057 | 0.070 |
| 6 | 60 | 0.5 | 0.3 | 0.173 | 0.103 | 0.137 | 0.150 | 0.483 | 0.353 | 0.380 | 0.393 |
| 10 | 10 | 0.03 | 0 | 0.110 | 0.110 | 0.110 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Reading

- **The mismatch is conservative, not anti-conservative.** `current` flags a student with no weakness at 0.07 to 0.11 where the target is 0.159 and `fixed` gives 0.11 to 0.19. It never over-flags, so it is not a correctness bug in the direction that loses trust.
- **It costs power.** Where items are answered at about even odds, `current` finds the real weakness much less often than the reference (0.26 against 0.44 at 3 labels and 18 answers, 0.33 against 0.62 at 6 and 60). Part of that is inherent to `update_difficulty` with one item per label: the item's learned difficulty absorbs part of the label's shortfall, so no null can give it back.
- **Redrawing at the prior difficulties (`prior_redraw`) removes the mismatch best.** Its false-flag rate tracks the reference in every cell (0.11 to 0.21, against 0.11 to 0.19), and it recovers most of the lost power (0.40 and 0.48 in the two cells above). Its 0.213 at 3 labels and 18 answers is 2.6 Monte Carlo sd above target, but the reference itself is at 0.190 there.
- **Seeding the replay with the learned difficulties (`seeded_replay`) over-corrects.** It is close to target at even odds but strongly conservative where answers are skewed (0.037 and 0.000 at difficulty 0.05 and 0.03), with the least power there.
- Where items are nearly always answered right (difficulty 0.05 or 0.03), all variants agree with each other and with the reference: the learned difficulties barely move from the prior, so the mismatch does not matter there.

## Recommendation

Change nothing in the direction of safety (the shipped behaviour never over-flags). If the power lost with `update_difficulty=True` matters, make `null_response` redraw at the prior difficulty (the item's own `difficulty`, ignoring `state["items"]`) when the estimator co-estimates difficulty, which is `prior_redraw` above. That change is tracked separately so this measurement lands on its own.

**Done in [#48](https://github.com/thorwhalen/learny/issues/48):** `null_response` now redraws at the difficulty each replay starts from, which with `update_difficulty=True` is the prior. The shipped behaviour is `prior_redraw` above; the script reproduces the old one as `current`. `test_weakest_calibration.py` checks it at `update_difficulty=True` (`TestSimulatedGateWithUpdateDifficulty`).
