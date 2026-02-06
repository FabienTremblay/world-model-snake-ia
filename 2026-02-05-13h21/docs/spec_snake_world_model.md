# Spécification – Snake à règles découvertes par l’agent

## 1. Objectif
Implémenter une version de Snake où l’agent **ne connaît pas les règles à l’avance** et doit les découvrir par interaction avec le monde.
Le jeu comporte deux **régimes d’épisode** (terme à privilégier plutôt que « mode ») :
- **Régime entraînement** : apprentissage des règles et des effets des objets.
- **Régime compétition** : exploitation des règles apprises pour maximiser le score.

Les objets du monde (mur, nourriture, warp, porte) sont **représentés par des attributs visuels** (ex. couleur), sans sémantique explicite fournie à l’agent.

---

## 2. Représentation du monde

### 2.1 Observation (entrée agent)
Signal perceptif : grille 2D de cellules avec attributs visuels.
Ce signal est la seule entrée de l’agent.
Note : un rendu ASCII peut exister **uniquement** en mode développement (debug) et ne doit pas être consommé par l’agent.

```
(x,y) -> {
  couleur: RGB | ID,
  animation: optionnel,
  forme: optionnel
}
```
Ce signal ne contient aucune information sémantique explicite.
Toute interprétation (mur, nourriture, porte, etc.) est inférée par l’agent.

Aucune étiquette explicite de type (mur, warp, etc.) n’est transmise à l’agent.

---

## 3. État et règles

### 3.1 État observable (s)
- Position du serpent (liste ordonnée de cellules)
- Direction actuelle
- Carte des attributs (features) des cellules
- État de la porte (ouverte/fermée via attribut visuel)

### 3.2 Règles latentes (θ)
Les règles sont fixes pendant un épisode, mais peuvent changer entre épisodes.
Elles sont inconnues de l’agent.

```
θ = {
  mur: { effet: mort | blocage },
  warp: { type: fixe | aléatoire, mapping: positions },
  nourriture: { croissance: +1 | +k, score: valeur },
  porte: { condition_ouverture },
}
```

### 3.3 État interne de l’agent
L’agent maintient une croyance probabiliste :

```
b(θ) = P(θ | historique)
```

## 3.4 Définition d’arène (configuration)
Les règles et paramètres d’un épisode devraient être décrits par une **définition d’arène** (ex. fichier YAML),
afin de rendre explicites et versionnables :
- dimensions de la grille, vitesse, seed
- catalogue d’objets et leurs attributs visuels (mur, nourriture, warp, porte)
- règles latentes activées et leurs paramètres (θ), incluant **porte** et **conditions d’ouverture**
- récompenses (ε par pas, bonus de fin, valeurs de score)
- bruit capteurs (niveau, distribution)
- critères de fin d’épisode

Cette définition d’arène sert d’entrée au simulateur et au runner, et permet de reproduire exactement un épisode.
---

## 4. Dynamique

### 4.1 Monde réel

```
(s_t, θ, a_t) -> (s_{t+1}, θ)
```

### 4.2 Monde interne (agent)

```
(s_t, b_t, a_t) -> (s_{t+1}, b_{t+1})
```

Mise à jour de la croyance :

```
b_{t+1}(θ) ∝ b_t(θ) × P(s_{t+1} | s_t, a_t, θ)
```

---

## 5. Récompense

- Bonus de fin si la porte est atteinte (selon l’arène / le régime d’épisode)

---

## 6. Incertitude

### 6.1 Incertitude épistémique
Manque de connaissance sur :
- effet des murs
- effet des warps
- condition d’ouverture de la porte

Réduite par exploration.

### 6.2 Incertitude aléatoire
Liée aux tirages stochastiques :
- apparition nourriture
- warp aléatoire (si défini ainsi)

---

## 7. Régimes d’épisode

### 7.1 Régime entraînement
Objectif : apprendre θ (ou, à défaut, réduire l’incertitude sur les règles).

Politique :

```
a = argmax ( E[score] + β × E[gain_information] )
```

Actions informatives attendues :
- tester collision avec objets
- entrer dans warp
- atteindre porte

### 7.2 Régime compétition
Objectif : maximiser le score (exploitation).

- Utiliser θ* = argmax b(θ)
- Plus d’exploration volontaire

---

## 8. Porte de fin
**Priorité** : compléter le jeu de base avec la porte de fin et ses conditions d’ouverture.
Objet avec attribut visuel distinct.

Règle latente :

```
open = f(longueur_serpent, nourriture_mangée, temps, warp_passé, etc.)
```

Quand ouverte :
- entrer dans la porte termine l’épisode
- récompense de fin possible

---

## 9. Implémentation recommandée

### 9.1 Version simple (discrète)
- Espace θ discret (quelques hypothèses)
- Mise à jour par élimination pondérée

### 9.2 Version avancée
- Modèle appris f(s,a)->s'
- Ensemble de modèles = estimation incertitude

---

## 10. Critères de réussite

- L’agent identifie correctement : mur / warp / nourriture / porte
- L’agent réduit son incertitude en mode entraînement
- L’agent augmente son score en mode compétition

---

## 11. Principes de design

- 1 attribut visuel = 1 type d’objet (au départ)
- épisodes courts
- règles stables par épisode
- curriculum progressif

---

## 12. Résumé conceptuel

Le système implémente un agent tel que :

```
(État, croyance_sur_règles, action)
   -> (État, croyance_sur_règles)
```

Les règles sont **inférées**, pas codées côté agent.

---
## 13. Replay et traçabilité

### 13.1 Outils d’observation (spectateur)
Un **agent spectateur** peut être utilisé pour calculer des métriques sur le signal et sur la trace
(ex. checksum, variance, détection de ruptures), **sans agir** et sans influencer le monde.
Il sert à la validation, au debugging et à l’analyse, pas à la décision.

Chaque interaction produit une trace journalisée (tick par tick) contenant
le signal perceptif et les métadonnées d’exécution.

Ces traces peuvent être rejouées afin de :
- comparer agent et humain à signal égal
- analyser les erreurs de prédiction
- mesurer la stabilité des inférences sur un même signal

Fin du document.

