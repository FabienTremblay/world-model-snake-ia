# services/runner/app/journal.py
from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from commun.contrats import Pixel


def encoder_capteurs_b64(capteurs: List[List[Pixel]]) -> tuple[str, int, int, str]:
    """
    Encodage compact v1:
      - par cellule: uint16 teinte (0..359), uint8 intensite (0..255), uint8 pack (motif<<1 | clignote)
      - ordre: lignes (y), colonnes (x)
    """
    hauteur = len(capteurs)
    largeur = len(capteurs[0]) if hauteur else 0

    buf = bytearray()
    for y in range(hauteur):
        row = capteurs[y]
        for x in range(largeur):
            px = row[x]
            teinte = int(px.teinte) & 0xFFFF
            intensite = int(px.intensite) & 0xFF
            pack = ((int(px.motif) & 0x7) << 1) | (int(px.clignote) & 0x1)
            # little-endian uint16
            buf.append(teinte & 0xFF)
            buf.append((teinte >> 8) & 0xFF)
            buf.append(intensite)
            buf.append(pack & 0xFF)

    b64 = base64.b64encode(bytes(buf)).decode("ascii")
    return b64, largeur, hauteur, "capteurs_b64_v1(u16_teinte,u8_int,u8_pack)"


class JournalEpisodes:
    """
    Journal JSONL append-only.
    Par défaut: artefacts/episodes.jsonl (au root du projet), configurable via SNAKE_JOURNAL_PATH.
    Désactivation via SNAKE_JOURNAL=0.
    """

    def __init__(self, racine_projet: Path) -> None:
        actif = os.getenv("SNAKE_JOURNAL", "1").strip()
        self.actif = actif not in {"0", "false", "False", "non", "NO"}

        path_env = os.getenv("SNAKE_JOURNAL_PATH", "").strip()
        if path_env:
            self.path = Path(path_env)
        else:
            self.path = racine_projet / "artefacts" / "episodes.jsonl"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(self.path, "a", encoding="utf-8") if self.actif else None

    def fermer(self) -> None:
        if self._f:
            self._f.flush()
            self._f.close()
            self._f = None

    def ecrire_tick(
        self,
        *,
        episode_id: int,
        tick: int,
        action_direction: Optional[str],
        niveau_bruit: int,
        score: int,
        longueur: int,
        termine: bool,
        raison_fin: Optional[str],
        capteurs: List[List[Pixel]],
    ) -> None:
        if not self._f:
            return

        capteurs_b64, largeur, hauteur, fmt = encoder_capteurs_b64(capteurs)
        ligne = {
            "ts_ns": time.time_ns(),
            "episode_id": episode_id,
            "tick": tick,
            "action": action_direction,  # "haut|bas|gauche|droite" ou null
            "niveau_bruit": int(niveau_bruit),
            "score": int(score),
            "longueur": int(longueur),
            "termine": bool(termine),
            "raison_fin": raison_fin,
            "largeur": largeur,
            "hauteur": hauteur,
            "format_capteurs": fmt,
            "capteurs_compact": capteurs_b64,
        }
        self._f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        # flush opportuniste à la fin d'épisode
        if termine:
            self._f.flush()
