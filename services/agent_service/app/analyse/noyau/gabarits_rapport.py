"""Gabarits et rendu du rapport diagnostics.

Le rapport est standardisé, puis chaque diagnostic peut ajouter des sections.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List

from .types import ContexteRun, ResultatDiagnostic, SectionRapport


def _md_liste(items: List[str]) -> str:
    if not items:
        return ""
    return "\n".join(f"- {x}" for x in items)


def rendre_rapport_md(contexte: ContexteRun, resultats: List[ResultatDiagnostic], sections_extra: List[SectionRapport]) -> str:
    maintenant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    exp = contexte.experience_id or "(inconnue)"
    run_id = contexte.run_id or contexte.run_dir.name

    lignes: List[str] = []
    lignes.append(f"# Rapport diagnostics — {exp} — {run_id}")
    lignes.append("")
    lignes.append(f"Généré le {maintenant} (UTC).")
    lignes.append("")

    # Chemins
    lignes.append("## Chemins")
    lignes.append("")
    for k, v in contexte.chemins.items():
        lignes.append(f"- **{k}** : `{v}`")
    lignes.append("")

    # Résumé
    lignes.append("## Résumé")
    lignes.append("")
    for r in resultats:
        lignes.append(f"- **{r.diagnostic_id}** — *{r.statut}* : {r.resume}")
    lignes.append("")

    # Détails par diagnostic
    lignes.append("## Détails")
    lignes.append("")

    for r in resultats:
        lignes.append(f"### {r.diagnostic_id}")
        lignes.append("")
        lignes.append(f"**Statut** : `{r.statut}`")
        lignes.append("")
        lignes.append(r.resume)
        lignes.append("")

        if r.alertes:
            lignes.append("**Alertes**")
            lignes.append("")
            for a in r.alertes:
                quoi = f" — *quoi faire* : {a.quoi_faire}" if a.quoi_faire else ""
                lignes.append(f"- `{a.niveau}` : {a.message}{quoi}")
            lignes.append("")

        if r.mesures:
            lignes.append("**Mesures**")
            lignes.append("")
            for k, v in r.mesures.items():
                lignes.append(f"- **{k}** : `{v}`")
            lignes.append("")

        if r.fragments_md:
            lignes.append("**Notes**")
            lignes.append("")
            lignes.extend(r.fragments_md)
            lignes.append("")

    # Sections extra (diagnostics)
    if sections_extra:
        lignes.append("## Annexes")
        lignes.append("")
        for s in sections_extra:
            lignes.append(f"### {s.titre}")
            lignes.append("")
            lignes.append(s.contenu_md.rstrip())
            lignes.append("")

    return "\n".join(lignes).rstrip() + "\n"
