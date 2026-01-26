# services/agent_service/app/spectateur.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from commun.contrats import Observation, Pixel


def _stats_intensite(capteurs: List[List[Pixel]]) -> tuple[float, float, float]:
    """
    Retourne (moyenne, variance, proportion_nonvide)
    - nonvide = motif != 0
    """
    h = len(capteurs)
    w = len(capteurs[0]) if h else 0
    n = h * w
    if n == 0:
        return 0.0, 0.0, 0.0

    s = 0.0
    s2 = 0.0
    nonvides = 0
    for y in range(h):
        for x in range(w):
            v = float(capteurs[y][x].intensite)
            s += v
            s2 += v * v
            if int(capteurs[y][x].motif) != 0:
                nonvides += 1
    mu = s / n
    var = (s2 / n) - (mu * mu)
    return mu, var, nonvides / n


def _checksum_rapide(capteurs: List[List[Pixel]]) -> int:
    """
    Checksum non-cryptographique (debug) pour détecter des changements.
    """
    h = len(capteurs)
    w = len(capteurs[0]) if h else 0
    acc = 2166136261  # FNV-ish
    for y in range(h):
        for x in range(w):
            px = capteurs[y][x]
            # mélange léger
            acc ^= (int(px.teinte) & 0xFFFF)
            acc *= 16777619
            acc &= 0xFFFFFFFF
            acc ^= (int(px.intensite) & 0xFF)
            acc *= 16777619
            acc &= 0xFFFFFFFF
            acc ^= ((int(px.motif) & 0x7) << 1) | (int(px.clignote) & 0x1)
            acc *= 16777619
            acc &= 0xFFFFFFFF
    return int(acc)


class Spectateur:
    """
    Agent spectateur: observe seulement. Ne produit aucune action.
    """

    def __init__(self, racine_projet: Path) -> None:
        self.racine = racine_projet
        self.path = self.racine / "artefacts" / "spectateur.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(self.path, "a", encoding="utf-8")

        self._dernier_episode: Optional[int] = None
        self._dernier_tick: Optional[int] = None
        self._dernier_checksum: Optional[int] = None

    def fermer(self) -> None:
        try:
            self._f.flush()
            self._f.close()
        except Exception:
            pass

    def traiter(self, obs: Observation) -> None:
        mu, var, prop_nonvide = _stats_intensite(obs.capteurs)
        chk = _checksum_rapide(obs.capteurs)

        # Détection simple de discontinuités (utile au debug)
        rupture = False
        if self._dernier_episode is not None and obs.episode_id != self._dernier_episode:
            rupture = True
        if self._dernier_tick is not None and obs.tick < self._dernier_tick:
            rupture = True

        # Baseline prédictive v0:
        # prédire que le prochain checksum sera identique au précédent.
        chk_pred = self._dernier_checksum
        err_pred = None
        if chk_pred is not None and not rupture:
            err_pred = 0 if chk == chk_pred else 1

        ligne = {
            "ts_ns": time.time_ns(),
            "episode_id": int(obs.episode_id),
            "tick": int(obs.tick),
            "score": int(obs.score),
            "longueur": int(obs.longueur),
            "termine": bool(obs.termine),
            "raison_fin": obs.raison_fin,
            "mu_int": mu,
            "var_int": var,
            "prop_nonvide": prop_nonvide,
            "checksum": chk,
            "checksum_pred": chk_pred,
            "err_pred": err_pred,
            "rupture": rupture,
            "note": obs.mesure_bruit,  # pratique: inclut "REPLAY ..." si présent
        }
        self._f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        if obs.termine:
            self._f.flush()

        self._dernier_episode = int(obs.episode_id)
        self._dernier_tick = int(obs.tick)
        self._dernier_checksum = chk

