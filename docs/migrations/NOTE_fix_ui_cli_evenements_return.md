# Note — fix du CLI `ui_cli evenements`

Symptôme :
- `python -m ui_cli.app.main evenements --help` → `SyntaxError: 'return' outside function`

Cause :
- le routage `evenements` était ajouté **au niveau module** (après `if __name__ == "__main__":`).

Correctif :
- déplacer ce routage **dans** `main(argv)` à côté de `pipeline` et `preparer-agent`.
