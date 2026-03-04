# Migration — Individu (transportable) + Monde événementiel (E/F) — v2

Date : 2026-03-04

Ce patch conserve la logique suivante (statu quo : pas de restructuration globale du dépôt ici) :

- Ajout de `donnees/catalogues/{familles,individus}`
- Ajout de `donnees/schemas/` (spécifications yaml)
- Ajout d'un bus d'événements et d'un runner événementiel **nouveau** (à brancher ensuite)

## Décisions intégrées

1) **R2 autonome**  
Un individu transporte :
- son `famille_id`
- **un ou plusieurs gabarits embarqués** (copie locale du gabarit) pour reproduction future sans dépendance.

2) **Inaction**  
L'inaction n'est pas un événement.  
C'est l'absence d'émission d'événements d'action (inférable à l'analyse).

3) **Objets du monde**  
- Instruments : objets du monde passifs ou actifs.  
  *S'ils sont actifs, ils résolvent eux-mêmes et publient leurs événements.*
- Individu (agent) : objet du monde passif ou actif.

4) **Deux modes**  
- entraînement : **Architecture E (pull)** — le monde collecte les événements des objets actifs au tick.
- épreuve : **Architecture F (push)** — les objets publient sur le bus; le runner publie seulement `tick_annonce`/`tick_survenu` si activé.

## Application

```bash
unzip -o snakeai_patch_individu_evenements_v2.zip -d .
```

## Intégration (prochaine étape)

- Brancher ce runner sur le monde existant.
- Faire du monde l'orchestrateur des objets (E) ou l'abonné du bus (F).
