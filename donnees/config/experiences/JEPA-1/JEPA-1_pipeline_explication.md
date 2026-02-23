
# JEPA-1 — Déroulement complet du pipeline

_Date de génération : 2026-02-22 19:24_

---

## 1️⃣ Phase de Collecte — Agent spécialisé "Fourmi"

### Objectif
Produire un journal riche d'observations couvrant l'arène.

### Fichiers produits

- `journal_episodes_fourmi.jsonl`
- `journal_episodes_fourmi.enrichi.jsonl`
- `paires_capteurs.pt`

### Exemple (journal enrichi)

```json
{
  "tick": 42,
  "capteurs_compact": "...base64...",
  "action": "observer_gauche",
  "agent_id": "fourmi",
  "role_agent": "collecteur",
  "objectif": "couverture_observations"
}
```

### Interprétation

La fourmi n’est pas un agent intelligent final.
Elle est un **instrument de génération de données**.

---

## 2️⃣ Extraction des paires capteurs

Transformation des observations en dataset supervisé :

```
capteurs(t)  →  capteurs(t+1)
```

### Artefact

`paires_capteurs.pt`

```python
x: torch.Size([4969, 560])
y: torch.Size([4969, 560])
```

Chaque ligne représente une transition observée.

---

## 3️⃣ Entraînement de l’hypothèse neuronale

### Hypothèse

> Je peux prédire capteurs(t+1) à partir de capteurs(t).

### Résultat (extrait console)

```
[epoch 1/5] mse=0.135261
[epoch 5/5] mse=0.001721
```

### Artefacts produits

- `agent_personne.poids.pt`
- `agent_personne.json`
- `rapport_entrainement.json`

Extrait rapport :

```json
{
  "epochs": 5,
  "mse_par_epoch": [
    0.135261,
    0.033732,
    0.005596,
    0.002196,
    0.001721
  ]
}
```

---

## 4️⃣ Mise à l’épreuve (SAI-A108)

### Calcul de la surprise

```
surprise = MSE(prediction, observation)
```

### Gate calibré

```json
{
  "mode": "quantile",
  "quantile": 0.9,
  "seuil_connu": 0.00265217
}
```

### Exemple journal_agent.jsonl

```json
{
  "idx": 153,
  "mode": "connu_exploiter",
  "surprise": 0.00173,
  "seuil_connu": 0.00265,
  "action": "avant"
}
```

```json
{
  "idx": 4801,
  "mode": "inconnu_explorer",
  "surprise": 0.00291,
  "seuil_connu": 0.00265,
  "action": "observer_droite"
}
```

---

## 5️⃣ Registre épistémique

`registre_epistemique.json`

```json
{
  "gate": {
    "stats_surprise": {
      "mean": 0.00165,
      "std": 0.00050,
      "quantiles": {
        "p50": 0.00167,
        "p90": 0.00265,
        "p99": 0.00291
      }
    },
    "effet": {
      "ratio_connu": 0.90,
      "ratio_inconnu": 0.10
    }
  }
}
```

### Interprétation

Le système distingue :
- 90% situations connues
- 10% situations surprenantes

---

# 🧠 Synthèse du Pipeline

```
Fourmi (collecte)
        ↓
Journal observations
        ↓
Extraction paires (t → t+1)
        ↓
Entraînement hypothèse neuronale
        ↓
Calcul surprise
        ↓
Gate (connu / inconnu)
        ↓
Action (exploiter / explorer)
        ↓
Registre épistémique
```

---

# 🎯 État actuel

✔ Hypothèse symbolique instanciée neuronale  
✔ Gate mesuré objectivement  
✔ Registre traçable  
✔ Séparation collecteur / agent-personne  

Nous disposons maintenant d’un **pipeline épistémique complet minimal**.

