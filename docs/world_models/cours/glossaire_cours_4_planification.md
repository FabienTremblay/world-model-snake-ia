# Glossaire – Cours 4 : imagination, incertitude et planification

Ce glossaire introduit et stabilise le vocabulaire conceptuel utilisé à partir du **Cours 4**.  
Il vise à éviter toute confusion entre les notions issues de l’apprentissage contrastif (Cours 3) et celles propres à la décision, à l’imagination et à la planification.

---

## 1. Positif / négatif (contrastif)

**Contexte** : apprentissage contrastif du monde interne (Cours 3).

- **Positif (contrastif)** : le futur latent réellement observé `z_{t+1}` pour une transition `(z_t, a_t)`.
- **Négatif (contrastif)** : les autres futurs latents du batch, utilisés comme contre-exemples.

> Positif et négatif ne qualifient **ni la valeur**, ni la désirabilité, ni le danger d’un futur, mais uniquement son **rôle discriminant** dans l’apprentissage.

Un futur catastrophique peut parfaitement être un *positif contrastif* s’il est le futur réel observé.

---

## 2. Connu / inconnu

**Contexte** : modèle du monde tabulaire appris offline.

- **Transition connue** : une transition `(z, a → z')` présente dans le journal, avec un support strictement positif.
- **Transition inconnue** : une transition absente du journal, ou dont le support est nul ou trop faible.

L’inconnu n’est **pas** une erreur du modèle :
- il révèle une **absence d’information**,
- il signale une **zone non explorée** du monde.

---

## 3. Favorable / défavorable (planification)

**Contexte** : imagination et planification (Cours 4).

Ces termes introduisent une **évaluation normative**, absente du Cours 3.

- **Futur favorable** : futur associé à une espérance de récompense positive ou à une survie prolongée.
- **Futur défavorable** : futur associé à une pénalité, un coût élevé ou une terminaison probable.

Cette distinction repose sur :
- les modèles de récompense,
- les modèles de terminaison,
- les coûts de vie (par pas).

---

## 4. Incertitude

**Définition** : situation où plusieurs futurs sont possibles pour une même transition `(z, a)`.

Dans ce projet, l’incertitude émerge de manière **non probabiliste explicite**, via :
- la multiplicité des transitions observées,
- l’entropie de la distribution tabulaire,
- la faiblesse du support.

L’incertitude n’est pas un défaut :
> elle est une propriété structurelle du monde appris.

---

## 5. Risque

**Définition** : incertitude associée à des conséquences négatives identifiées.

Exemples :
- probabilité de terminaison non nulle,
- pénalité de fin,
- perte certaine de score.

Un futur peut être :
- **connu et risqué**,
- **inconnu mais potentiellement favorable**.

---

## 6. Espoir

**Définition** : valeur accordée à un futur incertain lorsqu’aucun futur connu favorable n’existe.

L’espoir n’est pas une croyance naïve :
> c’est une stratégie rationnelle face à un connu défavorable.

Un agent rationnel peut préférer :
- un futur inconnu
- à un futur connu et catastrophique.

---

## 7. Curiosité

**Définition** : paramètre de tempérament qui module l’attirance de l’agent pour l’inconnu.

La curiosité influence :
- la pondération de l’inconnu,
- l’acceptation du risque,
- la tolérance à l’absence d’information.

Elle ne crée pas l’exploration, mais **oriente l’arbitrage** entre sécurité et découverte.

---

## 8. Tempérament de l’agent

Le tempérament est un **méta-paramètre décisionnel**, distinct du monde interne.

Exemples de tempéraments :
- **prudent** : privilégie les transitions connues et sûres,
- **audacieux** : accepte l’inconnu face au risque,
- **curieux** : valorise les zones peu couvertes,
- **conservateur** : pénalise fortement l’incertitude.

Le tempérament agit **sur la planification**, pas sur l’apprentissage du monde.

---

## 9. Principe de dominance décisionnelle

Règle centrale du Cours 4 :

> Un agent rationnel préfère :  
> 1. un futur connu favorable  
> 2. un futur inconnu  
> 3. un futur connu défavorable

Cette règle fonde l’arbitrage entre exploitation, prudence et exploration.

---

## 10. Séparation des rôles

| Élément | Rôle |
|------|------|
| Monde interne | Décrit ce qui peut arriver |
| Incertitude | Indique ce qui est mal connu |
| Planification | Évalue ce qui est souhaitable |
| Tempérament | Oriente les choix sous incertitude |

---

**Note pédagogique**  
Ce glossaire évoluera avec les expériences du Cours 4.  
Il constitue une base conceptuelle stable, mais non figée.