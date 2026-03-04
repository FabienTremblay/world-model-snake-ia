# Runner événementiel v2

Deux modes :

- **entrainement** (Architecture E / pull)
  - le runner donne la chance aux objets actifs d'émettre au tick
  - le monde reçoit tous les événements du tick

- **epreuve** (Architecture F / push)
  - les objets publient sur le bus
  - le runner publie `tick_annonce`/`tick_survenu` (optionnel) et transmet au monde

Règle : le runner ne filtre rien.
