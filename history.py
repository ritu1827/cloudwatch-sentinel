import json
from pathlib import Path
from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "logs" / "metrics_history.json"

_lock = Lock()
MAX_HISTORY_RECORDS = 1000


def save_metrics(metrics):
    """Save metrics and retain the latest 1000 records."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        history = []

        if HISTORY_FILE.exists():
            try:
                with HISTORY_FILE.open("r", encoding="utf-8") as file:
                    history = json.load(file)

                if not isinstance(history, list):
                    history = []
            except (json.JSONDecodeError, OSError):
                history = []

        history.append(metrics)
        history = history[-MAX_HISTORY_RECORDS:]

        with HISTORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)


def get_metrics_history(limit=50):
    """Return the latest metrics records."""
    if limit < 1:
        return []

    with _lock:
        if not HISTORY_FILE.exists():
            return []

        try:
            with HISTORY_FILE.open("r", encoding="utf-8") as file:
                history = json.load(file)

            if not isinstance(history, list):
                return []

            return history[-min(limit, MAX_HISTORY_RECORDS):]

        except (json.JSONDecodeError, OSError):
            return []