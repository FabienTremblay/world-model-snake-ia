# SAI-A106 : Produire des Hypothèses (Registre Épistémique)

## Vue d'ensemble

L'activité **SAI-A106** est le processus de **découverte et formalisation de connaissances** à partir des données brutes d'expérimentation. C'est l'étape où les régularités observées deviennent des hypothèses validées, structurées dans un **registre épistémique**.

### Position dans le flux de travail

```
SAI-A104                SAI-A106                SAI-A107
Inférer les       →     Produire des      →     Préparer un
épisodes                hypothèses              agent-personne
(Journal               (Registre               (Instillation
enrichi)               épistémique)            des connaissances)
```

### Objectif

Transformer les **observations empiriques** en **connaissances structurées** :
- Identifier les régularités dans les données
- Formuler des hypothèses testables
- Évaluer leur validité statistique
- Créer des règles d'inférence
- Constituer une ontologie (vocabulaire conceptuel)

---

## Le Principe Fondamental : Terminologie Émergente

### Axiome central

> **Le monde n'impose aucune sémantique.**  
> Les noms et concepts sont créés par l'Agent Producteur de Connaissances (APK).

Cela signifie :
- Le simulateur du monde ne connaît que des pixels, positions, états
- L'APK **nomme** ce qu'il observe : "mur", "collision", "croissance"
- Ces noms sont **révisables** : ils peuvent être renommés, fusionnés, spécialisés
- C'est une **ontologie en construction**, pas une vérité absolue

### Exemple concret

Le monde dit : `pixel[x,y] = 3`  
L'APK interprète : "c'est un **mur**"  
L'APK formule : "si action vers mur → collision → fin"

Le concept "mur" n'existe que dans la tête de l'APK. Un autre APK pourrait appeler ça "obstacle", "barrière" ou "zone_interdite".

---

## L'Agent Producteur de Connaissances (APK)

### Rôle

L'**APK** est un système analytique qui :
1. **Lit** les journaux d'épisodes
2. **Détecte** les régularités statistiques
3. **Nomme** les concepts émergents
4. **Formule** des hypothèses
5. **Évalue** leur validité
6. **Produit** un registre épistémique

### Différence avec l'agent joueur

| Agent Joueur | APK |
|--------------|-----|
| Agit dans le monde | Observe depuis l'extérieur |
| Temps réel (online) | Analyse rétrospective (offline) |
| Prend des décisions | Produit des connaissances |
| Vue subjective | Vue d'estrade |

L'APK est comme un **scientifique** qui analyse les enregistrements d'expériences.

---

## Structure du Registre Épistémique

Le **registre épistémique** est un artefact JSON contenant :

### 1. Hypothèses

Une **hypothèse** est une assertion testable sur le monde.

```python
@dataclass(frozen=True)
class HypotheseEpistemiqueV1:
    id_hypothese: str           # Identifiant unique
    etiquette: str              # Description lisible
    antecedents: List[str]      # Conditions
    consequences: List[str]     # Résultats attendus
    metadonnees: Dict[str, str] # Informations supplémentaires
```

**Exemple concret :**
```json
{
  "id_hypothese": "h.danger_mur_v1",
  "etiquette": "collision mur → terminaison",
  "antecedents": ["mur_devant", "action_vers_mur"],
  "consequences": ["termine"],
  "metadonnees": {
    "type": "danger",
    "motif_mur": "3"
  }
}
```

### 2. Règles d'Inférence

Une **règle** transforme une information en une autre.

```python
@dataclass(frozen=True)
class RegleInferenceV1:
    id_regle: str           # Identifiant unique
    etiquette: str          # Description
    premisses: List[str]    # Conditions
    conclusion: str         # Déduction
    metadonnees: Dict       # Contexte
```

**Exemple concret :**
```json
{
  "id_regle": "r.eviter_mur_v1",
  "etiquette": "si mur devant → action interdite",
  "premisses": ["mur_devant", "action_vers_mur"],
  "conclusion": "action_interdite",
  "metadonnees": {
    "note": "dérivée empiriquement (cours 4)"
  }
}
```

### 3. Évaluations

Une **évaluation** quantifie la validité d'une hypothèse.

```python
@dataclass(frozen=True)
class EvaluationHypotheseV1:
    id_hypothese: str       # Lien vers l'hypothèse
    support: int            # Nombre d'occurrences
    confirmations: int      # Cas confirmant l'hypothèse
    contradictions: int     # Cas infirmant l'hypothèse
    confiance: float        # Ratio confirmations/support
    note: Optional[str]     # Détails
```

**Exemple concret :**
```json
{
  "id_hypothese": "h.danger_mur_v1",
  "support": 59,
  "confirmations": 59,
  "contradictions": 0,
  "confiance": 1.0,
  "note": "confirmations_raison=59"
}
```

**Interprétation :** Sur 59 cas où l'agent a foncé vers un mur, 59 fois (100%) cela a mené à la terminaison. L'hypothèse est **validée**.

### 4. Index et Métadonnées

```json
{
  "version": "registre_epistemique_v1",
  "index_par_etiquette": {
    "dangers_v1": ["h.danger_mur_v1", "r.eviter_mur_v1"]
  }
}
```

---

## Pipeline SAI-A106 en Détail

### Phase 1 : Préparation des Données

**Entrée :** Journal d'épisodes augmenté (produit par SAI-A104)

Le journal contient pour chaque transition :
```json
{
  "tick": 42,
  "episode_id": 3,
  "capteurs_compact": "base64...",
  "action": "droite",
  "termine": false,
  "raison_fin": null,
  "score": 15,
  "longueur_serpent": 5,
  "largeur": 30,
  "hauteur": 12
}
```

### Phase 2 : Extraction de Signaux

L'APK extrait des **signaux du monde** depuis les transitions :

```python
def extraire_signaux_monde_v1(e0, e1):
    """Compare deux états successifs pour détecter les changements."""
    return {
        "collision_mur": bool(...),
        "delta_longueur": e1["longueur"] - e0["longueur"],
        "delta_score": e1["score"] - e0["score"],
        "termine": e1["termine"],
        "raison_fin": e1["raison_fin"],
        # ...
    }
```

### Phase 3 : Détection de Régularités

L'APK cherche des **patterns statistiques** :

#### Pattern 1 : Règles de danger

```python
# Pour chaque transition
if motif_devant == MOTIF_MUR:  # ex: pixel = 3
    support_mur += 1
    if transition.termine:
        confirmations_mur += 1
    else:
        contradictions_mur += 1
```

#### Pattern 2 : Règles de bénéfice

```python
if delta_longueur > 0:  # Le serpent a grandi
    support_croissance += 1
    if delta_score > 0:  # ET le score a augmenté
        confirmations_nourriture += 1
    else:
        contradictions_nourriture += 1
```

### Phase 4 : Formulation d'Hypothèses

À partir des patterns, l'APK crée des hypothèses :

**Hypothèse de danger :**
```
SI (mur_devant ET action_vers_mur)
ALORS termine (avec confiance 1.0 sur 59 cas)
```

**Hypothèse de bénéfice :**
```
SI (croissance ET delta_score_positif)
ALORS nourriture_consommée (avec confiance 0.95 sur 142 cas)
```

### Phase 5 : Création de Règles

Les hypothèses validées deviennent des **règles actionnables** :

```
Règle R1: mur_devant + action_vers_mur → action_interdite
Règle R2: delta_longueur_positif → croissance
Règle R3: delta_score_positif → gain_score
```

### Phase 6 : Construction du Registre

Tout est assemblé dans le **registre épistémique** :

```json
{
  "hypotheses": {...},
  "regles": {...},
  "evaluations": {...},
  "index_par_etiquette": {...},
  "version": "registre_epistemique_v1"
}
```

---

## Types d'APK Disponibles

### 1. APK Règles de Danger (v1)

**Fichier :** `apk_regles_dangers_v1.py`

**Objectif :** Détecter les situations dangereuses

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.epistemique.apk_regles_dangers_v1 \
  --journal donnees/.../journal_episodes.jsonl \
  --experience cours4 \
  --etiquette dangers_v1
```

**Hypothèses produites :**
- `h.danger_mur_v1` : collision avec mur → terminaison
- `h.danger_corps_v1` : collision avec soi → terminaison

**Méthode :**
1. Analyse les capteurs de voisinage (motifs devant/gauche/droite/derrière)
2. Corrèle avec les actions prises
3. Vérifie si cela mène à une terminaison
4. Identifie la raison exacte (collision_mur vs collision_soi)

### 2. APK Général (v1)

**Fichier :** `agent_producteur_connaissances_v1.py`

**Objectif :** Analyse globale du monde

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.epistemique.agent_producteur_connaissances_v1 \
  --journal artefacts/episodes.jsonl \
  --out-registre artefacts/registre_epistemique_v1.json
```

**Hypothèses produites :**
- `H1` : collision_mur → fin_irreversible
- `H2` : croissance + delta_score_pos → nourriture_consommée

**Règles produites :**
- `R1` : delta_longueur_pos → croissance
- `R2` : delta_score_pos → gain_score

### 3. APK Épistémique v2 (Cours 5)

**Fichier :** `epistemique_v2/`

**Objectif :** Analyse avancée avec indices statistiques

**Commande :**
```bash
PYTHONPATH=services python -m agent_service.app.epistemique_v2.cli \
  --experience preparation_cours_5
```

**Indices produits :**
```json
{
  "indices": {
    "episodes": 200,
    "ticks": 5479,
    "raisons_fin": {
      "collision_mur": 200,
      "collision_soi": 1
    },
    "latents_distincts": 1935
  },
  "hypotheses": [
    {
      "id": "raison_fin_dominante",
      "titre": "une seule raison de fin domine",
      "confiance": 0.6,
      "evidences": {
        "raison_fin": "collision_mur",
        "part": 0.995
      }
    }
  ]
}
```

**Caractéristiques :**
- Détection de biais (raison de fin dominante)
- Analyse de la diversité d'états latents
- Hypothèses de haut niveau avec conditions de test

---

## Concepts Clés de l'APK

### 1. Support

**Définition :** Nombre d'occurrences où les conditions de l'hypothèse sont remplies

**Exemple :**
```
Hypothèse : "mur devant → collision"
Support = 59 (il y a eu 59 situations où l'agent était face à un mur)
```

**Importance :** Un support faible (< 10) rend l'hypothèse peu fiable.

### 2. Confirmation vs Contradiction

**Confirmation :** Cas où l'hypothèse est vérifiée
**Contradiction :** Cas où l'hypothèse est infirmée

```python
if mur_devant and action_vers_mur:
    support += 1
    if termine:
        confirmations += 1  # L'hypothèse est confirmée
    else:
        contradictions += 1  # L'hypothèse est infirmée
```

### 3. Confiance

**Formule :** `confiance = confirmations / support`

**Interprétation :**
- `confiance = 1.0` : Toujours vrai (règle absolue)
- `confiance = 0.95` : Vrai dans 95% des cas (règle forte)
- `confiance = 0.5` : Vrai dans 50% des cas (règle faible/aléatoire)

**Seuils recommandés :**
- `confiance > 0.9` : Hypothèse validée
- `0.7 < confiance < 0.9` : Hypothèse probable
- `confiance < 0.7` : Hypothèse douteuse

### 4. Terminologie Propre

L'APK crée son **vocabulaire** :

```
Concepts de base :
- mur_devant
- corps_devant
- collision_mur
- fin_irreversible

Concepts dérivés :
- croissance (= delta_longueur > 0)
- gain_score (= delta_score > 0)
- nourriture_consommée (croissance + gain_score)

Concepts d'action :
- action_vers_mur
- action_interdite
```

Ces noms sont **arbitraires** mais **cohérents** au sein du registre.

---

## Utilisation du Registre Épistémique

### En SAI-A107 (Préparer un agent)

Le registre alimente la création de **têtes conceptuelles** :

```
Hypothèse validée : "mur_devant → collision"
  ↓
Tête : "detecteur_mur" (classification_binaire)
  ↓
Gouvernance : "si mur détecté → interdire action"
```

### En SAI-A108 (Éprouver)

Le registre sert de **référence** pour diagnostiquer :

```python
# L'agent se crashe souvent ?
# → Vérifier si la règle "eviter_mur" est bien apprise
# → Comparer avec l'hypothèse h.danger_mur_v1
```

### En SAI-A105 (Analyser)

Le registre permet de **comparer versions** :

```
Registre v1 : 2 hypothèses, confiance moyenne 0.95
Registre v2 : 5 hypothèses, confiance moyenne 0.88
  → Plus de connaissances mais moins certaines
  → Suggère un agent plus exploratoire
```

---

## Évolution du Registre

### Versionnage

Chaque registre est **versionné** :

```json
{
  "version": "registre_epistemique_v1",
  "genere_ts_ns": 1770401728661774941
}
```

### Fusion/Mise à jour

Un APK peut **enrichir** un registre existant :

```python
# Charger un registre existant
reg = RegistreEpistemiqueV1.charger_json("registre_v1.json")

# Ajouter de nouvelles hypothèses
reg.ajouter_hypothese(nouvelle_hypothese)

# Sauvegarder
reg.sauvegarder_json("registre_v2.json")
```

### Révision de Terminologie

Les concepts peuvent être **renommés** :

```
Version 1 : "obstacle" → "termine"
Version 2 : "mur" → "collision" (concept plus précis)
Version 3 : "mur" ou "corps" → "collision" (concepts fusionnés)
```

---

## Diagnostics et Qualité

### Indicateurs de Qualité du Registre

**1. Nombre d'hypothèses**
- Trop peu (< 3) : Connaissances insuffisantes
- Optimal (3-10) : Bon équilibre
- Trop (> 20) : Risque de sur-spécialisation

**2. Confiance moyenne**
- `> 0.9` : Excellente
- `0.7 - 0.9` : Bonne
- `< 0.7` : Douteuse

**3. Support moyen**
- `> 100` : Excellent
- `50 - 100` : Bon
- `< 50` : Faible (besoin de plus de données)

**4. Diversité**
- Hypothèses sur différents aspects (dangers, bénéfices, structures)
- Pas toutes concentrées sur un seul pattern

### Commande de Diagnostic

```bash
PYTHONPATH=services python -m agent_service.app.epistemique.diagnostic_epistemique_smoke_v1 \
  --journal donnees/.../journal_episodes.jsonl
```

**Vérifications :**
- Cohérence interne du registre
- Absence de contradictions
- Complétude des évaluations

---

## Exemples Concrets de Production

### Exemple 1 : APK Règles de Danger

**Contexte :** 200 épisodes, agent aléatoire dans arène simple

**Exécution :**
```bash
PYTHONPATH=services python -m agent_service.app.epistemique.apk_regles_dangers_v1 \
  --journal donnees/config/experiences/cours4/artefacts/runs/2026-02-04_15h37/journal_episodes.jsonl \
  --experience cours4 \
  --etiquette dangers_v1
```

**Sortie :**
```
Analysé 7207 événements
Hypothèse h.danger_mur_v1:
  - Support: 59
  - Confirmations: 59
  - Contradictions: 0
  - Confiance: 1.0
  
Hypothèse h.danger_corps_v1:
  - Support: 0
  - Confirmations: 0
  - Contradictions: 0
  - Confiance: 0.0
```

**Artefact produit :**
```
donnees/config/experiences/cours4/artefacts/registres/
  └── apk_regles_dangers_v1__journal_episodes.json
```

**Interprétation :**
- La règle "mur → collision" est **parfaitement validée** (100%)
- Aucune collision avec soi-même détectée (agent pas assez long)
- Registre minimal mais fiable

### Exemple 2 : APK Général

**Contexte :** 150 épisodes, agent planificateur

**Exécution :**
```bash
PYTHONPATH=services python -m agent_service.app.epistemique.agent_producteur_connaissances_v1 \
  --journal artefacts/episodes.jsonl \
  --out-registre artefacts/registre_v1.json
```

**Sortie :**
```json
{
  "hypotheses": {
    "H1": {
      "etiquette": "collision_mur -> fin_irreversible",
      "antecedents": ["collision_mur"],
      "consequences": ["fin_irreversible"]
    },
    "H2": {
      "etiquette": "croissance + delta_score_pos -> nourriture_consomme",
      "antecedents": ["croissance", "delta_score_pos"],
      "consequences": ["nourriture_consomme"]
    }
  },
  "evaluations": {
    "H1": {
      "support": 142,
      "confirmations": 142,
      "confiance": 1.0
    },
    "H2": {
      "support": 38,
      "confirmations": 37,
      "confiance": 0.974
    }
  }
}
```

**Interprétation :**
- H1 validée à 100% (142/142)
- H2 validée à 97.4% (37/38)
  - 1 contradiction : croissance sans gain de score (bug ou edge case)
- Registre riche avec 2 types de connaissances

---

## Bonnes Pratiques

### 1. Commencer avec des Hypothèses Simples

**Première itération :**
- 2-3 hypothèses maximum
- Concepts observables directement
- Règles déterministes

**Exemple minimal :**
```
H1: mur devant → collision
H2: croissance → score augmente
```

### 2. Valider avec Plusieurs Arènes

Une hypothèse doit être testée sur différentes configurations :

```bash
# Arène simple
apk_regles_dangers_v1 --journal tiny_v0.jsonl --experience test_tiny

# Arène complexe
apk_regles_dangers_v1 --journal demo_v0.jsonl --experience test_demo
```

Si la confiance reste élevée partout → hypothèse robuste.

### 3. Documenter les Métadonnées

```json
"metadonnees": {
  "version": "v1",
  "type": "danger",
  "arene_source": "tiny_v0",
  "agent_source": "agent_curiosite",
  "date_generation": "2026-02-04",
  "note": "Première version, validée manuellement"
}
```

### 4. Évaluer la Complétude

Un bon registre couvre :
- ✅ Les dangers (collision, terminaison)
- ✅ Les bénéfices (score, croissance)
- ✅ Les structures spatiales (couloir, impasse)
- ✅ Les stratégies (exploration, exploitation)

### 5. Réviser Régulièrement

```
Itération 1 : Registre v1 (2 hypothèses)
  ↓ Analyse
Itération 2 : Registre v2 (4 hypothèses, 1 renommée)
  ↓ Validation
Itération 3 : Registre v3 (5 hypothèses, 2 fusionnées)
```

---

## Pièges à Éviter

### 1. Confondre Support et Confiance

❌ **Mauvais :**
```
Hypothèse : "situation rare → succès"
Support : 2
Confiance : 1.0
→ Validée !
```

✅ **Bon :**
```
Support trop faible (< 10)
→ Hypothèse non concluante, besoin de plus de données
```

### 2. Ignorer les Contradictions

❌ **Mauvais :**
```
Confirmations : 95
Contradictions : 5
→ Confiance = 0.95, validée !
```

✅ **Bon :**
```
Analyser les 5 contradictions :
- Sont-elles des edge cases ?
- Y a-t-il un bug dans l'extraction ?
- Faut-il spécialiser l'hypothèse ?
```

### 3. Sur-spécialiser

❌ **Mauvais :**
```
h.danger_mur_devant_gauche_score_pair_tick_impair
```

✅ **Bon :**
```
h.danger_mur (général)
→ Ensuite spécialiser si nécessaire
```

### 4. Vocabulaire Incohérent

❌ **Mauvais :**
```
H1: "mur" → "fin"
H2: "obstacle" → "terminaison"
H3: "barrière" → "stop"
```

✅ **Bon :**
```
H1: "mur" → "termine"
H2: "mur" → "collision_mur"
H3: "corps" → "collision_soi"
(vocabulaire unifié)
```

---

## Lien avec la Recherche

### World Models et Épistémologie

SAI-A106 implémente une forme de :

**Model-Based Epistemology :**
- L'agent construit une **théorie du monde**
- Cette théorie est **falsifiable** (Popper)
- Elle évolue par **révision** (Lakatos)

**Différence avec Deep Learning :**

| Deep Learning | APK Épistémique |
|---------------|-----------------|
| Poids opaques | Hypothèses explicites |
| Boîte noire | Boîte blanche |
| Corrélations | Causalité (tentative) |
| Non interprétable | Lisible par humain |

### Inspiration

- **Induction logique** (Mitchell, 1997)
- **Symbolic AI** (Newell & Simon)
- **Scientific Discovery** (Langley et al.)
- **Automated Science** (King et al., 2009)

---

## Conclusion

**SAI-A106** est l'activité où les **données deviennent savoir**.

Elle transforme :
- Des séquences d'observations brutes
- En connaissances structurées et validées
- Exprimées dans un vocabulaire émergent
- Prêtes à être opérationnalisées

Le **registre épistémique** qui en résulte est :
- Un **artefact cognitif** : il capture ce que l'APK "sait"
- Un **pont** : entre données (SAI-A104) et capacités (SAI-A107)
- Une **ontologie** : un système cohérent de concepts
- Un **contrat** : ce que l'agent peut affirmer sur le monde

C'est la différence entre un système qui **corrèle** (ML classique) et un système qui **comprend** (IA symbolique/hybride).

Le registre épistémique est la **mémoire sémantique** de l'agent : non pas ce qu'il a vu, mais ce qu'il en a compris.
