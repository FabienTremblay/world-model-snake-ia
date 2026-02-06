from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Iterator

from commun.contrats import Pixel

from .contrats import EvenementTick


def decoder_capteurs_b64_v1(
    capteurs_b64: str,
    largeur: int,
    hauteur: int,
) -> list[list[Pixel]]:
    """Decode `capteurs_b64_v1(u16_teinte,u8_int,u8_pack)` -> grille de Pixel.

    Format par cellule (4 bytes) :
      - uint16 teinte (little-endian)
      - uint8 intensité
      - uint8 pack : (motif<<1 | clignote)
    """
    raw = base64.b64decode(capteurs_b64.encode("ascii"))
    attendu = largeur * hauteur * 4
    if len(raw) != attendu:
        raise ValueError(f"capteurs_compact taille invalide: {len(raw)} != {attendu}")

    capteurs: list[list[Pixel]] = []
    i = 0
    for _y in range(hauteur):
        row: list[Pixel] = []
        for _x in range(largeur):
            teinte = raw[i] | (raw[i + 1] << 8)
            intensite = raw[i + 2]
            pack = raw[i + 3]
            motif = (pack >> 1) & 0x7
            clignote = pack & 0x1
            row.append(Pixel(teinte=int(teinte), intensite=int(intensite), motif=int(motif), clignote=int(clignote)))
            i += 4
        capteurs.append(row)
    return capteurs


def lire_journal_ticks(path_journal: Path) -> Iterator[EvenementTick]:
    """Lit un journal JSONL produit par `JournalEpisodes` et émet des `EvenementTick`."""
    with open(path_journal, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            fmt = d.get("format_capteurs", "")
            if not fmt.startswith("capteurs_b64_v1"):
                raise ValueError(f"format_capteurs non supporté: {fmt!r}")

            largeur = int(d["largeur"])
            hauteur = int(d["hauteur"])
            capteurs = decoder_capteurs_b64_v1(d["capteurs_compact"], largeur, hauteur)

            yield EvenementTick(
                ts_ns=int(d.get("ts_ns", 0)),
                run_id=str(d["run_id"]),
                episode_id=int(d["episode_id"]),
                tick=int(d["tick"]),
                arene_id=d.get("arene_id"),
                seed=d.get("seed"),
                action=d.get("action"),
                niveau_bruit=int(d.get("niveau_bruit", 0)),
                score=int(d.get("score", 0)),
                longueur=int(d.get("longueur", 0)),
                termine=bool(d.get("termine", False)),
                raison_fin=d.get("raison_fin"),
                largeur=largeur,
                hauteur=hauteur,
                capteurs=capteurs,
            )
