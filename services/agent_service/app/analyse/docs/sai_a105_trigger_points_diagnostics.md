# SAI-A105 — Trigger points pour réviser les diagnostics (logique, préconditions, seuils)

Version : 2026-02-28  
Portée : mécanisme **services/agent_service/app/analyse/** (catalogue + CLI + diagnostics)

Ce document sert de “check-list” : quand un des signaux ci-dessous apparaît, **on doit revisiter** (a) la logique des diagnostics, (b) les préconditions déclarées, et/ou (c) les seuils/epsilons d’alerte.

---

## 0) Principe directeur

Un diagnostic SAI-A105 est **généralisé** : il vise à répondre à des questions de pilotage (“est‑ce que ça fonctionne / est‑ce que ça dégénère ?”) sans dépendre d’un détail fragile de l’implémentation.

Donc : on ne révise pas un diagnostic parce qu’on a “changé un champ interne sans impact”, on le révise quand **la sémantique observable** (ou le contrat d’artefacts) change.

---

## 1) Triggers “contrat de données” (cassures du pipeline)

### 1.1 Changement de schéma du journal ou du registre
Déclencheurs typiques :
- Le champ qui porte le *mode* (connu/inconnu) change de nom, ou sa sémantique change.
- Les champs `surprise` / `disagree` changent de nom, disparaissent, ou changent d’échelle (normalisation, clipping, quantification).
- Les seuils (`seuil_surprise`, `seuil_disagree`) ne sont plus présents dans le journal, deviennent tick‑level, ou viennent d’une autre source.

Conséquence attendue côté diagnostic :
- Passage en `skip` (préconditions non satisfaites) OU
- ratios incohérents (ex : la décomposition ne somme plus à `ratio_inconnu_total`).

Action :
- Mettre à jour `preconditions()` + résolution de chemins + lecture d’artefacts.
- Ajouter un fallback explicite si la donnée migre (ex : seuils déplacés du journal vers `config_epreuve.json`).

### 1.2 Migration des artefacts / chemins
Déclencheurs :
- déplacement des artefacts (ex : `epreuve/` renommé, ou fichiers déplacés).
- le run fourni au CLI peut être racine de runs, et la règle “dernier run” change.

Action :
- Ajuster `resoudre_run_dir()` et les heuristiques de `lecture_artefacts.py`.
- Ajouter un test “smoke” qui valide la résolution sur un run et sur une racine.

---

## 2) Triggers “sémantique” (catégories qui changent)

### 2.1 Passage exclusif ↔ non‑exclusif (intersection)
Si la définition de l’inconnu change :
- **exclusive** : un tick inconnu est attribué à une seule cause (surprise OU désaccord)
- **non‑exclusive** : un tick peut être à la fois surprise ET désaccord (intersection)

Signal :
- l’intersection `ratio_inconnu_surprise_et_disagree` devient non‑nulle de façon systématique (ou, inversement, passe à 0 partout).

Action :
- Documenter la règle (priorité, séquence, arbitration).
- Versionner le diagnostic (ex : `diag.gate_partition.v2`) si la sortie machine ou l’interprétation change.

### 2.2 Ajout d’une 3e cause d’inconnu (ou plus)
Exemples : inconfiance, nouveauté, erreur modèle, inconnus “autres”.
Signal :
- `ratio_inconnu_autre` devient non‑nul de façon stable, ou on ajoute un nouveau signal.

Action :
- Ajouter une catégorie explicite (et un champ de sortie stable).
- Mettre à jour la doc longue (TUI) : “ce que mesure le diagnostic” + “ce que ça ne mesure pas”.

---

## 3) Triggers “divergence registre vs tick-level” (sanity check)

Le journal (tick-level) est la **source de vérité**. Le registre est une agrégation (fenêtre, filtrage, définition).

Signal :
- un ou plusieurs `delta_*` (tick-level – registre) dépasse l’epsilon (`epsilon_delta_registre`, ex 0.01).

Exemple : sur ton run actuel, le registre ne fournit qu’un seul ratio comparable (`ratio_inconnu_total`) et le delta est 0 — c’est bon. fileciteturn6file0

Causes possibles :
- fenêtre différente (ticks filtrés, sous-échantillonnage).
- définition différente (exclusive vs “any”, intersection incluse/exclue).
- bug de calcul dans le registre.

Action :
- si différence voulue : **documenter** précisément la différence (et idéalement exposer “fenêtre/filtre” dans le registre).
- sinon : corriger le registre ou le diagnostic (mais garder un champ de sortie stable).

---

## 4) Triggers “seuils non informatifs / pathologies statistiques”

### 4.1 Plateau / clipping / quantification
Signal :
- `q90 == q95 == q99 == max` et/ou masse importante au max.
- seuil = max (seuil peu informatif).

Exemple : ton `diag.disagree_plateau.v1` détecte exactement cette pathologie (plateau + seuil=max). fileciteturn6file0

Action :
- revoir la stratégie de seuil (quantile robuste, percentile sur valeurs uniques, histogramme, seuil fixe).
- vérifier l’origine : clipping, quantification, type float→int, arrondi.

### 4.2 Dominance d’un poids adaptatif (gate/poids)
Signal :
- `ratio(w_k > 0.7)` très élevé sur une longue fenêtre, ou std très faible → dégénérescence.

Exemple : `diag.poids_adaptatifs.v1` signale une dominance de `w2` (≈ 0.981 des ticks > 0.7). fileciteturn6file0

Action :
- revoir le calibrage (temperature, EMA, alpha) et l’échelle des signaux.
- éventuellement durcir/assouplir les seuils d’alerte **en les versionnant** (pour éviter de “casser” l’interprétation historique).

---

## 5) Triggers “objectif d’usage” (passage de diagnostic informatif → décisionnel)

Quand tu commences à utiliser les diagnostics comme critères de campagne (stop/continue, alerte d’exploration, gating automatique), il faut revisiter :

- la tolérance aux faux positifs / faux négatifs,
- la stabilité des seuils selon la taille de run,
- la comparabilité inter-runs (normalisation, durée, seeds).

Signal :
- tu constates des alertes fréquentes mais “non utiles” (faux positifs),
- ou tu détectes des échecs réels sans alerte (faux négatifs).

Action :
- calibrer les seuils sur une matrice de runs “bons” vs “mauvais”.
- introduire des métriques robustes (quantiles, médianes, histogrammes) et versionner.

---

## 6) Triggers “maintenance” (versionnage et compatibilité)

On doit versionner un diagnostic (ex : `...v2`) si :
- la **sémantique** d’une métrique change (même nom, autre sens),
- la structure de sortie change (champs supprimés/renommés),
- l’interprétation recommandée change (quoi_faire différent pour la même alerte).

On peut rester en v1 si :
- on ajoute uniquement des champs nouveaux (backward compatible),
- on améliore la doc,
- on rend la lecture d’artefacts plus robuste sans changer la signification.

---

## Où déposer ce document

Recommandé :
- `services/agent_service/app/analyse/docs/TRIGGER_POINTS_DIAGNOSTICS.md`

Alternative (si tu veux centraliser la doc “contrat” SAI-A105) :
- `donnees/config/experiences/JEPA-5/rapports/sai_a105_trigger_points.md`

---

## Résumé opérationnel

Réviser un diagnostic quand :
1) le **contrat d’artefacts** bouge (schéma/chemins),  
2) la **définition des catégories** bouge (exclusive vs intersection, nouvelle cause),  
3) le **registre diverge** du tick-level au-delà d’un epsilon,  
4) les **seuils deviennent non informatifs** (plateau/dominance),  
5) l’usage devient **décisionnel** (calibrage + versionnage).
