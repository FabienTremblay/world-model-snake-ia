"""Statistiques de base (1D) pour diagnostics.

Pas de dépendances externes (numpy) pour garder le module léger.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Stats1D:
    n: int
    mean: float
    std: float
    min: float
    max: float
    quantiles: Dict[str, float]


def _quantile_sur_trie(v_trie: Sequence[float], q: float) -> float:
    """Quantile par interpolation linéaire (type 7 / proche numpy default)."""

    if not v_trie:
        raise ValueError("Liste vide")
    if q <= 0:
        return float(v_trie[0])
    if q >= 1:
        return float(v_trie[-1])
    n = len(v_trie)
    # position 0..n-1
    pos = (n - 1) * q
    i = int(pos)
    frac = pos - i
    if i >= n - 1:
        return float(v_trie[-1])
    return float(v_trie[i] * (1 - frac) + v_trie[i + 1] * frac)


def stats_1d(valeurs: Iterable[float], quantiles: Optional[Dict[str, float]] = None) -> Stats1D:
    v = [float(x) for x in valeurs]
    n = len(v)
    if n == 0:
        return Stats1D(n=0, mean=0.0, std=0.0, min=0.0, max=0.0, quantiles={})

    s = sum(v)
    mean = s / n
    # variance population
    var = sum((x - mean) ** 2 for x in v) / n
    std = sqrt(var)
    mn = min(v)
    mx = max(v)

    qs: Dict[str, float] = {}
    if quantiles:
        v_trie = sorted(v)
        for nom, q in quantiles.items():
            qs[nom] = _quantile_sur_trie(v_trie, q)

    return Stats1D(n=n, mean=mean, std=std, min=mn, max=mx, quantiles=qs)


def ratio_condition(valeurs: Iterable[float], predicate) -> float:
    v = list(valeurs)
    if not v:
        return 0.0
    ok = sum(1 for x in v if predicate(float(x)))
    return ok / len(v)


def correlation_pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sx = sqrt(sum((xi - mx) ** 2 for xi in x) / n)
    sy = sqrt(sum((yi - my) ** 2 for yi in y) / n)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / n
    return cov / (sx * sy)


def detect_plateau_quantiles(stats: Stats1D, cle_max: str = "q99", cles_plateau: Tuple[str, ...] = ("q90", "q95", "q99")) -> bool:
    if not stats.quantiles:
        return False
    # plateau si tous égaux entre eux et au max
    valeurs = [stats.quantiles.get(k) for k in cles_plateau]
    if any(v is None for v in valeurs):
        return False
    v0 = valeurs[0]
    if any(abs(v - v0) > 0.0 for v in valeurs[1:]):
        return False
    return abs(v0 - stats.max) <= 0.0


def masse_au_max(valeurs: Sequence[float]) -> float:
    if not valeurs:
        return 0.0
    mx = max(valeurs)
    return sum(1 for v in valeurs if float(v) == float(mx)) / len(valeurs)
