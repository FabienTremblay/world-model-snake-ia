# services/runner/app/replay.py
from __future__ import annotations

import base64
from dataclasses import dataclass
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

def detecter_dernier_run_id(journal_path: Path) -> Optional[str]:
    dernier: Optional[str] = None
    for evt in _lire_jsonl(journal_path):
        rid = evt.get("run_id")
        if rid:
            dernier = str(rid)
    return dernier


@dataclass(frozen=True)
class EpisodeInfo:
    episode_id: int
    nb_frames: int
    tick_min: int
    tick_max: int
    score_final: int
    score_max: int
    longueur_finale: int
    longueur_max: int
    termine: bool
    raison_fin: Optional[str]

def resoudre_run_id_cible(journal_path: Path) -> Optional[str]:
    """Détermine le run_id à rejouer: env SNAKE_RUN_ID ou dernier run_id du fichier."""
    run_id_force = os.getenv("SNAKE_RUN_ID", "").strip() or None
    if run_id_force:
        return run_id_force
    return detecter_dernier_run_id(journal_path)

def indexer_episodes(journal_path: Path, run_id_cible: Optional[str]) -> list[EpisodeInfo]:
    """Scanne le JSONL et retourne les EpisodeInfo pour un run_id (ou tous si None)."""
    stats: dict[int, dict] = {}
    for evt in _lire_jsonl(journal_path):
        if run_id_cible is not None and str(evt.get("run_id", "")) != str(run_id_cible):
            continue
        eid = int(evt.get("episode_id", 0))
        tick = int(evt.get("tick", 0))
        score = int(evt.get("score", 0))
        longueur = int(evt.get("longueur", 0))
        termine = bool(evt.get("termine", False))
        raison_fin = evt.get("raison_fin")
        s = stats.get(eid)
        if s is None:
            s = {
                "nb": 0,
                "tick_min": tick,
                "tick_max": tick,
                "score_max": score,
                "score_final": score,
                "longueur_max": longueur,
                "longueur_finale": longueur,
                "termine": termine,
                "raison_fin": raison_fin,
            }
            stats[eid] = s
        s["nb"] += 1
        s["tick_min"] = min(s["tick_min"], tick)
        s["tick_max"] = max(s["tick_max"], tick)
        s["score_max"] = max(s["score_max"], score)
        s["score_final"] = score
        s["longueur_max"] = max(s["longueur_max"], longueur)
        s["longueur_finale"] = longueur
        # On retient la dernière raison_fin non vide si termine
        if termine:
            s["termine"] = True
            if raison_fin is not None:
                s["raison_fin"] = raison_fin
    infos: list[EpisodeInfo] = []
    for eid in sorted(stats.keys()):
        s = stats[eid]
        infos.append(EpisodeInfo(
            episode_id=eid,
            nb_frames=int(s["nb"]),
            tick_min=int(s["tick_min"]),
            tick_max=int(s["tick_max"]),
            score_final=int(s["score_final"]),
            score_max=int(s["score_max"]),
            longueur_finale=int(s["longueur_finale"]),
            longueur_max=int(s["longueur_max"]),
            termine=bool(s["termine"]),
            raison_fin=s.get("raison_fin"),
        ))
    return infos


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
            # run_id + index (1 scan) pour navigation et stats
            run_id_cible = resoudre_run_id_cible(journal_path)
            episodes = indexer_episodes(journal_path, run_id_cible)

            # 🔒 Sécurité : si aucun épisode ne correspond au run_id,
            # on désactive le filtrage run_id pour éviter un replay vide.
            if run_id_cible is not None and not episodes:
                print(
                    f"REPLAY: aucun épisode pour run_id={run_id_cible}, "
                    "désactivation du filtre run_id",
                    flush=True,
                )
                run_id_cible = None
                episodes = indexer_episodes(journal_path, None)
            # épisode courant: demande UI, env SNAKE_EPISODE, sinon 1er épisode présent, sinon 0
            demande = controle.consommer_episode()
            if demande is not None:
                episode_courant = int(demande)
            else:
                env_ep = os.getenv("SNAKE_EPISODE", "").strip()
                episode_courant = int(env_ep) if env_ep.isdigit() else (episodes[0].episode_id if episodes else 0)

            idx_frame = 0
            for evt in _lire_jsonl(journal_path):
                # switch de replay demandé ?
                slot = controle.consommer_replay_slot()
                if slot is not None:
                    p = catalogue.resoudre(slot)
                    if p and p.exists():
                        journal_path = p
                    # on casse la boucle courante et on redémarre du début du nouveau fichier
                    break

                # bascule d'épisode demandée ?
                eid_demande = controle.consommer_episode()
                if eid_demande is not None:
                    episode_courant = int(eid_demande)
                    break

                if controle.consommer_reset():
                    break

                # Filtrage par run_id (si disponible)
                if run_id_cible is not None:
                    if str(evt.get("run_id", "")) != str(run_id_cible):
                        continue

                # Filtrage par épisode
                if int(evt.get("episode_id", 0)) != int(episode_courant):
                    continue

                # IMPORTANT:
                # on publie la 1re frame immédiatement (même si on démarre en pause),
                # puis on exige une autorisation entre les frames suivantes.
                if idx_frame > 0:
                    controle.attendre_autorisation()
                    if controle.consommer_reset():
                        break
                    # re-check épisode demandé pendant pause
                    eid_demande = controle.consommer_episode()
                    if eid_demande is not None:
                        episode_courant = int(eid_demande)
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
                    mesure_bruit=f"REPLAY run={evt.get('run_id', run_id_cible)} file={journal_path.name} frame={idx_frame} episode={episode_courant} action={evt.get('action')}",
                    score=int(evt.get("score", 0)),
                    longueur=int(evt.get("longueur", 0)),
                    termine=bool(evt.get("termine", False)),
                    raison_fin=evt.get("raison_fin"),
                )
                bus.publier(obs)

                idx_frame += 1

                # vitesse de lecture (optionnelle) – en pause, attendre_autorisation() gère déjà
                if not controle.est_en_pause():
                    time.sleep(controle.delai_s())

            if not boucle_infinie:
                return

            # Fin de fichier: on gèle sur la dernière frame,
            # et on repart seulement sur reset / changement d'épisode / changement de slot.
            while True:
                slot = controle.consommer_replay_slot()
                if slot is not None:
                    p = CatalogueReplays(racine_projet).resoudre(slot)
                    if p and p.exists():
                        journal_path = p
                    break
                eid_demande = controle.consommer_episode()
                if eid_demande is not None:
                    # redémarrer au début du fichier sur un autre épisode
                    break
                if controle.consommer_reset():
                    break
                time.sleep(0.05)

