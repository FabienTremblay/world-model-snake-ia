# World Models — Cours 2  
## État latent invariant au bruit (discret_v1)

Ce cours prolonge directement le **Cours 1**.  
Le monde, les agents, les métriques et les commandes sont identiques.  
**Une seule chose change : la définition de l’état latent.**

---

## Rappel du Cours 1 (point de départ)

### Choix techniques
- état latent : `checksum(capteurs)`
- modèle du monde : tabulaire `(z, action) → z_suivant`
- apprentissage : offline (split 70/30)
- agent : curiosité tabulaire

### Résultat clé (Cours 1)
- couverture ≈ **37 %**
- exactitude conditionnelle = **1.0**
- entropie = **0.0**
- support moyen ≈ **1.2**

### Interprétation
Le modèle :
- mémorise parfaitement ce qu’il connaît
- généralise très peu
- est extrêmement sensible au bruit

➡️ **Motivation du Cours 2 :** améliorer la couverture sans deep learning.

---

## Hypothèse du Cours 2

> Si l’état latent est rendu plus **invariant au bruit**,  
> alors les mêmes situations du monde retomberont plus souvent
> dans un même état latent, augmentant la couverture.

---

## Changement introduit (unique)

### Nouvel état latent : `discret_v1`

L’état latent n’est plus un hash exact des capteurs, mais une **compression discrète** :
- binning des intensités
- binning des teintes
- regroupement spatial grossier
- hash stable du résumé

Propriété recherchée :
- petites variations (bruit) → **même état latent**
- situations structurellement proches → regroupées

Aucun autre changement :
- mêmes agents
- même moteur
- mêmes métriques
- même protocole d’évaluation

---

## Commandes exécutées

### Génération des données
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --arene demo_v0 \
  --episodes 200 \
  --max-ticks 2000 \
  --agent curiosite_tabulaire \
  --latent discret_v1 \
  --epsilon 0.05 \
  --seed 123 \
  --truncate \
  --journal artefacts/episodes_latent_discret.jsonl \
  --metrics artefacts/exploration_metrics_latent_discret.jsonl
```

### Évaluation offline
```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes_latent_discret.jsonl \
  --mode split \
  --ratio-train 0.7
```

---

## Résultats observés (Cours 2)

### Statistiques du modèle (après train)
- nombre de clés `(z, action)` : **441**
- support moyen : **5.89**
- support max : **127**

➡️ **Réduction massive de l’espace d’états** par rapport au Cours 1 (~3000 clés).

---

### Performances en test
- couverture : **95.3 %**
- exactitude conditionnelle : **1.0**
- entropie : **0.0**
- transitions prédites : **1061 / 1113**

➡️ Le modèle peut presque toujours prédire quelque chose.

---

## Comparaison Cours 1 vs Cours 2

| Indicateur | Cours 1 (checksum) | Cours 2 (discret_v1) |
|-----------|-------------------|----------------------|
| nb clés | ~3000 | **441** |
| support moyen | ~1.2 | **5.9** |
| couverture | ~0.38 | **0.95** |
| exactitude conditionnelle | 1.0 | 1.0 |
| entropie | 0.0 | 0.0 |

---

## Interprétation conceptuelle

### Ce qui s’est produit
- plusieurs états distincts au Cours 1 sont désormais regroupés
- le modèle revisite les mêmes clés beaucoup plus souvent
- l’agent « reconnaît » plus rapidement les situations

### Ce que cela montre
- la **représentation de l’état** est le facteur dominant
- l’apprentissage n’était pas le problème au Cours 1
- la généralisation dépend avant tout de l’invariance du latent

---

## Limite observée

Malgré la compression :
- exactitude = 1.0
- entropie = 0.0

➡️ Le monde reste **déterministe** à cette résolution.
Aucune ambiguïté n’est encore introduite.

---

## Conclusion du Cours 2

> En changeant uniquement l’état latent,  
> nous avons transformé un world model qui connaissait peu de choses
> en un world model qui reconnaît presque toutes les situations,
> sans sacrifier la précision.

Ce résultat justifie :
- l’apprentissage de représentations (Cours 3)
- l’introduction de bruit ou de partial observability
- l’étude de l’incertitude réelle (entropie > 0)

---

## Prochaine étape

**Cours 3 — État latent appris**
- encodeur (ML)
- robustesse au bruit non linéaire
- entropie non nulle
- préparation à la planification et à l’imagination
