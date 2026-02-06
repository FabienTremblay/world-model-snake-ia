# conftest.py (racine)
import random
import pytest

@pytest.fixture(autouse=True)
def seed_aleatoire():
    random.seed(12345)
