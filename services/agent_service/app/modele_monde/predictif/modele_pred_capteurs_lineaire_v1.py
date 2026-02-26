"""Modèle prédictif des capteurs projetés - Linéaire (v1).

But
---
Fournir une hypothèse concurrente *à biais différent* pour JEPA-3/JEPA-4.

Contrairement à ModelePredCapteursV1 (MLP non-linéaire), ce modèle est une
simple transformation linéaire dim_in -> dim_in.

Intérêt scientifique
--------------------
- baseline explicite (capacité limitée)
- favorise une compétition saillante (winner non trivial)
- favorise un désaccord non dégénéré (JEPA-4)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from .modele_predictif_base import ModelePredicifBase


class ModelePredCapteursLineaireV1(ModelePredicifBase):
    """Prédiction linéaire z_t -> z_{t+1}."""

    def __init__(self, dim_in: int = 560):
        super().__init__()
        self.dim_in = dim_in
        self.net = nn.Linear(dim_in, dim_in, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.valider_dimensions(x, self.dim_in)
        return self.net(x)

    def calculer_surprise(self, prediction: torch.Tensor, observation: torch.Tensor) -> torch.Tensor:
        self.valider_dimensions(prediction, self.dim_in)
        self.valider_dimensions(observation, self.dim_in)
        return F.mse_loss(prediction, observation, reduction='none').mean(dim=1)

    def sauvegarder(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        save_dict = {
            'state_dict': self.state_dict(),
            'dim_in': self.dim_in,
            'model_type': 'ModelePredCapteursLineaireV1',
        }
        if metadata:
            save_dict['metadata'] = metadata
        torch.save(save_dict, path)

    def charger(self, path: str, device: str = 'cpu') -> None:
        """Recharge le modèle à partir d'un checkpoint sauvegardé par `sauvegarder`.

        Note: cette méthode existe surtout pour respecter le contrat abstrait
        (utilisée par le pipeline pour recharger avant l'épreuve).
        """
        checkpoint = torch.load(path, map_location=device)
        dim_in = int(checkpoint.get('dim_in', self.dim_in))
        if dim_in != self.dim_in:
            raise ValueError(f"checkpoint dim_in={dim_in} incompatible avec self.dim_in={self.dim_in}")
        self.load_state_dict(checkpoint['state_dict'])
        self.to(device)
        self.eval()

    @classmethod
    def depuis_checkpoint(cls, path: str, device: str = 'cpu') -> 'ModelePredCapteursLineaireV1':
        checkpoint = torch.load(path, map_location=device)
        model = cls(dim_in=int(checkpoint['dim_in'])).to(device)
        model.load_state_dict(checkpoint['state_dict'])
        return model

    def __repr__(self) -> str:
        return f"ModelePredCapteursLineaireV1(dim_in={self.dim_in}, params={sum(p.numel() for p in self.parameters())})"
