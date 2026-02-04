# Structure du projet

> note : les dossiers suivent la convention **snake_case** (ex. `world_sim`).

Le projet est organisé autour d’un principe central : **la séparation stricte entre le code, les configurations d’expérience et les artefacts produits**.

À partir du **cours 4**, la notion de **bac-à-sable d’expérience** structure explicitement cette séparation et devient le support principal de reproductibilité.

---

## vue d’ensemble

```
.
├── services/                # code exécutable (simulateur, agents, outils)
├── donnees/config/          # configurations déclaratives (YAML)
├── docs/                    # documentation conceptuelle et pédagogique
├── artefacts/               # sorties globales (héritage / historique)
├── scripts/                 # scripts utilitaires (dev, replay, archivage)
└── tmp/                     # fichiers temporaires
```

---

## services — code applicatif

Le code est structuré par **rôles fonctionnels**, pas par technologies.

- `services/world_sim/`
  - simulateur du monde Snake
  - interprétation des arènes YAML
  - dynamique du monde (collisions, récompenses, capteurs)

- `services/agent_service/`
  - agents décisionnels (politiques, planification, curiosité)
  - world models (tabulaires, latents, simulateur interne)
  - recoders, diagnostics, APK épistémiques

- `services/commun/`
  - contrats partagés
  - bus d’événements
  - mécanismes de contrôle communs

- `services/runner/`
  - orchestration d’épisodes
  - relecture (`replay`)
  - journalisation des événements

- `services/ui_cli/`
  - interface ligne de commande (mode headless)
  - point d’entrée principal pour la génération d’épisodes
  - gestion des **bacs-à-sable d’expérience**

- `services/ui_tui/`
  - interface texte interactive (TUI)
  - visualisation live et relecture

- `services/ui_web/` *(prévu)*
  - interface web (non implémentée à ce stade)

---

## donnees/config — configurations déclaratives

Les configurations sont **des données**, jamais du code.

```
donnees/config/
├── arenes/                  # descriptions YAML des mondes
└── experiences/             # bacs-à-sable d’expérience
```

### arènes

- grilles
- objets
- règles implicites
- récompenses

Les arènes sont **indépendantes des agents**.

### expériences (bacs-à-sable)

Chaque expérience est un dossier autonome :

```
donnees/config/experiences/<id>/
├── experience.yml           # description de l’expérience
├── README.md                # intention expérimentale
└── artefacts/               # sorties liées à cette expérience
```

Le fichier `experience.yml` décrit :
- l’arène
- l’agent
- la représentation latente
- les paramètres de génération
- les journaux d’entrée éventuels

Il sert de **contrat commun** à l’ensemble des outils.

---

## artefacts — sorties expérimentales

À partir du cours 4, les artefacts sont **prioritairement stockés dans les bacs-à-sable**.

```
artefacts/
├── runs/          # exécutions ui_cli (journaux + métriques)
├── datasets/      # journaux recodés
├── diagnostics/   # rapports d’analyse
├── registres/     # connaissances épistémiques (APK)
└── notes/
```

> le dossier `artefacts/` à la racine du projet subsiste à des fins
> historiques ou exploratoires, mais n’est plus le chemin recommandé.

---

## docs — documentation

- `docs/world_models/` : cours progressifs (1 → 4)
- `docs/architecture.md` : architecture globale
- `docs/structure.md` : ce document
- `docs/spec_snake_world_model.md` : spécification du world model

La documentation est pensée comme **support pédagogique et conceptuel**,
au même titre que le code.

---

## philosophie générale

- le code décrit **ce qui est possible**
- les configurations décrivent **ce qui est expérimenté**
- les artefacts décrivent **ce qui s’est effectivement produit**

Le bac-à-sable d’expérience est le point de convergence de ces trois niveaux.

Il permet de raisonner en **expériences reproductibles**,
plutôt qu’en exécutions isolées.

