# SAI-A108 : Éprouver un Agent (Validation et Tests)

## Vue d'ensemble

L'activité **SAI-A108** est le processus de **validation et d'évaluation** d'un agent préparé. C'est l'étape où l'on teste si l'agent-personne est **prêt pour la compétition** en le mettant à l'épreuve dans des conditions contrôlées.

### Position dans le flux de travail

```
SAI-A107                SAI-A108                SAI-B
Préparer un       →     Éprouver un       →     Compétition
agent-personne          agent                   (Exploitation)
(Entraînement)          (Validation)            
```

### Objectif

Répondre à la question : **"L'agent est-il prêt ?"**

Pour cela, on :
1. **Exécute** l'agent dans l'arène cible
2. **Mesure** ses performances objectives
3. **Compare** avec les attentes/baselines
4. **Décide** : prêt pour compétition ou retour en SAI-A107

---

## Principe Fondamental : Test sous Conditions Contrôlées

### Différence avec SAI-A102

| SAI-A102 (Générer) | SAI-A108 (Éprouver) |
|--------------------|---------------------|
| **Exploration** | **Exploitation** |
| Agent simple (aléatoire, curiosité) | Agent préparé (agent-personne) |
| Objectif : collecter données | Objectif : mesurer performance |
| Nombreux épisodes (100-200+) | Peu d'épisodes (1-10) |
| Arènes variées | Arène cible spécifique |
| Pas d'attente de performance | Critères de réussite définis |

### Métaphore

```
SAI-A102 = Entraînement en salle de sport
  → On explore, on essaie, on apprend

SAI-A108 = Examen de qualification
  → On teste si on est prêt pour la compétition
```

---

## Le Runtime de l'Agent-Personne

### Incarnation vs Artefact

**Artefact (SAI-A107) :**
```json
{
  "agent_personne_id": "ap_cours4_v1",
  "tronc": {...},
  "tetes": [...],
  "gouvernance": {...},
  "poids": {...}
}
```
→ Fichier statique, description

**Runtime (SAI-A108) :**
```python
class AgentPersonneRuntimeV1(IAgent):
    def __init__(self, agent_personne_path):
        # Charge l'artefact
        self.agent_personne = charger_json(agent_personne_path)
        
        # État d'instance (mémoire)
        self.memoire = {
            "tick": 0,
            "dernier_latent": None,
            "derniere_action": None
        }
    
    def choisir_action(self, capteurs, contexte):
        # 1. Évaluer les têtes
        sorties_tetes = self._evaluer_tetes(capteurs)
        
        # 2. Appliquer la gouvernance
        # 3. Retourner une action
        return action
```
→ Instance vivante, en exécution

### Cycle d'Exécution

```
Pour chaque tick :
  1. Monde → capteurs (observation)
  2. Runtime → choisir_action(capteurs, contexte)
     a. Encoder observation → état latent
     b. Évaluer chaque tête → sorties
     c. Appliquer gouvernance → décision
     d. Policy → action
  3. Runtime → action
  4. Monde applique action → nouvel état
  5. Répéter
```

---

## Pipeline SAI-A108 Détaillé

### Étape 1 : Configuration de l'Épreuve

**Paramètres expérimentaux :**

```bash
./scripts/a108_eprouver_agent_personne.sh \
  cours4 \                          # Expérience
  cours4_tiny_planification \       # Arène cible
  ap_cours4_v1 \                    # ID agent-personne
  5 \                               # Nombre d'épisodes
  50                                # Max ticks par épisode
```

**Ou via CLI directe :**

```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --arene cours4_tiny_planification \
  --agent agent_personne \
  --agent-personne-id ap_cours4_v1 \
  --episodes 5 \
  --max-ticks 50 \
  --seed 123
```

### Étape 2 : Chargement de l'Agent

Le runtime charge l'artefact :

```
donnees/config/experiences/cours4/artefacts/agent_personne/
  └── ap_cours4_v1/
      └── agent_personne.json
```

**Contenu :**
- Référence au tronc
- Liste des têtes avec leurs rôles
- Règles de gouvernance
- Pointeurs vers les poids (si entraînés)

### Étape 3 : Exécution

Pour chaque épisode :

```
1. Initialiser le monde (seed, arène)
2. Initialiser l'agent (reset mémoire)
3. Boucle jusqu'à terminaison ou max_ticks :
   a. Observer (capteurs)
   b. Décider (runtime)
   c. Agir (monde)
   d. Enregistrer (journal + métriques)
4. Finaliser l'épisode
```

### Étape 4 : Enregistrement

**Artefacts produits :**

```
donnees/config/experiences/cours4/artefacts/runs/2026-02-10_14h35/
  ├── meta.json              # Métadonnées du run
  ├── journal_episodes.jsonl # Actions détaillées
  ├── metrics.jsonl          # Métriques par tick
  └── stdout.log             # Logs de l'exécution
```

**Format journal :**
```json
{
  "run_id": "1770401785892872331",
  "episode_id": 0,
  "tick": 5,
  "capteurs_compact": "eJzt...",
  "action": "observer_droite",
  "score": 10,
  "longueur_serpent": 4,
  "termine": false
}
```

**Format métriques :**
```json
{
  "tick": 5,
  "episode_id": 0,
  "score": 10,
  "longueur_serpent": 4,
  "termine": false,
  "sorties_tetes": {
    "structure_locale": "couloir",
    "mode_enjeu": "prudent",
    "dbg_motifs_voisins": {
      "haut": 0,
      "droite": 2
    }
  }
}
```

### Étape 5 : Analyse des Résultats

Le script `a108_eprouver_agent_personne.sh` génère automatiquement un résumé :

```
=== Résumé A108 ===
Journal: .../journal_episodes.jsonl

Actions (top 15):
            avant : 142
  observer_gauche : 28
  observer_droite : 15
             null : 5

Fin d'épisodes:
  collision_mur : 3
  max_ticks_atteint : 2

Détails par épisode:
  ep   0 | ticks≈50  | score=25  | longueur=7  | termine=True | raison_fin=max_ticks_atteint
  ep   1 | ticks≈18  | score=10  | longueur=4  | termine=True | raison_fin=collision_mur
  ep   2 | ticks≈50  | score=30  | longueur=8  | termine=True | raison_fin=max_ticks_atteint
  ep   3 | ticks≈12  | score=5   | longueur=3  | termine=True | raison_fin=collision_mur
  ep   4 | ticks≈50  | score=28  | longueur=7  | termine=True | raison_fin=max_ticks_atteint
```

---

## Critères de Validation

### Métriques Primaires

**1. Taux de survie**
```
taux_survie = (episodes_max_ticks / total_episodes) * 100
```

**Interprétation :**
- `> 80%` : Excellent (agent maîtrise l'arène)
- `50-80%` : Bon (quelques erreurs)
- `< 50%` : Insuffisant (retour SAI-A107)

**2. Score moyen**
```
score_moyen = somme(scores) / nb_episodes
```

**Comparaison avec baseline :**
- Agent aléatoire : score ≈ 5-10
- Agent prudent : score ≈ 15-25
- Agent expert : score ≈ 30-50

**3. Longueur moyenne**
```
longueur_moyenne = somme(longueurs_finales) / nb_episodes
```

**4. Distribution des raisons de fin**

```python
raisons = Counter()
for episode in resultats:
    raisons[episode.raison_fin] += 1

# Attendu pour un bon agent :
# collision_mur : < 20%
# collision_soi : < 10%
# max_ticks : > 70%
```

### Métriques Secondaires

**5. Actions dominantes**

Un agent équilibré devrait avoir :
- `avant` : 60-80% (avance souvent)
- `observer_gauche/droite` : 15-30% (tourne quand nécessaire)

**6. Variabilité entre épisodes**

```python
import statistics

scores = [ep.score for ep in episodes]
variance = statistics.variance(scores)

# Faible variance (<10) : comportement stable
# Haute variance (>30) : comportement erratique
```

**7. Activation des têtes**

Si l'agent a des têtes cognitives :

```python
sorties = extract_sorties_tetes(metrics)

# Vérifier que les têtes s'activent
tete_structure_activations = [
    s["structure_locale"] for s in sorties
]

# Attendu : variété de détections
# Mauvais : toujours "inconnu"
```

---

## Décisions Post-Épreuve

### Arbre de Décision

```
Taux survie > 80% ET Score moyen > 25 ?
  ├─ OUI → Prêt pour compétition (SAI-B)
  └─ NON → Analyser les causes
            ├─ Collisions fréquentes ?
            │   └─ Retour SAI-A107 : renforcer tête "détection danger"
            ├─ Score faible mais survit ?
            │   └─ Retour SAI-A107 : ajouter tête "opportunité nourriture"
            ├─ Comportement erratique ?
            │   └─ Retour SAI-A106 : valider hypothèses
            └─ Couverture modèle faible ?
                └─ Retour SAI-A102 : collecter plus de données
```

### Cas Typiques

**Cas 1 : Agent trop prudent**
```
Résultat :
- Taux survie : 100%
- Score moyen : 12
- Longueur moyenne : 3

Diagnostic : Évite tout mais ne cherche pas la nourriture
Action : Retour SAI-A107, ajouter tête "attraction_nourriture"
```

**Cas 2 : Agent téméraire**
```
Résultat :
- Taux survie : 30%
- Score moyen : 35 (quand survit)
- raison_fin : 70% collision_mur

Diagnostic : Cherche la nourriture sans précaution
Action : Retour SAI-A107, renforcer poids tête "danger"
```

**Cas 3 : Agent confus**
```
Résultat :
- Actions : 40% avant, 30% gauche, 30% droite
- Variance score : 45
- Têtes : toujours "inconnu"

Diagnostic : Gouvernance défaillante ou têtes non entraînées
Action : Retour SAI-A107, vérifier entraînement têtes
```

**Cas 4 : Agent prêt**
```
Résultat :
- Taux survie : 90%
- Score moyen : 32
- Longueur moyenne : 8
- Actions : 75% avant, 20% observer, 5% autres
- Têtes : détections variées et cohérentes

Diagnostic : Bon équilibre survie/performance
Action : Passage en SAI-B (compétition)
```

---

## Comparaison avec Baselines

### Agents de Référence

**Agent Aléatoire :**
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --agent aleatoire \
  --episodes 10
```

**Performance attendue :**
- Taux survie : 0-5%
- Score moyen : 5-8
- Sert de plancher absolu

**Agent Planificateur MPC :**
```bash
PYTHONPATH=services python -m ui_cli.app.main \
  --experience cours4 \
  --agent planif_mpc_observateur_tabulaire \
  --episodes 10
```

**Performance attendue :**
- Taux survie : 60-80%
- Score moyen : 25-35
- Sert de référence haute

### Table Comparative

| Agent | Survie | Score moy | Longueur moy |
|-------|--------|-----------|--------------|
| Aléatoire | 2% | 6 | 3 |
| Prudent simple | 50% | 15 | 5 |
| MPC tabulaire | 70% | 28 | 7 |
| **Agent-personne (cible)** | **>80%** | **>25** | **>6** |

---

## Variantes d'Épreuves

### Épreuve Standard (Qualification)

**Objectif :** Valider agent prêt pour compétition

**Configuration :**
- Arène : celle de la compétition
- Épisodes : 5-10
- Seed : fixe (reproductibilité)
- Max ticks : 50-100

**Critères :**
- Survie > 80%
- Score > baseline + 20%

### Épreuve de Robustesse

**Objectif :** Tester stabilité face aux perturbations

**Configuration :**
- Arène : identique
- Épisodes : 20
- Seeds : variés (différents spawns)
- Niveau bruit : 0, 1, 2 (si supporté)

**Critères :**
- Variance score < 15
- Performance stable sur tous seeds

### Épreuve de Généralisation

**Objectif :** Vérifier transfert à nouvelles arènes

**Configuration :**
- Arènes : 3-5 différentes
- Épisodes : 5 par arène
- Seed : fixe

**Critères :**
- Performance > 60% sur toutes arènes
- Pas de chute drastique (>50%)

### Épreuve de Stress

**Objectif :** Trouver les limites

**Configuration :**
- Arène : complexe
- Max ticks : 500-1000
- Épisodes : 3

**Critères :**
- Identifier comportements émergents
- Détecter bugs/edge cases

---

## Diagnostics Avancés Post-A108

### 1. Analyse Temporelle

```python
# Examiner l'évolution du comportement au cours de l'épisode
from collections import defaultdict

actions_par_phase = defaultdict(list)
for evt in journal:
    phase = evt["tick"] // 10  # Découper en tranches de 10 ticks
    actions_par_phase[phase].append(evt["action"])

# Vérifier : agent plus prudent en fin de partie ?
```

### 2. Heatmap des Terminaisons

```python
# Où l'agent meurt-il le plus souvent ?
positions_mort = []
for episode in episodes:
    if episode.termine and episode.raison_fin == "collision_mur":
        evt_final = get_last_event(episode)
        pos = extraire_position_tete(evt_final.capteurs)
        positions_mort.append(pos)

# Visualiser la heatmap
# → Identifier zones dangereuses
```

### 3. Cohérence Têtes-Actions

```python
# Les têtes influencent-elles vraiment les actions ?
from scipy.stats import chi2_contingency

contingence = defaultdict(lambda: defaultdict(int))
for m in metrics:
    structure = m["sorties_tetes"]["structure_locale"]
    action = m["action"]
    contingence[structure][action] += 1

# Test chi2
# p-value < 0.05 → dépendance significative
# p-value > 0.05 → têtes n'influencent pas (problème !)
```

---

## Bonnes Pratiques

### 1. Toujours Fixer le Seed

```bash
# Reproductibilité
--seed 123

# Relancer avec même seed → mêmes résultats
```

### 2. Petites Épreuves Fréquentes

Mieux vaut :
- 5 épisodes, 3 fois par jour
- Qu'une épreuve de 100 épisodes une fois

Itération rapide > validation exhaustive

### 3. Comparer avec Run Précédent

```bash
# Run 1 (baseline)
./scripts/a108_eprouver_agent_personne.sh cours4 tiny ap_v1 > run1.log

# Modification SAI-A107

# Run 2 (test)
./scripts/a108_eprouver_agent_personne.sh cours4 tiny ap_v1 > run2.log

# Comparer
diff run1.log run2.log
```

### 4. Documenter les Résultats

```json
{
  "date": "2026-02-10",
  "agent_personne_id": "ap_cours4_v1",
  "version": "v2",
  "arene": "cours4_tiny_planification",
  "resultats": {
    "taux_survie": 0.9,
    "score_moyen": 32.5,
    "longueur_moyenne": 7.8
  },
  "decision": "Prêt pour compétition",
  "notes": [
    "Excellente survie",
    "Score supérieur à MPC baseline",
    "Têtes activées correctement"
  ]
}
```

### 5. Archiver les Runs de Qualification

Les runs SAI-A108 qui mènent à une qualification doivent être conservés :

```
artefacts/runs/
  ├── 2026-02-10_14h35_qualification_ap_v1/
  └── 2026-02-10_16h22_qualification_ap_v2/
```

---

## Pièges à Éviter

### 1. Sur-optimiser pour l'Épreuve

❌ **Mauvais :**
```
Agent parfait sur arène de test (seed 123)
Agent échoue sur arène similaire (seed 456)
→ Overfitting sur la configuration de test
```

✅ **Bon :**
Tester sur plusieurs seeds et configurations.

### 2. Ignorer les Métriques Intermédiaires

❌ **Mauvais :**
```
Score final : 40 → "Excellent !"
(mais 80% du score en 5 premiers ticks, puis stagnation)
```

✅ **Bon :**
Analyser la trajectoire complète du score.

### 3. Confondre Survie et Performance

❌ **Mauvais :**
```
Agent survit 100% du temps
Mais score = 8 (juste meilleur qu'aléatoire)
→ Agent trop défensif
```

✅ **Bon :**
Balance survie ET score.

### 4. Tester trop Peu

❌ **Mauvais :**
```
1 épisode → succès → "Prêt !"
```

✅ **Bon :**
Minimum 5 épisodes pour détecter variance.

---

## Automatisation du Cycle

### Script de Qualification Complet

```bash
#!/bin/bash
# qualification_complete.sh

EXPERIENCE="cours4"
AGENT_ID="ap_cours4_v1"

echo "=== Qualification $AGENT_ID ==="

# 1. Épreuve standard
echo "1. Épreuve standard..."
./scripts/a108_eprouver_agent_personne.sh $EXPERIENCE cours4_tiny_planification $AGENT_ID 10 100 123 > standard.log

# 2. Épreuve robustesse (seeds variés)
echo "2. Épreuve robustesse..."
for seed in 100 200 300; do
  PYTHONPATH=services python -m ui_cli.app.main \
    --experience $EXPERIENCE \
    --agent agent_personne \
    --agent-personne-id $AGENT_ID \
    --episodes 5 \
    --seed $seed >> robustesse.log
done

# 3. Analyse
echo "3. Analyse des résultats..."
python analyze_qualification.py standard.log robustesse.log

# 4. Décision
if grep -q "QUALIFICATION: RÉUSSIE" analyze_results.txt; then
  echo "✓ Agent prêt pour compétition"
  exit 0
else
  echo "✗ Retour en SAI-A107 requis"
  exit 1
fi
```

---

## Lien avec SAI-B (Compétition)

### Différences

| SAI-A108 (Épreuve) | SAI-B (Compétition) |
|--------------------|---------------------|
| Environnement connu | Peut être nouveau |
| Seed fixe | Seed aléatoire |
| Épisodes limités | Nombreux matchs |
| Feedback détaillé | Score final seulement |
| Itération permise | Pas de modifications |

### Préparation

SAI-A108 simule les conditions de SAI-B :

```
Épreuve de qualification = Dress rehearsal
  → Si échec ici → échec assuré en compétition
  → Si succès ici → succès probable en compétition
```

---

## Conclusion

**SAI-A108** est l'activité de **validation finale**.

Elle transforme :
- Un agent-personne préparé (artefact)
- En agent qualifié (ou non) pour la compétition
- Via des tests objectifs et reproductibles
- Avec des critères de décision clairs

C'est le **contrôle qualité** avant production :
- ✓ Les têtes fonctionnent-elles ?
- ✓ La gouvernance est-elle cohérente ?
- ✓ La performance est-elle acceptable ?
- ✓ Le comportement est-il stable ?

SAI-A108 répond à la question :  
**"Ai-je confiance pour mettre cet agent en compétition ?"**

Sans SAI-A108, on envoie un agent au combat sans savoir s'il est prêt.  
Avec SAI-A108, on a des **preuves objectives** de sa capacité.

C'est la différence entre **espérer** que ça marche et **savoir** que ça marche.
