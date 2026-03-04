# SAI-A104 : Inférer les Épisodes (Recodage et Enrichissement)

## Vue d'ensemble

L'activité **SAI-A104** est le processus de **transformation et enrichissement** du journal d'épisodes brut en un journal **exploitable** pour l'apprentissage. C'est l'étape où les données deviennent des **représentations latentes** utilisables par les modèles du monde.

### Position dans le flux de travail

```
SAI-A102                SAI-A104                SAI-A105/A106
Générer des       →     Inférer les       →     Analyser /
épisodes                épisodes                Hypothèses
(Journal brut)          (Journal enrichi)       (Diagnostics)
```

### Objectif

Transformer le journal brut en **états latents exploitables** :
- **Encoder** les observations en représentations compactes
- **Extraire** les signaux pertinents (delta_score, collision, etc.)
- **Augmenter** le journal avec ces nouvelles informations
- Permettre l'apprentissage de modèles du monde tabulaires

---

## Principe Fondamental : De l'Observation à l'État Latent

### Le Problème de la Représentation

Le journal brut contient des **observations visuelles** (grilles de pixels) :

```json
{
  "tick": 42,
  "capteurs_compact": "base64_encoded_grid...",
  "largeur": 30,
  "hauteur": 12,
  "score": 15,
  "action": "droite"
}
```

**Problème :** On ne peut pas utiliser directement ces pixels pour :
- Créer un modèle tabulaire (espace d'états trop grand)
- Généraliser (deux observations similaires = deux états différents)
- Planifier (pas de notion de "similarité")

**Solution :** Créer un **état latent** `z` qui :
- Compresse l'information
- Regroupe les situations similaires
- Reste discriminant pour les différences importantes

### Métaphore

```
Observation brute = Photo haute résolution (millions de pixels)
État latent      = Résumé conceptuel (quelques attributs clés)

"Grille 30x12 avec pixels RGB" → "Mur devant, nourriture à droite, corps long"
```

---

## Les 3 Modes d'Encodage Latent

### 1. Checksum (Identité Parfaite)

**Principe :** Hash cryptographique des capteurs

**Formule :**
```python
z = checksum_rapide(capteurs)  # FNV-1a hash
```

**Caractéristiques :**
- **Totalement discriminant** : 2 observations identiques → même z
- **Trop précis** : 2 observations très similaires → z différents
- **Déterministe** : même observation → toujours même z

**Exemple :**
```
Observation A : Serpent en (5,3), nourriture en (8,4)
  → z = 3849571024

Observation B : Serpent en (5,3), nourriture en (8,5)  # 1 pixel de différence !
  → z = 2193847562  # Complètement différent
```

**Avantages :**
- Précision parfaite
- Pas d'ambiguïté

**Inconvénients :**
- Aucune généralisation
- Couverture très faible (< 30%)
- Inutilisable pour un modèle tabulaire

**Usage :** Baseline, validation, debugging

### 2. Discret v1 (Pooling Spatial)

**Principe :** Découpage en régions + binning des attributs

**Algorithme :**
```python
def latent_discret_v1(capteurs, grilles=4):
    # 1. Découper l'image en 4x4 régions
    # 2. Pour chaque région :
    #    - Teinte : 360° → 6 bins de 60°
    #    - Intensité : 0-255 → 4 bins de 64
    #    - Motif : 0-7 (conservé)
    # 3. Classe dominante par région (mode)
    # 4. Hash FNV-64 des 16 valeurs régionales
    return hash_value
```

**Caractéristiques :**
- **Invariant au bruit** : petites variations de teinte/intensité ignorées
- **Pooling spatial** : plusieurs pixels → une classe
- **Défini manuellement** : les bins sont choisis a priori

**Exemple :**
```
Région haut-gauche :
  Pixels majoritaires : teinte=120° (vert), intensité=180
  → Bins : teinte_bin=2, intens_bin=2, motif=1
  → Classe régionale = 2*32 + 2*8 + 1 = 81
```

**Avantages :**
- Excellente couverture (> 90%)
- Robuste au bruit
- Généralisation spatiale

**Inconvénients :**
- Bins définis manuellement (pas appris)
- Peut masquer des différences importantes
- Encore déterministe (entropie = 0)

**Usage :** Cours 2, modèles tabulaires basiques

### 3. Signaux Perçus Hash v1 (Voisinage de la Tête)

**Principe :** Encoder uniquement ce qui est **directement utile** pour décider

**Algorithme :**
```python
def latent_signaux_percus_hash_v1(capteurs):
    # 1. Trouver la tête (motif == 5)
    x, y = trouver_tete(capteurs)
    
    # 2. Lire les 4 cases adjacentes
    motif_haut    = capteurs[y-1][x].motif
    motif_bas     = capteurs[y+1][x].motif
    motif_gauche  = capteurs[y][x-1].motif
    motif_droite  = capteurs[y][x+1].motif
    
    # 3. Hash du tuple (tête, haut, bas, gauche, droite)
    return fnv_hash(motif_tete, motif_haut, motif_bas, motif_gauche, motif_droite)
```

**Signaux extraits :**
```python
{
  "motif_tete": 5,      # Toujours 5 (tête)
  "motif_haut": 0,      # 0=vide, 1=corps, 2=nourriture, 3=mur
  "motif_bas": 1,       # Corps en dessous
  "motif_gauche": 3,    # Mur à gauche
  "motif_droite": 2,    # Nourriture à droite
  "signaux_tuple": "5,0,1,3,2"
}
```

**Caractéristiques :**
- **Contexte local** : seulement le voisinage immédiat
- **Exploitable** : directement lié aux actions (haut/bas/gauche/droite)
- **Compactage agressif** : ignore tout le reste de la grille

**Exemple :**
```
Situation A : Serpent long, mur devant, nourriture loin
Situation B : Serpent court, mur devant, nourriture loin
  → Même latent si voisinage identique !
  → Généralisation : "mur devant" peu importe le contexte global
```

**Avantages :**
- Couverture élevée (> 85%)
- États répétés → généralisation
- Incertitude émerge (plusieurs futurs possibles)
- Directement interprétable

**Inconvénients :**
- Perd l'information globale
- Peut confondre des situations stratégiquement différentes

**Usage :** Cours 4, modèles exploitables, planification

### 4. Latent Appris (Encodeur Contrastif + K-means)

**Principe :** Apprendre la représentation qui maximise la prédiction du futur

**Pipeline :**
```
1. Entraîner un encodeur contrastif :
   E(obs_t) → z_t (vecteur dense)
   F(z_t, action) → y_t (prédiction du futur)
   Loss : y_t proche de z_{t+1}

2. Encoder tout le journal :
   obs → z (vecteurs de dimension d=64)

3. K-means clustering :
   z → cluster_id ∈ {0, ..., 511}

4. Journa augmenté :
   evt["latent_id"] = cluster_id
```

**Caractéristiques :**
- **Appris** : représentation optimisée pour prédire le futur
- **Non supervisé** : pas besoin de labels
- **Quantifié** : vecteurs continus → IDs discrets

**Avantages :**
- Représentation optimale pour la dynamique
- Incertitude naturelle (plusieurs obs → même cluster)
- Pas de biais manuel

**Inconvénients :**
- Complexe à entraîner
- Nécessite beaucoup de données
- Moins interprétable

**Usage :** Cours 3, recherche avancée

---

## Pipeline SAI-A104 Détaillé

### Étape 1 : Lecture du Journal Brut

**Entrée :**
```
donnees/config/experiences/cours4/artefacts/runs/2026-02-09_13h40/
  └── journal_episodes.jsonl
```

**Format d'un événement :**
```json
{
  "run_id": "1769627687674217456",
  "episode_id": 3,
  "tick": 42,
  "capteurs_compact": "eJzt1...",  // Base64 de la grille
  "largeur": 30,
  "hauteur": 12,
  "action": "droite",
  "score": 15,
  "longueur_serpent": 5,
  "termine": false,
  "raison_fin": null
}
```

### Étape 2 : Décodage des Capteurs

```python
from runner.app.replay import decoder_capteurs_b64

capteurs = decoder_capteurs_b64(
    evt["capteurs_compact"],
    largeur=evt["largeur"],
    hauteur=evt["hauteur"]
)
# → List[List[Pixel]]
# Pixel = (teinte, intensite, motif, clignote)
```

### Étape 3 : Encodage Latent

**Option A : Signaux Perçus Hash**

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.recoder_journal_signaux_hash_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --mode signaux_percus_hash_v1 \
  --champ signaux_hash \
  --experience cours4
```

**Option B : Latent Appris**

```bash
# 1. Entraîner l'encodeur (voir cours 3)
PYTHONPATH=services python -m agent_service.app.modele_monde.apprendre_encodeur_contrastif_v1 \
  --journal episodes.jsonl \
  --out encodeur_contrastif_v1.npz

# 2. Recoder le journal
PYTHONPATH=services python -m agent_service.app.modele_monde.recoder_journal_latent_v1 \
  --episodes journal_episodes.jsonl \
  --encodeur encodeur_contrastif_v1.npz \
  --k 512 \
  --experience cours4
```

### Étape 4 : Extraction de Signaux Supplémentaires

En plus du latent, on peut extraire :

**Signaux du monde :**
```python
from agent_service.app.signaux.signaux_monde_v1 import extraire_signaux_monde_v1

signaux = extraire_signaux_monde_v1(prev_evt, curr_evt)
# {
#   "delta_longueur": 1,
#   "delta_score": 10,
#   "termine": False,
#   "collision_mur": False
# }
```

**Signaux perçus (voisinage) :**
```python
from agent_service.app.modele_monde.latent_v1 import extraire_signaux_percus_voisinage_v1

signaux = extraire_signaux_percus_voisinage_v1(capteurs)
# {
#   "x": 15,
#   "y": 6,
#   "motif_tete": 5,
#   "motif_haut": 0,
#   "motif_bas": 1,
#   "motif_gauche": 3,
#   "motif_droite": 2,
#   "signaux_tuple": "5,0,1,3,2"
# }
```

### Étape 5 : Journal Augmenté

**Sortie :**
```
donnees/config/experiences/cours4/artefacts/datasets/
  └── journal_episodes_signauxhash.jsonl
```

**Format d'un événement enrichi :**
```json
{
  "run_id": "1769627687674217456",
  "episode_id": 3,
  "tick": 42,
  "capteurs_compact": "eJzt1...",
  "largeur": 30,
  "hauteur": 12,
  "action": "droite",
  "score": 15,
  "longueur_serpent": 5,
  "termine": false,
  "raison_fin": null,
  
  // NOUVEAUX CHAMPS AJOUTÉS PAR SAI-A104
  "signaux_hash": 2936432768,         // État latent
  "signaux_tuple": "5,0,1,3,2",       // Voisinage lisible
  "motif_haut": 0,
  "motif_bas": 1,
  "motif_gauche": 3,
  "motif_droite": 2
}
```

---

## Utilisation du Journal Augmenté

### En SAI-A105 (Diagnostics)

Le champ latent permet les diagnostics :

```python
# Diagnostic avec latent
diagnostic_termination_binning_v1 \
  --journal episodes_signauxhash.jsonl \
  --champ-latent signaux_hash
```

### En SAI-A106 (Hypothèses)

Les signaux perçus alimentent l'APK :

```python
if signaux["motif_haut"] == 3:  # Mur au-dessus
    if action == "haut":
        # Hypothèse : mur + action vers mur → collision
```

### En Entraînement (Modèles Tabulaires)

L'itérateur de transitions utilise le latent :

```python
from agent_service.app.modele_monde.entrainement_depuis_journal import iterer_transitions

for prev_evt, evt, z_prev, z, action in iterer_transitions(
    journal_path,
    champ_latent="signaux_hash"
):
    # z_prev, z = états latents
    # Utilisables directement pour l'apprentissage
    modele.apprendre_transition(z_prev, action, z)
```

---

## Comparaison des Modes

### Table Comparative

| Critère | Checksum | Discret v1 | Signaux Hash | Latent Appris |
|---------|----------|------------|--------------|---------------|
| **Couverture** | < 30% | > 90% | > 85% | > 80% |
| **Entropie** | 0.0 | 0.0 | > 0 | > 0 |
| **Exactitude** | 1.0 | 1.0 | 0.9-0.95 | 0.85-0.92 |
| **Interprétable** | Non | Oui | Très | Non |
| **Coût calcul** | Très faible | Faible | Faible | Élevé |
| **Données requises** | Aucune | Aucune | Aucune | Beaucoup |
| **Généralisation** | Nulle | Bonne | Excellente | Optimale |

### Évolution Pédagogique

```
Cours 1 : Checksum
  → Problème : pas de généralisation
  
Cours 2 : Discret v1
  → Progrès : généralisation
  → Problème : déterministe, bins manuels
  
Cours 3 : Latent Appris
  → Progrès : incertitude émerge
  → Problème : complexe, peu interprétable
  
Cours 4 : Signaux Perçus Hash
  → Compromis : simple, interprétable, efficace
```

---

## Commandes Pratiques

### Recoder avec Signaux Hash

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.recoder_journal_signaux_hash_v1 \
  --journal donnees/config/experiences/cours4/artefacts/runs/2026-02-09_13h40/journal_episodes.jsonl \
  --experience cours4 \
  --mode signaux_percus_hash_v1 \
  --champ signaux_hash \
  --ecrire-signaux-tuple
```

**Produit :**
```
donnees/config/experiences/cours4/artefacts/datasets/
  └── journal_episodes_signauxhash.jsonl
```

### Recoder avec Latent Appris

```bash
# 1. Entraîner
PYTHONPATH=services python -m agent_service.app.modele_monde.apprendre_encodeur_contrastif_v1 \
  --journal artefacts/episodes.jsonl \
  --out artefacts/out_cours3/encodeur_contrastif_v1.npz \
  --dim 64 \
  --epochs 10

# 2. Recoder
PYTHONPATH=services python -m agent_service.app.modele_monde.recoder_journal_latent_v1 \
  --episodes artefacts/episodes.jsonl \
  --encodeur artefacts/out_cours3/encodeur_contrastif_v1.npz \
  --k 512 \
  --out artefacts/episodes_latent_appris.jsonl
```

**Produit :**
```
artefacts/
  ├── episodes_latent_appris.jsonl
  ├── stats_kmeans_v1.json
  └── centroides_kmeans_v1.npy
```

### Recoder Delta Score (Simplification)

Pour certains diagnostics, on peut simplifier encore plus :

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.recoder_delta_score_pos_v1 \
  --journal episodes.jsonl \
  --out episodes_delta_score.jsonl
```

Ajoute un champ booléen `delta_score_positif`.

---

## Itérer sur les Transitions

L'API centrale pour utiliser le journal augmenté :

```python
from agent_service.app.modele_monde.entrainement_depuis_journal import iterer_transitions

for prev_evt, evt, z_prev, z, action in iterer_transitions(
    journal_path,
    champ_latent="signaux_hash"  # ou "checksum", "latent_id"
):
    # prev_evt : événement au tick t-1
    # evt      : événement au tick t
    # z_prev   : état latent au tick t-1
    # z        : état latent au tick t
    # action   : action appliquée pour passer de t-1 à t
    
    # Exemple : entraîner un modèle tabulaire
    delta_score = evt["score"] - prev_evt["score"]
    termine = evt["termine"]
    
    modele_monde.apprendre(z_prev, action, z)
    modele_recompense.apprendre(z_prev, action, z, delta_score)
    modele_terminaison.apprendre(z_prev, action, z, termine)
```

**Conventions importantes :**

1. **Tick 0 : état initial**
   - `action = null`
   - Pas de transition

2. **Tick t ≥ 1 : transition**
   - `action` = action appliquée pour passer de t-1 à t
   - Enregistrée dans l'événement du tick t

3. **Continuité stricte**
   - Même run_id
   - Même episode_id
   - Ticks consécutifs

---

## Bonnes Pratiques

### 1. Choisir le Bon Mode

**Pour débugger / valider :**
→ `checksum` (parfait, pas de généralisation)

**Pour un prototype rapide :**
→ `signaux_percus_hash_v1` (simple, efficace)

**Pour la production :**
→ Dépend du besoin :
- Si interprétabilité requise : `signaux_percus_hash_v1`
- Si performance maximale : `latent_appris`

### 2. Toujours Vérifier la Couverture

Après recodage, lancer un diagnostic :

```bash
PYTHONPATH=services python -m agent_service.app.modele_monde.diagnostic_utilite_v1 \
  --journal episodes_signauxhash.jsonl \
  --champ-latent signaux_hash
```

Vérifier :
- `couverture_test > 0.8` : OK
- `couverture_test < 0.6` : Besoin de plus de données ou latent plus compressif

### 3. Conserver les Journaux Intermédiaires

Structure recommandée :

```
artefacts/datasets/
  ├── journal_episodes.jsonl              # Original (brut)
  ├── journal_episodes_checksum.jsonl     # Baseline
  ├── journal_episodes_signauxhash.jsonl  # Exploitable
  └── journal_episodes_latent_appris.jsonl # Avancé
```

### 4. Documenter le Mode Utilisé

Dans les rapports :

```json
{
  "modele": "tabulaire_v1",
  "journal_source": "episodes_signauxhash.jsonl",
  "champ_latent": "signaux_hash",
  "mode_encodage": "signaux_percus_hash_v1",
  "stats": {...}
}
```

---

## Pièges à Éviter

### 1. Confondre Mode et Champ

❌ **Mauvais :**
```python
iterer_transitions(journal, champ_latent="discret_v1")
# discret_v1 est un MODE, pas un CHAMP !
```

✅ **Bon :**
```python
# D'abord recoder avec mode discret_v1
recoder(..., mode="discret_v1", champ="latent_discret")

# Puis itérer sur le champ
iterer_transitions(journal, champ_latent="latent_discret")
```

### 2. Oublier de Recoder

❌ **Mauvais :**
```python
# Journal brut sans recodage
diagnostic_utilite_v1(journal, champ_latent="signaux_hash")
# KeyError: 'signaux_hash' !
```

✅ **Bon :**
```python
# Toujours recoder d'abord (SAI-A104)
# Puis diagnostiquer (SAI-A105)
```

### 3. Mélanger les Journaux

❌ **Mauvais :**
```python
# Entraîner sur journal A
modele.apprendre(journal_A, champ="signaux_hash")

# Évaluer sur journal B (encodé différemment !)
diagnostic(journal_B, champ="signaux_hash")
# Les hash ne correspondent pas !
```

✅ **Bon :**
Toujours recoder avec le même encodeur/mode ou utiliser checksum pour la cohérence.

---

## Lien avec la Recherche

### Correspondances Académiques

**Checksum** ≈ Perfect hashing (pas de collision)

**Discret v1** ≈ Vector Quantization (VQ) manuelle

**Signaux Perçus** ≈ Feature Engineering ciblé

**Latent Appris** ≈ 
- Contrastive Learning (SimCLR, MoCo)
- VQ-VAE (Vector Quantized Variational AutoEncoder)
- World Models (Ha & Schmidhuber, 2018)

### Différence avec Deep RL

| Deep RL Classique | SAI-A104 |
|-------------------|----------|
| End-to-end training | Décomposition modulaire |
| Représentation implicite | Représentation explicite |
| Pas de généralisation garantie | Généralisation contrôlable |
| Boîte noire | Interprétable (signaux hash) |

---

## Conclusion

**SAI-A104** est l'activité de **compression intelligente**.

Elle transforme :
- Des observations visuelles brutes (grilles de pixels)
- En états latents compacts et exploitables
- Permettant la généralisation et l'apprentissage
- Tout en conservant l'information essentielle

C'est le pont entre :
- **Perception** (SAI-A102 : on observe le monde)
- **Modélisation** (SAI-A105/A106 : on apprend des règles)

Les choix d'encodage déterminent :
- La **capacité de généralisation** du modèle
- L'**émergence de l'incertitude** (entropie)
- La **facilité d'interprétation** des résultats

SAI-A104 est où la **représentation** devient un choix de design crucial, pas un détail d'implémentation.

Le bon encodage rend l'apprentissage possible.  
Le mauvais encodage le rend impossible, peu importe le modèle.

C'est l'activité qui répond à la question :  
**"Comment transformer ce que je vois en ce que je peux comprendre ?"**
