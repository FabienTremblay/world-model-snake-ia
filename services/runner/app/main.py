# services/runner/app/main.py
from __future__ import annotations

import os
import time
from pathlib import Path

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Observation

from world_sim.app.monde_snake import ConfigMonde, MondeSnake
from world_sim.app.arenes_yaml import charger_arene_v0
from runner.app.journal import JournalEpisodes

from agent_service.app.agent_runtime.agents_in_arene.contrats import ContexteDecision, ContextePerception, IAgent


def _mesurer_bruit(capteurs_canon, capteurs):
    # métriques simples: delta teinte moyen (cercle) et delta intensité moyen
    h = len(capteurs)
    w = len(capteurs[0]) if h else 0
    if h == 0 or w == 0:
        return "bruit: n/a"
    somme_dt = 0.0
    somme_di = 0.0
    n = h * w
    for y in range(h):
        for x in range(w):
            a = capteurs_canon[y][x]
            b = capteurs[y][x]
            # distance circulaire teinte
            d = abs(a.teinte - b.teinte) % 360
            dt = min(d, 360 - d)
            somme_dt += dt
            somme_di += abs(a.intensite - b.intensite)
    return f"bruit: Δteinte≈{somme_dt/n:.1f}, Δint≈{somme_di/n:.1f}"


def _fabriquer_agent_depuis_env() -> IAgent | None:
    """Option TUI : si SNAKE_AGENT est défini, on joue en mode auto.

    Exemples :
      - SNAKE_AGENT=aleatoire
      - SNAKE_AGENT=curiosite_tabulaire
      - SNAKE_AGENT=planif_mpc_tabulaire
      - SNAKE_AGENT=planif_mpc_observateur_tabulaire
      - SNAKE_AGENT=planif_1pas_temperament

    Paramètres :
      - SNAKE_AGENT_SEED (int)
      - SNAKE_AGENT_EPSILON (float)
      - SNAKE_AGENT_LATENT (str, ex: checksum, signaux_percus_hash_v1)
    """
    nom = os.getenv("SNAKE_AGENT", "").strip().lower()
    if not nom:
        return None

    seed = os.getenv("SNAKE_AGENT_SEED")
    epsilon = os.getenv("SNAKE_AGENT_EPSILON", "0.0")
    mode_latent = os.getenv("SNAKE_AGENT_LATENT", "checksum")

    seed_int = int(seed) if seed not in (None, "") else None

    # On privilégie `agent_runtime` (cours 5) ; wrappers vers cours 4.
    if nom == "aleatoire":
        from agent_service.app.agent_runtime.agents_in_arene import AgentAleatoire

        return AgentAleatoire(seed=seed_int, epsilon=float(epsilon))

    if nom == "curiosite_tabulaire":
        # paramètres de curiosité définis dans le module historique (cours 4)
        from agent_service.app.agents.agent_curiosite_tabulaire import ParametresCuriosite
        from agent_service.app.agent_runtime.agents_in_arene import AgentCuriositeTabulaire

        params = ParametresCuriosite(
            epsilon=float(epsilon),
            w_inconnu=float(os.getenv("SNAKE_W_INCONNU", "1.0")),
            w_entropie=float(os.getenv("SNAKE_W_ENTROPIE", "1.0")),
            w_inconfiance=float(os.getenv("SNAKE_W_INCONFIANCE", "1.0")),
        )
        return AgentCuriositeTabulaire(seed=seed_int, params=params, mode_latent=mode_latent)

    if nom == "planif_mpc_tabulaire":
        from agent_service.app.agent_runtime.agents_in_arene.agent_planif_mpc_tabulaire import (
            AgentPlanifMPC as AgentPlanifMPCTabulaire,
        )

        return AgentPlanifMPCTabulaire(seed=seed_int, mode_latent=mode_latent)

    if nom == "planif_mpc_observateur_tabulaire":
        from agent_service.app.agent_runtime.agents_in_arene.agent_planif_mpc_observateur_tabulaire import (
            AgentPlanifMPCObservateurTabulaire,
        )

        return AgentPlanifMPCObservateurTabulaire(seed=seed_int, mode_latent=mode_latent)

    if nom == "planif_1pas_temperament":
        from agent_service.app.agent_runtime.agents_in_arene.agent_planif_1pas_temperament_v1 import (
            AgentPlanif1PasTemperamentV1,
        )

        return AgentPlanif1PasTemperamentV1(seed=seed_int, mode_latent=mode_latent)

    raise SystemExit(f"SNAKE_AGENT inconnu: {nom!r}")


def boucle_episodes(
    bus: BusEtatMemoire,
    controle: ControleExecution,
    ticks_max: int = 10_000,
) -> None:
    # root projet = 3 niveaux au-dessus de services/runner/app
    racine_projet = Path(__file__).resolve().parents[3]

    # arène (donnée)
    arene_id = os.getenv("SNAKE_ARENE", "demo_v0").strip()
    path_arene = racine_projet / "donnees" / "config" / "arenes" / f"{arene_id}.yml"
    ar = charger_arene_v0(path_arene)
    cfg = ConfigMonde(
        largeur=ar.largeur,
        hauteur=ar.hauteur,
        seed=ar.seed,
        nb_nourriture=ar.nb_nourriture,
        niveau_bruit=ar.niveau_bruit_defaut,
        arene_id=ar.id,
        epsilon_par_pas=ar.epsilon_par_pas,
        bonus_fin=ar.bonus_fin,
        porte_position=ar.porte_position,
        porte_ouverte_initiale=(ar.porte_etat_initial == "ouverte"),
        regle_ouverture_porte=ar.regle_ouverture,
        palette=ar.palette,
    )

    # journal (optionnel)
    journal = JournalEpisodes(racine_projet)

    # agent auto (optionnel) — sinon mode manuel (direction via TUI)
    agent = _fabriquer_agent_depuis_env()
    perception = ContextePerception(champ_vision_deg=180)

    run_id = time.strftime("%Y%m%d_%H%M%S")
    episode_id = 0

    while True:
        monde = MondeSnake(cfg)
        monde.reset()
        niveau_bruit = controle.niveau_bruit()
        capteurs, rendu_debug = monde.observer(niveau_bruit=niveau_bruit)

        bus.publier(
            Observation(
                run_id=run_id,
                episode_id=episode_id,
                tick=monde.tick,
                capteurs=capteurs,
                rendu_debug=rendu_debug,
                mesure_bruit="",
                score=monde.score,
                longueur=len(monde.serpent),
                termine=monde.termine,
                raison_fin=monde.raison_fin,
            )
        )
        journal.ecrire_tick(
            run_id=run_id,
            episode_id=episode_id,
            tick=monde.tick,
            arene_id=cfg.arene_id,
            seed=cfg.seed,
            action_direction=None,
            niveau_bruit=niveau_bruit,
            score=monde.score,
            longueur=len(monde.serpent),
            termine=monde.termine,
            raison_fin=monde.raison_fin,
            capteurs=capteurs,
        )

        for _ in range(ticks_max):
            if controle.consommer_reset():
                break

            controle.attendre_autorisation()

            if controle.consommer_reset():
                break

            if agent is None:
                # mode assisté: direction 1-shot si fournie par le TUI
                direction = controle.consommer_direction()
                monde.step(direction=direction)
            else:
                # mode auto: l'agent décide depuis l'observation courante
                contexte = ContexteDecision(
                    run_id=run_id,
                    episode_id=episode_id,
                    tick=monde.tick,
                    largeur=cfg.largeur,
                    hauteur=cfg.hauteur,
                    perception=perception,
                )
                direction = agent.choisir_action(capteurs=capteurs, contexte=contexte)
                monde.step(direction=direction)

            niveau_bruit = controle.niveau_bruit()
            capteurs, rendu_debug = monde.observer(niveau_bruit=niveau_bruit)
            capteurs_canon, _ = monde.observer(niveau_bruit=0)
            mesure_bruit = _mesurer_bruit(capteurs_canon, capteurs)

            bus.publier(
                Observation(
                    run_id=run_id,
                    episode_id=episode_id,
                    tick=monde.tick,
                    capteurs=capteurs,
                    rendu_debug=rendu_debug,
                    mesure_bruit=mesure_bruit,
                    score=monde.score,
                    longueur=len(monde.serpent),
                    termine=monde.termine,
                    raison_fin=monde.raison_fin,
                )
            )
            journal.ecrire_tick(
                run_id=run_id,
                episode_id=episode_id,
                tick=monde.tick,
                arene_id=cfg.arene_id,
                seed=cfg.seed,
                action_direction=direction,
                niveau_bruit=niveau_bruit,
                score=monde.score,
                longueur=len(monde.serpent),
                termine=monde.termine,
                raison_fin=monde.raison_fin,
                capteurs=capteurs,
            )

            if monde.termine:
                while True:
                    if controle.consommer_reset():
                        break
                    time.sleep(0.05)
                break

            # cadence UI
            time.sleep(controle.delai_s())

        episode_id += 1


def main() -> None:
    bus = BusEtatMemoire()
    controle = ControleExecution(delai_s=0.05)
    boucle_episodes(bus, controle)


if __name__ == "__main__":
    main()
