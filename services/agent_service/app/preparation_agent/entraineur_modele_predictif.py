"""
Entraîneur pour modèles prédictifs.

Module générique pour entraîner des modèles prédictifs sur des paires
de transitions observées.

Alignement théorique:
- Chapitre 4: Apprentissage du modèle interne du tronc
- Chapitre 5: Amélioration progressive des capacités prédictives
"""

import time
import random
from typing import Dict, Any, List, Optional
import torch
import torch.nn.functional as F


class EntraineurModelePredicdictif:
    """
    Entraîneur générique pour modèles prédictifs.
    
    Rôle:
        Entraîner un modèle f̂: zₜ → ẑₜ₊₁ à partir de paires
        de transitions observées.
    
    Théorie (Chapitre 4):
        L'entraînement construit le modèle interne du tronc.
        Ce modèle permet:
        - La simulation interne (prédiction)
        - Le calcul de surprise (classification)
        - La planification (via les têtes)
    
    Architecture:
        - Optimisation: Adam
        - Loss: MSE (Mean Squared Error)
        - Mini-batches avec permutation aléatoire
    
    Origine:
        Refactorisé depuis JEPA-1/outils/entrainer_hypothese_pred_capteurs_v1.py
    """
    
    def __init__(
        self,
        model: torch.nn.Module,
        device: str = "cpu",
        lr: float = 0.001,
        batch_size: int = 128,
        epochs: int = 5,
        seed: Optional[int] = None
    ):
        """
        Initialiser l'entraîneur.
        
        Args:
            model: Modèle PyTorch à entraîner
            device: Device ('cpu' ou 'cuda')
            lr: Learning rate
            batch_size: Taille des mini-batches
            epochs: Nombre d'epochs
            seed: Seed aléatoire pour reproductibilité (optionnel)
        
        Hyperparamètres (JEPA-1):
            - lr=0.001: Valeur par défaut Adam, stable pour ce type de modèle
            - batch_size=128: Compromis vitesse/stabilité
            - epochs=5: Suffisant pour convergence sur Snake simple
        """
        self.model = model.to(device)
        self.device = device
        self.lr = lr
        self.batch_size = batch_size
        self.epochs = epochs
        self.seed = seed
        
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        self.historique_mse: List[float] = []
        
        if seed is not None:
            self._set_seed(seed)
    
    def _set_seed(self, seed: int) -> None:
        """
        Fixer les seeds pour reproductibilité.
        
        Args:
            seed: Valeur du seed
        """
        random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    
    def entrainer(
        self, 
        x: torch.Tensor, 
        y: torch.Tensor,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Entraîner le modèle sur les données (x, y).
        
        Args:
            x: Observations au temps t [N, dim]
            y: Observations au temps t+1 [N, dim]
            verbose: Afficher les logs d'entraînement
        
        Returns:
            Rapport d'entraînement avec:
                - epochs, batch_size, lr, seed
                - mse_par_epoch: [epoch1, epoch2, ...]
                - mse_finale: MSE de la dernière epoch
                - duree_secondes: temps d'entraînement
        
        Théorie:
            L'entraînement minimise:
                MSE(f̂(zₜ), zₜ₊₁)
            
            Cela apprend au modèle à prédire les transitions observées.
            
            La MSE finale sera utilisée pour calibrer le gate de surprise.
        
        Pipeline:
            1. Pour chaque epoch:
                a. Permuter aléatoirement les données
                b. Pour chaque mini-batch:
                    - Forward: pred = model(x)
                    - Loss: mse = MSE(pred, y)
                    - Backward + step optimizer
                c. Calculer MSE moyenne de l'epoch
            2. Retourner rapport complet
        """
        x = x.to(self.device)
        y = y.to(self.device)
        
        n = x.shape[0]
        indices = torch.arange(n, device=self.device)
        
        self.model.train()
        self.historique_mse = []
        
        debut = time.time()
        
        for epoch in range(1, self.epochs + 1):
            # Permutation aléatoire des indices
            perm = indices[torch.randperm(n)]
            
            total_loss = 0.0
            nb_samples = 0
            
            # Mini-batches
            for i in range(0, n, self.batch_size):
                batch_idx = perm[i:i+self.batch_size]
                xb = x[batch_idx]
                yb = y[batch_idx]
                
                # Forward
                pred = self.model(xb)
                loss = F.mse_loss(pred, yb)
                
                # Backward
                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                self.optimizer.step()
                
                # Accumulation
                total_loss += float(loss.item()) * xb.shape[0]
                nb_samples += xb.shape[0]
            
            mse_epoch = total_loss / nb_samples
            self.historique_mse.append(mse_epoch)
            
            if verbose:
                print(f"[epoch {epoch}/{self.epochs}] mse={mse_epoch:.6f}")
        
        duree = time.time() - debut
        
        return {
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'lr': self.lr,
            'seed': self.seed,
            'mse_par_epoch': self.historique_mse,
            'mse_finale': self.historique_mse[-1] if self.historique_mse else None,
            'duree_secondes': duree,
            'horodatage': time.strftime("%Y-%m-%d_%Hh%M"),
        }
    
    def evaluer(
        self, 
        x: torch.Tensor, 
        y: torch.Tensor
    ) -> Dict[str, float]:
        """
        Évaluer le modèle sur un dataset de test.
        
        Args:
            x: Observations au temps t [N, dim]
            y: Observations au temps t+1 [N, dim]
        
        Returns:
            Statistiques d'erreur:
                - mse_moyenne: MSE globale
                - mse_std: écart-type de la MSE par exemple
                - mse_min: MSE minimale
                - mse_max: MSE maximale
        
        Utilité:
            - Validation sur données de test
            - Détection d'overfitting
            - Analyse de la qualité du modèle
        """
        x = x.to(self.device)
        y = y.to(self.device)
        
        self.model.eval()
        
        with torch.no_grad():
            pred = self.model(x)
            mse_global = F.mse_loss(pred, y)
            mse_par_exemple = F.mse_loss(
                pred, y, reduction='none'
            ).mean(dim=1)
        
        mse_np = mse_par_exemple.detach().cpu().numpy()
        
        return {
            'mse_moyenne': float(mse_global.item()),
            'mse_std': float(mse_np.std()),
            'mse_min': float(mse_np.min()),
            'mse_max': float(mse_np.max()),
        }
    
    def calculer_surprises(
        self,
        x: torch.Tensor,
        y: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculer les surprises pour un dataset.
        
        Args:
            x: Observations au temps t [N, dim]
            y: Observations au temps t+1 [N, dim]
        
        Returns:
            Surprises [N] (MSE par exemple)
        
        Utilité:
            Utilisé pour calibrer le gate de surprise.
        """
        x = x.to(self.device)
        y = y.to(self.device)
        
        self.model.eval()
        
        with torch.no_grad():
            pred = self.model(x)
            surprises = F.mse_loss(
                pred, y, reduction='none'
            ).mean(dim=1)
        
        return surprises
    
    def sauvegarder_checkpoint(
        self, 
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Sauvegarder un checkpoint complet.
        
        Args:
            output_path: Chemin de sauvegarde
            metadata: Métadonnées optionnelles
        
        Format:
            {
                'state_dict': poids du modèle,
                'optimizer_state': état de l'optimiseur,
                'historique_mse': historique d'entraînement,
                'config': hyperparamètres,
                'metadata': métadonnées optionnelles
            }
        """
        checkpoint = {
            'state_dict': self.model.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'historique_mse': self.historique_mse,
            'config': {
                'lr': self.lr,
                'batch_size': self.batch_size,
                'epochs': self.epochs,
                'seed': self.seed,
            }
        }
        if metadata:
            checkpoint['metadata'] = metadata
        
        torch.save(checkpoint, output_path)
    
    def charger_checkpoint(self, path: str) -> Dict[str, Any]:
        """
        Charger un checkpoint pour reprendre l'entraînement.
        
        Args:
            path: Chemin du checkpoint
        
        Returns:
            Métadonnées du checkpoint
        """
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        self.historique_mse = checkpoint.get('historique_mse', [])
        
        return checkpoint.get('metadata', {})
    
    def __repr__(self) -> str:
        return (
            f"EntraineurModelePredicdictif("
            f"lr={self.lr}, batch_size={self.batch_size}, "
            f"epochs={self.epochs}, device={self.device})"
        )
