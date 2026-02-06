# bac à sable — expérience

Ce répertoire est créé automatiquement par `ui_cli` lorsqu'une nouvelle expérience est détectée.

- `experience.yml` : paramètres et conventions du bac à sable
- `artefacts/` : sorties produites par les exécutions
  - `runs/` : exécutions horodatées (journaux + stdout éventuel)
  - `datasets/` : journaux stabilisés (train/eval/mix)
  - `diagnostics/` : sorties sauvegardées des diagnostics (optionnel)
  - `registres/` : registres épistémiques (APK)
  - `notes/` : observations humaines

Tu peux remplacer ce README par celui du template si tu veux une description complète.


## modèle monde

`ui_cli` lit `experience.yml` (section `modele_monde`) et exporte automatiquement :

- `SNAKE_MODELE_JOURNAL` (chemin absolu)
- `SNAKE_CHAMP_LATENT`

Il écrit aussi un événement JSON sur stdout : `{"event":"modele_monde_resolu", ...}`.

Si le journal déclaré n'existe pas, l'exécution échoue immédiatement avec un message explicite.
