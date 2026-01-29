# World Models — Cours 3  
## État latent appris (contrastif) : faire émerger l’incertitude

L’objectif du cours 3 est de comprendre **comment un monde interne peut devenir incertain**, sans injecter explicitement de probabilités, simplement par la manière dont on **représente et apprend l’état du monde**.

Ce cours s’appuie sur une expérience complète :
- un environnement simulé,
- un journal d’interactions,
- un modèle du monde discret,
- et une évaluation mesurable.

Contrairement aux cours précédents, le monde interne n’est plus donné : **il est appris**.

Ce cours prolonge ainsi les **Cours 1 et 2** en changeant **uniquement** la manière de produire l’état latent `z`.

- Cours 1 : `z = checksum(capteurs)` (trop discriminant)
- Cours 2 : `z = discret_v1(capteurs)` (invariant au bruit, défini à la main)
- **Cours 3 : `z = Q(E(capteurs))` (latent appris, puis quantifié)**

L’objectif du Cours 3 n’est pas d’obtenir un “meilleur score” au jeu, mais de faire apparaître un phénomène central des world models :
> l’**incertitude** (entropie non nulle) qui émerge quand l’observation est partielle et que la représentation regroupe des situations.

---

## 1. Ce que les Cours 1 et 2 ont prouvé

### Cours 1 (checksum)
- couverture faible
- exactitude conditionnelle = 1.0 quand connu
- entropie = 0.0

➡️ le modèle mémorise parfaitement mais reconnaît peu.

### Cours 2 (discret_v1)
- couverture très élevée (≈ 95 %)
- exactitude conditionnelle = 1.0
- entropie = 0.0

➡️ la généralisation vient de la représentation, mais l’incertitude n’apparaît pas : le monde reste perçu comme déterministe.

**Conclusion intermédiaire :**
> tant que l’état latent est défini manuellement, il impose ses invariances et peut masquer l’incertitude.

---

## 2. Question fondatrice du Cours 3

> Comment faire apparaître l’incertitude **sans la forcer artificiellement** ?

On ne veut pas :
- injecter du bruit “pour tricher”
- dégrader volontairement le modèle

On veut :
- apprendre une représentation qui regroupe automatiquement les situations “équivalentes” du point de vue de la dynamique,
- ce qui fait apparaître naturellement des futurs multiples possibles pour un même latent.

---

## 3. Principe : encodeur contrastif + prédiction du futur

On introduit deux modules appris :

- `E(obs) -> z` : **encodeur** qui transforme les capteurs en vecteur latent `z` (dimension `d`)
- `F(z, a) -> y` : **prédicteur** qui produit un embedding du futur attendu après l’action `a`

Pour une transition observée `(obs_t, a_t, obs_{t+1})` :

- `z_t = E(obs_t)`
- `z_{t+1} = E(obs_{t+1})`
- `y_t = F(z_t, a_t)`

On veut que `y_t` soit **proche** de `z_{t+1}`, et **loin** des autres `z_{t+1}` du batch.

---

## 4. Positifs / négatifs (in-batch)

- **positif** : le vrai futur `z_{t+1}` de la transition
- **négatifs** : les `z_{t+1}` des autres transitions du batch

Ce choix est minimal, efficace et pédagogique.

---

## 5. Perte contrastive (InfoNCE)

Pour chaque transition du batch :

- similarité `sim(y_t, z_{t+1})` = cosinus (par défaut)
- température `τ` (par défaut 0.2)

On minimise :

\[
\mathcal{L} = -\log \frac{\exp(sim(y_t, z_{t+1})/\tau)}
{\sum_{k=1}^{B}\exp(sim(y_t, z_{t+1}^{(k)})/\tau)}
\]

**Interprétation :**
> apprendre un latent où “ce qui compte” est ce qui aide à prédire le futur, pas ce qui ressemble visuellement.

---

## 6. Quantification Q2 : k-means (choix fixé)

Le modèle tabulaire exige un identifiant discret. On adopte :

- `Q(z) = cluster_id` via **k-means**
- `k = 512` (par défaut)

Donc l’état latent final est :

\[
z^{disc}_t = Q(E(obs_t)) \in \{0, \dots, k-1\}
\]

---

## 7. Pourquoi l’entropie peut apparaître (phénomène attendu)

Avec un encodeur appris + quantification, il devient possible que :

- plusieurs états réels différents (non distinguables par les capteurs) soient projetés vers le même cluster `z^{disc}`,
- mais que leurs futurs diffèrent,

donc le tabulaire observe :

- même clé `(z^{disc}, a)` → plusieurs successeurs possibles

➡️ **entropie > 0** (incertitude irréductible), même si le monde “réel” est déterministe.

C’est la signature attendue d’un world model dans un monde **partiellement observable**.

---

## 8. protocole expérimental

Le protocole est volontairement conservateur :  
on ne modifie **ni le simulateur**, **ni l’évaluateur tabulaire**, uniquement la manière de produire l’état latent.

### 8.1 journal d’expérience

On part d’un journal existant :

```
artefacts/episodes.jsonl
```

Il contient des transitions `(obs_t, action_t, obs_{t+1})` issues d’un agent simple.

---

### 8.2 apprentissage de l’encodeur contrastif

Un encodeur contrastif est entraîné **offline** à partir du journal brut.

```
PYTHONPATH=services python -m agent_service.app.modele_monde.apprendre_encodeur_contrastif_v1 \
  --episodes artefacts/episodes.jsonl \
  --out-dir artefacts/out_cours3
```

Paramètres figés pour le cours :
- dimension latente `d = 16`
- batch `= 256`
- epochs `= 10`
- température `τ = 0.2`

L’encodeur appris est sauvegardé dans :

```
artefacts/out_cours3/encodeur_contrastif_v1.npz
```

---

### 8.3 recodage du journal en latent discret

Chaque observation est encodée puis quantifiée par **k-means (k = 512)** :

```
PYTHONPATH=services python -m agent_service.app.modele_monde.recoder_journal_latent_v1 \
  --episodes artefacts/episodes.jsonl \
  --encodeur artefacts/out_cours3/encodeur_contrastif_v1.npz \
  --out artefacts/episodes_latent_appris.jsonl
```

Chaque événement contient désormais un champ :

```
latent_id ∈ {0, …, 511}
```

---

### 8.4 évaluation tabulaire

Le modèle tabulaire est évalué **sans modification**, comme dans les cours précédents :

```
PYTHONPATH=services python -m agent_service.app.modele_monde.evaluer_tabulaire_v1 \
  --journal artefacts/episodes_latent_appris.jsonl \
  --champ-latent latent_id \
  --out artefacts/modele_monde_eval_tabulaire_latent_v1.jsonl
```

---

## 9. résultats expérimentaux

### 9.1 première tentative — représentation trop pauvre

Avec une représentation fondée sur un **histogramme global** des capteurs (24 dimensions) :

- identifiants latents distincts : 3  
- états tabulaires effectifs : 8  
- exactitude conditionnelle ≈ 0.999  
- entropie moyenne ≈ 0.01  

Le monde interne s’effondre en un quasi-automate déterministe.

**Conclusion intermédiaire** :  
une représentation trop pauvre impose artificiellement un monde déterministe.

---

### 9.2 correction minimale — structure spatiale

Une seule modification est apportée à l’observation :

- découpage de l’image en **4 quadrants (2×2)**,
- histogramme (24 bins) par quadrant,
- concaténation → **96 dimensions**.

Le reste du pipeline est strictement identique.

---

### 9.3 résultat après correction — émergence de l’incertitude

Avec cette représentation légèrement enrichie :

- identifiants latents distincts ≈ 44  
- états tabulaires effectifs : 136  
- couverture ≈ 0.997  
- exactitude conditionnelle ≈ 0.84  
- entropie moyenne ≈ 0.64 (max > 2)

Pour un même état latent et une même action, plusieurs futurs plausibles apparaissent.

L’incertitude **émerge**.

---

## 10. interprétation

Ces résultats montrent que :

- l’incertitude n’est pas ajoutée artificiellement,
- elle dépend directement de la représentation,
- le paramètre `k = 512` fournit une capacité maximale, non une obligation.

Le world model apprend une **compression compatible avec l’expérience**, pas une vérité cachée.

---

## 11. message clé du cours 3

Le cours 3 ne montre pas comment injecter de l’incertitude.

Il montre :
- quand elle apparaît,
- pourquoi elle apparaît,
- et de quoi elle dépend.

- représentation trop grossière → monde déterministe  
- représentation structurée → monde ambigu  

L’incertitude est une **propriété émergente du modèle du monde**.

---

## 12. conclusion

À l’issue de ce cours, l’étudiant a vu :

- comment apprendre un état latent sans supervision,
- comment diagnostiquer un effondrement de représentation,
- comment faire émerger une incertitude exploitable,
- comment relier représentation, dynamique et prédiction.

Le monde interne n’est plus implicite.  
Il est **observable, mesurable et critiquable**.

Le cours 3 est maintenant **conceptuellement et expérimentalement clos**.
