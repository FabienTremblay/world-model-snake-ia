# SAI-A107 : Préparer un Agent-Personne

## Vue d'ensemble

L'activité **SAI-A107** est l'étape cruciale où l'on **instille des connaissances** dans un agent pour le transformer d'un simple modèle mathématique en une "personne" capable d'agir de manière informée dans l'arène.

### Position dans le flux de travail

```
SAI-A106                SAI-A107                SAI-A108
Produire des      →     Préparer un       →     Éprouver
hypothèses              agent-personne          l'agent
(Registre               (Assemblage +           (Tests de
épistémique)            Entraînement)           performance)
```

### Objectif

Créer un **agent-personne** : une entité qui possède :
1. Une **structure cognitive** (tronc + têtes spécialisées)
2. Des **connaissances** issues du registre épistémique
3. Une **gouvernance** (comment les connaissances influencent les décisions)
4. Des **poids entraînés** pour opérationnaliser ces connaissances

---

## Concepts Fondamentaux

### 1. L'Agent-Personne

Un **agent-personne** n'est pas juste un réseau de neurones. C'est une architecture cognitive complète qui distingue :

- **Le tronc** : système de représentation de base
  - Encode les observations en états latents
  - Peut être tabulaire, neuronal, contrastif, etc.
  
- **Les têtes** : modules spécialisés qui "comprennent" des concepts
  - Chaque tête reconnaît un aspect du monde
  - Exemple : détecter un "couloir", une "impasse", un "espace ouvert"
  
- **La gouvernance** : système de décision intégré
  - Comment les têtes influencent les actions
  - Gestion des intentions et priorités

### 2. Les Têtes Conceptuelles

Une **tête** est un "slot instanciable" qui représente un concept :

```json
{
  "id": "structure_locale",
  "nom": "structure locale",
  "type_sortie": "classification_multiclasse",
  "role": "categorie_contenu",
  "classes": ["couloir", "impasse", "espace_ouvert"],
  "supervision": {},
  "influence": {},
  "meta": {}
}
```

#### Types de têtes possibles :

**Par type de sortie :**
- `classification_binaire` : oui/non (ex: "y a-t-il un mur devant ?")
- `classification_multiclasse` : choix parmi N classes (ex: type de structure)
- `multi_label` : plusieurs labels simultanés (ex: "couloir ET dangereux")
- `score` : valeur continue (ex: "niveau de danger")
- `regression` : prédiction numérique
- `policy_actions` : suggère des actions
- `gate` : contrôle d'activation (méta-cognition)

**Par rôle :**
- `categorie_contenu` : comprend ce qui EST (ontologie du monde)
- `categorie_controle` : détecte les situations d'action (pragmatique)
- `policy` : suggère directement des actions
- `gouvernance` : méta-décision (quand explorer vs exploiter)
- `journalisation` : mémoire et traçabilité

### 3. Le Registre Épistémique

Le **registre épistémique** (produit par SAI-A106) contient les connaissances validées :

- Régularités découvertes dans les données
- Hypothèses confirmées par analyse
- Concepts émergents identifiés
- Règles de cause à effet

**Exemple de connaissance épistémique :**
> "Dans 95% des cas où on observe un motif X devant et Y à gauche, tourner à droite mène à une terminaison dans les 3 prochains pas"

Cette connaissance peut être transformée en :
- Une tête "détecteur_piège" (classification_binaire)
- Une règle de gouvernance "éviter si détecté"

---

## Pipeline SAI-A107 en Détail

### Étape 1 : Éditer le Catalogue de Têtes

**Objectif** : Déclarer les concepts que l'agent devra maîtriser

```bash
PYTHONPATH=services python -m ui_cli.app.main preparer-agent editer-tete \
  --experience cours4 \
  --tete-id structure_locale \
  --nom "structure locale" \
  --type classification_multiclasse \
  --role categorie_contenu \
  --classes "couloir,impasse,espace_ouvert"
```

**Ce qui se passe :**
1. Le concept est ajouté au catalogue (`catalogue_tetes.json`)
2. Il devient un "slot" prêt à être instancié
3. On ne l'entraîne pas encore, on le déclare

**Artefact produit :**
```
donnees/config/experiences/cours4/artefacts/catalogues/
  └── catalogue_tetes.json
```

#### Stratégie de sélection des têtes

Les têtes doivent être choisies en fonction :

1. **Du registre épistémique** : quelles connaissances ont été validées ?
2. **De l'arène cible** : quels concepts sont pertinents ?
3. **De la complexité acceptable** : trop de têtes = surapprentissage

**Exemples de têtes utiles pour Snake :**
- `proximite_mur` : distance au plus proche obstacle
- `type_structure` : configuration spatiale locale
- `opportunite_nourriture` : détection de nourriture accessible
- `risque_collision` : anticipation de danger imminent
- `strategie_recommandee` : conseil tactique de haut niveau

### Étape 2 : Assembler l'Agent-Personne

**Objectif** : Sélectionner et organiser les têtes dans un agent cohérent

```bash
PYTHONPATH=services python -m ui_cli.app.main preparer-agent assembler \
  --experience cours4 \
  --arene-id cours4_tiny_planification \
  --agent-personne-id ap_cours4_v1 \
  --tronc-id tronc_tabulaire_v1 \
  --type-tronc tabulaire_v1 \
  --tetes "structure_locale,proximite_mur,risque_collision"
```

**Ce qui se passe :**
1. Sélection des têtes depuis le catalogue
2. Création de la structure de gouvernance
3. Initialisation des liens d'influence
4. Production d'un plan d'assemblage

**Artefacts produits :**
```
donnees/config/experiences/cours4/artefacts/
  ├── plans_preparation/
  │   └── ap_cours4_v1.plan.json
  └── agent_personne/
      └── ap_cours4_v1/
          └── agent_personne_assemble.json
```

#### Structure de l'agent assemblé

```json
{
  "version": "v1",
  "experience": "cours4",
  "arene_id": "cours4_tiny_planification",
  "agent_personne_id": "ap_cours4_v1",
  
  "tronc": {
    "id": "tronc_tabulaire_v1",
    "type_tronc": "tabulaire_v1",
    "chemin_poids": null
  },
  
  "tetes": [
    {
      "id": "structure_locale",
      "nom": "structure locale",
      "type_sortie": "classification_multiclasse",
      "role": "categorie_contenu",
      "classes": ["couloir", "impasse", "espace_ouvert"]
    }
  ],
  
  "gouvernance": {
    "intentions": {},
    "influences": {
      "structure_locale": {}
    },
    "notes": []
  },
  
  "poids": {
    "tronc": "",
    "tetes": "a_definir",
    "policy": "a_definir"
  }
}
```

### Étape 3 : Entraîner l'Agent

**Objectif** : Apprendre à reconnaître les concepts déclarés

```bash
PYTHONPATH=services python -m ui_cli.app.main preparer-agent entrainer \
  --experience cours4 \
  --agent-personne-id ap_cours4_v1
```

**Ce qui se passe :**
1. Lecture du plan d'assemblage
2. Lecture du registre épistémique pour supervision
3. Entraînement de chaque tête sur les données annotées
4. Validation croisée
5. Production du rapport d'entraînement
6. Sauvegarde de l'agent final avec poids

**Artefacts produits :**
```
donnees/config/experiences/cours4/artefacts/
  ├── runs_preparation/
  │   └── ap_cours4_v1/
  │       ├── checkpoints/
  │       └── logs/
  ├── rapports_preparation/
  │   └── ap_cours4_v1.rapport.json
  └── agent_personne/
      └── ap_cours4_v1/
          └── agent_personne.json  (version finale avec poids)
```

#### Le rapport d'entraînement

```json
{
  "genere_ts_ns": 1770401785892872331,
  "experience": "cours4",
  "arene_id": "cours4_tiny_planification",
  "agent_personne_id": "ap_cours4_v1",
  "succes": true,
  
  "mesures": {
    "tetes": {
      "structure_locale": {
        "accuracy_train": 0.94,
        "accuracy_val": 0.89,
        "entropie_moyenne": 0.12,
        "support_moyen": 450
      }
    },
    "tronc": {
      "couverture_latent": 0.87
    }
  },
  
  "chemins": {
    "agent_final": "donnees/.../agent_personne.json",
    "checkpoints": "donnees/.../runs_preparation/..."
  },
  
  "notes": [
    "Tête 'structure_locale' bien apprise",
    "Légère sur-apprentissage sur classe 'impasse'"
  ]
}
```

---

## Gouvernance et Influence

### Principe de la gouvernance

La **gouvernance** détermine comment les têtes influencent les décisions :

```python
# Pseudo-code de décision avec gouvernance
observation → tronc → état_latent

# Activation des têtes
for tete in agent.tetes:
    sortie_tete = tete.forward(état_latent)
    
# Application de la gouvernance
if tete["structure_locale"].classe == "impasse":
    if tete["risque_collision"].score > 0.8:
        # Influence forte : bloquer certaines actions
        actions_interdites.add("avancer")
        
if tete["opportunite_nourriture"].detecte:
    # Influence modérée : bonus à certaines actions
    poids_actions["vers_nourriture"] *= 1.5
```

### Types d'influence

1. **Veto absolu** : bloquer une action
   ```json
   "influence": {
     "type": "veto",
     "condition": "si classe = 'danger_imminent'",
     "actions_bloquees": ["avancer"]
   }
   ```

2. **Modulation** : ajuster les poids de la policy
   ```json
   "influence": {
     "type": "modulation",
     "facteur": 2.0,
     "cible": "action_explorateur"
   }
   ```

3. **Intention** : objectif de haut niveau
   ```json
   "intentions": {
     "mission_principale": "maximiser_score",
     "sous_mission": "explorer_zones_inconnues",
     "contrainte": "eviter_collisions"
   }
   ```

---

## Lien avec le Registre Épistémique

### Comment le registre alimente SAI-A107

Le **registre épistémique** (produit par SAI-A106) sert de source pour :

#### 1. Proposition automatique de têtes

Le système analyse le registre et suggère :
```
Hypothèse validée : "Motif X précède collision dans 92% des cas"
→ Suggestion : tête "detecteur_motif_X" (classification_binaire)
```

#### 2. Génération de labels de supervision

```python
# Le registre contient une règle validée
regle = {
  "condition": "mur_devant AND mur_gauche",
  "consequence": "structure_type = 'couloir'",
  "confiance": 0.95
}

# Utilisée pour annoter automatiquement
for episode in journal:
    if regle.condition(episode.observation):
        episode.label["structure_type"] = "couloir"
```

#### 3. Initialisation de la gouvernance

```
Connaissance : "Dans configuration Y, action Z mène à terminaison"
→ Gouvernance : interdire action Z si configuration Y détectée
```

### Pipeline complet registre → agent

```
1. SAI-A104 : Inférer épisodes
   → Journal d'épisodes enrichi

2. SAI-A106 : Produire hypothèses
   → Registre épistémique validé
   
3. SAI-A107a : Analyser le registre
   → Proposer des têtes candidates
   → Générer des labels de supervision
   
4. SAI-A107b : Éditer le catalogue
   → Sélectionner les têtes pertinentes
   → Définir leurs rôles
   
5. SAI-A107c : Assembler l'agent
   → Organiser la structure cognitive
   → Définir la gouvernance
   
6. SAI-A107d : Entraîner
   → Apprendre les concepts
   → Valider la performance
   
7. SAI-A108 : Éprouver
   → Tester en conditions réelles
   → Valider avant compétition
```

---

## Bonnes Pratiques

### 1. Commencer simple

**Première itération :**
- 1-2 têtes seulement
- Concepts simples et mesurables
- Tronc tabulaire (pas de deep learning)

**Exemple minimal viable :**
```bash
# Une seule tête : "mur devant ?"
editer-tete --tete-id mur_devant \
  --type classification_binaire \
  --classes "oui,non"
```

### 2. Valider avant de complexifier

Après chaque entraînement :
- Vérifier le rapport
- Tester en SAI-A108
- Seulement alors ajouter une nouvelle tête

### 3. Aligner têtes et arène

**Pour une arène avec portes :**
```
Têtes utiles :
- detecteur_porte
- etat_porte (ouverte/fermée)
- condition_ouverture
```

**Pour une arène d'exploration :**
```
Têtes utiles :
- zones_visitees
- frontieres_inconnues
- densite_nourriture
```

### 4. Documenter les intentions

```json
"gouvernance": {
  "intentions": {
    "objectif_principal": "survivre le plus longtemps",
    "sous_objectif": "cartographier l'arène",
    "mode_actuel": "exploration_prudente"
  },
  "notes": [
    "Priorité à la sécurité en phase initiale",
    "Basculer en exploitation après 100 ticks"
  ]
}
```

---

## Différences Tronc vs Têtes

### Le Tronc

- **Rôle** : représentation de base
- **Nature** : général, non spécialisé
- **Apprentissage** : sur tous les épisodes
- **Sortie** : état latent (vecteur ou ID discret)

### Les Têtes

- **Rôle** : interprétation conceptuelle
- **Nature** : spécialisées, sémantiques
- **Apprentissage** : sur données annotées
- **Sortie** : classification, score, policy

### Analogie

```
Tronc = "système perceptif de base"
  (comme la rétine qui transforme la lumière en signaux)
  
Têtes = "centres cognitifs spécialisés"
  (comme l'aire visuelle qui reconnaît les visages)
```

---

## Diagnostics et Déboggage

### Problème : Têtes mal apprises

**Symptômes :**
```json
"mesures": {
  "structure_locale": {
    "accuracy_val": 0.52  // Proche du hasard !
  }
}
```

**Causes possibles :**
1. Labels de supervision incorrects
2. Concept trop complexe pour le tronc
3. Données d'entraînement insuffisantes
4. Classe déséquilibrée

**Solutions :**
- Vérifier le registre épistémique source
- Simplifier le concept
- Générer plus d'épisodes en SAI-A102
- Ré-échantillonner les classes

### Problème : Gouvernance incohérente

**Symptômes :**
L'agent en SAI-A108 prend des décisions aberrantes

**Causes possibles :**
1. Influences contradictoires
2. Intentions mal définies
3. Poids d'influence mal calibrés

**Solutions :**
- Simplifier la gouvernance (1 intention à la fois)
- Tester les têtes individuellement
- Ajouter des logs de décision

---

## Conclusion

**SAI-A107** est l'activité où la **connaissance devient capacité**. 

Elle transforme :
- Des hypothèses (registre épistémique)
- En concepts (têtes)
- Opérationnalisés (poids entraînés)
- Intégrés (gouvernance)
- Dans une entité cohérente (agent-personne)

C'est le pont entre **comprendre le monde** (SAI-A106) et **agir efficacement** (SAI-A108).

L'agent-personne qui en résulte n'est pas qu'un modèle statistique : c'est une architecture cognitive qui possède des connaissances structurées sur son environnement et sait comment les utiliser pour décider.
