# services/runner/app/main.py
from __future__ import annotations

import time
from pathlib import Path

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Observation

from world_sim.app.monde_snake import ConfigMonde, MondeSnake
from runner.app.journal import JournalEpisodes


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

def boucle_episodes(
    bus: BusEtatMemoire,
    controle: ControleExecution,
    ticks_max: int = 10_000,
) -> None:
    cfg = ConfigMonde(largeur=30, hauteur=12, seed=12345, nb_nourriture=1, niveau_bruit=0)
    # root projet = 3 niveaux au-dessus de services/runner/app
    racine_projet = Path(__file__).resolve().parents[3]
    journal = JournalEpisodes(racine_projet=racine_projet)
    episode_id = 0
    # Identifiant de session (stable pour tout le process)
    run_id = str(time.time_ns())

    while True:
        episode_id += 1
        monde = MondeSnake(cfg)

        # bruit piloté par TUI
        niveau_bruit = controle.niveau_bruit()
        capteurs, rendu_debug = monde.observer(niveau_bruit=niveau_bruit)
        capteurs_canon, _ = monde.observer(niveau_bruit=0)
        mesure_bruit = _mesurer_bruit(capteurs_canon, capteurs)
        # observation initiale
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
            action_direction=None,
            niveau_bruit=niveau_bruit,
            score=monde.score,
            longueur=len(monde.serpent),
            termine=monde.termine,
            raison_fin=monde.raison_fin,
            capteurs=capteurs,
        )

        for _ in range(ticks_max):
            # reset demandé ? on redémarre un épisode immédiatement
            if controle.consommer_reset():
                break

            controle.attendre_autorisation()

            # reset peut aussi être demandé pendant l'attente
            if controle.consommer_reset():
                break

            # mode assisté: direction 1-shot si fournie par le TUI
            direction = controle.consommer_direction()
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
                action_direction=direction,
                niveau_bruit=niveau_bruit,
                score=monde.score,
                longueur=len(monde.serpent),
                termine=monde.termine,
                raison_fin=monde.raison_fin,
                capteurs=capteurs,
            )

            if monde.termine:
                # Ne PAS enchaîner automatiquement.
                # On attend un reset explicite (r) pour démarrer un nouvel épisode.
                while True:
                    # si reset => on sort et on recrée un monde (nouvel episode_id)
                    if controle.consommer_reset():
                        break
                    # sinon, on laisse le TUI vivre (pause/step/vitesse)
                    # step n'a pas d'effet ici: épisode terminé.
                    time.sleep(0.05)
                break

            time.sleep(controle.delai_s())


def main() -> None:
    bus = BusEtatMemoire()
    controle = ControleExecution(delai_s=0.05)
    boucle_episodes(bus, controle)


if __name__ == "__main__":
    main()

