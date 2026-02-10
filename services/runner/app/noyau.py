# services/runner/app/noyau.py
from __future__ import annotations

"""Noyau d'exécution (Cours 5)

Objectif
--------
Éviter le développement en double (CLI vs autres interfaces) en fournissant
un noyau commun pour l'exécution d'épisodes.

Portée
------
- Mode "headless" / batch (utilisé par ui_cli).
- Le noyau orchestre : monde, agent, temps, journal.
- Le noyau ne fait ni diagnostic, ni épistémique, ni évaluation.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from agent_service.app.contrats_agents import ContexteDecision, ContextePerception, IAgentArene
from instrument.app.contrats import EtatMondeCanonique, ObservationInstrument, ObservationPixels
from runner.app.journal import JournalEpisodes
from world_sim.app.monde_snake import ConfigMonde, MondeSnake


@dataclass(frozen=True)
class ParametresExecution:
    """Paramètres d'exécution communs."""

    episodes: int = 100
    max_ticks: int = 2_000
    # si True : varie le seed du monde par épisode (seed_base + episode_id)
    seed_episode: bool = False


# Hooks optionnels (pour CLI : métriques, apprentissage, etc.)
HookTick0 = Callable[[str, int, MondeSnake, list], None]
HookApresAction = Callable[[str, int, MondeSnake, str, str, str, list, list], None]
# signature hook_apres_action :
# (run_id, episode_id, monde, action, z_avant, z_apres, capteurs_avant, capteurs_apres)


def _etat_canonique_depuis_monde(monde: MondeSnake, cfg: ConfigMonde) -> EtatMondeCanonique:
    return EtatMondeCanonique(
        largeur=cfg.largeur,
        hauteur=cfg.hauteur,
        serpent=list(getattr(monde, "serpent", [])),
        direction=getattr(monde, "direction", None),
        nourritures=set(getattr(monde, "nourriture", [])) if hasattr(monde, "nourriture") else set(),
        porte=getattr(monde, "porte_pos", None),
        porte_ouverte=bool(getattr(monde, "porte_ouverte", False)),
        palette=cfg.palette,
    )


def _observer_instruments(insts, etat: EtatMondeCanonique) -> dict[str, ObservationInstrument]:
    sorties: dict[str, ObservationInstrument] = {}
    for inst in insts:
        obs = inst.observer(etat)
        sorties[getattr(inst, "instrument_id", inst.__class__.__name__)] = obs
    return sorties


def _capteurs_depuis_observations(obs: dict[str, ObservationInstrument]) -> list | None:
    for v in obs.values():
        if isinstance(v, ObservationPixels):
            return v.pixels
    return None


def executer_episodes_headless(
    *,
    run_id: str,
    cfg_base: ConfigMonde,
    agent: IAgentArene,
    journal: JournalEpisodes,
    params: ParametresExecution,
    # perception par défaut côté agent (point de vue incarné)
    perception: ContextePerception | None = None,
    # encodeur latent optionnel (pour métriques + apprentissage en ligne)
    encoder_latent: Optional[Callable[[list, str], str]] = None,
    mode_latent: str = "checksum",
    # hooks
    hook_tick0: HookTick0 | None = None,
    hook_apres_action: HookApresAction | None = None,
) -> None:
    """Exécute des épisodes en mode batch.

    Notes
    -----
    - Le runner écrit systématiquement le tick 0 (action=None) dans le journal.
    - Le choix d'action est fait à partir des capteurs de l'état courant (tick t),
      puis on applique l'action et on journalise l'état résultant (tick t+1).
    """

    if perception is None:
        perception = ContextePerception(run_id=None, episode_id=None, tick=0, observations={})

    episodes = int(params.episodes)
    max_ticks = int(params.max_ticks)

    base_seed = getattr(cfg_base, "seed", None)

    for episode_id in range(1, episodes + 1):
        cfg = cfg_base

        if params.seed_episode and base_seed is not None:
            # compat pydantic v1/v2
            if hasattr(cfg_base, "model_copy"):
                cfg = cfg_base.model_copy(update={"seed": int(base_seed) + episode_id})
            else:
                cfg = ConfigMonde(**{**cfg_base.__dict__, "seed": int(base_seed) + episode_id})

        monde = MondeSnake(cfg)

        # tick 0
        capteurs, _ = monde.observer(niveau_bruit=cfg.niveau_bruit)
        journal.ecrire_tick(
            run_id=run_id,
            episode_id=episode_id,
            tick=monde.tick,
            arene_id=cfg.arene_id,
            seed=cfg.seed,
            action_direction=None,
            niveau_bruit=cfg.niveau_bruit,
            score=monde.score,
            longueur=len(monde.serpent),
            termine=monde.termine,
            raison_fin=monde.raison_fin,
            capteurs=capteurs,
        )
        if hook_tick0 is not None:
            hook_tick0(run_id, episode_id, monde, capteurs)

        # ticks
        for _ in range(max_ticks):
            # instruments -> observations pour la décision
            etat_canonique = _etat_canonique_depuis_monde(monde, cfg)
            insts = list(agent.instruments())
            observations = _observer_instruments(insts, etat_canonique)

            ctx = ContexteDecision(
                run_id=run_id,
                episode_id=episode_id,
                tick=monde.tick,
                observations=observations,
                info={"largeur": cfg.largeur, "hauteur": cfg.hauteur, "direction": getattr(monde, "direction", None)},
            )

            action = agent.choisir_action(ctx)
            if action is None:
                raise RuntimeError(f"agent a retourné None: {type(agent).__module__}.{type(agent).__name__}")

            z_avant = ""
            z_apres = ""
            if encoder_latent is not None:
                capteurs_avant = _capteurs_depuis_observations(observations) or capteurs
                z_avant = encoder_latent(capteurs_avant, mode_latent)

            # appliquer => tick t+1
            monde.step(direction=action)
            capteurs_apres, _ = monde.observer(niveau_bruit=cfg.niveau_bruit)

            if encoder_latent is not None:
                z_apres = encoder_latent(capteurs_apres, mode_latent)

            journal.ecrire_tick(
                run_id=run_id,
                episode_id=episode_id,
                tick=monde.tick,
                arene_id=cfg.arene_id,
                seed=cfg.seed,
                action_direction=action,
                niveau_bruit=cfg.niveau_bruit,
                score=monde.score,
                longueur=len(monde.serpent),
                termine=monde.termine,
                raison_fin=monde.raison_fin,
                capteurs=capteurs_apres,
            )

            if hook_apres_action is not None:
                hook_apres_action(
                    run_id,
                    episode_id,
                    monde,
                    action,
                    z_avant,
                    z_apres,
                    capteurs,
                    capteurs_apres,
                )

            capteurs = capteurs_apres
            if monde.termine:
                break
