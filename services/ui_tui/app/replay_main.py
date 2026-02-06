from __future__ import annotations

import os
from pathlib import Path

from ui_tui.app.main import SnakeTuiApp

def main() -> None:
    journal = os.getenv("SNAKE_JOURNAL_PATH", "").strip()
    journal_path = Path(journal) if journal else None
    SnakeTuiApp(mode="replay", journal=journal_path).run()

if __name__ == "__main__":
    main()
