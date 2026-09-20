# learny.tracing.stores

Where learner data lives, and how code reaches it.

Two stores, both plain `MutableMapping` so the backend is configuration rather than
code: swapping local JSON files for S3 (`s3dol`) or a database is an argument, not a
rewrite.

The default root is `~/.local/share/learny/` — deliberately **not** inside the package
or any app directory. Per-student responses are personal data and mutable runtime state;
a store that defaulted to `./data` would invite every caller to commit it. Override the
root for the whole package with the `LEARNY_DATA_DIR` environment variable, which is
what tests and CI should set.

### Functions

| [`data_dir`](#learny.tracing.stores.data_dir)([kind, app_name])    | The per-kind data directory, created on demand.                     |
|--------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`response_log`](#learny.tracing.stores.response_log)(\*[, rootdir])   | The default response log, under `~/.local/share/learny/responses/`. |
| [`estimate_store`](#learny.tracing.stores.estimate_store)(\*[, rootdir]) | Per-student mastery estimates, keyed by student.                    |

### Classes

| [`ResponseLog`](#learny.tracing.stores.ResponseLog)(\*[, rootdir])   | The append-only record of every response.   |
|-------------------------------------------------------------------------------|---------------------------------------------|

### *class* learny.tracing.stores.ResponseLog(, rootdir=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The append-only record of every response. The single source of truth.

One JSON-lines file per student, so one student’s data can be handed over, audited
or deleted on its own — which matters when the data is a child’s.

Append-only is not fastidiousness: the estimator *will* change, and a log that can
be replayed is what makes changing it a re-run rather than a migration.

```pycon
>>> import tempfile
>>> from learny.tracing.records import Response, Outcome
>>> log = ResponseLog(rootdir=tempfile.mkdtemp())
>>> log.append(Response('ada', 'q1', Outcome.CORRECT, at=1.0))
>>> log.append(Response('ada', 'q2', Outcome.SKIPPED, at=2.0))
>>> log.append(Response('bob', 'q1', Outcome.WRONG, at=1.5))
>>> sorted(log.students())
['ada', 'bob']
>>> [r.item for r in log['ada']]
['q1', 'q2']
>>> len(list(log))
3
```

#### append(response)

Append one response. Never rewrites or reorders what is already there.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### extend(responses)

Append many responses, grouped so each student’s file is opened once.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### students()

Every student with at least one logged response.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### learny.tracing.stores.data_dir(kind='', , app_name='learny')

The per-kind data directory, created on demand.

Resolution order: the `LEARNY_DATA_DIR` environment variable, then
`config2py.AppData` if it is installed (which gets Windows right), then the XDG
default. Data is always written under a *kind* subfolder so the root stays free for
kinds that do not exist yet.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

```pycon
>>> import tempfile, os
>>> os.environ['LEARNY_DATA_DIR'] = tmp = tempfile.mkdtemp()
>>> data_dir('responses') == Path(tmp) / 'responses'
True
>>> data_dir('responses').is_dir()
True
```

### learny.tracing.stores.estimate_store(, rootdir=None)

Per-student mastery estimates, keyed by student.

This is a **cache**. Anything in here can be thrown away and rebuilt by replaying
the response log, and the tests assert exactly that.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### learny.tracing.stores.response_log(, rootdir=None)

The default response log, under `~/.local/share/learny/responses/`.

* **Return type:**
  [`ResponseLog`](#learny.tracing.stores.ResponseLog)
