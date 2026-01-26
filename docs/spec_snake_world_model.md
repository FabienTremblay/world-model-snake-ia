# Spécification – Snake à règles découvertes par l’agent

## 1. Objectif
Implémenter une version de Snake où l’agent **ne connaît pas les règles à l’avance** et doit les découvrir par interaction avec le monde.
Le jeu comporte deux modes :
- **Mode entraînement** : apprentissage des règles et des effets des objets.
- **Mode compétition** : exploitation des règles apprises pour maximiser le score.

Les objets du monde (mur, nourriture, warp, porte) sont **représentés par des attributs visuels** (ex. couleur), sans sémantique explicite fournie à l’agent.

---

## 2. Représentation du monde

### 2.1 Observation (entrée agent)
Grille 2D de cellules avec attributs visuels :

```
(x,y) -> {
  couleur: RGB | ID,
  animation: optionnel,
  forme: optionnel
}
```

Aucune étiquette explicite de type (mur, warp, etc.) n’est transmise à l’agent.

---

## 3. État et règles

### 3.1 État observable (s)
- Position du serpent (liste ordonnée de cellules)
- Direction actuelle
- Carte des attributs (features) des cellules
- État de la porte (ouverte/fermée via attribut visuel)

### 3.2 Règles latentes (θ)
Les règles sont fixes pendant un épisode mais inconnues de l’agent :

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

- +1 (ou +10) : ingestion nourriture
- -1 (ou -10) : collision mortelle
- -ε (ex. -0.01) par pas (optionnel)
- Bonus fin si porte atteinte en mode entraînement

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

## 7. Modes de fonctionnement

### 7.1 Mode entraînement
Objectif : apprendre θ.

Politique :

```
a = argmax ( E[score] + β × E[gain_information] )
```

Actions informatives attendues :
- tester collision avec objets
- entrer dans warp
- atteindre porte

### 7.2 Mode compétition
Objectif : maximiser le score.

- Utiliser θ* = argmax b(θ)
- Plus d’exploration volontaire

---

## 8. Porte de fin

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

Fin du document.

