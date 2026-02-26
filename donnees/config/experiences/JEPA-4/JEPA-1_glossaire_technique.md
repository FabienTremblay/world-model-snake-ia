
# JEPA-1 — Glossaire des termes techniques et lecture des statistiques

_Date de génération : 2026-02-22 19:28_

---

# 1️⃣ Termes liés à l’entraînement

## Epoch

Une **epoch** correspond à un passage complet sur l’ensemble du dataset.

Exemple :
Si le dataset contient 4969 paires et que l’on entraîne pendant 5 epochs,
cela signifie que le modèle a vu 5 fois l’ensemble des 4969 exemples.

---

## Batch size

Le **batch size** est le nombre d’exemples utilisés avant de mettre à jour les poids du réseau.

Exemple :
Batch size = 128 signifie que le modèle traite 128 paires,
calcule l’erreur moyenne,
met à jour ses poids,
puis passe aux 128 suivantes.

---

## Learning rate (lr)

Le **learning rate** contrôle l’amplitude des mises à jour des poids.

- Trop grand → instabilité
- Trop petit → apprentissage lent

---

# 2️⃣ Termes liés à l’erreur et à la surprise

## MSE (Mean Squared Error)

La **MSE** est la moyenne des carrés des différences entre prédiction et réalité.

Formule simplifiée :

MSE = moyenne( (prediction - observation)^2 )

Plus la MSE est petite, plus la prédiction est proche de la réalité.

Dans JEPA-1, la MSE correspond à la **surprise**.

---

## Surprise

La surprise est la MSE calculée pour un exemple donné.

Surprise faible → situation connue  
Surprise élevée → situation inattendue  

---

# 3️⃣ Lecture des statistiques

Les statistiques sont calculées sur l’ensemble des valeurs de surprise.

Exemple typique :

mean = 0.00165  
std = 0.00050  
min = 0.00111  
max = 0.00306  

---

## Mean (moyenne)

La **mean** est la moyenne arithmétique des valeurs.

Elle représente la surprise moyenne globale.

---

## Standard deviation (std)

La **std** mesure la dispersion autour de la moyenne.

- Petite std → valeurs concentrées
- Grande std → valeurs étalées

Si mean = 0.00165 et std = 0.00050,
alors la plupart des valeurs se situent approximativement dans :

0.00165 ± 0.00050

---

## Min / Max

- **min** : plus petite valeur observée
- **max** : plus grande valeur observée

---

# 4️⃣ Quantiles (px)

Nous utilisons la notation **pX** pour les quantiles.

Exemple :
p90 signifie 90ᵉ centile.

Un quantile pX indique que X % des valeurs sont inférieures ou égales à cette valeur.

Exemples :

p50 = médiane  
→ 50 % des valeurs sont en dessous

p90  
→ 90 % des valeurs sont en dessous  
→ 10 % sont au-dessus

p99  
→ 99 % des valeurs sont en dessous  
→ 1 % sont au-dessus

---

## Interprétation dans JEPA-1

Si le gate est calibré avec :

quantile = 0.9

Cela signifie :

Le seuil_connu est fixé au p90.

Donc :
- 90 % des situations sont considérées connues
- 10 % sont considérées surprenantes

---

# 5️⃣ Lecture pratique complète

Exemple :

mean = 0.00165  
std = 0.00050  
p90 = 0.00265  

Interprétation :

La surprise moyenne est faible (≈ 0.00165).  
La plupart des cas sont proches de cette valeur.  
Les 10 % les plus surprenants dépassent 0.00265.  

Le système classera donc environ 10 % des cas comme « inconnu ».  

---

# 6️⃣ Résumé visuel

Distribution simplifiée :

faible surprise → majorité des cas  
moyenne surprise → zone normale  
forte surprise → extrémité de distribution (queue)  

Le quantile permet de définir objectivement la frontière entre ces zones.

---

# 🎯 Conclusion

Les statistiques utilisées dans JEPA-1 permettent :

- de mesurer la qualité de la prédiction
- de calibrer objectivement la frontière connu / inconnu
- de transformer une erreur numérique en décision comportementale

