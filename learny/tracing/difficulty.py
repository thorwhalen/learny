"""Explanatory item difficulty: which item features make an item hard.

An item bank often carries features of every item — how many glyphs it has, how
irregular its rhythm is, how frequent its words are — and a hypothesis that some of
them drive difficulty. :func:`fit_feature_difficulty` tests that hypothesis against
play. It fits the Linear Logistic Test Model (Fischer 1973) with a residual per item
(the random-item extension of De Boeck 2008)::

    logit P(correct) = ability[student] - difficulty[item]
    difficulty[item] = intercept + weights . features[item] + residual[item]

with Gaussian priors on every parameter, by maximum a posteriori and a Laplace
approximation, so each weight comes with a standard deviation: which features matter,
and how sure the fit is. The result predicts the difficulty of an item nobody has
played yet from its features alone, which is the cold start for a new item.

This is the one place in :mod:`learny.tracing` that reads *across* students, so it
follows the rule for that (decision 8 in ``docs/learner-model-design.md``): it runs
only when called, over a log it is handed, and what it learns leaves as an exported,
reviewable artifact (:class:`FeatureDifficulty`, JSON by :meth:`~FeatureDifficulty.to_dict`)
that enters the learner model through the existing ``items=`` seam
(:meth:`~FeatureDifficulty.apply`), never as a side effect of fitting.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, NamedTuple

from learny.tracing.estimators import expit
from learny.tracing.records import Item, Response

__all__ = ["Estimate", "FeatureDifficulty", "fit_feature_difficulty", "item_features"]

#: The tag :meth:`FeatureDifficulty.to_dict` writes, so a stored artifact says what it is.
_SCHEMA = "learny.feature_difficulty/1"

#: The empirical-Bayes residual variance: where EM starts, the floor that keeps it off
#: zero (where the residuals would be pinned to the features and the fit could not
#: recover), and the relative change at which it is taken as converged.
_TAU2_START, _TAU2_FLOOR, _TAU2_TOL = 0.5, 1e-4, 1e-4


class Estimate(NamedTuple):
    """A posterior mean and standard deviation, on the logit scale."""

    mean: float
    sd: float


def item_features(item: Item) -> Mapping[str, float] | None:
    """The default feature source: ``item.meta['features']``, or ``None``.

    >>> item_features(Item('q', meta={'features': {'n_glyphs': 4}}))
    {'n_glyphs': 4}
    >>> item_features(Item('q')) is None
    True
    """
    return item.meta.get("features")


@dataclass(frozen=True)
class FeatureDifficulty:
    """A fitted explanatory difficulty model; see :func:`fit_feature_difficulty`.

    Features are stored standardised (``(x - center) / scale`` over the fitted items),
    which is what the priors and the covariance refer to; :meth:`weights` reports them
    in each feature's own units. ``covariance`` is over ``(intercept, *weights)`` in the
    standardised form. ``residuals`` are the fitted items' own departures from what their
    features predict, and ``residual_var`` the prior variance of a new item's.
    """

    names: tuple[str, ...]
    center: tuple[float, ...]
    scale: tuple[float, ...]
    coef: tuple[float, ...]  # (intercept, *standardised weights)
    covariance: tuple[tuple[float, ...], ...]
    residual_var: float
    residuals: Mapping[str, float] = field(default_factory=dict)
    n_students: int = 0
    n_responses: int = 0

    def weights(self) -> dict[str, Estimate]:
        """Each feature's weight in logits of difficulty per unit of the feature.

        Positive: more of the feature makes an item harder. The sd is the weight's
        posterior sd; a weight within about two of zero is not distinguishable from
        "this feature does not matter".
        """
        return {
            name: Estimate(self.coef[1 + f] / self.scale[f],
                           math.sqrt(self.covariance[1 + f][1 + f]) / self.scale[f])
            for f, name in enumerate(self.names)
        }

    def _row(self, features: Mapping[str, float]) -> list[float]:
        missing = [name for name in self.names if name not in features]
        if missing:
            raise KeyError(f"features {missing!r} are missing; the model needs {list(self.names)!r}")
        return [1.0] + [
            (float(features[name]) - c) / s
            for name, c, s in zip(self.names, self.center, self.scale)
        ]

    def predict(self, features: Mapping[str, float], *, item_id: str | None = None) -> Estimate:
        """The difficulty, in logits, of an item with these features.

        For an item the model was fitted on (``item_id`` among its ``residuals``) the
        mean includes that item's own residual and the sd is the features' part alone;
        for any other item the residual is unknown, so its prior variance is added.
        """
        h = self._row(features)
        mean = sum(c * x for c, x in zip(self.coef, h))
        var = sum(h[a] * self.covariance[a][b] * h[b] for a in range(len(h)) for b in range(len(h)))
        if item_id is not None and item_id in self.residuals:
            mean += self.residuals[item_id]
        else:
            var += self.residual_var
        return Estimate(mean, math.sqrt(max(var, 0.0)))

    def apply(
        self,
        items: Mapping[str, Item],
        *,
        features: Mapping[str, Mapping[str, float]] | None = None,
        overwrite: bool = False,
    ) -> dict[str, Item]:
        """A copy of ``items`` with each item's ``difficulty`` predicted from features.

        Only items without a difficulty are filled unless ``overwrite=True``; an item
        with no features is left as it is. The result is an item bank for the ``items=``
        seam of :class:`~learny.tracing.model.LearnerModel`.
        """
        out = dict(items)
        for key, item in items.items():
            if item.difficulty is not None and not overwrite:
                continue
            x = _features_of(item, features)
            if x is None:
                continue
            out[key] = replace(item, difficulty=expit(self.predict(x, item_id=item.id).mean))
        return out

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict: the artifact to store, version and review."""
        return {
            "schema": _SCHEMA,
            "names": list(self.names),
            "center": list(self.center),
            "scale": list(self.scale),
            "coef": list(self.coef),
            "covariance": [list(row) for row in self.covariance],
            "residual_var": self.residual_var,
            "residuals": dict(self.residuals),
            "n_students": self.n_students,
            "n_responses": self.n_responses,
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "FeatureDifficulty":
        """Inverse of :meth:`to_dict`; refuses an artifact of another schema."""
        if d.get("schema") != _SCHEMA:
            raise ValueError(f"not a {_SCHEMA} artifact (schema {d.get('schema')!r})")
        return cls(
            names=tuple(d["names"]),
            center=tuple(d["center"]),
            scale=tuple(d["scale"]),
            coef=tuple(d["coef"]),
            covariance=tuple(tuple(row) for row in d["covariance"]),
            residual_var=float(d["residual_var"]),
            residuals=dict(d.get("residuals", {})),
            n_students=int(d.get("n_students", 0)),
            n_responses=int(d.get("n_responses", 0)),
        )


def _features_of(
    item: Item, features: Mapping[str, Mapping[str, float]] | None
) -> Mapping[str, float] | None:
    if features is not None:
        return features.get(item.id)
    return item_features(item)


def _cholesky_inverse(a: list[list[float]]) -> list[list[float]]:
    """The inverse of a symmetric positive definite matrix, by Cholesky."""
    n = len(a)
    low = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = a[i][j] - sum(low[i][k] * low[j][k] for k in range(j))
            if i == j:
                if s <= 0.0:
                    raise ArithmeticError("the posterior precision is not positive definite")
                low[i][i] = math.sqrt(s)
            else:
                low[i][j] = s / low[j][j]
    inv_low = [[0.0] * n for _ in range(n)]  # L^-1, lower triangular
    for i in range(n):
        inv_low[i][i] = 1.0 / low[i][i]
        for j in range(i):
            inv_low[i][j] = -sum(low[i][k] * inv_low[k][j] for k in range(j, i)) / low[i][i]
    return [  # (L L')^-1 = L^-T L^-1
        [sum(inv_low[k][i] * inv_low[k][j] for k in range(max(i, j), n)) for j in range(n)]
        for i in range(n)
    ]


def fit_feature_difficulty(
    log: Mapping[str, Iterable[Response]],
    *,
    items: Mapping[str, Item],
    features: Mapping[str, Mapping[str, float]] | None = None,
    students: Iterable[str] | None = None,
    ability_prior_var: float = 1.0,
    weight_prior_var: float = 1.0,
    intercept_prior_var: float = 4.0,
    residual_var: float | None = None,
    max_iter: int = 100,
    tol: float = 1e-9,
) -> FeatureDifficulty:
    """Fit which item features predict difficulty, from a log of play.

    ``features`` maps an item id to ``{name: value}``; by default each item's
    ``meta['features']`` (:func:`item_features`). Every item answered in the log needs a
    value for every feature named anywhere, or the fit is refused rather than guessed.
    A right/wrong response counts as one trial, a score ``k`` out of ``max_score`` as
    ``k`` successes in ``max_score`` trials (the binomial reading that
    :func:`~learny.tracing.estimators.binomial_thresholds` gives a score); skips are not
    evidence about difficulty and are left out. Each student has one ability over the
    whole log: learning during the log is not modelled, so fit on a window short enough
    for ability to be roughly constant. Guessing is not modelled either.

    The priors, all Gaussian and centred on zero, are the keyword arguments. Weights
    are per *standard deviation* of each feature across the fitted items, so
    ``weight_prior_var=1`` says a one-sd change in a feature plausibly moves difficulty
    by up to a logit or two, whatever its units. ``residual_var`` is how far an item may
    sit from what its features predict. Left ``None`` it is estimated from the log
    (empirical Bayes, by EM), which is what keeps the weights' sds honest: fixed below
    the truth (0.25 where it is 1.0), 95% intervals covered the true weights 80% of the
    time; estimated, 93-97%, and a new item's 90-95%. With around 15 responses per item
    the estimate runs about 20% low, as Laplace estimates of a variance component do
    on right/wrong data (``docs/learner-model-design.md``, decision 13).

    >>> import random
    >>> rng = random.Random(0)
    >>> bank = {f'q{i}': Item(f'q{i}', meta={'features': {'length': i % 6}}) for i in range(30)}
    >>> log = {}
    >>> for s in range(20):
    ...     theta = rng.gauss(0, 1)
    ...     log[f's{s}'] = [
    ...         Response(f's{s}', q, rng.random() < expit(theta - (0.6 * bank[q].meta['features']['length'] - 1.5)))
    ...         for q in bank]
    >>> model = fit_feature_difficulty(log, items=bank)
    >>> w = model.weights()['length']
    >>> abs(w.mean - 0.6) < 2 * w.sd, w.mean > 2 * w.sd   # recovered, and it matters
    (True, True)
    >>> model.predict({'length': 5}).mean > model.predict({'length': 0}).mean
    True
    """
    checked = [("ability_prior_var", ability_prior_var),
               ("weight_prior_var", weight_prior_var),
               ("intercept_prior_var", intercept_prior_var)]
    if residual_var is not None:
        checked.append(("residual_var", residual_var))
    for name, value in checked:
        if not (isinstance(value, (int, float)) and value > 0 and math.isfinite(value)):
            raise ValueError(f"{name} must be a positive number, got {value!r}")

    # -- the data: (student, item, successes, trials) ---------------------------------
    names_of_students = list(students) if students is not None else (
        log.students() if hasattr(log, "students") else list(log)
    )
    rows: list[tuple[int, int, int, int]] = []
    item_index: dict[str, int] = {}
    no_bank, no_features = set(), set()
    feats: list[Mapping[str, float]] = []
    student_index: dict[str, int] = {}
    for name in names_of_students:
        for r in log[name]:
            if not r.outcome.is_scored:
                continue
            item = items.get(r.item)
            if item is None:
                no_bank.add(r.item)
                continue
            x = _features_of(item, features)
            if x is None:
                no_features.add(r.item)
                continue
            if r.item not in item_index:
                item_index[r.item] = len(item_index)
                feats.append(x)
            k, m = (r.score, r.max_score) if r.score is not None else (int(r.correct), 1)
            p = student_index.setdefault(name, len(student_index))
            rows.append((p, item_index[r.item], k, m))
    for missing, what in ((no_bank, "not in items"), (no_features, "without features")):
        if missing:
            shown = sorted(missing)[:5]
            raise ValueError(
                f"{len(missing)} answered item(s) {what}, e.g. {shown!r}: pass features= "
                "or restrict the log to items that have them"
            )
    if not rows:
        raise ValueError("the log has no scored responses to fit")
    names = tuple(sorted({n for x in feats for n in x}))
    incomplete = [iid for iid, x in zip(item_index, feats) if any(n not in x for n in names)]
    if incomplete:
        raise ValueError(
            f"{len(incomplete)} item(s) lack a value for some feature, e.g. "
            f"{incomplete[:5]!r}; every item needs all of {list(names)!r}"
        )

    # -- standardise the features over the fitted items -------------------------------
    n_items, n_feat = len(item_index), len(names)
    raw = [[float(x[n]) for n in names] for x in feats]
    center, scale = [], []
    for f, name in enumerate(names):
        col = [row[f] for row in raw]
        mu = sum(col) / n_items
        sd = math.sqrt(sum((v - mu) ** 2 for v in col) / n_items)
        if not sd > 0:
            raise ValueError(
                f"feature {name!r} has the same value on every fitted item, so it cannot be "
                "told apart from the intercept; drop it or fit on more varied items"
            )
        center.append(mu)
        scale.append(sd)
    z = [[(row[f] - center[f]) / scale[f] for f in range(n_feat)] for row in raw]

    # -- MAP by Newton, the item residuals eliminated by Schur complement -------------
    n_stud = len(student_index)
    g_dim = n_stud + 1 + n_feat  # (abilities, intercept, weights); residuals apart
    prior = [1.0 / ability_prior_var] * n_stud + [1.0 / intercept_prior_var] + [
        1.0 / weight_prior_var
    ] * n_feat
    theta = [0.0] * g_dim
    resid = [0.0] * n_items
    by_item: dict[int, list[tuple[int, int, int]]] = {}
    for p, i, k, m in rows:
        by_item.setdefault(i, []).append((p, k, m))

    def item_coords(i: int) -> list[tuple[int, float]]:
        # d(eta)/d(param) for the global params of an item, apart from the ability
        return [(n_stud, -1.0)] + [(n_stud + 1 + f, -z[i][f]) for f in range(n_feat)]

    def newton(tau2: float) -> tuple[list[list[float]], list[float], list[float]]:
        """Run Newton to the mode at residual variance ``tau2``; return the global
        params' covariance and each residual's posterior variance and mean square."""
        nonlocal theta, resid
        for _ in range(max_iter):
            grad = [-prior[a] * theta[a] for a in range(g_dim)]
            hess = [[0.0] * g_dim for _ in range(g_dim)]
            for a in range(g_dim):
                hess[a][a] = prior[a]
            grad_e = [-resid[i] / tau2 for i in range(n_items)]
            d_e = [1.0 / tau2] * n_items
            b_cols: list[dict[int, float]] = []
            for i in range(n_items):
                coords = item_coords(i)
                b_i = theta[n_stud] + sum(theta[n_stud + 1 + f] * z[i][f] for f in range(n_feat))
                col: dict[int, float] = {}
                for p, k, m in by_item.get(i, ()):
                    q = expit(theta[p] - b_i - resid[i])
                    r, c = k - m * q, m * q * (1.0 - q)
                    g = [(p, 1.0)] + coords
                    for a, ga in g:
                        grad[a] += r * ga
                        for b, gb in g:
                            hess[a][b] += c * ga * gb
                        col[a] = col.get(a, 0.0) - c * ga  # cross term with the residual
                    grad_e[i] -= r
                    d_e[i] += c
                b_cols.append(col)
            # Schur complement onto the global params: S = A - sum_i b_i b_i' / d_i
            rhs = grad[:]
            for i, col in enumerate(b_cols):
                inv = 1.0 / d_e[i]
                for a, va in col.items():
                    rhs[a] -= va * inv * grad_e[i]
                    for b, vb in col.items():
                        hess[a][b] -= va * vb * inv
            cov = _cholesky_inverse(hess)
            step = [sum(cov[a][b] * rhs[b] for b in range(g_dim)) for a in range(g_dim)]
            step_e = [
                (grad_e[i] - sum(v * step[a] for a, v in b_cols[i].items())) / d_e[i]
                for i in range(n_items)
            ]
            theta = [t + d for t, d in zip(theta, step)]
            resid = [e + d for e, d in zip(resid, step_e)]
            if max(abs(d) for d in step + step_e) < tol:
                break
        # Var(residual_i) from the block inverse: 1/d_i + b_i' S^-1 b_i / d_i^2
        var_e = [
            1.0 / d_e[i] + sum(
                va * cov[a][b] * vb for a, va in col.items() for b, vb in col.items()
            ) / d_e[i] ** 2
            for i, col in enumerate(b_cols)
        ]
        return cov, var_e, [e * e for e in resid]

    if residual_var is not None:
        tau2 = float(residual_var)
        covariance, _, _ = newton(tau2)
    else:
        # Empirical Bayes by EM: tau2 <- mean of E[residual^2] at the current mode.
        tau2 = _TAU2_START
        for _ in range(max_iter):
            covariance, var_e, sq = newton(tau2)
            new_tau2 = max(sum(v + q for v, q in zip(var_e, sq)) / n_items, _TAU2_FLOOR)
            if abs(new_tau2 - tau2) < _TAU2_TOL * tau2:
                tau2 = new_tau2
                break
            tau2 = new_tau2
        covariance, _, _ = newton(tau2)

    lo = n_stud
    return FeatureDifficulty(
        names=names,
        center=tuple(center),
        scale=tuple(scale),
        coef=tuple(theta[lo:]),
        covariance=tuple(tuple(row[lo:]) for row in covariance[lo:]),
        residual_var=tau2,
        residuals={iid: resid[i] for iid, i in item_index.items()},
        n_students=n_stud,
        n_responses=len(rows),
    )
