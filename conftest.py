# conftest.py (à la racine du repo)
import sys
from pathlib import Path

RACINE_REPO = Path(__file__).resolve().parent
if str(RACINE_REPO) not in sys.path:
    sys.path.insert(0, str(RACINE_REPO))
