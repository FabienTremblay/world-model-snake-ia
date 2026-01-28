"""Agents disponibles.

On évite de casser le mode `aleatoire` si un agent optionnel (curiosité) a une dépendance
temporairement incohérente suite à un refactor.
"""

from .agent_aleatoire import AgentAleatoire

try:
    from .agent_curiosite_tabulaire import AgentCuriositeTabulaire
except Exception:  # pragma: no cover
    AgentCuriositeTabulaire = None  # type: ignore
