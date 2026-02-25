"""
Modèles prédictifs pour simulation interne.
"""
from .modele_predictif_base import ModelePredicifBase
from .modele_pred_capteurs_v1 import ModelePredCapteursV1

__all__ = [
    'ModelePredicifBase',
    'ModelePredCapteursV1',
]
