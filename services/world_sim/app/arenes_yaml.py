# services/world_sim/app/arenes_yaml.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from commun.contrats import Pixel


@dataclass(frozen=True)
class PalettePixels:
    sol: Pixel
    mur: Pixel
    serpent_corps: Pixel
    serpent_tete: Pixel
    nourriture: Pixel
    porte_fermee: Pixel
    porte_ouverte: Pixel


@dataclass(frozen=True)
class ReglePorteV0:
    longueur_min: int = 0
    score_min: int = 0
    tick_min: int = 0


@dataclass(frozen=True)
class ArenaV0:
    id: str
    largeur: int
    hauteur: int
    seed: int
    nb_nourriture: int
    porte_position: Optional[Tuple[int, int]]
    porte_etat_initial: str  # "fermee" | "ouverte"
    regle_ouverture: ReglePorteV0
    epsilon_par_pas: float
    bonus_fin: float
    niveau_bruit_defaut: int
    palette: PalettePixels


PALETTE_DEFAUT = PalettePixels(
    sol=Pixel(teinte=200, intensite=40, motif=0, clignote=0),
    mur=Pixel(teinte=210, intensite=120, motif=3, clignote=0),
    serpent_corps=Pixel(teinte=120, intensite=160, motif=2, clignote=0),
    serpent_tete=Pixel(teinte=120, intensite=230, motif=5, clignote=0),
    nourriture=Pixel(teinte=30, intensite=220, motif=6, clignote=1),
    porte_fermee=Pixel(teinte=300, intensite=180, motif=1, clignote=0),
    porte_ouverte=Pixel(teinte=300, intensite=240, motif=1, clignote=1),
)


def _px(d: Dict[str, Any]) -> Pixel:
    return Pixel(
        teinte=int(d["teinte"]),
        intensite=int(d["intensite"]),
        motif=int(d["motif"]),
        clignote=int(d["clignote"]),
    )


def charger_arene_v0(path: Path) -> ArenaV0:
    """Charge une arène YAML v0 depuis disque (donnée pure)."""
    obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("version") != "snake_arene_v0":
        raise ValueError("arene: version non supportée (attendu snake_arene_v0)")

    grille = obj.get("grille") or {}
    rep = obj.get("reproductibilite") or {}
    objets = obj.get("objets") or {}
    palette = (objets.get("palette") or {})
    instances = (objets.get("instances") or {})

    inst_n = instances.get("nourriture") or {}
    inst_p = instances.get("porte") or {}

    porte_pos = None
    pos = inst_p.get("position")
    if isinstance(pos, dict):
        porte_pos = (int(pos["x"]), int(pos["y"]))

    porte_etat_initial = str(inst_p.get("etat_initial", "fermee"))

    porte_fin = obj.get("porte_fin") or {}
    ouverture = porte_fin.get("ouverture") or {}
    regle = ReglePorteV0(
        longueur_min=int(ouverture.get("longueur_min", 0)),
        score_min=int(ouverture.get("score_min", 0)),
        tick_min=int(ouverture.get("tick_min", 0)),
    )

    recomp = obj.get("recompenses") or {}
    capteurs = obj.get("capteurs") or {}
    bruit = (capteurs.get("bruit") or {})

    pal = PalettePixels(
        sol=_px(palette.get("sol", {"teinte": 200, "intensite": 40, "motif": 0, "clignote": 0})),
        mur=_px(palette.get("mur", {"teinte": 210, "intensite": 120, "motif": 3, "clignote": 0})),
        serpent_corps=_px(palette.get("serpent_corps", {"teinte": 120, "intensite": 160, "motif": 2, "clignote": 0})),
        serpent_tete=_px(palette.get("serpent_tete", {"teinte": 120, "intensite": 230, "motif": 5, "clignote": 0})),
        nourriture=_px(palette.get("nourriture", {"teinte": 30, "intensite": 220, "motif": 6, "clignote": 1})),
        porte_fermee=_px(palette.get("porte_fermee", {"teinte": 300, "intensite": 180, "motif": 1, "clignote": 0})),
        porte_ouverte=_px(palette.get("porte_ouverte", {"teinte": 300, "intensite": 240, "motif": 1, "clignote": 1})),
    )

    return ArenaV0(
        id=str(obj["id"]),
        largeur=int(grille["largeur"]),
        hauteur=int(grille["hauteur"]),
        seed=int(rep.get("seed", 0)),
        nb_nourriture=int(inst_n.get("nb", 1)),
        porte_position=porte_pos,
        porte_etat_initial=porte_etat_initial,
        regle_ouverture=regle,
        epsilon_par_pas=float(recomp.get("epsilon_par_pas", 0.0)),
        bonus_fin=float(recomp.get("bonus_fin", 0.0)),
        niveau_bruit_defaut=int(bruit.get("niveau_defaut", 0)),
        palette=pal,
    )

