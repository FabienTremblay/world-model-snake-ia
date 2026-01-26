#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
UI_DIR="$ROOT/services/ui"
TUI_DIR="$ROOT/services/ui-tui"

if [[ -d "$TUI_DIR" ]]; then
  echo "Erreur: $TUI_DIR existe déjà" >&2
  exit 1
fi

if [[ -d "$UI_DIR" ]]; then
  mv "$UI_DIR" "$TUI_DIR"
else
  mkdir -p "$TUI_DIR"
fi

mkdir -p "$TUI_DIR/app" "$TUI_DIR/tests"

cat > "$TUI_DIR/pyproject.toml" <<'TOML'
[project]
name = "ui-tui"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "textual>=0.70.0",
  "httpx>=0.27.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
TOML

cat > "$TUI_DIR/app/__init__.py" <<'PY'
PY

cat > "$TUI_DIR/app/main.py" <<'PY'
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Vertical

# v1: on affiche un placeholder. On branchera ensuite sur runner/world-sim via HTTP.

class Grille(Static):
    def render(self) -> str:
        # rendu ASCII minimal
        lignes = []
        largeur, hauteur = 20, 10
        for y in range(hauteur):
            if y == 0 or y == hauteur - 1:
                lignes.append("#" * largeur)
            else:
                lignes.append("#" + ("." * (largeur - 2)) + "#")
        return "\n".join(lignes)

class SnakeTui(App):
    BINDINGS = [
        ("q", "quitter", "Quitter"),
        ("p", "pause", "Pause"),
        ("s", "step", "Step"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Snake TUI (v1) — placeholder", id="titre")
            yield Grille(id="grille")
            yield Static("Touches: p=pause, s=step, q=quit", id="aide")
        yield Footer()

    def action_quitter(self) -> None:
        self.exit()

    def action_pause(self) -> None:
        # plus tard: basculer l’état pause et arrêter l’auto-step
        self.bell()

    def action_step(self) -> None:
        # plus tard: appeler runner pour faire 1 step et rafraîchir la grille
        self.bell()

if __name__ == "__main__":
    SnakeTui().run()
PY

cat > "$TUI_DIR/README.md" <<'MD'
# ui-tui

TUI minimal basé sur **Textual**.

## Lancer
```bash
python -m app.main
MD

