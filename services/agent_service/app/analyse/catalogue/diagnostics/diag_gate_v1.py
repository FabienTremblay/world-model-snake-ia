"""Diagnostic: diag.gate_partition.v1 (tick-level + sanity check registre)

Mini-étape:
- On conserve le calcul tick-level (journal_agent.jsonl)
- On ajoute un sanity-check: si le registre_epistemique contient des ratios comparables,
  on calcule des deltas et on alerte si écart > epsilon.

Pourquoi:
- Garantir que ce que le registre "raconte" correspond au journal (source de vérité tick-level).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_service.app.analyse.noyau.types import ResultatDiagnostic, AlerteDiagnostic


DIAG_ID = "diag.gate_partition.v1"
TITRE = "partition du gate (connu vs inconnu: surprise / désaccord / intersection)"

DOC_COURTE = (
    "Mesure la partition 'connu' vs 'inconnu' et, pour l'inconnu, la part attribuable "
    "à la surprise, au désaccord, et à leur intersection (calcul tick-level). "
    "Compare aussi aux ratios présents dans le registre (sanity check)."
)

DOC_LONGUE = (
    "Diagnostic tick-level de la partition du gate.\n\n"
    "1) Source de vérité: journal_agent.jsonl (un enregistrement par tick).\n"
    "   - On calcule connu/inconnu via le champ 'mode'.\n"
    "   - Pour les ticks inconnu, on classe selon (surprise>=seuil_surprise) et (disagree>=seuil_disagree):\n"
    "     surprise seule / désaccord seul / intersection / autre.\n\n"
    "2) Sanity check: si registre_epistemique.json contient des ratios comparables (souvent agrégés),\n"
    "   on calcule des deltas et on alerte si l'écart dépasse un epsilon (par défaut 0.01).\n\n"
    "Ce diagnostic reste 'généralisé': il ne dépend pas de la structure exacte du registre, "
    "il cherche les clés attendues si elles existent."
)


EPSILON_DELTA = 0.01


def _get_attr(obj: Any, *noms: str, default=None):
    for n in noms:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


def _charger_json(path: Path) -> Any:
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def _charger_registre(contexte) -> Tuple[Optional[dict], Optional[str]]:
    r = _get_attr(contexte, "registre_epistemique", default=None)
    if isinstance(r, dict):
        return r, "contexte"
    if isinstance(r, str):
        p = Path(r)
        if p.is_file():
            return _charger_json(p), str(p)
    p = _get_attr(contexte, "chemin_registre_epistemique", default=None)
    if isinstance(p, str) and Path(p).is_file():
        return _charger_json(Path(p)), p
    return None, None


def _charger_journal(contexte) -> Tuple[List[dict], Optional[str]]:
    j = _get_attr(contexte, "journal_agent", default=None)
    if isinstance(j, list):
        return j, "contexte"

    p = _get_attr(contexte, "chemin_journal_agent", default=None)
    if isinstance(p, str) and Path(p).is_file():
        lignes = []
        with Path(p).open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    lignes.append(__import__("json").loads(line))
        return lignes, p

    return [], None


def _mode_est_inconnu(mode: Any) -> bool:
    return isinstance(mode, str) and "inconnu" in mode.lower()


def _collecter_floats(d: Any, prefix: str = "") -> Dict[str, float]:
    """Traverse récursivement un dict/list et retourne {chemin: float} pour les valeurs numériques."""
    out: Dict[str, float] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.update(_collecter_floats(v, p))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            p = f"{prefix}[{i}]"
            out.update(_collecter_floats(v, p))
    else:
        if isinstance(d, (int, float)):
            out[prefix] = float(d)
    return out


def _extraire_ratios_registre(registre: dict) -> Dict[str, float]:
    """Heuristique: extrait les ratios utiles si présents sous des clés attendues."""
    flat = _collecter_floats(registre)

    # clés cibles (suffixes possibles)
    cibles = {
        "ratio_connu_total": None,
        "ratio_inconnu_total": None,
        "ratio_inconnu_surprise_seul": None,
        "ratio_inconnu_disagree_seul": None,
        "ratio_inconnu_surprise_et_disagree": None,
        # compat ancienne version (any)
        "ratio_inconnu_surprise_any": None,
        "ratio_inconnu_disagree_any": None,
    }

    # stratégie: si un chemin se termine par le nom exact, on prend.
    for path, val in flat.items():
        for nom in list(cibles.keys()):
            if path.endswith(nom):
                cibles[nom] = val

    # fallback: anciens noms possibles (surprise/disagree "ratio_inconnu_surprise", etc.)
    if cibles["ratio_inconnu_surprise_any"] is None:
        for path, val in flat.items():
            if path.endswith("ratio_inconnu_surprise"):
                cibles["ratio_inconnu_surprise_any"] = val
                break
    if cibles["ratio_inconnu_disagree_any"] is None:
        for path, val in flat.items():
            if path.endswith("ratio_inconnu_disagree"):
                cibles["ratio_inconnu_disagree_any"] = val
                break

    # nettoie Nones
    return {k: v for k, v in cibles.items() if v is not None}


def executer(contexte) -> ResultatDiagnostic:
    journal, journal_src = _charger_journal(contexte)
    registre, registre_src = _charger_registre(contexte)

    if not journal:
        return ResultatDiagnostic(
            diagnostic_id=DIAG_ID,
            statut="skip",
            resume="journal_agent absent",
            mesures={"journal_source": journal_src, "registre_source": registre_src},
            alertes=[],
            fragments_md=[],
        )

    s_sur = journal[0].get("seuil_surprise")
    s_dis = journal[0].get("seuil_disagree")

    n_total = len(journal)
    n_connu = 0
    n_inconnu = 0

    n_sur_only = 0
    n_dis_only = 0
    n_both = 0
    n_other = 0

    for tick in journal:
        mode = tick.get("mode")
        is_inconnu = _mode_est_inconnu(mode)

        if is_inconnu:
            n_inconnu += 1
        else:
            n_connu += 1

        surprise = tick.get("surprise")
        disagree = tick.get("disagree")

        is_sur = s_sur is not None and isinstance(surprise, (int, float)) and surprise >= s_sur
        is_dis = s_dis is not None and isinstance(disagree, (int, float)) and disagree >= s_dis

        if is_inconnu:
            if is_sur and is_dis:
                n_both += 1
            elif is_sur:
                n_sur_only += 1
            elif is_dis:
                n_dis_only += 1
            else:
                n_other += 1

    def r(x: int) -> float:
        return x / n_total if n_total else 0.0

    mesures: Dict[str, Any] = {
        "n": n_total,
        "journal_source": journal_src,
        "registre_source": registre_src,
        "ratio_connu_total": r(n_connu),
        "ratio_inconnu_total": r(n_inconnu),
        "ratio_inconnu_surprise_seul": r(n_sur_only),
        "ratio_inconnu_disagree_seul": r(n_dis_only),
        "ratio_inconnu_surprise_et_disagree": r(n_both),
        "ratio_inconnu_autre": r(n_other),
        # pour comparaison "ancienne" (any)
        "ratio_inconnu_surprise_any": r(n_sur_only + n_both),
        "ratio_inconnu_disagree_any": r(n_dis_only + n_both),
        "epsilon_delta_registre": EPSILON_DELTA,
    }

    resume = (
        f"gate tick-level: connu={mesures['ratio_connu_total']:.3f} "
        f"inconnu={mesures['ratio_inconnu_total']:.3f} "
        f"(sur={mesures['ratio_inconnu_surprise_seul']:.3f}, "
        f"dis={mesures['ratio_inconnu_disagree_seul']:.3f}, "
        f"both={mesures['ratio_inconnu_surprise_et_disagree']:.3f})"
    )

    table_md = (
        "| catégorie (inconnu) | ratio |\n"
        "|---|---:|\n"
        f"| surprise seule | {mesures['ratio_inconnu_surprise_seul']:.6f} |\n"
        f"| désaccord seul | {mesures['ratio_inconnu_disagree_seul']:.6f} |\n"
        f"| surprise ∩ désaccord | {mesures['ratio_inconnu_surprise_et_disagree']:.6f} |\n"
        f"| autre | {mesures['ratio_inconnu_autre']:.6f} |\n"
    )

    alertes: List[AlerteDiagnostic] = []
    statut = "ok"

    # Sanity check registre vs tick-level
    ratios_reg = _extraire_ratios_registre(registre) if isinstance(registre, dict) else {}
    mesures["ratios_registre"] = ratios_reg
    if ratios_reg:
        deltas: Dict[str, float] = {}
        for k, v_reg in ratios_reg.items():
            v_tick = mesures.get(k)
            if isinstance(v_tick, (int, float)):
                deltas[f"delta_{k}"] = float(v_tick) - float(v_reg)
        mesures["deltas_registre"] = deltas

        # alerte si un delta dépasse epsilon
        gros = {k: v for k, v in deltas.items() if abs(v) > EPSILON_DELTA}
        if gros:
            statut = "warn"
            alertes.append(
                AlerteDiagnostic(
                    niveau="warn",
                    message="écarts registre vs tick-level au-delà de l'epsilon",
                    quoi_faire=(
                        "Vérifier si le registre est calculé sur la même fenêtre (ticks), "
                        "la même définition des catégories (exclusive vs any), et les mêmes seuils. "
                        "Si c'est voulu, documenter la différence."
                    ),
                )
            )
    else:
        mesures["ratios_registre"] = {}
        mesures["deltas_registre"] = {}

    # Intersection notable -> warn (informative)
    if mesures["ratio_inconnu_surprise_et_disagree"] > 0.01:
        statut = "warn" if statut == "ok" else statut
        alertes.append(
            AlerteDiagnostic(
                niveau="warn",
                message="intersection surprise∩désaccord non négligeable (tick-level)",
                quoi_faire="Décider/expliciter une règle de priorité (surprise vs désaccord) ou conserver l'intersection et l'interpréter.",
            )
        )

    return ResultatDiagnostic(
        diagnostic_id=DIAG_ID,
        statut=statut,
        resume=resume,
        mesures=mesures,
        alertes=alertes,
        fragments_md=[table_md],
    )


@dataclass(frozen=True)
class DiagnosticGatePartitionV1:
    # compat catalogue
    id: str = DIAG_ID

    diagnostic_id: str = DIAG_ID
    titre: str = TITRE
    doc_courte: str = DOC_COURTE
    doc_longue: str = DOC_LONGUE

    def preconditions(self) -> List[str]:
        return ["journal_agent doit contenir mode, surprise, disagree, seuil_surprise, seuil_disagree"]

    def executer(self, contexte) -> ResultatDiagnostic:
        return executer(contexte)


DIAGNOSTIC = DiagnosticGatePartitionV1()
