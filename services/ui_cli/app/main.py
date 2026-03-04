# services/ui_cli/app/main.py
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import yaml
from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

from agent_service.app.catalogue_agents import creer_agent

from agent_service.app.contrats_agents import ContexteDecision, ContextePerception, IAgentArene
from agent_service.app.modele_monde.latent_v1 import encoder_latent, ModeLatent

from runner.app.journal import JournalEpisodes
from runner.app.noyau import ParametresExecution, executer_episodes_headless
from world_sim.app.arenes_yaml import charger_arene_v0
from world_sim.app.monde_snake import ConfigMonde, MondeSnake


def _horodatage_compact() -> str:
    """Horodatage lisible pour nommer un répertoire d'exécution."""
    # ex: 2026-02-02_14h31
    t = time.localtime()
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}_{t.tm_hour:02d}h{t.tm_min:02d}"


def _chemin_experience(racine: Path, experience_id: str) -> Path:
    return racine / "donnees" / "config" / "experiences" / experience_id


def _assurer_bac_a_sable(exp_dir: Path) -> dict:
    """Crée la structure minimale d'un bac à sable si absente.

    Retourne un petit rapport (dict) pour stdout.
    """
    cree = []
    if not exp_dir.exists():
        exp_dir.mkdir(parents=True, exist_ok=True)
        cree.append(str(exp_dir))

    # sous-répertoires canonique
    artefacts = exp_dir / "artefacts"
    for p in [
        artefacts,
        artefacts / "runs",
        artefacts / "datasets",
        artefacts / "diagnostics",
        artefacts / "registres",
        artefacts / "notes",
    ]:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            cree.append(str(p))

    exp_yml = exp_dir / "experience.yml"
    if not exp_yml.exists():
        exp_yml.write_text(
            """# donnees/config/experiences/<id>/experience.yml
# Bac à sable d'expérience (SAI).

id: CHANGER_MOI
description: ""

arene:
  # id d'arène (raccourci) ou chemin .yml
  id: demo_v0

agent:
  id: aleatoire

latent: checksum

modele_monde:
  journal: artefacts/datasets/train.jsonl
  champ_latent: signaux_hash

generation:
  episodes: 100
  max_ticks: 2000
  seed: 123
  niveau_bruit: null

sorties:
  run_dir: artefacts/runs
  journal: journal_episodes.jsonl
  capture_stdout: false

notes:
  - "Ce fichier est un gabarit minimal."
""",
            encoding="utf-8",
        )
        cree.append(str(exp_yml))

    exp_readme = exp_dir / "README.md"
    if not exp_readme.exists():
        exp_readme.write_text(
            """# bac à sable — expérience

Ce répertoire est créé automatiquement par `ui_cli` lorsqu'une nouvelle expérience est détectée.

- `experience.yml` : paramètres et conventions du bac à sable
- `artefacts/` : sorties produites par les exécutions
  - `runs/` : exécutions horodatées (journaux + stdout éventuel)
  - `datasets/` : journaux stabilisés (train/eval/mix)
  - `diagnostics/` : sorties sauvegardées des diagnostics (optionnel)
  - `registres/` : registres épistémiques (APK)
  - `notes/` : observations humaines

Tu peux remplacer ce README par celui du template si tu veux une description complète.
""",
            encoding="utf-8",
        )
        cree.append(str(exp_readme))

    return {
        "experience_dir": str(exp_dir),
        "creations": cree,
    }


def _charger_experience_yml(exp_dir: Path) -> dict:
    """Charge experience.yml si présent, sinon retourne dict vide."""
    fp = exp_dir / "experience.yml"
    if not fp.exists():
        return {}
    data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _resoudre_modele_monde_depuis_experience(exp_dir: Path, experience_id: str) -> None:
    """Résout et exporte les variables d'environnement liées au modèle monde.

    - SNAKE_MODELE_JOURNAL : chemin absolu vers le journal d'entraînement
    - SNAKE_CHAMP_LATENT   : nom du champ latent à lire dans le journal

    Si la section `modele_monde` n'est pas présente, ne fait rien.
    """
    cfg = _charger_experience_yml(exp_dir)
    mm = cfg.get("modele_monde") if isinstance(cfg, dict) else None
    if not isinstance(mm, dict):
        return

    journal_rel = mm.get("journal")
    champ_latent = mm.get("champ_latent")

    if isinstance(journal_rel, str) and journal_rel.strip():
        journal_path = (exp_dir / journal_rel).resolve()
        os.environ["SNAKE_MODELE_JOURNAL"] = str(journal_path)
    else:
        journal_path = None

    if isinstance(champ_latent, str) and champ_latent.strip():
        os.environ["SNAKE_CHAMP_LATENT"] = champ_latent.strip()

    # trace stdout (utile pour tes schémas)
    payload = {
        "event": "modele_monde_resolu",
        "experience": experience_id,
        "SNAKE_MODELE_JOURNAL": os.environ.get("SNAKE_MODELE_JOURNAL"),
        "SNAKE_CHAMP_LATENT": os.environ.get("SNAKE_CHAMP_LATENT"),
        "source": str((exp_dir / "experience.yml").resolve()),
    }
    print(json.dumps(payload, ensure_ascii=False))

    # validation minimale (échec explicite et tôt)
    if journal_path is not None and not journal_path.exists():
        raise FileNotFoundError(
            "Journal du modèle monde introuvable: "
            f"{journal_path} (déclaré dans experience.yml → modele_monde.journal)"
        )


def _resoudre_sorties_experience(
    racine: Path,
    experience_id: str,
    run_tag: str | None,
    run_id: str,
) -> tuple[Path, Path, Path, Path, Path]:
    """Retourne (exp_dir, run_dir, journal_path, stdout_path, meta_path)."""
    exp_dir = _chemin_experience(racine, experience_id)
    rapport = _assurer_bac_a_sable(exp_dir)
    if rapport.get("creations"):
        print(
            json.dumps(
                {
                    "event": "bac_a_sable_cree",
                    "experience": experience_id,
                    "experience_dir": rapport["experience_dir"],
                    "creations": rapport["creations"],
                },
                ensure_ascii=False,
            )
        )
    else:
        print(
            json.dumps(
                {
                    "event": "bac_a_sable_detecte",
                    "experience": experience_id,
                    "experience_dir": str(exp_dir),
                },
                ensure_ascii=False,
            )
        )

    base_runs = exp_dir / "artefacts" / "runs"
    base_runs.mkdir(parents=True, exist_ok=True)
    suffix = _horodatage_compact()
    tag = (run_tag.strip() if run_tag else "").strip()
    nom_run = f"{suffix}_{tag}" if tag else suffix
    run_dir = base_runs / nom_run
    # éviter collision rare si relancé dans la même minute
    if run_dir.exists():
        run_dir = base_runs / f"{nom_run}_{run_id[-6:]}"
    run_dir.mkdir(parents=True, exist_ok=True)

    journal_path = run_dir / "journal_episodes.jsonl"
    stdout_path = run_dir / "stdout.log"
    meta_path = run_dir / "meta.json"
    return exp_dir, run_dir, journal_path, stdout_path, meta_path


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            s.write(data)

    def flush(self):
        for s in self._streams:
            s.flush()


@contextmanager
def _capture_stdout_stderr(fp: Path):
    """Duplique stdout/stderr vers un fichier, sans masquer la console."""
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open("w", encoding="utf-8") as f:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = _Tee(old_out, f)
        sys.stderr = _Tee(old_err, f)
        try:
            yield
        finally:
            sys.stdout = old_out
            sys.stderr = old_err


@contextmanager
def _nullcontext():
    """Fallback de context manager (équivalent de contextlib.nullcontext)."""
    yield



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

def _resoudre_path_utilisateur(racine_projet: Path, exp_dir: Path | None, run_dir: Path | None, chemin: str) -> Path:
    # règle: si chemin absolu, on le garde; sinon on l'ancre sur exp_dir si disponible, sinon sur run_dir, sinon sur racine_projet
    s = (chemin or '').strip()
    p = Path(s)
    if not s:
        raise ValueError('chemin vide')
    if p.is_absolute():
        return p
    if exp_dir is not None:
        return (exp_dir / p).resolve()
    if run_dir is not None:
        return (run_dir / p).resolve()
    return (racine_projet / p).resolve()



def _fabriquer_agent(args: argparse.Namespace) -> IAgentArene:
    """Sélection canonique: toute instanciation passe par le catalogue.

    Exception: la résolution de `agent_personne_path` reste côté UI car elle dépend du bac-à-sable.
    """
    nom = args.agent.strip().lower()

    params: dict = {}

    # paramètres communs
    if getattr(args, "seed", None) is not None:
        params["seed"] = args.seed
    if getattr(args, "latent", None):
        params["mode_latent"] = str(args.latent)

    if nom == "agent_personne":
        agent_personne_path = None
        if getattr(args, "agent_personne_path", None):
            agent_personne_path = str(args.agent_personne_path)
        elif getattr(args, "agent_personne_id", None):
            # si on a --experience (obligatoire), on résout sous artefacts/agent_personne/<id>/agent_personne.json
            racine = _racine_projet()
            exp_dir = _chemin_experience(racine, str(args.experience))
            agent_personne_path = str(
                (
                    exp_dir
                    / "artefacts"
                    / "agent_personne"
                    / str(args.agent_personne_id)
                    / "agent_personne.json"
                ).resolve()
            )

        if not agent_personne_path:
            raise SystemExit(
                "agent_personne: fournir --agent-personne-path, ou bien --agent-personne-id (avec --experience)"
            )

        params["agent_personne_path"] = agent_personne_path
        return creer_agent(nom, params=params)

    if nom == "aleatoire":
        params["epsilon"] = float(args.epsilon)
        return creer_agent(nom, params=params)

    if nom == "curiosite_tabulaire":
        params.update(
            {
                "epsilon": float(args.epsilon),
                "w_inconnu": float(args.w_inconnu),
                "w_entropie": float(args.w_entropie),
                "w_inconfiance": float(args.w_inconfiance),
            }
        )
        return creer_agent(nom, params=params)

    if nom in (
        "planif_mpc_tabulaire",
        "planif_mpc_observateur_tabulaire",
        "planif_1pas_temperament",
    ):
        return creer_agent(nom, params=params)

    # Fallback canon (agents plug-ins v1) :
    # Si l'id n'est pas dans la liste d'agents explicitement gérés par l'UI,
    # on délègue au catalogue (qui validera l'existence et donnera une erreur claire sinon).
    return creer_agent(nom, params=params)

def _ecrire_metrics(
    fp,
    run_id: str,
    episode_id: int,
    tick: int,
    action: str,
    checksum_avant: int,
    checksum_apres: int,
    agent: IAgentArene,
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


    # sorties de têtes (A108) si l'agent expose un accès journalisable
    get_sorties_tetes = getattr(agent, 'get_sorties_tetes', None)
    if callable(get_sorties_tetes):
        try:
            ligne['sorties_tetes'] = get_sorties_tetes()
        except Exception as e:
            ligne['sorties_tetes'] = {'erreur': str(e)}

    fp.write(json.dumps(ligne, ensure_ascii=False) + "\n")




def _hook_apres_action_pour_cli(metrics_fp, agent, mode_latent: str):
    """Fabrique un hook post-action pour le CLI.

    - écrit les métriques si demandé
    - déclenche l'apprentissage en ligne si l'agent le supporte
    """

    def _hook(run_id, episode_id, monde, action, z_avant, z_apres, capteurs_avant, capteurs_apres):
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

        apprendre_transition = getattr(agent, "apprendre_transition", None)
        if callable(apprendre_transition) and z_avant and z_apres:
            apprendre_transition(z_avant, action, z_apres)

    return _hook


def construire_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ui_cli",
        description="Exécute des épisodes snake en mode headless (batch) et journalise episodes.jsonl.",
        epilog=(
            "Sous-commandes disponibles (voir l'aide dédiée):\n"
            "  ui_cli pipeline --help\n  ui_cli evenements --help\n"
            "  ui_cli preparer-agent --help\n"
            "\n"
            "Note: si tu exécutes `ui_cli --help`, tu es dans le mode legacy (exécution d'épisodes)."
        ),
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
        help="Agent: aleatoire | curiosite_tabulaire | planif_mpc_tabulaire | planif_mpc_observateur_tabulaire | planif_1pas_temperament | agent_personne",
    )
    ap.add_argument(
        '--agent-personne-id',
        dest='agent_personne_id',
        type=str,
        default=None,
        help=(
            "Id d'agent-personne (A107) sous artefacts/agent_personne/<id>/agent_personne.json. "
            "Requiert --experience."
        ),
    )
    ap.add_argument(
        '--agent-personne-path',
        dest='agent_personne_path',
        type=str,
        default=None,
        help="Chemin explicite vers un agent_personne.json (override de --agent-personne-id).",
    )
    ap.add_argument(
        "--latent",
        type=str,
        default="checksum",
        # IMPORTANT: ne pas figer `choices`.
        # Les modes évoluent (ex: signaux_percus_hash_v1 au cours 4) et on veut
        # que `ui_cli` demeure forward-compatible.
        help=(
            "État latent (exemples): checksum (cours 1) | discret_v1 (cours 2) | "
            "signaux_percus_hash_v1 (cours 4)."
        ),
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
        default="journal_episodes.jsonl",
        help="Chemin de sortie du journal episodes.jsonl (chemin relatif ancré sur l'expérience).",
    )
    ap.add_argument(
        "--truncate",
        action="store_true",
        help="Si activé, supprime le fichier journal avant exécution (recommandé en batch).",
    )
    ap.add_argument(
        "--experience",
        type=str,
        default=None,
        help=(
            "Id d'expérience (bac à sable) sous donnees/config/experiences/<id>. "
            "Si fourni, `ui_cli` crée automatiquement la structure et écrit le journal "
            "dans artefacts/runs/<horodatage>/journal_episodes.jsonl."
        ),
    )
    ap.add_argument(
        "--run-tag",
        type=str,
        default=None,
        help="Tag optionnel pour nommer le répertoire d'exécution (ex: mpc_obs_v2).",
    )
    ap.add_argument(
        "--capture-stdout",
        action="store_true",
        help="Si activé, duplique stdout/stderr vers artefacts/runs/.../stdout.log (requiert --experience).",
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


def _appliquer_defaults_experience(args: argparse.Namespace, cfg: dict) -> None:
    """Si l'utilisateur n'a pas surchargé un paramètre CLI, utiliser experience.yml."""
    if not isinstance(cfg, dict):
        return

    arene = cfg.get("arene")
    if isinstance(arene, dict):
        ar_id = arene.get("id")
        if isinstance(ar_id, str) and ar_id.strip():
            if args.arene == "demo_v0":
                args.arene = ar_id.strip()

    agent = cfg.get("agent")
    if isinstance(agent, dict):
        ag_id = agent.get("id")
        if isinstance(ag_id, str) and ag_id.strip():
            if args.agent == "aleatoire":
                args.agent = ag_id.strip()

    latent = cfg.get("latent")
    if isinstance(latent, str) and latent.strip():
        if args.latent == "checksum":
            args.latent = latent.strip()

    gen = cfg.get("generation")
    if isinstance(gen, dict):
        if args.episodes == 100 and gen.get("episodes") is not None:
            try:
                args.episodes = int(gen["episodes"])
            except Exception:
                pass
        if args.max_ticks == 2000 and gen.get("max_ticks") is not None:
            try:
                args.max_ticks = int(gen["max_ticks"])
            except Exception:
                pass
        if args.seed is None and gen.get("seed") is not None:
            try:
                args.seed = int(gen["seed"])
            except Exception:
                pass
        if args.niveau_bruit is None and gen.get("niveau_bruit") is not None:
            # null => None ; sinon int
            try:
                if gen["niveau_bruit"] is None:
                    args.niveau_bruit = None
                else:
                    args.niveau_bruit = int(gen["niveau_bruit"])
            except Exception:
                pass


def main(argv: list[str] | None = None) -> None:
    # ------------------------------------------------------------
    # ROUTAGE SOUS-COMMANDES (ex: sai-a107 / preparer-agent)
    # Doit être AVANT le parsing principal pour ne rien casser.
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) >= 1 and argv[0] == "preparer-agent":
        from ui_cli.app.preparation_agent.cli_preparer_agent import main_preparer_agent

        # délègue au sous-cli, sans interférer avec le reste
        main_preparer_agent(argv[1:])
        return

    if len(argv) >= 1 and argv[0] == "pipeline":
        from ui_cli.app.pipeline.cli_pipeline import main_pipeline

        main_pipeline(argv[1:])
        return

    if len(argv) >= 1 and argv[0] == "evenements":
        from ui_cli.app.evenements.cli_evenements import main_evenements

        main_evenements(argv[1:])
        return

        # ------------------------------------------------------------

        args = construire_parser().parse_args(argv)
        racine = _racine_projet()

        # Identifiant d'exécution (partagé partout)
        run_id = str(time.time_ns())

        # Discipline: exiger un bac à sable d'expérience (pas d'écriture dans ./artefacts)
        if not args.experience:
            raise SystemExit("ui_cli: --experience est requis (le répertoire ./artefacts n'est plus utilisé).")

        # Si on lance via un bac à sable (expérience), on résout un répertoire de run dédié.
        exp_dir: Path | None = None
        run_dir: Path | None = None
        stdout_path: Path | None = None
        meta_path: Path | None = None
        if True:

            bac = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
            rapport = bac.assurer_structure()
            if rapport.get("creations"):
                print(
                    json.dumps(
                        {
                            "event": "bac_a_sable_cree",
                            "experience": str(args.experience),
                            "experience_dir": rapport["experience_dir"],
                            "creations": rapport["creations"],
                        },
                        ensure_ascii=False,
                    )
                )
            else:
                print(
                    json.dumps(
                        {
                            "event": "bac_a_sable_detecte",
                            "experience": str(args.experience),
                            "experience_dir": str(bac.experience_dir),
                        },
                        ensure_ascii=False,
                    )
                )

            # defaults CLI depuis experience.yml (si l'utilisateur n'a pas surchargé)
            _appliquer_defaults_experience(args=args, cfg=bac.cfg)

            exp_dir = bac.experience_dir
            run_dir, journal_path, stdout_path, meta_path = bac.preparer_run(
                run_tag=str(args.run_tag) if args.run_tag else None,
                run_id=run_id,
            )
            args.journal = str(journal_path)

            if args.metrics is None:
                args.metrics = str(run_dir / "metrics.jsonl")


            # agent-personne-path : si relatif, l'ancrer aussi sur l'expérience/run (évite ./)
            if getattr(args, "agent_personne_path", None):
                args.agent_personne_path = str(
                    _resoudre_path_utilisateur(
                        racine_projet=racine,
                        exp_dir=bac.experience_dir,
                        run_dir=run_dir,
                        chemin=str(args.agent_personne_path),
                    )
                )

            # env modèle monde
            payload_mm = bac.appliquer_env_modele_monde()
            print(json.dumps(payload_mm, ensure_ascii=False))

        path_arene = _resoudre_path_arene(racine, args.arene)
        ar = charger_arene_v0(path_arene)
        os.environ["SNAKE_ARENE_PATH"] = str(path_arene)

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

        # ------------------------------------------------------------
        # Journalisation canonique (runner/app/journal.py)
        # On pilote le chemin via SNAKE_JOURNAL_PATH pour réutiliser le même composant.
        journal_path = Path(args.journal)
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        if args.truncate and journal_path.exists():
            journal_path.unlink()
        os.environ["SNAKE_JOURNAL_PATH"] = str(journal_path)

        # Si capture stdout/stderr demandée, activer un tee vers stdout.log (seulement avec --experience).
        capture_effectif = bool(args.capture_stdout)
        if args.experience and exp_dir is not None:
            # si experience.yml demande la capture, on l'applique par défaut
            bac2 = BacASableV1.charger_depuis_id(racine_projet=racine, experience_id=str(args.experience))
            capture_effectif = capture_effectif or bac2.capture_stdout_defaut()

        if capture_effectif and stdout_path is not None:
            sys.stdout.write(f"[ui_cli] capture stdout/stderr -> {stdout_path}\n")
        capture_ctx = (
            _capture_stdout_stderr(stdout_path) if (capture_effectif and stdout_path is not None) else _nullcontext()
        )

        # meta.json pour rendre le run reproductible / traçable
        if meta_path is not None:
            meta = {
                "run_id": run_id,
                "experience": args.experience,
                "run_tag": args.run_tag,
                "arene": args.arene,
                "arene_path": str(path_arene),
                "agent": args.agent,
                "latent": args.latent,
                "episodes": int(args.episodes),
                "max_ticks": int(args.max_ticks),
                "seed": args.seed,
                "seed_episode": bool(args.seed_episode),
                "niveau_bruit": args.niveau_bruit,
                "journal": str(journal_path),
                "metrics": args.metrics,
            }
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Exécution (journal + monde) sous capture éventuelle.
        with capture_ctx:
            journal = JournalEpisodes(racine_projet=racine)
            metrics_fp = None
            try:
                if args.metrics:
                    metrics_path = Path(args.metrics)
                    metrics_path.parent.mkdir(parents=True, exist_ok=True)
                    metrics_fp = metrics_path.open("w", encoding="utf-8")

                agent = _fabriquer_agent(args)
                print({"event":"agent_instancie","type":type(agent).__name__,"module":type(agent).__module__}, flush=True)

                # exécution (noyau runner commun — cours 5)
                params_exec = ParametresExecution(
                    episodes=int(args.episodes),
                    max_ticks=int(args.max_ticks),
                    seed_episode=bool(args.seed_episode),
                )

                hook_apres_action = _hook_apres_action_pour_cli(metrics_fp, agent, mode_latent=str(args.latent))

                executer_episodes_headless(
                    run_id=run_id,
                    cfg_base=cfg_base,
                    agent=agent,
                    journal=journal,
                    params=params_exec,
                    perception=None,
                    encoder_latent=encoder_latent,
                    mode_latent=str(args.latent),
                    hook_apres_action=hook_apres_action,
                )


            finally:
                journal.fermer()
                if metrics_fp is not None:
                    metrics_fp.close()


if __name__ == "__main__":
    main()

