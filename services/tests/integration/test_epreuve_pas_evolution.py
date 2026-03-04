
def test_epreuve_pas_evolution():
    mode="epreuve"
    individu_sortie=None if mode=="epreuve" else {}

    assert individu_sortie is None
