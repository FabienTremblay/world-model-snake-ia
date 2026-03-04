
import pytest

def promote(mode):
    if mode=="epreuve":
        raise SystemExit("promotion interdite")

def test_promotion_epreuve_interdite():
    with pytest.raises(SystemExit):
        promote("epreuve")
