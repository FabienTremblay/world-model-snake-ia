from __future__ import annotations

import argparse
import os
from pathlib import Path

from .pipeline import executer_pipeline_epistemique_v2


def construire_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Épistémique v2 (cours 5) — estrade")
    ap.add_argument("--journal", type=str, default="", help="Chemin vers episodes.jsonl")
    ap.add_argument("--out", type=str, default="", help="Chemin sortie registre_epistemique_v2.json")
    ap.add_argument("--latent", type=str, default="", help="Mode latent: checksum|discret_v1|signaux_percus_hash_v1 (optionnel)")
    return ap


def main() -> None:
    ap = construire_parser()
    args = ap.parse_args()

    path_journal = Path(args.journal) if args.journal else None
    if path_journal is None:
        # même convention que JournalEpisodes
        racine = Path(__file__).resolve().parents[4]
        path_env = os.getenv("SNAKE_JOURNAL_PATH", "").strip()
        if path_env:
            path_journal = Path(path_env)
        else:
            path_journal = racine / "artefacts" / "episodes.jsonl"

    path_out = Path(args.out) if args.out else None
    if path_out is None:
        racine = Path(__file__).resolve().parents[4]
        path_out = racine / "artefacts" / "registre_epistemique_v2.json"

    mode_latent = args.latent.strip() or None

    executer_pipeline_epistemique_v2(
        path_journal=path_journal,
        path_sortie_registre=path_out,
        mode_latent=mode_latent,
    )

    print(f"[epistemique_v2] registre écrit: {path_out}")


if __name__ == "__main__":
    main()
