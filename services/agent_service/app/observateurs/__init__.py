# services/agent_service/app/observateurs/__init__.py
"""Observateurs.

Un observateur transforme des signaux (souvent perçus) en "intérêt" / utilité,
sans présumer de l'ontologie au départ.
"""

from .observateur_croissance_v1 import ObservateurCroissanceV1

__all__ = ["ObservateurCroissanceV1"]

