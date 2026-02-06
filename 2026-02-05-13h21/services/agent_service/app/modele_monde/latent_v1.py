from __future__ import annotations

"""Encodage d'état latent (v1).

Objectif:
- fournir une représentation d'état (z) utilisée par les world models tabulaires
- permettre de comparer (cours 1) un latent très discriminant (checksum) vs
  (cours 2) un latent plus invariant au bruit (discret_v1)

Note:
- le latent discret_v1 n'est pas "intelligent": il compresse grossièrement les capteurs.
- il est volontairement robuste à de petites variations (teinte / intensité) via binning.

API:
- encoder_latent(capteurs, mode) -> int
  mode: "checksum" | "discret_v1" | "signaux_percus_hash_v1"
"""

from collections import Counter
from typing import Literal

from commun.contrats import Pixel

from agent_service.app.spectateur import _checksum_rapide


ModeLatent = Literal["checksum", "discret_v1", "signaux_percus_hash_v1"]


def _classe_pixel_discret_v1(px: Pixel) -> int:
    # teinte 0..359 -> 6 bins de 60 degrés (robuste au bruit de quelques degrés)
    teinte_bin = int(px.teinte) // 60
    if teinte_bin < 0:
        teinte_bin = 0
    elif teinte_bin > 5:
        teinte_bin = 5

    # intensité 0..255 -> 4 bins de 64 (robuste au bruit)
    intens_bin = int(px.intensite) // 64
    if intens_bin < 0:
        intens_bin = 0
    elif intens_bin > 3:
        intens_bin = 3

    motif = int(px.motif) & 0x7  # 0..7
    return teinte_bin * (4 * 8) + intens_bin * 8 + motif  # 0..191


def _latent_discret_v1(capteurs: list[list[Pixel]], grilles: int = 4) -> int:
    """Latent discret v1: pooling spatial grossier + binning.

    - découpe l'image en grilles x grilles régions
    - pour chaque région: classe dominante (mode) des pixels (teinte_bin, intens_bin, motif)
    - combine les classes régionales dans un hash 64-bit stable
    """
    h = len(capteurs)
    w = len(capteurs[0]) if h else 0
    if h == 0 or w == 0:
        return 0

    # découpe en régions
    step_y = max(1, h // grilles)
    step_x = max(1, w // grilles)

    valeurs: list[int] = []
    for gy in range(grilles):
        y0 = gy * step_y
        y1 = h if gy == grilles - 1 else min(h, (gy + 1) * step_y)
        for gx in range(grilles):
            x0 = gx * step_x
            x1 = w if gx == grilles - 1 else min(w, (gx + 1) * step_x)

            cnt: Counter[int] = Counter()
            for y in range(y0, y1):
                row = capteurs[y]
                for x in range(x0, x1):
                    cnt[_classe_pixel_discret_v1(row[x])] += 1

            if cnt:
                valeurs.append(cnt.most_common(1)[0][0])
            else:
                valeurs.append(0)

    # hash FNV-1a 64-bit
    fnv_offset = 1469598103934665603
    fnv_prime = 1099511628211
    acc = fnv_offset
    for v in valeurs:
        acc ^= int(v) & 0xFF
        acc = (acc * fnv_prime) & 0xFFFFFFFFFFFFFFFF
        acc ^= (int(v) >> 8) & 0xFF
        acc = (acc * fnv_prime) & 0xFFFFFFFFFFFFFFFF

    return int(acc)


def _trouver_tete(capteurs: list[list[Pixel]]) -> tuple[int, int] | None:
    """Retourne (x,y) de la tête si détectée (motif==5), sinon None."""
    for y, row in enumerate(capteurs):
        for x, px in enumerate(row):
            if int(px.motif) == 5:
                return x, y
    return None


def _motif_cellule(capteurs: list[list[Pixel]], x: int, y: int) -> int:
    h = len(capteurs)
    w = len(capteurs[0]) if h else 0
    if x < 0 or y < 0 or y >= h or x >= w:
        # hors-grille = "mur" conceptuel (utile pour généraliser au bord)
        return 3
    return int(capteurs[y][x].motif) & 0x7




def extraire_signaux_percus_voisinage_v1(capteurs: list[list[Pixel]]) -> dict | None:
    pos = _trouver_tete(capteurs)
    if pos is None:
        return None
    x, y = pos
    motif_tete = _motif_cellule(capteurs, x, y)
    motif_haut = _motif_cellule(capteurs, x, y - 1)
    motif_bas = _motif_cellule(capteurs, x, y + 1)
    motif_gauche = _motif_cellule(capteurs, x - 1, y)
    motif_droite = _motif_cellule(capteurs, x + 1, y)

    signaux_tuple = f"{motif_tete},{motif_haut},{motif_bas},{motif_gauche},{motif_droite}"

    return {
        "x": x,
        "y": y,
        "signaux_tuple": signaux_tuple,
        "motif_tete": motif_tete,
        "motif_haut": motif_haut,
        "motif_bas": motif_bas,
        "motif_gauche": motif_gauche,
        "motif_droite": motif_droite,
    }
def _latent_signaux_percus_hash_v1(capteurs: list[list[Pixel]]) -> int:
    """Latent *exploitable* (v1): voisinage local autour de la tête.

    Idée:
      - au lieu d'encoder toute la grille (checksum), on encode seulement ce qui
        guide une décision immédiate : ce qu'il y a autour de la tête.

    Représentation:
      - motifs dans les 4 cases adjacentes (haut, bas, gauche, droite)
      - motif de la case tête (devrait être 5)
      - longueur (binning grossier) pour éviter de distinguer chaque taille

    Remarques:
      - on conserve *tous* les motifs (mur/corps/tête/nourriture/...) afin de
        laisser le WM apprendre seul la sémantique.
      - si la tête n'est pas détectée, on retombe sur une signature minimale.
    """

    pos = _trouver_tete(capteurs)
    if pos is None:
        # cas pathologique: pas de tête => latent très grossier
        return 0

    x, y = pos
    motifs = (
        _motif_cellule(capteurs, x, y),
        _motif_cellule(capteurs, x, y - 1),
        _motif_cellule(capteurs, x, y + 1),
        _motif_cellule(capteurs, x - 1, y),
        _motif_cellule(capteurs, x + 1, y),
    )

    # hash FNV-1a 64-bit (stable, cheap)
    fnv_offset = 1469598103934665603
    fnv_prime = 1099511628211
    acc = fnv_offset
    for m in motifs:
        acc ^= int(m) & 0xFF
        acc = (acc * fnv_prime) & 0xFFFFFFFFFFFFFFFF

    return int(acc)


def encoder_latent(capteurs: list[list[Pixel]], mode: ModeLatent = "checksum") -> int:
    if mode == "checksum":
        return int(_checksum_rapide(capteurs))
    if mode == "discret_v1":
        return _latent_discret_v1(capteurs)
    if mode == "signaux_percus_hash_v1":
        return _latent_signaux_percus_hash_v1(capteurs)
    raise ValueError(f"mode latent inconnu: {mode!r}")
