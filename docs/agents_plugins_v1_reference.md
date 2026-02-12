# Agents Plug-ins v1 — Référence technique

## Objectif
Normaliser la définition et l’instanciation des agents via un mécanisme
de plug-ins déclaratifs basés sur YAML.

Le catalogue d’agents est désormais data-driven.

---

## Arborescence attendue

services/agent_service/app/agents/
    aleatoire/
        agent.yml
    planif_mpc_tabulaire/
        agent.yml
    snake_collectif_v1/
        agent_c1.yml
        agent_c2.yml

Seuls les fichiers agent*.yml dans ce répertoire sont découverts.

---

## Contrat minimal agent.yml

version: 1
id: planif_mpc_tabulaire
fabrique: agent_service.app.agents._infra.fabriques_catalogue_v1:fabriquer_planif_mpc_tabulaire
params_requis:
  - SNAKE_MODELE_JOURNAL

### Champs

- version : version du schéma
- id : identifiant unique du type d’agent
- fabrique : module:callable
- params_requis : liste optionnelle de paramètres requis

---

## API stricte

creer_agent(id: str, params: dict)

Aucun kwargs supplémentaire n’est autorisé.

---

## Règles de prérequis

Un paramètre requis peut être satisfait via :
1. params
2. variable d’environnement

Sinon, exception explicite.

---

## Garanties via tests

Les tests valident :
- YAML parseable
- Fabriques importables
- Agents instanciables si prérequis satisfaits
- API stricte

---

## Erreurs typiques

- ModuleNotFoundError → chemin fabrique incorrect
- ParserError YAML → indentation invalide
- OSError → variable d’environnement manquante
