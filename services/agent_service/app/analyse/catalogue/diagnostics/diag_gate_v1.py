from __future__ import annotations

from typing import Any, Dict, List

from ...noyau.types import AlerteDiagnostic, ContexteRun, DocDiagnostic, ResultatDiagnostic, Diagnostic


class DiagnosticGatePartitionV1(Diagnostic):
    id = "diag.gate_partition.v1"

    def doc(self) -> DocDiagnostic:
        return DocDiagnostic(
            titre="partition du gate (inconnu: surprise vs désaccord)",
            doc_courte="Explique la partition du gate et détecte les cas dégénérés (tout sur un gate, tout inconnu/rien inconnu).",
            doc_longue=(
                "Ce diagnostic lit `registre_epistemique.json` et résume la **partition du gate** :\n"
                "- proportions d'états classés **connus** vs **inconnus**\n"
                "- parmi les inconnus : due à **surprise** vs due au **désaccord**\n"
                "\n"
                "Il vérifie aussi la présence de seuils/quantiles (seuil_surprise, seuil_disagree).\n"
                "\n"
                "Cas dégénérés typiques :\n"
                "- 0% inconnu (exploration jamais déclenchée)\n"
                "- 100% inconnu (seuils trop bas ou signaux mal calibrés)\n"
                "- 99% des inconnus dus à une seule cause (surprise ou désaccord)\n"
            ),
            entrees=["registre_epistemique.json (effets_gate, gate, stats)"] ,
            sorties=["mesures: ratios", "alertes actionnables"],
        )

    def preconditions(self, contexte: ContexteRun) -> List[AlerteDiagnostic]:
        reg = contexte.registre_epistemique
        if not reg:
            return [AlerteDiagnostic("fail", "registre_epistemique manquant", "Vérifier phase epreuve")]
        if "effets_gate" not in reg:
            return [AlerteDiagnostic("fail", "champ effets_gate manquant", "Vérifier la version du registre")]
        return []


    def _reconstruire_partition_depuis_journal(self, contexte: ContexteRun) -> Dict[str, float] | None:
        """Reconstruit la partition connu/inconnu depuis le journal si possible.

        Hypothèse (alignée à JEPA-5):
        - un tick est 'inconnu' si surprise >= seuil_surprise OU disagree >= seuil_disagree.
        - on calcule aussi les contributions: surprise, disagree, et l'intersection.
        """
        if not contexte.journal_agent:
            return None

        n = 0
        inconnu = 0
        trig_surprise = 0
        trig_disagree = 0
        trig_both = 0

        for e in contexte.journal_agent:
            if "surprise" not in e or "disagree" not in e:
                continue
            # seuils peuvent être par tick (JEPA-5) ou globaux; on tente les deux
            seuil_s = e.get("seuil_surprise")
            seuil_d = e.get("seuil_disagree")
            if seuil_s is None:
                seuil_s = contexte.registre_epistemique.get("gate", {}).get("seuil_surprise")
            if seuil_d is None:
                seuil_d = contexte.registre_epistemique.get("gate", {}).get("seuil_disagree")
            if seuil_s is None or seuil_d is None:
                continue

            try:
                s = float(e["surprise"])
                d = float(e["disagree"])
                ss = float(seuil_s)
                sd = float(seuil_d)
            except Exception:
                continue

            n += 1
            s_trig = s >= ss
            d_trig = d >= sd

            if s_trig:
                trig_surprise += 1
            if d_trig:
                trig_disagree += 1
            if s_trig and d_trig:
                trig_both += 1
            if s_trig or d_trig:
                inconnu += 1

        if n == 0:
            return None

        return {
            "n": float(n),
            "ratio_connu_total": (n - inconnu) / n,
            "ratio_inconnu_total": inconnu / n,
            "ratio_inconnu_surprise": trig_surprise / n,
            "ratio_inconnu_disagree": trig_disagree / n,
            "ratio_inconnu_surprise_et_disagree": trig_both / n,
        }

    def executer(self, contexte: ContexteRun) -> ResultatDiagnostic:
        alertes_pre = self.preconditions(contexte)
        if alertes_pre:
            return ResultatDiagnostic(
                diagnostic_id=self.id,
                statut="skip",
                resume="préconditions non satisfaites",
                alertes=alertes_pre,
            )

        reg = contexte.registre_epistemique
        effets = reg.get("effets_gate", {})

        # on accepte plusieurs formes; on récupère des ratios si présents
        ratio_inconnu_total = effets.get("ratio_inconnu_total")
        ratio_inconnu_surprise = effets.get("ratio_inconnu_surprise")
        ratio_inconnu_disagree = effets.get("ratio_inconnu_disagree")
        ratio_connu = effets.get("ratio_connu_total")

        # si le registre ne contient pas la partition, on tente de la reconstruire depuis journal_agent.jsonl
        recon = None
        if ratio_connu is None or ratio_inconnu_total is None or (ratio_inconnu_surprise is None and ratio_inconnu_disagree is None):
            recon = self._reconstruire_partition_depuis_journal(contexte)
            if recon:
                ratio_connu = recon.get("ratio_connu_total", ratio_connu)
                ratio_inconnu_total = recon.get("ratio_inconnu_total", ratio_inconnu_total)
                ratio_inconnu_surprise = recon.get("ratio_inconnu_surprise", ratio_inconnu_surprise)
                ratio_inconnu_disagree = recon.get("ratio_inconnu_disagree", ratio_inconnu_disagree)
                ratio_inconnu_both = recon.get("ratio_inconnu_surprise_et_disagree")
            else:
                ratio_inconnu_both = None
        else:
            ratio_inconnu_both = None


        alertes: List[AlerteDiagnostic] = []
        statut = "ok"

        # seuils dans gate ou stats
        gate = reg.get("gate", {})
        seuil_surprise = gate.get("seuil_surprise")
        seuil_disagree = gate.get("seuil_disagree")

        # si on ne peut pas expliquer la partition, on le signale
        if ratio_inconnu_surprise is None or ratio_inconnu_disagree is None:
            statut = "warn" if statut == "ok" else statut
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    "partition inconnus (surprise vs désaccord) indisponible",
                    "Ajouter les ratios au registre OU reconstruire depuis le journal (surprise/disagree + seuils) pour expliquer la cause de l'inconnu",
                )
            )

        if seuil_surprise is None or seuil_disagree is None:
            statut = "warn"
            alertes.append(
                AlerteDiagnostic(
                    "warn",
                    "seuil_surprise ou seuil_disagree absents du registre",
                    "Vérifier la génération du registre; sans seuils, l'interprétation du gate est moins solide",
                )
            )

        # heuristiques
        try:
            if ratio_inconnu_total is not None:
                rit = float(ratio_inconnu_total)
                if rit <= 0.001:
                    statut = "warn" if statut == "ok" else statut
                    alertes.append(
                        AlerteDiagnostic(
                            "warn",
                            "quasi aucun inconnu (ratio_inconnu_total≈0)",
                            "Explorer risque de ne jamais être déclenché; vérifier seuils trop hauts",
                        )
                    )
                if rit >= 0.999:
                    statut = "warn" if statut == "ok" else statut
                    alertes.append(
                        AlerteDiagnostic(
                            "warn",
                            "presque tout est inconnu (ratio_inconnu_total≈1)",
                            "Seuils trop bas ou signaux mal calibrés; vérifier échelle surprise/disagree",
                        )
                    )
        except Exception:
            pass

        try:
            if ratio_inconnu_surprise is not None and ratio_inconnu_disagree is not None:
                rs = float(ratio_inconnu_surprise)
                rd = float(ratio_inconnu_disagree)
                if rs > 0.99:
                    statut = "warn" if statut == "ok" else statut
                    alertes.append(
                        AlerteDiagnostic(
                            "warn",
                            "les inconnus semblent presque tous dus à la surprise",
                            "Vérifier si le désaccord est saturé/plat ou si son seuil est trop haut",
                        )
                    )
                if rd > 0.99:
                    statut = "warn" if statut == "ok" else statut
                    alertes.append(
                        AlerteDiagnostic(
                            "warn",
                            "les inconnus semblent presque tous dus au désaccord",
                            "Vérifier la calibration de la surprise ou si son seuil est trop haut",
                        )
                    )
        except Exception:
            pass

        mesures: Dict[str, Any] = {
            "ratio_connu_total": ratio_connu,
            "ratio_inconnu_total": ratio_inconnu_total,
            "ratio_inconnu_surprise": ratio_inconnu_surprise,
            "ratio_inconnu_disagree": ratio_inconnu_disagree,
            "ratio_inconnu_surprise_et_disagree": ratio_inconnu_both,
            "seuil_surprise": seuil_surprise,
            "seuil_disagree": seuil_disagree,
        }

        resume = "partition gate: "
        if ratio_connu is not None:
            resume += f"connu={float(ratio_connu):.3f} "
        if ratio_inconnu_total is not None:
            resume += f"inconnu={float(ratio_inconnu_total):.3f} "
        if ratio_inconnu_surprise is not None and ratio_inconnu_disagree is not None:
            resume += f"(surprise={float(ratio_inconnu_surprise):.3f}, disagree={float(ratio_inconnu_disagree):.3f})"

        fragments = [
            "| item | valeur |\n|---|---:|\n"
            f"| ratio_connu_total | {ratio_connu} |\n"
            f"| ratio_inconnu_total | {ratio_inconnu_total} |\n"
            f"| ratio_inconnu_surprise | {ratio_inconnu_surprise} |\n"
            f"| ratio_inconnu_disagree | {ratio_inconnu_disagree} |\n| ratio_inconnu_surprise_et_disagree | {ratio_inconnu_both} |\n"
            f"| seuil_surprise | {seuil_surprise} |\n"
            f"| seuil_disagree | {seuil_disagree} |\n"
        ]

        return ResultatDiagnostic(
            diagnostic_id=self.id,
            statut=statut,
            resume=resume.strip(),
            mesures=mesures,
            alertes=alertes,
            fragments_md=fragments,
        )
