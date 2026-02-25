"""
Modèle prédictif de base pour l'architecture cognitive.

Ce module définit l'interface abstraite pour tous les modèles prédictifs
utilisés dans le système. Un modèle prédictif est une composante du tronc
qui permet d'anticiper les observations futures.

Alignement théorique:
- Chapitre 4: Composante du tronc pour la simulation interne
- Chapitre 5: Base pour les têtes de simulation et planification
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch
import torch.nn as nn


class ModelePredicifBase(ABC, nn.Module):
    """
    Classe abstraite pour tous les modèles prédictifs.
    
    Un modèle prédictif doit pouvoir:
    1. Prédire une observation future à partir d'une observation courante
    2. Calculer une mesure de surprise (erreur de prédiction)
    3. Être sauvegardé et rechargé
    
    Théorie (Chapitre 4):
    Ces modèles sont des composantes du tronc permettant la simulation
    interne et l'anticipation.
    """
    
    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Prédire l'observation suivante.
        
        Args:
            x: Observation encodée au temps t [batch, dim]
        
        Returns:
            Prédiction de l'observation au temps t+1 [batch, dim]
        
        Théorie:
            Correspond à la simulation interne f̂(zₜ) → ẑₜ₊₁
        """
        pass
    
    @abstractmethod
    def calculer_surprise(
        self, 
        prediction: torch.Tensor, 
        observation: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculer la surprise (erreur de prédiction).
        
        Args:
            prediction: Prédiction du modèle [batch, dim]
            observation: Observation réelle [batch, dim]
        
        Returns:
            Surprise pour chaque exemple [batch]
        
        Théorie:
            La surprise mesure l'écart entre le modèle interne
            et la réalité observée. C'est un signal épistémique
            crucial pour le gate de classification (Γ).
        """
        pass
    
    @abstractmethod
    def sauvegarder(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Sauvegarder le modèle et ses métadonnées.
        
        Args:
            path: Chemin du fichier de sauvegarde
            metadata: Métadonnées additionnelles (config, historique, etc.)
        """
        pass
    
    @abstractmethod
    def charger(self, path: str) -> Dict[str, Any]:
        """
        Charger le modèle depuis un fichier.
        
        Args:
            path: Chemin du fichier
        
        Returns:
            Métadonnées associées au modèle
        """
        pass
    
    def valider_dimensions(self, x: torch.Tensor, expected_dim: int) -> None:
        """
        Valider que les dimensions d'entrée sont correctes.
        
        Args:
            x: Tensor à valider
            expected_dim: Dimension attendue
        
        Raises:
            ValueError: Si les dimensions ne correspondent pas
        """
        if x.dim() != 2:
            raise ValueError(f"Expected 2D tensor, got {x.dim()}D")
        if x.shape[1] != expected_dim:
            raise ValueError(
                f"Expected dimension {expected_dim}, got {x.shape[1]}"
            )
