from __future__ import annotations

from typing import Any, Dict, List

from ...noyau.stats_base import ratio_condition, stats_1d
from ...noyau.types import (
    AlerteDiagnostic,
    ContexteRun,
    DocDiagnostic,
    ResultatDiagnostic,
    Diagnostic,
)


class DiagnosticPoidsAdaptatifsV1(Diagnostic):
    id = "diag.poids_adaptatifs.v1"

    def doc(self) -> DocDiagnostic:
        return DocDiagnostic(
            titre="poids adaptatifs (w1, w2)",
            doc_courte="Vérifie si les poids adaptatifs w1/w2 sont stables, dégénérés ou oscillants.",
            doc_longue=(
                "Ce diagnostic examine la dynamique des poids adaptatifs **w1** et **w2** dans `journal_agent.jsonl`.\n"
                "\n"
                "Il calcule des statistiques (min/max/moyenne/std) et des indicateurs de dégénérescence :\n"
                "- **std(w1)** trop faible → poids quasi constant (règle adaptative inactive)\n"
                "- **dominance** (ratio w1>0.7 ou w2>0.7) → collapse sur une tête\n"
                "- **respect du poids_min** si disponible dans le registre épistémique\n"
                "\n"
                "Interprétation :\n"
                "- Un **collapse** peut indiquer un mauvais calibrage (temperature trop faible, mise à jour trop agressive, clipping).\n"
                "- Une **absence de mouvement** (std très faible) peut indiquer que le signal de mise à jour n'est jamais activé.\n"
            ),
            entrees=["journal_agent.jsonl (w1, w2)", "registre_epistemique.json (adaptive.poids_min optionnel)"],
            sorties=["mesures: stats w1/w2, ratios dominance", "alertes actionnables"],
        )

    def preconditions(self, contexte: ContexteRun) -> List[AlerteDiagnostic]:
        if not contexte.journal_agent:
            return [AlerteDiagnostic("fail", "journal_agent vide", "Vérifier le run et la phase epreuve")]
        e0 = contexte.journal_agent[0]
        manquants = [k for k in ("w1", "w2") if k not in e0]
        if manquants:
            return [
                AlerteDiagnostic(
                    "fail",
                    f"champs manquants dans journal_agent: {', '.join(manquants)}",
                    "Vérifier l'agent épistémique (journalisation) ou la version du run",
                )
            ]
        return []

    def executer(self, contexte: ContexteRun) -> ResultatDiagnostic:
        alertes_pre = self.preconditions(contexte)
        if alertes_pre:
            return ResultatDiagnostic(
                diagnostic_id=self.id,
                statut="skip",
                resume="préconditions non satisfaites",
                mesures={},
                alertes=alertes_pre,
            )

        w1 = [float(e["w1"]) for e in contexte.journal_agent]
        w2 = [float(e["w2"]) for e in contexte.journal_agent]

        st_w1 = stats_1d(w1)
        st_w2 = stats_1d(w2)

        ratio_w1_07 = ratio_condition(w1, lambda x: x > 0.7)
        ratio_w2_07 = ratio_condition(w2, lambda x: x > 0.7)

        # poids_min (si disponible)
        poids_min = None
        try:
            poids_min = float(contexte.registre_epistemique.get("adaptive", {}).get("poids_min"))
        except Exception:
            poids_min = None

        viol_min_w1 = 0.0
        viol_min_w2 = 0.0
        if poids_min is not None:
            viol_min_w1 = ratio_condition(w1, lambda x: x < poids_min)
            viol_min_w2 = ratio_condition(w2, lambda x: x < poids_min)

        alertes: List[AlerteDiagnostic] = []
        statut = "ok"

        # Heuristiques MV
        if st_w1.std < 1e-3 and st_w2.std < 1e-3:
            statut = "warn"
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    "std(w1) et std(w2) très faibles : les poids bougent peu",
                    "Vérifier temperature/adaptive, ou si la mise à jour est activée à chaque tick",
                )
            )

        if ratio_w1_07 > 0.8 or ratio_w2_07 > 0.8:
            statut = "warn" if statut == "ok" else statut
            dominant = "w1" if ratio_w1_07 > ratio_w2_07 else "w2"
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    f"dominance détectée : {dominant} > 0.7 dans une large fraction des ticks",
                    "Réviser le calibrage (temperature, alpha_ema) et vérifier l'échelle des signaux s1/s2",
                )
            )

        if poids_min is not None and (viol_min_w1 > 0.0 or viol_min_w2 > 0.0):
            statut = "warn" if statut == "ok" else statut
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    f"poids_min violé (w1<{poids_min} ou w2<{poids_min})",
                    "Vérifier la normalisation et les bornes; le poids_min doit être appliqué après mise à jour",
                )
            )

        resume = f"w1 mean={st_w1.mean:.3f} std={st_w1.std:.3f}; w2 mean={st_w2.mean:.3f} std={st_w2.std:.3f}"

        mesures: Dict[str, Any] = {
            "n": st_w1.n,
            "w1_mean": st_w1.mean,
            "w1_std": st_w1.std,
            "w1_min": st_w1.min,
            "w1_max": st_w1.max,
            "w2_mean": st_w2.mean,
            "w2_std": st_w2.std,
            "w2_min": st_w2.min,
            "w2_max": st_w2.max,
            "ratio_w1_gt_0_7": ratio_w1_07,
            "ratio_w2_gt_0_7": ratio_w2_07,
        }
        if poids_min is not None:
            mesures["poids_min"] = poids_min
            mesures["ratio_w1_lt_poids_min"] = viol_min_w1
            mesures["ratio_w2_lt_poids_min"] = viol_min_w2

        fragments = [
            "| métrique | valeur |\n|---|---:|\n"
            f"| n | {st_w1.n} |\n"
            f"| w1 mean/std | {st_w1.mean:.6f} / {st_w1.std:.6f} |\n"
            f"| w2 mean/std | {st_w2.mean:.6f} / {st_w2.std:.6f} |\n"
            f"| ratio(w1>0.7) | {ratio_w1_07:.3f} |\n"
            f"| ratio(w2>0.7) | {ratio_w2_07:.3f} |\n"
        ]

        return ResultatDiagnostic(
            diagnostic_id=self.id,
            statut=statut,
            resume=resume,
            mesures=mesures,
            alertes=alertes,
            fragments_md=fragments,
        )
