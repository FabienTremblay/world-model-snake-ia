"""
Tests unitaires pour le gate de surprise.
"""

import pytest
import torch
import numpy as np


from services.agent_service.app.epistemique_v2.gates.gate_surprise import (
    GateSurprise,
    ConfigGate,
    StatsSurprise,
)

class TestStatsSurprise:
    """Tests pour StatsSurprise."""
    
    def test_depuis_array(self):
        """Test calcul statistiques depuis array."""
        arr = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        stats = StatsSurprise.depuis_array(arr)
        
        assert stats.n == 5
        assert stats.mean == pytest.approx(0.3)
        assert stats.min == 0.1
        assert stats.max == 0.5
        assert 'p50' in stats.quantiles
        assert 'p90' in stats.quantiles
    
    def test_to_dict(self):
        """Test export en dict."""
        arr = np.array([1.0, 2.0, 3.0])
        stats = StatsSurprise.depuis_array(arr)
        d = stats.to_dict()
        
        assert 'n' in d
        assert 'mean' in d
        assert 'quantiles' in d


class TestConfigGate:
    """Tests pour ConfigGate."""
    
    def test_defaults(self):
        """Test valeurs par défaut."""
        cfg = ConfigGate()
        assert cfg.mode == "quantile"
        assert cfg.quantile == 0.90
        assert cfg.seuil_connu == 0.10
    
    def test_custom(self):
        """Test valeurs personnalisées."""
        cfg = ConfigGate(mode="seuil", quantile=0.95, seuil_connu=0.05)
        assert cfg.mode == "seuil"
        assert cfg.quantile == 0.95
        assert cfg.seuil_connu == 0.05


class TestGateSurprise:
    """Tests pour GateSurprise."""
    
    def test_init(self):
        """Test initialisation."""
        cfg = ConfigGate()
        gate = GateSurprise(cfg)
        
        assert gate.config.mode == "quantile"
        assert gate.calibre == False
    
    def test_calibrer_quantile(self):
        """Test calibration mode quantile."""
        surprises = torch.tensor([
            0.01, 0.02, 0.03, 0.04, 0.05,
            0.06, 0.07, 0.08, 0.09, 0.10
        ])
        
        cfg = ConfigGate(mode="quantile", quantile=0.90)
        gate = GateSurprise(cfg)
        gate.calibrer(surprises)
        
        assert gate.calibre == True
        assert gate.stats is not None
        # p90 de [0.01...0.10] ≈ 0.091
        assert gate.seuil_calibre == pytest.approx(0.091, abs=0.01)
    
    def test_calibrer_seuil(self):
        """Test calibration mode seuil fixe."""
        surprises = torch.randn(100)
        
        cfg = ConfigGate(mode="seuil", seuil_connu=0.15)
        gate = GateSurprise(cfg)
        gate.calibrer(surprises)
        
        assert gate.calibre == True
        assert gate.seuil_calibre == 0.15  # Seuil fixe, non modifié
    
    def test_est_connu_error_avant_calibration(self):
        """Test erreur si gate non calibré."""
        gate = GateSurprise(ConfigGate())
        
        with pytest.raises(RuntimeError):
            gate.est_connu(0.05)
    
    def test_est_connu_apres_calibration(self):
        """Test classification après calibration."""
        surprises = torch.linspace(0, 1, 100)
        
        cfg = ConfigGate(mode="quantile", quantile=0.90)
        gate = GateSurprise(cfg)
        gate.calibrer(surprises)
        
        # Surprise faible → connu
        assert gate.est_connu(0.01) == True
        
        # Surprise élevée → inconnu
        assert gate.est_connu(0.99) == False
    
    def test_decider_mode(self):
        """Test décision de mode."""
        surprises = torch.linspace(0, 1, 100)
        
        cfg = ConfigGate(mode="quantile", quantile=0.80)
        gate = GateSurprise(cfg)
        gate.calibrer(surprises)
        
        # Situation connue
        mode1, action1 = gate.decider_mode(0.1)
        assert mode1 == "connu_exploiter"
        assert action1 == "exploiter"
        
        # Situation inconnue
        mode2, action2 = gate.decider_mode(0.9)
        assert mode2 == "inconnu_explorer"
        assert action2 == "explorer"
    
    def test_analyser_batch(self):
        """Test analyse d'un batch."""
        surprises = torch.cat([
            torch.ones(80) * 0.01,   # 80 faibles
            torch.ones(20) * 0.99    # 20 élevées
        ])
        
        cfg = ConfigGate(mode="quantile", quantile=0.80)
        gate = GateSurprise(cfg)
        gate.calibrer(surprises)
        
        analyse = gate.analyser_batch(surprises)
        
        assert analyse['nb_total'] == 100
        assert analyse['nb_connu'] == 80
        assert analyse['nb_inconnu'] == 20
        assert analyse['ratio_connu'] == pytest.approx(0.80, abs=0.05)
    
    def test_to_dict(self):
        """Test export en dict."""
        surprises = torch.randn(50)
        
        gate = GateSurprise(ConfigGate())
        gate.calibrer(surprises)
        
        d = gate.to_dict()
        
        assert 'config' in d
        assert 'seuil_calibre' in d
        assert 'calibre' in d
        assert 'stats_surprise' in d
    
    def test_depuis_dict(self):
        """Test reconstruction depuis dict."""
        surprises = torch.randn(50)
        
        # Créer et exporter
        gate1 = GateSurprise(ConfigGate(mode="quantile", quantile=0.85))
        gate1.calibrer(surprises)
        d = gate1.to_dict()
        
        # Reconstruire
        gate2 = GateSurprise.depuis_dict(d)
        
        assert gate2.config.mode == "quantile"
        assert gate2.config.quantile == 0.85
        assert gate2.calibre == True
        assert gate2.seuil_calibre == gate1.seuil_calibre
    
    def test_repr(self):
        """Test représentation string."""
        gate = GateSurprise(ConfigGate())
        repr_str = repr(gate)
        
        assert 'GateSurprise' in repr_str
        assert 'non calibré' in repr_str
        
        gate.calibrer(torch.randn(10))
        repr_str2 = repr(gate)
        assert 'calibré' in repr_str2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
