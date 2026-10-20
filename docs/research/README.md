# Research

Point-in-time landscape studies behind `learny`'s design. They **date**: each
carries the date it was researched, and library versions, prices and
platform-policy claims need re-verifying after a few months.

Each report separates what was read in full from what was reached only as an
abstract or a secondary source, and says so in place rather than asserting a
uniform confidence it does not have.

| File | What it covers |
|---|---|
| [`multidimensional-skill-spaces.md`](multidimensional-skill-spaces.md) | What happens when a curriculum has several ordered dimensions at once. Knowledge Space Theory and learning spaces; the Q-matrix / cognitive-diagnostic-model mirror; whether mastery propagates down a product order; how the combinatorial explosion actually behaves; and the four separate literatures that partially cover "temporarily simplify one dimension while advancing another". Includes the substantial negative evidence on prerequisite-driven sequencing. |
| [`symbol-introduction-order.md`](symbol-introduction-order.md) | The order and step size in which to introduce a set of symbols (katakana as the first case). Cumulative versus split-then-merge, interleaving, symbols per step, look-alikes and diacritic pairs, songs; the algorithms for choosing a symbol subset that spells the most words (densest k-subhypergraph, set-union knapsack) and for ordering subsets (minimum-latency set cover); and what an optimised order did on a 3,700-word katakana loanword lexicon. |
| [`learning-game-patterns.md`](learning-game-patterns.md) | A pattern language for games that teach symbols and vocabulary. Six axes (family, pattern, pressure, feedback, progression, wrapper); ten learning families; six matching patterns and how the timer, falling-object and overflow-box variants sit on them; nine pressure renderings; a phase ladder; and what each pattern must log for the learner model. Evidence is by component: no study compares matching forms. A distilled skill is in [`../../skills/learning-game-patterns/`](../../skills/learning-game-patterns/SKILL.md). |
| [`weakest-update-difficulty-mismatch.md`](weakest-update-difficulty-mismatch.md) | A measurement, not a survey: how `weakest(multiplicity="simulated")` behaves with `RaschEstimator(update_difficulty=True)`, whose null redrew at learned difficulties while each replay relearns them from the prior. False-flag rate and power on the calibration sims for that behaviour and the two ways to remove the mismatch, with the script that reproduces them; the `prior_redraw` fix shipped in #48. |
