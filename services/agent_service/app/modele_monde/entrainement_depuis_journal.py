# services/agent_service/app/modele_monde/entrainement_depuis_journal.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple

from runner.app.replay import decoder_capteurs_b64
from agent_service.app.spectateur import _checksum_rapide
from agent_service.app.modele_monde.tabulaire_v1 import ModeleMondeTabulaireV1


def _lire_jsonl(path: Path) -> Iterator[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _checksum_evt(evt: dict) -> int:
    b64 = evt["capteurs_compact"]
    w = int(evt["largeur"])
    h = int(evt["hauteur"])
    capteurs = decoder_capteurs_b64(b64, w, h)
    return _checksum_rapide(capteurs)


def calculer_checksum_evt(evt: dict) -> int:
    """API publique: checksum rapide d'un événement à partir de capteurs_compact.

    Utile pour l'évaluation lorsque champ_latent != "checksum" et qu'on veut
    tracer checksum vs latent_id dans le même jsonl.
    """
    return _checksum_evt(evt)


def _etat_evt(evt: dict, champ_latent: str) -> int:
    """Retourne l'identifiant d'état latent pour un événement.

    - champ_latent == "checksum": calcule un checksum rapide depuis capteurs_compact
    - sinon: lit evt[champ_latent] et le convertit en int (ex: latent_id)
    """
    if champ_latent == "checksum":
        return _checksum_evt(evt)

    if champ_latent not in evt:
        raise KeyError(f'Champ latent absent dans l\'événement: {champ_latent}')
    return int(evt[champ_latent])



def iterer_transitions(
    journal_path: Path,
    champ_latent: str = "checksum",
) -> Iterator[Tuple[dict, dict, int, int, str]]:
    """Itère des transitions (prev_evt, evt, etat_prev, etat, action).

    Convention :
      - tick 0: action null, observation initiale
      - tick t>=1: action est l'action appliquée pour passer de (t-1) à t
    => transition: (etat[t-1], action[t]) -> etat[t]

    champ_latent:
      - "checksum" : calcule l'état depuis capteurs_compact
      - autre      : lit evt[champ_latent] (ex: "latent_id") en int
    """
    prev_evt: Optional[dict] = None
    prev_etat: Optional[int] = None

    for evt in _lire_jsonl(journal_path):
        # on doit pouvoir obtenir un état latent
        try:
            etat_evt = _etat_evt(evt, champ_latent)
        except Exception:
            # événement inutilisable pour l'entraînement/évaluation
            prev_evt = None
            prev_etat = None
            continue

        if prev_evt is None:
            prev_evt = evt
            prev_etat = etat_evt
            continue

        # continuité stricte: même run + episode, ticks consécutifs
        if (
            str(evt.get("run_id")) != str(prev_evt.get("run_id"))
            or int(evt.get("episode_id")) != int(prev_evt.get("episode_id"))
            or int(evt.get("tick")) != int(prev_evt.get("tick")) + 1
        ):
            prev_evt = evt
            prev_etat = etat_evt
            continue

        action = evt.get("action")
        if action is None:
            # on ne peut pas apprendre sans action
            prev_evt = evt
            prev_etat = etat_evt
            continue

        yield prev_evt, evt, int(prev_etat), int(etat_evt), str(action)

        prev_evt = evt
        prev_etat = etat_evt


def entrainer_modele_tabulaire_v1(journal_path: Path, champ_latent: str = "checksum") -> tuple[ModeleMondeTabulaireV1, dict]:
    modele = ModeleMondeTabulaireV1()
    nb = 0
    par_action: Dict[str, int] = {}

    for _prev, _evt, chk_prev, chk, action in iterer_transitions(journal_path, champ_latent=champ_latent):
        modele.apprendre_transition(chk_prev, action, chk)
        nb += 1
        par_action[action] = par_action.get(action, 0) + 1

    rapport = {
        "journal_path": str(journal_path),
        "nb_transitions": int(nb),
        "par_action": dict(sorted(par_action.items())),
        "stats_modele": modele.stats(),
    }
    return modele, rapport
