"""Where learner data lives, and how code reaches it.

Two stores, both plain ``MutableMapping`` so the backend is configuration rather than
code: swapping local JSON files for S3 (``s3dol``) or a database is an argument, not a
rewrite.

The default root is ``~/.local/share/learny/`` — deliberately **not** inside the package
or any app directory. Per-student responses are personal data and mutable runtime state;
a store that defaulted to ``./data`` would invite every caller to commit it. Override the
root for the whole package with the ``LEARNY_DATA_DIR`` environment variable, which is
what tests and CI should set.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator, MutableMapping
from pathlib import Path
from typing import Any

from learny.tracing.records import Response

__all__ = ["data_dir", "response_log", "estimate_store", "ResponseLog"]

_DEFAULT_APP_NAME = "learny"


def data_dir(kind: str = "", *, app_name: str = _DEFAULT_APP_NAME) -> Path:
    """The per-kind data directory, created on demand.

    Resolution order: the ``LEARNY_DATA_DIR`` environment variable, then
    ``config2py.AppData`` if it is installed (which gets Windows right), then the XDG
    default. Data is always written under a *kind* subfolder so the root stays free for
    kinds that do not exist yet.

    >>> import tempfile, os
    >>> os.environ['LEARNY_DATA_DIR'] = tmp = tempfile.mkdtemp()
    >>> data_dir('responses') == Path(tmp) / 'responses'
    True
    >>> data_dir('responses').is_dir()
    True
    """
    root = os.environ.get("LEARNY_DATA_DIR")
    if root:
        base = Path(root)
    else:
        try:  # config2py resolves %LOCALAPPDATA% on Windows; optional, not required
            from config2py import AppData  # type: ignore

            base = Path(AppData(app_name).app_folder())
        except Exception:
            xdg = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
            base = Path(xdg) / app_name
    path = base / kind if kind else base
    path.mkdir(parents=True, exist_ok=True)
    return path


def _json_files(kind: str, *, rootdir: str | Path | None = None) -> MutableMapping:
    """A ``{name: obj}`` mapping over JSON files, via ``dol`` when available."""
    root = Path(rootdir) if rootdir is not None else data_dir(kind)
    root.mkdir(parents=True, exist_ok=True)
    try:
        from dol import JsonFiles  # type: ignore

        return JsonFiles(str(root))
    except Exception:
        return _JsonDirectory(root)


class _JsonDirectory(MutableMapping):
    """Minimal stdlib fallback with the same contract as ``dol.JsonFiles``.

    Exists so the package works with no third-party dependency at all; ``dol`` is used
    when present because it is what the rest of the ecosystem swaps backends through.
    """

    def __init__(self, rootdir: str | Path):
        self.rootdir = Path(rootdir)

    def _path(self, k: str) -> Path:
        return self.rootdir / k

    def __getitem__(self, k: str) -> Any:
        try:
            return json.loads(self._path(k).read_text())
        except FileNotFoundError:
            raise KeyError(k) from None

    def __setitem__(self, k: str, v: Any) -> None:
        self._path(k).parent.mkdir(parents=True, exist_ok=True)
        self._path(k).write_text(json.dumps(v, indent=1))

    def __delitem__(self, k: str) -> None:
        try:
            self._path(k).unlink()
        except FileNotFoundError:
            raise KeyError(k) from None

    def __iter__(self) -> Iterator[str]:
        yield from sorted(
            str(p.relative_to(self.rootdir))
            for p in self.rootdir.rglob("*")
            if p.is_file()
        )

    def __len__(self) -> int:
        return sum(1 for _ in self)


def estimate_store(*, rootdir: str | Path | None = None) -> MutableMapping:
    """Per-student mastery estimates, keyed by student.

    This is a **cache**. Anything in here can be thrown away and rebuilt by replaying
    the response log, and the tests assert exactly that.
    """
    return _json_files("estimates", rootdir=rootdir)


class ResponseLog:
    """The append-only record of every response. The single source of truth.

    One JSON-lines file per student, so one student's data can be handed over, audited
    or deleted on its own — which matters when the data is a child's.

    Append-only is not fastidiousness: the estimator *will* change, and a log that can
    be replayed is what makes changing it a re-run rather than a migration.

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
    """

    def __init__(self, *, rootdir: str | Path | None = None):
        self.rootdir = Path(rootdir) if rootdir is not None else data_dir("responses")
        self.rootdir.mkdir(parents=True, exist_ok=True)

    def _path(self, student: str) -> Path:
        safe = student.replace("/", "_")
        return self.rootdir / f"{safe}.jsonl"

    def append(self, response: Response) -> None:
        """Append one response. Never rewrites or reorders what is already there."""
        with self._path(response.student).open("a") as f:
            f.write(json.dumps(response.to_dict()) + "\n")

    def extend(self, responses: Iterable[Response]) -> None:
        """Append many responses, grouped so each student's file is opened once."""
        for response in responses:
            self.append(response)

    def students(self) -> list[str]:
        """Every student with at least one logged response."""
        return sorted(p.stem for p in self.rootdir.glob("*.jsonl"))

    def __getitem__(self, student: str) -> list[Response]:
        """Every response by one student, in the order they were logged."""
        path = self._path(student)
        if not path.exists():
            raise KeyError(student)
        return [
            Response.from_dict(json.loads(line))
            for line in path.read_text().splitlines()
            if line.strip()
        ]

    def __iter__(self) -> Iterator[Response]:
        """Every response by every student."""
        for student in self.students():
            yield from self[student]

    def __len__(self) -> int:
        return sum(1 for _ in self)


def response_log(*, rootdir: str | Path | None = None) -> ResponseLog:
    """The default response log, under ``~/.local/share/learny/responses/``."""
    return ResponseLog(rootdir=rootdir)
