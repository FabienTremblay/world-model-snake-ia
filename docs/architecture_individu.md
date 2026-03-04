# Architecture — individu transportable, monde événementiel, traçabilité

## Intention

L'agent en arène doit être un **individu isolé** (comme un cerveau qui meurt avec l'individu) :

- identité propre
- politique (tronc/têtes à venir)
- mémoires (courte/longue)
- poids / réseaux
- gabarits nécessaires à sa reproduction éventuelle

Rien d'essentiel à l'individu ne doit vivre ailleurs que dans sa structure transportable.

## Trois couches

### 1) catalogue (état courant)
- `donnees/catalogues/familles/`
- `donnees/catalogues/individus/`

Contient les définitions transportables et l'état courant des individus.

### 2) runs (vérité expérimentale)
- `donnees/config/experiences/<id>/artefacts/runs/<run>/`

Chaque run est une observation, avec snapshots et lineage.

### 3) monde (simulation)
Le monde avance par ticks et collecte/publie des événements.

## Flux canonique

catalogue → run (snapshot entrée) → monde → événements → évolution (entraînement) → snapshot sortie → promotion optionnelle
