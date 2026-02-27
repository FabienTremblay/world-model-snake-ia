"""Types de base pour SAI-A105 (Analyse des résultats).

Objectifs:
- Contrats stables (diagnostic, résultat) pour usage CLI et TUI.
- Sorties JSON sérialisables.

Tout est en français volontairement (convention du projet).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional


NiveauAlerte = Literal["info", "warn", "fail"]
StatutDiagnostic = Literal["ok", "warn", "fail", "skip"]


@dataclass(frozen=True)
class AlerteDiagnostic:
    """Message court + action recommandée."""

    niveau: NiveauAlerte
    message: str
    quoi_faire: str = ""


@dataclass(frozen=True)
class DocDiagnostic:
    """Documentation intégrée d'un diagnostic (affichable dans le TUI)."""

    titre: str
    doc_courte: str
    doc_longue: str
    entrees: List[str] = field(default_factory=list)
    sorties: List[str] = field(default_factory=list)


@dataclass
class SectionRapport:
    """Section rendue dans rapport_diagnostics.md."""

    titre: str
    contenu_md: str


@dataclass
class ResultatDiagnostic:
    """Résultat d'un diagnostic.

    - mesures: dict JSON sérialisable
    - alertes: liste d'alertes courtes et actionnables
    - fragments_md: fragments Markdown (ex.: listes, tableaux) intégrés au rapport
    """

    diagnostic_id: str
    statut: StatutDiagnostic
    resume: str
    mesures: Dict[str, Any] = field(default_factory=dict)
    alertes: List[AlerteDiagnostic] = field(default_factory=list)
    fragments_md: List[str] = field(default_factory=list)

    def vers_json(self) -> Dict[str, Any]:
        return {
            "diagnostic_id": self.diagnostic_id,
            "statut": self.statut,
            "resume": self.resume,
            "mesures": self.mesures,
            "alertes": [asdict(a) for a in self.alertes],
        }


@dataclass
class ContexteRun:
    """Contexte d'analyse d'un run.

    Les champs contiennent les artefacts chargés (dict/objets python).
    """

    run_dir: Path
    epreuve_dir: Path
    experience_id: Optional[str] = None
    run_id: Optional[str] = None

    # Artefacts
    config_epreuve: Dict[str, Any] = field(default_factory=dict)
    registre_epistemique: Dict[str, Any] = field(default_factory=dict)
    journal_agent: List[Dict[str, Any]] = field(default_factory=list)

    # Aide
    chemins: Dict[str, str] = field(default_factory=dict)


class Diagnostic:
    """Interface minimale d'un diagnostic."""

    id: str

    def doc(self) -> DocDiagnostic:  # pragma: no cover
        raise NotImplementedError

    def preconditions(self, contexte: ContexteRun) -> List[AlerteDiagnostic]:
        """Retourne une liste d'alertes si des champs requis manquent.

        Une precondition non satisfaite devrait conduire à un statut 'skip'.
        """

        return []

    def executer(self, contexte: ContexteRun) -> ResultatDiagnostic:  # pragma: no cover
        raise NotImplementedError

    def sections_rapport(self, resultat: ResultatDiagnostic, contexte: ContexteRun) -> List[SectionRapport]:
        """Sections spécifiques (optionnelles) ajoutées au rapport."""

        # Par défaut, aucune section additionnelle.
        return []
