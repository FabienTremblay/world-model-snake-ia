# services/runner/app/main.py
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import yaml

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Observation

from world_sim.app.monde_snake import ConfigMonde, MondeSnake
from world_sim.app.arenes_yaml import charger_arene_v0
from runner.app.journal_v2 import JournalV2Writer

from agent_service.app.catalogue_agents import creer_agent
from agent_service.app.contrats_agents import ContexteDecision, ContextePerception, IAgentArene

from instrument.app.contrats import EtatMondeCanonique, ObservationInstrument
from instrument.app.instruments import CameraEgocentreeV1, InstrumentGPSV1


def _charger_yaml(path: Path) -> dict:
    """Charge un YAML en dict (ou {} si absent/invalide)."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _horodatage_compact() -> str:
    t = time.localtime()
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}_{t.tm_hour:02d}h{t.tm_min:02d}"


def _preparer_run_dir(exp_dir: Path, cfg_exp: dict) -> Path:
    """Prépare le répertoire de run selon `experience.yml`.

    Objectif: journal v2 strictement aligné sur les paramètres du bac-à-sable.
    - base = sorties.run_dir (relatif à exp_dir) ou `artefacts/runs`
    - nom = horodatage + _tag optionnel (SNAKE_RUN_TAG)
    - la convention est : <experience_dir>/<base>/<nom_run>/
    """
    sorties = cfg_exp.get("sorties") if isinstance(cfg_exp, dict) else None
    if not isinstance(sorties, dict):
        sorties = {}

    run_dir_rel = sorties.get("run_dir")
    if not isinstance(run_dir_rel, str) or not run_dir_rel.strip():
        run_dir_rel = "artefacts/runs"

    base_runs = (exp_dir / run_dir_rel).resolve()
    base_runs.mkdir(parents=True, exist_ok=True)

    tag = os.getenv("SNAKE_RUN_TAG", "").strip()
    nom = _horodatage_compact()
    nom_run = f"{nom}_{tag}" if tag else nom

    run_dir = base_runs / nom_run
    # Évite collision rare si relancé dans la même minute
    if run_dir.exists():
        run_dir = base_runs / f"{nom_run}_{time.time_ns() % 1_000_000:06d}"

    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


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


def _fabriquer_agent_depuis_env() -> IAgentArene | None:
    """Option TUI : si SNAKE_AGENT est défini, on joue en mode auto."""
    nom = os.getenv("SNAKE_AGENT", "").strip().lower()
    if not nom:
        return None

    seed = os.getenv("SNAKE_AGENT_SEED")
    epsilon = os.getenv("SNAKE_AGENT_EPSILON", "0.0")
    mode_latent = os.getenv("SNAKE_AGENT_LATENT", "checksum")

    seed_int = int(seed) if seed not in (None, "") else None

    if nom == "aleatoire":
        return creer_agent(nom, seed=seed_int, epsilon=float(epsilon))

    if nom == "curiosite_tabulaire":
        from agent_service.app.agents.agent_curiosite_tabulaire import ParametresCuriosite

        params = ParametresCuriosite(
            epsilon=float(epsilon),
            w_inconnu=float(os.getenv("SNAKE_W_INCONNU", "1.0")),
            w_entropie=float(os.getenv("SNAKE_W_ENTROPIE", "1.0")),
            w_inconfiance=float(os.getenv("SNAKE_W_INCONFIANCE", "1.0")),
        )
        return creer_agent(nom, seed=seed_int, params=params, mode_latent=mode_latent)

    if nom == "planif_mpc_tabulaire":
        return creer_agent(nom, seed=seed_int, mode_latent=mode_latent)

    if nom == "planif_mpc_observateur_tabulaire":
        return creer_agent(nom, seed=seed_int, mode_latent=mode_latent)

    if nom == "planif_1pas_temperament":
        return creer_agent(nom, seed=seed_int, mode_latent=mode_latent)

    raise SystemExit(f"SNAKE_AGENT inconnu: {nom!r}")


def _etat_canonique_depuis_monde(monde: MondeSnake, cfg: ConfigMonde) -> EtatMondeCanonique:
    """Construit l'état canonique pour alimenter des instruments.

    - monde.serpent: liste (x,y) corps...tête (tête = dernier)
    - monde.direction: direction absolue courante
    """
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


def _instruments_depuis_agent(agent: IAgentArene | None):
    """Retourne la liste des instruments 'portés' par l'agent.

    Convention:
      - si l'agent expose une méthode `instruments()` => on l'utilise.
      - sinon, fallback minimal (utile en mode manuel ou agents legacy).
    """
    if agent is not None:
        fn = getattr(agent, "instruments", None)
        if callable(fn):
            insts = fn()
            if insts is not None:
                return list(insts)

    # fallback minimal : caméra égocentrée + gps (données)
    return [
        CameraEgocentreeV1(rayon=2, niveau_bruit=0, seed_bruit=1),
        InstrumentGPSV1(),
    ]


def _observer_instruments(insts, etat: EtatMondeCanonique) -> dict[str, ObservationInstrument]:
    sorties: dict[str, ObservationInstrument] = {}
    for inst in insts:
        obs = inst.observer(etat)
        sorties[getattr(inst, "instrument_id", inst.__class__.__name__)] = obs
    return sorties


def boucle_episodes(
    bus: BusEtatMemoire,
    controle: ControleExecution,
    ticks_max: int = 10_000,
) -> None:
    racine_projet = Path(__file__).resolve().parents[3]

    # --- bac-à-sable (expérience) -------------------------------------------------
    experience_id = (os.getenv("SNAKE_EXPERIENCE") or os.getenv("SNAKE_EXPERIENCE_ID") or "").strip()
    exp_dir: Path | None = None
    cfg_exp: dict = {}
    if experience_id:
        exp_dir = (racine_projet / "donnees" / "config" / "experiences" / experience_id).resolve()
        cfg_exp = _charger_yaml(exp_dir / "experience.yml")

        # Si l'expérience déclare un journal_basename, on impose journal.jsonl (v2).
        sorties = cfg_exp.get("sorties")
        if isinstance(sorties, dict):
            jb = sorties.get("journal_basename") or sorties.get("journal")
            if isinstance(jb, str) and jb.strip() and jb.strip() != "journal.jsonl":
                raise SystemExit(
                    f"experience.yml ({experience_id}) doit déclarer sorties.journal_basename=journal.jsonl (v2). "
                    f"Valeur actuelle: {jb!r}"
                )

        # Aligne le max_ticks avec l'expérience si fourni.
        gen = cfg_exp.get("generation")
        if isinstance(gen, dict):
            mt = gen.get("max_ticks")
            if isinstance(mt, int) and mt > 0:
                ticks_max = mt

    # arène : priorité experience.yml -> env -> défaut
    arene_id = "demo_v0"
    ar = None
    arene_cfg = cfg_exp.get("arene") if isinstance(cfg_exp, dict) else None
    if isinstance(arene_cfg, dict) and isinstance(arene_cfg.get("id"), str) and arene_cfg.get("id").strip():
        arene_id = arene_cfg["id"].strip()
    else:
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

    # Journal v2 (sans compat v1) : 1 répertoire par run, meta.json + journal.jsonl.
    # run_id: stable, rejouable, peut être fourni par le bac-à-sable.
    run_id = (os.getenv("SNAKE_RUN_ID") or str(time.time_ns())).strip()
    if not run_id:
        run_id = str(time.time_ns())

    # Répertoire de run : priorité env -> bac-à-sable -> fallback projet
    run_dir_env = (os.getenv("SNAKE_RUN_DIR") or "").strip()
    if run_dir_env:
        run_dir = Path(run_dir_env).expanduser().resolve()
    elif exp_dir is not None:
        run_dir = _preparer_run_dir(exp_dir, cfg_exp)
    else:
        run_dir = (racine_projet / "artefacts" / "runs" / run_id).resolve()

    meta = {
        "run": {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "ticks_max": ticks_max,
        },
        "bac_a_sable": {
            "experience": {
                "id": experience_id or None,
                "dir": str(exp_dir) if exp_dir is not None else None,
                "source_yml": (
                    (exp_dir / "experience.yml").read_text(encoding="utf-8")
                    if exp_dir is not None and (exp_dir / "experience.yml").exists()
                    else None
                ),
                "config_resolue": cfg_exp,
            },
            "sorties": {
                "journal_basename": "journal.jsonl",
                "meta_filename": "meta.json",
                "obs_dirname": "obs",
            },
            "arene": {
                "id": ar.id,
                "source_yml": (path_arene.read_text(encoding="utf-8") if path_arene.exists() else None),
                "config_resolue": ar.__dict__,
            },
            "cfg_monde": cfg.__dict__,
        },
        "env": {
            "SNAKE_EXPERIENCE": os.getenv("SNAKE_EXPERIENCE"),
            "SNAKE_EXPERIENCE_ID": os.getenv("SNAKE_EXPERIENCE_ID"),
            "SNAKE_RUN_ID": os.getenv("SNAKE_RUN_ID"),
            "SNAKE_RUN_DIR": os.getenv("SNAKE_RUN_DIR"),
            "SNAKE_RUN_TAG": os.getenv("SNAKE_RUN_TAG"),
            "SNAKE_ARENE": os.getenv("SNAKE_ARENE"),
            "SNAKE_AGENT": os.getenv("SNAKE_AGENT"),
            "SNAKE_AGENT_SEED": os.getenv("SNAKE_AGENT_SEED"),
            "SNAKE_AGENT_EPSILON": os.getenv("SNAKE_AGENT_EPSILON"),
            "SNAKE_AGENT_LATENT": os.getenv("SNAKE_AGENT_LATENT"),
        },
    }
    journal = JournalV2Writer(run_dir=run_dir, run_id=run_id, meta=meta)

    agent = _fabriquer_agent_depuis_env()
    perception = ContextePerception(champ_vision_deg=180)

    insts = _instruments_depuis_agent(agent)

    # Identité logique de l'agent (utile aux analyses).
    agent_id = os.getenv("SNAKE_AGENT", "manuel").strip() or "manuel"
    incarnation_id = None
    episode_id = 0

    while True:
        monde = MondeSnake(cfg)
        monde.reset()
        niveau_bruit = controle.niveau_bruit()
        capteurs, rendu_debug = monde.observer(niveau_bruit=niveau_bruit)

        etat = _etat_canonique_depuis_monde(monde, cfg)
        observations = _observer_instruments(insts, etat)

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
            episode_id=episode_id,
            tick=monde.tick,
            arene_id=cfg.arene_id,
            seed=cfg.seed,
            agent_id=agent_id,
            incarnation_id=incarnation_id,
            action=None,
            niveau_bruit=niveau_bruit,
            etat=etat,
            score=monde.score,
            longueur=len(monde.serpent),
            termine=monde.termine,
            raison_fin=monde.raison_fin,
            observations=observations,
        )

        for _ in range(ticks_max):
            if controle.consommer_reset():
                break

            controle.attendre_autorisation()

            if controle.consommer_reset():
                break

            if agent is None:
                direction = controle.consommer_direction()
                monde.step(direction=direction)
            else:
                contexte = ContexteDecision(
                    run_id=run_id,
                    episode_id=episode_id,
                    tick=monde.tick,
                    largeur=cfg.largeur,
                    hauteur=cfg.hauteur,
                    perception=perception,
                    direction=getattr(monde, "direction", None),
                    observations=observations,
                )
                direction = agent.choisir_action(capteurs=capteurs, contexte=contexte)
                monde.step(direction=direction)

            niveau_bruit = controle.niveau_bruit()
            capteurs, rendu_debug = monde.observer(niveau_bruit=niveau_bruit)
            capteurs_canon, _ = monde.observer(niveau_bruit=0)
            mesure_bruit = _mesurer_bruit(capteurs_canon, capteurs)

            etat = _etat_canonique_depuis_monde(monde, cfg)
            observations = _observer_instruments(insts, etat)

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
                episode_id=episode_id,
                tick=monde.tick,
                arene_id=cfg.arene_id,
                seed=cfg.seed,
                agent_id=agent_id,
                incarnation_id=incarnation_id,
                action=direction,
                niveau_bruit=niveau_bruit,
                etat=etat,
                score=monde.score,
                longueur=len(monde.serpent),
                termine=monde.termine,
                raison_fin=monde.raison_fin,
                observations=observations,
            )

            if monde.termine:
                while True:
                    if controle.consommer_reset():
                        break
                    time.sleep(0.05)
                break

            time.sleep(controle.delai_s())

        episode_id += 1


def main() -> None:
    bus = BusEtatMemoire()
    controle = ControleExecution(delai_s=0.05)
    boucle_episodes(bus, controle)


if __name__ == "__main__":
    main()
