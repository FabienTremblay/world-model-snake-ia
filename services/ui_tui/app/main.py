from __future__ import annotations

from pathlib import Path

from textual.app import App

from ui_tui.app.cli import parser, appliquer_env
from ui_tui.app.ecrans import EcranMenu, EcranSession

class SnakeTuiApp(App):
    CSS = """
    #menu_root { padding: 1; }
    #titre { margin-bottom: 1; }
    #side { width: 40; padding-left: 1; }
    #journal { margin-top: 1; }
    #stats { margin-top: 1; }
    #situation_root { padding: 1; }
    #sit_texte { margin-top: 1; }
    #sit_hint { margin-top: 1; }
    """

    BINDINGS = [("q", "quitter", "Quitter")]

    def __init__(self, mode: str = "menu", journal: Path | None = None) -> None:
        super().__init__()
        self.mode = mode
        self.journal = journal

    def on_mount(self) -> None:
        if self.mode == "menu":
            self.push_screen(EcranMenu())
        elif self.mode == "replay":
            self.push_screen(EcranSession(mode="replay", journal=self.journal))
        else:
            self.push_screen(EcranSession(mode="manual", journal=None))

    def action_quitter(self) -> None:
        self.exit()

def main() -> None:
    ap = parser()
    args = ap.parse_args()
    appliquer_env(args)

    journal = Path(args.journal) if args.journal else None
    SnakeTuiApp(mode=args.mode, journal=journal).run()

if __name__ == "__main__":
    main()
