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

> ⚠️ **Attention terminologique (Cours 4)** : ces termes ne doivent jamais être confondus avec *favorable / défavorable* ou *bonne / mauvaise expérience*, qui relèvent de l’évaluation par un observateur.

---

## 2. Connu / inconnu

**Contexte** : modèle du monde tabulaire appris offline.

- **Transition connue** : une transition `(z, a → z')` présente dans le journal, avec un support strictement positif.
- **Transition inconnue** : une transition absente du journal, ou dont le support est nul ou trop faible.

L’inconnu n’est **pas** une erreur du modèle :
- il révèle une **absence d’information**,
- il signale une **zone non explorée** du monde.

> L’inconnu n’a **aucune valence intrinsèque** : il peut devenir favorable, défavorable ou porteur d’espoir selon l’expérience ultérieure.

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

> Elle constitue la **matière première** de la planification et de l’imagination.

---

## 5. Risque

**Définition** : incertitude associée à des conséquences négatives identifiées.

Exemples :
- probabilité de terminaison non nulle,
- pénalité de fin,
- perte certaine de score ou de survie.

Un futur peut être :
- **connu et risqué**,
- **inconnu mais potentiellement favorable**.

> Le risque n’existe que relativement à un **observateur** et à ce qu’il considère comme une mauvaise conséquence.

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

**Définition** : paramètre de tempérament qui module l’attirance de l’agent pour l’inconnu ou pour des signaux encore mal expliqués.

La curiosité influence :
- la pondération de l’inconnu,
- l’acceptation du risque,
- la propension à déclencher des **enquêtes** ou **expéditions**.

Elle ne crée pas l’exploration par hasard, mais **oriente l’attention vers des signaux jugés intéressants**.

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
| Signaux de transition | Changements émis par l’environnement |
| Observateur | Sélectionne et interprète les signaux |
| Connaissance | Régularités découvertes par expérience |
| Ontologie | Concepts et relations stabilisés |
| Planification | Évalue ce qui est souhaitable |
| Tempérament | Oriente les choix sous incertitude |

---

## 11. Signal de transition

**Définition** : modification émise par l’environnement lors d’une transition, avant toute interprétation.

Exemples :
- variation de longueur,
- variation de score,
- apparition ou disparition d’un objet,
- terminaison de l’épisode.

Le signal est **amoral et non sémantique** : il n’est ni bon ni mauvais.

---

## 12. Observateur

**Définition** : entité (conceptuelle ou logicielle) qui :
- détecte certains signaux,
- les considère comme dignes d’attention,
- cherche à en comprendre les effets par l’expérience ou l’échange.

Différents observateurs peuvent coexister et produire des évaluations divergentes d’une même trajectoire.

---

## 13. Enquête / expédition

- **Enquête** : processus par lequel un observateur cherche à établir une relation causale à partir de signaux répétés.
- **Expédition** : comportement dirigé visant à provoquer ou reproduire des signaux afin de réduire l’incertitude.

Ces notions introduisent une **curiosité structurée**, distincte de l’exploration aléatoire.

---

**Note pédagogique**  
Ce glossaire reflète la vision du Cours 4 : la valeur n’est pas donnée par le monde, elle est **construite par l’expérience et l’observation**.
