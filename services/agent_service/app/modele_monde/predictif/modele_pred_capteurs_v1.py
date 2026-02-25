"""
Modèle prédictif des capteurs projetés - Version 1.

Implémentation d'un réseau neuronal simple pour prédire les observations
au temps t+1 à partir des observations au temps t.

Origine: JEPA-1 (expérimentation prototype)
Architecture: Linear -> ReLU -> Linear

Alignement théorique:
- Chapitre 3: Encodage des observations instrumentales
- Chapitre 4: Composante du tronc pour simulation interne
"""

from typing import Dict, Any, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from .modele_predictif_base import ModelePredicifBase


class ModelePredCapteursV1(ModelePredicifBase):
    """
    Modèle prédictif simple pour les capteurs projetés.
    
    Architecture:
        - Couche linéaire: dim_in -> hidden
        - Activation: ReLU
        - Couche linéaire: hidden -> dim_in
    
    Théorie:
        Ce modèle implémente une simulation interne minimale.
        Il apprend f̂: zₜ → ẑₜ₊₁ où z est l'espace latent des capteurs.
        
        La surprise (MSE) produite par ce modèle sera utilisée
        par le gate épistémique pour classifier les situations
        en connues (exploiter) ou inconnues (explorer).
    
    Origine:
        Extrait et refactorisé depuis JEPA-1/outils/entrainer_hypothese_pred_capteurs_v1.py
    """
    
    def __init__(self, dim_in: int = 560, hidden: int = 64):
        """
        Initialiser le modèle.
        
        Args:
            dim_in: Dimension de l'espace d'observations encodées
            hidden: Dimension de la couche cachée
        
        Defaults:
            dim_in=560: Taille du vecteur capteurs_compact base64 (JEPA-1)
            hidden=64: Capacité suffisante pour Snake simple
        """
        super().__init__()
        self.dim_in = dim_in
        self.hidden = hidden
        
        self.net = nn.Sequential(
            nn.Linear(dim_in, hidden),
            nn.ReLU(),
            nn.Linear(hidden, dim_in),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Prédire l'observation suivante.
        
        Args:
            x: Observations au temps t [batch, dim_in]
        
        Returns:
            Prédictions au temps t+1 [batch, dim_in]
        """
        self.valider_dimensions(x, self.dim_in)
        return self.net(x)
    
    def calculer_surprise(
        self, 
        prediction: torch.Tensor, 
        observation: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculer la MSE par exemple (surprise).
        
        Args:
            prediction: Prédiction du modèle [batch, dim_in]
            observation: Observation réelle [batch, dim_in]
        
        Returns:
            MSE pour chaque exemple [batch]
        
        Théorie:
            La surprise est l'erreur quadratique moyenne entre
            la prédiction et l'observation réelle.
            
            surprise = MSE(ẑₜ₊₁, zₜ₊₁)
            
            Une surprise faible indique une situation connue.
            Une surprise élevée indique une situation nouvelle.
        """
        self.valider_dimensions(prediction, self.dim_in)
        self.valider_dimensions(observation, self.dim_in)
        
        # MSE par exemple (moyenne sur la dimension des features)
        return F.mse_loss(prediction, observation, reduction='none').mean(dim=1)
    
    def sauvegarder(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Sauvegarder le modèle avec métadonnées.
        
        Args:
            path: Chemin de sauvegarde (.pt)
            metadata: Métadonnées additionnelles
        
        Format du fichier:
            {
                'state_dict': poids du réseau,
                'dim_in': dimension d'entrée,
                'hidden': dimension cachée,
                'model_type': 'ModelePredCapteursV1',
                'metadata': métadonnées optionnelles
            }
        """
        save_dict = {
            'state_dict': self.state_dict(),
            'dim_in': self.dim_in,
            'hidden': self.hidden,
            'model_type': 'ModelePredCapteursV1',
        }
        if metadata:
            save_dict['metadata'] = metadata
        
        torch.save(save_dict, path)
    
    def charger(self, path: str) -> Dict[str, Any]:
        """
        Charger les poids depuis un fichier.
        
        Args:
            path: Chemin du fichier
        
        Returns:
            Métadonnées associées
        
        Raises:
            ValueError: Si les dimensions ne correspondent pas
        """
        checkpoint = torch.load(path, map_location='cpu')
        
        # Vérifier compatibilité
        if checkpoint['dim_in'] != self.dim_in:
            raise ValueError(
                f"Dimension mismatch: checkpoint has dim_in={checkpoint['dim_in']}, "
                f"but model has dim_in={self.dim_in}"
            )
        if checkpoint['hidden'] != self.hidden:
            raise ValueError(
                f"Hidden dimension mismatch: checkpoint has hidden={checkpoint['hidden']}, "
                f"but model has hidden={self.hidden}"
            )
        
        self.load_state_dict(checkpoint['state_dict'])
        return checkpoint.get('metadata', {})
    
    @classmethod
    def depuis_checkpoint(cls, path: str, device: str = 'cpu') -> 'ModelePredCapteursV1':
        """
        Créer une instance du modèle depuis un checkpoint.
        
        Args:
            path: Chemin du checkpoint
            device: Device PyTorch ('cpu' ou 'cuda')
        
        Returns:
            Instance du modèle avec poids chargés
        
        Usage:
            model = ModelePredCapteursV1.depuis_checkpoint('agent.poids.pt')
        """
        checkpoint = torch.load(path, map_location=device)
        
        model = cls(
            dim_in=checkpoint['dim_in'],
            hidden=checkpoint['hidden']
        ).to(device)
        
        model.load_state_dict(checkpoint['state_dict'])
        return model
    
    def __repr__(self) -> str:
        return (
            f"ModelePredCapteursV1(dim_in={self.dim_in}, hidden={self.hidden}, "
            f"params={sum(p.numel() for p in self.parameters())})"
        )
