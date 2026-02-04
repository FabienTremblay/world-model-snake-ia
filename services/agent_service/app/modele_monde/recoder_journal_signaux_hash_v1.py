# services/agent_service/app/modele_monde/recoder_journal_signaux_hash_v1.py
"""CLI - recoder_journal_signaux_hash_v1

But:
- lire un journal episodes.jsonl
- décoder les capteurs
- calculer un latent *exploitable* basé sur les signaux perçus (voisinage tête)
- écrire un nouveau jsonl où chaque événement reçoit: `signaux_hash`

Pourquoi:
- `checksum` est (trop) injectif => états rares => p_fin ~ 0, support0_ratio élevé
- `signaux_hash` regroupe par configuration locale pertinente (mur/corps/nourriture)
  autour de la tête => généralisation ("mur devant" => danger)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from runner.app.replay import decoder_capteurs_b64

from agent_service.app.modele_monde.latent_v1 import encoder_latent, extraire_signaux_percus_voisinage_v1


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True, help="Path vers episodes.jsonl")
    p.add_argument("--out", required=True, help="Sortie episodes_signaux_hash.jsonl")
    p.add_argument(
        "--champ",
        default="signaux_hash",
        help="Nom du champ latent écrit dans le jsonl (défaut: signaux_hash)",
    )
    p.add_argument(
        "--mode",
        default="signaux_percus_hash_v1",
        choices=["signaux_percus_hash_v1", "discret_v1", "checksum"],
        help="Mode latent (défaut: signaux_percus_hash_v1)",
    )
    p.add_argument("--ecrire-signaux-tuple", action="store_true", help="Écrire aussi signaux_tuple (lisible) + motifs_* (défaut: non)")
    p.add_argument("--limite", type=int, default=None, help="Limiter le nombre d'événements")
    return p


def main() -> int:
    args = _parser().parse_args()
    journal_path = Path(args.journal)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    nb_in = 0
    nb_out = 0
    nb_skip = 0

    with open(journal_path, "r", encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            nb_in += 1
            try:
                evt = json.loads(line)
                w = int(evt["largeur"])
                h = int(evt["hauteur"])
                capteurs = decoder_capteurs_b64(evt["capteurs_compact"], largeur=w, hauteur=h)
                z = int(encoder_latent(capteurs, mode=args.mode))
                extras = extraire_signaux_percus_voisinage_v1(capteurs)
            except Exception:
                nb_skip += 1
                continue

            evt2 = dict(evt)
            # latent exploitable (ex: signaux_hash) requis par iterer_transitions(..., champ_latent=...)
            evt2[args.champ] = z

            if args.ecrire_signaux_tuple and extras:
                signaux_tuple = extras.get("signaux_tuple")
                if signaux_tuple is not None:
                    evt2["signaux_tuple"] = signaux_tuple

                for k in ("motif_tete","motif_haut","motif_bas","motif_gauche","motif_droite"):
                    if k in extras:
                        evt2[k] = extras[k]

            out.write(json.dumps(evt2, ensure_ascii=False) + "\n")
            nb_out += 1

            if args.limite is not None and nb_out >= int(args.limite):
                break

    print(f"[ok] lu: {nb_in} ; écrit: {nb_out} ; ignorés: {nb_skip}")
    print(f"[ok] sortie: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
