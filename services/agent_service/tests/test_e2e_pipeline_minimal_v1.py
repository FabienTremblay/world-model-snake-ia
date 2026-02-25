import base64
import json
from pathlib import Path

import pytest
import torch

from services.agent_service.app.preparation_agent.extracteurs import ExtracteurPairesCapteurs
from services.agent_service.app.modele_monde.predictif.modele_pred_capteurs_v1 import ModelePredCapteursV1
from services.agent_service.app.epistemique_v2.gates.gate_surprise import GateSurprise, ConfigGate


def _encoder_capteurs_compact(vec: torch.Tensor) -> str:
    """
    Fabrique un capteurs_compact compatible "base64_bytes" :
    float32[dim] -> bytes -> base64 str
    """
    v = vec.detach().to(dtype=torch.float32, device="cpu").contiguous()
    return base64.b64encode(v.numpy().tobytes()).decode("ascii")


def test_e2e_pipeline_minimal(tmp_path: Path):
    torch.manual_seed(0)

    dim = 560
    # 2 épisodes, 6 observations chacun => (6-1)*2 = 10 paires attendues
    obs_par_episode = 6
    nb_episodes = 2

    journal = tmp_path / "journal_episodes.jsonl"
    sortie = tmp_path / "paires.pt"

    lignes = []
    for episode_id in range(1, nb_episodes + 1):
        for tick in range(obs_par_episode):
            vec = torch.randn(dim) * 0.1 + (episode_id * 0.01)  # léger décalage par épisode
            lignes.append({
                "episode_id": episode_id,
                "tick": tick,
                "capteurs_compact": _encoder_capteurs_compact(vec),
            })

    journal.write_text("\n".join(json.dumps(o) for o in lignes) + "\n", encoding="utf-8")

    # 1) Extraction (journal -> dataset)
    extracteur = ExtracteurPairesCapteurs(dim)
    meta_stats = extracteur.extraire_et_sauvegarder(
        str(journal),
        str(sortie),
        cle_capteurs="capteurs_compact",
        cle_episode_id="episode_id",
    )

    obj = torch.load(sortie, map_location="cpu")
    x = obj["x"]
    y = obj["y"]
    meta = obj.get("meta", obj.get("metadata", {}))

    assert x.shape == y.shape
    assert x.shape[1] == dim

    nb_paires_attendues = nb_episodes * (obs_par_episode - 1)
    assert x.shape[0] == nb_paires_attendues
    assert int(meta.get("nb_paires", x.shape[0])) == nb_paires_attendues
    assert int(meta.get("dim", dim)) == dim
    assert meta.get("champ_capteurs") == "capteurs_compact"

    # 2) Modèle + surprises (dataset -> surprises)
    model = ModelePredCapteursV1(dim_in=dim, hidden=64)
    model.eval()

    with torch.no_grad():
        pred = model(x)
        surprises = model.calculer_surprise(pred, y)

    assert pred.shape == x.shape
    assert surprises.shape == (nb_paires_attendues,)
    assert torch.isfinite(surprises).all()
    assert (surprises >= 0).all()

    # 3) Gate (surprises -> seuil + ratio)
    cfg = ConfigGate(mode="quantile", quantile=0.80)
    gate = GateSurprise(cfg)
    gate.calibrer(surprises)

    assert gate.calibre is True
    analyse = gate.analyser_batch(surprises)

    assert analyse["nb_total"] == nb_paires_attendues
    assert analyse["ratio_connu"] == pytest.approx(0.80, abs=0.10)
