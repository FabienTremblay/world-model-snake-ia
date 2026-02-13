#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Observateur O2 — Transforme registre_epistemique_v2.json -> propositions JSONL (v1)

But
- Reprendre ce que produit déjà epistemique_v2 (registre JSON dict)
- Le convertir en "propositions" JSONL inter-opérables avec d'autres observateurs.

Entrées possibles
- --registre <fichier.json>  (registre_epistemique_v2.json)
- --run-dir <rep>           (dossier d'un run; auto-détecte registre_epistemique_v2.json)

Sortie
- --sortie <fichier.jsonl>

NB: outil d'expérience (snake_collectif_v1), rien d'intégré au runtime.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _charger_registre(registre_path: Path | None, run_dir: Path | None) -> Dict[str, Any]:
    candidates: List[Path] = []
    if registre_path:
        candidates.append(registre_path)
    if run_dir:
        # formes: <run_dir>/registre_epistemique_v2.json ou <run_dir>/registre_epistemique_v2.jsonl (non attendu)
        candidates.append(run_dir / "registre_epistemique_v2.json")
        # certains tools écrivent directement dans runs/<id>/...; tolérer un niveau
        candidates += list(run_dir.glob("**/registre_epistemique_v2.json"))

    for c in candidates:
        if c.exists() and c.is_file():
            return json.loads(c.read_text(encoding="utf-8"))

    # mode dégradé : on laisse la démo/pipeline avancer même si sai-a106 n'a
    # pas encore produit le fichier. la correction structurelle reste :
    # créer/produire <run-dir>/registre_epistemique_v2.json.
    # dégradation contrôlée :
    # pour la recette de snake_collectif_v1, on peut lancer o2 même si sai-a106 n’a pas encore
    # produit le fichier registre_epistemique_v2.json. dans ce cas, on préfère émettre 0 proposition
    # plutôt que de bloquer le pipeline.
    if run_dir and not registre_path:
        print("[WARN] registre_epistemique_v2.json introuvable dans run-dir; O2 émet 0 proposition.")
        print("       (Rappel: SAI-A106 est responsable de produire ce fichier, même vide.)")
        return {
            "run_dir": str(run_dir),
            "indices": {"episodes": 0},
            "actions": {},
            "raisons_fin": {},
            "concepts_candidates": [],
        }

    msg = ["Registre introuvable."]
    if registre_path:
        msg.append(f"- demandé: {registre_path}")
    if run_dir:
        msg.append(f"- run-dir: {run_dir}")
        msg.append("  attendu: <run-dir>/registre_epistemique_v2.json")
    msg.append("")
    msg.append("Astuce: utilise le chemin dans ton repo, ex:")
    msg.append("  donnees/config/experiences/snake_collectif_v1/artefacts/runs/<run-id>/registre_epistemique_v2.json")
    raise FileNotFoundError("\n".join(msg))


def _emit_transition_dominante(registre: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    concepts = registre.get("concepts_candidates") or []
    for c in concepts:
        # on accepte déjà la forme de registre v2 (liste de dict)
        if c.get("type") != "transition_dominante":
            continue
        out.append({
            "type": "transition_dominante",
            "cible": c.get("cible", {}),
            "hypothese": c.get("hypothese", {}),
            "preuve": c.get("preuve", {}),
            "support": c.get("support"),
            "confiance": c.get("confiance"),
            "source": {
                "observateur": "O2",
                "run_dir": registre.get("run_dir"),
                "registre": "registre_epistemique_v2.json"
            }
        })
    return out


def _emit_diagnostic(registre: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    indices = registre.get("indices", {})
    out.append({
        "type": "diagnostic_global",
        "cible": {"run": registre.get("run_dir")},
        "hypothese": None,
        "preuve": {"indices": indices, "raisons_fin": registre.get("raisons_fin"), "actions": registre.get("actions")},
        "support": indices.get("episodes"),
        "confiance": 1.0,
        "source": {"observateur": "O2", "registre": "registre_epistemique_v2.json"}
    })
    return out


def _emit_terminalite(registre: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Résumé statistique des fins d'épisodes.

    On ne "nomme" pas la mort; on conserve une forme neutre exploitable par SAI-A107.
    """
    out: List[Dict[str, Any]] = []
    raisons = registre.get("raisons_fin") or {}
    indices = registre.get("indices") or {}
    nb = indices.get("episodes")
    out.append({
        "type": "terminalite_statistique",
        "cible": {"run": registre.get("run_dir")},
        "hypothese": None,
        "preuve": {"raisons_fin": raisons},
        "support": nb,
        "confiance": 1.0,
        "source": {"observateur": "O2", "registre": "registre_epistemique_v2.json"}
    })
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--registre", help="Chemin vers registre_epistemique_v2.json (JSON dict)")
    p.add_argument("--run-dir", help="Dossier du run (auto-détecte registre_epistemique_v2.json)")
    p.add_argument("--sortie", required=True, help="Chemin JSONL de sortie")
    args = p.parse_args()

    registre_path = Path(args.registre) if args.registre else None
    run_dir = Path(args.run_dir) if args.run_dir else None
    registre = _charger_registre(registre_path, run_dir)

    propositions: List[Dict[str, Any]] = []
    propositions += _emit_diagnostic(registre)
    propositions += _emit_terminalite(registre)
    propositions += _emit_transition_dominante(registre)

    sortie = Path(args.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.open("w", encoding="utf-8") as f:
        for prop in propositions:
            f.write(json.dumps(prop, ensure_ascii=False) + "\n")

    print(f"[OK] écrit: {sortie} ({len(propositions)} propositions)")


if __name__ == "__main__":
    main()
