from __future__ import annotations

from .contrats import HypotheseV2, IndicesEpistemiques


def inferer_hypotheses(indices: IndicesEpistemiques) -> list[HypotheseV2]:
    hyps: list[HypotheseV2] = []

    if indices.latents_distincts is not None and indices.ticks > 0:
        ratio = indices.latents_distincts / max(1, indices.ticks)
        if ratio > 0.4:
            hyps.append(
                HypotheseV2(
                    id="latent_trop_discriminant",
                    titre="le latent est trop discriminant",
                    description=(
                        "Le nombre de latents distincts est élevé par rapport au nombre de ticks, "
                        "ce qui suggère une représentation trop fine (ex: checksum) et donc un support fragmenté."
                    ),
                    confiance=0.7,
                    evidences={
                        "latents_distincts": indices.latents_distincts,
                        "ticks": indices.ticks,
                        "ratio": ratio,
                    },
                    conditions=[
                        "vérifier le mode latent (checksum vs discret_v1 vs signaux_percus_hash_v1)",
                        "vérifier le niveau de bruit et la sensibilité du latent",
                    ],
                )
            )

    total_fin = sum(indices.raisons_fin.values())
    if total_fin >= 10:
        raison, n = max(indices.raisons_fin.items(), key=lambda kv: kv[1])
        part = n / total_fin
        if part >= 0.75:
            hyps.append(
                HypotheseV2(
                    id="raison_fin_dominante",
                    titre="une seule raison de fin domine",
                    description=(
                        "La majorité des épisodes terminent de la même manière. "
                        "C'est un signal d'un biais (arène, agent, ou capteurs/latent)."
                    ),
                    confiance=0.6,
                    evidences={"raison_fin": raison, "part": part, "total": total_fin},
                    conditions=[
                        "inspecter les épisodes correspondants (replay)",
                        "tester un agent de référence (aléatoire) sur la même arène",
                    ],
                )
            )

    total_actions = sum(indices.actions.values())
    if total_actions >= 50:
        action, n = max(indices.actions.items(), key=lambda kv: kv[1])
        part = n / total_actions
        if part >= 0.8:
            hyps.append(
                HypotheseV2(
                    id="biais_action",
                    titre="l'agent utilise massivement une seule action",
                    description=(
                        "Une action est choisie dans une proportion très élevée. "
                        "Cela peut indiquer une politique dégénérée ou un bug de décision."
                    ),
                    confiance=0.6,
                    evidences={"action": action, "part": part, "total": total_actions},
                    conditions=[
                        "valider la sortie du choix d'action (mapping)",
                        "examiner la configuration de l'agent (epsilon, etc.)",
                    ],
                )
            )

    return hyps
