
import yaml
from pathlib import Path

def test_individu_entree_snapshot(tmp_path):
    individu_catalogue = {"individu_id":"ia_demo","version":1}
    catalogue = tmp_path/"catalogue.yml"
    entree = tmp_path/"individu_entree.yml"

    yaml.safe_dump(individu_catalogue, catalogue.open("w"))

    # simulation snapshot
    entree.write_text(catalogue.read_text())

    entree_loaded = yaml.safe_load(entree.read_text())
    catalogue_loaded = yaml.safe_load(catalogue.read_text())

    assert entree_loaded == catalogue_loaded
