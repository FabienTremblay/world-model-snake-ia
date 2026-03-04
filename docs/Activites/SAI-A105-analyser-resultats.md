# SAI-A105 : Analyser les Résultats (Diagnostics)

## Vue d'ensemble

L'activité **SAI-A105** est le processus d'**évaluation et d'analyse** des comportements observés lors des expérimentations. C'est l'étape où l'on pose des questions précises aux données pour comprendre ce qui fonctionne, ce qui échoue, et pourquoi.

### Position dans le flux de travail

```
SAI-A102                SAI-A105                SAI-A106
Générer des       →     Analyser les      →     Produire des
épisodes                résultats               hypothèses
(Journal               (Diagnostics)           (Registre
d'épisodes)                                    épistémique)
```

### Objectif

Produire des **diagnostics ciblés** qui répondent à des questions précises :
- L'agent évite-t-il les murs ?
- Quand l'agent se crashe-t-il contre lui-même ?
- Le modèle du monde prédit-il bien les terminaisons ?
- Quelle est la couverture du modèle tabulaire ?
- Les récompenses prédites sont-elles proches de la réalité ?

---

## Principe Fondamental : Question → Diagnostic

### Philosophie

SAI-A105 n'est **pas une analyse exploratoire générale**. C'est un ensemble de **diagnostics ciblés**, chacun conçu pour répondre à une question spécifique de l'expérimentateur.

Chaque diagnostic :
1. **Pose une question précise** : "Que se passe-t-il quand X est vrai ?"
2. **Extrait les données pertinentes** du journal
3. **Calcule des métriques spécifiques**
4. **Produit un rapport structuré** (JSON)

### Métaphore médicale

| Analyse générale (mauvais) | Diagnostic ciblé (bon) |
|---------------------------|----------------------|
| "Bilan sanguin complet" | "Test de glycémie à jeun" |
| "Regardons toutes les données" | "Vérifions si le taux de collision diminue" |
| Exploration sans but | Investigation guidée par hypothèse |

---

## Types de Diagnostics Disponibles

### 1. Diagnostic Mur Devant (v1)

**Question :** Que se passe-t-il quand l'agent fonce vers un mur ?

**Fichier :** `diagnostic_mur_devant_v1.py`

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_mur_devant_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --experience cours4
```

**Ce qu'il mesure :**
- Proportion de transitions où l'action pointe vers un mur
- Proportion de terminaisons dans ces cas
- Ventilation par direction (haut/bas/gauche/droite)

**Exemple de sortie :**
```json
{
  "nb_transitions": 7007,
  "nb_action_vers_mur": 59,
  "ratio_action_vers_mur": 0.0084,
  "nb_termine_si_action_vers_mur": 59,
  "ratio_termine_si_action_vers_mur": 1.0,
  "par_action": {
    "gauche": {
      "nb_transitions": 1933,
      "nb_action_vers_mur": 41,
      "ratio_action_vers_mur": 0.0212,
      "ratio_termine_si_action_vers_mur": 1.0
    }
  }
}
```

**Interprétation :**
- L'agent fonce vers un mur dans 0.84% des cas
- 100% de ces actions mènent à une terminaison
- L'action "gauche" est la plus dangereuse (41/59 collisions)

**Usage :**
- Valider l'hypothèse "mur → collision"
- Détecter un biais directionnel de l'agent
- Comparer agents (aléatoire vs planificateur)

### 2. Diagnostic Collision Soi (v1)

**Question :** L'agent se mord-il la queue ?

**Fichier :** `diagnostic_collision_soi_devant_v1.py`

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_collision_soi_devant_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --motif-corps 1 \
  --raison-fin collision_soi \
  --experience cours4
```

**Ce qu'il mesure :**
- Proportion de transitions vers son propre corps
- Proportion de terminaisons avec raison "collision_soi"

**Interprétation :**
```json
{
  "total_corps_action": 0,
  "ratio_termine_si_action_vers_corps": null
}
```
→ Aucune collision avec soi détectée  
→ L'agent est trop court ou trop prudent

**Usage :**
- Vérifier si l'agent apprend à éviter son corps
- Comparer avec les collisions mur

### 3. Diagnostic Terminaison (Binning v1)

**Question :** Le modèle prédit-il bien les terminaisons ?

**Fichier :** `diagnostic_termination_binning_v1.py`

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_termination_binning_v1 \
  --journal artefacts/episodes_signaux_hash.jsonl \
  --champ-latent signaux_hash \
  --experience cours4
```

**Ce qu'il mesure :**
- Distribution de P(terminaison) prédite
- Ratio de transitions inconnues (support=0)
- Calibration du modèle

**Exemple de sortie :**
```json
{
  "support0_ratio": 0.23,
  "bins_p_fin": {
    "None": 1420,
    "0.0": 3200,
    "0.1": 50,
    "1.0": 180
  }
}
```

**Interprétation :**
- 23% des transitions sont inconnues du modèle
- La plupart des prédictions sont à 0.0 (sûr) ou 1.0 (danger certain)
- Peu de cas ambigus (0.1-0.9)

**Usage :**
- Évaluer la qualité du modèle tabulaire
- Comparer latent fin (checksum) vs compressé (signaux_hash)
- Identifier les situations mal modélisées

### 4. Diagnostic Utilité du Modèle (v1)

**Question :** Le modèle du monde est-il précis ?

**Fichier :** `diagnostic_utilite_v1.py`

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_utilite_v1 \
  --journal artefacts/episodes_latent_appris.jsonl \
  --champ-latent latent_id \
  --ratio-train 0.7 \
  --experience cours4
```

**Ce qu'il mesure :**

#### Pour la récompense :
- **Couverture** : % de transitions connues
- **MAE** (Mean Absolute Error) : |delta_score_réel - delta_score_prédit|

#### Pour la terminaison :
- **Couverture** : % de transitions connues
- **Brier Score** : (p_terminaison - terminaison_réelle)²

**Exemple de sortie :**
```json
{
  "couverture_recompense_test": 0.92,
  "couverture_termination_test": 0.94,
  "mae_esperance_delta_score": {
    "moy": 0.12,
    "med": 0.0,
    "max": 2.0
  },
  "brier_termination": {
    "moy": 0.03,
    "med": 0.0
  }
}
```

**Interprétation :**
- Excellente couverture (>90%)
- Erreur moyenne faible (0.12 points de score)
- Brier faible (0.03) = bonnes prédictions de terminaison

**Usage :**
- Validation du modèle avant planification (MPC)
- Comparaison de différents encodages latents
- Décision "prêt pour SAI-A107" ou "besoin de plus de données"

### 5. Diagnostic Pas Unique (v1)

**Question :** Le futur est-il déterministe ou stochastique ?

**Fichier :** `diagnostic_pas_unique_v1.py`

**Ce qu'il mesure :**
- Pour chaque (état, action), combien d'états suivants différents ?
- Distribution de cette multiplicité

**Exemple de sortie :**
```json
{
  "cles_uniques": 842,
  "cles_multiples": 158,
  "ratio_multiples": 0.158,
  "multiplicite_moyenne": 1.3
}
```

**Interprétation :**
- 15.8% des situations ont plusieurs futurs possibles
- En moyenne, 1.3 états suivants par (z, a)
- Le monde n'est pas déterministe du point de vue du latent

**Usage :**
- Comprendre l'incertitude du modèle
- Justifier l'utilisation de distributions (vs prédiction unique)
- Valider que le latent regroupe des situations similaires

### 6. Diagnostic Épistémique Smoke (v1)

**Question :** Le registre épistémique est-il cohérent ?

**Fichier :** `diagnostic_epistemique_smoke_v1.py`

**Ce qu'il mesure :**
- Présence de toutes les hypothèses attendues
- Présence des évaluations correspondantes
- Cohérence interne (pas de contradictions logiques)

**Usage :**
- Test de santé du registre
- Validation avant utilisation en SAI-A107

### 7. Diagnostic Observateur Croissance (v1)

**Question :** L'observateur détecte-t-il les bons signaux ?

**Fichier :** `diagnostic_observateur_croissance_v1.py`

**Ce qu'il mesure :**
- Corrélation entre delta_longueur et utilité calculée
- Cohérence des pénalités (collision_mur)

---

## Architecture d'un Diagnostic

### Structure Standard

Chaque diagnostic suit le même pattern :

```python
def main() -> int:
    # 1. Parser les arguments
    args = _parser().parse_args()
    
    # 2. Résoudre les chemins (bac à sable)
    bac = BacASableV1.charger_depuis_id(...)
    journal_path = bac.resoudre_chemin(args.journal)
    
    # 3. Charger et regrouper les données
    episodes = _charger_episodes(journal_path)
    
    # 4. Calculer les statistiques ciblées
    stats = _calculer_statistiques(episodes)
    
    # 5. Produire le rapport JSON
    rapport = {
        "journal": str(journal_path),
        "nb_evenements": ...,
        "resultats": stats
    }
    
    # 6. Écrire la sortie
    print(json.dumps(rapport, indent=2))
    out_path.write_text(json.dumps(rapport))
    
    return 0
```

### Conventions de Sortie

**Nom du fichier :**
```
donnees/config/experiences/<experience>/artefacts/diagnostics/
  └── diagnostic_<type>_v<version>__<source>.json
```

**Exemple :**
```
diagnostic_mur_devant_v1__journal_episodes.json
```

---

## Workflow Typique SAI-A105

### Scénario : Évaluer un nouvel agent

**Étape 1 : Collecter les données**
```bash
# SAI-A102 : Générer 100 épisodes
./scripts/dev.sh --arene tiny_v0 --agent agent_nouveau --episodes 100
```

**Étape 2 : Diagnostics de base**
```bash
# Question : L'agent évite-t-il les murs ?
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_mur_devant_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --experience test_agent_nouveau

# Question : Se crashe-t-il contre lui-même ?
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_collision_soi_devant_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --experience test_agent_nouveau
```

**Étape 3 : Analyser les résultats**
```bash
# Lire les rapports JSON
cat donnees/.../diagnostics/diagnostic_mur_devant_v1__journal_episodes.json

# Interpréter
# - ratio_action_vers_mur: 0.15 → agent pas très prudent
# - ratio_termine: 1.0 → mais il meurt à chaque fois
```

**Étape 4 : Diagnostic du modèle**
```bash
# Le modèle apprend-il bien ?
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_utilite_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --champ-latent signaux_hash \
  --experience test_agent_nouveau
```

**Étape 5 : Décision**
```
Si couverture > 0.85 ET mae < 0.3 ET brier < 0.1
  → Passer à SAI-A106 (produire hypothèses)
Sinon
  → Retour à SAI-A102 (collecter plus de données)
```

---

## Métriques Clés

### 1. Couverture

**Définition :** Proportion de transitions connues du modèle

**Formule :** `couverture = nb_transitions_support>0 / nb_transitions_total`

**Interprétation :**
- `> 0.9` : Excellente
- `0.7 - 0.9` : Bonne
- `< 0.7` : Insuffisante (besoin de plus de données)

**Importance :** Un modèle à 100% de précision mais 10% de couverture est inutile.

### 2. Ratio de Terminaison

**Définition :** Proportion de terminaisons dans un contexte donné

**Formule :** `ratio = nb_termine / nb_occurrences`

**Interprétation :**
- `1.0` : Toujours dangereux (règle absolue)
- `0.9` : Très dangereux (règle forte)
- `0.5` : Ambiguë (pas une règle)
- `0.0` : Jamais dangereux (sûr)

**Usage :** Valider les hypothèses de danger

### 3. MAE (Mean Absolute Error)

**Définition :** Erreur moyenne absolue de prédiction

**Formule :** `MAE = moyenne(|prédit - réel|)`

**Interprétation pour delta_score :**
- `< 0.2` : Excellent
- `0.2 - 0.5` : Bon
- `> 0.5` : Moyen

**Usage :** Évaluer la qualité des prédictions de récompense

### 4. Brier Score

**Définition :** Erreur quadratique de prédiction probabiliste

**Formule :** `Brier = moyenne((p_prédit - y_réel)²)`

**Interprétation :**
- `< 0.05` : Excellent
- `0.05 - 0.15` : Bon
- `> 0.15` : Mauvais

**Valeur de référence :**
- Prédire toujours 0.5 : Brier = 0.25
- Mieux que 0.25 = mieux que hasard

**Usage :** Évaluer la calibration des probabilités de terminaison

### 5. Support

**Définition :** Nombre d'observations pour une clé (z, a, z')

**Formule :** `support = nb_fois_observé`

**Interprétation :**
- `> 100` : Très fiable
- `10 - 100` : Fiable
- `< 10` : Peu fiable
- `0` : Inconnu

**Usage :** Pondérer la confiance dans les prédictions

---

## Intégration avec les Autres Activités

### Avec SAI-A102 (Générer)

Les diagnostics guident la **collecte de données** :

```
Diagnostic : couverture = 0.6 (trop faible)
  ↓
SAI-A102 : Générer 200 épisodes supplémentaires
  ↓
SAI-A105 : Re-diagnostiquer
  ↓
Diagnostic : couverture = 0.88 (OK)
```

### Avec SAI-A106 (Hypothèses)

Les diagnostics **valident les hypothèses** :

```
Diagnostic mur : ratio_termine = 1.0
  ↓
SAI-A106 : Hypothèse "mur → collision" validée (confiance 1.0)
  ↓
Registre épistémique enrichi
```

### Avec SAI-A107 (Préparer agent)

Les diagnostics **informent le choix de têtes** :

```
Diagnostic : 15% des terminaisons = collision_soi
  ↓
SAI-A107 : Ajouter tête "detecteur_corps_devant"
  ↓
Agent préparé
```

### Avec SAI-A108 (Éprouver)

Les diagnostics **comparent avant/après** :

```
Avant SAI-A107 :
  Diagnostic : ratio_action_vers_mur = 0.15
  
Après SAI-A107 :
  Diagnostic : ratio_action_vers_mur = 0.02
  ↓
  Amélioration de 87% !
```

---

## Bonnes Pratiques

### 1. Diagnostic Incrémental

Ne pas tout diagnostiquer d'un coup :

```
Itération 1 : Diagnostic mur (simple)
  ↓ Si OK
Itération 2 : Diagnostic collision soi
  ↓ Si OK
Itération 3 : Diagnostic modèle complet
```

### 2. Versionner les Diagnostics

```
diagnostic_mur_devant_v1.py  # Version stable
diagnostic_mur_devant_v2.py  # Version expérimentale
```

Conserver les anciennes versions pour comparaison.

### 3. Automatiser les Seuils

```python
def est_pret_pour_sai_a106(diagnostic: dict) -> bool:
    return (
        diagnostic["couverture_recompense_test"] > 0.85 and
        diagnostic["mae_esperance"]["moy"] < 0.3 and
        diagnostic["brier_termination"]["moy"] < 0.1
    )
```

### 4. Visualiser les Résultats

Bien que les diagnostics produisent du JSON, créer des scripts de visualisation :

```python
import matplotlib.pyplot as plt

def plot_distribution_p_fin(diagnostic: dict):
    bins = diagnostic["bins_p_fin"]
    plt.bar(bins.keys(), bins.values())
    plt.title("Distribution de P(terminaison)")
    plt.xlabel("P(fin)")
    plt.ylabel("Nombre de transitions")
    plt.show()
```

### 5. Documenter les Anomalies

Quand un diagnostic révèle quelque chose d'inattendu :

```json
{
  "anomalies": [
    {
      "type": "bias_directionnel",
      "description": "70% des collisions mur sont à gauche",
      "hypothese": "Arène asymétrique ou agent biaisé",
      "action": "Tester sur arène symétrique"
    }
  ]
}
```

---

## Création d'un Nouveau Diagnostic

### Template

```python
# services/agent_service/app/modele_monde/diagnostic_<nom>_v1.py
"""Diagnostic ciblé: <description>.

Question : <question précise> ?

Mesure :
- <métrique 1>
- <métrique 2>
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from ui_cli.app.bac_a_sable.bac_a_sable_v1 import BacASableV1

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--journal", required=True)
    p.add_argument("--experience", required=False)
    p.add_argument("--out", required=False)
    return p

def main() -> int:
    args = _parser().parse_args()
    
    # Résolution des chemins
    racine = Path(__file__).resolve().parents[4]
    bac = BacASableV1.charger_depuis_id(
        racine_projet=racine,
        experience_id=args.experience
    ) if args.experience else None
    
    journal_path = Path(args.journal)
    if bac and not journal_path.is_absolute():
        journal_path = bac.resoudre_chemin(journal_path)
    
    # Calcul des statistiques
    stats = _calculer_stats(journal_path)
    
    # Rapport
    rapport = {
        "journal": str(journal_path),
        "resultats": stats
    }
    
    # Sortie
    texte = json.dumps(rapport, indent=2, ensure_ascii=False)
    print(texte)
    
    if bac:
        out_path = bac.paths.diagnostics_dir / f"{Path(__file__).stem}__{journal_path.stem}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(texte + "\n")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### Checklist

- [ ] Question précise dans la docstring
- [ ] Arguments standardisés (journal, experience, out)
- [ ] Résolution des chemins via bac à sable
- [ ] Sortie JSON structurée
- [ ] Écriture dans artefacts/diagnostics/
- [ ] Tests avec données réelles
- [ ] Documentation des métriques

---

## Exemples de Questions → Diagnostics

| Question | Diagnostic à utiliser |
|----------|---------------------|
| L'agent évite-t-il les murs ? | diagnostic_mur_devant_v1 |
| Le serpent se mord-il ? | diagnostic_collision_soi_devant_v1 |
| Le modèle est-il précis ? | diagnostic_utilite_v1 |
| Le futur est-il prévisible ? | diagnostic_pas_unique_v1 |
| Les terminaisons sont-elles bien modélisées ? | diagnostic_termination_binning_v1 |
| L'observateur fonctionne-t-il ? | diagnostic_observateur_croissance_v1 |
| Le registre est-il valide ? | diagnostic_epistemique_smoke_v1 |

---

## Pièges à Éviter

### 1. Diagnostic sans Question

❌ **Mauvais :**
```python
def diagnostic_general():
    # Calculer toutes les métriques possibles
    return {
        "stat1": ...,
        "stat2": ...,
        # ... 100 stats
    }
```

✅ **Bon :**
```python
def diagnostic_mur_devant():
    """Question : Que se passe-t-il quand action vers mur ?"""
    return {
        "nb_action_vers_mur": ...,
        "ratio_termine": ...
    }
```

### 2. Ignorer les Cas Limites

❌ **Mauvais :**
```python
ratio = confirmations / support  # Crash si support == 0 !
```

✅ **Bon :**
```python
ratio = confirmations / support if support > 0 else 0.0
```

### 3. Pas de Contexte

❌ **Mauvais :**
```json
{"ratio_termine": 0.8}
```

✅ **Bon :**
```json
{
  "ratio_termine": 0.8,
  "support": 150,
  "journal": "episodes_v2.jsonl",
  "champ_latent": "signaux_hash"
}
```

### 4. Interprétation Prématurée

❌ **Mauvais :**
```json
{
  "resultats": {...},
  "conclusion": "L'agent est mauvais"  // Opinion !
}
```

✅ **Bon :**
```json
{
  "resultats": {...},
  "note": "ratio_termine=1.0 indique une règle déterministe"
}
```

---

## Conclusion

**SAI-A105** est l'activité de **questionnement scientifique**.

Elle transforme :
- Des questions de recherche floues
- En diagnostics précis et reproductibles
- Qui produisent des métriques interprétables
- Pour guider les décisions d'expérimentation

Les diagnostics sont :
- **Ciblés** : une question = un diagnostic
- **Reproductibles** : même input → même output
- **Automatisables** : intégrables dans un pipeline
- **Interprétables** : résultats compréhensibles par humain

C'est le pont entre :
- **Observation** (SAI-A102 : on a des données)
- **Compréhension** (SAI-A106 : on formule des hypothèses)

Sans SAI-A105, on navigue à l'aveugle. Avec, on peut :
- Valider les hypothèses quantitativement
- Comparer des agents objectivement
- Détecter des problèmes tôt
- Décider quand passer à l'étape suivante

Les diagnostics sont la **méthode scientifique** appliquée à l'apprentissage automatique.
