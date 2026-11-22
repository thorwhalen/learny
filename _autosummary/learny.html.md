# learny

Turn learning into play — build knowledge with joy.

`learny` is a Python library for learner modelling: estimating what a student
knows from what they have answered.

## Sub-packages

`learny.tracing`
: A per-student learner model whose priors update from that student’s own
  data. Start with [`LearnerModel`](learny.tracing.model.html.md#learny.tracing.model.LearnerModel).

`learny.scheduling` and `learny.distractors`
: Which item to ask next and which options to show with it, read from the
  same response log: Leitner, SM-2, FSRS-lite, confusion-weighted and
  weakest-label strategies, and distractors drawn from what the learner
  confuses. Start with [`make_strategy()`](learny.scheduling.html.md#learny.scheduling.make_strategy).

The 11+ vocabulary games that used to live here (word lists, game parameters
and a quiz front-end) are plain data and a web app, not Python API. They are
kept in the repository under `games/`, outside this package, so they are not
part of the installed distribution.

The installed distribution is the library alone; `tracing` is its only
sub-package (the other two are modules):

```pycon
>>> from pathlib import Path
>>> import learny
>>> pkg_dir = Path(learny.__file__).parent
>>> sorted(p.name for p in pkg_dir.iterdir()
...        if p.is_dir() and (p / '__init__.py').exists())
['tracing']
```

### Modules

| [`distractors`](learny.distractors.html.md#module-learny.distractors)   | Which wrong options to show beside the right one, from what the learner confuses.   |
|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| [`scheduling`](learny.scheduling.html.md#module-learny.scheduling)     | Which item to ask next, and which options to show with it, from the response log.   |
| [`tracing`](learny.tracing.html.md#module-learny.tracing)           | Learner modelling: what a student knows, estimated from what they have answered.    |
