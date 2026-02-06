from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Temperament:
    """Paramètres d'arbitrage (cours 5).

    Ces paramètres n'affectent pas le *point de vue* : ils modulent l'arbitrage
    prudence/curiosité/risque à l'intérieur d'un même agent en arène.
    """

    prudence: float = 0.5          # 0 = téméraire, 1 = très prudent
    curiosite: float = 0.5         # 0 = conservateur, 1 = très curieux
    aversion_risque: float = 0.5   # 0 = accepte le risque, 1 = évite fortement le risque
