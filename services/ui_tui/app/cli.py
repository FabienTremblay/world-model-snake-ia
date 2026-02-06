from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Literal

ModeTui = Literal["menu", "manual", "replay"]

def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ui_tui")
    ap.add_argument("--mode", choices=["menu", "manual", "replay"], default="menu")
    ap.add_argument("--arene", type=str, default=None, help="ex: cours4_tiny_planification")
    ap.add_argument("--agent", type=str, default=None, help="ex: aleatoire, planif_mpc_observateur_tabulaire")
    ap.add_argument("--latent", type=str, default=None, help="ex: checksum, signaux_percus_hash_v1")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--epsilon", type=float, default=None)
    ap.add_argument("--journal", type=str, default=None, help="chemin replay (jsonl)")
    return ap

def appliquer_env(args: argparse.Namespace) -> None:
    # Permet de lancer via CLI sans exporter les variables à la main.
    if args.arene:
        os.environ["SNAKE_ARENE"] = args.arene
    if args.agent:
        os.environ["SNAKE_AGENT"] = args.agent
    if args.latent:
        os.environ["SNAKE_AGENT_LATENT"] = args.latent
    if args.seed is not None:
        os.environ["SNAKE_AGENT_SEED"] = str(args.seed)
    if args.epsilon is not None:
        os.environ["SNAKE_AGENT_EPSILON"] = str(args.epsilon)
    if args.journal:
        os.environ["SNAKE_JOURNAL_PATH"] = str(Path(args.journal))
