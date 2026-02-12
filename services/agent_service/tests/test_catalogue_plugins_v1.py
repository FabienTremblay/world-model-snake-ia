from __future__ import annotations

from pathlib import Path
import os
import pytest

from agent_service.app.catalogue_agents import charger_catalogue, creer_agent

@pytest.fixture(autouse=True)
def _nettoyer_env():
    old = os.environ.get("SNAKE_MODELE_JOURNAL")
    yield
    if old is None:
        os.environ.pop("SNAKE_MODELE_JOURNAL", None)
    else:
        os.environ["SNAKE_MODELE_JOURNAL"] = old


def test_catalogue_plugins_liste_ids_minimaux():
    cat = charger_catalogue()
    # ids attendus selon ton état actuel (plug-ins)
    attendus = {
        "aleatoire",
        "curiosite_tabulaire",
        "planif_1pas_temperament",
        "planif_mpc_observateur_tabulaire",
        "planif_mpc_tabulaire",
        "snake_collectif_v1_c1",
        "snake_collectif_v1_c2",
    }
    assert attendus.issubset(set(cat.keys()))


@pytest.mark.parametrize(
    "id_agent",
    [
        "aleatoire",
        "curiosite_tabulaire",
        "snake_collectif_v1_c1",
        "snake_collectif_v1_c2",
    ],
)
def test_agents_instanciables_sans_params(id_agent: str):
    a = creer_agent(id_agent, params={})
    assert a is not None


def test_planif_mpc_tabulaire_refuse_sans_journal():
    # On s'assure que l'env n'aide pas
    if "SNAKE_MODELE_JOURNAL" in os.environ:
        os.environ.pop("SNAKE_MODELE_JOURNAL")

    with pytest.raises(ValueError) as e:
        creer_agent("planif_mpc_tabulaire", params={})

    # message actuel de l'agent (on veut au moins la variable dans le message)
    assert "SNAKE_MODELE_JOURNAL" in str(e.value)


def test_planif_mpc_tabulaire_ok_avec_env(tmp_path: Path):
    # Crée un journal minimal pour satisfaire le constructeur
    j = tmp_path / "train.jsonl"
    j.write_text('{"tick":0}\n', encoding="utf-8")

    os.environ["SNAKE_MODELE_JOURNAL"] = str(j)

    a = creer_agent("planif_mpc_tabulaire", params={})
    assert a is not None

def test_creer_agent_api_stricte_pas_de_kwargs():
    with pytest.raises(TypeError):
        # type: ignore[call-arg]
        creer_agent("aleatoire", params={}, seed=123)

def test_planif_1pas_temperament_refuse_sans_journal():
    if "SNAKE_MODELE_JOURNAL" in os.environ:
        os.environ.pop("SNAKE_MODELE_JOURNAL")

    with pytest.raises(Exception) as e:
        creer_agent("planif_1pas_temperament", params={})

    assert "SNAKE_MODELE_JOURNAL" in str(e.value)


def test_planif_1pas_temperament_ok_avec_env(tmp_path: Path):
    j = tmp_path / "train.jsonl"
    j.write_text('{"tick":0}\n', encoding="utf-8")

    os.environ["SNAKE_MODELE_JOURNAL"] = str(j)

    a = creer_agent("planif_1pas_temperament", params={})
    assert a is not None

from pathlib import Path
import yaml

def test_tous_les_agent_yml_sont_valides_et_importables():
    base = Path("services/agent_service/app/agents")
    ymls = sorted(list(base.glob("**/agent*.yml")) + list(base.glob("**/agent*.yaml")))
    assert ymls, "aucun agent*.yml trouvé"

    # Parse YAML
    for p in ymls:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{p} doit être un dict YAML (map), pas une liste"

    # Et surtout: charger_catalogue doit réussir (import des fabriques/classes)
    cat = charger_catalogue()
    assert isinstance(cat, dict) and cat

