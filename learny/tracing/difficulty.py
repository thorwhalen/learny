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
import warnings
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from numbers import Real
from typing import Any, Literal, NamedTuple

from learny.tracing.estimators import expit, logit
from learny.tracing.records import Item, Response

__all__ = [
    "Estimate",
    "FeatureDifficulty",
    "attempt_features",
    "fit_feature_difficulty",
    "item_features",
]

Anchor = Literal["location", "exact", "none"]
_ANCHORS = ("location", "exact", "none")

#: The tag :meth:`FeatureDifficulty.to_dict` writes, so a stored artifact says what it is.
_SCHEMA = "learny.feature_difficulty/2"

#: Empirical-Bayes variances: where EM starts, the floor that keeps one off zero (where
#: it could not recover), and the change, relative to the variance plus a negligible
#: one (0.01 logit², where EM would otherwise crawl toward zero), taken as converged.
_VAR_START, _VAR_FLOOR, _EM_TOL, _EM_NEGLIGIBLE = 0.5, 1e-4, 1e-2, 0.01
#: The ability prior variance when there are too few students to estimate it: the
#: default estimator's own (``RaschEstimator.prior_var``).
_ABILITY_VAR_DEFAULT = 1.0


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


def attempt_features(response: Response) -> Mapping[str, float] | None:
    """The default per-attempt feature source: ``response.meta['features']``, or ``None``.

    These describe how one attempt was set up (``n_decoys``, a mix with vocals), so the
    same item can be harder on one attempt than on another.

    >>> attempt_features(Response('s', 'q', True, meta={'features': {'n_decoys': 3}}))
    {'n_decoys': 3}
    >>> attempt_features(Response('s', 'q', True)) is None
    True
    """
    return response.meta.get("features")


@dataclass(frozen=True)
class FeatureDifficulty:
    """A fitted explanatory difficulty model; see :func:`fit_feature_difficulty`.

    Features are stored standardised (``(x - center) / scale`` over the fitted items),
    which is what the priors and the covariance refer to; :meth:`weights` reports them
    in each feature's own units. ``covariance`` is over ``(intercept, *weights)`` in the
    standardised form. ``residual_var`` is the prior variance of a new item's departure
    from what its features predict, ``ability_mean`` and ``ability_var`` the fitted
    students' ability distribution, on the scale of the bank's given difficulties when
    the fit was anchored on them. ``residuals`` holds each fitted item's own departure,
    as ``(mean, variance, *covariance with the coefficients)``; it carries the fitted
    students' data, so :meth:`apply` leaves it out unless asked. ``converged`` is false
    when an iteration cap was hit (a ``RuntimeWarning`` said so at fit time).

    Per-attempt features (``attempt_names``, standardised over the fitted attempts by
    ``attempt_center`` and ``attempt_scale``) add their weights after the item weights,
    so ``coef`` and ``covariance`` are over ``(intercept, *weights, *attempt weights)``;
    :meth:`attempt_weights` reports them. They have no residual: an attempt's setup
    moves the difficulty of whatever item it is played with by its weights alone.
    """

    names: tuple[str, ...]
    center: tuple[float, ...]
    scale: tuple[float, ...]
    coef: tuple[float, ...]  # (intercept, *standardised weights)
    covariance: tuple[tuple[float, ...], ...]
    residual_var: float
    ability_mean: float = 0.0
    ability_var: float = 1.0
    residuals: Mapping[str, tuple[float, ...]] = field(default_factory=dict)
    anchors: int = 0
    n_students: int = 0
    n_responses: int = 0
    converged: bool = True
    attempt_names: tuple[str, ...] = ()
    attempt_center: tuple[float, ...] = ()
    attempt_scale: tuple[float, ...] = ()

    def weights(self) -> dict[str, Estimate]:
        """Each feature's weight in logits of difficulty per unit of the feature.

        Positive: more of the feature makes an item harder. The sd is the weight's
        posterior sd; a weight within about two of zero is not distinguishable from
        "this feature does not matter". Two features that move together split their
        weight between them, each with a wide sd.
        """
        return {
            name: Estimate(self.coef[1 + f] / self.scale[f],
                           math.sqrt(self.covariance[1 + f][1 + f]) / self.scale[f])
            for f, name in enumerate(self.names)
        }

    def attempt_weights(self) -> dict[str, Estimate]:
        """Each per-attempt feature's weight, as :meth:`weights` reports the item ones."""
        first = 1 + len(self.names)
        return {
            name: Estimate(self.coef[first + f] / self.attempt_scale[f],
                           math.sqrt(self.covariance[first + f][first + f]) / self.attempt_scale[f])
            for f, name in enumerate(self.attempt_names)
        }

    def _row(
        self, features: Mapping[str, float], attempt: Mapping[str, float] | None = None
    ) -> list[float]:
        h = [1.0] + _standardised(features, self.names, self.center, self.scale)
        if attempt is None:  # the average attempt: every standardised value at 0
            return h + [0.0] * len(self.attempt_names)
        return h + _standardised(
            attempt, self.attempt_names, self.attempt_center, self.attempt_scale, what="attempt features"
        )

    def predict(
        self,
        features: Mapping[str, float],
        *,
        attempt: Mapping[str, float] | None = None,
        item_id: str | None = None,
    ) -> Estimate:
        """The difficulty, in logits, of an item with these features.

        For any item the residual is unknown, so its prior variance ``residual_var`` is
        added to the features' part. Pass ``item_id`` of an item the model was fitted on
        to use that item's own fitted residual instead, with its posterior variance and
        its covariance with the coefficients. Features far outside the fitted range are
        extrapolated linearly, without warning.

        ``attempt`` gives the per-attempt features of one way of playing the item (a new
        song with 3 decoys); left ``None``, the attempt is the fitted attempts' average.
        """
        h = self._row(features, attempt)
        n = len(h)
        mean = sum(c * x for c, x in zip(self.coef, h))
        var = sum(h[a] * self.covariance[a][b] * h[b] for a in range(n) for b in range(n))
        own = self.residuals.get(item_id) if item_id is not None else None
        if own is None:
            var += self.residual_var
        else:
            r_mean, r_var, *r_cov = own
            mean += r_mean
            var += r_var + 2.0 * sum(x * c for x, c in zip(h, r_cov))
        return Estimate(mean, math.sqrt(max(var, 0.0)))

    def apply(
        self,
        items: Mapping[str, Item],
        *,
        features: Mapping[str, Mapping[str, float]] | None = None,
        overwrite: bool = False,
        use_residuals: bool = False,
    ) -> dict[str, Item]:
        """A copy of ``items`` with each item's ``difficulty`` predicted from features.

        Only items without a difficulty are filled unless ``overwrite=True``; an item
        with no features is left as it is, and per-attempt features are taken at the
        fitted attempts' average. The difficulty comes from the features alone
        unless ``use_residuals=True`` adds each fitted item's own residual. That residual
        is learned from the fitted students' answers, so feeding it back to estimate
        those same students counts their answers twice; with one or two learners it is
        mostly their own results (#18 review). The result is an item bank for the
        ``items=`` seam of :class:`~learny.tracing.model.LearnerModel`.
        """
        out = dict(items)
        for key, item in items.items():
            if item.difficulty is not None and not overwrite:
                continue
            x = _features_of(key, item, features)
            if x is None:
                continue
            est = self.predict(x, item_id=key if use_residuals else None)
            out[key] = replace(item, difficulty=expit(est.mean))
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
            "ability_mean": self.ability_mean,
            "ability_var": self.ability_var,
            "residuals": {k: list(v) for k, v in self.residuals.items()},
            "anchors": self.anchors,
            "n_students": self.n_students,
            "n_responses": self.n_responses,
            "converged": self.converged,
            "attempt_names": list(self.attempt_names),
            "attempt_center": list(self.attempt_center),
            "attempt_scale": list(self.attempt_scale),
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
            ability_mean=float(d.get("ability_mean", 0.0)),
            ability_var=float(d.get("ability_var", 1.0)),
            residuals={k: tuple(v) for k, v in d.get("residuals", {}).items()},
            anchors=int(d.get("anchors", 0)),
            n_students=int(d.get("n_students", 0)),
            n_responses=int(d.get("n_responses", 0)),
            converged=bool(d.get("converged", True)),
            attempt_names=tuple(d.get("attempt_names", ())),
            attempt_center=tuple(d.get("attempt_center", ())),
            attempt_scale=tuple(d.get("attempt_scale", ())),
        )


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"feature {name!r} must be a finite number, got {value!r}")
    return float(value)


def _standardised(features, names, center, scale, *, what="features") -> list[float]:
    missing = [name for name in names if name not in features]
    if missing:
        raise KeyError(f"{what} {missing!r} are missing; the model needs {list(names)!r}")
    values = [_number(features[name], name) for name in names]
    return [(v - c) / s for v, c, s in zip(values, center, scale)]


def _center_and_scale(raw: list[list[float]], names, *, over: str):
    """Each column's mean and sd; a column constant over the fitted rows is refused."""
    center, scale = [], []
    for f, name in enumerate(names):
        col = [row[f] for row in raw]
        mu = sum(col) / len(col)
        sd = math.sqrt(sum((v - mu) ** 2 for v in col) / len(col))
        if not sd > 1e-12 * (1.0 + abs(mu)):
            raise ValueError(
                f"feature {name!r} has the same value on every fitted {over}, so it cannot be "
                f"told apart from the intercept; drop it or fit on more varied {over}s"
            )
        center.append(mu)
        scale.append(sd)
    return center, scale


def _features_of(
    key: str, item: Item, features: Mapping[str, Mapping[str, float]] | None
) -> Mapping[str, float] | None:
    if features is not None:
        return features.get(key)
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


def _shift_to_anchors(coef, covariance, residuals, published, h_of, keys):
    """Move the intercept so the anchors' fitted difficulties average their given ones.

    With ``A`` the anchors, ``hbar`` their mean feature row and ``ebar`` their mean
    residual, the new intercept is ``mean(given) - sum_f hbar_f w_f - ebar``: a linear
    map of the fitted coefficients and residuals, so the covariance follows exactly,
    except that residual-residual covariances between anchors (not kept) are taken as 0.
    Returns the new ``(coef, covariance, residuals, shift)``.
    """
    n_coef = len(coef)
    idx = list(published)
    n = len(idx)
    hbar = [sum(h_of[i][c] for i in idx) / n for c in range(n_coef)]
    own = [residuals[keys[i]] for i in idx]  # (mean, var, *cov with coef)
    ebar = sum(r[0] for r in own) / n
    cov_c_ebar = [sum(r[2 + c] for r in own) / n for c in range(n_coef)]
    var_ebar = sum(r[1] for r in own) / n**2
    fitted_mean = sum(hbar[c] * coef[c] for c in range(n_coef)) + ebar
    shift = sum(published.values()) / n - fitted_mean
    # new = M coef - u0 * ebar + const, with M = identity except row 0 = (0, -hbar_1..)
    m_rows = [[0.0] + [-hbar[c] for c in range(1, n_coef)]] + [
        [1.0 if c == r else 0.0 for c in range(n_coef)] for r in range(1, n_coef)
    ]

    def m_times(v):
        return [sum(m_rows[r][c] * v[c] for c in range(n_coef)) for r in range(n_coef)]

    m_cov = [m_times([covariance[c][k] for c in range(n_coef)]) for k in range(n_coef)]
    m_cov = [[m_cov[k][r] for k in range(n_coef)] for r in range(n_coef)]  # M Sigma
    new_cov = [[sum(m_cov[r][c] * m_rows[k][c] for c in range(n_coef)) for k in range(n_coef)]
               for r in range(n_coef)]  # M Sigma M'
    m_ce = m_times(cov_c_ebar)  # M Cov(coef, ebar)
    for r in range(n_coef):
        new_cov[r][0] -= m_ce[r]
        new_cov[0][r] -= m_ce[r]
    new_cov[0][0] += var_ebar
    anchored = {keys[i] for i in idx}
    new_residuals = {}
    for key, (mean, var, *c_e) in residuals.items():
        cov_ebar_e = var / n if key in anchored else 0.0
        m_ce_j = m_times(c_e)
        m_ce_j[0] -= cov_ebar_e
        new_residuals[key] = (mean, var, *m_ce_j)
    new_coef = list(coef)
    new_coef[0] = coef[0] + shift
    return new_coef, new_cov, new_residuals, shift


def fit_feature_difficulty(
    log: Mapping[str, Iterable[Response]],
    *,
    items: Mapping[str, Item],
    features: Mapping[str, Mapping[str, float]] | None = None,
    attempt_features: Callable[[Response], Mapping[str, float] | None] | None = attempt_features,
    students: Iterable[str] | None = None,
    anchor: Anchor = "location",
    ability_prior_var: float | None = None,
    residual_var: float | None = None,
    weight_prior_var: float = 1.0,
    intercept_prior_var: float = 4.0,
    max_iter: int = 100,
    max_em_iter: int = 200,
    tol: float = 1e-9,
) -> FeatureDifficulty:
    """Fit which item features predict difficulty, from a log of play.

    ``features`` maps an item key to ``{name: value}``; by default each item's
    ``meta['features']`` (:func:`item_features`). Every item answered in the log needs a
    finite value for every feature named anywhere, or the fit is refused rather than
    guessed. A right/wrong response counts as one trial, a score ``k`` out of
    ``max_score`` as ``k`` successes in ``max_score`` trials (the binomial reading that
    :func:`~learny.tracing.estimators.binomial_thresholds` gives a score; other step
    spacings are not modelled here); skips are not evidence about difficulty and are
    left out. Guessing is not modelled.

    **Per-attempt features.** ``attempt_features`` reads, from each response, features
    of how that attempt was set up (by default ``response.meta['features']``, see
    :func:`attempt_features`; ``None`` ignores them). They enter the same linear
    predictor, ``difficulty = intercept + w . x_item + v . x_attempt + residual_item``,
    standardised over the fitted attempts and with the same weight prior, but with no
    residual of their own. If any scored attempt has them, every one needs a finite
    value for each, or the fit is refused. A given ``difficulty`` that anchors the scale
    is the item's at the average attempt.

    **The scale.** Every answered item that already has a ``difficulty`` can anchor
    the fit to the bank's scale. ``anchor="location"`` (the default) fits on play alone
    and then shifts the intercept (and the students' mean ability) so that the anchors'
    fitted difficulties average their given ones: filled items land where the bank's
    would, while the weights stay exactly what play says, whatever the bank's spread
    (a published band from :func:`~learny.tracing.estimators.difficulty_from_rank` is
    an ordering, not a scale). ``anchor="exact"`` holds each anchor at its given value
    instead, which also lets the given values inform the weights; it trusts them, spread
    included, and a bank anchored throughout is then a regression of the given values
    on the features, with play only placing the students. ``anchor="none"`` keeps the
    fitted students' scale (mean ability 0). A given difficulty of exactly 0 or 1 has no
    finite logit and is skipped as an anchor, with a warning.

    **What it assumes about the log.** Each student has one ability over the log
    (learning within the window is not modelled, so fit on a window short enough for
    that). Which items a student was given may depend on their *earlier answers*, as an
    adaptive game's choice does, but not on anything about them the log does not show:
    stronger students steered to harder items by some other route confound ability
    with difficulty, and no fit of this log can undo that.

    **The priors.** Weights are per *standard deviation* of each feature across the
    fitted items, so ``weight_prior_var=1`` says a one-sd change in a feature plausibly
    moves difficulty by up to a logit or two, whatever its units. ``residual_var`` (how
    far an item may sit from what its features predict) and ``ability_prior_var`` (how
    spread the students are) are estimated from the log when left ``None`` (empirical
    Bayes, by EM; the ability spread only with two or more students, else 1.0), which is what keeps the weights' sds honest: fixed below the truth,
    the 95% intervals covered the true weights 72-80% of the time; estimated, 93-97%
    (``docs/learner-model-design.md``, decision 13). With around 15 responses per item
    the estimates run about 20% low, as Laplace estimates of variance components do on
    right/wrong data.

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
    checked = [("weight_prior_var", weight_prior_var), ("intercept_prior_var", intercept_prior_var)]
    checked += [(n, v) for n, v in (("ability_prior_var", ability_prior_var),
                                    ("residual_var", residual_var)) if v is not None]
    for name, value in checked:
        if not (isinstance(value, Real) and value > 0 and math.isfinite(value)):
            raise ValueError(f"{name} must be a positive number, got {value!r}")

    # -- the data: (student, item, successes, trials) ---------------------------------
    if students is not None:
        student_names = list(students)
        absent = [s for s in student_names if s not in log]
        if absent:
            raise KeyError(f"students {absent[:5]!r} are not in the log")
    else:
        student_names = log.students() if hasattr(log, "students") else list(log)
    rows: list[tuple[int, int, int, int, Mapping[str, float]]] = []
    item_index: dict[str, int] = {}
    no_bank, no_features = set(), set()
    feats: list[Mapping[str, float]] = []
    student_index: dict[str, int] = {}
    for name in student_names:
        for r in log[name]:
            if not r.outcome.is_scored:
                continue
            item = items.get(r.item)
            if item is None:
                no_bank.add(r.item)
                continue
            x = _features_of(r.item, item, features)
            if x is None:
                no_features.add(r.item)
                continue
            if r.item not in item_index:
                item_index[r.item] = len(item_index)
                feats.append(x)
            k, m = (r.score, r.max_score) if r.score is not None else (int(r.correct), 1)
            p = student_index.setdefault(name, len(student_index))
            z = (attempt_features(r) if attempt_features is not None else None) or {}
            rows.append((p, item_index[r.item], k, m, z))
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
    keys = list(item_index)
    incomplete = [key for key, x in zip(keys, feats) if any(n not in x for n in names)]
    if incomplete:
        raise ValueError(
            f"{len(incomplete)} item(s) lack a value for some feature, e.g. "
            f"{incomplete[:5]!r}; every item needs all of {list(names)!r}"
        )
    attempt_names = tuple(sorted({n for *_, z in rows for n in z}))
    lacking = sum(any(n not in z for n in attempt_names) for *_, z in rows)
    if lacking:
        raise ValueError(
            f"{lacking} scored attempt(s) lack a value for some per-attempt feature; every "
            f"attempt needs all of {list(attempt_names)!r} (attempt_features=None ignores them)"
        )

    # -- standardise the features over the fitted items -------------------------------
    n_items, n_feat, n_att = len(item_index), len(names), len(attempt_names)
    raw = [[_number(x[n], n) for n in names] for x in feats]
    center, scale = _center_and_scale(raw, names, over="item")
    # item rows over every coefficient, zero on the attempt weights (an item's own part)
    h_of = [[1.0] + [(row[f] - center[f]) / scale[f] for f in range(n_feat)] + [0.0] * n_att
            for row in raw]
    attempt_center, attempt_scale = [], []
    if n_att:
        raw_z = [[_number(z[n], n) for n in attempt_names] for *_, z in rows]
        attempt_center, attempt_scale = _center_and_scale(raw_z, attempt_names, over="attempt")
        rows = [(*row[:4], [(v - c) / s for v, c, s in zip(zr, attempt_center, attempt_scale)])
                for row, zr in zip(rows, raw_z)]
    else:
        rows = [(*row[:4], []) for row in rows]
    if anchor not in _ANCHORS:
        raise ValueError(f"anchor must be one of {_ANCHORS}, got {anchor!r}")
    given = {i: items[key].difficulty for key, i in item_index.items()
             if anchor != "none" and items[key].difficulty is not None}
    extreme = sorted(key for key, i in item_index.items() if given.get(i) in (0.0, 1.0))
    if extreme:
        warnings.warn(
            f"{len(extreme)} item(s) with a given difficulty of exactly 0 or 1, e.g. "
            f"{extreme[:5]!r}, have no finite logit and were not used as anchors",
            RuntimeWarning,
            stacklevel=2,
        )
    published = {i: logit(d) for i, d in given.items() if 0.0 < d < 1.0}
    known = published if anchor == "exact" else {}
    if all(k == m for _, _, k, m, _ in rows) or all(k == 0 for _, _, k, _, _ in rows):
        warnings.warn(
            "every answer in the log is right (or every one wrong): difficulty is not "
            "identified by play, so the fit is the priors'",
            RuntimeWarning,
            stacklevel=2,
        )

    # -- MAP by Newton, the free items' residuals eliminated by Schur complement ------
    n_stud, n_coef = len(student_index), 1 + n_feat + n_att
    first_att = n_stud + 1 + n_feat
    g_dim = n_stud + n_coef  # (abilities, intercept, weights, attempt weights); residuals apart
    coef_prior = [1.0 / intercept_prior_var] + [1.0 / weight_prior_var] * (n_feat + n_att)
    by_item: dict[int, list[tuple[int, int, int, list[float]]]] = {}
    for p, i, k, m, z in rows:
        by_item.setdefault(i, []).append((p, k, m, z))
    theta = [0.0] * g_dim
    resid = [0.0] * n_items
    newton_converged = em_converged = True

    def newton(tau2: float, a_mean: float, a_var: float):
        """Newton to the mode; returns the global covariance and, per free item, its
        residual's ``(variance, Schur column, d)`` for the block inverse."""
        nonlocal theta, resid, newton_converged
        prior = [1.0 / a_var] * n_stud + coef_prior
        center_of = [a_mean] * n_stud + [0.0] * n_coef
        for _ in range(max_iter):
            grad = [-prior[a] * (theta[a] - center_of[a]) for a in range(g_dim)]
            hess = [[0.0] * g_dim for _ in range(g_dim)]
            for a in range(g_dim):
                hess[a][a] = prior[a]
            cols: dict[int, dict[int, float]] = {}
            grad_e, d_e = {}, {}
            for i in range(n_items):
                h = h_of[i]
                fixed = known.get(i)
                b_i = fixed if fixed is not None else sum(
                    theta[n_stud + c] * h[c] for c in range(n_coef)
                ) + resid[i]
                if fixed is not None:  # the anchor's known difficulty, regressed on h
                    gap = fixed - sum(theta[n_stud + c] * h[c] for c in range(n_coef))
                    for c in range(n_coef):
                        grad[n_stud + c] += gap * h[c] / tau2
                        for c2 in range(n_coef):
                            hess[n_stud + c][n_stud + c2] += h[c] * h[c2] / tau2
                    coords = []
                else:
                    coords = [(n_stud + c, -h[c]) for c in range(1 + n_feat)]
                    grad_e[i], d_e[i], cols[i] = -resid[i] / tau2, 1.0 / tau2, {}
                for p, k, m, z in by_item.get(i, ()):
                    b_r = b_i + sum(theta[first_att + j] * v for j, v in enumerate(z))
                    q = expit(theta[p] - b_r)
                    r, w = k - m * q, m * q * (1.0 - q)
                    g = [(p, 1.0)] + coords + [(first_att + j, -v) for j, v in enumerate(z)]
                    for a, ga in g:
                        grad[a] += r * ga
                        for b, gb in g:
                            hess[a][b] += w * ga * gb
                    if fixed is None:
                        for a, ga in g:  # cross term with the residual, d(eta)/d(e) = -1
                            cols[i][a] = cols[i].get(a, 0.0) - w * ga
                        grad_e[i] -= r
                        d_e[i] += w
            rhs = grad[:]
            for i, col in cols.items():  # S = A - sum_i b_i b_i' / d_i
                inv = 1.0 / d_e[i]
                for a, va in col.items():
                    rhs[a] -= va * inv * grad_e[i]
                    for b, vb in col.items():
                        hess[a][b] -= va * vb * inv
            cov = _cholesky_inverse(hess)
            step = [sum(cov[a][b] * rhs[b] for b in range(g_dim)) for a in range(g_dim)]
            step_e = {
                i: (grad_e[i] - sum(v * step[a] for a, v in cols[i].items())) / d_e[i]
                for i in cols
            }
            theta = [t + d for t, d in zip(theta, step)]
            for i, d in step_e.items():
                resid[i] += d
            if max(abs(d) for d in [*step, *step_e.values()]) < tol:
                newton_converged = True
                break
        else:
            newton_converged = False
        return cov, cols, d_e

    def moments(cov, cols, d_e):
        """Posterior second moments for EM: residuals (free and anchored), abilities."""
        resid_sq = []
        for i in range(n_items):
            h = h_of[i]
            hc = [n_stud + c for c in range(n_coef)]
            if i in known:
                gap = known[i] - sum(theta[n_stud + c] * h[c] for c in range(n_coef))
                v = sum(h[a] * cov[hc[a]][hc[b]] * h[b] for a in range(n_coef) for b in range(n_coef))
            else:
                col = cols[i]
                gap = resid[i]
                v = 1.0 / d_e[i] + sum(
                    va * cov[a][b] * vb for a, va in col.items() for b, vb in col.items()
                ) / d_e[i] ** 2
            resid_sq.append(gap * gap + v)
        abil = [(theta[p], cov[p][p]) for p in range(n_stud)]
        return resid_sq, abil

    learn_ability_var = ability_prior_var is None and n_stud > 1
    tau2 = float(residual_var) if residual_var is not None else _VAR_START
    a_var = float(ability_prior_var) if ability_prior_var is not None else _ABILITY_VAR_DEFAULT
    a_mean = 0.0
    estimate = residual_var is None or learn_ability_var or bool(known)
    cov, cols, d_e = newton(tau2, a_mean, a_var)
    if estimate:
        for _ in range(max_em_iter):
            resid_sq, abil = moments(cov, cols, d_e)
            old = (tau2, a_var, a_mean)
            if known:  # the scale is the anchors': the students' mean is free
                a_mean = sum(t for t, _ in abil) / n_stud
            if residual_var is None:
                tau2 = max(sum(resid_sq) / n_items, _VAR_FLOOR)
            if learn_ability_var:
                a_var = max(sum((t - a_mean) ** 2 + v for t, v in abil) / n_stud, _VAR_FLOOR)
            cov, cols, d_e = newton(tau2, a_mean, a_var)
            if all(abs(new - prev) <= _EM_TOL * (abs(prev) + _EM_NEGLIGIBLE)
                   for new, prev in zip((tau2, a_var, a_mean), old)):
                break
        else:
            em_converged = False
    converged = newton_converged and em_converged  # judged on the final fit only
    if not converged:
        warnings.warn(
            "fit_feature_difficulty hit an iteration cap before converging; the weights "
            "and their sds may be off (raise max_iter or max_em_iter)",
            RuntimeWarning,
            stacklevel=2,
        )

    coef_idx = list(range(n_stud, g_dim))
    residuals: dict[str, tuple[float, ...]] = {}
    for key, i in item_index.items():
        if i in known:
            continue
        col, d = cols[i], d_e[i]
        s_b = {a: sum(cov[a][b] * vb for b, vb in col.items()) for a in range(g_dim)}
        var = 1.0 / d + sum(va * s_b[a] for a, va in col.items()) / d**2
        cov_coef = [-s_b[a] / d for a in coef_idx]  # Cov(coef, residual_i)
        residuals[key] = (resid[i], var, *cov_coef)
    coef = list(theta[n_stud:])
    covariance = [[cov[a][b] for b in coef_idx] for a in coef_idx]
    if anchor == "location" and published:
        coef, covariance, residuals, shift = _shift_to_anchors(
            coef, covariance, residuals, published, h_of, keys
        )
        a_mean += shift
    return FeatureDifficulty(
        names=names,
        center=tuple(center),
        scale=tuple(scale),
        coef=tuple(coef),
        covariance=tuple(tuple(row) for row in covariance),
        residual_var=tau2,
        ability_mean=a_mean,
        ability_var=a_var,
        residuals=residuals,
        anchors=len(published),
        n_students=n_stud,
        n_responses=len(rows),
        converged=converged,
        attempt_names=attempt_names,
        attempt_center=tuple(attempt_center),
        attempt_scale=tuple(attempt_scale),
    )
