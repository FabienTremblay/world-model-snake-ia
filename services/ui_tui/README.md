# ui_tui — TUI d'expérimentation

But : offrir un **instrument** pour l'expérimentateur :

- **commande manuelle** : jouer des épisodes au clavier (humain = agent)
- **replay** : relire un journal d'épisodes (pas-à-pas, play/pause, stats)
- (à venir) **édition d'épisode** : rejouer / tronquer / annoter / sauvegarder

## lancer

Depuis la racine du projet :

```bash
export PYTHONPATH=services
python -m ui_tui.app.main
```

Accès direct (sans menu) :

```bash
python -m ui_tui.app.main --mode manual
python -m ui_tui.app.main --mode replay --journal artefacts/episodes.jsonl
```

Variables utiles :

- `SNAKE_ARENE` : nom de l'arène
- `SNAKE_AGENT` : nom de l'agent (si vide → mode manuel)
- `SNAKE_JOURNAL_PATH` : chemin du journal pour replay (alternative à --journal)

## philosophie

- Le TUI **ne contient aucune logique métier** : il projette (affiche) et relaie des commandes.
- Live et replay passent par le même contrat `SourceEpisode`.


## menu

Le menu guide la configuration:

1. domaine: live / replay
2. bac à sable (optionnel): choisir une expérience sous donnees/config/experiences
3. live: choisir l'arène (donnees/config/arenes/*.yml)
   replay: choisir le journal (artefacts ou runs du bac)
4. lancer la session


### règle de priorité bac à sable

Si un bac à sable (expérience) est choisi, ses paramètres (arène, agent, latent, etc.) ont priorité et **ne sont pas modifiables** depuis le menu TUI. Le menu d'édition du bac viendra plus tard.


## présentation de la situation

Après configuration (menu), le TUI affiche un écran **Situation** qui résume la configuration effective (env final, arène imposée par le bac, journal, run dir). C'est seulement après cette étape qu'on démarrera la session et qu'on branchera les actions manuelles.
