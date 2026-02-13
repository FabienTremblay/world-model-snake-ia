#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Conventionneur v1 — fusion + canonisation de propositions épistémiques (JSONL)

- Entrées: un ou plusieurs fichiers JSONL, chaque ligne = une proposition.
- Sortie: un JSONL "collectif" avec dédoublonnage simple + concept_id canonique.

NB: outil d'expérience (snake_collectif_v1), rien d'intégré au runtime.

Format attendu (minimum):
{
  "type": "transition_dominante" | "surprise_transition" | ...,
  "cible": {...},
  "hypothese": {...} (optionnel),
  "preuve": {...} (optionnel),
  "support": int (optionnel),
  "confiance": float (optionnel),
  "source": {"observateur": "O1", ...} (optionnel)
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def _canoniser_id(proposition: Dict[str, Any]) -> str:
    """Génère un concept_id stable à partir du contenu (type + cible + hypothese)."""
    type_ = proposition.get("type", "inconnu")
    cible = proposition.get("cible", {})
    hypothese = proposition.get("hypothese", None)
    blob = json.dumps({"type": type_, "cible": cible, "hypothese": hypothese}, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]
    return f"{type_}__{h}"


def _cle_dedoublonnage(proposition: Dict[str, Any]) -> Tuple[str, str]:
    """Clé de fusion: (type, canon_id)."""
    cid = _canoniser_id(proposition)
    return (proposition.get("type", "inconnu"), cid)


def _lire_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)


def _fusionner(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Fusion naïve: support s'additionne, confiance = moyenne pondérée par support si possible."""
    out = dict(a)
    sa = int(a.get("support") or 0)
    sb = int(b.get("support") or 0)
    out["support"] = sa + sb if (sa or sb) else a.get("support") or b.get("support")

    ca = a.get("confiance")
    cb = b.get("confiance")
    if isinstance(ca, (int, float)) and isinstance(cb, (int, float)) and (sa + sb) > 0:
        out["confiance"] = (ca * sa + cb * sb) / (sa + sb)
    elif cb is not None:
        out["confiance"] = cb

    # preuves: concat léger
    if "preuve" in a or "preuve" in b:
        out["preuve"] = {"a": a.get("preuve"), "b": b.get("preuve")}

    # sources
    sources = []
    if "sources" in a and isinstance(a["sources"], list):
        sources += a["sources"]
    else:
        if a.get("source"):
            sources.append(a["source"])
    if "sources" in b and isinstance(b["sources"], list):
        sources += b["sources"]
    else:
        if b.get("source"):
            sources.append(b["source"])
    if sources:
        out["sources"] = sources
        out.pop("source", None)

    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sortie", required=True, help="Fichier JSONL de sortie (registre collectif)")
    # Compat: ancienne forme positionnelle + alias --inputs
    p.add_argument("entrees", nargs="*", help="Fichiers JSONL d'entrée")
    p.add_argument("--inputs", dest="inputs", nargs="+", help="Alias de 'entrees' (compat)")
    args = p.parse_args()

    entrees = list(args.entrees)
    if args.inputs:
        entrees.extend(args.inputs)
    if not entrees:
        raise SystemExit("Aucune entrée fournie. Donne au moins un fichier JSONL (positionnel ou --inputs).")

    chemins = [Path(x) for x in entrees]
    for c in chemins:
        if not c.exists():
            raise SystemExit(f"Entrée introuvable: {c}")

    fusion: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for c in chemins:
        for prop in _lire_jsonl(c):
            key = _cle_dedoublonnage(prop)
            # inject concept_id canonique
            prop["concept_id"] = key[1]
            if key in fusion:
                fusion[key] = _fusionner(fusion[key], prop)
            else:
                fusion[key] = prop

    sortie = Path(args.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.open("w", encoding="utf-8") as f:
        for _, prop in sorted(fusion.items(), key=lambda kv: kv[0][1]):
            f.write(json.dumps(prop, ensure_ascii=False) + "\n")

    print(f"[OK] écrit: {sortie} ({len(fusion)} propositions fusionnées)")


if __name__ == "__main__":
    main()
