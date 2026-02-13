from __future__ import annotations

from .contrats import IndicesEpistemiques


def produire_concepts_candidates(indices: IndicesEpistemiques) -> list[dict]:
    """Produit des concepts candidats *instillables* à partir des indices.

    Remarque : on reste volontairement "agnostique" (pas de mur, pas de nourriture).
    On travaille sur des invariants observables :
    - action nulle (état inchangé)
    - transition dominante (état,action -> état2)
    - boucle / revisite (proxy)
    """
    concepts: list[dict] = []

    if not indices.metrics_present:
        return concepts

    # 1) actions nulles
    if indices.actions_nulles_top:
        for cle, support in indices.actions_nulles_top[:10]:
            # cle = "etat|action"
            etat, action = cle.split("|", 1)
            concepts.append(
                {
                    "id": "action_nulle",
                    "titre": "action nulle (état inchangé)",
                    "cible": {"etat": int(etat), "action": action},
                    "support": int(support),
                    "confiance": 0.9,
                    "preuve": {"regle": "checksum == checksum_avant"},
                }
            )

    # 2) transitions dominantes
    if indices.transitions_top:
        for cle, support in indices.transitions_top[:10]:
            # cle = "etat|action|etat2"
            etat, action, etat2 = cle.split("|", 2)
            concepts.append(
                {
                    "id": "transition_dominante",
                    "titre": "transition dominante",
                    "cible": {"etat": int(etat), "action": action},
                    "hypothese": {"etat_suivant": int(etat2)},
                    "support": int(support),
                    "confiance": 0.75,
                }
            )

    # 3) indices globaux utilisables
    if indices.ratio_stationnaire is not None and indices.ratio_stationnaire > 0.2:
        concepts.append(
            {
                "id": "tendance_stationnaire",
                "titre": "fort taux d'actions sans effet",
                "cible": {"ratio_stationnaire": float(indices.ratio_stationnaire)},
                "support": int(indices.transitions or 0),
                "confiance": 0.7,
            }
        )

    if indices.ratio_revisite_etats is not None and indices.ratio_revisite_etats > 0.8:
        concepts.append(
            {
                "id": "boucle_probable",
                "titre": "boucle / revisite élevée (proxy)",
                "cible": {"ratio_revisite": float(indices.ratio_revisite_etats)},
                "support": int(indices.transitions or 0),
                "confiance": 0.7,
            }
        )

    return concepts
