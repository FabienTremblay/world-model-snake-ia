from pathlib import Path
import torch
import pytest

from services.agent_service.app.modele_monde.predictif.modele_pred_capteurs_v1 import ModelePredCapteursV1
from services.agent_service.app.epistemique_v2.gates.gate_surprise import GateSurprise, ConfigGate


def test_contrat_pipeline_surprise_gate():
    torch.manual_seed(0)

    # dataset synthétique stable
    n = 512
    dim = 560
    x = torch.randn(n, dim)
    y = x + 0.05 * torch.randn(n, dim)  # proche de x, surprise faible/modérée

    meta = {
        "source": "synthetique",
        "dim": dim,
        "nb_paires": n,
        "champ_capteurs": "synthetique",
    }

    # modèle (déterministe en eval)
    model = ModelePredCapteursV1(dim_in=dim, hidden=64)
    model.eval()

    with torch.no_grad():
        pred = model(x)
        surprises = model.calculer_surprise(pred, y)

    assert pred.shape == x.shape
    assert surprises.shape == (n,)
    assert torch.isfinite(surprises).all()
    assert (surprises >= 0).all()

    # stats robustes
    p50 = float(surprises.quantile(0.50))
    p90 = float(surprises.quantile(0.90))
    assert p90 >= p50

    # gate calibré
    cfg = ConfigGate(mode="quantile", quantile=0.90)
    gate = GateSurprise(cfg)
    gate.calibrer(surprises)

    assert gate.calibre is True
    # seuil calibré doit être proche du p90 (tolérance large)
    assert gate.seuil_calibre == pytest.approx(p90, rel=0.15, abs=1e-6)

    analyse = gate.analyser_batch(surprises)
    assert analyse["nb_total"] == n
    # si quantile=0.90, on s'attend à ~90% connu
    assert analyse["ratio_connu"] == pytest.approx(0.90, abs=0.05)
