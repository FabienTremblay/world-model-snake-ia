# services/ui_cli/app/main.py
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from agent_service.app.agents import AgentAleatoire, AgentCuriositeTabulaire
from agent_service.app.agents.contrats import ContexteDecision, IAgent
from agent_service.app.modele_monde.latent_v1 import encoder_latent, ModeLatent

from runner.app.journal import JournalEpisodes
from world_sim.app.arenes_yaml import charger_arene_v0
from world_sim.app.monde_snake import ConfigMonde, MondeSnake


def _racine_projet() -> Path:
    # services/ui_cli/app/main.py -> parents[3] = racine projet
    return Path(__file__).resolve().parents[3]


def _resoudre_path_arene(racine: Path, arene: str) -> Path:
    s = arene.strip()
    p = Path(s)
    if p.suffix == ".yml" and p.exists():
        return p
    # raccourci: id d'arène
    if not s.endswith(".yml"):
        return racine / "donnees" / "config" / "arenes" / f"{s}.yml"
    return racine / s


def _fabriquer_agent(args: argparse.Namespace) -> IAgent:
    nom = args.agent.strip().lower()
    if nom == "aleatoire":
        return AgentAleatoire(seed=args.seed, epsilon=float(args.epsilon))
    if nom == "curiosite_tabulaire":
        # epsilon = exploration aléatoire (epsilon-greedy)
        from agent_service.app.agents.agent_curiosite_tabulaire import ParametresCuriosite

        params = ParametresCuriosite(
            epsilon=float(args.epsilon),
            w_inconnu=float(args.w_inconnu),
            w_entropie=float(args.w_entropie),
            w_inconfiance=float(args.w_inconfiance),
        )
        return AgentCuriositeTabulaire(seed=args.seed, params=params, mode_latent=args.latent)
    raise SystemExit(f"agent inconnu: {args.agent!r} (attendus: aleatoire, curiosite_tabulaire)")


def _ecrire_metrics(
    fp,
    run_id: str,
    episode_id: int,
    tick: int,
    action: str,
    checksum_avant: int,
    checksum_apres: int,
    agent: IAgent,
) -> None:
    ligne: dict = {
        "ts_ns": time.time_ns(),
        "run_id": run_id,
        "episode_id": episode_id,
        "tick": tick,
        "action": action,
        "checksum_avant": checksum_avant,
        "checksum": checksum_apres,
    }

    # métriques optionnelles si l'agent expose un modèle tabulaire
    modele = getattr(agent, "modele", None)
    if modele is not None and hasattr(modele, "predire"):
        pred = modele.predire(checksum_avant, action)
        ligne.update(
            {
                "cle_connue": bool(pred.support > 0),
                "confiance": float(pred.confiance),
                "entropie": float(pred.entropie),
                "support": int(pred.support),
            }
        )

    fp.write(json.dumps(ligne, ensure_ascii=False) + "\n")


def construire_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ui_cli",
        description="Exécute des épisodes snake en mode headless (batch) et journalise episodes.jsonl.",
    )
    ap.add_argument(
        "--arene",
        type=str,
        default="demo_v0",
        help="Chemin vers une arène .yml, ou id d'arène (ex: demo_v0).",
    )
    ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--max-ticks", type=int, default=2_000)
    ap.add_argument(
        "--agent",
        type=str,
        default="aleatoire",
        help="Agent: aleatoire | curiosite_tabulaire",
    )
    ap.add_argument(
    "--latent",
    type=str,
    default="checksum",
    choices=["checksum", "discret_v1"],
    help="État latent: checksum (cours 1) | discret_v1 (cours 2, plus invariant au bruit).",
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument(
        "--seed-episode",
        action="store_true",
        help="Si activé, dérive la seed par épisode (seed + episode_id).",
    )
    ap.add_argument(
        "--niveau-bruit",
        type=int,
        default=None,
        help="Override du niveau de bruit (sinon valeur par défaut de l'arène).",
    )
    ap.add_argument(
        "--journal",
        type=str,
        default="artefacts/episodes.jsonl",
        help="Chemin de sortie du journal episodes.jsonl.",
    )
    ap.add_argument(
        "--truncate",
        action="store_true",
        help="Si activé, supprime le fichier journal avant exécution (recommandé en batch).",
    )
    ap.add_argument(
        "--metrics",
        type=str,
        default=None,
        help="Optionnel: journal de métriques d'exploration (jsonl).",
    )
    ap.add_argument(
        "--epsilon",
        type=float,
        default=0.05,
        help="Paramètre d'exploration (epsilon-greedy).",
    )
    ap.add_argument("--w-inconnu", type=float, default=10.0)
    ap.add_argument("--w-entropie", type=float, default=1.0)
    ap.add_argument("--w-inconfiance", type=float, default=1.0)
    return ap


def main(argv: list[str] | None = None) -> None:
    args = construire_parser().parse_args(argv)
    racine = _racine_projet()

    path_arene = _resoudre_path_arene(racine, args.arene)
    ar = charger_arene_v0(path_arene)

    # config monde (identique à runner/app/main.py, sauf overrides CLI)
    base_seed = int(args.seed) if args.seed is not None else int(ar.seed)
    niveau_bruit_defaut = int(ar.niveau_bruit_defaut)
    if args.niveau_bruit is not None:
        niveau_bruit_defaut = int(args.niveau_bruit)

    cfg_base = ConfigMonde(
        largeur=ar.largeur,
        hauteur=ar.hauteur,
        seed=base_seed,
        nb_nourriture=ar.nb_nourriture,
        niveau_bruit=niveau_bruit_defaut,
        arene_id=ar.id,
        epsilon_par_pas=ar.epsilon_par_pas,
        bonus_fin=ar.bonus_fin,
        porte_position=ar.porte_position,
        porte_ouverte_initiale=(ar.porte_etat_initial == "ouverte"),
        regle_ouverture_porte=ar.regle_ouverture,
        palette=ar.palette,
    )

    # journalisation canonique (runner/app/journal.py)
    # On pilote le chemin via SNAKE_JOURNAL_PATH pour réutiliser le même composant.
    journal_path = Path(args.journal)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    if args.truncate and journal_path.exists():
        journal_path.unlink()
    os.environ["SNAKE_JOURNAL_PATH"] = str(journal_path)
    journal = JournalEpisodes(racine_projet=racine)

    metrics_fp = None
    if args.metrics:
        metrics_path = Path(args.metrics)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_fp = metrics_path.open("w", encoding="utf-8")

    agent = _fabriquer_agent(args)
    run_id = str(time.time_ns())

    try:
        for episode_id in range(1, int(args.episodes) + 1):
            cfg = cfg_base
            if args.seed_episode:
                cfg = ConfigMonde(**{**cfg_base.__dict__, "seed": base_seed + episode_id})

            monde = MondeSnake(cfg)
            capteurs, _ = monde.observer(niveau_bruit=cfg.niveau_bruit)

            # tick 0 (action=null)
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

            for _ in range(int(args.max_ticks)):
                # décision sur l'état courant (tick t)
                ctx = ContexteDecision(
                    run_id=run_id,
                    episode_id=episode_id,
                    tick=monde.tick,
                    largeur=cfg.largeur,
                    hauteur=cfg.hauteur,
                )
                action = agent.choisir_action(capteurs, ctx)
                z_avant = encoder_latent(capteurs, args.latent)

                # appliquer l'action => tick t+1
                monde.step(direction=action)
                capteurs_apres, _ = monde.observer(niveau_bruit=cfg.niveau_bruit)
                z_apres = encoder_latent(capteurs_apres, args.latent)

                # journaliser tick t+1 avec action appliquée
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

                if metrics_fp is not None:
                    _ecrire_metrics(
                        metrics_fp,
                        run_id=run_id,
                        episode_id=episode_id,
                        tick=monde.tick,
                        action=action,
                        checksum_avant=z_avant,
                        checksum_apres=z_apres,
                        agent=agent,
                    )

                # apprentissage en ligne, si l'agent le supporte
                apprendre_transition = getattr(agent, "apprendre_transition", None)
                if callable(apprendre_transition):
                    apprendre_transition(z_avant, action, z_apres)

                capteurs = capteurs_apres

                if monde.termine:
                    break
    finally:
        journal.fermer()
        if metrics_fp is not None:
            metrics_fp.close()


if __name__ == "__main__":
    main()
