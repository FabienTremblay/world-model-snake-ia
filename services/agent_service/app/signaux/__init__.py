# services/agent_service/app/signaux/__init__.py
"""Signaux.

Cours 4 : on distingue deux niveaux.

1) signaux du monde : ce qui se passe objectivement dans l'environnement
2) signaux perçus : ce qu'un agent (ou un observateur) détecte réellement,
   selon ses modalités et limites de perception
"""

from .signaux_monde_v1 import extraire_signaux_monde_v1
from .signaux_percus_v1 import extraire_signaux_percus_v1

__all__ = [
    "extraire_signaux_monde_v1",
    "extraire_signaux_percus_v1",
]

