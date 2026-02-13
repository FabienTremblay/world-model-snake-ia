from __future__ import annotations

from .contrats import HypotheseV2, IndicesEpistemiques


def inferer_hypotheses(indices: IndicesEpistemiques) -> list[HypotheseV2]:
    """Infère des hypothèses *épistémiques* (diagnostic + orientation).

    - Diagnostic : latent trop discriminant, biais d'action, etc.
    - Orientation : exploration faible, stationnaire, revisite.
    """
    hyps: list[HypotheseV2] = []

    # --- latent ---
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
                    evidences={"latents_distincts": indices.latents_distincts, "ticks": indices.ticks, "ratio": ratio},
                )
            )

    # --- actions ---
    if indices.actions:
        total = sum(indices.actions.values())
        top = sorted(indices.actions.items(), key=lambda kv: kv[1], reverse=True)[:3]
        if total > 0 and top and (top[0][1] / total) > 0.65:
            hyps.append(
                HypotheseV2(
                    id="biais_action_fort",
                    titre="biais fort vers une action",
                    description=(
                        "Une action domine nettement la distribution des actions. "
                        "Cela peut indiquer un agent stationnaire, un bug d'action, ou une gouvernance trop rigide."
                    ),
                    confiance=0.6,
                    evidences={"total": total, "top_actions": top},
                )
            )

    # --- métriques (checksum) : exploration / stationnaire ---
    if indices.metrics_present:
        if indices.ratio_stationnaire is not None and indices.ratio_stationnaire > 0.2:
            hyps.append(
                HypotheseV2(
                    id="beaucoup_actions_nulles",
                    titre="beaucoup d'actions sans effet (stationnaire)",
                    description=(
                        "Le taux de transitions où l'état ne change pas (checksum == checksum_avant) est élevé. "
                        "Souvent signe d'actions bloquées, de rebonds, ou de boucles locales."
                    ),
                    confiance=0.7,
                    evidences={"ratio_stationnaire": indices.ratio_stationnaire, "transitions": indices.transitions},
                )
            )

        if indices.ratio_revisite_etats is not None and indices.ratio_revisite_etats > 0.8:
            hyps.append(
                HypotheseV2(
                    id="revisite_elevee",
                    titre="revisite des états très élevée",
                    description=(
                        "Proxy simple : 1 - (états uniques / transitions). "
                        "Si ce ratio est élevé, l'agent revisite massivement les mêmes états (boucles probables)."
                    ),
                    confiance=0.65,
                    evidences={
                        "ratio_revisite": indices.ratio_revisite_etats,
                        "etats_uniques": indices.etats_uniques,
                        "transitions": indices.transitions,
                    },
                )
            )

    return hyps
