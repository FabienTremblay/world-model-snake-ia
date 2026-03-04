
def evolution(individu):
    individu = dict(individu)
    individu["version"] += 1
    individu.setdefault("memoire_courte",{})
    individu["memoire_courte"]["compteur_runs"] = individu["memoire_courte"].get("compteur_runs",0)+1
    return individu

def test_individu_evolution():
    individu = {"version":1,"memoire_courte":{"compteur_runs":0}}
    new = evolution(individu)

    assert new["version"] == 2
    assert new["memoire_courte"]["compteur_runs"] == 1
