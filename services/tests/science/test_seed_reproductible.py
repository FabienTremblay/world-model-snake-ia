
import random

def run(seed):
    random.seed(seed)
    return [random.randint(0,10) for _ in range(5)]

def test_seed_reproductible():
    assert run(42)==run(42)
