from __future__ import annotations

from typing import Any, Dict, List

from ...noyau.stats_base import masse_au_max, stats_1d
from ...noyau.types import AlerteDiagnostic, ContexteRun, DocDiagnostic, ResultatDiagnostic, Diagnostic


class DiagnosticDisagreePlateauV1(Diagnostic):
    id = "diag.disagree_plateau.v1"

    def doc(self) -> DocDiagnostic:
        return DocDiagnostic(
            titre="plateau du désaccord (disagree)",
            doc_courte="Détecte un plateau du désaccord (quantiles supérieurs égaux au max / masse au max) et propose une action.",
            doc_longue=(
                "Ce diagnostic vérifie si la distribution de **disagree** est *plate* ou *saturée*.\n"
                "\n"
                "Signaux typiques :\n"
                "- `q90 == q95 == q99 == max` (plateau dans les quantiles supérieurs)\n"
                "- une **forte masse au max** (beaucoup de valeurs exactement égales au max)\n"
                "\n"
                "Un plateau peut provenir de :\n"
                "- clipping / quantification du désaccord\n"
                "- résolution numérique (arrondis)\n"
                "- définition du désaccord qui prend peu de valeurs distinctes\n"
                "\n"
                "Conséquence : le seuil basé sur les quantiles devient instable (seuil_disagree≈max).\n"
            ),
            entrees=["journal_agent.jsonl (disagree, seuil_disagree)", "registre_epistemique.json (stats.disagree optionnel)"],
            sorties=["mesures: quantiles, masse_au_max", "alerte plateau"],
        )

    def preconditions(self, contexte: ContexteRun) -> List[AlerteDiagnostic]:
        if not contexte.journal_agent:
            return [AlerteDiagnostic("fail", "journal_agent vide", "Vérifier le run")]
        e0 = contexte.journal_agent[0]
        if "disagree" not in e0:
            return [AlerteDiagnostic("fail", "champ disagree absent", "Vérifier la journalisation de l'agent")]
        return []

    def executer(self, contexte: ContexteRun) -> ResultatDiagnostic:
        alertes_pre = self.preconditions(contexte)
        if alertes_pre:
            return ResultatDiagnostic(
                diagnostic_id=self.id,
                statut="skip",
                resume="préconditions non satisfaites",
                alertes=alertes_pre,
            )

        disagree = [float(e["disagree"]) for e in contexte.journal_agent]
        st = stats_1d(disagree, quantiles={"q50": 0.50, "q90": 0.90, "q95": 0.95, "q99": 0.99})
        masse = masse_au_max(disagree)

        # Seuil (si présent dans journal)
        seuil = None
        try:
            seuil = float(contexte.journal_agent[0].get("seuil_disagree"))
        except Exception:
            seuil = None

        q90 = st.quantiles.get("q90")
        q95 = st.quantiles.get("q95")
        q99 = st.quantiles.get("q99")

        plateau_quantiles = (q90 is not None and q95 is not None and q99 is not None and q90 == q95 == q99 == st.max)

        alertes: List[AlerteDiagnostic] = []
        statut = "ok"

        if plateau_quantiles or masse >= 0.5:
            statut = "warn"
            cause = []
            if plateau_quantiles:
                cause.append("quantiles supérieurs égaux au max")
            if masse >= 0.5:
                cause.append(f"masse_au_max={masse:.3f}")
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    "plateau probable du désaccord (" + ", ".join(cause) + ")",
                    "Réviser la stratégie de seuil (quantile robuste) ou vérifier clipping/quantification du disagree",
                )
            )

        if seuil is not None and abs(seuil - st.max) == 0.0:
            statut = "warn" if statut == "ok" else statut
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    "seuil_disagree égal au max : seuil peu informatif",
                    "Si plateau confirmé, utiliser un seuil alternatif (ex. percentile sur valeurs uniques, histogramme, ou seuil fixe)",
                )
            )

        resume = f"disagree mean={st.mean:.6f} std={st.std:.6f} max={st.max:.6f} masse_au_max={masse:.3f}"
        mesures: Dict[str, Any] = {
            "n": st.n,
            "mean": st.mean,
            "std": st.std,
            "min": st.min,
            "max": st.max,
            "q50": st.quantiles.get("q50"),
            "q90": q90,
            "q95": q95,
            "q99": q99,
            "masse_au_max": masse,
            "seuil_disagree": seuil,
            "plateau_quantiles": plateau_quantiles,
        }

        fragments = [
            "| métrique | valeur |\n|---|---:|\n"
            f"| n | {st.n} |\n"
            f"| mean/std | {st.mean:.9f} / {st.std:.9f} |\n"
            f"| min/max | {st.min:.9f} / {st.max:.9f} |\n"
            f"| q90/q95/q99 | {q90} / {q95} / {q99} |\n"
            f"| masse_au_max | {masse:.3f} |\n"
            f"| seuil_disagree | {seuil} |\n"
        ]

        return ResultatDiagnostic(
            diagnostic_id=self.id,
            statut=statut,
            resume=resume,
            mesures=mesures,
            alertes=alertes,
            fragments_md=fragments,
        )
