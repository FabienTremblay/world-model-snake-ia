"""
Gate de surprise - Classification épistémique connu/inconnu.

Ce module implémente le mécanisme de classification des situations
basé sur la surprise (erreur de prédiction du modèle interne).

Alignement théorique:
- Chapitre 4: Début de la classification de voie Γ
- Chapitre 5: Base pour l'activation de la conscience (voie Attention)

Le gate de surprise est un précurseur du classificateur Γ complet.
Dans JEPA-1, il distingue uniquement connu/inconnu.
Une version future pourrait distinguer Réflexe/Automatisme/Attention.
"""

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import torch
import numpy as np


@dataclass
class StatsSurprise:
    """
    Statistiques descriptives sur les valeurs de surprise.
    
    Ces statistiques permettent de calibrer objectivement le seuil
    de classification connu/inconnu.
    
    Théorie:
        La distribution de la surprise reflète la qualité du modèle
        interne. Elle permet de définir ce qui est "normal" (connu)
        et ce qui est "anormal" (inconnu).
    """
    n: int                          # Nombre d'observations
    mean: float                     # Moyenne
    std: float                      # Écart-type
    min: float                      # Minimum
    max: float                      # Maximum
    quantiles: Dict[str, float]     # Quantiles (p50, p75, p90, p95, p99)
    
    @classmethod
    def depuis_array(cls, surprises: np.ndarray) -> 'StatsSurprise':
        """
        Calculer les statistiques depuis un array NumPy.
        
        Args:
            surprises: Array 1D de valeurs de surprise
        
        Returns:
            StatsSurprise avec toutes les statistiques calculées
        """
        quantiles_vals = [0.50, 0.75, 0.90, 0.95, 0.99]
        quantiles_dict = {
            f"p{int(q*100):02d}": float(np.quantile(surprises, q))
            for q in quantiles_vals
        }
        
        return cls(
            n=int(surprises.size),
            mean=float(surprises.mean()),
            std=float(surprises.std()),
            min=float(surprises.min()),
            max=float(surprises.max()),
            quantiles=quantiles_dict
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export en dictionnaire pour sérialisation."""
        return asdict(self)


@dataclass
class ConfigGate:
    """
    Configuration du gate épistémique.
    
    Modes disponibles:
    - 'quantile': Seuil calibré automatiquement sur un quantile
    - 'seuil': Seuil fixe prédéfini
    
    Théorie:
        Le mode quantile est recommandé car il s'adapte automatiquement
        à la distribution empirique de la surprise.
        
        Exemple: quantile=0.90 signifie que 90% des situations seront
        classées comme connues, et 10% comme inconnues.
    """
    mode: str = "quantile"          # 'quantile' ou 'seuil'
    quantile: float = 0.90          # Utilisé si mode='quantile'
    seuil_connu: float = 0.10       # Utilisé si mode='seuil'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GateSurprise:
    """
    Gate épistémique basé sur la surprise du modèle prédictif.
    
    Rôle:
        Classifier chaque situation en 'connu' (exploiter) ou 'inconnu' (explorer)
        basé sur l'erreur de prédiction du modèle interne.
    
    Théorie (Chapitre 4):
        Ce gate est un précurseur du classificateur de voie Γ complet.
        
        Dans l'architecture finale, Γ devra distinguer:
        - ℛ (Réflexe): Traitement ultra-rapide, sans modèle
        - 𝒰 (Automatisme): Traitement rapide avec modèle comprimé
        - 𝒜 (Attention): Traitement lent, conscient, délibératif
        
        Le GateSurprise actuel distingue uniquement:
        - Connu (exploiter): surprise <= seuil → action rapide
        - Inconnu (explorer): surprise > seuil → exploration attentionnelle
        
        C'est une version binaire simplifiée de Γ.
    
    Usage:
        # Calibration (phase d'apprentissage)
        gate = GateSurprise(ConfigGate(mode='quantile', quantile=0.90))
        gate.calibrer(surprises_entrainement)
        
        # Utilisation (phase d'épreuve)
        if gate.est_connu(surprise):
            action = strategie_exploitation()
        else:
            action = strategie_exploration()
    """
    
    def __init__(self, config: ConfigGate):
        """
        Initialiser le gate.
        
        Args:
            config: Configuration du gate
        """
        self.config = config
        self.seuil_calibre: float = config.seuil_connu
        self.stats: Optional[StatsSurprise] = None
        self.calibre: bool = False
    
    def calibrer(self, surprises: torch.Tensor) -> None:
        """
        Calibrer le seuil à partir d'un ensemble de surprises.
        
        Args:
            surprises: Tensor 1D de valeurs de surprise [N]
        
        Théorie:
            La calibration détermine objectivement le seuil de
            classification connu/inconnu à partir de la distribution
            empirique de la surprise.
            
            Mode quantile (recommandé):
                seuil = quantile(surprises, q)
            
            Mode seuil:
                seuil = config.seuil_connu (fixe)
        """
        surprises_np = surprises.detach().cpu().numpy()
        self.stats = StatsSurprise.depuis_array(surprises_np)
        
        if self.config.mode == "quantile":
            q = np.clip(self.config.quantile, 0.0, 1.0)
            self.seuil_calibre = float(np.quantile(surprises_np, q))
        else:  # mode == "seuil"
            self.seuil_calibre = self.config.seuil_connu
        
        self.calibre = True
    
    def est_connu(self, surprise: float) -> bool:
        """
        Déterminer si une situation est connue.
        
        Args:
            surprise: Valeur de surprise pour une observation
        
        Returns:
            True si surprise <= seuil (situation connue)
            False si surprise > seuil (situation inconnue)
        
        Raises:
            RuntimeError: Si le gate n'a pas été calibré
        """
        if not self.calibre:
            raise RuntimeError(
                "Gate non calibré. Appeler calibrer() avant utilisation."
            )
        return surprise <= self.seuil_calibre
    
    def decider_mode(self, surprise: float) -> Tuple[str, str]:
        """
        Décider le mode de traitement basé sur la surprise.
        
        Args:
            surprise: Valeur de surprise
        
        Returns:
            (mode_descriptif, action_type)
            - mode_descriptif: "connu_exploiter" ou "inconnu_explorer"
            - action_type: "exploiter" ou "explorer"
        
        Théorie:
            Dans l'architecture complète (Chapitre 4), cette fonction
            correspondrait à une version simplifiée de:
                cₜ = Γ(zₜᵖʳⁱᵐⁱᵗⁱᵛᵉ)
            
            La version actuelle retourne une classification binaire.
            Une version future pourrait retourner {ℛ, 𝒰, 𝒜}.
        """
        if self.est_connu(surprise):
            return "connu_exploiter", "exploiter"
        else:
            return "inconnu_explorer", "explorer"
    
    def analyser_batch(self, surprises: torch.Tensor) -> Dict[str, Any]:
        """
        Analyser un batch de surprises.
        
        Args:
            surprises: Tensor 1D de surprises [N]
        
        Returns:
            Dictionnaire avec statistiques de classification:
                - nb_total, nb_connu, nb_inconnu
                - ratio_connu, ratio_inconnu
        
        Utilité:
            Permet de mesurer l'effet du gate et d'ajuster le quantile
            si nécessaire.
        """
        if not self.calibre:
            raise RuntimeError("Gate non calibré.")
        
        surprises_np = surprises.detach().cpu().numpy()
        nb_total = surprises_np.size
        nb_connu = int((surprises_np <= self.seuil_calibre).sum())
        nb_inconnu = nb_total - nb_connu
        
        return {
            'nb_total': nb_total,
            'nb_connu': nb_connu,
            'nb_inconnu': nb_inconnu,
            'ratio_connu': nb_connu / max(nb_total, 1),
            'ratio_inconnu': nb_inconnu / max(nb_total, 1),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export pour registre épistémique.
        
        Returns:
            Dictionnaire complet de l'état du gate
        """
        result = {
            'config': self.config.to_dict(),
            'seuil_calibre': self.seuil_calibre,
            'calibre': self.calibre,
        }
        if self.stats:
            result['stats_surprise'] = self.stats.to_dict()
        return result
    
    @classmethod
    def depuis_dict(cls, data: Dict[str, Any]) -> 'GateSurprise':
        """
        Créer un gate depuis un dictionnaire (pour charger registre).
        
        Args:
            data: Dictionnaire exporté par to_dict()
        
        Returns:
            Instance de GateSurprise avec état restauré
        """
        config = ConfigGate(
            mode=data['config']['mode'],
            quantile=data['config']['quantile'],
            seuil_connu=data['config']['seuil_connu']
        )
        gate = cls(config)
        gate.seuil_calibre = data['seuil_calibre']
        gate.calibre = data['calibre']
        
        # Restaurer stats si présentes
        if 'stats_surprise' in data:
            stats_dict = data['stats_surprise']
            gate.stats = StatsSurprise(**stats_dict)
        
        return gate
    
    def __repr__(self) -> str:
        status = "calibré" if self.calibre else "non calibré"
        return (
            f"GateSurprise(mode={self.config.mode}, "
            f"seuil={self.seuil_calibre:.6f}, {status})"
        )
