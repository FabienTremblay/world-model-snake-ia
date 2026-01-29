# cours 4 — world models  
*(modèles du monde internes)*

> Objectif pédagogique : comprendre **pourquoi** et **comment** un agent construit un modèle interne du monde,  
> et ce qui se passe quand ce modèle est trop pauvre, trop rigide ou mal aligné avec la réalité.

Ce cours s’appuie sur les expérimentations réalisées avec l’arène `cours4_tiny_planification` et les journaux JSONL produits par le moteur.

---

## 1. rappel : agent, environnement et perception

Un agent n’interagit jamais directement avec le monde réel.

Il interagit avec :
- des **observations** (capteurs),
- un **état interne**,
- une **fonction de décision** qui choisit une action.

Entre le monde et l’action, il existe donc toujours une médiation :  
👉 **le modèle interne du monde**.

---

## 2. qu’est-ce qu’un world model ?

Un *world model* est une représentation interne qui permet à l’agent de répondre à des questions implicites comme :

- « si je fais cette action, que va-t-il probablement se passer ? »
- « quelles situations sont dangereuses ? »
- « quelles trajectoires sont plausibles ? »

Ce modèle peut être :
- **explicite** (symbolique, tabulaire, règles),
- **implicite** (poids neuronaux, états latents),
- ou **hybride**.

Dans notre moteur Snake :
- le monde réel est la grille,
- le monde perçu est un tenseur de capteurs,
- le world model est ce que l’agent **infère** à partir de ces capteurs.

---

## 3. modèle du monde ≠ carte exacte

Un point fondamental :

> Un world model n’est **jamais** une copie fidèle du monde.

Il est :
- partiel,
- compressé,
- orienté vers l’action.

Un bon modèle n’est pas « vrai », il est **utile**.

---

## 4. expérience de base : agent aléatoire

Dans `cours4_tiny_planification` :

- grille 7×7
- aucun bonus
- aucune pénalité
- agent aléatoire

Résultat observé :
- trajectoires erratiques,
- collisions rapides,
- aucune anticipation.

👉 L’agent **n’a pas de world model exploitable**.  
Il ne projette rien : chaque action est locale et instantanée.

---

## 5. naissance d’un world model minimal

Dès qu’on introduit une **régularité**, un modèle interne émerge.

Exemples de régularités :
- murs infranchissables,
- continuité spatiale,
- invariance de la grille,
- pénalité ou récompense systématique.

Même un agent simple finit par apprendre :
- que certaines directions mènent souvent à une collision,
- que certaines configurations sont récurrentes.

👉 Le world model commence comme une **statistique d’expériences passées**.

---

## 6. compression et effondrement du monde interne

Considérons une représentation très pauvre :
- peu de capteurs,
- peu d’états distincts,
- forte compression.

Conséquence :

- plusieurs situations réelles différentes
- sont perçues comme **identiques**

Le monde interne devient alors :

- quasi déterministe,
- pauvre en alternatives,
- rigide.

On observe un **effondrement du world model** :
> le monde interne n’exprime plus la richesse du monde réel.

---

## 7. exemple conceptuel : histogramme global

Si l’agent ne perçoit que :
- un histogramme global des couleurs,
- sans information spatiale,

alors :
- des positions très différentes deviennent équivalentes,
- l’avenir semble prévisible à tort,
- les actions perdent leur sens.

👉 Ce n’est pas le monde qui est déterministe,  
👉 c’est **la représentation qui l’impose**.

---

## 8. déterminisme artificiel

Point clé du cours :

> Une représentation trop pauvre **fabrique artificiellement un monde déterministe**.

Ce déterminisme :
- ne vient pas des règles du jeu,
- mais des limites du modèle interne.

C’est une illusion de contrôle.

---

## 9. attention, intention et modèle interne

Le world model n’est pas neutre :
- il oriente l’attention,
- il filtre ce qui compte,
- il rend certaines intentions possibles… et d’autres invisibles.

Un agent ne choisit pas seulement une action,
il choisit **dans le monde qu’il croit habiter**.

---

## 10. lien avec la planification

Planifier, c’est :
- simuler des futurs possibles,
- comparer des trajectoires,
- anticiper des conséquences.

Sans world model :
- pas de projection,
- pas de planification,
- seulement de la réaction.

La planification est donc un **usage avancé du world model**.

---

## 11. limites et dangers

Un world model peut être :
- trop simple → rigidité
- trop complexe → bruit, instabilité
- mal calibré → illusions, comportements absurdes

L’enjeu n’est pas d’avoir **le meilleur modèle**,
mais **le bon niveau de détail** pour la tâche.

---

## 12. ce qu’il faut retenir

- un agent n’agit jamais dans le monde réel, mais dans un monde **interne**
- ce monde est une construction
- sa qualité dépend de la représentation
- une mauvaise représentation peut rendre le monde artificiellement déterministe
- la planification repose sur la richesse du world model

---

## 13. transition vers la suite

Au prochain cours, nous verrons :
- comment enrichir progressivement un world model,
- comment tester sa qualité,
- et comment relier modèle du monde, récompense et politique d’action.

---

*fin du cours 4*
