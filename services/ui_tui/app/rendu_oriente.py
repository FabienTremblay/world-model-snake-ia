# services/ui_tui/app/rendu_oriente.py

from __future__ import annotations

from typing import Any


def rendu_oriente_tete(rendu: list[str], direction: Any) -> list[str]:
    """Substitution visuelle: remplace le premier 'O' par une flèche.

    - Ne modifie pas la production ASCII des capteurs.
    - Remplacement purement visuel côté TUI.
    - Si direction absente/inconnue: conserve 'O'.
    """
    if not rendu:
        return rendu

    d = (str(direction).strip().lower() if direction is not None else "")
    # Tolérance: vocabulaire FR (haut/bas/gauche/droite) + EN/geo (nord/sud/est/ouest).
    fleche = {
        "haut": "↑",
        "nord": "↑",
        "up": "↑",
        "droite": "→",
        "est": "→",
        "right": "→",
        "bas": "↓",
        "sud": "↓",
        "down": "↓",
        "gauche": "←",
        "ouest": "←",
        "left": "←",
    }.get(d)

    if not fleche:
        return rendu

    # Chercher le premier 'O' (ordre lecture: haut->bas, gauche->droite).
    out = list(rendu)
    for i, ln in enumerate(out):
        j = ln.find("O")
        if j >= 0:
            out[i] = ln[:j] + fleche + ln[j + 1 :]
            break
    return out

