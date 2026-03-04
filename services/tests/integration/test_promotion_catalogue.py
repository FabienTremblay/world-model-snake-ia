
import yaml
from pathlib import Path

def test_promotion_catalogue(tmp_path):
    cat = tmp_path/"catalogue"
    hist = cat/"historique"
    hist.mkdir(parents=True)

    individu={"version":2}
    hash="xyz"

    (hist/f"{hash}.yml").write_text(yaml.safe_dump(individu))
    (cat/"individu.yml").write_text(yaml.safe_dump(individu))

    assert (cat/"individu.yml").exists()
    assert (hist/f"{hash}.yml").exists()
