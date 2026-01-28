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
  mode: "checksum" | "discret_v1"
"""

from collections import Counter
from typing import Literal

from commun.contrats import Pixel

from agent_service.app.spectateur import _checksum_rapide


ModeLatent = Literal["checksum", "discret_v1"]


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


def encoder_latent(capteurs: list[list[Pixel]], mode: ModeLatent = "checksum") -> int:
    if mode == "checksum":
        return int(_checksum_rapide(capteurs))
    if mode == "discret_v1":
        return _latent_discret_v1(capteurs)
    raise ValueError(f"mode latent inconnu: {mode!r}")
