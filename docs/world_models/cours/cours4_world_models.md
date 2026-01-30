# Cours 4 — World Models : prédire, imaginer, décider

> **Objectif du cours**  
> Comprendre ce qu’est réellement un *world model* en pratique,  
> sans deep learning,  
> par l’expérience, la trace, l’erreur et l’incertitude.

Ce cours s’appuie sur l’environnement **Snake**, instrumenté pour permettre
l’apprentissage, l’évaluation et l’exploitation d’un **modèle du monde interne**.

---

## 1. Rappel conceptuel

Un *world model* n’est pas :
- un moteur de jeu,
- une reproduction exacte du monde réel,
- un oracle omniscient.

Un *world model* est :
> un **modèle interne appris** qui permet de **prédire des conséquences**
> sans interroger directement le monde réel.

Formellement :
```
(observation_t) → encodage → état latent z_t
(z_t, action_t) → modèle du monde → distribution(z_{t+1})
```

---

## 2. Architecture expérimentale (ce que nous avons)

### 2.1 Monde réel
- Arènes YAML (`donnees/config/arenes/*.yml`)
- Règles implicites : murs, nourriture, score, terminaison
- Moteur déterministe

### 2.2 Agent
- Actions discrètes
- Ne connaît pas les règles
- Ne voit que des observations

### 2.3 Spectateur (observer)
- Calcule descripteurs d’état
- Écrit un journal temporel (`jsonl`)
- Produit déjà :
  - statistiques globales
  - checksum d’observation
  - erreur de prédiction
  - détection de rupture

### 2.4 Replay
- Permet de rejouer exactement une expérience
- Condition nécessaire aux world models

> **Axiome clé**  
> Le monde existe indépendamment de l’agent.  
> L’agent n’accède qu’à des signaux partiels.

---

## 3. Le modèle du monde tabulaire (World Model v1)

### 3.1 Principe

Nous utilisons un **modèle tabulaire empirique** :

```
(z_t, action_t) → distribution(z_{t+1})
```

Il apprend par comptage à partir d’un journal d’épisodes.

Chaque prédiction fournit :
- état suivant le plus probable
- distribution complète
- support (nombre d’observations)
- confiance
- entropie (incertitude)

---

## 4. Entraîner un world model depuis un journal

### 4.1 Journal requis
Un fichier `episodes.jsonl` contenant :
- capteurs compactés
- actions
- états successifs
- (optionnel) champ latent déjà calculé

### 4.2 Commande d’évaluation (latent = checksum)

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1   --journal artefacts/episodes.jsonl   --champ-latent checksum   --split 0.8   --sortie artefacts/eval_checksum.jsonl
```

### 4.3 Interprétation attendue

| Indicateur | Attendu |
|-----------|--------|
| Couverture | Élevée |
| Exactitude conditionnelle | Très élevée |
| Entropie moyenne | Proche de 0 |

**Conclusion intermédiaire**  
Un état latent trop fin (checksum) rend le monde interne quasi déterministe.

---

## 5. Changer de représentation : faire émerger l’incertitude

### 5.1 Principe
Un world model devient intéressant **quand l’incertitude apparaît**.

Pour cela, on compresse l’observation :
- soit par un encodage discret simple,
- soit par un encodage appris (cours 3).

### 5.2 Journal recodé avec `latent_id`

Le journal contient désormais :
```
evt["latent_id"]
```

### 5.3 Évaluation sur latent appris

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1   --journal artefacts/episodes_latent_appris.jsonl   --champ-latent latent_id   --split 0.8   --sortie artefacts/eval_latent_id.jsonl
```

### 5.4 Résultat attendu

| Indicateur | Évolution |
|-----------|-----------|
| Couverture | Toujours élevée |
| Exactitude conditionnelle | Diminue |
| Entropie | Augmente |

> **Message clé**  
> L’incertitude n’est pas une erreur :  
> elle émerge quand on regroupe des états.

---

## 6. Boucle imaginaire : simuler sans le monde réel

### 6.1 Simulation interne

Le simulateur interne permet :
```
(z_t, action_t) → z_{t+1} simulé
```

sans appeler le moteur réel.

Il :
- échantillonne dans la distribution
- signale les transitions inconnues

### 6.2 Diagnostic : prédiction non unique

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_pas_unique_v1   --journal artefacts/episodes_latent_appris.jsonl
```

**Interprétation**  
Plusieurs futurs plausibles peuvent exister pour un même état latent.

---

## 7. Prédire à plusieurs pas (rollout interne)

Un world model n’est utile que s’il peut simuler **au-delà d’un pas**.

Principe :
1. partir d’un état latent réel `z_t`
2. simuler k pas via le modèle interne
3. comparer avec la trajectoire réelle

Effet attendu :
- l’erreur augmente avec l’horizon
- l’incertitude s’accumule

---

## 8. Décider avec le monde interne (MPC)

### 8.1 Planification par imagination

Le module de planification :
- simule plusieurs futurs
- évalue récompense et terminaison
- choisit l’action qui maximise l’espérance

### 8.2 Message pédagogique central

> Agir dans le monde imaginé  
> est moins coûteux que d’explorer dans le monde réel.

---

## 9. Incertitude et exploration

L’incertitude sert à :
- détecter l’inconnu
- éviter les actions irréversibles
- forcer l’exploration ciblée

Un agent peut :
- **savoir qu’il ne sait pas**
- adapter son comportement en conséquence

---

## 10. Ce que ce cours démontre

### Ce qui est prouvé expérimentalement
- un world model peut être appris sans deep learning
- l’erreur prédictive est mesurable
- l’incertitude émerge d’une représentation compressée
- la simulation interne est exploitable pour décider

### Ce que l’étudiant doit retenir
- un world model est un objet scientifique testable
- la représentation est plus importante que l’algorithme
- l’incertitude est une information, pas un défaut

---

## 11. Transition vers la suite

Ce cours ouvre naturellement vers :
- exploration guidée par l’incertitude
- modèles de récompense plus riches
- apprentissage actif du monde

> **Fin du Cours 4**  
> À partir d’ici, l’agent n’est plus réactif :  
> il commence à imaginer.
