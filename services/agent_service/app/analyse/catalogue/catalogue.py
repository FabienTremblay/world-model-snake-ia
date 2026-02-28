"""Catalogue exécutable des diagnostics SAI-A105.

Le catalogue sert de registre stable:
- liste des diagnostics disponibles
- doc intégrée (courte + longue)
- factory d'instances

Le CLI/TUI s'appuie sur ce catalogue.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from ..noyau.types import Diagnostic, DocDiagnostic

from .diagnostics.diag_poids_adaptatifs_v1 import DiagnosticPoidsAdaptatifsV1
from .diagnostics.diag_gate_v1 import DiagnosticGatePartitionV1
from .diagnostics.diag_disagree_plateau_v1 import DiagnosticDisagreePlateauV1


_REGISTRE: Dict[str, Type[Diagnostic]] = {
    DiagnosticPoidsAdaptatifsV1.id: DiagnosticPoidsAdaptatifsV1,
    DiagnosticGatePartitionV1.id: DiagnosticGatePartitionV1,
    DiagnosticDisagreePlateauV1.id: DiagnosticDisagreePlateauV1,
}


def liste_diagnostics() -> List[str]:
    return sorted(_REGISTRE.keys())


def get_diagnostic(diagnostic_id: str) -> Diagnostic:
    if diagnostic_id not in _REGISTRE:
        raise KeyError(f"Diagnostic inconnu: {diagnostic_id}. Disponibles: {liste_diagnostics()}")
    return _REGISTRE[diagnostic_id]()


def docs(diagnostic_id: str) -> DocDiagnostic:
    return get_diagnostic(diagnostic_id).doc()


def set_minimum_v1() -> List[str]:
    """Ensemble par défaut (minimum viable)"""

    return [
        DiagnosticPoidsAdaptatifsV1.id,
        DiagnosticGatePartitionV1.id,
        DiagnosticDisagreePlateauV1.id,
    ]


# Ensembles (sets) nommés
_LISTE_SETS = {
    "minimum_v1": set_minimum_v1,
    "jepa5_v1": set_minimum_v1,  # alias (mêmes diagnostics)
}


def liste_sets() -> List[str]:
    return sorted(_LISTE_SETS.keys())


def get_set(nom_set: str) -> List[str]:
    if nom_set not in _LISTE_SETS:
        raise KeyError(f"Set inconnu: {nom_set}. Disponibles: {liste_sets()}")
    return _LISTE_SETS[nom_set]()
