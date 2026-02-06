# services/runner/app/replay.py
from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from commun.bus import BusEtatMemoire
from commun.controle import ControleExecution
from commun.contrats import Observation, Pixel
from runner.app.replay_catalogue import CatalogueReplays


def decoder_capteurs_b64(
    b64: str,
    largeur: int,
    hauteur: int,
) -> List[List[Pixel]]:
    """
    Decode capteurs_b64_v1(u16_teinte,u8_int,u8_pack)
      - 4 octets / cellule: teinte(lo,hi), intensite, pack(motif<<1 | clignote)
    """
    raw = base64.b64decode(b64.encode("ascii"))
    attendu = largeur * hauteur * 4
    if len(raw) != attendu:
        raise ValueError(f"Taille capteurs invalide: {len(raw)} != {attendu}")

    capteurs: List[List[Pixel]] = []
    i = 0
    for _y in range(hauteur):
        row: List[Pixel] = []
        for _x in range(largeur):
            teinte = raw[i] | (raw[i + 1] << 8)
            intensite = raw[i + 2]
            pack = raw[i + 3]
            motif = (pack >> 1) & 0x7
            clignote = pack & 0x1
            row.append(Pixel(teinte=int(teinte) % 360, intensite=int(intensite), motif=int(motif), clignote=int(clignote)))
            i += 4
        capteurs.append(row)
    return capteurs


def _rendre_debug_depuis_capteurs(capteurs: List[List[Pixel]]) -> List[str]:
    """
    Rendu debug DEV ONLY pour replay.
    On n'a plus les pixels canoniques, donc on fait un mapping heuristique
    basé sur (motif, clignote, intensite).
    """
    lignes: List[str] = []
    for row in capteurs:
        chars = []
        for px in row:
            # heuristiques v1 compatibles avec notre projection:
            if px.motif == 3 and px.clignote == 0:
                chars.append("#")  # mur
            elif px.motif == 6 and px.clignote == 1:
                chars.append("*")  # nourriture
            elif px.motif == 5:
                chars.append("O")  # tête
            elif px.motif == 2:
                chars.append("o")  # corps
            else:
                chars.append(".")
        lignes.append("".join(chars))
    return lignes


def _lire_jsonl(path: Path) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def _detecter_dernier_run_id(journal_path: Path) -> Optional[str]:
    dernier: Optional[str] = None
    for evt in _lire_jsonl(journal_path):
        rid = evt.get("run_id")
        if rid:
            dernier = str(rid)
    return dernier


def boucle_replay(
    bus: BusEtatMemoire,
    controle: ControleExecution,
    journal_path: Path,
    racine_projet: Path,
    boucle_infinie: bool = True,
) -> None:
    """
    Lit le journal JSONL et republie des Observations.
    - pause/step/vitesse via ControleExecution
    - reset => recommencer au début du fichier
    """
    if not journal_path.exists():
        raise FileNotFoundError(f"Journal introuvable: {journal_path}")

    catalogue = CatalogueReplays(racine_projet)

    while True:
        run_id_force = os.getenv("SNAKE_RUN_ID", "").strip() or None
        run_id_cible = run_id_force or _detecter_dernier_run_id(journal_path)
        idx = 0
        for evt in _lire_jsonl(journal_path):
            # switch de replay demandé ?
            slot = controle.consommer_replay_slot()
            if slot is not None:
                p = catalogue.resoudre(slot)
                if p and p.exists():
                    journal_path = p
                # on casse la boucle courante et on redémarre du début du nouveau fichier
                break

            if controle.consommer_reset():
                break

            # Filtrage par run_id (si disponible)
            if run_id_cible is not None:
                if str(evt.get("run_id", "")) != str(run_id_cible):
                    continue

            # IMPORTANT:
            # on publie la 1re frame immédiatement (même si on démarre en pause),
            # puis on exige une autorisation entre les frames suivantes.
            if idx > 0:
                controle.attendre_autorisation()
                if controle.consommer_reset():
                    break

            largeur = int(evt["largeur"])
            hauteur = int(evt["hauteur"])
            capteurs = decoder_capteurs_b64(
                evt["capteurs_compact"],
                largeur=largeur,
                hauteur=hauteur,
            )
            rendu_debug = _rendre_debug_depuis_capteurs(capteurs)

            run_id = str(evt.get("run_id") or f"replay:{journal_path.name}")
            obs = Observation(
                run_id=str(evt.get("run_id") or (run_id_cible or f"legacy:{journal_path.name}")),
                episode_id=int(evt.get("episode_id", 0)),
                tick=int(evt.get("tick", 0)),
                capteurs=capteurs,
                rendu_debug=rendu_debug,
                mesure_bruit=f"REPLAY run={evt.get('run_id', run_id_cible)} file={journal_path.name} frame={idx} episode={evt.get('episode_id')} action={evt.get('action')}",
                score=int(evt.get("score", 0)),
                longueur=int(evt.get("longueur", 0)),
                termine=bool(evt.get("termine", False)),
                raison_fin=evt.get("raison_fin"),
            )
            bus.publier(obs)

            idx += 1

            # vitesse de lecture (optionnelle) – en pause, attendre_autorisation() gère déjà
            if not controle.est_en_pause():
                time.sleep(controle.delai_s())

        if not boucle_infinie:
            return

        # Fin de fichier: on gèle sur la dernière frame (comme LIVE),
        # et on repart seulement sur reset.
        while True:
            slot = controle.consommer_replay_slot()
            if slot is not None:
                p = CatalogueReplays(racine_projet).resoudre(slot)
                if p and p.exists():
                    journal_path = p
                break
            if controle.consommer_reset():
                break
            time.sleep(0.05)
