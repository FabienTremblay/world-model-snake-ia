# -*- coding: utf-8 -*-
"""
Diagnostic conditionnel : quand l'action pointe vers un motif candidat (ex: 2),
est-ce que la probabilité de collision_soi dépend de la croissance (delta_score_pos) ?

Convention journal (alignée sur notre correction mur) :
Transition e0 -> e1
  - état observé : capteurs de e0
  - action appliquée : e1.action
  - résultat : e1.termine / e1.raison_fin
  - croissance : e1.delta_score_pos (paramétrable)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

ACTIONS = ("haut", "bas", "gauche", "droite")


@dataclass
class Stats:
    nb_transitions: int = 0
    nb_action_vers_motif: int = 0
    nb_termine_si_action_vers_motif: int = 0
    nb_collision_soi_si_action_vers_motif: int = 0
    raisons_fin: Counter = None

    def __post_init__(self):
        if self.raisons_fin is None:
            self.raisons_fin = Counter()

    def ajouter(self, action_vers_motif: bool, termine: bool, raison_fin: Optional[str]) -> None:
        self.nb_transitions += 1
        if not action_vers_motif:
            return
        self.nb_action_vers_motif += 1
        if termine:
            self.nb_termine_si_action_vers_motif += 1
        if raison_fin == "collision_soi":
            self.nb_collision_soi_si_action_vers_motif += 1
        if raison_fin is not None:
            self.raisons_fin[raison_fin] += 1

    def to_dict(self) -> Dict[str, Any]:
        ratio_action_vers = (self.nb_action_vers_motif / self.nb_transitions) if self.nb_transitions else 0.0
        ratio_termine = (
            self.nb_termine_si_action_vers_motif / self.nb_action_vers_motif
            if self.nb_action_vers_motif else 0.0
        )
        ratio_col_soi = (
            self.nb_collision_soi_si_action_vers_motif / self.nb_action_vers_motif
            if self.nb_action_vers_motif else 0.0
        )
        return {
            "nb_transitions": self.nb_transitions,
            "nb_action_vers_motif": self.nb_action_vers_motif,
            "ratio_action_vers_motif": ratio_action_vers,
            "nb_termine_si_action_vers_motif": self.nb_termine_si_action_vers_motif,
            "ratio_termine_si_action_vers_motif": ratio_termine,
            "nb_collision_soi_si_action_vers_motif": self.nb_collision_soi_si_action_vers_motif,
            "ratio_collision_soi_si_action_vers_motif": ratio_col_soi,
            "raisons_fin_si_action_vers_motif": dict(self.raisons_fin),
        }


def lire_evenements(path: str) -> List[Dict[str, Any]]:
    evts: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            evts.append(json.loads(line))
    return evts

def motif_cible_depuis_evt0(e0: Dict[str, Any], action: str) -> int:
    """
    Utilise directement les signaux perçus déjà recodés dans l'événement e0 :
    motif_haut/bas/gauche/droite.
    """
    if action == "haut":
        return int(e0.get("motif_haut", -1))
    if action == "bas":
        return int(e0.get("motif_bas", -1))
    if action == "gauche":
        return int(e0.get("motif_gauche", -1))
    if action == "droite":
        return int(e0.get("motif_droite", -1))
    return -1

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--motif-candidat", type=int, default=2)
    ap.add_argument("--champ-croissance", default="delta_score_pos")
    ap.add_argument("--experience", required=False, help="Id d'expérience (pour résoudre les chemins + sortie défaut)")
    ap.add_argument("--out", required=False, help="Fichier JSON de sortie (optionnel; défaut: artefacts/diagnostics)")
    args = ap.parse_args()

    racine = Path(__file__).resolve().parents[4]
    bac = None
    if args.experience:
        bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
        bac.assurer_structure()

    journal_path = Path(args.journal)
    if bac is not None and not journal_path.is_absolute():
        journal_path = bac.resoudre_chemin(journal_path)

    out_path = None
    if args.out:
        out_path = Path(args.out)
        if bac is not None and not out_path.is_absolute():
            out_path = bac.resoudre_chemin(out_path)
    elif bac is not None:
        out_path = bac.paths.diagnostics_dir / f"{Path(__file__).stem}__{journal_path.stem}.json"

    evts = lire_evenements(str(journal_path))

    # Grouper par run_id + episode_id, et trier par tick
    by_ep: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    for e in evts:
        rid = str(e.get("run_id", ""))
        eid = int(e.get("episode_id", 0))
        by_ep[(rid, eid)].append(e)

    stats_global = {
        "croissance_0": Stats(),
        "croissance_1": Stats(),
        "croissance_none": Stats(),
    }
    par_action = {
        "croissance_0": {a: Stats() for a in ACTIONS},
        "croissance_1": {a: Stats() for a in ACTIONS},
        "croissance_none": {a: Stats() for a in ACTIONS},
    }

    nb_transitions = 0
    for (_, _), seq in by_ep.items():
        seq.sort(key=lambda x: int(x.get("tick", 0)))
        # transitions e0->e1
        for i in range(len(seq) - 1):
            e0 = seq[i]
            e1 = seq[i + 1]

            # on nécessite les motifs recodés dans e0
            if "motif_haut" not in e0:
                continue

            action = e1.get("action")  # convention corrigée
            if action not in ACTIONS:
                continue

            croissance = e1.get(args.champ_croissance)
            if croissance is None:
                bucket = "croissance_none"
            else:
                bucket = "croissance_1" if int(croissance) == 1 else "croissance_0"

            m_cible = motif_cible_depuis_evt0(e0, action)
            action_vers_motif = (m_cible == int(args.motif_candidat))

            termine = bool(e1.get("termine", False))
            raison_fin = e1.get("raison_fin")

            stats_global[bucket].ajouter(action_vers_motif, termine, raison_fin)
            par_action[bucket][action].ajouter(action_vers_motif, termine, raison_fin)

            nb_transitions += 1

    out = {
        "journal": args.journal,
        "motif_candidat": args.motif_candidat,
        "champ_croissance": args.champ_croissance,
        "nb_evenements": len(evts),
        "nb_transitions_comptees": nb_transitions,
        "par_croissance": {
            "croissance_0": stats_global["croissance_0"].to_dict(),
            "croissance_1": stats_global["croissance_1"].to_dict(),
            "croissance_none": stats_global["croissance_none"].to_dict(),
        },
        "par_action_et_croissance": {
            bucket: {a: par_action[bucket][a].to_dict() for a in ACTIONS}
            for bucket in ("croissance_0", "croissance_1", "croissance_none")
        },
        "note": (
            "Transition e0->e1 : action = e1.action ; état/capteurs = e0.capteurs_compact ; "
            "croissance = e1[champ_croissance]. motifs cibles issus de e0.motif_{haut,bas,gauche,droite}."
        )
    }

    texte = json.dumps(out, indent=2, ensure_ascii=False)
    print(texte)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(texte + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

