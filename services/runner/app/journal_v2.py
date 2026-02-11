# services/runner/app/journal_v2.py
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from commun.contrats import Pixel
from instrument.app.contrats import (
    EtatMondeCanonique,
    ObservationDonnees,
    ObservationInstrument,
    ObservationPixels,
)


def _jsonable(obj: Any) -> Any:
    """Convertit un objet Python en structure JSON-serialisable.

    Règle: on privilégie dataclasses.asdict(), puis les structures natives.
    """

    if obj is None:
        return None

    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]

    if isinstance(obj, set):
        # pas de set en JSON
        return sorted([_jsonable(x) for x in obj])

    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}

    # fallback : représentation textuelle (utile pour debug, mais à éviter)
    return repr(obj)


def _pixels_vers_npz(pixels: list[list[Pixel]], path_npz: Path) -> None:
    """Sérialise une grille de Pixel en NPZ (teinte/intensite/motif/clignote)."""
    h = len(pixels)
    w = len(pixels[0]) if h else 0
    teinte = np.zeros((h, w), dtype=np.int16)
    intensite = np.zeros((h, w), dtype=np.uint8)
    motif = np.zeros((h, w), dtype=np.uint8)
    clignote = np.zeros((h, w), dtype=np.uint8)

    for y in range(h):
        for x in range(w):
            px = pixels[y][x]
            teinte[y, x] = int(px.teinte)
            intensite[y, x] = int(px.intensite)
            motif[y, x] = int(px.motif)
            clignote[y, x] = int(px.clignote)

    path_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path_npz, teinte=teinte, intensite=intensite, motif=motif, clignote=clignote)


class JournalV2Writer:
    """Journal v2 :

    - meta.json (paramètres du run / bac-à-sable / instruments)
    - journal.jsonl (1 ligne par tick)
    - obs/ (payloads lourds, ex. caméras)

    Pas de compat v1 : ce writer remplace l'ancien JournalEpisodes.
    """

    VERSION = "journal_v2"

    def __init__(self, run_dir: Path, run_id: str, meta: Dict[str, Any]) -> None:
        actif = os.getenv("SNAKE_JOURNAL", "1").strip()
        self.actif = actif not in {"0", "false", "False", "non", "NO"}
        self.run_id = run_id

        # Répertoire de run fourni par le bac-à-sable (ou fallback).
        # Convention: <experience_dir>/artefacts/runs/<run_name>/
        self.run_dir = Path(run_dir).resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.path_meta = self.run_dir / "meta.json"
        self.path_journal = self.run_dir / "journal.jsonl"
        self.obs_dir = self.run_dir / "obs"

        self._f = open(self.path_journal, "a", encoding="utf-8") if self.actif else None

        # Écrit meta une seule fois (idempotent simple)
        if self.actif:
            # Meta: on force run_id + run_dir pour assurer la rejouabilité.
            meta_out = {
                "version": self.VERSION,
                "ts_ns": time.time_ns(),
                "run_id": self.run_id,
                "run_dir": str(self.run_dir),
                **_jsonable(meta),
            }
            self.path_meta.write_text(json.dumps(meta_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def fermer(self) -> None:
        if self._f:
            self._f.flush()
            self._f.close()
            self._f = None

    def _serialiser_observation(
        self,
        instrument_id: str,
        obs: ObservationInstrument,
        episode_id: int,
        tick: int,
    ) -> Dict[str, Any]:
        """Retourne un dict JSON v2 pour une observation d'instrument."""

        base = {
            "instrument_id": instrument_id,
        }

        if isinstance(obs, ObservationDonnees):
            return {
                **base,
                "type": "donnees",
                "payload": _jsonable(obs.donnees),
                "meta": _jsonable(obs.meta),
            }

        if isinstance(obs, ObservationPixels):
            rel = (
                Path("obs")
                / f"ep{episode_id:04d}"
                / f"t{tick:04d}"
                / f"{instrument_id}.npz"
            )
            path_npz = self.run_dir / rel
            _pixels_vers_npz(obs.pixels, path_npz)
            return {
                **base,
                "type": "pixels_npz",
                "payload_ref": str(rel.as_posix()),
                "meta": _jsonable(obs.meta),
            }

        # Si un instrument sort autre chose un jour, on le verra immédiatement.
        raise TypeError(f"ObservationInstrument non supportée: {type(obs)!r}")

    def ecrire_tick(
        self,
        *,
        episode_id: int,
        tick: int,
        arene_id: Optional[str],
        seed: Optional[int],
        agent_id: Optional[str],
        incarnation_id: Optional[str],
        action: Optional[str],
        niveau_bruit: int,
        etat: EtatMondeCanonique,
        score: int,
        longueur: int,
        termine: bool,
        raison_fin: Optional[str],
        observations: Dict[str, ObservationInstrument],
    ) -> None:
        if not self._f:
            return

        monde_canon = {
            "largeur": int(etat.largeur),
            "hauteur": int(etat.hauteur),
            "serpent": _jsonable(etat.serpent),
            "direction": etat.direction,
            "nourritures": _jsonable(etat.nourritures),
            "porte": _jsonable(etat.porte),
            "porte_ouverte": bool(etat.porte_ouverte),
            "score": int(score),
            "longueur": int(longueur),
            "termine": bool(termine),
            "raison_fin": raison_fin,
        }

        inst_out: Dict[str, Any] = {}
        for inst_id, obs in observations.items():
            inst_out[inst_id] = self._serialiser_observation(inst_id, obs, episode_id, tick)

        ligne = {
            "version": self.VERSION,
            "ts_ns": time.time_ns(),
            "run_id": self.run_id,
            "episode_id": int(episode_id),
            "tick": int(tick),
            "arene_id": arene_id,
            "seed": seed,
            "agent": {
                "agent_id": agent_id,
                "incarnation_id": incarnation_id,
            },
            "decision": {
                "action": action,
            },
            "perception": {
                "niveau_bruit": int(niveau_bruit),
                "instruments": inst_out,
            },
            "monde_canonique": monde_canon,
        }

        self._f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        if termine:
            self._f.flush()
