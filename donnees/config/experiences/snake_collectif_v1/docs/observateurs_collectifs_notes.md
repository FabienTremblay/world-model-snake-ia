# Observateurs épistémiques collectifs — notes de conception

Date: 2026-02-12

## Intuition

On veut éviter de "coder dur" une liste de concepts sémantiques.
À la place, on multiplie les **observateurs** avec des biais/"instincts" différents,
qui produisent des **propositions** et convergent vers une **convention**.

L'agent en arène ne "voit" pas sa mort (il n'est plus). L'observateur, lui,
constate la **terminalité** et produit un signal répulsif.

## Opérateurs épistémiques (moteurs de concepts)

1. **Rupture (surprise)** : l'état suivant observé n'est pas celui attendu.
2. **Régularité (invariance)** : transition quasi déterministe (proto-loi).
3. **Similarité / compression** : deux états différents se comportent pareil.
4. **Contraste** : états proches → issues très différentes (variable manquante).
5. **Saillance** : événement dominant statistiquement.
6. **Rareté** : événements rares mais structurants.

## Multiplicité d'observateurs

### O1 — Surprise de transition
- Entrée: metrics.jsonl (checksum_avant, checksum, action)
- Produit: `surprise_transition`

### O2 — Invariances / diagnostic (epistemique_v2)
- Entrée: registre_epistemique_v2.json (issu d'epistemique_v2)
- Produit: `transition_dominante`, `indices`, `hypothese_macro`

### O3 — Similarité
- À faire plus tard : clustering sur profils de transitions et politiques empiriques.

### O4 — Contraste / split de régime
- À faire plus tard : détecter (etat,action) multi-modaux, ou contradictions inter-observateurs.

### O5 — Terminalité
- Déjà implicite via segmentation d'épisodes + `raison_fin` si disponible.

## Convention et échanges

Les observateurs n'échangent pas des opinions, mais des **propositions**:

- type
- cible
- hypothese
- preuve
- support
- confiance
- observateur_id / run_dir

### Conventionneur (v1)
- Dédoublonne sur (type, cible, hypothese)
- Fusionne support
- Confiance pondérée par support
- Trace les observateurs contributeurs

## Pipeline opérable (v1)

1) Générer le registre epistemique_v2 (déjà existant)

2) O1 Surprise → JSONL

3) O2 Transform → JSONL

4) Conventionneur → registre collectif

## Questions ouvertes

- Quelles têtes (SAI-A107) consomment quels types de propositions ?
- Doit-on distinguer "instincts" (veto) vs "préférences" (soft) ?
- Quelle temporalité: tick local vs agrégats par épisode ?

