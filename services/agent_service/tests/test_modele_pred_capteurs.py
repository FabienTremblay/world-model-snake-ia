"""
Tests unitaires pour le modèle prédictif de capteurs.
"""

import pytest
import torch
import tempfile
from pathlib import Path

from services.agent_service.app.modele_monde.predictif.modele_pred_capteurs_v1 import (
    ModelePredCapteursV1,
)


class TestModelePredCapteursV1:
    """Tests pour ModelePredCapteursV1."""
    
    def test_init_defaults(self):
        """Test initialisation avec valeurs par défaut."""
        model = ModelePredCapteursV1()
        assert model.dim_in == 560
        assert model.hidden == 64
    
    def test_init_custom(self):
        """Test initialisation avec valeurs personnalisées."""
        model = ModelePredCapteursV1(dim_in=128, hidden=32)
        assert model.dim_in == 128
        assert model.hidden == 32
    
    def test_forward_shape(self):
        """Test que forward préserve la forme."""
        model = ModelePredCapteursV1(dim_in=100, hidden=50)
        x = torch.randn(10, 100)
        y = model(x)
        assert y.shape == (10, 100)
    
    def test_forward_deterministic(self):
        """Test que forward est déterministe en eval."""
        model = ModelePredCapteursV1(dim_in=50, hidden=25)
        model.eval()
        x = torch.randn(5, 50)
        
        y1 = model(x)
        y2 = model(x)
        
        assert torch.allclose(y1, y2)
    
    def test_calculer_surprise_shape(self):
        """Test que surprise a la bonne forme."""
        model = ModelePredCapteursV1(dim_in=60, hidden=30)
        pred = torch.randn(8, 60)
        obs = torch.randn(8, 60)
        
        surprise = model.calculer_surprise(pred, obs)
        
        assert surprise.shape == (8,)
        assert (surprise >= 0).all()  # MSE toujours positif
    
    def test_calculer_surprise_zero(self):
        """Test surprise nulle pour prédiction parfaite."""
        model = ModelePredCapteursV1(dim_in=40, hidden=20)
        x = torch.randn(3, 40)
        
        surprise = model.calculer_surprise(x, x)
        
        assert torch.allclose(surprise, torch.zeros(3), atol=1e-6)
    
    def test_sauvegarder_charger(self):
        """Test sauvegarde et chargement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.pt"
            
            # Créer et sauvegarder
            model1 = ModelePredCapteursV1(dim_in=80, hidden=40)
            metadata = {'test': 'value'}
            model1.sauvegarder(str(path), metadata)
            
            # Charger dans nouveau modèle
            model2 = ModelePredCapteursV1(dim_in=80, hidden=40)
            loaded_meta = model2.charger(str(path))
            
            # Vérifier métadonnées
            assert loaded_meta['test'] == 'value'
            
            # Vérifier poids identiques
            x = torch.randn(5, 80)
            model1.eval()
            model2.eval()
            
            y1 = model1(x)
            y2 = model2(x)
            
            assert torch.allclose(y1, y2)
    
    def test_depuis_checkpoint(self):
        """Test création depuis checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.pt"
            
            # Sauvegarder
            model1 = ModelePredCapteursV1(dim_in=70, hidden=35)
            model1.sauvegarder(str(path))
            
            # Charger via classmethod
            model2 = ModelePredCapteursV1.depuis_checkpoint(str(path))
            
            # Vérifier config
            assert model2.dim_in == 70
            assert model2.hidden == 35
            
            # Vérifier prédictions identiques
            x = torch.randn(4, 70)
            model1.eval()
            model2.eval()
            
            assert torch.allclose(model1(x), model2(x))
    
    def test_valider_dimensions_error(self):
        """Test que validation détecte erreurs de dimensions."""
        model = ModelePredCapteursV1(dim_in=50, hidden=25)
        
        # Mauvaise dimension
        x_wrong = torch.randn(10, 60)  # 60 au lieu de 50
        
        with pytest.raises(ValueError):
            model.valider_dimensions(x_wrong, 50)
    
    def test_charger_mismatch_error(self):
        """Test erreur si dimensions incompatibles au chargement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.pt"
            
            # Sauvegarder avec dim=50
            model1 = ModelePredCapteursV1(dim_in=50, hidden=25)
            model1.sauvegarder(str(path))
            
            # Essayer charger dans modèle avec dim=60
            model2 = ModelePredCapteursV1(dim_in=60, hidden=30)
            
            with pytest.raises(ValueError):
                model2.charger(str(path))
    
    def test_repr(self):
        """Test représentation string."""
        model = ModelePredCapteursV1(dim_in=100, hidden=50)
        repr_str = repr(model)
        
        assert 'ModelePredCapteursV1' in repr_str
        assert 'dim_in=100' in repr_str
        assert 'hidden=50' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
