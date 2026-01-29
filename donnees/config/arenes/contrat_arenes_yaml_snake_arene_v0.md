# contrat yaml — arènes (`donnees/config/arenes/*.yml`) — version `snake_arene_v0`

Ce document décrit **exactement** la structure yaml attendue par le programme (loader `charger_arene_v0`).

- chemin chargé : `donnees/config/arenes/{SNAKE_ARENE}.yml`
- sélection : variable d’environnement `SNAKE_ARENE` (défaut : `demo_v0`)
- format supporté : `version: "snake_arene_v0"`

---

## 1) règles générales

### 1.1 types
- `string` : chaîne de caractères yaml
- `int` : entier
- `float` : nombre réel
- `bool` : booléen (mais ici, certains champs booléens sont implémentés en `0/1`)

### 1.2 clés inconnues
Les clés supplémentaires **peuvent être présentes** dans le yaml, mais **sont ignorées** par le loader v0 (aucun effet), sauf si elles entrent en collision avec une clé attendue.

### 1.3 erreurs
- si `version` est absent ou différent de `snake_arene_v0` : échec (format non supporté)
- si une section obligatoire manque (`id`, `grille.largeur`, `grille.hauteur`) : échec
- si un pixel fourni dans la palette n’a pas toutes ses clés (`teinte`, `intensite`, `motif`, `clignote`) : échec

---

## 2) schéma contractuel (v0)

### racine (obligatoire)

| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `version` | string | oui | — | valeur exacte : `"snake_arene_v0"` |
| `id` | string | oui | — | identifiant logique de l’arène |

### `grille` (obligatoire)

| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `grille.largeur` | int | oui | — | largeur de la grille |
| `grille.hauteur` | int | oui | — | hauteur de la grille |

### `reproductibilite` (optionnel)

| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `reproductibilite.seed` | int | non | `0` | seed utilisée par le monde/placement |

### `objets` (optionnel)

#### `objets.palette` (optionnel)
`palette` permet de définir les pixels utilisés pour dessiner certains éléments.  
Chaque entrée est un **Pixel**.

**type Pixel**
| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `teinte` | int | oui (si pixel fourni) | — | ex. 0..360 selon ton moteur |
| `intensite` | int | oui | — | ex. 0..255 |
| `motif` | int | oui | — | index de motif |
| `clignote` | int | oui | — | 0/1 |

**entrées reconnues (toutes optionnelles, chacune avec un défaut interne si absente)**
- `sol`
- `mur`
- `serpent_corps`
- `serpent_tete`
- `nourriture`
- `porte_fermee`
- `porte_ouverte`

> remarque : si une entrée est fournie, elle doit contenir **toutes** les clés du Pixel.

#### `objets.instances` (optionnel)

##### `objets.instances.nourriture` (optionnel)
| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `objets.instances.nourriture.nb` | int | non | `1` | nombre de nourritures |

##### `objets.instances.porte` (optionnel)
| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `objets.instances.porte.position.x` | int | non* | — | *si `porte.position` est présent |
| `objets.instances.porte.position.y` | int | non* | — | *si `porte.position` est présent |
| `objets.instances.porte.etat_initial` | string | non | `"fermee"` | convention : `"fermee"` ou `"ouverte"` |

> remarque : si `objets.instances.porte.position` est absent, la porte n’est pas instanciée.

### `porte_fin` (optionnel)

#### `porte_fin.ouverture` (optionnel)
| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `porte_fin.ouverture.longueur_min` | int | non | `0` | condition d’ouverture |
| `porte_fin.ouverture.score_min` | int | non | `0` | condition d’ouverture |
| `porte_fin.ouverture.tick_min` | int | non | `0` | condition d’ouverture |

### `recompenses` (optionnel)
| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `recompenses.epsilon_par_pas` | float | non | `0.0` | pénalité/bonus par pas |
| `recompenses.bonus_fin` | float | non | `0.0` | bonus à la fin |

### `capteurs` (optionnel)

#### `capteurs.bruit` (optionnel)
| clé | type | obligatoire | défaut | notes |
|---|---:|:---:|---:|---|
| `capteurs.bruit.niveau_defaut` | int | non | `0` | seul champ lu en v0 |

---

## 3) exemples complets

### exemple minimal (valide)
```yaml
version: "snake_arene_v0"
id: "minimal"

grille:
  largeur: 10
  hauteur: 6
```

### exemple riche (valide)
```yaml
version: "snake_arene_v0"
id: "demo_v0"

grille:
  largeur: 30
  hauteur: 12

reproductibilite:
  seed: 12345

objets:
  palette:
    sol:           { teinte: 200, intensite: 40,  motif: 0, clignote: 0 }
    mur:           { teinte: 210, intensite: 120, motif: 3, clignote: 0 }
    serpent_corps: { teinte: 120, intensite: 160, motif: 2, clignote: 0 }
    serpent_tete:  { teinte: 120, intensite: 230, motif: 5, clignote: 0 }
    nourriture:    { teinte: 30,  intensite: 220, motif: 6, clignote: 1 }
    porte_fermee:  { teinte: 300, intensite: 180, motif: 1, clignote: 0 }
    porte_ouverte: { teinte: 300, intensite: 240, motif: 1, clignote: 1 }

  instances:
    nourriture: { nb: 2 }
    porte:
      position: { x: 2, y: 2 }
      etat_initial: "fermee"

porte_fin:
  ouverture:
    longueur_min: 5
    score_min: 2
    tick_min: 0

recompenses:
  epsilon_par_pas: -0.02
  bonus_fin: 5.0

capteurs:
  bruit:
    niveau_defaut: 1
```

---

