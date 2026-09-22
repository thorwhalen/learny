# learny

A Python library for learner modelling: estimating what a student knows from what
they have answered. The installed distribution is `learny.tracing` alone — the 11+
vocabulary games that used to live in the package are now plain data/a web app under
`games/`, outside the wheel (see `learny/__init__.py`).

## Module map (`learny/tracing/`)

- `model.py` — `LearnerModel`, the facade most callers touch. Owns four
  collaborators (store, estimator, diagnostics, records), each a constructor
  argument with a working default — every part is replaceable without touching
  the others.
- `estimators.py` — how one response changes belief about a student. Default is
  `RaschEstimator`: online Rasch with a Gaussian posterior, one Newton step per
  response (a Glicko-style update against an opponent of known strength).
- `records.py` — core data types (`Item`, `Outcome`, `Response`) — the vocabulary
  every other module speaks. `Response` is deliberately small/serialisable: it is
  what gets appended to the append-only response log, the system's single source
  of truth.
- `stores.py` — where learner data lives: two `MutableMapping` stores (local JSON
  files by default), so swapping in `s3dol` or a database is a keyword argument,
  not a rewrite.
- `diagnostics.py` — when to trust an estimate: calibration + how well the model
  has predicted so far, so it can say "I'm guessing" instead of guessing silently.
- `tests/` — `test_model.py`, `test_records_and_stores.py`, `test_diagnostics.py`.

## Tests & lint (verified)

```bash
uv venv .venv && uv pip install -e . pytest ruff
.venv/bin/pytest -v --tb=short --doctest-modules --ignore=games   # 122 passed
.venv/bin/ruff check .
```
Or `wads ci-local` for the full gate (Python 3.10+3.12, Windows included, doctests
gate CI — `--doctest-modules` is in `pytest_args`; `games`/`examples`/`scrap`/`docsrc`
are excluded — see `[tool.wads.ci.testing]`).

## Invariants

- **Cold start is the normal case, not an edge case** — regime is few learners
  (often exactly one), sparse responses (0-3 observations per label is typical).
  See `docs/learner-model-design.md` for the full design rationale (dated 2026-09-20).
- Designed for an *externally calibrated* item bank — difficulty often comes from
  a published source, not purely from local data.
- The response log is append-only; nothing in `tracing` rewrites history.

## Docs

- `docs/learner-model-design.md` — the v1 design decisions and their boundaries.
- `docs/research/` — background research (`multidimensional-skill-spaces.md`).

## Dependents

None recorded in the fleet dependency graph.
