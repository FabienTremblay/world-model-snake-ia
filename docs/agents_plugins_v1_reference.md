# agents plug-ins v1 — référence technique

ce document complète la documentation existante. il ne remplace rien.

## objectif

normaliser la définition et l’instanciation des agents via un catalogue déclaratif basé sur yaml.

## arborescence attendue

```
services/agent_service/app/agents/
    <agent_id>/
        agent.yml
    <famille>/
        agent_c1.yml
        agent_c2.yml
```

seuls les fichiers `agent*.yml` dans ce répertoire sont découverts.

## contrat minimal `agent.yml`

```yaml
version: 1
id: aleatoire
fabrique: agent_service.app.agents._infra.fabriques_catalogue_v1:fabriquer_aleatoire
params_requis: []
```

### champs

- `version` : version du schéma (actuellement `1`)
- `id` : identifiant unique du type d’agent (utilisé par `--agent <id>`)
- `fabrique` : chaîne `module:callable` importable (ex. `pkg.mod:fonction`)
- `params_requis` : liste optionnelle de noms (env/params) requis

## discovery

le catalogue scanne :

- `services/agent_service/app/agents/**/agent*.yml`

il ne doit pas scanner :
- `incarnations/`
- `donnees/config/experiences/` (ce sont des bacs-à-sable, pas des types)

## api stricte

```python
creer_agent(id: str, params: dict) -> object
```

- pas de kwargs
- `params` est un dictionnaire libre transmis à la fabrique

## prérequis

certains agents dépendent de ressources externes (ex. journal d’entraînement).

norme :
- la fabrique (ou l’agent) doit refuser explicitement si les prérequis sont absents
- les prérequis sont satisfaits via :
  - `params`
  - ou variables d’environnement (ex. `SNAKE_MODELE_JOURNAL`)

## tests

garanties minimales :
- tous les `agent*.yml` sont parseables
- toutes les fabriques sont importables
- les agents “sans prérequis” sont instanciables avec `params={}`
- les agents “avec prérequis” refusent sans env et passent avec env
- l’api stricte refuse les kwargs
